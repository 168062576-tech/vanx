"""
御龙军虚拟 Agent 世界 - 可视化系统 v3.0
版本：v3.0
创建时间：2026-03-16
功能：Flask 后端 + HTML5 实时可视化，支持主世界/实验世界
"""

from flask import Flask, render_template_string, jsonify
import json
import os
import threading
import time
from datetime import datetime

app = Flask(__name__)

# 配置
import os
# 动态获取工作区路径
WORKSPACE = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    'base_path': WORKSPACE,
    'worlds_path': os.path.join(WORKSPACE, 'worlds'),
    'data_path': os.path.join(WORKSPACE, 'data'),
    'max_display_agents': 2000,  # 最多显示 2000 个 Agent (浏览器性能限制)
    'refresh_interval_sec': 5   # 刷新间隔 5 秒
}

# 全局状态
global_state = {
    'current_world': 'world_alpha',
    'worlds': {},
    'last_update': None,
    'agents_cache': [],
    'stats_cache': {}
}


def load_latest_state(world_name: str = 'world_alpha'):
    """加载最新的世界状态"""
    worlds_path = CONFIG['worlds_path']
    
    # 查找最新的保存文件
    pattern = f"{world_name}_state_*.json"
    import glob
    files = glob.glob(os.path.join(worlds_path, pattern))
    
    if not files:
        return None
    
    latest_file = max(files, key=os.path.getmtime)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[ERR] 加载状态失败：{e}")
        return None


def get_agents_display_data(state: dict) -> list:
    """处理 Agent 数据用于显示"""
    if not state:
        return []
    
    # 优先使用 agents_sample，如果没有则用 agents
    agents = state.get('agents_sample', state.get('agents', []))
    
    # 限制显示数量（性能优化）
    if len(agents) > CONFIG['max_display_agents']:
        import random
        agents = random.sample(agents, CONFIG['max_display_agents'])
    
    display_agents = []
    for agent in agents:
        # 生成可视化位置（基于 ID 哈希，确保固定）
        agent_id = agent.get('id', 'unknown')
        hash_val = hash(agent_id) % 10000
        
        display_agents.append({
            'id': agent_id,
            'name': agent.get('name', '未知'),
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
            'x': hash_val % 100,  # 0-99
            'y': (hash_val // 100) % 100,  # 0-99
            'activity': '工作中' if agent.get('occupation') != '其他' else '休息',
            'region': get_region_for_agent(agent)
        })
    
    return display_agents


def get_region_for_agent(agent: dict) -> str:
    """根据职业分配区域"""
    occupation = agent.get('occupation', '其他')
    
    region_map = {
        '农业': '郊区',
        '制造业': '工业区',
        '服务业': '商业区',
        '信息技术': '商业区',
        '医疗': '医疗区',
        '教育': '教育区',
        '金融': '商业区',
        '政府': '商业区',
        '其他': '住宅区'
    }
    
    return region_map.get(occupation, '住宅区')


def get_occupation_colors():
    """职业颜色映射"""
    return {
        '农业': '#8B4513',
        '制造业': '#708090',
        '服务业': '#FF69B4',
        '信息技术': '#4169E1',
        '医疗': '#DC143C',
        '教育': '#228B22',
        '金融': '#DAA520',
        '政府': '#9932CC',
        '其他': '#808080'
    }


def get_region_colors():
    """区域颜色映射"""
    return {
        '住宅区': '#FF6B6B',
        '商业区': '#4ECDC4',
        '工业区': '#FFE66D',
        '教育区': '#95E1D3',
        '医疗区': '#F38181',
        '休闲区': '#AA96DA',
        '郊区': '#FCBAD3'
    }


@app.route('/')
def index():
    """主页面"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/worlds')
def api_worlds():
    """获取世界列表"""
    import glob
    worlds_path = CONFIG['worlds_path']
    
    files = glob.glob(os.path.join(worlds_path, '*_state_*.json'))
    
    worlds = {}
    for file in files:
        filename = os.path.basename(file)
        # 解析世界名
        parts = filename.replace('.json', '').split('_state_')
        if len(parts) >= 2:
            world_name = '_state_'.join(parts[:-1])  # 处理 world_alpha_global 这种多段命名
            timestamp = parts[-1]
            
            if world_name not in worlds:
                worlds[world_name] = []
            
            worlds[world_name].append({
                'file': filename,
                'timestamp': timestamp,
                'size_mb': round(os.path.getsize(file) / (1024 * 1024), 2),
                'modified': datetime.fromtimestamp(os.path.getmtime(file)).isoformat()
            })
    
    return jsonify({
        'worlds': list(worlds.keys()),
        'details': worlds,
        'current': global_state['current_world']
    })


@app.route('/api/agents')
def api_agents():
    """获取 Agent 列表"""
    world = request.args.get('world', global_state['current_world'])
    
    state = load_latest_state(world)
    if not state:
        return jsonify({'agents': [], 'error': 'No state found'})
    
    agents = get_agents_display_data(state)
    
    return jsonify({
        'agents': agents,
        'total': len(agents),
        'world': world,
        'time': state.get('time', {}),
        'last_update': datetime.now().isoformat()
    })


@app.route('/api/stats')
def api_stats():
    """获取统计数据"""
    world = request.args.get('world', global_state['current_world'])
    
    state = load_latest_state(world)
    if not state:
        return jsonify({'error': 'No state found'})
    
    agents = state.get('agents_sample', [])
    
    # 职业统计
    occ_stats = {}
    for agent in agents:
        job = agent.get('occupation', '其他')
        occ_stats[job] = occ_stats.get(job, 0) + 1
    
    # 洲际统计
    continent_stats = {}
    for agent in agents:
        continent = agent.get('continent', '未知')
        continent_stats[continent] = continent_stats.get(continent, 0) + 1
    
    # 区域统计
    region_stats = {}
    for agent in agents:
        region = get_region_for_agent(agent)
        region_stats[region] = region_stats.get(region, 0) + 1
    
    # 就业率
    employed = sum(1 for a in agents if a.get('occupation') != '其他')
    employment_rate = employed / len(agents) * 100 if agents else 0
    
    return jsonify({
        'population': len(agents),
        'occupation': occ_stats,
        'continent': continent_stats,
        'region': region_stats,
        'employment_rate': round(employment_rate, 1),
        'avg_satisfaction': round(sum(a.get('satisfaction', 0) for a in agents) / len(agents), 2) if agents else 0,
        'avg_income': round(sum(a.get('income_monthly', 0) for a in agents) / len(agents), 2) if agents else 0,
        'time': state.get('time', {}),
        'statistics': state.get('statistics', {})
    })


@app.route('/api/agent/<agent_id>')
def api_agent_detail(agent_id):
    """获取单个 Agent 详情"""
    world = request.args.get('world', global_state['current_world'])
    
    state = load_latest_state(world)
    if not state:
        return jsonify({'error': 'No state found'})
    
    agents = state.get('agents_sample', [])
    
    for agent in agents:
        if agent.get('id') == agent_id:
            return jsonify({
                'agent': agent,
                'region': get_region_for_agent(agent)
            })
    
    return jsonify({'error': 'Agent not found'}), 404


@app.route('/api/evolve', methods=['POST'])
def api_evolve():
    """启动演化（实验世界）"""
    import requests
    
    world_name = request.json.get('world', 'world_beta_experiment')
    time_scale = request.json.get('time_scale', 1.0)
    duration = request.json.get('duration', 30)
    
    # TODO: 调用演化引擎
    # 这里需要启动后台演化线程
    
    return jsonify({
        'status': 'started',
        'world': world_name,
        'time_scale': time_scale,
        'duration': duration
    })


# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>御龙军虚拟 Agent 世界 v3.0 - 实时可视化</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 20px;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .status-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            margin-left: 10px;
        }
        .status-running { background: #4CAF50; color: white; }
        .status-stopped { background: #999; color: white; }
        .container {
            display: grid;
            grid-template-columns: 300px 1fr 300px;
            gap: 20px;
            max-width: 1800px;
            margin: 0 auto;
        }
        .panel {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .panel h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .stat-label { color: #666; }
        .stat-value { font-weight: bold; color: #333; }
        #world-map {
            width: 100%;
            height: 700px;
            background: #f8f9fa;
            border-radius: 10px;
            position: relative;
            overflow: hidden;
        }
        .agent-dot {
            position: absolute;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .agent-dot:hover {
            transform: scale(2);
            z-index: 100;
        }
        .agent-detail {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-top: 15px;
        }
        .agent-detail h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            font-size: 0.9em;
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            margin-top: 10px;
            width: 100%;
        }
        .refresh-btn:hover { background: #5568d3; }
        .world-selector {
            margin-bottom: 15px;
        }
        .world-selector select {
            width: 100%;
            padding: 8px;
            border-radius: 5px;
            border: 1px solid #ddd;
            font-size: 1em;
        }
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin: 5px 0;
            font-size: 0.85em;
        }
        .legend-color {
            width: 15px;
            height: 15px;
            border-radius: 3px;
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌍 御龙军虚拟 Agent 世界 v4.0</h1>
        <p>双世界模式 | 真实时间 + 加速实验 | 职业自主演化</p>
        <div id="world-status"></div>
    </div>
    
    <div class="container">
        <!-- 左侧面板：统计信息 -->
        <div class="panel">
            <h2>📊 实时统计</h2>
            
            <div class="world-selector">
                <label>选择世界：</label>
                <select id="world-select" onchange="loadData()">
                    <option value="world_alpha">主世界 Alpha (真实时间)</option>
                    <option value="world_alpha_global">主世界 Alpha Global</option>
                    <option value="world_alpha_v3">主世界 V3</option>
                </select>
            </div>
            
            <div id="stats-content">
                <div class="loading">加载中...</div>
            </div>
            
            <h3 style="margin-top: 20px; color: #667eea;">区域图例</h3>
            <div id="region-legend"></div>
            
            <h3 style="margin-top: 20px; color: #667eea;">职业图例</h3>
            <div id="occupation-legend"></div>
            
            <button class="refresh-btn" onclick="loadData()">🔄 刷新</button>
        </div>
        
        <!-- 中间面板：世界地图 -->
        <div class="panel">
            <h2>🗺️ 世界地图</h2>
            <div id="world-map">
                <div class="loading">加载地图...</div>
            </div>
        </div>
        
        <!-- 右侧面板：Agent 详情 -->
        <div class="panel">
            <h2>👤 Agent 详情</h2>
            <div id="agent-detail">
                <p style="color: #999; text-align: center; padding: 50px;">
                    点击地图上的点查看详情
                </p>
            </div>
            
            <h3 style="margin-top: 20px; color: #667eea;">职业分布</h3>
            <canvas id="occupation-chart"></canvas>
        </div>
    </div>
    
    <script>
        let occupationChart = null;
        
        async function loadData() {
            const world = document.getElementById('world-select').value;
            
            // 加载统计数据
            const statsRes = await fetch(`/api/stats?world=${world}`);
            const stats = await statsRes.json();
            
            // 渲染统计
            document.getElementById('stats-content').innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">总人口</span>
                    <span class="stat-value">${stats.population.toLocaleString()}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">就业率</span>
                    <span class="stat-value">${stats.employment_rate}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">平均满意度</span>
                    <span class="stat-value">${stats.avg_satisfaction.toFixed(2)}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">平均月收入</span>
                    <span class="stat-value">$${stats.avg_income.toLocaleString()}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">世界时间</span>
                    <span class="stat-value">${stats.time.year || 2026}年${stats.time.day || 1}天</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">总出生</span>
                    <span class="stat-value">${(stats.statistics.total_births || 0).toLocaleString()}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">总死亡</span>
                    <span class="stat-value">${(stats.statistics.total_deaths || 0).toLocaleString()}</span>
                </div>
            `;
            
            // 渲染图例
            renderLegends(stats);
            
            // 渲染职业分布图
            renderOccupationChart(stats.occupation);
            
            // 加载 Agent
            const agentsRes = await fetch(`/api/agents?world=${world}`);
            const agentsData = await agentsRes.json();
            
            renderMap(agentsData.agents);
        }
        
        function renderLegends(stats) {
            // 区域图例
            const regionColors = {
                '住宅区': '#FF6B6B', '商业区': '#4ECDC4', '工业区': '#FFE66D',
                '教育区': '#95E1D3', '医疗区': '#F38181', '休闲区': '#AA96DA', '郊区': '#FCBAD3'
            };
            let regionHtml = '';
            for (const [region, count] of Object.entries(stats.region || {})) {
                regionHtml += `
                    <div class="legend-item">
                        <div class="legend-color" style="background: ${regionColors[region] || '#888'}"></div>
                        <span>${region}: ${count}人</span>
                    </div>
                `;
            }
            document.getElementById('region-legend').innerHTML = regionHtml;
            
            // 职业图例
            const occColors = {
                '农业': '#8B4513', '制造业': '#708090', '服务业': '#FF69B4',
                '信息技术': '#4169E1', '医疗': '#DC143C', '教育': '#228B22',
                '金融': '#DAA520', '政府': '#9932CC', '其他': '#808080'
            };
            let occHtml = '';
            for (const [occ, count] of Object.entries(stats.occupation || {})) {
                occHtml += `
                    <div class="legend-item">
                        <div class="legend-color" style="background: ${occColors[occ] || '#888'}"></div>
                        <span>${occ}: ${count}人</span>
                    </div>
                `;
            }
            document.getElementById('occupation-legend').innerHTML = occHtml;
        }
        
        function renderOccupationChart(occupation) {
            const ctx = document.getElementById('occupation-chart').getContext('2d');
            
            if (occupationChart) {
                occupationChart.destroy();
            }
            
            const colors = {
                '农业': '#8B4513', '制造业': '#708090', '服务业': '#FF69B4',
                '信息技术': '#4169E1', '医疗': '#DC143C', '教育': '#228B22',
                '金融': '#DAA520', '政府': '#9932CC', '其他': '#808080'
            };
            
            occupationChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: Object.keys(occupation),
                    datasets: [{
                        data: Object.values(occupation),
                        backgroundColor: Object.keys(occupation).map(k => colors[k] || '#888')
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }
        
        function renderMap(agents) {
            const mapDiv = document.getElementById('world-map');
            mapDiv.innerHTML = '';
            
            const occColors = {
                '农业': '#8B4513', '制造业': '#708090', '服务业': '#FF69B4',
                '信息技术': '#4169E1', '医疗': '#DC143C', '教育': '#228B22',
                '金融': '#DAA520', '政府': '#9932CC', '其他': '#808080'
            };
            
            agents.forEach(agent => {
                const dot = document.createElement('div');
                dot.className = 'agent-dot';
                dot.style.left = agent.x + '%';
                dot.style.top = agent.y + '%';
                dot.style.background = occColors[agent.occupation] || '#888';
                dot.title = `${agent.name} - ${agent.occupation}`;
                dot.onclick = () => showAgentDetail(agent);
                mapDiv.appendChild(dot);
            });
        }
        
        async function showAgentDetail(agent) {
            const world = document.getElementById('world-select').value;
            const res = await fetch(`/api/agent/${agent.id}?world=${world}`);
            const data = await res.json();
            
            if (data.error) {
                document.getElementById('agent-detail').innerHTML = `<p style="color: red;">${data.error}</p>`;
                return;
            }
            
            const a = data.agent;
            document.getElementById('agent-detail').innerHTML = `
                <div class="agent-detail">
                    <h3>${a.name}</h3>
                    <div class="detail-row"><span>年龄:</span><span>${a.age}岁</span></div>
                    <div class="detail-row"><span>性别:</span><span>${a.gender}</span></div>
                    <div class="detail-row"><span>国籍:</span><span>${a.nationality}</span></div>
                    <div class="detail-row"><span>职业:</span><span>${a.occupation}</span></div>
                    <div class="detail-row"><span>月收入:</span><span>$${(a.income_monthly || 0).toLocaleString()}</span></div>
                    <div class="detail-row"><span>技能等级:</span><span>${a.skill_level}</span></div>
                    <div class="detail-row"><span>教育:</span><span>${a.education}</span></div>
                    <div class="detail-row"><span>满意度:</span><span>${(a.satisfaction || 0).toFixed(2)}</span></div>
                    <div class="detail-row"><span>状态:</span><span>${a.status}</span></div>
                    <div class="detail-row"><span>区域:</span><span>${data.region}</span></div>
                    <div class="detail-row"><span>位置:</span><span>(${a.x}, ${a.y})</span></div>
                </div>
            `;
        }
        
        // 初始加载
        loadData();
        
        // 自动刷新（每 5 秒）
        setInterval(loadData, 5000);
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    print("=== 虚拟 Agent 世界可视化系统 v3.0 ===")
    print(f"\n启动服务器...")
    print(f"访问地址：http://localhost:5001")
    print(f"局域网访问：http://<你的 IP>:5001")
    print(f"\n功能:")
    print(f"  - 实时查看 Agent 分布")
    print(f"  - 职业统计图表")
    print(f"  - Agent 详情查看")
    print(f"  - 自动刷新（5 秒）")
    print(f"\n按 Ctrl+C 停止服务\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
