"""
御龙军虚拟 Agent 世界 - Web 报告生成页面
版本：v1.0
创建时间：2026-03-17
功能：在 Web 界面中添加报告生成入口
"""

# 添加到 visualizer_v3.py 的路由

REPORT_PAGE = '''
@app.route('/reports')
def reports_page():
    """报告生成页面"""
    return render_template_string(REPORT_TEMPLATE)


@app.route('/api/generate_report', methods=['POST'])
def api_generate_report():
    """生成报告 API"""
    import json
    
    data = request.json
    report_type = data.get('type', 'excel')  # excel/html/json
    world_name = data.get('world', 'world_alpha')
    
    # 加载世界状态
    state = load_latest_state(world_name)
    if not state:
        return jsonify({'error': 'World state not found', 'success': False})
    
    # 生成统计数据
    agents = state.get('agents_sample', state.get('agents', []))
    
    # 职业统计
    occupation_stats = {}
    for agent in agents:
        job = agent.get('occupation', '其他')
        occupation_stats[job] = occupation_stats.get(job, 0) + 1
    
    # 收入统计
    incomes = [a.get('income_monthly', 0) for a in agents if a.get('income_monthly', 0) > 0]
    avg_income = sum(incomes) / len(incomes) if incomes else 0
    
    # 满意度统计
    satisfactions = [a.get('satisfaction', 0) for a in agents]
    avg_satisfaction = sum(satisfactions) / len(satisfactions) if satisfactions else 0
    
    # 教育统计
    education_stats = {}
    for agent in agents:
        edu = agent.get('education', '未知')
        education_stats[edu] = education_stats.get(edu, 0) + 1
    
    # 生成报告数据
    report_data = {
        'world': world_name,
        'timestamp': datetime.now().isoformat(),
        'population': len(agents),
        'occupation_distribution': occupation_stats,
        'average_income': round(avg_income, 2),
        'average_satisfaction': round(avg_satisfaction, 2),
        'education_distribution': education_stats,
        'time': state.get('time', {}),
        'statistics': state.get('statistics', {})
    }
    
    if report_type == 'json':
        # 保存为 JSON 文件
        filepath = os.path.join(CONFIG['data_path'], f'report_{world_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'type': 'json',
            'file': filepath,
            'data': report_data
        })
    
    elif report_type == 'html':
        # 生成 HTML 报告
        html_content = generate_html_report(report_data)
        filepath = os.path.join(CONFIG['data_path'], f'report_{world_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return jsonify({
            'success': True,
            'type': 'html',
            'file': filepath
        })
    
    return jsonify({'error': 'Unsupported report type', 'success': False})


def generate_html_report(data: Dict) -> str:
    """生成 HTML 报告"""
    html = f"""
<!DOCTYPE html>
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
        
        <h2>📈 核心指标</h2>
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value">{data['population']:,}</div>
                <div class="stat-label">总人口</div>
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
                <div class="stat-value">{len(data['occupation_distribution'])}</div>
                <div class="stat-label">职业类型</div>
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
        
        <h2>📋 详细数据</h2>
        <table>
            <tr><th>职业</th><th>人数</th><th>占比</th></tr>
"""
    
    total = data['population']
    for job, count in sorted(data['occupation_distribution'].items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100 if total > 0 else 0
        html += f"<tr><td>{job}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>"
    
    html += """
        </table>
        
        <div class="footer">
            <p>御龙军虚拟 Agent 世界 · 报告生成系统</p>
        </div>
    </div>
    
    <script>
        // 职业分布饼图
        new Chart(document.getElementById('occupationChart'), {
            type: 'pie',
            data: {
                labels: """ + str(list(data['occupation_distribution'].keys())) + """,
                datasets: [{
                    data: """ + str(list(data['occupation_distribution'].values())) + """,
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF']
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
        
        // 教育分布柱状图
        new Chart(document.getElementById('educationChart'), {
            type: 'bar',
            data: {
                labels: """ + str(list(data['education_distribution'].keys())) + """,
                datasets: [{
                    label: '人数',
                    data: """ + str(list(data['education_distribution'].values())) + """,
                    backgroundColor: '#667eea'
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    </script>
</body>
</html>
"""
    return html


# HTML 报告页面模板
REPORT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>报告生成 - 御龙军虚拟 Agent 世界</title>
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
            margin-bottom: 30px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 { color: #667eea; margin-bottom: 20px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; color: #333; }
        select, button { 
            width: 100%; 
            padding: 12px; 
            border-radius: 8px; 
            border: 1px solid #ddd;
            font-size: 1em;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
            margin-top: 10px;
        }
        button:hover { opacity: 0.9; }
        .result { 
            margin-top: 20px; 
            padding: 20px; 
            border-radius: 8px;
            display: none;
        }
        .result.success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .result.error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .back-link { 
            display: inline-block; 
            margin-top: 20px; 
            color: #667eea; 
            text-decoration: none; 
        }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 报告生成系统</h1>
        <p>生成虚拟 Agent 世界的可视化分析报告</p>
    </div>
    
    <div class="container">
        <h2>选择报告参数</h2>
        
        <div class="form-group">
            <label for="worldSelect">选择世界：</label>
            <select id="worldSelect">
                <option value="world_alpha">主世界 Alpha</option>
                <option value="world_beta">实验世界 Beta</option>
                <option value="world_gamma">快速世界 Gamma</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="reportType">报告类型：</label>
            <select id="reportType">
                <option value="html">HTML 可视化报告（推荐）</option>
                <option value="json">JSON 数据报告</option>
            </select>
        </div>
        
        <button onclick="generateReport()">🚀 生成报告</button>
        
        <div id="result" class="result"></div>
        
        <a href="/" class="back-link">← 返回主界面</a>
    </div>
    
    <script>
        // 加载世界列表
        fetch('/api/worlds')
            .then(r => r.json())
            .then(data => {
                const select = document.getElementById('worldSelect');
                select.innerHTML = '';
                data.worlds.forEach(w => {
                    const opt = document.createElement('option');
                    opt.value = w;
                    opt.textContent = w;
                    select.appendChild(opt);
                });
            });
        
        async function generateReport() {
            const world = document.getElementById('worldSelect').value;
            const type = document.getElementById('reportType').value;
            const resultDiv = document.getElementById('result');
            
            resultDiv.style.display = 'block';
            resultDiv.className = 'result';
            resultDiv.textContent = '正在生成报告...';
            
            try {
                const response = await fetch('/api/generate_report', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ world, type })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.className = 'result success';
                    resultDiv.innerHTML = `
                        ✅ 报告生成成功！<br>
                        文件：${data.file}<br>
                        <a href="${data.file}" target="_blank" style="color: #155724; font-weight: bold;">📄 查看报告</a>
                    `;
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.textContent = '❌ 生成失败：' + (data.error || '未知错误');
                }
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.textContent = '❌ 生成失败：' + error.message;
            }
        }
    </script>
</body>
</html>
'''
