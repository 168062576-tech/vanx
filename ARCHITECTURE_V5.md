# 御龙军虚拟 Agent 世界 v5 — 系统架构文档

**版本：** v5.0  
**日期：** 2026-03-25  
**Agent 数量：** 10,000  
**子系统数：** 40+  

---

## 一、系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                      前端展示层 (Flask :5001)                 │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────┐ ┌────────┐ │
│  │ Dashboard │ │ WorldMap │ │Console │ │ Demo │ │Reports │ │
│  │ 仪表板    │ │ 世界地图  │ │控制台   │ │演示  │ │报告    │ │
│  │ MBTI/雷达 │ │ Leaflet  │ │24模板  │ │90秒  │ │Excel   │ │
│  └──────────┘ └──────────┘ └────────┘ └──────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      API 服务层 (Flask :5002)                │
│  认证: API Key + JWT | Rate Limit | CORS/CSP | 日志         │
│  端点: /agents /stats /simulate /experiments /chat /story   │
│       /abilities /mbti /finance /events /config/llm         │
│       /simulation/pause|resume /world/inject_event          │
├─────────────────────────────────────────────────────────────┤
│                      事件管理器 (EventManager)               │
│  发布/订阅 | 归档 | 索引 | 上限控制 (50K hot + disk archive) │
├─────────────────────────────────────────────────────────────┤
│                    AI 决策层 (混合架构)                       │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────┐  │
│  │ L0 规则  │ │ L1 本地   │ │ L2 云端    │ │ 上帝视角对话  │  │
│  │ (默认)   │ │ LLM      │ │ LLM       │ │ /chat /story │  │
│  │ 0成本    │ │ (Ollama) │ │ (API)     │ │ 模板降级     │  │
│  └─────────┘ └──────────┘ └───────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                深度集成引擎 (DeepIntegrationEngine)           │
│              17 阶段月度模拟循环 (见下方)                      │
├─────────────────────────────────────────────────────────────┤
│                      核心子系统 (8个)                         │
│  婚姻家庭 | 经济 | 企业 | 住房 | 医疗 | 社交 | 政府 | 微观   │
├─────────────────────────────────────────────────────────────┤
│                    能力系统 (AbilitySystem)                   │
│  三层：天赋(8维) → 技能(35个) → 特质(16种) + MBTI(16型)      │
├─────────────────────────────────────────────────────────────┤
│                    扩展子系统 (18个)                          │
│  金融 | 群体智能 | 因果推断 | 文化传承 | 退休 | 增强职业       │
│  增强教育 | 增强医疗 | 股票 | 职业行为 | 作息 | 多样性保护     │
│  AI决策 | 产品市场 | 商业运营 | 演化报告 | 新闻 | 讨论        │
├─────────────────────────────────────────────────────────────┤
│                    工具模块 (6个)                             │
│  场景系统(4) | 租户 | 多世界管理                              │
├─────────────────────────────────────────────────────────────┤
│                  数据持久层 (SQLite + JSON)                   │
│  agents表 | events表 | world_snapshots | 世界状态JSON        │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、simulate_month 17阶段流程

```
每月模拟循环：

Phase 1:  宏观经济更新 (EconomicSystem.update_economy)
Phase 2:  Agent个体更新 (_update_agent × 10,000)
          ├── 经济 → 住房 → 企业状态 → 金融系统
          ├── 医疗 → 社交 → 深层微观
          ├── 能力系统 (成长/衰减/顿悟/觉醒)
          └── AI决策引擎 (LLM优先 → 规则降级)
Phase 3:  公司月度更新 (O(M) 非 O(N×M))
Phase 4:  政府系统
Phase 5:  婚姻家庭事件
Phase 6:  深层微观18子系统批量模拟
Phase 7:  群体智能 (信息传播/极化/从众)
Phase 8:  金融市场更新 (股市/利率)
Phase 9:  文化传承 (代际影响)
Phase 10: 退休检查
Phase 11: 增强职业 (晋升/失业/转行)
Phase 12: 增强教育 (GPA/考试/升学)
Phase 13: 增强医疗 (疾病/诊断/治疗)
Phase 14: 股票交易 (22个交易日/月)
Phase 15: 作息/职业行为
Phase 16: 新闻系统 (事件注入)
Phase 17: 多样性保护 (防同质化)
```

---

## 三、API 端点清单

### 核心 API
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/health | 健康检查 |
| GET | /api/v1/stats | 世界统计 |
| GET | /api/v1/agents | Agent列表(筛选/分页/排序) |
| GET | /api/v1/agents/{id} | Agent详情 |
| POST | /api/v1/simulate | 模拟N个月 |

### 能力系统
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/agents/{id}/abilities | 能力档案 |
| GET | /api/v1/stats/mbti | MBTI分布 |
| GET | /api/v1/stats/abilities | 能力统计 |
| GET | /api/v1/agents/{id}/finance | 金融摘要 |

### 上帝视角
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | /api/v1/agents/{id}/chat | 与Agent对话 |
| GET | /api/v1/agents/{id}/story | Agent生命故事 |

### 控制
| 方法 | 端点 | 说明 |
|------|------|------|
| GET/PUT | /api/v1/config/llm | LLM模式配置 |
| POST | /api/v1/simulation/pause | 暂停模拟 |
| POST | /api/v1/simulation/resume | 恢复模拟 |
| GET | /api/v1/simulation/status | 模拟状态 |
| POST | /api/v1/world/inject_event | 注入事件 |
| POST | /api/v1/worlds/compare | 世界对比 |

### 事件系统
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/events | 事件列表 |
| GET | /api/v1/events/query | 事件查询(类型/Agent/来源) |
| GET | /api/v1/events/stats | 事件统计 |
| GET | /api/v1/events/stream | SSE实时推送 |

### 实验
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/templates | 模板列表 |
| POST | /api/v1/experiments | 创建实验 |
| GET | /api/v1/experiments/{id} | 实验详情 |
| GET | /api/v1/reports/excel | Excel报告 |

---

## 四、文件结构

```
virtual_world_v5/
├── run.py                          # 一键启动
├── config.py                       # 配置
├── api_server.py (85KB+)           # API服务 + 引擎初始化
├── web_server.py                   # Web前端服务
├── utils.py                        # 工具函数
│
├── deep_integration_engine.py      # 核心引擎 (17阶段循环)
├── ability_system.py               # 三层能力 + MBTI
├── event_manager.py                # 事件总线
├── decision_engine.py              # 规则决策
├── ai_evolution_engine.py          # LLM混合决策
├── narrative_engine.py             # 叙事引擎
│
├── # 核心子系统 (8个)
├── marriage_family_system.py
├── economic_system.py
├── corporate_system.py
├── housing_system.py
├── healthcare_system.py
├── social_network_system.py
├── government_system.py
├── deep_micro_systems.py
│
├── # 扩展子系统 (18个)
├── financial_system.py
├── swarm_intelligence.py
├── causal_inference.py
├── cultural_inheritance_system.py
├── retirement_system.py
├── career_system_enhanced.py
├── education_system_enhanced.py
├── healthcare_system_enhanced.py
├── stock_market_system.py
├── occupation_system.py
├── work_schedule_system.py
├── diversity_protection.py
├── product_market_simulator.py
├── commercial_operations_optimizer.py
├── evolution_report.py
├── integration_modules.py
├── multi_source_news_system.py
├── agent_discussion.py
│
├── # 工具模块
├── custom_scenario.py
├── scenario_applier.py
├── scenario_selector.py
├── scenario_examples.py
├── tenant_system.py
├── multi_world_manager.py
├── experiment_runner.py
├── storage.py
│
├── web/                            # 前端
│   ├── index.html                  # 仪表板
│   ├── worldmap.html               # 世界地图(主页)
│   ├── console.html                # 控制台
│   ├── demo.html                   # 演示模式
│   ├── reports.html                # 报告中心
│   ├── css/main.css
│   └── js/app.js
│
├── data/                           # 数据
│   ├── world.db                    # SQLite
│   └── event_archive/              # 事件归档
│
└── worlds/                         # 世界状态快照
```

---

## 五、性能基准

| 指标 | 数值 |
|------|------|
| Agent 创建 | 10,000 in ~2s |
| 月度模拟 (1000 Agent) | 1.06s |
| 月度模拟 (10000 Agent) | ~10s (估) |
| API 响应 | <100ms (读) |
| 内存占用 | ~200-400MB (10K Agent) |
| MBTI 16型覆盖 | ✅ |
| 稀有特质比例 | ~1% |

---

_御龙军 · 虚拟 Agent 世界 v5 架构文档_  
_2026-03-25_
