# 🚀 快速开始

_5 分钟从零到跑起来的上手指南_

---

## 环境要求

- **Python 3.10+**
- **依赖安装：**

```bash
pip install flask requests
```

---

## 一键启动

```bash
cd virtual_world
python run.py
```

启动后会自动：
1. 初始化 API 引擎 + 创建 10,000 个 Agent
2. 启动 Web 前端服务
3. 自动打开浏览器（可用 `--no-browser` 禁用）

```
============================================================
  Yulong Virtual Agent World
  Dual-service architecture
============================================================
  Web:    http://127.0.0.1:5001
  API:    http://127.0.0.1:5002
  Agents: 10000
============================================================
```

---

## 访问地址

| 地址 | 说明 |
|------|------|
| http://localhost:5001 | 🏠 主界面（仪表板 + 区域地图 + 趋势图 + 事件流） |
| http://localhost:5002 | ⚙️ API 服务（RESTful 接口） |
| http://localhost:5001/demo | 🎬 演示模式（1000 Agent × 12 月加速模拟） |
| http://localhost:5001/reports | 📊 报告中心（生成/查看/下载报告） |

---

## 配置

通过环境变量自定义：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `AGENT_COUNT` | `10000` | 初始 Agent 数量 |
| `BIND_HOST` | `127.0.0.1` | 绑定地址 |
| `WEB_PORT` | `5001` | Web 前端端口 |
| `API_PORT` | `5002` | API 服务端口 |
| `YULONG_API_KEY` | `yulong-dev-key` | API 认证密钥 |

**示例：** 启动 500 个 Agent 并监听所有网卡

```bash
# Linux / macOS
AGENT_COUNT=500 BIND_HOST=0.0.0.0 python run.py

# Windows PowerShell
$env:AGENT_COUNT=500; $env:BIND_HOST="0.0.0.0"; python run.py
```

---

## API 快速参考

所有 API 端点（健康检查除外）需在请求头中携带 `X-API-Key`。

### 基础

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查（无需认证） |
| GET | `/api/v1/stats` | 世界统计数据 |
| GET | `/api/v1/stats/pyramid` | 人口金字塔（按年龄/性别） |
| GET | `/api/v1/events` | 最近事件流（?limit=50） |

### Agent 管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/agents` | Agent 列表（?limit=100&offset=0） |
| GET | `/api/v1/agents/<id>` | Agent 详情 |
| GET | `/api/v1/agents/<id>/story` | Agent 生命故事（叙事引擎） |
| GET | `/api/v1/agents/<id>/display` | Agent 显示数据（含中文名） |
| GET | `/api/v1/agents/display` | Agent 地图显示列表 |
| POST | `/api/v1/agents/create` | 创建 Agent（body: `{count, agent_data}`） |

### 模拟控制

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/simulate` | 推进模拟（body: `{months: 1-120}`） |
| POST | `/api/v1/demo/start` | 启动演示模式（独立沙盒） |

### 实验系统

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/experiments/templates` | 实验模板列表（?category=...） |
| GET | `/api/v1/experiments/templates/<id>` | 模板详情 |
| POST | `/api/v1/experiments/run` | 运行实验（body: `{template_id, ...}`） |

### 报告系统

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/reports/generate` | 生成报告（body: `{type: html/json/markdown}`） |
| POST | `/api/v1/reports/smart` | 智能报告（body: `{level: executive/business/technical}`） |
| GET | `/api/v1/reports/list` | 已生成报告列表 |

### 快速测试

```bash
# 健康检查
curl http://localhost:5002/api/v1/health

# 获取统计（需认证）
curl -H "X-API-Key: yulong-dev-key" http://localhost:5002/api/v1/stats

# 推进 3 个月
curl -X POST -H "Content-Type: application/json" \
     -H "X-API-Key: yulong-dev-key" \
     -d '{"months": 3}' \
     http://localhost:5002/api/v1/simulate

# 生成 HTML 报告
curl -X POST -H "Content-Type: application/json" \
     -H "X-API-Key: yulong-dev-key" \
     -d '{"type": "html"}' \
     http://localhost:5002/api/v1/reports/generate
```

---

## 项目结构

```
virtual_world/
├── run.py                  # 一键启动脚本
├── config.py               # 全局配置
├── api_server.py           # API 服务（端口 5002）
├── web_server.py           # Web 服务（端口 5001）
├── deep_integration_engine.py  # 深度集成引擎（核心）
├── decision_engine.py      # LLM 混合决策引擎
├── narrative_engine.py     # 叙事引擎
├── report_generator_v2.py  # 报告生成器
├── storage.py              # SQLite 持久化层
├── web/                    # 前端资源
│   ├── index.html          # 主仪表板
│   ├── demo.html           # 演示模式页面
│   ├── reports.html        # 报告中心
│   ├── css/main.css        # 样式
│   └── js/app.js           # 前端逻辑
├── data/                   # 生成的报告文件
├── worlds/                 # 世界存档
└── tests/                  # 测试
```

---

## 常见问题

**Q: 端口被占用？**
```bash
$env:WEB_PORT=8001; $env:API_PORT=8002; python run.py
```

**Q: 启动慢？**
减少初始 Agent 数量：`$env:AGENT_COUNT=500; python run.py`

**Q: API 返回 401？**
所有非健康检查接口需要 `X-API-Key` 请求头，默认值为 `yulong-dev-key`。

---

_御龙军虚拟 Agent 世界 · 快速上手指南_
