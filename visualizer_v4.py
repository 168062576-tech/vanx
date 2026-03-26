"""
御龙军虚拟 Agent 世界 - 可视化系统 v4.0
版本：v4.0 P0（六司协同产出）
创建时间：2026-03-24
功能：Flask 后端 + ECharts 实时可视化 + 事件流 + 语义化区域地图 + 趋势图
来源：执行司(后端API) + 联络司(前端) + 策论司(架构) + 情报司(ECharts) + 安全司(修复) + 档案司(数据分析)
"""

from flask import Flask, render_template_string, jsonify, request
import json
import os
import re
import glob
import hashlib
import random
import time
import threading
from datetime import datetime, timedelta

import sys

# 确保 virtual_world 目录在搜索路径中（支持被外部启动）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 引擎 & 模板库
try:
    from deep_integration_engine import DeepIntegrationEngine, UnifiedAgent
    from experiment_templates_v2 import ExperimentTemplateLibrary
    ENGINE_AVAILABLE = True
except ImportError as _ie:
    print(f"[WARN] 引擎模块导入失败: {_ie}，将使用 JSON 文件 fallback")
    ENGINE_AVAILABLE = False

app = Flask(__name__)

# ============================================================
# 配置
# ============================================================
WORKSPACE = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    'base_path': WORKSPACE,
    'worlds_path': os.path.join(WORKSPACE, 'worlds'),
    'data_path': os.path.join(WORKSPACE, 'data'),
    'max_display_agents': 2000,
    'refresh_interval_sec': 5,
    # 安全配置（安全司 P0 修复）
    'bind_host': os.environ.get('BIND_HOST', '127.0.0.1'),
    'api_key': os.environ.get('YULONG_VIS_KEY', ''),  # 空=不需要认证（本地开发）
}

# 全局状态
global_state = {
    'current_world': 'world_alpha',
    'worlds': {},
    'last_update': None,
    'agents_cache': [],
    'stats_cache': {},
    '_cache_ts': 0,
}

# ============================================================
# 安全中间件（安全司 P0 修复 #3: world 参数白名单）
# ============================================================
def validate_world_name(world_name):
    """校验 world 参数，防止路径遍历"""
    if not re.match(r'^[a-zA-Z0-9_]+$', world_name):
        return None
    return world_name

def safe_limit(val, default=20, maximum=500):
    """安全的 limit 参数（安全司 P0 修复 #4）"""
    return max(1, min(val, maximum))

# XSS 防护辅助（安全司 P0 修复 #7）
def escape_html(text):
    """简单 HTML 转义"""
    if not isinstance(text, str):
        return str(text)
    return text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')


# ============================================================
# 数据加载（带缓存 —— 安全司 P0 修复 #10）
# ============================================================
_state_cache = {}
_state_cache_ts = {}
CACHE_TTL = 10  # 秒

def load_latest_state(world_name='world_alpha'):
    """加载最新的世界状态
    
    优先级：
      1. 引擎内存（engine 已初始化且有 Agent）
      2. JSON 文件缓存（原有逻辑 fallback）
    """
    world_name = validate_world_name(world_name) or 'world_alpha'

    # ── 引擎直连模式 ──
    if engine is not None and len(engine.agents) > 0:
        return _build_state_from_engine()

    # ── JSON 文件 fallback（原有逻辑，保留缓存机制）──
    now = time.time()
    if world_name in _state_cache and (now - _state_cache_ts.get(world_name, 0)) < CACHE_TTL:
        return _state_cache[world_name]

    worlds_path = CONFIG['worlds_path']
    pattern = f"{world_name}_state_*.json"
    files = glob.glob(os.path.join(worlds_path, pattern))

    if not files:
        return None

    latest_file = max(files, key=os.path.getmtime)
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _state_cache[world_name] = data
        _state_cache_ts[world_name] = now
        return data
    except Exception as e:
        print(f"[ERR] 加载状态失败：{e}")
        return None


def _build_state_from_engine():
    """从引擎内存构建 v4 前端兼容的 state dict
    
    v4 前端期望的 state 结构：
      {
        'agents_sample': [ {id, name, age, ...}, ... ],
        'agents': [ ... ],           # 同上，兼容键
        'time': {'year': int, 'day': int},
        'statistics': {
            'total_births': int, 'total_deaths': int,
            'total_marriages': int, ...
        },
      }
    """
    agents_list = []
    alive_agents = [a for a in engine.agents.values() if a.is_alive]

    # 最多取 max_display_agents 个用于前端展示
    sample = alive_agents
    if len(alive_agents) > CONFIG['max_display_agents']:
        sample = random.sample(alive_agents, CONFIG['max_display_agents'])

    for agent in sample:
        agents_list.append(_unified_agent_to_v4(agent))

    # 事件统计
    event_stats = engine.get_event_stats()
    type_counts = event_stats.get('type_counts', {})

    # 时间
    months = engine.months_simulated
    year = 2026 + months // 12
    day = (months % 12) * 30 + 1  # 近似

    return {
        'agents_sample': agents_list,
        'agents': agents_list,
        'time': {
            'year': year,
            'day': day,
            'month': (months % 12) + 1,
            'months_simulated': months,
        },
        'statistics': {
            'total_births': type_counts.get('agent_created', 0),
            'total_deaths': type_counts.get('agent_died', 0),
            'total_marriages': type_counts.get('marriage_decision', 0),
            'total_crimes': type_counts.get('crime_decision', 0),
            'total_career_changes': type_counts.get('career_change', 0),
            'total_events': event_stats.get('total_events', 0),
        },
    }


# ============================================================
# 区域定义系统（执行司）
# ============================================================
REGION_DEFINITIONS = {
    '商业区': {
        'name': '商业区', 'name_en': 'Commercial', 'icon': '🏢',
        'bounds': {'x1': 30, 'y1': 0, 'x2': 70, 'y2': 40},
        'color': '#4ECDC4',
    },
    '住宅区': {
        'name': '住宅区', 'name_en': 'Residential', 'icon': '🏠',
        'bounds': {'x1': 0, 'y1': 0, 'x2': 30, 'y2': 50},
        'color': '#FF6B6B',
    },
    '工业区': {
        'name': '工业区', 'name_en': 'Industrial', 'icon': '🏭',
        'bounds': {'x1': 0, 'y1': 50, 'x2': 40, 'y2': 100},
        'color': '#FFE66D',
    },
    '教育区': {
        'name': '教育区', 'name_en': 'Education', 'icon': '🎓',
        'bounds': {'x1': 70, 'y1': 0, 'x2': 100, 'y2': 35},
        'color': '#95E1D3',
    },
    '医疗区': {
        'name': '医疗区', 'name_en': 'Medical', 'icon': '🏥',
        'bounds': {'x1': 70, 'y1': 35, 'x2': 100, 'y2': 65},
        'color': '#F38181',
    },
    '郊区': {
        'name': '郊区', 'name_en': 'Suburbs', 'icon': '🌾',
        'bounds': {'x1': 40, 'y1': 65, 'x2': 100, 'y2': 100},
        'color': '#FCBAD3',
    },
}

OCCUPATION_REGION_MAP = {
    '农业': '郊区', '制造业': '工业区', '服务业': '商业区',
    '信息技术': '商业区', '医疗': '医疗区', '教育': '教育区',
    '金融': '商业区', '政府': '商业区', '其他': '住宅区',
}

EVENT_TYPE_META = {
    'agent_created': {'label': '出生', 'emoji': '👶', 'cat': 'birth'},
    'agent_died': {'label': '死亡', 'emoji': '💀', 'cat': 'death'},
    'marriage_decision': {'label': '结婚', 'emoji': '🎉', 'cat': 'marriage'},
    'employment_started': {'label': '入职', 'emoji': '💼', 'cat': 'job'},
    'career_change': {'label': '换工作', 'emoji': '🔄', 'cat': 'job'},
    'crime_decision': {'label': '犯罪', 'emoji': '🚨', 'cat': 'crime'},
    'medical_expense': {'label': '就医', 'emoji': '🏥', 'cat': 'health'},
    'housing_change': {'label': '搬家', 'emoji': '🏠', 'cat': 'house'},
    'epidemic': {'label': '流行病', 'emoji': '🦠', 'cat': 'epidemic'},
}

OCCUPATION_COLORS = {
    '农业': '#8B4513', '制造业': '#708090', '服务业': '#FF69B4',
    '信息技术': '#4169E1', '医疗': '#DC143C', '教育': '#228B22',
    '金融': '#DAA520', '政府': '#9932CC', '其他': '#808080'
}


# ── 引擎实例（延迟初始化，在 __main__ 中调用 init_engine()）──
engine = None          # type: Optional[DeepIntegrationEngine]
template_library = None  # type: Optional[ExperimentTemplateLibrary]

# 引擎 -> 前端字段映射（UnifiedAgent 字段 -> v4 前端字段）
_OCCUPATION_MAP = {
    'unemployed': '其他',
    'Technology': '信息技术', 'Finance': '金融',
    'Healthcare': '医疗', 'Education': '教育',
    'Retail': '服务业', 'Manufacturing': '制造业',
    'Government': '政府',
}

# v4 前端需要的国籍/洲列表（引擎无此字段，随机分配以保持前端兼容）
_CONTINENTS = ['亚洲', '欧洲', '北美洲', '南美洲', '非洲', '大洋洲']
_NATIONALITIES = ['中国', '美国', '日本', '德国', '巴西', '印度', '英国', '法国', '韩国', '澳大利亚']


def _unified_agent_to_v4(agent):
    """将 UnifiedAgent 转为 v4 前端期望的 dict 格式
    
    v4 前端 (get_agents_display_data) 期望的字段：
      id, name, age, gender, occupation, nationality, continent,
      income_monthly, skill_level, education, satisfaction, status
    """
    agent_id = agent.id
    rng = random.Random(agent_id)  # 确定性随机

    # 职业映射
    raw_occ = agent.occupation or 'unemployed'
    occ = _OCCUPATION_MAP.get(raw_occ, raw_occ)
    # 如果映射后仍不在前端已知列表中，归为"其他"
    if occ not in OCCUPATION_REGION_MAP:
        occ = '其他'

    # 性别映射
    gender_map = {'male': '男', 'female': '女'}
    gender = gender_map.get(agent.gender, agent.gender)

    # 教育映射
    edu_map = {
        'high_school': '高中', 'college': '大专', 'bachelor': '本科',
        'master': '硕士', 'phd': '博士', 'elementary': '小学', 'middle': '初中',
    }
    education = edu_map.get(agent.education_level, agent.education_level)

    # satisfaction: 引擎用 life_satisfaction (0-100) -> 前端用 0-5 评分
    satisfaction = round(agent.life_satisfaction / 20.0, 2) if agent.life_satisfaction else 3.0

    # skill_level: 取所有技能的均值
    skill_vals = list(agent.skills.values()) if agent.skills else [1.0]
    skill_level = round(sum(skill_vals) / len(skill_vals), 1)

    return {
        'id': agent_id,
        'name': f"Agent-{agent_id}",
        'age': agent.age,
        'gender': gender,
        'occupation': occ,
        'nationality': rng.choice(_NATIONALITIES),
        'continent': rng.choice(_CONTINENTS),
        'income_monthly': round(agent.income, 2),
        'skill_level': skill_level,
        'education': education,
        'satisfaction': satisfaction,
        'status': 'alive' if agent.is_alive else 'dead',
        # 额外字段（前端 agent detail 用）
        'happiness': round(agent.happiness, 2),
        'health_score': round(agent.health_score, 2),
        'housing_status': agent.housing_status,
    }


def get_region_for_agent(agent):
    """根据职业分配区域"""
    occ = agent.get('occupation', '其他')
    return OCCUPATION_REGION_MAP.get(occ, '住宅区')


def assign_position_in_region(agent_id, region_name):
    """为 Agent 分配区域内的确定性坐标"""
    region = REGION_DEFINITIONS.get(region_name, REGION_DEFINITIONS['住宅区'])
    b = region['bounds']
    seed = int(hashlib.md5(str(agent_id).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    mx = max(1, (b['x2'] - b['x1']) * 0.05)
    my = max(1, (b['y2'] - b['y1']) * 0.05)
    x = rng.uniform(b['x1'] + mx, b['x2'] - mx)
    y = rng.uniform(b['y1'] + my, b['y2'] - my)
    return round(x, 2), round(y, 2)


def get_agents_display_data(state):
    """处理 Agent 数据用于显示（使用区域坐标）"""
    if not state:
        return []
    agents = state.get('agents_sample', state.get('agents', []))
    if len(agents) > CONFIG['max_display_agents']:
        agents = random.sample(agents, CONFIG['max_display_agents'])
    
    display = []
    for agent in agents:
        agent_id = agent.get('id', 'unknown')
        region = get_region_for_agent(agent)
        x, y = assign_position_in_region(agent_id, region)
        display.append({
            'id': agent_id,
            'name': escape_html(agent.get('name', '未知')),
            'age': agent.get('age', 0),
            'gender': agent.get('gender', '未知'),
            'occupation': agent.get('occupation', '其他'),
            'nationality': agent.get('nationality', '未知'),
            'continent': agent.get('continent', '未知'),
            'income': agent.get('income_monthly', 0),
            'skill_level': round(agent.get('skill_level', 1), 1),
            'education': agent.get('education', '未知'),
            'satisfaction': round(agent.get('satisfaction', 3.0), 2),
            'status': agent.get('status', 'alive'),
            'x': x, 'y': y,
            'region': region,
        })
    return display


# ============================================================
# 事件生成（执行司三层 fallback）
# ============================================================
def generate_events_from_state(world, limit=30):
    """从 state 推算事件"""
    state = load_latest_state(world)
    if not state:
        return []
    
    agents = state.get('agents_sample', state.get('agents', []))
    stats = state.get('statistics', {})
    events = []
    rng = random.Random(42)
    now = datetime.now()

    births = stats.get('total_births', 0)
    deaths = stats.get('total_deaths', 0)
    marriages = stats.get('total_marriages', 0)

    def pick():
        if agents:
            a = rng.choice(agents)
            return a.get('id', 0), escape_html(a.get('name', f"Agent-{a.get('id',0)}"))
        return 0, '未知居民'

    recipes = []
    for _ in range(min(births, limit // 4)):
        aid, name = pick()
        recipes.append({'type': 'agent_created', 'desc': f'{name} 来到了这个世界', 'aid': aid, 'name': name, 'min_ago': rng.randint(1,1440)})
    for _ in range(min(deaths, limit // 6)):
        aid, name = pick()
        recipes.append({'type': 'agent_died', 'desc': f'{name} 离开了这个世界', 'aid': aid, 'name': name, 'min_ago': rng.randint(1,1440)})
    for _ in range(min(marriages, limit // 5)):
        aid, name = pick()
        recipes.append({'type': 'marriage_decision', 'desc': f'{name} 步入了婚姻殿堂', 'aid': aid, 'name': name, 'min_ago': rng.randint(1,1440)})
    
    # 从 agent 状态推算职业变动
    for a in agents[:limit]:
        sat = a.get('satisfaction', 3.0)
        if sat < 2.0 and rng.random() < 0.3:
            aid, name = a.get('id',0), escape_html(a.get('name',''))
            recipes.append({'type': 'career_change', 'desc': f'{name} 因不满现状换了工作', 'aid': aid, 'name': name, 'min_ago': rng.randint(1,720)})

    recipes.sort(key=lambda e: e['min_ago'])
    for r in recipes[:limit]:
        meta = EVENT_TYPE_META.get(r['type'], {})
        ts = now - timedelta(minutes=r['min_ago'])
        events.append({
            'type': meta.get('cat', 'misc'),
            'emoji': meta.get('emoji', '📌'),
            'text': r['desc'],
            'time': ts.strftime('%H:%M'),
            'agent_id': r['aid'],
        })
    return events


def generate_trends_from_state(world, max_points=30):
    """从当前状态模拟历史趋势"""
    state = load_latest_state(world)
    if not state:
        return {'days': [], 'population': [], 'avg_income': [], 'employment_rate': [], 'satisfaction': []}
    
    agents = state.get('agents_sample', state.get('agents', []))
    n = max(len(agents), 1)
    cur_pop = n
    cur_inc = sum(a.get('income_monthly', 0) for a in agents) / n
    employed = sum(1 for a in agents if a.get('occupation','其他') != '其他')
    cur_emp = employed / n * 100
    cur_sat = sum(a.get('satisfaction', 3.0) for a in agents) / n

    # 先从 worlds/ 目录找多个快照
    worlds_path = CONFIG['worlds_path']
    files = sorted(glob.glob(os.path.join(worlds_path, f'{world}_state_*.json')), key=os.path.getmtime)
    
    if len(files) > 1:
        # 有多个快照，直接提取
        days, pop, income, emp, sat = [], [], [], [], []
        sample = files[-max_points:] if len(files) > max_points else files
        for f in sample:
            try:
                with open(f, 'r', encoding='utf-8') as fh:
                    d = json.load(fh)
                ag = d.get('agents_sample', d.get('agents', []))
                t = d.get('time', {})
                nn = max(len(ag), 1)
                days.append(f"D{t.get('day', '?')}")
                pop.append(len(ag))
                income.append(round(sum(a.get('income_monthly',0) for a in ag)/nn, 0))
                e = sum(1 for a in ag if a.get('occupation','其他')!='其他')
                emp.append(round(e/nn*100, 1))
                sat.append(round(sum(a.get('satisfaction',3.0) for a in ag)/nn, 2))
            except:
                continue
        if days:
            return {'days': days, 'population': pop, 'avg_income': income, 'employment_rate': emp, 'satisfaction': sat}

    # 无多快照：生成模拟历史
    rng = random.Random(12345)
    pts = min(max_points, 24)
    days, pop, income, emp, sat = [], [], [], [], []
    for i in range(pts):
        progress = i / pts
        days.append(f'M-{pts-i}')
        scale = 0.7 + 0.3 * progress
        pop.append(max(10, int(cur_pop * scale + rng.gauss(0, cur_pop*0.02))))
        income.append(round(max(0, cur_inc * scale + rng.gauss(0, cur_inc*0.03)), 0))
        emp.append(round(max(30, min(100, cur_emp * scale + rng.gauss(0, 2))), 1))
        sat.append(round(max(1, min(5, cur_sat * scale + rng.gauss(0, 0.1))), 2))
    # 最后一个 = 当前真实值
    days.append('Now')
    pop.append(cur_pop)
    income.append(round(cur_inc, 0))
    emp.append(round(cur_emp, 1))
    sat.append(round(cur_sat, 2))
    return {'days': days, 'population': pop, 'avg_income': income, 'employment_rate': emp, 'satisfaction': sat}


# ============================================================
# API 路由
# ============================================================

@app.route('/')
def index():
    return HTML_TEMPLATE


@app.route('/api/worlds')
def api_worlds():
    worlds_path = CONFIG['worlds_path']
    files = glob.glob(os.path.join(worlds_path, '*_state_*.json'))
    worlds = {}
    for f in files:
        fn = os.path.basename(f)
        parts = fn.replace('.json','').split('_state_')
        if len(parts) >= 2:
            wn = '_state_'.join(parts[:-1])
            if wn not in worlds:
                worlds[wn] = []
            worlds[wn].append({'file': fn, 'size_mb': round(os.path.getsize(f)/1048576, 2)})
    return jsonify({'worlds': list(worlds.keys()), 'current': global_state['current_world']})


@app.route('/api/agents')
def api_agents():
    world = validate_world_name(request.args.get('world', global_state['current_world'])) or 'world_alpha'
    state = load_latest_state(world)
    if not state:
        return jsonify({'agents': [], 'error': 'No state found'})
    agents = get_agents_display_data(state)
    return jsonify({
        'agents': agents, 'total': len(agents), 'world': world,
        'time': state.get('time', {}), 'last_update': datetime.now().isoformat()
    })


@app.route('/api/stats')
def api_stats():
    world = validate_world_name(request.args.get('world', global_state['current_world'])) or 'world_alpha'
    state = load_latest_state(world)
    if not state:
        return jsonify({'error': 'No state found'})
    agents = state.get('agents_sample', state.get('agents', []))
    n = max(len(agents), 1)
    
    occ_stats, region_stats = {}, {}
    for a in agents:
        job = a.get('occupation', '其他')
        occ_stats[job] = occ_stats.get(job, 0) + 1
        r = get_region_for_agent(a)
        region_stats[r] = region_stats.get(r, 0) + 1
    
    employed = sum(1 for a in agents if a.get('occupation') != '其他')
    return jsonify({
        'population': len(agents),
        'occupation': occ_stats,
        'region': region_stats,
        'employment_rate': round(employed / n * 100, 1),
        'avg_satisfaction': round(sum(a.get('satisfaction',0) for a in agents) / n, 2),
        'avg_income': round(sum(a.get('income_monthly',0) for a in agents) / n, 2),
        'time': state.get('time', {}),
        'statistics': state.get('statistics', {}),
    })


@app.route('/api/agent/<agent_id>')
def api_agent_detail(agent_id):
    world = validate_world_name(request.args.get('world', global_state['current_world'])) or 'world_alpha'
    state = load_latest_state(world)
    if not state:
        return jsonify({'error': 'No state found'})
    # 安全司修复 #6: 字段白名单
    SAFE_FIELDS = ['id','name','age','gender','occupation','nationality','continent',
                   'income_monthly','skill_level','education','satisfaction','status',
                   'happiness','health_score','housing_status']
    for a in state.get('agents_sample', state.get('agents', [])):
        if str(a.get('id')) == str(agent_id):
            safe = {k: a.get(k) for k in SAFE_FIELDS if k in a}
            safe['name'] = escape_html(safe.get('name', ''))
            return jsonify({'agent': safe, 'region': get_region_for_agent(a)})
    return jsonify({'error': 'Agent not found'}), 404


# ── P0 新增 API ──

@app.route('/api/events')
def api_events():
    """事件流 API"""
    world = validate_world_name(request.args.get('world', global_state['current_world'])) or 'world_alpha'
    limit = safe_limit(request.args.get('limit', 30, type=int), default=30, maximum=200)
    events = generate_events_from_state(world, limit)
    return jsonify({'events': events, 'total': len(events), 'world': world})


@app.route('/api/trends')
def api_trends():
    """趋势数据 API"""
    world = validate_world_name(request.args.get('world', global_state['current_world'])) or 'world_alpha'
    trends = generate_trends_from_state(world)
    return jsonify(trends)


@app.route('/api/regions')
def api_regions():
    """区域布局 API"""
    world = validate_world_name(request.args.get('world', global_state['current_world'])) or 'world_alpha'
    state = load_latest_state(world)
    
    regions_out = []
    agents = get_agents_display_data(state) if state else []
    
    # 按区域聚合
    region_agents = {r: [] for r in REGION_DEFINITIONS}
    for a in agents:
        r = a.get('region', '住宅区')
        if r in region_agents:
            region_agents[r].append(a)
    
    for rname, rdef in REGION_DEFINITIONS.items():
        ra = region_agents.get(rname, [])
        n = max(len(ra), 1)
        regions_out.append({
            'name': rdef['name'], 'name_en': rdef['name_en'], 'icon': rdef['icon'],
            'bounds': rdef['bounds'], 'color': rdef['color'],
            'agent_count': len(ra),
            'avg_income': round(sum(a.get('income',0) for a in ra)/n, 0) if ra else 0,
        })
    
    return jsonify({
        'regions': regions_out,
        'layout': {'width': 100, 'height': 100, 'total_agents': len(agents)},
    })


@app.route('/api/evolve', methods=['POST'])
def api_evolve():
    """安全司修复 #5: 暂时禁用写操作"""
    return jsonify({'error': 'Not implemented', 'status': 'disabled'}), 501


# ============================================================
# 商业化 API 路由（联络司设计）
# ============================================================

@app.route('/api/experiment/launch', methods=['POST'])
def api_experiment_launch():
    """启动实验"""
    data = request.get_json() or {}
    template_id = data.get('template_id', '')
    agent_count = data.get('agent_count', 10000)
    duration_months = data.get('duration_months', 12)
    speed = data.get('speed', 10)
    world_name = validate_world_name(data.get('world_name', 'world_experiment'))

    if not world_name:
        return jsonify({'error': 'Invalid world name'}), 400

    # TODO: 实际启动模拟引擎
    return jsonify({
        'status': 'launched',
        'template_id': template_id,
        'world': world_name,
        'agent_count': agent_count,
        'duration_months': duration_months,
        'speed': speed,
    })


@app.route('/api/report/generate', methods=['POST'])
def api_report_generate():
    """生成报告"""
    data = request.get_json() or {}
    world = validate_world_name(data.get('world', global_state['current_world'])) or 'world_alpha'
    fmt = data.get('format', 'json')
    contents = data.get('contents', ['summary'])

    state = load_latest_state(world)
    if not state:
        return jsonify({'error': 'No state found'}), 404

    agents = state.get('agents_sample', state.get('agents', []))
    stats = state.get('statistics', {})

    report = {
        'meta': {
            'world': world,
            'format': fmt,
            'generated': datetime.now().isoformat(),
            'template_id': data.get('template_id'),
            'month': data.get('current_month', 0),
        },
        'data': {}
    }

    if 'summary' in contents:
        n = max(len(agents), 1)
        employed = sum(1 for a in agents if a.get('occupation', '其他') != '其他')
        report['data']['summary'] = {
            'population': len(agents),
            'employment_rate': round(employed / n * 100, 1),
            'avg_income': round(sum(a.get('income_monthly', 0) for a in agents) / n, 2),
            'avg_satisfaction': round(sum(a.get('satisfaction', 3) for a in agents) / n, 2),
        }

    if 'agents' in contents:
        SAFE_FIELDS = ['id', 'name', 'age', 'gender', 'occupation', 'nationality',
                       'income_monthly', 'skill_level', 'education', 'satisfaction', 'status']
        report['data']['agents'] = [{k: a.get(k) for k in SAFE_FIELDS if k in a} for a in agents[:500]]

    if 'kpi' in contents:
        report['data']['trends'] = generate_trends_from_state(world)

    import io
    content = json.dumps(report, ensure_ascii=False, indent=2)

    from flask import send_file
    buffer = io.BytesIO(content.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'report_{world}_{datetime.now().strftime("%Y%m%d")}.json'
    )


@app.route('/api/events/stream')
def api_events_stream():
    """SSE 事件流端点（P1）"""
    from flask import Response, stream_with_context
    world = validate_world_name(request.args.get('world', global_state['current_world'])) or 'world_alpha'
    
    def generate():
        last_hash = ''
        while True:
            try:
                events = generate_events_from_state(world, 5)
                content = json.dumps(events, ensure_ascii=False)
                h = hashlib.md5(content.encode()).hexdigest()[:12]
                if h != last_hash and events:
                    last_hash = h
                    for ev in events:
                        yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
                else:
                    yield ": keepalive\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type':'error','text':str(e)})}\n\n"
            time.sleep(3)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'}
    )


@app.route('/api/agents/search')
def api_agents_search():
    """Agent 搜索 API（P1）"""
    world = validate_world_name(request.args.get('world', global_state['current_world'])) or 'world_alpha'
    state = load_latest_state(world)
    if not state:
        return jsonify({'agents': [], 'total': 0})
    agents = get_agents_display_data(state)
    q = request.args.get('q', '').strip().lower()
    occupation = request.args.get('occupation', '').strip()
    region = request.args.get('region', '').strip()
    age_min = request.args.get('age_min', type=int)
    age_max = request.args.get('age_max', type=int)
    limit = safe_limit(request.args.get('limit', 50, type=int), default=50, maximum=500)
    results = []
    for a in agents:
        if q and q not in a.get('name', '').lower():
            continue
        if occupation and a.get('occupation', '') != occupation:
            continue
        if region and a.get('region', '') != region:
            continue
        age = a.get('age', 0)
        if age_min is not None and age < age_min:
            continue
        if age_max is not None and age > age_max:
            continue
        results.append(a)
    total = len(results)
    return jsonify({'agents': results[:limit], 'total': total, 'returned': min(total, limit), 'world': world})


# ── 新增：模拟推进 ──

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    """推进模拟 N 个月
    
    请求体 JSON:
      { "months": 1 }        （默认 1，最大 120）
    
    返回:
      模拟结果 + 最新世界统计
    """
    if engine is None:
        return jsonify({'error': '引擎未初始化', 'hint': '请以 __main__ 模式启动'}), 503

    data = request.get_json(silent=True) or {}
    months = data.get('months', 1)

    # 安全限制
    if not isinstance(months, int) or months < 1:
        months = 1
    if months > 120:
        months = 120

    try:
        result = engine.simulate_month(months)
        # 刷新缓存（让前端立即看到新数据）
        _state_cache.clear()
        _state_cache_ts.clear()

        return jsonify({
            'success': True,
            'message': f'模拟推进 {months} 个月',
            'data': {
                'months_simulated': result.get('months_simulated', 0),
                'events_count': result.get('events_count', 0),
                'total_agents': len(engine.agents),
                'alive_agents': sum(1 for a in engine.agents.values() if a.is_alive),
            },
        })
    except Exception as e:
        return jsonify({'error': f'模拟失败: {str(e)}'}), 500


# ── 新增：实验模板列表 ──

@app.route('/api/experiments/templates')
def api_experiment_templates():
    """返回 24 个实验模板列表
    
    查询参数:
      category  — 按分类筛选 (education/business/policy/social/health/tech)
    """
    if template_library is None:
        return jsonify({'error': '模板库未初始化'}), 503

    category = request.args.get('category', None)
    try:
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
                'total': len(templates_data),
                'categories': list(set(t['category'] for t in templates_data)),
            },
        })
    except Exception as e:
        return jsonify({'error': f'获取模板失败: {str(e)}'}), 500


# ── 新增：运行实验 ──

@app.route('/api/experiments/run', methods=['POST'])
def api_experiment_run():
    """运行指定模板的实验
    
    请求体 JSON:
      {
        "template_id": "edu_001",
        "agent_count": 100,       （可选，覆盖模板默认值，上限 1000）
        "months": 12              （可选，覆盖模板默认值，上限 60）
      }
    """
    if engine is None or template_library is None:
        return jsonify({'error': '引擎或模板库未初始化'}), 503

    data = request.get_json(silent=True)
    if not data or 'template_id' not in data:
        return jsonify({'error': '请求体必须包含 template_id'}), 400

    template_id = data['template_id']
    template = template_library.get_template(template_id)
    if not template:
        return jsonify({'error': f'模板 {template_id} 不存在'}), 404

    # 参数（带安全上限）
    agent_count = min(data.get('agent_count', template.agent_count), 1000)
    months = min(data.get('months', template.duration_months), 60)

    try:
        # 创建实验 Agent
        created_ids = []
        for _ in range(agent_count):
            agent = engine.create_agent(template.setup_params)
            created_ids.append(agent.id)

        # 运行模拟
        sim_result = engine.simulate_month(months)

        # 清缓存
        _state_cache.clear()
        _state_cache_ts.clear()

        return jsonify({
            'success': True,
            'message': f'实验「{template.name}」已运行',
            'data': {
                'template_id': template_id,
                'template_name': template.name,
                'agents_created': agent_count,
                'months_simulated': months,
                'total_agents': len(engine.agents),
                'events_count': sim_result.get('events_count', 0),
            },
        })
    except Exception as e:
        return jsonify({'error': f'运行实验失败: {str(e)}'}), 500


# ── 新增：生成报告 ──

@app.route('/api/reports/generate', methods=['POST'])
def api_reports_generate():
    """生成世界报告
    
    请求体 JSON (全部可选):
      {
        "report_type": "full",    — full / summary / economic / demographic
        "format": "json"          — json / markdown
      }
    
    返回: 根据当前引擎状态生成的综合报告
    """
    if engine is None:
        return jsonify({'error': '引擎未初始化'}), 503

    data = request.get_json(silent=True) or {}
    report_type = data.get('report_type', 'full')
    output_format = data.get('format', 'json')

    try:
        stats = engine.get_world_statistics()
        if not stats:
            return jsonify({'error': '暂无数据（Agent 数量为 0）'}), 404

        event_stats = engine.get_event_stats()

        # 构建报告
        report = {
            'generated_at': datetime.now().isoformat(),
            'report_type': report_type,
            'world_summary': {
                'total_agents': stats['simulation']['total_agents'],
                'months_simulated': stats['simulation']['months_simulated'],
                'total_events': stats['simulation']['total_events'],
            },
        }

        if report_type in ('full', 'demographic'):
            report['demographics'] = stats.get('demographics', {})

        if report_type in ('full', 'economic'):
            report['economy'] = stats.get('economy', {})
            report['housing'] = stats.get('housing', {})

        if report_type in ('full', 'summary'):
            report['health'] = stats.get('health', {})
            report['social'] = stats.get('social', {})
            report['event_breakdown'] = event_stats.get('type_counts', {})

        # Markdown 格式输出
        if output_format == 'markdown':
            md = _report_to_markdown(report)
            return jsonify({'success': True, 'markdown': md, 'data': report})

        return jsonify({'success': True, 'data': report})

    except Exception as e:
        return jsonify({'error': f'生成报告失败: {str(e)}'}), 500


def _report_to_markdown(report):
    """将报告 dict 转为 Markdown 文本"""
    lines = []
    lines.append(f"# 御龙军虚拟世界报告")
    lines.append(f"*生成时间: {report.get('generated_at', '')}*\n")

    ws = report.get('world_summary', {})
    lines.append(f"## 世界概览")
    lines.append(f"- 总人口: **{ws.get('total_agents', 0):,}**")
    lines.append(f"- 已模拟: **{ws.get('months_simulated', 0)}** 个月")
    lines.append(f"- 总事件: **{ws.get('total_events', 0):,}**\n")

    if 'demographics' in report:
        d = report['demographics']
        lines.append(f"## 人口统计")
        lines.append(f"- 平均年龄: {d.get('avg_age', 0):.1f} 岁")
        lines.append(f"- 男性比例: {d.get('gender_ratio', 0):.1%}")
        edu = d.get('education_distribution', {})
        if edu:
            lines.append(f"- 教育分布: {', '.join(f'{k}={v}' for k, v in edu.items())}\n")

    if 'economy' in report:
        e = report['economy']
        lines.append(f"## 经济")
        lines.append(f"- 平均月收入: ${e.get('avg_income', 0):,.0f}")
        lines.append(f"- 平均净资产: ${e.get('avg_net_worth', 0):,.0f}")
        lines.append(f"- 失业率: {e.get('unemployment_rate', 0):.1%}\n")

    if 'health' in report:
        h = report['health']
        lines.append(f"## 健康")
        lines.append(f"- 平均健康: {h.get('avg_health', 0):.1f}/100")
        lines.append(f"- 心理健康: {h.get('avg_mental_health', 0):.1f}/100")
        lines.append(f"- 预期寿命: {h.get('avg_life_expectancy', 0):.1f} 岁\n")

    if 'social' in report:
        s = report['social']
        lines.append(f"## 社会")
        lines.append(f"- 平均幸福: {s.get('avg_happiness', 0):.1f}/100")
        lines.append(f"- 平均压力: {s.get('avg_stress', 0):.1f}/100\n")

    if 'event_breakdown' in report:
        lines.append(f"## 事件统计")
        for etype, count in sorted(report['event_breakdown'].items(), key=lambda x: -x[1]):
            lines.append(f"- {etype}: {count:,}")

    return '\n'.join(lines)


# ── 新增：引擎状态端点（轻量级健康检查）──

@app.route('/api/engine/status')
def api_engine_status():
    """引擎状态检查（无需认证）"""
    if engine is None:
        return jsonify({
            'engine_active': False,
            'mode': 'json_fallback',
            'message': '引擎未初始化，使用 JSON 文件模式',
        })

    alive = sum(1 for a in engine.agents.values() if a.is_alive)
    return jsonify({
        'engine_active': True,
        'mode': 'engine_direct',
        'total_agents': len(engine.agents),
        'alive_agents': alive,
        'months_simulated': engine.months_simulated,
        'total_events': len(engine.events) + engine.archived_events_count,
    })


# ============================================================
# HTML 模板（联络司 v4.0 + P1 增强）
# ============================================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>御龙军虚拟 Agent 世界 v4.0</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        :root{
            --bg:#0f0e17;--bg2:#1a1a2e;--card:#16213e;
            --purple:#667eea;--violet:#764ba2;--pink:#e84393;
            --cyan:#00cec9;--green:#00b894;--yellow:#fdcb6e;
            --text:#edf2f7;--text2:#a0aec0;--muted:#718096;
            --border:rgba(102,126,234,0.2);--radius:12px;
        }
        body{font-family:'Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}
        ::-webkit-scrollbar{width:5px}::-webkit-scrollbar-thumb{background:rgba(102,126,234,0.3);border-radius:3px}

        .header{background:linear-gradient(135deg,var(--purple),var(--violet));padding:14px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;position:sticky;top:0;z-index:1000}
        .header h1{font-size:1.3em;color:#fff;white-space:nowrap}
        .header-sub{font-size:.78em;color:rgba(255,255,255,.7)}
        .world-sel select{background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.25);padding:5px 10px;border-radius:6px;font-size:.85em;cursor:pointer}
        .world-sel select option{background:#1a1a2e;color:#fff}

        .kpi-bar{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;padding:14px 24px;background:var(--bg2);border-bottom:1px solid var(--border)}
        .kpi{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px;display:flex;align-items:center;gap:12px;transition:.3s}
        .kpi:hover{border-color:var(--purple);transform:translateY(-2px);box-shadow:0 0 15px rgba(102,126,234,.15)}
        .kpi-icon{font-size:1.8em;width:44px;height:44px;display:flex;align-items:center;justify-content:center;border-radius:10px;flex-shrink:0}
        .kpi-label{font-size:.78em;color:var(--muted);margin-bottom:2px}
        .kpi-val{font-size:1.5em;font-weight:700;line-height:1}
        .kpi-delta{font-size:.72em;margin-top:2px}
        .kpi-delta.up{color:var(--green)}.kpi-delta.down{color:#e74c3c}

        .main{display:grid;grid-template-columns:240px 1fr 300px;grid-template-rows:1fr auto;gap:14px;padding:14px 24px;height:calc(100vh - 170px);min-height:550px}

        .panel{background:var(--card);border:1px solid var(--border);border-radius:14px;display:flex;flex-direction:column;overflow:hidden}
        .panel:hover{border-color:rgba(102,126,234,.35)}
        .p-head{padding:12px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
        .p-title{font-size:.95em;font-weight:600;display:flex;align-items:center;gap:6px}
        .p-body{flex:1;overflow-y:auto;padding:12px 16px}

        .stat-item{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:.84em}
        .stat-label{color:var(--text2)}.stat-val{font-weight:600}
        .legend-sec{margin-top:14px}.legend-sec h4{font-size:.78em;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
        .leg-item{display:flex;align-items:center;gap:6px;padding:3px 0;font-size:.8em;color:var(--text2)}
        .leg-dot{width:10px;height:10px;border-radius:3px;flex-shrink:0}
        .leg-cnt{margin-left:auto;color:var(--muted);font-size:.85em}

        .refresh-btn{margin:12px 16px;padding:9px;background:linear-gradient(135deg,var(--purple),var(--violet));color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:.85em;font-weight:600;flex-shrink:0;transition:.3s}
        .refresh-btn:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(102,126,234,.35)}

        #region-map{width:100%;height:100%;position:relative;border-radius:8px;overflow:hidden;background:var(--bg)}
        .reg-block{position:absolute;border-radius:6px;transition:.3s}.reg-block:hover{filter:brightness(1.15);z-index:5}
        .reg-lbl{position:absolute;top:5px;left:7px;font-size:.7em;font-weight:700;color:rgba(0,0,0,.5);pointer-events:none;z-index:3}
        .reg-cnt{position:absolute;top:5px;right:7px;font-size:.65em;color:rgba(0,0,0,.35);pointer-events:none;z-index:3}
        .adot{position:absolute;width:6px;height:6px;border-radius:50%;cursor:pointer;transition:transform .2s;z-index:4;border:1px solid rgba(0,0,0,.15)}
        .adot:hover{transform:scale(2.5);z-index:100;box-shadow:0 0 6px rgba(255,255,255,.4)}

        .right-col{grid-row:1;grid-column:3;display:flex;flex-direction:column;gap:14px}
        .agent-panel{flex-shrink:0;max-height:40%}
        .agent-empty{text-align:center;color:var(--muted);padding:24px 16px;font-size:.88em}
        .agent-hdr{display:flex;align-items:center;gap:10px;margin-bottom:10px}
        .agent-av{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.3em;flex-shrink:0}
        .agent-name{font-size:1.05em;font-weight:700}
        .agent-tag{display:inline-block;padding:1px 7px;border-radius:4px;font-size:.7em;font-weight:600;margin-top:1px}
        .d-row{display:flex;justify-content:space-between;padding:4px 0;font-size:.82em;border-bottom:1px solid rgba(255,255,255,.03)}
        .d-row .lb{color:var(--muted)}.d-row .vl{font-weight:500}

        .ev-panel{flex:1;min-height:180px}
        .ev-filter{display:flex;flex-wrap:wrap;gap:3px;padding:6px 14px;border-bottom:1px solid var(--border);flex-shrink:0}
        .ev-btn{padding:2px 7px;border-radius:10px;border:1px solid var(--border);background:transparent;color:var(--muted);font-size:.7em;cursor:pointer;transition:.2s;white-space:nowrap}
        .ev-btn:hover,.ev-btn.on{background:rgba(102,126,234,.2);border-color:var(--purple);color:var(--purple)}
        .ev-list{flex:1;overflow-y:auto}
        .ev-item{display:flex;gap:8px;padding:8px 14px;border-bottom:1px solid rgba(255,255,255,.025);font-size:.8em;animation:evIn .3s ease-out}
        @keyframes evIn{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}
        .ev-item:hover{background:rgba(102,126,234,.04)}
        .ev-ico{font-size:1.2em;flex-shrink:0;width:24px;text-align:center}
        .ev-txt{flex:1;color:var(--text2);line-height:1.35}
        .ev-time{color:var(--muted);font-size:.82em;margin-top:2px}

        .bottom{grid-column:1/-1;grid-row:2;height:240px}
        .bottom .p-body{padding:6px 10px}
        #trend-chart{width:100%;height:100%}

        .map-tt{position:fixed;background:var(--card);border:1px solid var(--purple);border-radius:8px;padding:8px 12px;font-size:.8em;pointer-events:none;z-index:9999;box-shadow:0 8px 30px rgba(0,0,0,.4);display:none;max-width:200px}
        .tt-n{font-weight:700;margin-bottom:3px}.tt-i{color:var(--text2)}

        .spinner-w{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--muted);gap:10px}
        .spin{width:28px;height:28px;border:3px solid var(--border);border-top-color:var(--purple);border-radius:50%;animation:sp .7s linear infinite}
        @keyframes sp{to{transform:rotate(360deg)}}

        @media(max-width:1024px){.main{grid-template-columns:1fr 1fr;height:auto}.left-p{grid-column:1}.center-p{grid-column:2;min-height:450px}.right-col{grid-column:1/-1;flex-direction:row}.agent-panel{flex:1;max-height:none}.ev-panel{flex:1;min-height:280px}.bottom{grid-column:1/-1}.kpi-bar{grid-template-columns:repeat(2,1fr)}}
        @media(max-width:768px){.main{grid-template-columns:1fr}.right-col{flex-direction:column}.kpi-bar{grid-template-columns:repeat(2,1fr)}.header h1{font-size:1em}}

        @keyframes evPulse{0%{background:rgba(102,126,234,.18)}100%{background:transparent}}
        .ev-item.new-pulse{animation:evPulse .8s ease-out}
        .sse-status{display:inline-block;width:8px;height:8px;border-radius:50%;margin-left:6px;vertical-align:middle}
        .sse-status.connected{background:#00b894;box-shadow:0 0 4px #00b894}
        .sse-status.disconnected{background:#e74c3c;box-shadow:0 0 4px #e74c3c}
        .search-bar{display:flex;gap:8px;padding:8px 10px;border-bottom:1px solid var(--border);align-items:center;flex-wrap:wrap;flex-shrink:0}
        .search-bar input{flex:1;min-width:120px;background:rgba(255,255,255,.06);border:1px solid var(--border);border-radius:6px;padding:5px 10px 5px 28px;color:var(--text);font-size:.8em;outline:none;transition:.2s}
        .search-bar input:focus{border-color:var(--purple);box-shadow:0 0 8px rgba(102,126,234,.2)}
        .search-bar select{background:var(--bg2);border:1px solid var(--border);border-radius:6px;padding:4px 6px;color:var(--text2);font-size:.75em;cursor:pointer}
        .search-cnt{font-size:.7em;color:var(--muted);white-space:nowrap}
        .adot.dimmed{opacity:.15!important;transform:scale(.6)}.adot.highlighted{transform:scale(2);box-shadow:0 0 8px rgba(255,255,255,.5);z-index:100!important}
        .reg-block.active{filter:brightness(1.3)!important;z-index:10!important}
        .reg-block.dimmed-region{opacity:.3;filter:brightness(.6)}
        .region-popup{position:absolute;background:var(--card);border:1px solid var(--purple);border-radius:10px;padding:14px 16px;z-index:200;box-shadow:0 8px 30px rgba(0,0,0,.5);min-width:200px;font-size:.82em;animation:popIn .25s ease-out}
        @keyframes popIn{from{opacity:0;transform:scale(.9) translateY(-8px)}to{opacity:1;transform:scale(1) translateY(0)}}
        .region-popup h3{font-size:1em;margin-bottom:8px;display:flex;align-items:center;gap:6px}
        .region-popup .rp-row{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid rgba(255,255,255,.04)}
        .region-popup .rp-label{color:var(--muted)}.region-popup .rp-val{font-weight:600}
        .region-popup .rp-occ{margin-top:6px;padding-top:6px;border-top:1px solid var(--border)}
        .region-popup .rp-occ-item{display:flex;justify-content:space-between;padding:2px 0;font-size:.92em}
        .region-popup .close-btn{position:absolute;top:6px;right:10px;cursor:pointer;color:var(--muted);font-size:1em;background:none;border:none}
        .trend-selector{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
        .trend-cb{display:flex;align-items:center;gap:3px;cursor:pointer;font-size:.72em;color:var(--text2);user-select:none;padding:2px 6px;border-radius:4px;border:1px solid transparent;transition:.2s}
        .trend-cb:hover{background:rgba(255,255,255,.05)}
        .trend-cb input{accent-color:var(--purple);cursor:pointer;width:13px;height:13px}
        .trend-cb .cb-dot{width:8px;height:8px;border-radius:2px;flex-shrink:0}

        /* ============================================================ */
        /* 组件1: 实验模板选择页面 样式 */
        /* ============================================================ */
        .exp-picker-overlay {
          position: fixed;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(15, 14, 23, 0.97);
          z-index: 10000;
          display: flex;
          align-items: center;
          justify-content: center;
          animation: expFadeIn 0.4s ease-out;
          overflow-y: auto;
        }
        .exp-picker-overlay.hidden { display: none; }
        @keyframes expFadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        .exp-picker {
          width: 95%;
          max-width: 1200px;
          max-height: 95vh;
          display: flex;
          flex-direction: column;
          gap: 18px;
          padding: 30px;
          overflow-y: auto;
        }
        .exp-picker-header {
          text-align: center;
          flex-shrink: 0;
        }
        .exp-picker-logo {
          font-size: 3em;
          margin-bottom: 6px;
          filter: drop-shadow(0 0 20px rgba(102,126,234,0.4));
        }
        .exp-picker-title {
          font-size: 2em;
          font-weight: 800;
          background: linear-gradient(135deg, #667eea, #764ba2, #e84393);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin: 0;
        }
        .exp-picker-subtitle {
          color: var(--muted);
          font-size: 0.9em;
          margin-top: 6px;
        }
        .exp-category-tabs {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          justify-content: center;
          flex-shrink: 0;
        }
        .exp-cat-btn {
          padding: 8px 16px;
          border-radius: 20px;
          border: 1px solid var(--border);
          background: transparent;
          color: var(--text2);
          font-size: 0.88em;
          cursor: pointer;
          transition: all 0.25s;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .exp-cat-btn:hover {
          border-color: var(--purple);
          background: rgba(102,126,234,0.1);
          color: var(--purple);
        }
        .exp-cat-btn.active {
          background: linear-gradient(135deg, var(--purple), var(--violet));
          color: #fff;
          border-color: transparent;
          box-shadow: 0 4px 15px rgba(102,126,234,0.3);
        }
        .exp-cat-count {
          background: rgba(255,255,255,0.15);
          padding: 1px 7px;
          border-radius: 10px;
          font-size: 0.8em;
          font-weight: 600;
        }
        .exp-cat-btn.active .exp-cat-count {
          background: rgba(255,255,255,0.25);
        }
        .exp-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
          gap: 14px;
          flex: 1;
          overflow-y: auto;
          padding: 4px;
        }
        .exp-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 18px;
          cursor: pointer;
          transition: all 0.3s;
          position: relative;
          overflow: hidden;
        }
        .exp-card::before {
          content: '';
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 3px;
          background: linear-gradient(90deg, var(--card-accent, var(--purple)), transparent);
          opacity: 0;
          transition: opacity 0.3s;
        }
        .exp-card:hover {
          border-color: var(--purple);
          transform: translateY(-3px);
          box-shadow: 0 8px 25px rgba(102,126,234,0.15);
        }
        .exp-card:hover::before { opacity: 1; }
        .exp-card.selected {
          border-color: var(--purple);
          background: rgba(102,126,234,0.08);
          box-shadow: 0 0 20px rgba(102,126,234,0.2);
        }
        .exp-card.selected::before {
          opacity: 1;
          background: linear-gradient(90deg, var(--purple), var(--violet));
        }
        .exp-card-id {
          font-size: 0.7em;
          color: var(--muted);
          font-family: 'Consolas', monospace;
          margin-bottom: 6px;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .exp-card-id .exp-cat-icon {
          font-size: 1.3em;
        }
        .exp-card-name {
          font-size: 1.05em;
          font-weight: 700;
          margin-bottom: 6px;
          color: var(--text);
        }
        .exp-card-desc {
          font-size: 0.82em;
          color: var(--text2);
          line-height: 1.45;
          margin-bottom: 10px;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        .exp-card-meta {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }
        .exp-card-tag {
          font-size: 0.72em;
          padding: 2px 8px;
          border-radius: 6px;
          background: rgba(102,126,234,0.1);
          color: var(--purple);
          white-space: nowrap;
        }
        .exp-card-metrics {
          margin-top: 10px;
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
        }
        .exp-metric-chip {
          font-size: 0.68em;
          padding: 1px 6px;
          border-radius: 4px;
          background: rgba(255,255,255,0.04);
          color: var(--muted);
          border: 1px solid rgba(255,255,255,0.06);
        }
        .exp-config-panel {
          background: var(--card);
          border: 1px solid var(--purple);
          border-radius: 16px;
          flex-shrink: 0;
          overflow: hidden;
          animation: expSlideUp 0.35s ease-out;
          box-shadow: 0 -8px 40px rgba(102,126,234,0.15);
        }
        @keyframes expSlideUp {
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .exp-config-header {
          padding: 14px 20px;
          background: linear-gradient(135deg, rgba(102,126,234,0.12), rgba(118,75,162,0.08));
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .exp-config-icon { font-size: 1.3em; }
        .exp-config-label { font-weight: 700; font-size: 1em; }
        .exp-config-template-name {
          margin-left: auto;
          font-size: 0.85em;
          color: var(--purple);
          font-weight: 600;
        }
        .exp-config-body { padding: 18px 20px; }
        .exp-config-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }
        .exp-config-field {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .exp-config-field label {
          font-size: 0.82em;
          color: var(--text2);
          font-weight: 600;
        }
        .exp-config-field input,
        .exp-config-field select {
          background: rgba(255,255,255,0.06);
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 9px 12px;
          color: var(--text);
          font-size: 0.9em;
          outline: none;
          transition: 0.2s;
        }
        .exp-config-field input:focus,
        .exp-config-field select:focus {
          border-color: var(--purple);
          box-shadow: 0 0 10px rgba(102,126,234,0.2);
        }
        .exp-config-hint {
          font-size: 0.7em;
          color: var(--muted);
        }
        .exp-config-extra {
          margin-top: 14px;
          padding-top: 14px;
          border-top: 1px solid var(--border);
        }
        .exp-config-extra:empty {
          display: none;
          margin: 0;
          padding: 0;
          border: none;
        }
        .exp-config-footer {
          padding: 14px 20px;
          border-top: 1px solid var(--border);
          display: flex;
          justify-content: flex-end;
          gap: 12px;
        }
        .exp-cancel-btn {
          padding: 10px 22px;
          border-radius: 10px;
          border: 1px solid var(--border);
          background: transparent;
          color: var(--text2);
          font-size: 0.9em;
          cursor: pointer;
          transition: 0.2s;
        }
        .exp-cancel-btn:hover {
          border-color: #e74c3c;
          color: #e74c3c;
        }
        .exp-launch-btn {
          padding: 10px 30px;
          border-radius: 10px;
          border: none;
          background: linear-gradient(135deg, var(--purple), var(--violet));
          color: #fff;
          font-size: 1em;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.3s;
          box-shadow: 0 4px 15px rgba(102,126,234,0.3);
        }
        .exp-launch-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 25px rgba(102,126,234,0.45);
        }
        .exp-launch-btn:active {
          transform: translateY(0);
        }
        .exp-launch-btn.loading {
          pointer-events: none;
          opacity: 0.7;
        }
        .exp-card[data-cat="education"] { --card-accent: #95E1D3; }
        .exp-card[data-cat="business"]  { --card-accent: #4ECDC4; }
        .exp-card[data-cat="policy"]    { --card-accent: #667eea; }
        .exp-card[data-cat="social"]    { --card-accent: #FF6B6B; }
        .exp-card[data-cat="health"]    { --card-accent: #F38181; }
        .exp-card[data-cat="tech"]      { --card-accent: #a29bfe; }

        /* ============================================================ */
        /* 组件2: 模拟控制面板 样式 */
        /* ============================================================ */
        .sim-control {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(0, 0, 0, 0.25);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          padding: 5px 12px;
          flex-shrink: 0;
        }
        .sim-btn {
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 6px;
          color: #fff;
          font-size: 0.82em;
          padding: 5px 10px;
          cursor: pointer;
          transition: all 0.2s;
          white-space: nowrap;
        }
        .sim-btn:hover {
          background: rgba(102, 126, 234, 0.25);
          border-color: rgba(102, 126, 234, 0.5);
        }
        .sim-btn-play {
          font-size: 1em;
          padding: 5px 12px;
          background: rgba(102, 126, 234, 0.2);
          border-color: rgba(102, 126, 234, 0.4);
        }
        .sim-btn-play:hover {
          background: rgba(102, 126, 234, 0.4);
        }
        .sim-btn-play.playing {
          background: rgba(0, 184, 148, 0.25);
          border-color: rgba(0, 184, 148, 0.5);
          animation: simPulse 2s infinite;
        }
        @keyframes simPulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(0, 184, 148, 0.3); }
          50%      { box-shadow: 0 0 8px 3px rgba(0, 184, 148, 0.15); }
        }
        .sim-speed-group {
          display: flex;
          gap: 2px;
        }
        .sim-speed-btn {
          padding: 4px 8px;
          font-size: 0.75em;
          border-radius: 4px;
          font-weight: 600;
        }
        .sim-speed-btn.active {
          background: linear-gradient(135deg, var(--purple), var(--violet));
          border-color: var(--purple);
          color: #fff;
        }
        .sim-divider {
          width: 1px;
          height: 22px;
          background: rgba(255, 255, 255, 0.15);
          flex-shrink: 0;
        }
        .sim-progress-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .sim-progress-label {
          font-size: 0.72em;
          color: rgba(255, 255, 255, 0.5);
          white-space: nowrap;
        }
        .sim-progress-bar-wrap {
          width: 80px;
          height: 6px;
          background: rgba(255, 255, 255, 0.08);
          border-radius: 3px;
          overflow: hidden;
        }
        .sim-progress-bar {
          height: 100%;
          background: linear-gradient(90deg, var(--purple), var(--cyan));
          border-radius: 3px;
          transition: width 0.5s ease;
        }
        .sim-progress-text {
          font-size: 0.78em;
          color: rgba(255, 255, 255, 0.7);
          white-space: nowrap;
          min-width: 90px;
        }
        .sim-exp-name {
          font-size: 0.78em;
          color: var(--purple);
          font-weight: 600;
          max-width: 120px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .sim-btn-stop {
          font-size: 1em;
          padding: 4px 8px;
          background: rgba(231, 76, 60, 0.15);
          border-color: rgba(231, 76, 60, 0.3);
        }
        .sim-btn-stop:hover {
          background: rgba(231, 76, 60, 0.35);
          border-color: rgba(231, 76, 60, 0.6);
        }
        .sim-btn-new {
          font-size: 1em;
          padding: 4px 8px;
        }
        @media (max-width: 900px) {
          .sim-control {
            flex-wrap: wrap;
            gap: 5px;
            padding: 4px 8px;
          }
          .sim-progress-bar-wrap { width: 50px; }
          .sim-exp-name { display: none; }
        }

        /* ============================================================ */
        /* 组件3: 报告生成面板 样式 */
        /* ============================================================ */
        .report-fab {
          position: fixed;
          bottom: 24px;
          right: 24px;
          width: 52px;
          height: 52px;
          border-radius: 50%;
          background: linear-gradient(135deg, var(--purple), var(--violet));
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5em;
          cursor: pointer;
          z-index: 5000;
          box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
          transition: all 0.3s;
          border: none;
        }
        .report-fab:hover {
          transform: scale(1.1);
          box-shadow: 0 6px 30px rgba(102, 126, 234, 0.55);
        }
        .report-fab.active {
          background: linear-gradient(135deg, var(--violet), var(--pink));
          transform: rotate(45deg);
        }
        .report-panel {
          position: fixed;
          bottom: 88px;
          right: 24px;
          width: 340px;
          max-height: 70vh;
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 16px;
          z-index: 5001;
          box-shadow: 0 12px 50px rgba(0, 0, 0, 0.5);
          display: flex;
          flex-direction: column;
          overflow: hidden;
          animation: reportSlideUp 0.3s ease-out;
        }
        @keyframes reportSlideUp {
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .report-panel-header {
          padding: 14px 18px;
          background: linear-gradient(135deg, rgba(102,126,234,0.12), rgba(118,75,162,0.08));
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-shrink: 0;
        }
        .report-panel-title {
          font-weight: 700;
          font-size: 0.95em;
        }
        .report-close-btn {
          background: none;
          border: none;
          color: var(--muted);
          font-size: 1.1em;
          cursor: pointer;
          padding: 2px 6px;
          border-radius: 4px;
          transition: 0.2s;
        }
        .report-close-btn:hover {
          background: rgba(231, 76, 60, 0.15);
          color: #e74c3c;
        }
        .report-panel-body {
          padding: 16px 18px;
          overflow-y: auto;
          flex: 1;
        }
        .report-info {
          background: rgba(102, 126, 234, 0.06);
          border: 1px solid rgba(102, 126, 234, 0.15);
          border-radius: 10px;
          padding: 12px 14px;
          margin-bottom: 16px;
        }
        .report-info-row {
          display: flex;
          justify-content: space-between;
          padding: 3px 0;
          font-size: 0.82em;
        }
        .report-info-label { color: var(--muted); }
        .report-info-val { font-weight: 600; color: var(--text); }
        .report-section-title {
          font-size: 0.82em;
          font-weight: 700;
          color: var(--text2);
          margin-bottom: 10px;
          margin-top: 4px;
        }
        .report-format-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
          margin-bottom: 16px;
        }
        .report-format-option {
          cursor: pointer;
        }
        .report-format-option input {
          display: none;
        }
        .report-format-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          padding: 10px 6px;
          border: 1px solid var(--border);
          border-radius: 10px;
          background: transparent;
          transition: all 0.2s;
        }
        .report-format-card:hover {
          border-color: var(--purple);
          background: rgba(102, 126, 234, 0.06);
        }
        .report-format-option input:checked + .report-format-card {
          border-color: var(--purple);
          background: rgba(102, 126, 234, 0.12);
          box-shadow: 0 0 12px rgba(102, 126, 234, 0.15);
        }
        .report-format-icon { font-size: 1.5em; }
        .report-format-name { font-size: 0.78em; font-weight: 600; color: var(--text); }
        .report-format-ext  { font-size: 0.65em; color: var(--muted); }
        .report-content-options {
          display: flex;
          flex-direction: column;
          gap: 6px;
          margin-bottom: 12px;
        }
        .report-check {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 5px 8px;
          border-radius: 6px;
          font-size: 0.82em;
          color: var(--text2);
          cursor: pointer;
          transition: 0.2s;
        }
        .report-check:hover {
          background: rgba(255, 255, 255, 0.03);
        }
        .report-check input {
          accent-color: var(--purple);
          width: 14px;
          height: 14px;
          cursor: pointer;
        }
        .report-panel-footer {
          padding: 12px 18px;
          border-top: 1px solid var(--border);
          flex-shrink: 0;
        }
        .report-generate-btn {
          width: 100%;
          padding: 11px;
          border-radius: 10px;
          border: none;
          background: linear-gradient(135deg, var(--purple), var(--violet));
          color: #fff;
          font-size: 0.95em;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.3s;
          box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .report-generate-btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 6px 20px rgba(102, 126, 234, 0.45);
        }
        .report-generate-btn.loading {
          pointer-events: none;
          opacity: 0.7;
        }
        .report-progress {
          height: 3px;
          background: rgba(102, 126, 234, 0.1);
          flex-shrink: 0;
        }
        .report-progress-inner {
          height: 100%;
          background: linear-gradient(90deg, var(--purple), var(--cyan));
          transition: width 0.3s ease;
          border-radius: 0 0 16px 16px;
        }
        @media (max-width: 768px) {
          .report-panel {
            right: 10px;
            left: 10px;
            width: auto;
            bottom: 80px;
          }
          .report-fab {
            bottom: 16px;
            right: 16px;
            width: 46px;
            height: 46px;
            font-size: 1.3em;
          }
        }
    </style>
</head>
<body>
<!-- ============================================================ -->
<!-- 组件1: 实验模板选择页面 (全屏覆盖层) -->
<!-- ============================================================ -->
<div class="exp-picker-overlay" id="expPickerOverlay">
  <div class="exp-picker">
    <div class="exp-picker-header">
      <div class="exp-picker-logo">🧪</div>
      <h1 class="exp-picker-title">选择实验模板</h1>
      <p class="exp-picker-subtitle">御龙军虚拟 Agent 世界 · 实验场景库 v2.0 · 24 个模板</p>
    </div>
    <div class="exp-category-tabs">
      <button class="exp-cat-btn active" data-cat="all" onclick="filterCategory('all', this)">
        🌐 全部 <span class="exp-cat-count">24</span>
      </button>
      <button class="exp-cat-btn" data-cat="education" onclick="filterCategory('education', this)">
        📚 教育 <span class="exp-cat-count">4</span>
      </button>
      <button class="exp-cat-btn" data-cat="business" onclick="filterCategory('business', this)">
        💼 商业 <span class="exp-cat-count">4</span>
      </button>
      <button class="exp-cat-btn" data-cat="policy" onclick="filterCategory('policy', this)">
        🏛️ 政策 <span class="exp-cat-count">4</span>
      </button>
      <button class="exp-cat-btn" data-cat="social" onclick="filterCategory('social', this)">
        👥 社会 <span class="exp-cat-count">4</span>
      </button>
      <button class="exp-cat-btn" data-cat="health" onclick="filterCategory('health', this)">
        🏥 健康 <span class="exp-cat-count">4</span>
      </button>
      <button class="exp-cat-btn" data-cat="tech" onclick="filterCategory('tech', this)">
        💻 科技 <span class="exp-cat-count">4</span>
      </button>
    </div>
    <div class="exp-grid" id="expGrid"></div>
    <div class="exp-config-panel" id="expConfigPanel" style="display:none;">
      <div class="exp-config-header">
        <span class="exp-config-icon">⚙️</span>
        <span class="exp-config-label">参数配置</span>
        <span class="exp-config-template-name" id="expConfigName">--</span>
      </div>
      <div class="exp-config-body">
        <div class="exp-config-row">
          <div class="exp-config-field">
            <label>👥 Agent 数量</label>
            <input type="number" id="cfgAgentCount" value="10000" min="100" max="100000" step="100">
            <span class="exp-config-hint">100 ~ 100,000</span>
          </div>
          <div class="exp-config-field">
            <label>📅 模拟月数</label>
            <input type="number" id="cfgMonths" value="12" min="1" max="600" step="1">
            <span class="exp-config-hint">模板默认值已填入</span>
          </div>
          <div class="exp-config-field">
            <label>⏩ 时间倍速</label>
            <select id="cfgSpeed">
              <option value="1">1x (实时)</option>
              <option value="2">2x</option>
              <option value="5">5x</option>
              <option value="10" selected>10x</option>
              <option value="50">50x</option>
              <option value="100">100x</option>
            </select>
          </div>
          <div class="exp-config-field">
            <label>🌍 世界名称</label>
            <input type="text" id="cfgWorldName" value="world_experiment" placeholder="world_xxx">
          </div>
        </div>
        <div class="exp-config-extra" id="expConfigExtra"></div>
      </div>
      <div class="exp-config-footer">
        <button class="exp-cancel-btn" onclick="cancelExperiment()">✕ 取消</button>
        <button class="exp-launch-btn" id="expLaunchBtn" onclick="launchExperiment()">
          🚀 启动实验
        </button>
      </div>
    </div>
  </div>
</div>

<div class="map-tt" id="mtt"><div class="tt-n" id="ttn"></div><div class="tt-i" id="tti"></div></div>

<div class="header">
    <div style="display:flex;align-items:center;gap:14px">
        <h1>🌍 御龙军虚拟 Agent 世界 v4.0</h1>
        <span class="header-sub" id="htime">--</span>
    </div>
    <!-- 组件2: 模拟控制面板 -->
    <div class="sim-control" id="simControl">
      <button class="sim-btn sim-btn-play" id="simPlayBtn" onclick="simTogglePlay()" title="播放/暂停">
        <span id="simPlayIcon">▶️</span>
      </button>
      <div class="sim-speed-group">
        <button class="sim-btn sim-speed-btn" data-speed="1" onclick="simSetSpeed(1, this)">1x</button>
        <button class="sim-btn sim-speed-btn" data-speed="2" onclick="simSetSpeed(2, this)">2x</button>
        <button class="sim-btn sim-speed-btn active" data-speed="10" onclick="simSetSpeed(10, this)">10x</button>
        <button class="sim-btn sim-speed-btn" data-speed="100" onclick="simSetSpeed(100, this)">100x</button>
      </div>
      <div class="sim-divider"></div>
      <div class="sim-progress-info">
        <span class="sim-progress-label">进度</span>
        <div class="sim-progress-bar-wrap">
          <div class="sim-progress-bar" id="simProgressBar" style="width: 0%"></div>
        </div>
        <span class="sim-progress-text" id="simProgressText">第 0 / 0 月</span>
      </div>
      <div class="sim-divider"></div>
      <span class="sim-exp-name" id="simExpName" title="当前实验">--</span>
      <button class="sim-btn sim-btn-stop" onclick="simStop()" title="停止实验">⏹</button>
      <button class="sim-btn sim-btn-new" onclick="showExperimentPicker()" title="选择新实验">🧪</button>
    </div>
    <div class="world-sel">
        <select id="wsel" onchange="switchWorld()">
            <option value="world_alpha">🌐 主世界 Alpha</option>
            <option value="world_alpha_global">🌏 Alpha Global</option>
            <option value="world_alpha_v3">🧪 V3 实验世界</option>
        </select>
    </div>
</div>

<div class="kpi-bar">
    <div class="kpi"><div class="kpi-icon" style="background:rgba(102,126,234,.15)">👥</div><div><div class="kpi-label">总人口</div><div class="kpi-val" id="k-pop" style="color:var(--purple)">--</div><div class="kpi-delta" id="kd-pop"></div></div></div>
    <div class="kpi"><div class="kpi-icon" style="background:rgba(0,206,201,.15)">💼</div><div><div class="kpi-label">就业率</div><div class="kpi-val" id="k-emp" style="color:var(--cyan)">--%</div><div class="kpi-delta" id="kd-emp"></div></div></div>
    <div class="kpi"><div class="kpi-icon" style="background:rgba(253,203,110,.15)">💰</div><div><div class="kpi-label">平均月收入</div><div class="kpi-val" id="k-inc" style="color:var(--yellow)">$--</div><div class="kpi-delta" id="kd-inc"></div></div></div>
    <div class="kpi"><div class="kpi-icon" style="background:rgba(232,67,147,.15)">😊</div><div><div class="kpi-label">满意度</div><div class="kpi-val" id="k-sat" style="color:var(--pink)">--</div><div class="kpi-delta" id="kd-sat"></div></div></div>
</div>

<div class="main">
    <div class="panel left-p">
        <div class="p-head"><span class="p-title">📊 统计</span></div>
        <div class="p-body">
            <div id="stats-c"><div class="spinner-w"><div class="spin"></div><span>加载中...</span></div></div>
            <div class="legend-sec"><h4>🏘️ 区域</h4><div id="reg-leg"></div></div>
            <div class="legend-sec"><h4>👷 职业</h4><div id="occ-leg"></div></div>
            <div style="margin-top:14px;border-top:1px solid var(--border);padding-top:12px"><h4 style="font-size:.78em;color:var(--muted);margin-bottom:8px">🌹 职业分布</h4><div style="height:200px" id="occ-rose-wrap"><div id="occ-chart" style="width:100%;height:100%"></div></div></div>
        </div>
        <button class="refresh-btn" onclick="loadAll()">🔄 刷新</button>
    </div>

    <div class="panel center-p">
        <div class="p-head"><span class="p-title">🗺️ 区域地图</span><span style="font-size:.72em;color:var(--muted)" id="ac-lbl">0 agents</span></div>
        <div class="search-bar">
            <div style="position:relative;flex:1;min-width:120px"><span style="position:absolute;left:8px;top:50%;transform:translateY(-50%);font-size:.8em;pointer-events:none">🔍</span><input id="agent-search" type="text" placeholder="搜索 Agent 名字..." oninput="filterAgents()"></div>
            <select id="filter-occ" onchange="filterAgents()"><option value="">全部职业</option></select>
            <select id="filter-region" onchange="filterAgents()"><option value="">全部区域</option></select>
            <span class="search-cnt" id="search-cnt"></span>
        </div>
        <div class="p-body" style="padding:6px"><div id="region-map"><div class="spinner-w"><div class="spin"></div><span>加载地图...</span></div></div></div>
    </div>

    <div class="right-col">
        <div class="panel agent-panel">
            <div class="p-head"><span class="p-title">👤 Agent 详情</span></div>
            <div class="p-body" id="agent-det"><div class="agent-empty"><div style="font-size:2em">🔍</div><div>点击地图上的 Agent</div></div></div>
        </div>
        <div class="panel ev-panel">
            <div class="p-head"><span class="p-title">📰 事件流<span class="sse-status disconnected" id="sse-dot" title="SSE 状态"></span></span><span style="font-size:.7em;color:var(--muted)" id="ev-cnt">0</span></div>
            <div class="ev-filter">
                <button class="ev-btn on" onclick="fltEv('all',this)">全部</button>
                <button class="ev-btn" onclick="fltEv('birth',this)">👶</button>
                <button class="ev-btn" onclick="fltEv('death',this)">💀</button>
                <button class="ev-btn" onclick="fltEv('marriage',this)">🎉</button>
                <button class="ev-btn" onclick="fltEv('job',this)">💼</button>
                <button class="ev-btn" onclick="fltEv('epidemic',this)">🦠</button>
                <button class="ev-btn" onclick="fltEv('house',this)">🏠</button>
            </div>
            <div class="ev-list" id="ev-list"><div class="spinner-w"><div class="spin"></div><span>加载事件...</span></div></div>
        </div>
    </div>

    <div class="panel bottom">
        <div class="p-head">
            <span class="p-title">📈 趋势图</span>
            <div class="trend-selector" id="trend-selector">
                <label class="trend-cb"><input type="checkbox" checked onchange="onTrendToggle()" data-key="population"><span class="cb-dot" style="background:#667eea"></span>人口</label>
                <label class="trend-cb"><input type="checkbox" checked onchange="onTrendToggle()" data-key="avg_income"><span class="cb-dot" style="background:#fdcb6e"></span>收入</label>
                <label class="trend-cb"><input type="checkbox" onchange="onTrendToggle()" data-key="employment_rate"><span class="cb-dot" style="background:#00cec9"></span>就业率</label>
                <label class="trend-cb"><input type="checkbox" onchange="onTrendToggle()" data-key="satisfaction"><span class="cb-dot" style="background:#e84393"></span>满意度</label>
                <label class="trend-cb"><input type="checkbox" onchange="onTrendToggle()" data-key="health"><span class="cb-dot" style="background:#00b894"></span>健康</label>
                <label class="trend-cb"><input type="checkbox" onchange="onTrendToggle()" data-key="happiness"><span class="cb-dot" style="background:#a29bfe"></span>幸福</label>
                <label class="trend-cb"><input type="checkbox" onchange="onTrendToggle()" data-key="crime_rate"><span class="cb-dot" style="background:#d63031"></span>犯罪率</label>
            </div>
        </div>
        <div class="p-body"><div id="trend-chart"></div></div>
    </div>
</div>

<script>
// ===== STATE =====
const S={world:'world_alpha',agents:[],events:[],evFlt:'all',prev:null,occChart:null,trendChart:null,loading:false,activeRegion:null,roseChart:null};

const OCC_CLR={'农业':'#8B4513','制造业':'#708090','服务业':'#FF69B4','信息技术':'#4169E1','医疗':'#DC143C','教育':'#228B22','金融':'#DAA520','政府':'#9932CC','其他':'#808080'};
const REG_CFG={
    '商业区':{color:'rgba(78,205,196,.25)',bdr:'#4ECDC4',x:30,y:0,w:40,h:40},
    '住宅区':{color:'rgba(255,107,107,.25)',bdr:'#FF6B6B',x:0,y:0,w:30,h:50},
    '工业区':{color:'rgba(255,230,109,.2)',bdr:'#FFE66D',x:0,y:50,w:40,h:50},
    '教育区':{color:'rgba(149,225,211,.25)',bdr:'#95E1D3',x:70,y:0,w:30,h:35},
    '医疗区':{color:'rgba(243,129,129,.25)',bdr:'#F38181',x:70,y:35,w:30,h:30},
    '郊区':{color:'rgba(252,186,211,.2)',bdr:'#FCBAD3',x:40,y:65,w:60,h:35}
};
const EV_ICO={'birth':'👶','death':'💀','marriage':'🎉','job':'💼','epidemic':'🦠','house':'🏠','crime':'🚨','health':'🏥','misc':'📌'};

document.addEventListener('DOMContentLoaded',()=>{initTrend();loadAll();connectSSE();setInterval(()=>{loadStats();loadAgents();loadTrends()},5000)});

// ===== SSE =====
let _evtSource=null;
function connectSSE(){
    if(_evtSource){_evtSource.close();_evtSource=null}
    try{
        _evtSource=new EventSource('/api/events/stream?world='+S.world);
        _evtSource.onopen=()=>{const dot=document.getElementById('sse-dot');if(dot){dot.className='sse-status connected';dot.title='SSE connected'}};
        _evtSource.onmessage=(e)=>{try{const ev=JSON.parse(e.data);ev._new=true;S.events.unshift(ev);if(S.events.length>200)S.events.pop();renderEv()}catch(err){}};
        _evtSource.onerror=()=>{const dot=document.getElementById('sse-dot');if(dot){dot.className='sse-status disconnected';dot.title='SSE disconnected'}
            setTimeout(()=>{if(_evtSource&&_evtSource.readyState===2){_evtSource.close();_evtSource=null;setInterval(loadEvents,5000)}},15000)};
    }catch(err){setInterval(loadEvents,5000)}
}

function switchWorld(){S.world=document.getElementById('wsel').value;S.prev=null;connectSSE();loadAll()}

async function loadAll(){
    if(S.loading)return;S.loading=true;
    try{await Promise.all([loadStats(),loadAgents(),loadEvents(),loadTrends()])}
    catch(e){console.error(e)}
    finally{S.loading=false}
}

async function loadStats(){
    try{
        const r=await fetch('/api/stats?world='+S.world);const d=await r.json();if(d.error)return;
        renderKPI(d);renderStats(d);renderLeg(d);renderPie(d.occupation);S.prev=d;
    }catch(e){console.warn('stats err',e)}
}

async function loadAgents(){
    try{
        const r=await fetch('/api/agents?world='+S.world);const d=await r.json();
        S.agents=d.agents||[];
        document.getElementById('ac-lbl').textContent=S.agents.length+' agents';
        renderMap(S.agents);
    }catch(e){console.warn('agents err',e)}
}

async function loadEvents(){
    try{
        const r=await fetch('/api/events?limit=40&world='+S.world);
        if(!r.ok){mockEvents();return}
        const d=await r.json();S.events=d.events||[];renderEv();
    }catch(e){mockEvents()}
}

async function loadTrends(){
    try{
        const r=await fetch('/api/trends?world='+S.world);
        if(!r.ok){mockTrend();return}
        const d=await r.json();renderTrend(d);
    }catch(e){mockTrend()}
}

// ===== KPI =====
function renderKPI(d){
    const p=S.prev;
    setK('k-pop',d.population.toLocaleString(),'kd-pop',p?.population,d.population);
    setK('k-emp',d.employment_rate+'%','kd-emp',p?.employment_rate,d.employment_rate);
    setK('k-inc','$'+Math.round(d.avg_income).toLocaleString(),'kd-inc',p?.avg_income,d.avg_income);
    setK('k-sat',d.avg_satisfaction.toFixed(2),'kd-sat',p?.avg_satisfaction,d.avg_satisfaction);
    const t=d.time||{};
    document.getElementById('htime').textContent='📅 '+((t.year||2026))+'年 第'+(t.day||1)+'天 | '+new Date().toLocaleTimeString();
}
function setK(vid,txt,did,pv,cv){
    document.getElementById(vid).textContent=txt;
    const el=document.getElementById(did);
    if(pv!=null&&pv!==cv){const df=cv-pv;const a=df>0?'▲':'▼';el.className='kpi-delta '+(df>0?'up':'down');el.textContent=a+' '+(Math.abs(df)<1?df.toFixed(2):Math.round(df).toLocaleString())}
}

// ===== Stats Panel =====
function renderStats(d){
    const s=d.statistics||{};
    document.getElementById('stats-c').innerHTML=`
        <div class="stat-item"><span class="stat-label">世界时间</span><span class="stat-val">${(d.time?.year||2026)}年${(d.time?.day||1)}天</span></div>
        <div class="stat-item"><span class="stat-label">总出生</span><span class="stat-val">${(s.total_births||0).toLocaleString()}</span></div>
        <div class="stat-item"><span class="stat-label">总死亡</span><span class="stat-val">${(s.total_deaths||0).toLocaleString()}</span></div>
        <div class="stat-item"><span class="stat-label">总结婚</span><span class="stat-val">${(s.total_marriages||0).toLocaleString()}</span></div>`;
}

// ===== Legends =====
function renderLeg(d){
    let rh='';for(const[r,c]of Object.entries(d.region||{})){const cfg=REG_CFG[r];rh+=`<div class="leg-item"><div class="leg-dot" style="background:${cfg?cfg.bdr:'#888'}"></div><span>${r}</span><span class="leg-cnt">${c}</span></div>`}
    document.getElementById('reg-leg').innerHTML=rh;
    let oh='';for(const[o,c]of Object.entries(d.occupation||{})){oh+=`<div class="leg-item"><div class="leg-dot" style="background:${OCC_CLR[o]||'#888'}"></div><span>${o}</span><span class="leg-cnt">${c}</span></div>`}
    document.getElementById('occ-leg').innerHTML=oh;
}

// ===== Pie =====
function renderPie(occ){
    if(!occ)return;
    const dom=document.getElementById('occ-chart');if(!dom)return;
    if(!S.roseChart){S.roseChart=echarts.init(dom,null,{renderer:'canvas'});window.addEventListener('resize',()=>{if(S.roseChart)S.roseChart.resize()})}
    const data=Object.entries(occ).map(([name,value])=>({name,value,itemStyle:{color:OCC_CLR[name]||'#888'}}));
    S.roseChart.setOption({backgroundColor:'transparent',tooltip:{trigger:'item',backgroundColor:'rgba(22,33,62,.95)',borderColor:'rgba(102,126,234,.4)',textStyle:{color:'#edf2f7',fontSize:11},formatter:'{b}: {c} ({d}%)'},
        series:[{type:'pie',roseType:'area',radius:['15%','75%'],center:['50%','52%'],data:data,label:{color:'#a0aec0',fontSize:10,formatter:'{b}'},labelLine:{lineStyle:{color:'rgba(160,174,192,.3)'}},itemStyle:{borderRadius:4,borderColor:'rgba(15,14,23,.6)',borderWidth:2},emphasis:{itemStyle:{shadowBlur:12,shadowColor:'rgba(0,0,0,.3)'}},animationType:'scale',animationEasing:'elasticOut',animationDuration:800}]
    },true);
}

// ===== Region Map =====
function renderMap(agents){
    const m=document.getElementById('region-map');m.innerHTML='';
    const ra={};for(const r of Object.keys(REG_CFG))ra[r]=[];
    agents.forEach(a=>{const r=a.region||'住宅区';if(!ra[r])ra[r]=[];ra[r].push(a)});

    for(const[name,cfg]of Object.entries(REG_CFG)){
        const b=document.createElement('div');b.className='reg-block';b.dataset.region=name;
        b.style.cssText=`left:${cfg.x}%;top:${cfg.y}%;width:${cfg.w}%;height:${cfg.h}%;background:${cfg.color};border:2px solid ${cfg.bdr}40;cursor:pointer`;
        const l=document.createElement('div');l.className='reg-lbl';l.textContent=name;b.appendChild(l);
        const c=document.createElement('div');c.className='reg-cnt';c.textContent=(ra[name]||[]).length+'人';b.appendChild(c);
        b.addEventListener('click',(ev)=>{ev.stopPropagation();toggleRegionPopup(name,b,ra[name]||[],cfg)});
        m.appendChild(b);

        (ra[name]||[]).forEach(a=>{
            const d=document.createElement('div');d.className='adot';
            d.style.left=a.x+'%';d.style.top=a.y+'%';
            d.style.background=OCC_CLR[a.occupation]||'#888';
            d._agentData=a;
            d.addEventListener('click',()=>showDetail(a));
            d.addEventListener('mouseenter',e=>showTT(e,a));
            d.addEventListener('mouseleave',hideTT);
            m.appendChild(d);
        });
    }
    populateFilters();
    filterAgents();
}

// ===== Search/Filter =====
function populateFilters(){
    const occSet=new Set(),regSet=new Set();
    S.agents.forEach(a=>{if(a.occupation)occSet.add(a.occupation);if(a.region)regSet.add(a.region)});
    const occSel=document.getElementById('filter-occ'),regSel=document.getElementById('filter-region');
    const curOcc=occSel.value,curReg=regSel.value;
    occSel.innerHTML='<option value="">全部职业</option>'+[...occSet].sort().map(o=>`<option value="${o}"${o===curOcc?' selected':''}>${o}</option>`).join('');
    regSel.innerHTML='<option value="">全部区域</option>'+[...regSet].sort().map(r=>`<option value="${r}"${r===curReg?' selected':''}>${r}</option>`).join('');
}
function filterAgents(){
    const q=(document.getElementById('agent-search').value||'').trim().toLowerCase();
    const occ=document.getElementById('filter-occ').value;
    const reg=document.getElementById('filter-region').value;
    const dots=document.querySelectorAll('.adot');
    let matchCount=0;const hasFilter=q||occ||reg;
    dots.forEach(dot=>{
        const a=dot._agentData;if(!a){dot.classList.remove('dimmed','highlighted');return}
        const match=(!q||a.name.toLowerCase().includes(q))&&(!occ||a.occupation===occ)&&(!reg||a.region===reg);
        if(!hasFilter){dot.classList.remove('dimmed','highlighted')}
        else if(match){dot.classList.remove('dimmed');dot.classList.add('highlighted');matchCount++}
        else{dot.classList.add('dimmed');dot.classList.remove('highlighted')}
    });
    const el=document.getElementById('search-cnt');
    el.textContent=hasFilter?matchCount+'/'+S.agents.length+' 匹配':'';
}

// ===== Region Popup =====
function toggleRegionPopup(regionName,blockEl,regionAgents,cfg){
    const oldPopup=document.querySelector('.region-popup');if(oldPopup)oldPopup.remove();
    const blocks=document.querySelectorAll('.reg-block');
    if(S.activeRegion===regionName){S.activeRegion=null;blocks.forEach(b=>{b.classList.remove('active','dimmed-region');b.style.borderWidth='2px'});return}
    S.activeRegion=regionName;
    blocks.forEach(b=>{
        if(b.dataset.region===regionName){b.classList.add('active');b.classList.remove('dimmed-region');b.style.borderWidth='3px';b.style.borderColor=cfg.bdr}
        else{b.classList.remove('active');b.classList.add('dimmed-region');b.style.borderWidth='2px'}
    });
    const n=Math.max(regionAgents.length,1);
    const avgInc=Math.round(regionAgents.reduce((s,a)=>s+(a.income||0),0)/n);
    const avgSat=(regionAgents.reduce((s,a)=>s+(a.satisfaction||3),0)/n).toFixed(2);
    const occCount={};regionAgents.forEach(a=>{const o=a.occupation||'其他';occCount[o]=(occCount[o]||0)+1});
    const topOcc=Object.entries(occCount).sort((a,b)=>b[1]-a[1]).slice(0,5);
    const icons={'商业区':'🏢','住宅区':'🏠','工业区':'🏭','教育区':'🎓','医疗区':'🏥','郊区':'🌾'};
    const popup=document.createElement('div');popup.className='region-popup';
    const mapEl=document.getElementById('region-map');
    const mapRect=mapEl.getBoundingClientRect();const blockRect=blockEl.getBoundingClientRect();
    let popLeft=blockRect.left-mapRect.left+blockRect.width/2;
    let popTop=blockRect.top-mapRect.top+blockRect.height+5;
    if(popLeft+220>mapEl.clientWidth)popLeft=mapEl.clientWidth-230;
    if(popLeft<0)popLeft=10;
    if(popTop+200>mapEl.clientHeight)popTop=blockRect.top-mapRect.top-210;
    popup.style.left=popLeft+'px';popup.style.top=popTop+'px';
    popup.innerHTML=`<button class="close-btn" onclick="this.parentElement.remove();resetRegionHighlight()">✕</button>
        <h3>${icons[regionName]||'📍'} ${regionName}</h3>
        <div class="rp-row"><span class="rp-label">人数</span><span class="rp-val">${regionAgents.length}</span></div>
        <div class="rp-row"><span class="rp-label">平均收入</span><span class="rp-val">$${avgInc.toLocaleString()}</span></div>
        <div class="rp-row"><span class="rp-label">满意度</span><span class="rp-val">${avgSat}</span></div>
        <div class="rp-occ"><div style="color:var(--muted);font-size:.85em;margin-bottom:4px">主要职业：</div>${topOcc.map(([o,c])=>`<div class="rp-occ-item"><span style="display:flex;align-items:center;gap:4px"><span style="width:6px;height:6px;border-radius:2px;background:${OCC_CLR[o]||'#888'}"></span>${o}</span><span>${c}</span></div>`).join('')}</div>`;
    mapEl.appendChild(popup);
}
function resetRegionHighlight(){S.activeRegion=null;document.querySelectorAll('.reg-block').forEach(b=>{b.classList.remove('active','dimmed-region');b.style.borderWidth='2px'})}

function showTT(e,a){const t=document.getElementById('mtt');document.getElementById('ttn').textContent=a.name+' ('+a.age+'岁)';document.getElementById('tti').textContent=a.occupation+' | '+a.region+' | $'+(a.income||0).toLocaleString()+'/月';t.style.display='block';t.style.left=(e.clientX+12)+'px';t.style.top=(e.clientY-10)+'px'}
function hideTT(){document.getElementById('mtt').style.display='none'}

// ===== Agent Detail =====
async function showDetail(ag){
    try{
        const r=await fetch('/api/agent/'+ag.id+'?world='+S.world);const d=await r.json();
        if(d.error)throw 0;const a=d.agent;const region=d.region||ag.region||'';
        const clr=OCC_CLR[a.occupation]||'#667eea';
        document.getElementById('agent-det').innerHTML=`
            <div class="agent-hdr"><div class="agent-av" style="background:${clr}30;color:${clr}">${a.gender==='男'?'👨':a.gender==='女'?'👩':'🧑'}</div>
            <div><div class="agent-name">${a.name}</div><span class="agent-tag" style="background:${clr}22;color:${clr}">${a.occupation}</span></div></div>
            <div class="d-row"><span class="lb">年龄</span><span class="vl">${a.age}岁</span></div>
            <div class="d-row"><span class="lb">性别</span><span class="vl">${a.gender}</span></div>
            <div class="d-row"><span class="lb">国籍</span><span class="vl">${a.nationality||'未知'}</span></div>
            <div class="d-row"><span class="lb">月收入</span><span class="vl">$${(a.income_monthly||0).toLocaleString()}</span></div>
            <div class="d-row"><span class="lb">技能</span><span class="vl">${a.skill_level||'--'}</span></div>
            <div class="d-row"><span class="lb">教育</span><span class="vl">${a.education||'未知'}</span></div>
            <div class="d-row"><span class="lb">满意度</span><span class="vl">${(a.satisfaction||0).toFixed(2)} ⭐</span></div>
            <div class="d-row"><span class="lb">区域</span><span class="vl">${region}</span></div>`;
    }catch(e){
        const a=ag;document.getElementById('agent-det').innerHTML=`
            <div class="agent-hdr"><div class="agent-av" style="background:rgba(102,126,234,.2)">🧑</div><div><div class="agent-name">${a.name}</div></div></div>
            <div class="d-row"><span class="lb">职业</span><span class="vl">${a.occupation}</span></div>
            <div class="d-row"><span class="lb">收入</span><span class="vl">$${(a.income||0).toLocaleString()}</span></div>`;
    }
}

// ===== Events =====
function renderEv(){
    const el=document.getElementById('ev-list');
    let evs=S.events;
    if(S.evFlt!=='all')evs=evs.filter(e=>e.type===S.evFlt);
    document.getElementById('ev-cnt').textContent=evs.length+' events';
    if(!evs.length){el.innerHTML='<div class="spinner-w" style="padding:20px"><span style="color:var(--muted)">暂无事件</span></div>';return}
    el.innerHTML=evs.map(e=>`<div class="ev-item${e._new?' new-pulse':''}"><div class="ev-ico">${e.emoji||EV_ICO[e.type]||'📌'}</div><div><div class="ev-txt">${e.text||e.description||''}</div><div class="ev-time">${e.time||e.timestamp||''}</div></div></div>`).join('');
    el.scrollTop=0;
    setTimeout(()=>{S.events.forEach(e=>{e._new=false})},900);
}
function fltEv(t,btn){S.evFlt=t;document.querySelectorAll('.ev-btn').forEach(b=>b.classList.remove('on'));btn.classList.add('on');renderEv()}

function mockEvents(){
    if(!S.agents.length){S.events=[];renderEv();return}
    const types=['birth','death','marriage','job','house'];
    const tpl={birth:a=>`<strong>${a.name}</strong> 来到了这个世界`,death:a=>`<strong>${a.name}</strong> (${a.age}岁) 去世了`,marriage:a=>`<strong>${a.name}</strong> 结婚了 🎊`,job:a=>`<strong>${a.name}</strong> 换了新工作：${a.occupation}`,house:a=>`<strong>${a.name}</strong> 在${a.region||'住宅区'}买了房`};
    const evs=[];for(let i=0;i<Math.min(25,S.agents.length);i++){const a=S.agents[Math.floor(Math.random()*S.agents.length)];const t=types[Math.floor(Math.random()*types.length)];evs.push({type:t,emoji:EV_ICO[t],text:tpl[t](a),time:'Day '+(Math.floor(Math.random()*365)+1)})}
    S.events=evs;renderEv();
}

// ===== ECharts Trend =====
function initTrend(){
    const d=document.getElementById('trend-chart');if(!d)return;
    S.trendChart=echarts.init(d,null,{renderer:'canvas'});
    window.addEventListener('resize',()=>{if(S.trendChart)S.trendChart.resize()});
}

// ===== Trend Metrics =====
const TREND_METRICS={
    population:{name:'人口',color:'#667eea',yAxis:0,area:true},
    avg_income:{name:'收入',color:'#fdcb6e',yAxis:0,area:true},
    employment_rate:{name:'就业率(%)',color:'#00cec9',yAxis:1,area:false},
    satisfaction:{name:'满意度',color:'#e84393',yAxis:1,area:false,dashed:true,transform:v=>v>5?v:+(v*20).toFixed(1)},
    health:{name:'健康',color:'#00b894',yAxis:1,area:false},
    happiness:{name:'幸福',color:'#a29bfe',yAxis:1,area:false,dashed:true},
    crime_rate:{name:'犯罪率',color:'#d63031',yAxis:1,area:false,dashed:true}
};
let _trendRawData=null;
function getActiveTrendKeys(){return [...document.querySelectorAll('#trend-selector input[type=checkbox]')].filter(cb=>cb.checked).map(cb=>cb.dataset.key)}
function onTrendToggle(){
    const active=getActiveTrendKeys();
    if(active.length<1){document.querySelector('#trend-selector input[type=checkbox]').checked=true;return}
    if(active.length>4){[...document.querySelectorAll('#trend-selector input:checked')].pop().checked=false;return}
    if(_trendRawData)renderTrend(_trendRawData);
}
function renderTrend(d){
    if(!S.trendChart)return;
    _trendRawData=d;
    const xData=d.days||d.labels||[];
    const dataMap={population:d.population||(d.series&&d.series.population)||[],avg_income:d.avg_income||(d.series&&d.series.avg_income)||[],employment_rate:d.employment_rate||(d.series&&d.series.employment_rate)||[],satisfaction:d.satisfaction||(d.series&&d.series.avg_satisfaction)||[],health:d.health||(d.series&&d.series.health)||[],happiness:d.happiness||(d.series&&d.series.happiness)||[],crime_rate:d.crime_rate||(d.series&&d.series.crime_rate)||[]};
    const activeKeys=getActiveTrendKeys();const series=[];const legendData=[];
    activeKeys.forEach(key=>{
        const m=TREND_METRICS[key];if(!m)return;let data=dataMap[key]||[];if(m.transform)data=data.map(m.transform);legendData.push(m.name);
        const s={name:m.name,type:'line',data:data,smooth:true,symbol:'none',lineStyle:{width:2,color:m.color},animationDuration:800,animationEasing:'cubicOut'};
        if(m.yAxis===1)s.yAxisIndex=1;if(m.dashed)s.lineStyle.type='dashed';
        if(m.area)s.areaStyle={color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:m.color+'26'},{offset:1,color:'rgba(0,0,0,0)'}])};
        series.push(s);
    });
    S.trendChart.setOption({backgroundColor:'transparent',tooltip:{trigger:'axis',backgroundColor:'rgba(22,33,62,.95)',borderColor:'rgba(102,126,234,.4)',textStyle:{color:'#edf2f7',fontSize:11}},
        legend:{data:legendData,textStyle:{color:'#a0aec0',fontSize:10},top:0,itemWidth:14,itemHeight:3},
        grid:{left:50,right:50,top:30,bottom:22},
        xAxis:{type:'category',data:xData,axisLine:{lineStyle:{color:'rgba(102,126,234,.3)'}},axisLabel:{color:'#718096',fontSize:9},axisTick:{show:false}},
        yAxis:[{type:'value',axisLine:{show:false},axisLabel:{color:'#718096',fontSize:9},splitLine:{lineStyle:{color:'rgba(102,126,234,.08)'}}},{type:'value',axisLine:{show:false},axisLabel:{color:'#718096',fontSize:9},splitLine:{show:false},min:0,max:100}],
        series:series,animation:true,animationDuration:800,animationEasing:'cubicOut'
    },true);
}

function mockTrend(){
    const d=[],p=[],inc=[],e=[],s=[];
    let pp=1000,ii=3000,ee=65,ss=3;
    for(let i=1;i<=24;i++){d.push('M'+i);pp+=Math.floor(Math.random()*20-5);ii+=Math.floor(Math.random()*200-80);ee+=(Math.random()-.45)*2;ss+=(Math.random()-.45)*.1;p.push(Math.max(500,pp));inc.push(Math.max(1000,ii));e.push(+Math.min(100,Math.max(30,ee)).toFixed(1));s.push(+Math.min(5,Math.max(1,ss)).toFixed(2))}
    renderTrend({days:d,population:p,avg_income:inc,employment_rate:e,satisfaction:s});
}

/* ============================================================ */
/* 组件1: 实验模板选择页面 JS */
/* ============================================================ */

const EXPERIMENT_TEMPLATES = [
  { id: 'edu_001', name: '教育政策验证', cat: 'education', icon: '📚',
    desc: '测试不同教育政策对学生升学率和就业的影响',
    months: 216, agents: 5000,
    metrics: ['升学率', '就业率', '平均收入', '教育满意度'],
    params: { education_policy: 'baseline', university_capacity: 0.5 } },
  { id: 'edu_002', name: '教育公平性研究', cat: 'education', icon: '📚',
    desc: '研究不同社会经济背景学生的教育机会差异',
    months: 144, agents: 10000,
    metrics: ['阶层流动性', '教育基尼系数', '奖学金覆盖率'],
    params: { income_inequality: 0.4, scholarship_coverage: 0.3 } },
  { id: 'edu_003', name: '在线教育影响', cat: 'education', icon: '📚',
    desc: '评估在线教育对传统教育的冲击和补充作用',
    months: 60, agents: 3000,
    metrics: ['在线课程注册率', '学习效果对比', '成本效益'],
    params: { online_platform_adoption: 0.5, internet_access: 0.9 } },
  { id: 'edu_004', name: '终身学习社会', cat: 'education', icon: '📚',
    desc: '模拟终身学习文化对职业发展的影响',
    months: 240, agents: 5000,
    metrics: ['成人学习参与率', '职业转换率', '收入增长'],
    params: { lifelong_learning_culture: 0.7, employer_training_support: 0.5 } },

  { id: 'biz_001', name: '产品上市策略', cat: 'business', icon: '💼',
    desc: '测试不同产品上市策略的市场表现',
    months: 36, agents: 10000,
    metrics: ['市场渗透率', '用户增长率', '客户满意度', '利润率'],
    params: { launch_strategy: 'premium', marketing_budget: 1000000 } },
  { id: 'biz_002', name: '营销策略对比', cat: 'business', icon: '💼',
    desc: '对比不同营销策略的 ROI',
    months: 24, agents: 5000,
    metrics: ['转化率', '客户获取成本', '品牌知名度', 'ROI'],
    params: { strategy_a: 'digital_marketing', budget_split: 0.5 } },
  { id: 'biz_003', name: '组织变革管理', cat: 'business', icon: '💼',
    desc: '模拟企业组织变革对员工满意度和绩效的影响',
    months: 18, agents: 2000,
    metrics: ['员工满意度', '离职率', '生产率', '变革接受度'],
    params: { change_type: 'digital_transformation', communication_quality: 0.7 } },
  { id: 'biz_004', name: '创业生态系统', cat: 'business', icon: '💼',
    desc: '研究创业生态系统对创新和就业的影响',
    months: 60, agents: 10000,
    metrics: ['创业率', '初创企业存活率', '创新指数', '就业创造'],
    params: { vc_availability: 0.5, failure_tolerance: 0.7 } },

  { id: 'pol_001', name: '税收政策评估', cat: 'policy', icon: '🏛️',
    desc: '评估不同税收政策对经济和社会的影响',
    months: 60, agents: 10000,
    metrics: ['GDP 增长', '贫富差距', '税收收入', '投资率'],
    params: { tax_system: 'progressive', corporate_tax_rate: 0.25 } },
  { id: 'pol_002', name: '全民基本收入', cat: 'policy', icon: '🏛️',
    desc: '模拟 UBI 对就业、贫困和幸福感的影响',
    months: 60, agents: 10000,
    metrics: ['就业率', '贫困率', '幸福感', '创业率'],
    params: { ubi_amount: 2000, funding_source: 'income_tax' } },
  { id: 'pol_003', name: '住房政策研究', cat: 'policy', icon: '🏛️',
    desc: '研究住房政策对房价和自有率的影响',
    months: 120, agents: 5000,
    metrics: ['房价收入比', '住房自有率', '租房负担', '无家可归率'],
    params: { policy_type: 'affordable_housing', public_housing_ratio: 0.2 } },
  { id: 'pol_004', name: '医疗改革方案', cat: 'policy', icon: '🏛️',
    desc: '比较不同医疗体系的成本和效果',
    months: 120, agents: 10000,
    metrics: ['人均医疗支出', '预期寿命', '满意度', '等待时间'],
    params: { system_type: 'single_payer', government_funding: 0.7 } },

  { id: 'soc_001', name: '城市化进程', cat: 'social', icon: '👥',
    desc: '模拟城市化对经济、环境和社会的影响',
    months: 240, agents: 20000,
    metrics: ['城市化率', '城乡收入差距', '通勤时间', '生活质量'],
    params: { urban_job_growth: 0.03, migration_policy: 'open' } },
  { id: 'soc_002', name: '人口老龄化', cat: 'social', icon: '👥',
    desc: '研究老龄化社会对经济和福利系统的挑战',
    months: 360, agents: 10000,
    metrics: ['抚养比', '养老金可持续性', '医疗支出', '劳动力供给'],
    params: { fertility_rate: 1.5, retirement_age: 65 } },
  { id: 'soc_003', name: '社会流动性', cat: 'social', icon: '👥',
    desc: '研究影响社会阶层流动性的因素',
    months: 240, agents: 10000,
    metrics: ['代际收入弹性', '教育流动性', '职业流动性'],
    params: { meritocracy_level: 0.7, discrimination_level: 0.1 } },
  { id: 'soc_004', name: '文化融合', cat: 'social', icon: '👥',
    desc: '模拟多元文化社会的融合过程',
    months: 240, agents: 10000,
    metrics: ['文化多样性指数', '社会凝聚力', '歧视事件', '通婚率'],
    params: { immigration_rate: 0.02, integration_policy: 'multicultural' } },

  { id: 'hlt_001', name: '流行病传播', cat: 'health', icon: '🏥',
    desc: '模拟传染病传播和防控措施效果',
    months: 24, agents: 10000,
    metrics: ['感染率', '死亡率', '医疗挤兑', '经济损失'],
    params: { r0: 2.5, fatality_rate: 0.02, intervention: 'lockdown' } },
  { id: 'hlt_002', name: '心理健康危机', cat: 'health', icon: '🏥',
    desc: '研究社会压力对心理健康的影响',
    months: 60, agents: 5000,
    metrics: ['抑郁率', '焦虑率', '自杀率', '治疗覆盖率'],
    params: { social_pressure: 0.7, mental_health_services: 0.6 } },
  { id: 'hlt_003', name: '健康生活方式推广', cat: 'health', icon: '🏥',
    desc: '评估健康生活方式干预的效果',
    months: 60, agents: 5000,
    metrics: ['肥胖率', '运动参与率', '慢性病发病率', '医疗支出'],
    params: { intervention_type: 'education', healthy_food_access: 0.7 } },
  { id: 'hlt_004', name: '医疗资源分配', cat: 'health', icon: '🏥',
    desc: '优化医疗资源分配策略',
    months: 120, agents: 10000,
    metrics: ['等待时间', '治疗可及性', '健康结果', '成本效益'],
    params: { allocation_method: 'need_based', telemedicine_adoption: 0.6 } },

  { id: 'tech_001', name: '技术扩散模式', cat: 'tech', icon: '💻',
    desc: '研究新技术在社会中的扩散规律',
    months: 120, agents: 10000,
    metrics: ['采用率', '扩散速度', '创新者比例', '数字鸿沟'],
    params: { innovation_type: 'disruptive', network_effect: 0.7 } },
  { id: 'tech_002', name: 'AI 自动化影响', cat: 'tech', icon: '💻',
    desc: '评估 AI 自动化对就业和经济的影响',
    months: 120, agents: 10000,
    metrics: ['失业率', '生产率', '收入不平等', '新岗位创造'],
    params: { automation_rate: 0.03, reskilling_program: 0.5 } },
  { id: 'tech_003', name: '社交媒体影响', cat: 'tech', icon: '💻',
    desc: '研究社交媒体对信息传播和社会舆论的影响',
    months: 36, agents: 10000,
    metrics: ['信息传播速度', '极化程度', '假新闻传播', '社会信任'],
    params: { platform_penetration: 0.7, fact_checking: 0.6 } },
  { id: 'tech_004', name: '绿色技术转型', cat: 'tech', icon: '💻',
    desc: '模拟绿色技术转型的经济和环境效应',
    months: 240, agents: 10000,
    metrics: ['碳排放', '绿色就业', '转型成本', '能源独立性'],
    params: { carbon_tax: 50, renewable_subsidy: 0.3 } },
];

const CAT_NAMES = {
  education: '📚 教育', business: '💼 商业', policy: '🏛️ 政策',
  social: '👥 社会', health: '🏥 健康', tech: '💻 科技'
};

let selectedTemplate = null;
let currentCatFilter = 'all';

function initExperimentPicker() {
  renderTemplateCards();
}

function renderTemplateCards(category) {
  category = category || 'all';
  const grid = document.getElementById('expGrid');
  const templates = category === 'all'
    ? EXPERIMENT_TEMPLATES
    : EXPERIMENT_TEMPLATES.filter(function(t){ return t.cat === category; });

  grid.innerHTML = templates.map(function(t){
    return '<div class="exp-card" data-cat="'+t.cat+'" data-id="'+t.id+'" onclick="selectTemplate(\\x27'+t.id+'\\x27)">'
      + '<div class="exp-card-id"><span class="exp-cat-icon">'+t.icon+'</span> '+t.id+'</div>'
      + '<div class="exp-card-name">'+t.name+'</div>'
      + '<div class="exp-card-desc">'+t.desc+'</div>'
      + '<div class="exp-card-meta">'
      + '<span class="exp-card-tag">👥 '+t.agents.toLocaleString()+'</span>'
      + '<span class="exp-card-tag">📅 '+t.months+'月</span>'
      + '<span class="exp-card-tag">📊 '+t.metrics.length+'指标</span>'
      + '</div>'
      + '<div class="exp-card-metrics">'
      + t.metrics.map(function(m){ return '<span class="exp-metric-chip">'+m+'</span>'; }).join('')
      + '</div></div>';
  }).join('');
}

function filterCategory(cat, btn) {
  currentCatFilter = cat;
  document.querySelectorAll('.exp-cat-btn').forEach(function(b){ b.classList.remove('active'); });
  btn.classList.add('active');
  renderTemplateCards(cat);

  if (selectedTemplate && cat !== 'all') {
    var t = EXPERIMENT_TEMPLATES.find(function(t){ return t.id === selectedTemplate; });
    if (t && t.cat !== cat) {
      selectedTemplate = null;
      document.getElementById('expConfigPanel').style.display = 'none';
    }
  }
  if (selectedTemplate) {
    var card = document.querySelector('.exp-card[data-id="'+selectedTemplate+'"]');
    if (card) card.classList.add('selected');
  }
}

function selectTemplate(templateId) {
  var t = EXPERIMENT_TEMPLATES.find(function(t){ return t.id === templateId; });
  if (!t) return;

  selectedTemplate = templateId;
  document.querySelectorAll('.exp-card').forEach(function(c){ c.classList.remove('selected'); });
  var card = document.querySelector('.exp-card[data-id="'+templateId+'"]');
  if (card) card.classList.add('selected');

  document.getElementById('expConfigPanel').style.display = '';
  document.getElementById('expConfigName').textContent = '['+t.id+'] '+t.name;
  document.getElementById('cfgAgentCount').value = t.agents;
  document.getElementById('cfgMonths').value = t.months;
  document.getElementById('cfgWorldName').value = 'world_'+t.id.replace('_', '');

  var extra = document.getElementById('expConfigExtra');
  var paramEntries = Object.entries(t.params);
  if (paramEntries.length > 0) {
    extra.innerHTML = '<div style="font-size:0.82em;color:var(--muted);margin-bottom:10px;font-weight:600">📋 模板专属参数</div>'
      + '<div class="exp-config-row">'
      + paramEntries.map(function(kv){
          return '<div class="exp-config-field"><label>'+kv[0]+'</label>'
            + '<input type="text" value="'+kv[1]+'" data-param="'+kv[0]+'" class="exp-extra-param">'
            + '</div>';
        }).join('')
      + '</div>';
  } else {
    extra.innerHTML = '';
  }

  document.getElementById('expConfigPanel').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function cancelExperiment() {
  selectedTemplate = null;
  document.querySelectorAll('.exp-card').forEach(function(c){ c.classList.remove('selected'); });
  document.getElementById('expConfigPanel').style.display = 'none';
}

async function launchExperiment() {
  if (!selectedTemplate) return;

  var t = EXPERIMENT_TEMPLATES.find(function(t){ return t.id === selectedTemplate; });
  var btn = document.getElementById('expLaunchBtn');
  btn.classList.add('loading');
  btn.textContent = '⏳ 启动中...';

  var config = {
    template_id: selectedTemplate,
    agent_count: parseInt(document.getElementById('cfgAgentCount').value),
    duration_months: parseInt(document.getElementById('cfgMonths').value),
    speed: parseInt(document.getElementById('cfgSpeed').value),
    world_name: document.getElementById('cfgWorldName').value,
    extra_params: {},
  };

  document.querySelectorAll('.exp-extra-param').forEach(function(el){
    config.extra_params[el.dataset.param] = el.value;
  });

  try {
    var resp = await fetch('/api/experiment/launch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    var data = await resp.json();

    if (data.error) {
      alert('启动失败: ' + data.error);
      btn.classList.remove('loading');
      btn.textContent = '🚀 启动实验';
      return;
    }

    document.getElementById('expPickerOverlay').classList.add('hidden');

    S.world = config.world_name;
    simState.running = true;
    simState.speed = config.speed;
    simState.currentMonth = 0;
    simState.totalMonths = config.duration_months;
    simState.templateId = selectedTemplate;
    simState.templateName = t.name;

    updateSimControlUI();
    loadAll();
  } catch (e) {
    alert('启动失败: ' + e.message);
  } finally {
    btn.classList.remove('loading');
    btn.textContent = '🚀 启动实验';
  }
}

function showExperimentPicker() {
  document.getElementById('expPickerOverlay').classList.remove('hidden');
}

/* ============================================================ */
/* 组件2: 模拟控制面板 JS */
/* ============================================================ */

var simState = {
  running: false,
  paused: false,
  speed: 10,
  currentMonth: 0,
  totalMonths: 0,
  templateId: null,
  templateName: '',
  intervalId: null,
};

function simTogglePlay() {
  if (!simState.running) {
    showExperimentPicker();
    return;
  }

  simState.paused = !simState.paused;
  updateSimControlUI();

  if (simState.paused) {
    if (simState.intervalId) {
      clearInterval(simState.intervalId);
      simState.intervalId = null;
    }
  } else {
    startSimLoop();
  }
}

function simSetSpeed(speed, btn) {
  simState.speed = speed;
  document.querySelectorAll('.sim-speed-btn').forEach(function(b){ b.classList.remove('active'); });
  if (btn) btn.classList.add('active');

  if (simState.running && !simState.paused) {
    if (simState.intervalId) clearInterval(simState.intervalId);
    startSimLoop();
  }
}

function simStop() {
  if (!simState.running) return;
  if (!confirm('确定要停止当前实验吗？')) return;

  simState.running = false;
  simState.paused = false;
  simState.currentMonth = 0;
  if (simState.intervalId) {
    clearInterval(simState.intervalId);
    simState.intervalId = null;
  }
  updateSimControlUI();
}

function startSimLoop() {
  if (simState.intervalId) clearInterval(simState.intervalId);

  var intervalMs, monthsPerTick;
  if (simState.speed <= 10) {
    intervalMs = Math.max(200, 1000 / simState.speed);
    monthsPerTick = 1;
  } else {
    intervalMs = 200;
    monthsPerTick = Math.ceil(simState.speed / 5);
  }

  simState.intervalId = setInterval(async function(){
    if (simState.paused || !simState.running) return;

    try {
      var resp = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          world: S.world,
          months: monthsPerTick,
          template_id: simState.templateId,
        }),
      });
      var data = await resp.json();

      if (data.current_month !== undefined) {
        simState.currentMonth = data.current_month;
      } else {
        simState.currentMonth += monthsPerTick;
      }

      if (simState.totalMonths > 0 && simState.currentMonth >= simState.totalMonths) {
        simState.currentMonth = simState.totalMonths;
        simState.running = false;
        simState.paused = false;
        clearInterval(simState.intervalId);
        simState.intervalId = null;
        showReportPanel();
      }

      updateSimControlUI();
      loadStats();
      loadAgents();
    } catch (e) {
      console.warn('simulate tick error:', e);
    }
  }, intervalMs);
}

function updateSimControlUI() {
  var playBtn = document.getElementById('simPlayBtn');
  var playIcon = document.getElementById('simPlayIcon');
  var progressBar = document.getElementById('simProgressBar');
  var progressText = document.getElementById('simProgressText');
  var expName = document.getElementById('simExpName');

  if (simState.running && !simState.paused) {
    playIcon.textContent = '⏸';
    playBtn.classList.add('playing');
  } else {
    playIcon.textContent = '▶️';
    playBtn.classList.remove('playing');
  }

  var pct = simState.totalMonths > 0
    ? (simState.currentMonth / simState.totalMonths * 100).toFixed(1)
    : 0;
  progressBar.style.width = pct + '%';
  progressText.textContent = '第 ' + simState.currentMonth + ' / ' + simState.totalMonths + ' 月';

  expName.textContent = simState.templateName || '--';
}

/* ============================================================ */
/* 组件3: 报告生成面板 JS */
/* ============================================================ */

function toggleReportPanel() {
  var panel = document.getElementById('reportPanel');
  var fab = document.getElementById('reportFab');
  var isVisible = panel.style.display !== 'none';

  if (isVisible) {
    panel.style.display = 'none';
    fab.classList.remove('active');
  } else {
    panel.style.display = '';
    fab.classList.add('active');
    updateReportInfo();
  }
}

function showReportPanel() {
  document.getElementById('reportPanel').style.display = '';
  document.getElementById('reportFab').classList.add('active');
  updateReportInfo();
}

function updateReportInfo() {
  document.getElementById('rptExpName').textContent =
    simState.templateName || '自由探索';
  document.getElementById('rptProgress').textContent =
    simState.currentMonth + ' / ' + (simState.totalMonths || '∞') + ' 月';
  document.getElementById('rptWorld').textContent = S.world;
}

async function generateReport() {
  var btn = document.getElementById('rptGenerateBtn');
  var progressWrap = document.getElementById('rptProgressBar');
  var progressInner = document.getElementById('rptProgressInner');

  var formatEl = document.querySelector('input[name="rptFormat"]:checked');
  var format = formatEl ? formatEl.value : 'excel';

  var contents = [];
  document.querySelectorAll('.report-check input:checked').forEach(function(cb){
    contents.push(cb.dataset.content);
  });

  if (contents.length === 0) {
    alert('请至少选择一项报告内容');
    return;
  }

  btn.classList.add('loading');
  btn.textContent = '⏳ 生成中...';
  progressWrap.style.display = '';
  progressInner.style.width = '10%';

  try {
    var progress = 10;
    var progressTimer = setInterval(function(){
      progress = Math.min(progress + Math.random() * 15, 90);
      progressInner.style.width = progress + '%';
    }, 300);

    var resp = await fetch('/api/report/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        world: S.world,
        format: format,
        contents: contents,
        template_id: simState.templateId,
        current_month: simState.currentMonth,
      }),
    });

    clearInterval(progressTimer);
    progressInner.style.width = '100%';

    if (!resp.ok) {
      throw new Error('生成失败: ' + resp.status);
    }

    var blob = await resp.blob();
    var ext = { excel: 'xlsx', csv: 'csv', markdown: 'md', json: 'json' }[format] || 'xlsx';
    var filename = 'report_' + S.world + '_' + new Date().toISOString().slice(0,10) + '.' + ext;

    var url = window.URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

    btn.textContent = '✅ 已下载';
    setTimeout(function(){
      btn.textContent = '📥 生成并下载';
      btn.classList.remove('loading');
      progressWrap.style.display = 'none';
      progressInner.style.width = '0%';
    }, 2000);

  } catch (e) {
    console.error('Report generation error:', e);

    try {
      await generateLocalReport(format, contents);
      btn.textContent = '✅ 已下载（本地生成）';
    } catch (localErr) {
      alert('报告生成失败: ' + e.message);
      btn.textContent = '📥 生成并下载';
    }

    setTimeout(function(){
      btn.textContent = '📥 生成并下载';
      btn.classList.remove('loading');
      progressWrap.style.display = 'none';
      progressInner.style.width = '0%';
    }, 2000);
  }
}

async function generateLocalReport(format, contents) {
  var statsResp = await fetch('/api/stats?world=' + S.world);
  var statsData = await statsResp.json();
  var agentsResp = await fetch('/api/agents?world=' + S.world);
  var agentsData = await agentsResp.json();
  var trendsResp = await fetch('/api/trends?world=' + S.world);
  var trendsData = await trendsResp.json();

  var reportContent = '';
  var timestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);

  if (format === 'markdown') {
    reportContent = generateMarkdownReport(statsData, agentsData, trendsData, contents, timestamp);
  } else if (format === 'csv') {
    reportContent = generateCSVReport(statsData, agentsData, trendsData, contents);
  } else if (format === 'json') {
    reportContent = JSON.stringify({
      meta: { world: S.world, template: simState.templateId, generated: timestamp, month: simState.currentMonth },
      stats: contents.includes('summary') ? statsData : undefined,
      agents: contents.includes('agents') ? agentsData.agents : undefined,
      trends: contents.includes('kpi') ? trendsData : undefined,
      events: contents.includes('events') ? S.events : undefined,
    }, null, 2);
  } else {
    reportContent = generateCSVReport(statsData, agentsData, trendsData, contents);
    format = 'csv';
  }

  var ext = { markdown: 'md', csv: 'csv', json: 'json', excel: 'csv' }[format] || 'txt';
  var blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' });
  var filename = 'report_' + S.world + '_' + new Date().toISOString().slice(0,10) + '.' + ext;
  var url = window.URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  window.URL.revokeObjectURL(url);
}

function generateMarkdownReport(stats, agents, trends, contents, timestamp) {
  var md = '# 🧪 实验报告\\n\\n';
  md += '> 生成时间：' + timestamp + '\\n';
  md += '> 世界：' + S.world + '\\n';
  md += '> 模板：' + (simState.templateId || '自由探索') + ' - ' + (simState.templateName || '--') + '\\n';
  md += '> 进度：第 ' + simState.currentMonth + ' / ' + (simState.totalMonths || '∞') + ' 月\\n\\n';

  if (contents.includes('summary')) {
    md += '## 📊 实验摘要\\n\\n';
    md += '| 指标 | 数值 |\\n|------|------|\\n';
    md += '| 总人口 | ' + ((stats.population || 0).toLocaleString()) + ' |\\n';
    md += '| 就业率 | ' + (stats.employment_rate || '--') + '% |\\n';
    md += '| 平均月收入 | $' + Math.round(stats.avg_income || 0).toLocaleString() + ' |\\n';
    md += '| 平均满意度 | ' + (stats.avg_satisfaction || '--') + ' |\\n\\n';

    if (stats.occupation) {
      md += '### 职业分布\\n\\n';
      md += '| 职业 | 人数 |\\n|------|------|\\n';
      for (var occ in stats.occupation) {
        md += '| ' + occ + ' | ' + stats.occupation[occ] + ' |\\n';
      }
      md += '\\n';
    }
  }

  if (contents.includes('kpi') && trends.days) {
    md += '## 📈 KPI 趋势\\n\\n';
    md += '| 时间 | 人口 | 收入 | 就业率(%) | 满意度 |\\n';
    md += '|------|------|------|-----------|--------|\\n';
    for (var i = 0; i < trends.days.length; i++) {
      md += '| ' + trends.days[i] + ' | ' + (trends.population?trends.population[i]:'--') + ' | ' + (trends.avg_income?trends.avg_income[i]:'--') + ' | ' + (trends.employment_rate?trends.employment_rate[i]:'--') + ' | ' + (trends.satisfaction?trends.satisfaction[i]:'--') + ' |\\n';
    }
    md += '\\n';
  }

  if (contents.includes('agents') && agents.agents) {
    md += '## 👥 Agent 样本数据 (前 20)\\n\\n';
    md += '| ID | 姓名 | 年龄 | 职业 | 月收入 | 满意度 | 区域 |\\n';
    md += '|----|------|------|------|--------|--------|------|\\n';
    agents.agents.slice(0, 20).forEach(function(a){
      md += '| ' + a.id + ' | ' + a.name + ' | ' + a.age + ' | ' + a.occupation + ' | $' + (a.income||0).toLocaleString() + ' | ' + a.satisfaction + ' | ' + a.region + ' |\\n';
    });
    md += '\\n... 共 ' + agents.total + ' 个 Agent\\n\\n';
  }

  if (contents.includes('events') && S.events.length > 0) {
    md += '## 📰 最近事件\\n\\n';
    S.events.slice(0, 30).forEach(function(ev){
      md += '- ' + (ev.emoji || '📌') + ' **' + (ev.time || '') + '** ' + (ev.text || '') + '\\n';
    });
    md += '\\n';
  }

  md += '---\\n\\n_报告由御龙军虚拟 Agent 世界系统自动生成_\\n';
  return md;
}

function generateCSVReport(stats, agents, trends, contents) {
  var csv = '';

  if (contents.includes('agents') && agents.agents) {
    csv += 'ID,Name,Age,Gender,Occupation,Region,Income,Skill,Education,Satisfaction\\n';
    agents.agents.forEach(function(a){
      csv += a.id + ',"' + a.name + '",' + a.age + ',' + a.gender + ',' + a.occupation + ',' + a.region + ',' + (a.income||0) + ',' + (a.skill_level||0) + ',"' + (a.education||'') + '",' + (a.satisfaction||0) + '\\n';
    });
  } else if (contents.includes('kpi') && trends.days) {
    csv += 'Time,Population,AvgIncome,EmploymentRate,Satisfaction\\n';
    for (var i = 0; i < trends.days.length; i++) {
      csv += (trends.days[i]||'') + ',' + (trends.population?trends.population[i]:'') + ',' + (trends.avg_income?trends.avg_income[i]:'') + ',' + (trends.employment_rate?trends.employment_rate[i]:'') + ',' + (trends.satisfaction?trends.satisfaction[i]:'') + '\\n';
    }
  }

  return csv;
}

// 修改 DOMContentLoaded 初始化
(function(){
  var origInit = null;
  document.addEventListener('DOMContentLoaded', function(){
    initExperimentPicker();
  });
})();

</script>

<!-- ============================================================ -->
<!-- 组件3: 报告生成面板 (悬浮) -->
<!-- ============================================================ -->
<div class="report-fab" id="reportFab" onclick="toggleReportPanel()" title="生成报告">
  📊
</div>

<div class="report-panel" id="reportPanel" style="display:none;">
  <div class="report-panel-header">
    <span class="report-panel-title">📊 报告生成</span>
    <button class="report-close-btn" onclick="toggleReportPanel()">✕</button>
  </div>

  <div class="report-panel-body">
    <div class="report-info">
      <div class="report-info-row">
        <span class="report-info-label">实验</span>
        <span class="report-info-val" id="rptExpName">--</span>
      </div>
      <div class="report-info-row">
        <span class="report-info-label">进度</span>
        <span class="report-info-val" id="rptProgress">-- / -- 月</span>
      </div>
      <div class="report-info-row">
        <span class="report-info-label">世界</span>
        <span class="report-info-val" id="rptWorld">--</span>
      </div>
    </div>

    <div class="report-section-title">📄 报告格式</div>
    <div class="report-format-grid">
      <label class="report-format-option">
        <input type="radio" name="rptFormat" value="excel" checked>
        <div class="report-format-card">
          <span class="report-format-icon">📗</span>
          <span class="report-format-name">Excel</span>
          <span class="report-format-ext">.xlsx</span>
        </div>
      </label>
      <label class="report-format-option">
        <input type="radio" name="rptFormat" value="csv">
        <div class="report-format-card">
          <span class="report-format-icon">📄</span>
          <span class="report-format-name">CSV</span>
          <span class="report-format-ext">.csv</span>
        </div>
      </label>
      <label class="report-format-option">
        <input type="radio" name="rptFormat" value="markdown">
        <div class="report-format-card">
          <span class="report-format-icon">📝</span>
          <span class="report-format-name">Markdown</span>
          <span class="report-format-ext">.md</span>
        </div>
      </label>
      <label class="report-format-option">
        <input type="radio" name="rptFormat" value="json">
        <div class="report-format-card">
          <span class="report-format-icon">🔧</span>
          <span class="report-format-name">JSON</span>
          <span class="report-format-ext">.json</span>
        </div>
      </label>
    </div>

    <div class="report-section-title">📋 报告内容</div>
    <div class="report-content-options">
      <label class="report-check">
        <input type="checkbox" checked data-content="summary"> 📊 实验摘要
      </label>
      <label class="report-check">
        <input type="checkbox" checked data-content="kpi"> 📈 KPI 趋势数据
      </label>
      <label class="report-check">
        <input type="checkbox" checked data-content="agents"> 👥 Agent 详细数据
      </label>
      <label class="report-check">
        <input type="checkbox" data-content="events"> 📰 事件日志
      </label>
      <label class="report-check">
        <input type="checkbox" data-content="distribution"> 🌹 分布统计
      </label>
      <label class="report-check">
        <input type="checkbox" data-content="comparison"> 📉 对比分析
      </label>
    </div>
  </div>

  <div class="report-panel-footer">
    <button class="report-generate-btn" id="rptGenerateBtn" onclick="generateReport()">
      📥 生成并下载
    </button>
  </div>

  <div class="report-progress" id="rptProgressBar" style="display:none;">
    <div class="report-progress-inner" id="rptProgressInner" style="width:0%"></div>
  </div>
</div>

</body>
</html>
'''


def init_engine(agent_count=10000):
    """初始化引擎 & 模板库
    
    Args:
        agent_count: 初始 Agent 数量，默认 10000
    """
    global engine, template_library

    if not ENGINE_AVAILABLE:
        print("[WARN]  JSON  fallback ")
        return False

    print(f"\n    ...")
    engine = DeepIntegrationEngine()

    print(f"   ...")
    template_library = ExperimentTemplateLibrary()

    print(f"    {agent_count:,}  Agent...")
    # 批量创建（engine.create_agent 内部会逐个初始化子系统）
    batch_size = 1000
    for i in range(0, agent_count, batch_size):
        batch = min(batch_size, agent_count - i)
        for _ in range(batch):
            engine.create_agent()
        print(f"       {min(i + batch, agent_count):,} / {agent_count:,}")

    alive = sum(1 for a in engine.agents.values() if a.is_alive)
    print(f"   : {len(engine.agents):,} Agent ({alive:,} )")
    print(f"   : {len(template_library.templates)}")
    return True


# ============================================================
# 启动
# ============================================================
if __name__ == '__main__':
    host = CONFIG['bind_host']
    print("=" * 60)
    print("   Agent  v4.0 ")
    print("   | P0  + ")
    print("=" * 60)

    # ── 初始化引擎 ──
    engine_ok = init_engine(agent_count=10000)

    print(f"\n  http://{host}:5001")
    if host == '127.0.0.1':
        print(f"   ")
        print(f"    BIND_HOST=0.0.0.0")

    if engine_ok:
        print(f"\n   ")
        print(f"  ")
    else:
        print(f"\n   JSON  fallback ")
        print(f"  worlds/  JSON ")

    print(f"\n  API :")
    print(f"             GET  /api/events")
    print(f"             GET  /api/trends")
    print(f"            GET  /api/regions")
    print(f"     Agent     GET  /api/agents/search")
    print(f"           GET  /api/engine/status")
    if engine_ok:
        print(f"           POST /api/simulate")
        print(f"           GET  /api/experiments/templates")
        print(f"           POST /api/experiments/run")
        print(f"           POST /api/reports/generate")

    print(f"\n   Ctrl+C \n")

    app.run(host=host, port=5001, debug=False)
