## 情报司报告

**项目：** VanX 开源版 (Virtual World Open Source)  
**路径：** D:\YulongLegion\virtual-world-open-source  
**收集时间：** 2026-03-28 11:35  

---

### 文件统计

| 类型 | 数量 | 代码行数 |
|------|------|----------|
| **Python 文件** | 43 个 | 19,093 行 |
| **HTML 文件** | 5 个 | 4,704 行 |
| **JavaScript 文件** | 2 个 | 1,655 行 |
| **CSS 文件** | 1 个 | 2,005 行 |
| **Markdown 文档** | 7 个 | 1,433 行 |
| **前端文件总计** | 8 个 | 8,364 行 |
| **文档文件总计** | 7 个 | 1,433 行 |
| **总代码行数** | - | **27,490 行** |

**大型文件 Top 5:**
1. `visualizer_v4.py` - 2,871 行
2. `api_server.py` - 2,420 行
3. `deep_integration_engine.py` - 1,214 行
4. `deep_micro_systems.py` - 815 行
5. `ability_system.py` - 730 行

---

### 核心模块

**核心系统文件 (43 个 Python 文件):**

| 模块 | 行数 | 功能 |
|------|------|------|
| `api_server.py` | 2,420 | Flask API 服务器，提供 RESTful 接口 |
| `deep_integration_engine.py` | 1,214 | 深度集成引擎，核心系统协调 |
| `deep_micro_systems.py` | 815 | 微观系统（风险偏好、宗教等） |
| `ability_system.py` | 730 | 能力系统 |
| `corporate_system.py` | 564 | 企业系统 |
| `economic_system.py` | 519 | 经济系统 |
| `healthcare_system.py` | 487 | 医疗系统 |
| `social_network_system.py` | 475 | 社交网络系统 |
| `housing_system.py` | 464 | 住房系统 |
| `government_system.py` | 407 | 政府系统 |
| `marriage_family_system.py` | 372 | 婚姻家庭系统 |
| `decision_engine.py` | 318 | 决策引擎（规则/LLM） |
| `occupation_system.py` | 308 | 职业系统 |
| `emergence_detector.py` | 227 | 涌现检测器 |
| `narrative_engine.py` | 185 | 叙事引擎 |
| `event_manager.py` | 133 | 事件管理器 |
| `utils.py` | 150 | 工具函数 |
| `config.py` | 44 | 全局配置 |
| `run.py` | 46 | 主入口 |
| `web_server.py` | 121 | Web 服务器 |
| `visualizer_v4.py` | 2,871 | 可视化引擎 v4 |
| `visualizer_v3.py` | 648 | 可视化引擎 v3 |
| `experiment_runner.py` | 375 | 实验运行器 |
| `experiment_templates_v2.py` | 156 | 实验模板 |
| `experiment_report_generator.py` | 708 | 实验报告生成器 |
| `integration_modules.py` | 502 | 集成模块 |
| `core_systems_integrator.py` | 345 | 核心系统集成器 |
| `custom_scenario.py` | 194 | 自定义场景 |
| `scenario_selector.py` | 79 | 场景选择器 |
| `scenario_applier.py` | 91 | 场景应用器 |
| `scenario_examples.py` | 97 | 场景示例 |
| `data_exporter.py` | 160 | 数据导出器 |
| `report_web_page.py` | 347 | 报告网页生成 |
| `backup.py` | 77 | 备份工具 |
| `name_data_124.py` | 557 | 名称数据 |
| `check_db_extended.py` | 23 | 数据库检查 |
| `debug_occupation.py` | 22 | 职业调试 |
| `debug_test.py` | 8 | 调试测试 |
| `test_api_resp.py` | 7 | API 响应测试 |
| `test_utils.py` | 10 | 工具测试 |
| `split_js.py` | 40 | JS 分割工具 |
| `run_visualization.py` | 48 | 可视化运行器 |

---

### 可选模块

**使用 try/except 导入的模块:**

| 文件 | 可选模块 | 说明 |
|------|----------|------|
| `api_server.py` | `jwt` | JWT 认证（未安装则优雅降级） |
| `api_server.py` | `report_generator_v2` | 商业报告生成器（开源版缺失） |
| `api_server.py` | `multi_world_experiment` | 多世界实验（开源版缺失） |
| `data_exporter.py` | `openpyxl` | Excel 导出支持 |
| `decision_engine.py` | `requests` | 本地 LLM 调用（Ollama） |

---

### 依赖分析

**外部依赖 (requirements.txt):**
```
flask>=2.0
requests>=2.25
python-dotenv>=1.0
```

**标准库导入:**
- `sys`, `os`, `json`, `csv`, `time`, `random`, `math`
- `datetime`, `typing`, `dataclasses`, `enum`
- `collections`, `functools`, `pathlib`, `glob`
- `sqlite3`, `logging`, `logging.handlers`
- `threading`, `secrets`, `traceback`, `hashlib`, `re`
- `argparse`, `webbrowser`

**第三方导入:**
- `flask` - Web 框架
- `requests` - HTTP 请求
- `dotenv` - 环境变量加载
- `jwt` (可选) - JWT 认证
- `openpyxl` (可选) - Excel 处理

**内部依赖关系:**
```
run.py
├── config.py
├── api_server.py
│   ├── deep_integration_engine.py
│   ├── experiment_templates_v2.py
│   ├── narrative_engine.py
│   ├── experiment_report_generator.py
│   ├── experiment_runner.py
│   └── [可选] report_generator_v2, multi_world_experiment
├── web_server.py
├── visualizer_v4.py
└── 各核心系统模块

deep_integration_engine.py (核心协调器)
├── ability_system.py
├── corporate_system.py
├── economic_system.py
├── healthcare_system.py
├── housing_system.py
├── marriage_family_system.py
├── social_network_system.py
├── government_system.py
├── decision_engine.py
├── deep_micro_systems.py
└── occupation_system.py
```

---

### 日志分析

**日志文件:** `virtual_world.log` (6.3 MB)

**统计:**
- **WARNING 总数:** 33,679 条
- **ERROR 总数:** 0 条

**WARNING 类型分布:**

| 类型 | 数量 | 占比 |
|------|------|------|
| Financial system init failed | 33,655 | 99.93% |
| Rate limit exceeded (/api/v1/stats/pyramid) | 9 | 0.03% |
| Rate limit exceeded (/api/v1/stats) | 8 | 0.02% |
| Rate limit exceeded (/api/v1/social/network) | 4 | 0.01% |
| Rate limit exceeded (/api/v1/demo/start) | 3 | 0.01% |

**高频警告模式:**
```
[WARNING] virtual_world: Financial system init failed for agent: 
'NoneType' object has no attribute 'create_financial_profile'
```

**分析:**
- 主要警告来自财务系统初始化失败，原因是 `NoneType` 对象缺少 `create_financial_profile` 属性
- 这表明某个系统组件未正确初始化或被设置为 None
- 次要警告是 API 速率限制，来自本地 127.0.0.1 的频繁请求
- 无 ERROR 级别错误，系统整体稳定

---

### 数据库文件状态

**data/ 目录结构:**
```
data/
├── event_archive/    (空)
├── experiments/      (空)
└── reports/          (空)
```

**状态:**
- ❌ 无 SQLite 数据库文件 (.db)
- ⚠️ data/ 子目录存在但为空
- ℹ️ 系统可能使用内存存储或动态创建数据库

---

### 配置文件

**config.py 关键配置:**
```python
WORKSPACE = <项目根目录>
WORLDS_PATH = <workspace>/worlds
DATA_PATH = <workspace>/data
WEB_PATH = <workspace>/web

MAX_DISPLAY_AGENTS = 2000
REFRESH_INTERVAL_SEC = 5

WEB_PORT = 5001
API_PORT = 5002
BIND_HOST = 127.0.0.1

INITIAL_AGENT_COUNT = 10000

# LLM 配置
VOLCENGINE_API_KEY = <从环境变量加载>
VOLCENGINE_MODEL = doubao-seed-2.0-pro
VOLCENGINE_ENDPOINT = https://ark.cn-beijing.volces.com/api/v3
LLM_MODE = rule_only | local_llm | cloud_llm
```

**.env 文件内容:**
```
VOLCENGINE_API_KEY=fe3f0aa9-7919-4bcf-bdea-c62422ef93f1
VOLCENGINE_MODEL=doubao-seed-2.0-pro
VOLCENGINE_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3
YULONG_API_KEY=yulong-dev-key
AGENT_COUNT=10000
```

**安全提示:** ⚠️ .env 文件包含真实 API 密钥，不应提交到 Git

---

### 项目结构总览

```
virtual-world-open-source/
├── 核心系统 (20+ 个.py)
│   ├── ability_system.py
│   ├── corporate_system.py
│   ├── economic_system.py
│   ├── healthcare_system.py
│   ├── housing_system.py
│   ├── marriage_family_system.py
│   ├── social_network_system.py
│   ├── government_system.py
│   ├── occupation_system.py
│   └── deep_micro_systems.py
├── 引擎层
│   ├── deep_integration_engine.py (核心协调)
│   ├── decision_engine.py (决策)
│   ├── narrative_engine.py (叙事)
│   ├── emergence_detector.py (涌现检测)
│   └── event_manager.py (事件管理)
├── 实验系统
│   ├── experiment_runner.py
│   ├── experiment_templates_v2.py
│   └── experiment_report_generator.py
├── API/Web
│   ├── api_server.py (Flask API)
│   ├── web_server.py
│   └── web/ (HTML/JS/CSS)
├── 可视化
│   ├── visualizer_v4.py
│   └── visualizer_v3.py
├── 工具
│   ├── config.py
│   ├── utils.py
│   ├── backup.py
│   └── data_exporter.py
├── 场景系统
│   ├── scenario_selector.py
│   ├── scenario_applier.py
│   ├── scenario_examples.py
│   └── custom_scenario.py
├── 数据
│   ├── name_data_124.py
│   └── data/ (空目录)
└── 文档
    ├── README.md, README_CN.md
    ├── ARCHITECTURE_V5.md
    ├── DESIGN.md
    ├── QUICKSTART.md
    ├── USER_GUIDE.md
    └── CHANGELOG.md
```

---

**报告生成时间:** 2026-03-28 11:35 GMT+8  
**情报司:** 🐉 御龙军
