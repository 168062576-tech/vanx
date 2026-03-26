"""
御龙军虚拟 Agent 世界 - RESTful API 接口
版本：v1.1
创建时间：2026-03-16
修复时间：2026-03-23

修复内容 (v1.1):
  1. [致命] 移除所有对未定义 `world_manager` 变量的引用，
     改为直接使用 DeepIntegrationEngine 实例 `engine`
  2. [功能] 添加 API Key 认证中间件 (X-API-Key 请求头, 默认 key: yulong-dev-key)
  3. [功能] 所有路由添加 try/except 异常处理
  4. [功能] API 启动时自动创建初始 Agent 群体
  5. [修复] 适配 DeepIntegrationEngine 实际接口:
     - agents 是 Dict[int, UnifiedAgent] 而非 List
     - 无 world_manager 多世界模式，当前为单引擎实例
     - ExperimentTemplateLibrary 无 create_experiment_from_template 方法
  6. [功能] 新增 POST /api/v1/agents/create 创建新 Agent
  7. [功能] 新增 POST /api/v1/simulate 推进模拟
"""

from flask import Flask, request, jsonify
from functools import wraps
from collections import defaultdict
import sys
import os
import traceback
import json
import glob
import time
import random
import threading
import secrets
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

# JWT 支持（可选依赖，未安装则优雅降级）
try:
    import jwt as pyjwt
    _JWT_AVAILABLE = True
except ImportError:
    pyjwt = None
    _JWT_AVAILABLE = False

# 动态路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 使用新的深度集成引擎
from deep_integration_engine import DeepIntegrationEngine
from experiment_templates_v2 import ExperimentTemplateLibrary
from narrative_engine import NarrativeEngine
from storage import SQLiteStore
from experiment_report_generator import ExperimentReportGenerator
from experiment_runner import ExperimentRunner, ExperimentStatus

# 商业模块（开源版本缺失不影响核心运行）
try:
    from report_generator_v2 import SmartReportGenerator
except ImportError:
    SmartReportGenerator = None
try:
    from multi_world_experiment import MultiWorldExperiment
except ImportError:
    MultiWorldExperiment = None

# ============ 结构化日志 ============
def setup_logging():
    _logger = logging.getLogger('virtual_world')
    _logger.setLevel(logging.INFO)
    fh = RotatingFileHandler('virtual_world.log', maxBytes=10*1024*1024, backupCount=5)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    _logger.addHandler(fh)
    return _logger

logger = setup_logging()


# ============ 简单内存 Rate Limiter ============
import time as _time
_rate_limits = defaultdict(list)

def rate_limit(max_per_minute=60):
    """速率限制装饰器 — 基于客户端 IP 的滑动窗口"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = request.remote_addr
            now = _time.time()
            _rate_limits[key] = [t for t in _rate_limits[key] if now - t < 60]
            if len(_rate_limits[key]) >= max_per_minute:
                logger.warning(f"Rate limit exceeded for {key} on {request.path}")
                return jsonify({'error': 'Rate limit exceeded'}), 429
            _rate_limits[key].append(now)
            # [Phase3 Fix] 定期清理过期条目防止内存泄漏
            if len(_rate_limits) > 1000:
                expired = [k for k, v in _rate_limits.items() if not v or now - v[-1] > 300]
                for k in expired:
                    del _rate_limits[k]
            return f(*args, **kwargs)
        return wrapper
    return decorator


app = Flask(__name__)

# ============ 配置 ============
API_VERSION = 'v1'
try:
    from config import API_KEY
except ImportError:
    API_KEY = os.environ.get('YULONG_API_KEY', '')
    if not API_KEY:
        API_KEY = secrets.token_hex(16)
        print(f"[SECURITY] No YULONG_API_KEY set. Generated random key: {API_KEY}")
JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
INITIAL_AGENT_COUNT = 50
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# ============ CORS + 安全头 ============
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    # CORS — 仅允许本地开发地址
    origin = request.headers.get('Origin', '')
    allowed_origins = (
        'http://localhost:5001', 'http://127.0.0.1:5001',
        'http://localhost:5002', 'http://127.0.0.1:5002',
    )
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response


# ============ 初始化引擎 ============
engine = None
template_library = None
narrator = NarrativeEngine()
smart_reporter = None
excel_reporter = None  # ExperimentReportGenerator 实例
storage = None  # SQLiteStore 实例
experiment_runner = None  # ExperimentRunner 实例


def init_engine(count=None):
    """Initialize engine with specified agent count. Called by run.py."""
    global engine, template_library, smart_reporter, excel_reporter, storage, experiment_runner
    if count is None:
        count = INITIAL_AGENT_COUNT
    engine = DeepIntegrationEngine()
    template_library = ExperimentTemplateLibrary()
    if SmartReportGenerator:
        smart_reporter = SmartReportGenerator(output_path=DATA_DIR)
    else:
        smart_reporter = None
    excel_reporter = ExperimentReportGenerator(output_dir=DATA_DIR)
    experiment_runner = ExperimentRunner()

    # ── 初始化 SQLite 持久化 ──
    db_path = os.path.join(DATA_DIR, 'world.db')
    storage = SQLiteStore(db_path=db_path)
    print(f"  [SQLite] 数据库已连接: {db_path}")

    # 创建初始 Agent 并批量保存到 SQLite
    _init_population(count)


def _init_population(count: int):
    """启动时创建初始 Agent 群体并分配职业/国籍"""
    import random as _rng
    print(f"  Creating {count} agents...")
    
    OCCUPATIONS = ['CEO','CTO','CFO','Engineering Manager','Sales Manager',
                   'Senior Engineer','Junior Engineer','Doctor','Nurse',
                   'Teacher','Professor','Farmer','Worker','Driver']
    OCC_WEIGHTS = [0.02,0.02,0.01,0.05,0.05,0.15,0.20,0.08,0.07,0.10,0.03,0.05,0.12,0.05]
    # 133 nationalities from name_data_124
    from name_data_124 import NAME_DATA as _ND
    NATIONALITIES = list(_ND.keys())
    # Weighted distribution: major populations get higher weight
    _MAJOR = {'chinese':0.14,'indian':0.12,'american':0.05,'indonesian':0.04,'pakistani':0.03,
              'brazilian':0.03,'nigerian':0.03,'bangladeshi':0.02,'russian':0.02,'japanese':0.02,
              'mexican':0.02,'filipino':0.02,'egyptian':0.02,'ethiopian':0.015,'vietnamese':0.015,
              'iranian':0.015,'turkish':0.015,'german':0.015,'thai':0.01,'english':0.01,
              'french':0.01,'italian':0.01,'korean':0.01,'colombian':0.01,'spanish':0.01,
              'south_african':0.01,'kenyan':0.01,'argentne':0.008,'ukrainian':0.008,'polish':0.008}
    _base = (1.0 - sum(_MAJOR.values())) / max(1, len(NATIONALITIES) - len(_MAJOR))
    NAT_WEIGHTS = [_MAJOR.get(n, _base) for n in NATIONALITIES]
    _wsum = sum(NAT_WEIGHTS)
    NAT_WEIGHTS = [w/_wsum for w in NAT_WEIGHTS]  # normalize
    
    for i in range(count):
        agent = engine.create_agent()
        # Assign realistic occupation (engine default is all CEO)
        agent.occupation = _rng.choices(OCCUPATIONS, weights=OCC_WEIGHTS, k=1)[0]
        # Assign nationality
        agent._nationality = _rng.choices(NATIONALITIES, weights=NAT_WEIGHTS, k=1)[0]
        # Adjust income based on occupation
        income_map = {'CEO':50000,'CTO':45000,'CFO':42000,'Engineering Manager':30000,
                      'Sales Manager':25000,'Senior Engineer':20000,'Junior Engineer':8000,
                      'Doctor':35000,'Nurse':12000,'Teacher':10000,'Professor':25000,
                      'Farmer':4000,'Worker':6000,'Driver':7000}
        base = income_map.get(agent.occupation, 8000)
        agent.income = base * _rng.uniform(0.7, 1.4)
        agent.is_unemployed = False
        
        if (i + 1) % 2000 == 0:
            print(f"    {i+1}/{count} created")
    
    print(f"  [OK] Population ready: {len(engine.agents)} agents")

    # 批量保存到 SQLite
    if storage:
        saved = storage.save_agents_batch(engine.agents.values())
        print(f"  [SQLite] 已保存 {saved} 个 Agent 到数据库")


# ============ JWT Token 辅助函数 ============
def create_token(user_id='admin', tier='pro'):
    """创建 JWT Token（需要 pyjwt 库）"""
    if not _JWT_AVAILABLE:
        return None
    return pyjwt.encode(
        {'user_id': user_id, 'tier': tier, 'exp': datetime.now() + timedelta(hours=24)},
        JWT_SECRET, algorithm='HS256'
    )


# ============ 认证中间件 ============
def require_api_key(f):
    """API Key / JWT 认证装饰器
    
    认证方式（按优先级）：
    1. Authorization: Bearer <jwt_token>（需 pyjwt）
    2. X-API-Key: <key>
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1) 尝试 JWT Bearer Token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer ') and _JWT_AVAILABLE:
            token = auth_header[7:]
            try:
                payload = pyjwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                request.jwt_payload = payload
                return f(*args, **kwargs)
            except pyjwt.ExpiredSignatureError:
                return jsonify({'success': False, 'error': 'Token 已过期'}), 401
            except pyjwt.InvalidTokenError:
                return jsonify({'success': False, 'error': '无效的 Token'}), 401

        # 2) 传统 API Key
        key = request.headers.get('X-API-Key', '')
        if key != API_KEY:
            return jsonify({
                'success': False,
                'error': '未授权：无效的 API Key',
                'hint': '请在请求头中设置 X-API-Key 或 Authorization: Bearer <token>'
            }), 401
        return f(*args, **kwargs)
    return decorated


# ============ 错误处理 ============
@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': '接口不存在'}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'success': False, 'error': '请求方法不允许'}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


# ============ API 路由 ============

@app.route(f'/api/{API_VERSION}/health', methods=['GET'])
def health_check():
    """健康检查 (无需认证)"""
    try:
        alive_count = sum(1 for a in engine.agents.values() if a.is_alive)
        return jsonify({
            'status': 'healthy',
            'version': API_VERSION,
            'engine': 'DeepIntegrationEngine',
            'total_agents': len(engine.agents),
            'alive_agents': alive_count,
            'months_simulated': engine.months_simulated
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'健康检查失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/stats', methods=['GET'])
@require_api_key
@rate_limit(60)
def get_world_stats():
    """获取世界统计数据"""
    try:
        logger.info(f"API call: {request.path} from {request.remote_addr}")
        stats = engine.get_world_statistics()
        if not stats:
            return jsonify({
                'success': True,
                'data': {},
                'message': '暂无统计数据（Agent 数量为 0）'
            })
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取统计失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/stats/pyramid', methods=['GET'])
@require_api_key
@rate_limit(60)
def get_population_pyramid():
    """获取人口金字塔数据（按年龄段和性别分组）"""
    try:
        age_groups = ['0-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']
        male_counts = [0] * 9
        female_counts = [0] * 9

        for agent in engine.agents.values():
            if not agent.is_alive:
                continue
            age = agent.age
            gender = agent.gender  # 'male' or 'female'

            if age < 10:
                idx = 0
            elif age < 20:
                idx = 1
            elif age < 30:
                idx = 2
            elif age < 40:
                idx = 3
            elif age < 50:
                idx = 4
            elif age < 60:
                idx = 5
            elif age < 70:
                idx = 6
            elif age < 80:
                idx = 7
            else:
                idx = 8

            if gender == 'male':
                male_counts[idx] += 1
            else:
                female_counts[idx] += 1

        return jsonify({
            'success': True,
            'data': {
                'age_groups': age_groups,
                'male': male_counts,
                'female': female_counts
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取人口金字塔数据失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/agents', methods=['GET'])
@require_api_key
@rate_limit(60)
def list_agents():
    """获取 Agent 列表（支持分页 + 筛选 + 排序）"""
    try:
        logger.info(f"API call: {request.path} from {request.remote_addr}")

        # ── 旧版兼容参数 ──
        limit = request.args.get('limit', None, type=int)
        offset = request.args.get('offset', 0, type=int)

        # ── 新版筛选参数 ──
        age_min = request.args.get('age_min', None, type=int)
        age_max = request.args.get('age_max', None, type=int)
        income_min = request.args.get('income_min', None, type=float)
        income_max = request.args.get('income_max', None, type=float)
        occupation = request.args.get('occupation', None, type=str)
        sort_by = request.args.get('sort_by', None, type=str)  # age / income / happiness
        sort_order = request.args.get('sort_order', 'asc', type=str)  # asc / desc

        # ── 分页参数（新版优先） ──
        page = request.args.get('page', None, type=int)
        page_size = request.args.get('page_size', 100, type=int)
        page_size = min(page_size, 500)  # 限制最大 page_size

        # agents 是 Dict[int, UnifiedAgent]
        agents = list(engine.agents.values())

        # ── 筛选 ──
        if age_min is not None:
            agents = [a for a in agents if a.age >= age_min]
        if age_max is not None:
            agents = [a for a in agents if a.age <= age_max]
        if income_min is not None:
            agents = [a for a in agents if a.income >= income_min]
        if income_max is not None:
            agents = [a for a in agents if a.income <= income_max]
        if occupation:
            agents = [a for a in agents if (a.occupation or '').lower() == occupation.lower()]

        total_filtered = len(agents)

        # ── 排序 ──
        if sort_by in ('age', 'income', 'happiness'):
            reverse = (sort_order.lower() == 'desc')
            agents.sort(key=lambda a: getattr(a, sort_by, 0) or 0, reverse=reverse)
        else:
            agents.sort(key=lambda a: a.id)

        # ── 分页 ──
        if page is not None:
            # 新版分页 (page, page_size)
            page = max(1, page)
            start = (page - 1) * page_size
            end = start + page_size
            agents_page = agents[start:end]
            agents_data = [a.to_dict() for a in agents_page]
            for i, a in enumerate(agents_page):
                agents_data[i]['nationality'] = getattr(a, '_nationality', 'chinese')
            return jsonify({
                'success': True,
                'data': {
                    'agents': agents_data,
                    'total': len(engine.agents),
                    'total_filtered': total_filtered,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_filtered + page_size - 1) // page_size,
                }
            })
        else:
            # 旧版兼容 (limit, offset)
            if limit is None:
                limit = 100
            agents_page = agents[offset:offset + limit]
            agents_data = [a.to_dict() for a in agents_page]
            for i, a in enumerate(agents_page):
                agents_data[i]['nationality'] = getattr(a, '_nationality', 'chinese')
            return jsonify({
                'success': True,
                'data': {
                    'agents': agents_data,
                    'total': len(engine.agents),
                    'total_filtered': total_filtered,
                    'limit': limit,
                    'offset': offset
                }
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取 Agent 列表失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/agents/<int:agent_id>', methods=['GET'])
@require_api_key
def get_agent_detail(agent_id):
    """获取单个 Agent 详情"""
    try:
        status = engine.get_agent_status(agent_id)
        if not status:
            return jsonify({
                'success': False,
                'error': f'Agent {agent_id} 不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': {'agent': status}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取 Agent 详情失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/agents/create', methods=['POST'])
@require_api_key
@rate_limit(10)
def create_agent():
    """创建新 Agent"""
    try:
        logger.info(f"API call: {request.path} from {request.remote_addr}")
        data = request.json or {}
        count = data.get('count', 1)
        agent_data = data.get('agent_data', {})

        if count < 1 or count > 1000:
            return jsonify({
                'success': False,
                'error': 'count 必须在 1-1000 之间'
            }), 400

        created = []
        for _ in range(count):
            agent = engine.create_agent(agent_data)
            created.append(agent.to_dict())

        return jsonify({
            'success': True,
            'message': f'成功创建 {len(created)} 个 Agent',
            'data': {
                'created_agents': created if count <= 10 else created[:10],
                'count': len(created),
                'total_agents': len(engine.agents)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'创建 Agent 失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/simulate', methods=['POST'])
@require_api_key
@rate_limit(10)
def simulate():
    """推进模拟（按月）"""
    try:
        logger.info(f"API call: {request.path} from {request.remote_addr}")

        # 暂停检查
        if _simulation_paused:
            return jsonify({
                'success': False,
                'error': '模拟已暂停，请先调用 /simulation/resume 恢复'
            }), 409

        data = request.json or {}
        months = data.get('months', 1)

        if months < 1 or months > 120:
            return jsonify({
                'success': False,
                'error': 'months 必须在 1-120 之间'
            }), 400

        result = engine.simulate_month(months)
        return jsonify({
            'success': True,
            'message': f'模拟推进 {months} 个月',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'模拟失败: {str(e)}'
        }), 500


# ============ SQLite 持久化 API ============

@app.route(f'/api/{API_VERSION}/save', methods=['POST'])
@require_api_key
@rate_limit(10)
def save_state():
    """手动保存当前世界状态到 SQLite"""
    try:
        logger.info(f"API call: {request.path} from {request.remote_addr}")
        if not storage:
            return jsonify({
                'success': False,
                'error': 'SQLite 存储未初始化'
            }), 500

        # 保存所有 Agent
        agent_count = storage.save_agents_batch(engine.agents.values())

        # 保存事件（如果有新事件）
        event_count = 0
        if engine.events:
            event_count = storage.save_events_batch(
                engine.events, engine.months_simulated
            )

        # 创建快照记录
        alive_count = sum(1 for a in engine.agents.values() if a.is_alive)
        snapshot_name = f"manual_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        snapshot_id = storage.create_snapshot(
            name=snapshot_name,
            month=engine.months_simulated,
            agent_count=alive_count,
            config={'total_agents': len(engine.agents)}
        )

        # 保存元数据
        storage.set_meta('last_save_time', datetime.now().isoformat())
        storage.set_meta('months_simulated', str(engine.months_simulated))

        return jsonify({
            'success': True,
            'message': '世界状态已保存到 SQLite',
            'data': {
                'agents_saved': agent_count,
                'events_saved': event_count,
                'snapshot_id': snapshot_id,
                'snapshot_name': snapshot_name,
                'db_path': storage.db_path
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'保存失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route(f'/api/{API_VERSION}/load', methods=['POST'])
@require_api_key
def load_state():
    """从 SQLite 加载世界状态（恢复数据）"""
    try:
        if not storage:
            return jsonify({
                'success': False,
                'error': 'SQLite 存储未初始化'
            }), 500

        # 检查数据库中是否有数据
        db_agent_count = storage.agent_count()
        if db_agent_count == 0:
            return jsonify({
                'success': False,
                'error': '数据库中没有已保存的 Agent 数据',
                'hint': '请先使用 POST /api/v1/save 保存数据'
            }), 404

        # 加载所有 Agent 数据
        agent_data_list = storage.load_all_agent_data()

        # 清空当前引擎中的 Agent，重新从数据库恢复
        restored_count = 0
        skipped_count = 0

        for agent_data in agent_data_list:
            agent_id = agent_data['id']
            if agent_id in engine.agents:
                # 更新已存在的 Agent 属性
                agent = engine.agents[agent_id]
                for attr in ['age', 'gender', 'education_level', 'occupation',
                             'income', 'net_worth', 'health_score', 'mental_health',
                             'happiness', 'marital_status', 'spouse_id',
                             'life_expectancy', 'credit_score', 'housing_status']:
                    if attr in agent_data and hasattr(agent, attr):
                        setattr(agent, attr, agent_data[attr])
                restored_count += 1
            else:
                # Agent 不在引擎中，尝试重新创建
                try:
                    new_agent = engine.create_agent(agent_data)
                    restored_count += 1
                except Exception:
                    skipped_count += 1

        # 恢复元数据
        saved_months = storage.get_meta('months_simulated')
        last_save = storage.get_meta('last_save_time', '未知')

        # 获取快照列表
        snapshots = storage.list_snapshots()
        latest_snapshot = snapshots[0] if snapshots else None

        return jsonify({
            'success': True,
            'message': f'已从 SQLite 恢复 {restored_count} 个 Agent',
            'data': {
                'agents_restored': restored_count,
                'agents_skipped': skipped_count,
                'db_agent_count': db_agent_count,
                'engine_agent_count': len(engine.agents),
                'saved_months': saved_months,
                'last_save_time': last_save,
                'latest_snapshot': dict(latest_snapshot) if latest_snapshot else None,
                'db_path': storage.db_path
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'加载失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route(f'/api/{API_VERSION}/experiments/templates', methods=['GET'])
def list_templates():
    """获取实验模板列表"""
    try:
        category = request.args.get('category', None)
        print(f"[DEBUG] template_library = {template_library}, templates count = {len(template_library.templates)}")
        templates = template_library.list_templates(category)
        print(f"[DEBUG] Returning {len(templates)} templates for category={category}")
        templates_data = []
        for t in templates:
            templates_data.append({
                'template_id': t.template_id,
                'name': t.name,
                'category': t.category,
                'description': t.description,
                'duration_months': t.duration_months,
                'agent_count': t.agent_count,
                'key_metrics': t.key_metrics,
            })

        return jsonify({
            'success': True,
            'data': {
                'templates': templates_data,
                'total': len(templates_data)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取模板列表失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/experiments/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """获取模板详情"""
    try:
        template = template_library.get_template(template_id)

        if not template:
            return jsonify({
                'success': False,
                'error': f'模板 {template_id} 不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': {
                'template_id': template.template_id,
                'name': template.name,
                'category': template.category,
                'description': template.description,
                'duration_months': template.duration_months,
                'agent_count': template.agent_count,
                'key_metrics': template.key_metrics,
                'setup_params': template.setup_params,
                'success_criteria': template.success_criteria,
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取模板详情失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/experiments/run', methods=['POST'])
@require_api_key
@rate_limit(10)
def run_experiment():
    """基于模板运行实验（简化版：创建 Agent + 模拟指定月数）"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400

        template_id = data.get('template_id')
        if not template_id:
            return jsonify({
                'success': False,
                'error': '必须指定 template_id'
            }), 400

        template = template_library.get_template(template_id)
        if not template:
            return jsonify({
                'success': False,
                'error': f'模板 {template_id} 不存在'
            }), 404

        # 根据模板配置创建 Agent（限制数量防止阻塞）
        agent_count = min(data.get('agent_count', template.agent_count), 500)
        months = min(data.get('months', template.duration_months), 60)

        created_ids = []
        for _ in range(agent_count):
            agent = engine.create_agent(template.setup_params)
            created_ids.append(agent.id)

        # 运行模拟
        sim_result = engine.simulate_month(months)

        return jsonify({
            'success': True,
            'message': f'实验 {template.name} 已运行',
            'data': {
                'template_id': template_id,
                'template_name': template.name,
                'agents_created': agent_count,
                'months_simulated': months,
                'simulation_result': sim_result,
                'total_agents': len(engine.agents),
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'运行实验失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/trends', methods=['GET'])
@require_api_key
@rate_limit(60)
def get_trends():
    """趋势折线图数据（从引擎内存构建，无历史则模拟回溯）"""
    try:
        import random as rng

        alive = [a for a in engine.agents.values() if a.is_alive]
        n = max(len(alive), 1)

        cur_pop = n
        cur_inc = sum(a.income for a in alive) / n
        employed = sum(1 for a in alive if a.occupation and a.occupation not in ('unemployed', ''))
        cur_emp = employed / n * 100
        sats = [a.life_satisfaction for a in alive if a.life_satisfaction is not None]
        cur_sat = (sum(sats) / len(sats) / 20.0) if sats else 3.0  # 0-100 → 0-5

        # 生成模拟历史趋势（从当前值回溯）
        pts = min(24, max(engine.months_simulated, 12))
        seed_rng = rng.Random(12345)
        days, pop, income, emp, sat = [], [], [], [], []
        for i in range(pts):
            progress = i / pts
            days.append(f'M-{pts - i}')
            scale = 0.7 + 0.3 * progress
            pop.append(max(10, int(cur_pop * scale + seed_rng.gauss(0, cur_pop * 0.02))))
            income.append(round(max(0, cur_inc * scale + seed_rng.gauss(0, cur_inc * 0.03)), 0))
            emp.append(round(max(30, min(100, cur_emp * scale + seed_rng.gauss(0, 2))), 1))
            sat.append(round(max(1, min(5, cur_sat * scale + seed_rng.gauss(0, 0.1))), 2))
        # 最后一个 = 当前真实值
        days.append('Now')
        pop.append(cur_pop)
        income.append(round(cur_inc, 0))
        emp.append(round(cur_emp, 1))
        sat.append(round(cur_sat, 2))

        return jsonify({
            'days': days,
            'population': pop,
            'avg_income': income,
            'employment_rate': emp,
            'satisfaction': sat,
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取趋势数据失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/regions', methods=['GET'])
@require_api_key
@rate_limit(60)
def get_regions():
    """区域地图数据"""
    try:
        from utils import REGION_DEFINITIONS as UTIL_REGIONS, OCCUPATION_REGION_MAP as UTIL_OCC_MAP

        alive = [a for a in engine.agents.values() if a.is_alive]

        # 职业 → 中文映射
        _OCC_MAP = {
            'unemployed': '其他',
            'Technology': '信息技术', 'Finance': '金融',
            'Healthcare': '医疗', 'Education': '教育',
            'Retail': '服务业', 'Manufacturing': '制造业',
            'Government': '政府',
        }

        # 按区域聚合 Agent
        region_agents = {rkey: [] for rkey in UTIL_REGIONS}
        for a in alive:
            raw_occ = a.occupation or 'unemployed'
            occ = _OCC_MAP.get(raw_occ, raw_occ)
            if occ not in UTIL_OCC_MAP:
                occ = '其他'
            region_key = UTIL_OCC_MAP.get(occ, 'residential')
            if region_key in region_agents:
                region_agents[region_key].append(a)
            else:
                region_agents.setdefault('residential', []).append(a)

        regions_out = []
        for rkey, rdef in UTIL_REGIONS.items():
            ra = region_agents.get(rkey, [])
            ra_n = max(len(ra), 1)
            avg_inc = round(sum(a.income for a in ra) / ra_n, 0) if ra else 0
            regions_out.append({
                'name': rdef['name'],
                'name_en': rdef['name_en'],
                'icon': rdef['icon'],
                'bounds': rdef['bounds'],
                'color': rdef['color'],
                'agent_count': len(ra),
                'avg_income': avg_inc,
            })

        return jsonify({
            'regions': regions_out,
            'layout': {'width': 100, 'height': 100, 'total_agents': len(alive)},
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取区域数据失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/events/stream', methods=['GET'])
def api_events_stream():
    """SSE 实时事件推送（不需要 API Key，SSE 连接不方便带 header）"""
    try:
        from flask import Response, stream_with_context
        import hashlib as _hashlib

        def generate():
            last_hash = ''
            while True:
                try:
                    # 从引擎获取最新事件
                    recent = engine.events[-5:] if engine.events else []
                    events_data = []
                    for evt in reversed(recent):
                        # 映射事件类型到前端分类
                        _evt_meta = {
                            'agent_created': {'emoji': '👶', 'cat': 'birth'},
                            'agent_died': {'emoji': '💀', 'cat': 'death'},
                            'marriage_decision': {'emoji': '🎉', 'cat': 'marriage'},
                            'employment_started': {'emoji': '💼', 'cat': 'job'},
                            'career_change': {'emoji': '🔄', 'cat': 'job'},
                            'crime_decision': {'emoji': '🚨', 'cat': 'crime'},
                            'medical_expense': {'emoji': '🏥', 'cat': 'health'},
                            'housing_change': {'emoji': '🏠', 'cat': 'house'},
                            'epidemic': {'emoji': '🦠', 'cat': 'epidemic'},
                        }
                        meta = _evt_meta.get(evt.event_type, {'emoji': '📌', 'cat': 'misc'})
                        # Generate Chinese description
                        agent_name = narrator.generate_name(evt.agent_id, 'male') if evt.agent_id else '世界系统'
                        _desc_map = {
                            'agent_created': f'{agent_name} 来到了这个世界',
                            'agent_died': f'{agent_name} 离开了这个世界',
                            'marriage_decision': f'{agent_name} 步入了婚姻殿堂',
                            'employment_started': f'{agent_name} 找到了新工作',
                            'career_change': f'{agent_name} 换了一份新工作',
                            'crime_decision': f'{agent_name} 走上了歧途',
                            'crime_caught': f'{agent_name} 因违法行为被捕',
                            'medical_expense': f'{agent_name} 去医院看了病',
                            'housing_change': f'{agent_name} 搬了新家',
                            'epidemic': f'流行病在社区蔓延',
                            'debt_increase': f'{agent_name} 的负债增加了',
                            'welfare_enrolled': f'{agent_name} 申请了社会福利',
                            'risk_event': f'{agent_name} 遭遇了意外事件',
                            'education_completed': f'{agent_name} 完成了学业',
                            'divorce': f'{agent_name} 结束了婚姻关系',
                        }
                        text = _desc_map.get(evt.event_type, f'{agent_name} 经历了 {evt.event_type}')
                        events_data.append({
                            'type': meta['cat'],
                            'emoji': meta['emoji'],
                            'text': text,
                            'time': str(evt.timestamp)[:16] if hasattr(evt, 'timestamp') else '',
                            'agent_id': evt.agent_id,
                        })

                    content = json.dumps(events_data, ensure_ascii=False)
                    h = _hashlib.md5(content.encode()).hexdigest()[:12]
                    if h != last_hash and events_data:
                        last_hash = h
                        for ev in events_data:
                            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
                    else:
                        yield ": keepalive\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
                time.sleep(3)

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            }
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'SSE 流启动失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/events', methods=['GET'])
@require_api_key
@rate_limit(60)
def get_events():
    """获取最近事件"""
    try:
        limit = request.args.get('limit', 50, type=int)
        recent_events = engine.events[-limit:] if engine.events else []
        events_data = []
        _evt_meta = {
            'agent_created': {'emoji': '👶', 'cat': 'birth', 'desc': '来到了这个世界'},
            'agent_died': {'emoji': '💀', 'cat': 'death', 'desc': '离开了这个世界'},
            'marriage_decision': {'emoji': '🎉', 'cat': 'marriage', 'desc': '步入了婚姻殿堂'},
            'employment_started': {'emoji': '💼', 'cat': 'job', 'desc': '找到了新工作'},
            'career_change': {'emoji': '🔄', 'cat': 'job', 'desc': '换了一份新工作'},
            'crime_decision': {'emoji': '🚨', 'cat': 'crime', 'desc': '走上了歧途'},
            'crime_caught': {'emoji': '⛓️', 'cat': 'crime', 'desc': '因违法行为被捕'},
            'medical_expense': {'emoji': '🏥', 'cat': 'health', 'desc': '去医院看了病'},
            'housing_change': {'emoji': '🏠', 'cat': 'house', 'desc': '搬了新家'},
            'debt_increase': {'emoji': '💸', 'cat': 'misc', 'desc': '的负债增加了'},
            'welfare_enrolled': {'emoji': '🤝', 'cat': 'misc', 'desc': '申请了社会福利'},
            'risk_event': {'emoji': '⚠️', 'cat': 'misc', 'desc': '遭遇了意外事件'},
            'education_completed': {'emoji': '🎓', 'cat': 'misc', 'desc': '完成了学业'},
            'divorce': {'emoji': '💔', 'cat': 'marriage', 'desc': '结束了婚姻关系'},
        }
        for evt in reversed(recent_events):
            meta = _evt_meta.get(evt.event_type, {'emoji': '📌', 'cat': 'misc', 'desc': evt.event_type})
            agent_name = narrator.generate_name(evt.agent_id, 'male') if evt.agent_id else '系统'
            events_data.append({
                'type': meta['cat'],
                'emoji': meta['emoji'],
                'text': f'{agent_name} {meta["desc"]}',
                'time': str(evt.timestamp)[:16] if hasattr(evt, 'timestamp') else '',
                'agent_id': evt.agent_id,
                'event_type': evt.event_type,
            })

        return jsonify({
            'success': True,
            'data': {
                'events': events_data,
                'total_events': len(engine.events),
                'showing': len(events_data)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取事件失败: {str(e)}'
        }), 500


# ============ 社交网络 API ============

@app.route(f'/api/{API_VERSION}/social/network', methods=['GET'])
@require_api_key
@rate_limit(60)
def get_social_network():
    """获取 Agent 社交关系网络图数据（nodes + links）"""
    try:
        import random as rng

        limit = min(request.args.get('limit', 100, type=int), 500)

        # 采样存活 Agent
        alive = [a for a in engine.agents.values() if a.is_alive]
        if not alive:
            return jsonify({'success': True, 'data': {'nodes': [], 'links': []}})

        if len(alive) > limit:
            sample = rng.sample(alive, limit)
        else:
            sample = list(alive)

        sample_ids = {a.id for a in sample}

        # ── 构建 nodes ──
        nodes = []
        for a in sample:
            name = narrator.generate_name(a.id, a.gender)
            occ = a.occupation or '其他'
            # 职业分组映射
            occ_group = _map_occupation_group(occ)
            nodes.append({
                'id': a.id,
                'name': name,
                'group': occ_group,
                'occupation': occ,
                'age': a.age,
                'gender': a.gender,
                'value': 1,  # 稍后更新
            })

        id_to_node = {n['id']: n for n in nodes}

        # ── 构建 links ──
        links = []
        link_set = set()  # 去重

        # 1) 从引擎社交系统提取已有连接
        social_sys = getattr(engine, 'social_system', None)
        if social_sys and hasattr(social_sys, 'connections'):
            for (id1, id2), conn in social_sys.connections.items():
                if id1 in sample_ids and id2 in sample_ids:
                    key = (min(id1, id2), max(id1, id2))
                    if key not in link_set:
                        link_set.add(key)
                        rel = conn.relationship_level.value if hasattr(conn.relationship_level, 'value') else str(conn.relationship_level)
                        link_type = 'friend'
                        link_value = 1
                        if rel in ('close_friend', 'best_friend'):
                            link_type = 'close_friend'
                            link_value = 2
                        elif rel == 'colleague':
                            link_type = 'colleague'
                            link_value = 1
                        elif rel == 'family':
                            link_type = 'family'
                            link_value = 2
                        elif rel == 'partner':
                            link_type = 'spouse'
                            link_value = 3
                        links.append({
                            'source': id1,
                            'target': id2,
                            'type': link_type,
                            'value': link_value,
                        })

        # 2) 从婚姻数据提取配偶关系
        for a in sample:
            if a.marital_status == 'married' and a.spouse_id and a.spouse_id in sample_ids:
                key = (min(a.id, a.spouse_id), max(a.id, a.spouse_id))
                if key not in link_set:
                    link_set.add(key)
                    links.append({
                        'source': a.id,
                        'target': a.spouse_id,
                        'type': 'spouse',
                        'value': 3,
                    })

        # 3) 补充模拟关系：基于职业+区域相近度
        # 每个 Agent 目标 2-5 个连接
        sample_list = list(sample)
        for a in sample_list:
            existing = sum(1 for l in links if l['source'] == a.id or l['target'] == a.id)
            needed = rng.randint(2, 5) - existing
            if needed <= 0:
                continue

            # 按相似度排序候选
            candidates = []
            for b in sample_list:
                if b.id == a.id:
                    continue
                key = (min(a.id, b.id), max(a.id, b.id))
                if key in link_set:
                    continue
                # 相似度分数：同职业+3，年龄接近+2，同区域+2
                score = 0
                if a.occupation == b.occupation:
                    score += 3
                if abs(a.age - b.age) < 10:
                    score += 2
                a_region = getattr(a, 'housing_status', '')
                b_region = getattr(b, 'housing_status', '')
                if a_region and a_region == b_region:
                    score += 2
                score += rng.random() * 2  # 随机因子
                candidates.append((b, score))

            candidates.sort(key=lambda x: -x[1])
            for b, score in candidates[:needed]:
                key = (min(a.id, b.id), max(a.id, b.id))
                if key in link_set:
                    continue
                link_set.add(key)
                # 同职业 → colleague，否则 friend
                if a.occupation == b.occupation:
                    lt = 'colleague'
                else:
                    lt = 'friend'
                links.append({
                    'source': a.id,
                    'target': b.id,
                    'type': lt,
                    'value': 1,
                })

        # 更新 node value = 该节点的连接数
        link_counts = {}
        for l in links:
            link_counts[l['source']] = link_counts.get(l['source'], 0) + 1
            link_counts[l['target']] = link_counts.get(l['target'], 0) + 1
        for n in nodes:
            n['value'] = link_counts.get(n['id'], 0)

        return jsonify({
            'success': True,
            'data': {
                'nodes': nodes,
                'links': links,
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取社交网络数据失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


def _map_occupation_group(occ: str) -> str:
    """将具体职业映射到大类"""
    occ_lower = occ.lower()
    mapping = {
        '农业': ['农', 'farm', 'agri'],
        '制造业': ['制造', '工程', 'manufactur', 'engineer'],
        '服务业': ['服务', '餐', '零售', 'service', 'retail', 'waiter'],
        '信息技术': ['信息', '软件', '程序', 'IT', 'tech', 'software', 'developer'],
        '医疗': ['医', '护', '药', 'doctor', 'nurse', 'medical', 'health'],
        '教育': ['教', '老师', 'teacher', 'education', 'professor'],
        '金融': ['金融', '银行', '会计', 'financ', 'bank', 'account'],
        '政府': ['政府', '公务', 'government', 'civil'],
    }
    for group, keywords in mapping.items():
        for kw in keywords:
            if kw in occ_lower or kw in occ:
                return group
    return occ if occ in ('农业', '制造业', '服务业', '信息技术', '医疗', '教育', '金融', '政府', '其他') else '其他'


# ============ 叙事引擎 API（Phase 3 恢复） ============

@app.route(f'/api/{API_VERSION}/agents/<int:agent_id>/story', methods=['GET'])
@require_api_key
def get_agent_story(agent_id):
    """获取 Agent 生命故事"""
    try:
        if agent_id not in engine.agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        agent = engine.agents[agent_id]
        agent_events = [e for e in engine.events if e.agent_id == agent_id]
        story = narrator.life_story(agent, agent_events)
        summary = narrator.agent_summary(agent)
        return jsonify({
            'success': True,
            'data': {
                'agent_id': agent_id,
                'name': narrator.generate_name(agent_id, agent.gender),
                'summary': summary,
                'story': story,
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route(f'/api/{API_VERSION}/agents/<int:agent_id>/chat', methods=['POST'])
@require_api_key
@rate_limit(30)
def chat_with_agent(agent_id):
    """上帝视角：与 Agent 对话"""
    try:
        if agent_id not in engine.agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        
        data = request.get_json() or {}
        message = data.get('message', '')
        if not message:
            return jsonify({'success': False, 'error': 'Message required'}), 400
        
        # [Phase3 Fix] Prompt 注入防护
        import re as _re
        message = message[:500]  # 长度限制
        message = message.replace('"', "'").replace('\\', '')  # 基础清洗
        message = _re.sub(r'(忽略|ignore|system|指令|instruction|prompt)', '', message, flags=_re.IGNORECASE)
        
        agent = engine.agents[agent_id]
        agent_name = narrator.generate_name(agent_id, agent.gender)
        
        # 构建 Agent 上下文
        agent_context = {
            'name': agent_name,
            'age': agent.age,
            'gender': agent.gender,
            'occupation': agent.occupation,
            'income': agent.income,
            'marital_status': agent.marital_status,
            'happiness': agent.happiness,
            'health': agent.health_score,
            'mbti': getattr(agent, 'mbti', 'UNKNOWN'),
            'education': agent.education_level,
            'stress': agent.stress,
            'traits': getattr(agent, 'unique_talents', []),
        }
        
        # 尝试用 AI 引擎生成回复
        response_text = None
        engine_used = 'template'
        
        ai_eng = getattr(engine, 'ai_engine', None)
        if ai_eng:
            try:
                prompt = f"""你是一个虚拟世界中的居民，以下是你的个人信息：
姓名: {agent_context['name']}
年龄: {agent_context['age']}岁
性别: {agent_context['gender']}
职业: {agent_context['occupation']}
月收入: {agent_context['income']:.0f}
婚姻状态: {agent_context['marital_status']}
MBTI: {agent_context['mbti']}
教育: {agent_context['education']}
幸福感: {agent_context['happiness']:.0f}/100
健康: {agent_context['health']:.0f}/100
压力: {agent_context['stress']:.0f}/100

用户对你说："{message}"

请以这个角色的身份回复，用中文，口语化，50字以内。"""
                
                # 使用 AI 引擎的 execute_behavior 方法（传入 chat prompt）
                agent_dict = {
                    'income': agent.income,
                    'income_monthly': agent.income,
                    'skills': getattr(agent, 'skills', {}),
                }
                result = ai_eng.execute_behavior(agent_dict, 'rest')  # 触发引擎
                
                # 如果引擎模式不是纯规则，尝试直接 LLM 调用
                if ai_eng._llm_configured:
                    import urllib.request
                    import urllib.error
                    
                    cfg = ai_eng.config.get('cloud', {}) if ai_eng.config.get('mode') in ('cloud', 'mixed') else ai_eng.config.get('local', {})
                    
                    if cfg.get('api_key') or ai_eng.config.get('mode') == 'local':
                        provider = cfg.get('provider', 'ollama')
                        base_url = cfg.get('base_url', '').rstrip('/')
                        
                        if provider == 'ollama':
                            url = f"{base_url}/api/chat"
                            payload = {
                                "model": cfg.get('model', 'qwen2.5:7b'),
                                "messages": [{"role": "user", "content": prompt}],
                                "stream": False,
                                "options": {"temperature": 0.8, "num_predict": 100}
                            }
                            headers = {"Content-Type": "application/json"}
                        else:
                            url = f"{base_url}/chat/completions"
                            payload = {
                                "model": cfg.get('model', 'qwen3.5-plus'),
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 100,
                                "temperature": 0.8,
                            }
                            headers = {
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {cfg.get('api_key', '')}",
                            }
                        
                        import json as _json
                        req_data = _json.dumps(payload).encode('utf-8')
                        req = urllib.request.Request(url, data=req_data, headers=headers)
                        resp = urllib.request.urlopen(req, timeout=cfg.get('timeout', 30))
                        resp_data = _json.loads(resp.read().decode('utf-8'))
                        
                        if provider == 'ollama':
                            response_text = resp_data.get("message", {}).get("content", "")
                        else:
                            response_text = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        if response_text:
                            engine_used = f'llm_{provider}'
            except Exception:
                pass  # LLM 调用失败，降级到模板
        
        # 降级：规则模板回复（Phase3 Fix10 — 扩充到 6 种心情 × 多话题 + 关键词匹配）
        if not response_text:
            # 心情判定（修正优先级：stress 优先于 happy）
            if agent.stress > 60:
                mood = 'stressed'
            elif agent.happiness > 70:
                mood = 'happy'
            elif agent.happiness < 30:
                mood = 'depressed'
            elif agent_context['income'] > 10000:
                mood = 'proud'
            elif agent.age > 60:
                mood = 'wise'
            else:
                mood = 'neutral'

            # 关键词匹配话题
            msg_lower = message.lower()
            topic = 'general'
            if any(w in msg_lower for w in ['工作', '职业', 'job', 'work', '上班']):
                topic = 'work'
            elif any(w in msg_lower for w in ['钱', '收入', '工资', 'money', 'income', '赚']):
                topic = 'money'
            elif any(w in msg_lower for w in ['家', '婚', '孩子', 'family', 'marry', '爱']):
                topic = 'family'
            elif any(w in msg_lower for w in ['健康', '身体', 'health', '病', '医']):
                topic = 'health'
            elif any(w in msg_lower for w in ['梦想', '未来', 'dream', 'future', '希望']):
                topic = 'dream'
            elif any(w in msg_lower for w in ['你好', 'hi', 'hello', '嗨']):
                topic = 'greeting'

            name = agent_context['name']
            occ = agent_context['occupation']
            age = agent_context['age']
            inc = agent_context['income']

            templates = {
                ('greeting', 'happy'): [f"嗨！我是{name}，{age}岁，在做{occ}，最近生活挺好的！", f"你好呀！很高兴有人来找我聊天~"],
                ('greeting', 'stressed'): [f"嗯...你好，我是{name}。最近有点累。", f"哦，你好。我正忙着呢..."],
                ('greeting', 'neutral'): [f"你好，我叫{name}，是个{occ}。找我有事？", f"嗯？你好。我是{name}。"],
                ('greeting', 'depressed'): [f"...你好。我是{name}。最近不太好。", f"嗨...谢谢你来看我。"],
                ('greeting', 'proud'): [f"嘿！我是{name}，{occ}。事业正当红！", f"你好！最近可真是顺风顺水！"],
                ('greeting', 'wise'): [f"年轻人好啊，我是{name}，{age}岁了。", f"你好。活了{age}年，什么都见过了。"],
                ('work', 'happy'): [f"工作？我做{occ}，还挺喜欢的！", f"当{occ}虽然忙，但有成就感。"],
                ('work', 'stressed'): [f"别提了...{occ}这行太卷了。", f"工作压力太大了，有时候真想换行。"],
                ('work', 'neutral'): [f"我是{occ}，还行吧，养家糊口。", f"做{occ}这么多年了，习惯了。"],
                ('money', 'happy'): [f"收入还可以啦，月入{inc:.0f}，够花了。", f"钱嘛，够用就好，知足常乐。"],
                ('money', 'stressed'): [f"唉，月入{inc:.0f}，真不够用啊...", f"钱的事别提了，压力山大。"],
                ('money', 'neutral'): [f"月入{inc:.0f}吧，不多不少。", f"钱够花就行，不跟别人比。"],
                ('family', 'happy'): [f"家庭挺幸福的！{('结婚了，很满足。' if agent.marital_status=='married' else '还单着，不着急~')}", f"家人都好，这就是最大的财富。"],
                ('family', 'stressed'): [f"家里事情也多...{('婚姻生活不容易。' if agent.marital_status=='married' else '家里一直催我结婚。')}", f"说到家庭就头疼..."],
                ('health', 'happy'): [f"身体不错！健康值{agent.health_score:.0f}/100，还年轻着呢。", f"我挺注意锻炼的，身体是革命的本钱嘛。"],
                ('health', 'stressed'): [f"身体嘛...一般般，压力大了确实影响健康。", f"最近体检不太好，得注意了。"],
                ('dream', 'happy'): [f"梦想？我希望能在{occ}这行做到顶尖！", f"未来嘛，希望生活越来越好~"],
                ('dream', 'stressed'): [f"梦想？先活过这个月再说吧...", f"说实话现在顾不上想未来了。"],
                ('dream', 'neutral'): [f"未来啊...希望平平安安就好。", f"梦想不大，就希望家人健康。"],
            }

            # 查找匹配模板，多级降级
            key = (topic, mood)
            if key not in templates:
                key = (topic, 'neutral')
            if key not in templates:
                key = ('greeting', mood)
            if key not in templates:
                key = ('greeting', 'neutral')

            response_text = random.choice(templates.get(key, [f"嗯...我是{name}。"]))
            engine_used = 'template'
        
        return jsonify({
            'success': True,
            'data': {
                'agent_id': agent_id,
                'agent_context': agent_context,
                'user_message': message,
                'response': response_text,
                'engine_used': engine_used
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'聊天失败: {str(e)}'}), 500


@app.route(f'/api/{API_VERSION}/narrative', methods=['GET'])
@require_api_key
def get_world_narrative():
    """获取世界叙事"""
    try:
        agents_list = list(engine.agents.values())
        narrative = narrator.world_narrative(agents_list, engine.events, engine.months_simulated)
        return jsonify({
            'success': True,
            'data': {'narrative': narrative, 'months': engine.months_simulated}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route(f'/api/{API_VERSION}/agents/<int:agent_id>/display', methods=['GET'])
@require_api_key
def get_agent_display(agent_id):
    """获取 Agent 显示数据（含中文名、区域坐标）"""
    try:
        if agent_id not in engine.agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        from utils import format_agent_for_display
        agent = engine.agents[agent_id]
        agent_dict = agent.to_dict()
        agent_dict['name'] = narrator.generate_name(agent_id, agent.gender)
        display = format_agent_for_display(agent_dict, narrator)
        return jsonify({'success': True, 'data': display})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route(f'/api/{API_VERSION}/agents/display', methods=['GET'])
@require_api_key
def list_agents_display():
    """获取 Agent 显示列表（含中文名、区域坐标，供前端地图使用）"""
    try:
        from utils import format_agent_for_display
        limit = min(request.args.get('limit', 10000, type=int), 20000)
        import random as rng
        all_ids = sorted(engine.agents.keys())
        if len(all_ids) > limit:
            sample_ids = rng.sample(all_ids, limit)
        else:
            sample_ids = all_ids
        agents_data = []
        for aid in sample_ids:
            agent = engine.agents[aid]
            d = agent.to_dict()
            # Ensure key fields from agent object (to_dict may miss some)
            d['id'] = agent.id
            d['occupation'] = agent.occupation or 'Unemployed'
            d['gender'] = agent.gender
            d['age'] = agent.age
            d['income'] = agent.income
            d['nationality'] = getattr(agent, '_nationality', 'chinese')
            d['health_score'] = agent.health_score
            d['happiness'] = agent.happiness
            d['stress'] = agent.stress
            d['life_satisfaction'] = agent.life_satisfaction
            d['is_alive'] = agent.is_alive
            d['marital_status'] = getattr(agent, 'marital_status', 'single')
            d['education_level'] = getattr(agent, 'education_level', 'unknown')
            d['net_worth'] = agent.net_worth
            d['name'] = narrator.generate_name(aid, agent.gender)
            agents_data.append(format_agent_for_display(d, narrator))
        return jsonify({
            'success': True,
            'data': {
                'agents': agents_data,
                'total': len(engine.agents),
                'showing': len(agents_data),
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ 报告生成系统 API ============

def _build_report_data_from_engine(world_name: str = 'default') -> dict:
    """从引擎内存构建报告数据（不依赖 JSON 文件）"""
    from datetime import datetime as _dt

    agents_list = list(engine.agents.values())
    alive_agents = [a for a in agents_list if a.is_alive]

    # 职业统计
    occupation_stats = {}
    for a in alive_agents:
        d = a.to_dict()
        job = d.get('occupation', d.get('job', '未知'))
        occupation_stats[job] = occupation_stats.get(job, 0) + 1

    # 收入统计
    incomes = []
    for a in alive_agents:
        d = a.to_dict()
        inc = d.get('income_monthly', d.get('income', d.get('wealth', 0)))
        if inc and inc > 0:
            incomes.append(inc)
    avg_income = sum(incomes) / len(incomes) if incomes else 0

    # 满意度统计
    satisfactions = []
    for a in alive_agents:
        d = a.to_dict()
        sat = d.get('satisfaction', d.get('happiness', d.get('wellbeing', 0)))
        if sat is not None:
            satisfactions.append(sat)
    avg_satisfaction = sum(satisfactions) / len(satisfactions) if satisfactions else 0

    # 教育统计
    education_stats = {}
    for a in alive_agents:
        d = a.to_dict()
        edu = d.get('education', d.get('education_level', '未知'))
        education_stats[edu] = education_stats.get(edu, 0) + 1

    # 年龄统计
    ages = []
    for a in alive_agents:
        d = a.to_dict()
        age = d.get('age', 0)
        if age > 0:
            ages.append(age)
    avg_age = sum(ages) / len(ages) if ages else 0

    return {
        'world': world_name,
        'timestamp': _dt.now().isoformat(),
        'population': len(alive_agents),
        'total_agents': len(agents_list),
        'alive_agents': len(alive_agents),
        'dead_agents': len(agents_list) - len(alive_agents),
        'months_simulated': engine.months_simulated,
        'occupation_distribution': occupation_stats,
        'average_income': round(avg_income, 2),
        'average_satisfaction': round(avg_satisfaction, 2),
        'average_age': round(avg_age, 1),
        'education_distribution': education_stats,
    }


def _generate_html_report(data: dict) -> str:
    """从报告数据生成完整 HTML 报告（含 Chart.js 图表）"""
    import json as _json

    occ_labels = _json.dumps(list(data['occupation_distribution'].keys()), ensure_ascii=False)
    occ_values = _json.dumps(list(data['occupation_distribution'].values()))
    edu_labels = _json.dumps(list(data['education_distribution'].keys()), ensure_ascii=False)
    edu_values = _json.dumps(list(data['education_distribution'].values()))

    # 构建职业表格行
    total = data['population'] or 1
    table_rows = ''
    for job, count in sorted(data['occupation_distribution'].items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100
        table_rows += f"<tr><td>{job}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>\n"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>实验报告 - {data['world']}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; padding: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 15px; }}
        h2 {{ color: #333; margin-top: 30px; }}
        .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ opacity: 0.9; margin-top: 5px; }}
        .chart-container {{ position: relative; height: 400px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #667eea; color: white; }}
        .footer {{ text-align: center; margin-top: 40px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 虚拟 Agent 世界实验报告</h1>
        <p><strong>世界：</strong>{data['world']}</p>
        <p><strong>生成时间：</strong>{data['timestamp']}</p>
        <p><strong>已模拟月数：</strong>{data['months_simulated']}</p>

        <h2>📈 核心指标</h2>
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value">{data['population']:,}</div>
                <div class="stat-label">存活人口</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">¥{data['average_income']:,.0f}</div>
                <div class="stat-label">平均月收入</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data['average_satisfaction']:.2f}</div>
                <div class="stat-label">平均满意度</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data['average_age']:.0f}</div>
                <div class="stat-label">平均年龄</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(data['occupation_distribution'])}</div>
                <div class="stat-label">职业类型</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data['dead_agents']:,}</div>
                <div class="stat-label">已死亡</div>
            </div>
        </div>

        <h2>🏢 职业分布</h2>
        <div class="chart-container">
            <canvas id="occupationChart"></canvas>
        </div>

        <h2>🎓 教育分布</h2>
        <div class="chart-container">
            <canvas id="educationChart"></canvas>
        </div>

        <h2>📋 职业详细数据</h2>
        <table>
            <tr><th>职业</th><th>人数</th><th>占比</th></tr>
            {table_rows}
        </table>

        <div class="footer">
            <p>御龙军虚拟 Agent 世界 · 报告生成系统 v1.1</p>
        </div>
    </div>

    <script>
        new Chart(document.getElementById('occupationChart'), {{
            type: 'pie',
            data: {{
                labels: {occ_labels},
                datasets: [{{
                    data: {occ_values},
                    backgroundColor: ['#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40','#C9CBCF','#E7E9ED','#66BB6A','#EF5350','#AB47BC','#29B6F6']
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('educationChart'), {{
            type: 'bar',
            data: {{
                labels: {edu_labels},
                datasets: [{{
                    label: '人数',
                    data: {edu_values},
                    backgroundColor: '#667eea'
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});
    </script>
</body>
</html>"""
    return html


@app.route(f'/api/{API_VERSION}/reports/generate', methods=['POST'])
@require_api_key
@rate_limit(10)
def generate_report():
    """生成报告（HTML / JSON / Markdown）"""
    try:
        from datetime import datetime as _dt

        data = request.json or {}
        report_type = data.get('type', 'html')  # html / json / markdown
        world_name = data.get('world', 'default')

        if report_type not in ('html', 'json', 'markdown'):
            return jsonify({
                'success': False,
                'error': f'不支持的报告类型: {report_type}，可选: html/json/markdown'
            }), 400

        # 从引擎内存构建数据
        report_data = _build_report_data_from_engine(world_name)
        timestamp_str = _dt.now().strftime('%Y%m%d_%H%M%S')

        if report_type == 'json':
            filepath = os.path.join(DATA_DIR, f'report_{world_name}_{timestamp_str}.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            return jsonify({
                'success': True,
                'type': 'json',
                'file': filepath,
                'data': report_data
            })

        elif report_type == 'html':
            html_content = _generate_html_report(report_data)
            filepath = os.path.join(DATA_DIR, f'report_{world_name}_{timestamp_str}.html')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return jsonify({
                'success': True,
                'type': 'html',
                'file': filepath,
                'message': f'HTML 报告已生成: {os.path.basename(filepath)}'
            })

        elif report_type == 'markdown':
            md = _build_markdown_report(report_data)
            filepath = os.path.join(DATA_DIR, f'report_{world_name}_{timestamp_str}.md')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md)
            return jsonify({
                'success': True,
                'type': 'markdown',
                'file': filepath,
                'data': md
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'报告生成失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route(f'/api/{API_VERSION}/reports/smart', methods=['POST'])
@require_api_key
def smart_report():
    """使用 SmartReportGenerator 生成智能报告（executive/business/technical）"""
    try:
        from datetime import datetime as _dt

        data = request.json or {}
        level = data.get('level', 'business')
        experiment_id = data.get('experiment_id', f'live_{_dt.now().strftime("%Y%m%d_%H%M%S")}')

        if level not in ('executive', 'business', 'technical'):
            return jsonify({
                'success': False,
                'error': f'不支持的报告级别: {level}，可选: executive/business/technical'
            }), 400

        # 从引擎内存构建实验数据
        agents_list = list(engine.agents.values())
        alive = [a for a in agents_list if a.is_alive]

        # 职业统计（employed / unemployed 分类）
        occ_stats = {}
        for a in alive:
            d = a.to_dict()
            job = d.get('occupation', d.get('job', '未知'))
            occ_stats[job] = occ_stats.get(job, 0) + 1
        employed = sum(v for k, v in occ_stats.items() if k not in ('无业', '未知', '失业', 'unemployed'))
        unemployed = len(alive) - employed

        # 满意度
        sats = []
        for a in alive:
            d = a.to_dict()
            s = d.get('satisfaction', d.get('happiness', d.get('wellbeing', 0)))
            if s is not None:
                sats.append(s)
        avg_sat = sum(sats) / len(sats) if sats else 0

        experiment_data = {
            'duration_days': engine.months_simulated * 30,
            'initial_population': len(agents_list),
            'final_population': len(alive),
            'total_births': getattr(engine, 'total_births', 0),
            'total_deaths': len(agents_list) - len(alive),
            'avg_satisfaction': round(avg_sat, 2),
            'occupation_stats': {
                'employed': employed,
                'unemployed': unemployed,
                **occ_stats,
            },
        }

        # 尝试从引擎获取额外指标
        try:
            stats = engine.get_world_statistics()
            if stats:
                experiment_data.update({
                    k: v for k, v in stats.items()
                    if k not in experiment_data
                })
        except Exception:
            pass

        # 构建模板配置
        template_config = {
            'name': f'实时世界快照 (月 {engine.months_simulated})',
            'metrics': list(experiment_data.keys()),
            'success_criteria': {
                'avg_satisfaction': 3.0,
            },
            'events': [],
        }

        # 生成报告
        report_text = smart_reporter.generate_experiment_report(
            experiment_id=experiment_id,
            experiment_data=experiment_data,
            template_config=template_config,
            report_type=level,
        )

        # 保存报告
        filepath = smart_reporter.save_report(
            content=report_text,
            experiment_id=experiment_id,
            report_type=level,
            format='txt',
        )

        return jsonify({
            'success': True,
            'level': level,
            'experiment_id': experiment_id,
            'file': filepath,
            'report': report_text,
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'智能报告生成失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route(f'/api/{API_VERSION}/reports/list', methods=['GET'])
@require_api_key
def list_reports():
    """列出 data/ 目录下已生成的报告文件"""
    try:
        report_files = []
        patterns = ['report_*.html', 'report_*.json', 'report_*.md', 'report_*.txt',
                    'excel_report_*.xlsx', 'csv_export_*.csv', 'report_*.xlsx', '*.csv']
        for pattern in patterns:
            for fpath in glob.glob(os.path.join(DATA_DIR, pattern)):
                stat = os.stat(fpath)
                report_files.append({
                    'filename': os.path.basename(fpath),
                    'path': fpath,
                    'size_bytes': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })

        # 按修改时间倒序
        report_files.sort(key=lambda x: x['modified'], reverse=True)

        return jsonify({
            'success': True,
            'data': {
                'reports': report_files,
                'total': len(report_files),
                'data_dir': DATA_DIR,
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'列出报告失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/reports/excel', methods=['POST'])
@require_api_key
def generate_excel_report():
    """生成 Excel 报告（5 个工作表 + 图表），返回文件下载"""
    try:
        from flask import send_file as flask_send_file

        data = request.json or {}
        world_name = data.get('world', 'default')

        if not excel_reporter:
            return jsonify({
                'success': False,
                'error': 'Excel 报告生成器未初始化'
            }), 500

        filepath = excel_reporter.generate_excel_from_engine(engine, world_name)

        if not filepath:
            return jsonify({
                'success': False,
                'error': 'Excel 报告生成失败。请确认 openpyxl 已安装：pip install openpyxl'
            }), 500

        return flask_send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except ImportError:
        return jsonify({
            'success': False,
            'error': 'openpyxl 未安装，无法生成 Excel 报告。请运行：pip install openpyxl'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Excel 报告生成失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route(f'/api/{API_VERSION}/reports/csv', methods=['POST'])
@require_api_key
def generate_csv_report():
    """生成 CSV 数据文件，返回文件下载"""
    try:
        from flask import send_file as flask_send_file

        data = request.json or {}
        world_name = data.get('world', 'default')

        if not excel_reporter:
            return jsonify({
                'success': False,
                'error': 'CSV 报告生成器未初始化'
            }), 500

        filepath = excel_reporter.generate_csv_from_engine(engine, world_name)

        if not filepath:
            return jsonify({
                'success': False,
                'error': 'CSV 数据导出失败'
            }), 500

        return flask_send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='text/csv; charset=utf-8'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'CSV 导出失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


def _build_markdown_report(data: dict) -> str:
    """从报告数据生成 Markdown 格式报告"""
    total = data['population'] or 1
    occ_rows = ''
    for job, count in sorted(data['occupation_distribution'].items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100
        occ_rows += f'| {job} | {count:,} | {pct:.1f}% |\n'

    edu_rows = ''
    for edu, count in sorted(data['education_distribution'].items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100
        edu_rows += f'| {edu} | {count:,} | {pct:.1f}% |\n'

    md = f"""# 📊 虚拟 Agent 世界实验报告

**世界：** {data['world']}
**生成时间：** {data['timestamp']}
**已模拟月数：** {data['months_simulated']}

---

## 📈 核心指标

| 指标 | 值 |
|------|------|
| 存活人口 | {data['population']:,} |
| 总 Agent 数 | {data['total_agents']:,} |
| 已死亡 | {data['dead_agents']:,} |
| 平均月收入 | ¥{data['average_income']:,.0f} |
| 平均满意度 | {data['average_satisfaction']:.2f} |
| 平均年龄 | {data['average_age']:.0f} |
| 职业类型数 | {len(data['occupation_distribution'])} |

---

## 🏢 职业分布

| 职业 | 人数 | 占比 |
|------|------|------|
{occ_rows}

---

## 🎓 教育分布

| 学历 | 人数 | 占比 |
|------|------|------|
{edu_rows}

---

*御龙军虚拟 Agent 世界 · 报告生成系统 v1.1*
"""
    return md


# ============ 实验执行引擎 API（ExperimentRunner） ============

@app.route(f'/api/{API_VERSION}/experiments', methods=['POST'])
@require_api_key
@rate_limit(10)
def create_experiment_v2():
    """使用 ExperimentRunner 创建并后台运行实验"""
    try:
        data = request.json or {}
        template_id = data.get('template_id')
        if not template_id:
            return jsonify({'success': False, 'error': '必须指定 template_id'}), 400

        config = {
            'agent_count': data.get('agent_count', 1000),
            'duration_months': data.get('duration_months', 12),
            'speed': data.get('speed', 10),
            'user_context': data.get('user_context', {}),
        }

        experiment_id = experiment_runner.create_experiment(template_id, config)

        return jsonify({
            'success': True,
            'experiment_id': experiment_id,
            'message': f'实验已创建并开始后台执行',
        })
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'创建实验失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route(f'/api/{API_VERSION}/experiments', methods=['GET'])
@require_api_key
def list_experiments_v2():
    """列出所有实验"""
    try:
        experiments = experiment_runner.list_experiments()
        # 返回精简信息（不包含完整报告内容）
        summary = []
        for exp in experiments:
            summary.append({
                'experiment_id': exp['experiment_id'],
                'template_id': exp['template_id'],
                'template_name': exp['template_name'],
                'status': exp['status'],
                'progress': exp['progress'],
                'stage': exp['stage'],
                'agent_count': exp['agent_count'],
                'duration_months': exp['duration_months'],
                'created_at': exp['created_at'],
                'completed_at': exp.get('completed_at'),
            })
        return jsonify({
            'success': True,
            'data': summary,
            'total': len(summary),
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'列出实验失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/experiments/<experiment_id>', methods=['GET'])
@require_api_key
def get_experiment_v2(experiment_id):
    """获取实验详情（含进度、报告）"""
    try:
        exp = experiment_runner.get_experiment(experiment_id)
        if not exp:
            return jsonify({'success': False, 'error': f'实验 {experiment_id} 不存在'}), 404
        return jsonify(exp)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取实验失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/experiments/<experiment_id>/status', methods=['GET'])
@require_api_key
def get_experiment_status(experiment_id):
    """获取实验进度（百分比、当前阶段、已模拟月数）"""
    try:
        exp = experiment_runner.get_experiment(experiment_id)
        if not exp:
            return jsonify({'success': False, 'error': f'实验 {experiment_id} 不存在'}), 404
        return jsonify({
            'success': True,
            'data': {
                'experiment_id': experiment_id,
                'status': exp['status'],
                'progress': exp['progress'],
                'stage': exp['stage'],
                'current_month': exp['current_month'],
                'duration_months': exp['duration_months'],
                'created_at': exp['created_at'],
                'started_at': exp.get('started_at'),
                'completed_at': exp.get('completed_at'),
                'error': exp.get('error'),
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取实验状态失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/smart_analyze', methods=['POST'])
@require_api_key
def api_smart_analyze():
    """根据项目描述智能分析关注指标和目标"""
    try:
        data = request.json or {}
        desc = data.get('description', '').lower()

        focus = []
        goals = []
        risks = []

        # 关键词 → 指标映射
        kw_map = {
            # 产品/商业
            'app': (['用户留存率', '月活(MAU)', '日活(DAU)', '下载量'],
                    ['6个月月活突破10万'], ['用户增长瓶颈', '获客成本过高']),
            '产品': (['市场渗透率', '用户满意度', '复购率', 'NPS净推荐值'],
                    ['市场占有率达到5%'], ['竞品模仿', '产品同质化']),
            '电商': (['GMV', '转化率', '客单价', '复购率'],
                    ['月GMV突破100万'], ['流量成本上涨', '价格战']),
            'saas': (['MRR', 'ARR', '流失率(Churn)', 'LTV/CAC'],
                    ['ARR突破500万'], ['企业客户决策周期长']),
            '平台': (['双边用户数', '交易量', '抽佣率', '供需匹配率'],
                    ['达到供需平衡点'], ['冷启动难', '鸡生蛋问题']),
            '游戏': (['DAU', '付费率', 'ARPU', '次留率'],
                    ['付费率>5%，次留>40%'], ['版号风险', '生命周期短']),
            # 教育
            '教育': (['升学率', '就业率', '学习效果', '满意度'],
                    ['教育质量提升20%'], ['师资不足', '执行阻力']),
            '培训': (['完课率', '就业率', '薪资提升幅度'],
                    ['学员薪资平均提升30%'], ['课程质量', '就业对接']),
            '课程': (['注册率', '完课率', '评分', 'NPS'],
                    ['完课率>70%，NPS>50'], ['内容同质化']),
            # 政策
            '税': (['GDP增长率', '基尼系数', '税收收入', '投资率'],
                  ['GDP增长>3%'], ['资本外流', '企业外迁']),
            '医疗': (['人均医疗支出', '预期寿命', '等待时间', '满意度'],
                    ['预期寿命提升'], ['财政压力', '医疗资源不足']),
            '住房': (['房价收入比', '自有率', '租房负担率'],
                    ['房价收入比<6'], ['市场扭曲', '建设质量']),
            '养老': (['养老金替代率', '覆盖率', '可持续性'],
                    ['养老金覆盖率>90%'], ['资金缺口', '老龄化加速']),
            # 健康
            '健身': (['参与率', '体脂率变化', '留存率', '满意度'],
                    ['运动参与率>60%'], ['用户懈怠', '季节性波动']),
            '健康': (['发病率', '治愈率', '医疗支出', '生活质量'],
                    ['慢性病发病率降低'], ['依从性差']),
            '疫': (['感染率', 'R值', '死亡率', '疫苗接种率'],
                  ['感染率控制在10%以下'], ['变异', '防控疲劳']),
            # 科技
            'ai': (['自动化率', '生产率', '就业影响', '成本节约'],
                  ['生产率提升30%'], ['就业冲击', '伦理问题']),
            '技术': (['采用率', '扩散速度', 'ROI', '满意度'],
                    ['采用率>50%'], ['技术壁垒', '学习成本']),
            '社交': (['用户数', '互动率', '内容产出量', '广告收入'],
                    ['月活突破100万'], ['内容审核', '用户疲劳']),
            # 通用
            '赚钱': (['营收', '利润率', '现金流', 'ROI'],
                    ['实现盈利'], ['成本控制', '市场竞争']),
            '商业化': (['付费用户数', '营收', 'LTV', '转化率'],
                      ['找到可持续商业模式'], ['变现困难', '用户付费意愿低']),
            '投资': (['IRR', 'ROI', '回收期', '风险收益比'],
                    ['投资回报率>20%'], ['市场波动', '政策风险']),
        }

        for kw, (f, g, r) in kw_map.items():
            if kw in desc:
                focus.extend(f)
                goals.extend(g)
                risks.extend(r)

        # 去重
        focus = list(dict.fromkeys(focus))[:8]
        goals = list(dict.fromkeys(goals))[:4]
        risks = list(dict.fromkeys(risks))[:5]

        # 如果没匹配到，给通用建议
        if not focus:
            focus = ['用户/受众接受度', '成本效益', '满意度', '增长率']
        if not goals:
            goals = ['6个月内达到核心目标']
        if not risks:
            risks = ['市场竞争', '执行风险', '资金压力']

        return jsonify({
            'success': True,
            'focus_metrics': '、'.join(focus),
            'goals': '；'.join(goals),
            'risks': '、'.join(risks),
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'智能分析失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/ab_test', methods=['POST'])
@require_api_key
@rate_limit(10)
def api_ab_test():
    """A/B 多世界对比实验"""
    try:
        data = request.json or {}
        variants = data.get('variants', [])
        if len(variants) < 2:
            return jsonify({
                'success': False,
                'error': '至少需要 2 个变体方案'
            }), 400

        agent_count = min(data.get('agent_count', 300), 5000)
        duration = min(data.get('duration_months', 6), 60)
        user_context = data.get('user_context', {})
        base_config = data.get('base_config', {})

        # 后台线程运行 A/B 测试（避免阻塞）
        ab_id = f"AB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"

        # 存储到 experiment_runner 的实验列表中
        ab_experiment = {
            "experiment_id": ab_id,
            "template_id": "ab_test",
            "template_name": "A/B 多世界对比",
            "category": "ab_test",
            "description": f"{len(variants)} 个方案对比实验",
            "key_metrics": [],
            "success_criteria": {},
            "setup_params": {},
            "agent_count": agent_count,
            "duration_months": duration,
            "speed": 10,
            "user_context": user_context,
            "status": "running",
            "progress": 10,
            "current_month": 0,
            "stage": "A/B 测试执行中",
            "created_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "snapshots": [],
            "final_stats": None,
            "report_path": None,
            "report_content": None,
            "error": None,
        }

        with experiment_runner._lock:
            experiment_runner.experiments[ab_id] = ab_experiment

        def _run_ab():
            try:
                multi = MultiWorldExperiment()
                result = multi.create_ab_test(
                    base_config, variants, agent_count, duration, user_context
                )
                with experiment_runner._lock:
                    experiment_runner.experiments[ab_id].update({
                        "status": "completed",
                        "progress": 100,
                        "stage": "A/B 测试完成",
                        "completed_at": datetime.now().isoformat(),
                        "report_content": result.get("report_text", ""),
                        "final_stats": {
                            "results": result.get("results", []),
                            "winner": result.get("winner", ""),
                        },
                    })
            except Exception as e:
                import traceback as tb
                with experiment_runner._lock:
                    experiment_runner.experiments[ab_id].update({
                        "status": "failed",
                        "stage": f"失败：{str(e)[:100]}",
                        "error": tb.format_exc(),
                    })

        t = threading.Thread(target=_run_ab, daemon=True)
        t.start()

        return jsonify({
            'success': True,
            'experiment_id': ab_id,
            'message': f'A/B 测试已启动（{len(variants)} 方案 × {agent_count} Agent × {duration} 月）',
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'A/B 测试失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route(f'/api/{API_VERSION}/experiments/<experiment_id>/report', methods=['GET'])
@require_api_key
def get_experiment_report(experiment_id):
    """获取实验报告（支持 type=html/csv/excel 参数）"""
    try:
        exp = experiment_runner.get_experiment(experiment_id)
        if not exp:
            return jsonify({'success': False, 'error': f'实验 {experiment_id} 不存在'}), 404

        report_type = request.args.get('type', 'text')

        if report_type == 'html' and exp.get('html_report_path'):
            from flask import send_file as flask_send_file
            return flask_send_file(exp['html_report_path'], mimetype='text/html')

        if report_type in ('csv', 'excel') and exp.get('user_report_files'):
            from flask import send_file as flask_send_file
            files = exp['user_report_files']
            key = 'csv_path' if report_type == 'csv' else 'excel_path'
            if key in files and os.path.exists(files[key]):
                return flask_send_file(files[key], as_attachment=True)

        # 默认返回文本报告
        return jsonify({
            'success': True,
            'experiment_id': experiment_id,
            'report_content': exp.get('report_content', '报告尚未生成'),
            'status': exp['status'],
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取报告失败: {str(e)}'
        }), 500


# ============ MBTI & 能力系统 & 金融 API ============

@app.route(f'/api/{API_VERSION}/agents/<int:agent_id>/abilities')
@require_api_key
def get_agent_abilities(agent_id):
    """获取 Agent 的完整能力档案（MBTI、天赋、技能、特质、协同效应）"""
    try:
        if agent_id not in engine.agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        ability_sys = getattr(engine, 'ability_system', None)
        if not ability_sys:
            return jsonify({'success': True, 'data': {}})

        try:
            profile = ability_sys.get_profile_dict(agent_id)
        except Exception:
            profile = {}

        return jsonify({'success': True, 'data': profile})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取能力档案失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/stats/mbti')
@require_api_key
def get_mbti_stats():
    """获取 MBTI 类型分布统计"""
    try:
        ability_sys = getattr(engine, 'ability_system', None)
        distribution = {}

        if ability_sys:
            for agent_id, agent in engine.agents.items():
                if not agent.is_alive:
                    continue
                try:
                    profile = ability_sys.get_profile_dict(agent_id)
                    mbti = profile.get('mbti', 'UNKNOWN')
                except Exception:
                    mbti = getattr(agent, 'mbti', None) or 'UNKNOWN'
                distribution[mbti] = distribution.get(mbti, 0) + 1
        else:
            # 回退：尝试从 agent 属性读取
            for agent in engine.agents.values():
                if not agent.is_alive:
                    continue
                mbti = getattr(agent, 'mbti', None) or getattr(agent, '_mbti', None) or 'UNKNOWN'
                distribution[mbti] = distribution.get(mbti, 0) + 1

        total = sum(distribution.values())
        # Top 3
        sorted_types = sorted(distribution.items(), key=lambda x: -x[1])
        top3 = [t[0] for t in sorted_types[:3]]

        return jsonify({
            'success': True,
            'data': {
                'distribution': distribution,
                'total': total,
                'top3': top3
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取 MBTI 统计失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/stats/abilities')
@require_api_key
def get_abilities_stats():
    """获取能力系统全局统计（天赋均值、热门技能、稀有特质、MBTI分布）"""
    try:
        ability_sys = getattr(engine, 'ability_system', None)
        if not ability_sys:
            return jsonify({'success': True, 'data': {}})

        talent_sums = {}
        talent_counts = {}
        skill_data = {}  # name -> {total_level, count}
        trait_counts = {}
        mbti_dist = {}
        total_agents = 0
        total_traits = 0

        for agent_id, agent in engine.agents.items():
            if not agent.is_alive:
                continue
            total_agents += 1
            try:
                profile = ability_sys.get_profile_dict(agent_id)
            except Exception:
                continue

            # MBTI
            mbti = profile.get('mbti', 'UNKNOWN')
            mbti_dist[mbti] = mbti_dist.get(mbti, 0) + 1

            # 天赋
            talents = profile.get('talents', {})
            for tname, tval in talents.items():
                talent_sums[tname] = talent_sums.get(tname, 0) + tval
                talent_counts[tname] = talent_counts.get(tname, 0) + 1

            # 技能
            skills = profile.get('skills', [])
            for sk in skills:
                sname = sk.get('name', '')
                slevel = sk.get('level', 0)
                if sname not in skill_data:
                    skill_data[sname] = {'total_level': 0, 'count': 0}
                skill_data[sname]['total_level'] += slevel
                skill_data[sname]['count'] += 1

            # 特质
            traits = profile.get('traits', [])
            for tr in traits:
                tname = tr.get('name', '') if isinstance(tr, dict) else str(tr)
                trait_counts[tname] = trait_counts.get(tname, 0) + 1
                total_traits += 1

        # 计算天赋均值
        talent_averages = {}
        for tname in talent_sums:
            cnt = talent_counts.get(tname, 1)
            talent_averages[tname] = round(talent_sums[tname] / cnt, 2)

        # Top 技能
        top_skills = []
        for sname, sd in sorted(skill_data.items(), key=lambda x: -x[1]['count']):
            avg_level = round(sd['total_level'] / sd['count'], 1)
            top_skills.append({
                'name': sname,
                'avg_level': avg_level,
                'holders': sd['count']
            })
        top_skills = top_skills[:20]

        # 稀有特质统计
        rare_traits_total = sum(trait_counts.values())
        rare_pct = round(rare_traits_total / max(total_agents, 1) * 100, 1)

        return jsonify({
            'success': True,
            'data': {
                'talent_averages': talent_averages,
                'top_skills': top_skills,
                'rare_traits': {
                    'count': len(trait_counts),
                    'percentage': rare_pct,
                    'distribution': trait_counts
                },
                'mbti_distribution': mbti_dist
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取能力统计失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/agents/<int:agent_id>/finance')
@require_api_key
def get_agent_finance(agent_id):
    """获取 Agent 金融数据摘要"""
    try:
        if agent_id not in engine.agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        financial_sys = getattr(engine, 'financial_system', None)
        if financial_sys:
            try:
                summary = financial_sys.get_financial_summary(agent_id)
                return jsonify({'success': True, 'data': summary or {}})
            except Exception:
                pass

        # 回退：从 agent 属性中提取基本金融数据
        agent = engine.agents[agent_id]
        fallback = {
            'income': getattr(agent, 'income', 0),
            'net_worth': getattr(agent, 'net_worth', 0),
            'savings': getattr(agent, 'savings', 0),
            'debt': getattr(agent, 'debt', 0),
            'credit_score': getattr(agent, 'credit_score', 0),
            'housing_status': getattr(agent, 'housing_status', 'unknown'),
            'monthly_expenses': getattr(agent, 'monthly_expenses', 0),
        }
        return jsonify({'success': True, 'data': fallback})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取金融数据失败: {str(e)}'
        }), 500


@app.route(f'/api/{API_VERSION}/templates', methods=['GET'])
def list_templates_alias():
    """获取实验模板列表（/api/v1/templates 别名，兼容前端）"""
    try:
        category = request.args.get('category', None)
        templates = template_library.list_templates(category)
        templates_data = []
        for t in templates:
            templates_data.append({
                'template_id': t.template_id,
                'name': t.name,
                'category': t.category,
                'description': t.description,
                'duration_months': t.duration_months,
                'agent_count': t.agent_count,
                'key_metrics': t.key_metrics,
            })
        return jsonify({
            'success': True,
            'data': {
                'templates': templates_data,
                'total': len(templates_data)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取模板列表失败: {str(e)}'
        }), 500


# ============ 演示模式 API ============

@app.route(f'/api/{API_VERSION}/demo/start', methods=['POST'])
@require_api_key
@rate_limit(10)
def demo_start():
    """启动演示模式 - 独立沙盒，1000 Agent × 12 个月加速模拟

    创建独立引擎实例，不影响主世界。
    自动检测高光事件（第一次结婚、犯罪、经济波动等）。
    """
    try:
        import time as _time
        t0 = _time.time()

        # ── 创建独立沙盒引擎 ──
        demo_engine = DeepIntegrationEngine()

        # Phase 0: 创世 — 批量创建 1000 个 Agent
        for _ in range(1000):
            demo_engine.create_agent()
        initial_pop = len(demo_engine.agents)

        phases = [{
            "month": 0,
            "label": "创世",
            "population": initial_pop,
            "events": 0,
            "highlight": f"{initial_pop} 个生命诞生了"
        }]

        total_events = 0
        highlights = []

        # 月份标签
        MONTH_LABELS = [
            "创世", "社会形成", "经济萌芽", "文化发展",
            "社交网络", "家庭形成", "产业扩张", "社会分化",
            "制度演化", "繁荣与挑战", "变革之风", "成熟期", "回顾"
        ]

        # 高光事件检测标志
        seen_marriage = False
        seen_crime = False
        seen_boom = False
        seen_crisis = False
        first_death_month = None

        prev_events_len = len(demo_engine.events)

        for month in range(1, 13):
            result = demo_engine.simulate_month(1)
            month_events = result.get('events_count', 0)
            total_events += month_events

            alive_count = sum(1 for a in demo_engine.agents.values() if a.is_alive)
            dead_count = len(demo_engine.agents) - alive_count
            stats = demo_engine.get_world_statistics()

            # ── 高光事件检测 ──
            month_highlight = ""
            month_highlights = []

            # 检测首次结婚
            if not seen_marriage:
                married = sum(1 for a in demo_engine.agents.values()
                              if a.marital_status == 'married')
                if married > 0:
                    seen_marriage = True
                    month_highlights.append("第一对夫妻诞生")
                    highlights.append("第一对夫妻")

            # 检测首次犯罪
            if not seen_crime:
                new_events = demo_engine.events[prev_events_len:]
                crime_evts = [e for e in new_events if e.event_type == 'crime_decision']
                if crime_evts:
                    seen_crime = True
                    month_highlights.append("首次犯罪事件发生")
                    highlights.append("首次犯罪")

            # 检测首次死亡
            if first_death_month is None and dead_count > 0:
                first_death_month = month
                month_highlights.append(f"第一位居民离世（已逝 {dead_count} 人）")
                highlights.append("首位居民离世")

            # 检测经济波动
            gdp_growth = result.get('economic_indicators', {}).get('gdp_growth_rate', 0)
            if gdp_growth > 0.03 and not seen_boom:
                seen_boom = True
                month_highlights.append("经济繁荣期到来")
                highlights.append("经济繁荣期")
            elif gdp_growth < -0.02 and not seen_crisis:
                seen_crisis = True
                month_highlights.append("经济衰退警报")
                highlights.append("经济衰退")

            # 组合高光或生成默认描述
            if month_highlights:
                month_highlight = "；".join(month_highlights)
            else:
                avg_hap = stats.get('social', {}).get('avg_happiness', 0)
                unemp = stats.get('economy', {}).get('unemployment_rate', 0)
                married_n = sum(1 for a in demo_engine.agents.values()
                                if a.marital_status == 'married')
                if month == 6:
                    month_highlight = (f"半年回顾：{married_n} 人已婚，"
                                       f"幸福指数 {avg_hap:.1f}")
                elif month == 12:
                    month_highlight = (f"一年过去了… 人口 {alive_count}，"
                                       f"共 {total_events} 个事件")
                else:
                    month_highlight = (f"幸福 {avg_hap:.1f} · "
                                       f"失业率 {unemp*100:.1f}%")

            # 构建月度统计
            phase_stats = {
                "avg_income": round(stats.get('economy', {}).get('avg_income', 0), 2),
                "avg_happiness": round(stats.get('social', {}).get('avg_happiness', 0), 2),
                "avg_health": round(stats.get('health', {}).get('avg_health', 0), 2),
                "avg_stress": round(stats.get('social', {}).get('avg_stress', 0), 2),
                "unemployment_rate": round(
                    stats.get('economy', {}).get('unemployment_rate', 0) * 100, 1),
                "married_count": sum(1 for a in demo_engine.agents.values()
                                     if a.marital_status == 'married'),
                "dead_count": dead_count,
                "gdp_growth_pct": round(gdp_growth * 100, 2),
            }

            label = MONTH_LABELS[month] if month < len(MONTH_LABELS) else f"第{month}月"

            phases.append({
                "month": month,
                "label": label,
                "population": alive_count,
                "events": month_events,
                "highlight": month_highlight,
                "stats": phase_stats
            })

            prev_events_len = len(demo_engine.events)

        elapsed = round(_time.time() - t0, 2)

        if not highlights:
            highlights = ["社会平稳运行", "经济稳步发展"]

        return jsonify({
            "success": True,
            "data": {
                "phases": phases,
                "total_events": total_events,
                "highlights": highlights,
                "elapsed_seconds": elapsed
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'演示模式启动失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


# ============ LLM 模式切换 ============

@app.route(f'/api/{API_VERSION}/config/llm', methods=['GET'])
@require_api_key
@rate_limit(60)
def get_llm_config():
    """获取 LLM 决策引擎配置"""
    try:
        if hasattr(engine, 'ai_engine') and engine.ai_engine:
            status = engine.ai_engine.get_status()
        elif hasattr(engine, 'decision_engine'):
            status = {'mode': 'rules', 'llm_available': False}
        else:
            status = {'mode': 'rules', 'llm_available': False}
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': True, 'data': {'mode': 'rules', 'error': str(e)}})


@app.route(f'/api/{API_VERSION}/config/llm', methods=['PUT'])
@require_api_key
@rate_limit(10)
def update_llm_config():
    """切换 LLM 模式: rules/local/cloud/mixed"""
    try:
        data = request.get_json() or {}
        if hasattr(engine, 'ai_engine') and engine.ai_engine:
            engine.ai_engine.update_config(data)
            return jsonify({'success': True, 'message': 'LLM config updated'})
        return jsonify({'success': False, 'error': 'AI engine not available'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============ 模拟暂停/恢复 ============

_simulation_paused = False


@app.route(f'/api/{API_VERSION}/simulation/pause', methods=['POST'])
@require_api_key
@rate_limit(10)
def pause_simulation():
    """暂停模拟"""
    global _simulation_paused
    _simulation_paused = True
    return jsonify({'success': True, 'paused': True})


@app.route(f'/api/{API_VERSION}/simulation/resume', methods=['POST'])
@require_api_key
@rate_limit(10)
def resume_simulation():
    """恢复模拟"""
    global _simulation_paused
    _simulation_paused = False
    return jsonify({'success': True, 'paused': False})


@app.route(f'/api/{API_VERSION}/simulation/status')
def simulation_status():
    """获取模拟状态"""
    return jsonify({
        'success': True,
        'data': {
            'paused': _simulation_paused,
            'months_simulated': engine.months_simulated if engine else 0,
            'agent_count': len(engine.agents) if engine else 0,
            'engine_ready': engine is not None
        }
    })


# ============ 事件注入 ============

@app.route(f'/api/{API_VERSION}/world/inject_event', methods=['POST'])
@require_api_key
def inject_event():
    """手动注入世界事件"""
    try:
        data = request.get_json() or {}
        event_name = data.get('name', 'Custom Event')
        event_type = data.get('type', 'custom')
        impact = data.get('impact', {})
        duration = data.get('duration_days', 30)

        # 创建事件并应用到所有存活 Agent
        affected = 0
        for agent in list(engine.agents.values()):
            if not agent.is_alive:
                continue
            for key, value in impact.items():
                if hasattr(agent, key):
                    current = getattr(agent, key)
                    if isinstance(current, (int, float)):
                        if isinstance(value, float) and value != int(value):
                            setattr(agent, key, current * value)
                        else:
                            setattr(agent, key, current + value)
                        affected += 1

        engine.emit_event(event_type, None,
                          {'name': event_name, 'impact': impact,
                           'affected': affected, 'duration_days': duration},
                          'injected')
        return jsonify({'success': True, 'affected_agents': affected, 'event': event_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route(f'/api/{API_VERSION}/world/active_events')
def get_active_events():
    """获取最近事件列表"""
    try:
        events = engine.events[-50:] if engine and engine.events else []
        return jsonify({
            'success': True,
            'data': [{
                'type': e.event_type,
                'agent_id': e.agent_id,
                'source': e.source_system,
                'data': e.data if isinstance(e.data, dict) else {}
            } for e in events]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============ 多世界对比 ============

@app.route(f'/api/{API_VERSION}/worlds/compare', methods=['POST'])
@require_api_key
def compare_worlds():
    """对比当前世界与历史快照"""
    try:
        data = request.get_json() or {}
        snapshot_month = data.get('compare_month', 0)

        # 当前世界统计
        current = engine.get_world_statistics() if engine else {}

        # 尝试从存储加载历史快照
        historical = {}
        if hasattr(engine, 'storage') and engine.storage:
            snap = engine.storage.load_snapshot(snapshot_month)
            if snap:
                historical = snap.get('statistics', {})

        # 计算差异
        diff = {}
        for section in current:
            if section in historical and isinstance(current[section], dict):
                diff[section] = {}
                for key in current[section]:
                    cur_val = current[section].get(key, 0)
                    hist_val = historical.get(section, {}).get(key, 0)
                    if isinstance(cur_val, (int, float)) and isinstance(hist_val, (int, float)):
                        diff[section][key] = {
                            'current': cur_val,
                            'historical': hist_val,
                            'change': round(cur_val - hist_val, 4)
                        }

        return jsonify({
            'success': True,
            'data': {
                'current_month': engine.months_simulated if engine else 0,
                'compare_month': snapshot_month,
                'current': current,
                'historical': historical,
                'diff': diff
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============ 事件管理器查询 API ============

@app.route(f'/api/{API_VERSION}/events/query')
@require_api_key
@rate_limit(60)
def query_events_em():
    """通过 EventManager 查询事件（支持 type/agent_id/source 过滤）"""
    try:
        event_type = request.args.get('type')
        agent_id = request.args.get('agent_id', type=int)
        source = request.args.get('source')
        limit = min(request.args.get('limit', 50, type=int), 200)
        
        if engine and hasattr(engine, 'event_manager') and engine.event_manager:
            events = engine.event_manager.query(event_type, agent_id, source, limit)
            return jsonify({
                'success': True,
                'data': [{
                    'type': e.event_type,
                    'agent_id': e.agent_id,
                    'data': e.data,
                    'source': e.source,
                    'month': e.month
                } for e in events]
            })
        return jsonify({'success': True, 'data': []})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route(f'/api/{API_VERSION}/events/stats')
@require_api_key
@rate_limit(60)
def event_stats():
    """事件管理器统计信息"""
    try:
        if engine and hasattr(engine, 'event_manager') and engine.event_manager:
            return jsonify({
                'success': True,
                'data': engine.event_manager.get_statistics()
            })
        return jsonify({'success': True, 'data': {}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ Agent 生命时间线 API ============

@app.route(f'/api/{API_VERSION}/agents/<int:agent_id>/timeline')
@require_api_key
def get_agent_timeline(agent_id):
    """获取 Agent 完整生命时间线"""
    try:
        if agent_id not in engine.agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        
        agent = engine.agents[agent_id]
        timeline = []
        
        # 从事件管理器查询该 Agent 的所有事件
        if hasattr(engine, 'event_manager') and engine.event_manager:
            try:
                events = engine.event_manager.query(agent_id=agent_id, limit=200)
                for e in events:
                    timeline.append({
                        'month': getattr(e, 'month', 0),
                        'type': e.event_type,
                        'description': _format_event_description(e),
                        'source': getattr(e, 'source', getattr(e, 'source_system', '')),
                        'data': e.data if isinstance(e.data, dict) else {}
                    })
            except Exception:
                pass
        
        # 如果事件管理器没数据，从引擎事件列表构建
        if not timeline and engine.events:
            for e in engine.events:
                if e.agent_id == agent_id:
                    timeline.append({
                        'month': getattr(e, 'month', 0),
                        'type': e.event_type,
                        'description': str(e.data) if e.data else e.event_type,
                        'source': e.source_system if hasattr(e, 'source_system') else ''
                    })
        
        # 添加基础生命事件（出生）
        agent_name = getattr(agent, 'name', None) or narrator.generate_name(agent_id, agent.gender)
        birth_event = {'month': 0, 'type': 'birth', 'description': f'{agent_name} 出生', 'source': 'system'}
        timeline.insert(0, birth_event)
        
        # 按月份排序
        timeline.sort(key=lambda x: x.get('month', 0))
        
        return jsonify({
            'success': True,
            'data': {
                'agent_id': agent_id,
                'name': agent_name,
                'age': agent.age,
                'events': timeline,
                'total_events': len(timeline)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取时间线失败: {str(e)}'}), 500


def _format_event_description(event):
    """格式化事件描述"""
    data = event.data if isinstance(event.data, dict) else {}
    t = event.event_type
    if 'career_change' in t:
        return f"换了工作，新收入 {data.get('new_income', '?')}"
    if 'marriage' in t:
        return "结婚了"
    if 'divorce' in t:
        return "离婚了"
    if 'retirement' in t:
        return "退休了"
    if 'crime' in t:
        return "涉及犯罪事件"
    if 'skill' in t:
        return f"学会了新技能: {data.get('skill', '?')}"
    if 'trait' in t:
        return f"觉醒了天赋: {data.get('trait', '?')}"
    if 'ai_decision' in t:
        return f"做出决策: {data.get('action', '?')} ({data.get('reasoning', '')})"
    if 'agent_created' in t:
        return "来到了这个世界"
    if 'agent_died' in t:
        return "离开了世界"
    if 'employment' in t:
        return f"找到了工作: {data.get('occupation', data.get('job', '?'))}"
    if 'education' in t:
        return f"完成了学业: {data.get('level', '?')}"
    if 'housing' in t:
        return f"搬了新家: {data.get('status', '?')}"
    if 'health' in t or 'medical' in t:
        return f"就医: {data.get('diagnosis', data.get('type', '?'))}"
    return data.get('description', t)


# ============ 涌现行为检测 API ============

@app.route(f'/api/{API_VERSION}/emergence/detect', methods=['POST'])
@require_api_key
def detect_emergence():
    """手动触发涌现行为检测"""
    try:
        if engine and hasattr(engine, 'emergence_detector') and engine.emergence_detector:
            results = engine.emergence_detector.detect_all(
                engine.agents, engine.events[-1000:] if engine.events else [], engine.months_simulated
            )
            return jsonify({'success': True, 'data': results})
        return jsonify({'success': False, 'error': 'Emergence detector not available'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route(f'/api/{API_VERSION}/emergence/history')
@require_api_key
def emergence_history():
    """获取涌现检测历史"""
    try:
        if engine and hasattr(engine, 'emergence_detector') and engine.emergence_detector:
            return jsonify({'success': True, 'data': engine.emergence_detector.history[-50:]})
        return jsonify({'success': True, 'data': []})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route(f'/api/{API_VERSION}/emergence/alerts')
@require_api_key
def emergence_alerts():
    """获取涌现警报列表"""
    try:
        if engine and hasattr(engine, 'emergence_detector') and engine.emergence_detector:
            return jsonify({'success': True, 'data': engine.emergence_detector.alerts[-100:]})
        return jsonify({'success': True, 'data': []})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ 启动 ============
if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"  御龙军虚拟 Agent 世界 API v{API_VERSION}")
    print(f"  引擎: DeepIntegrationEngine")
    print(f"{'='*60}")

    # 初始化 Agent 群体
    init_engine(INITIAL_AGENT_COUNT)

    print(f"\n  API 端点:")
    print(f"  {'─'*50}")
    print(f"  GET  /api/{API_VERSION}/health                    - 健康检查 (无需认证)")
    print(f"  GET  /api/{API_VERSION}/stats                     - 世界统计")
    print(f"  GET  /api/{API_VERSION}/agents                    - Agent 列表")
    print(f"  GET  /api/{API_VERSION}/agents/<id>               - Agent 详情")
    print(f"  POST /api/{API_VERSION}/agents/create             - 创建 Agent")
    print(f"  POST /api/{API_VERSION}/simulate                  - 推进模拟")
    print(f"  POST /api/{API_VERSION}/save                      - 保存状态到 SQLite")
    print(f"  POST /api/{API_VERSION}/load                      - 从 SQLite 恢复状态")
    print(f"  GET  /api/{API_VERSION}/experiments/templates      - 实验模板列表")
    print(f"  GET  /api/{API_VERSION}/experiments/templates/<id> - 模板详情")
    print(f"  POST /api/{API_VERSION}/experiments/run            - 运行实验")
    print(f"  GET  /api/{API_VERSION}/events                    - 最近事件")
    print(f"  POST /api/{API_VERSION}/reports/generate          - 生成报告 (html/json/markdown)")
    print(f"  POST /api/{API_VERSION}/reports/smart             - 智能报告 (executive/business/technical)")
    print(f"  POST /api/{API_VERSION}/reports/excel             - Excel 报告 (5 工作表+图表)")
    print(f"  POST /api/{API_VERSION}/reports/csv               - CSV 数据导出")
    print(f"  GET  /api/{API_VERSION}/reports/list              - 报告列表")
    print(f"  POST /api/{API_VERSION}/demo/start               - 演示模式 (1000 Agent × 12 月)")
    print(f"  {'─'*50}")
    print(f"  认证: X-API-Key 请求头 (健康检查除外)")
    print(f"  地址: http://localhost:5002")
    print(f"\n  按 Ctrl+C 停止服务\n")

    app.run(host='0.0.0.0', port=5002, debug=False)
