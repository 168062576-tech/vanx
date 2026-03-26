# 虚拟 Agent 世界 — 系统设计文档

_从 PoC 到产品的完整蓝图_

**版本：** v3.0 设计稿  
**日期：** 2026-03-23  
**基于：** 六司协作分析报告（Phase 1 + Phase 3 质疑）  
**状态：** 设计中，待司令官审批

---

## 一、系统定位

### 1.1 一句话定义

> **高保真社会操作系统** — 不比"最像人"，比"最像社会"。

### 1.2 核心优势（vs 竞品）

| 维度 | 我们 | Stanford Generative Agents | OASIS | AI Town |
|------|------|---------------------------|-------|---------|
| 子系统丰富度 | **26+** ✅ | 1（沙盒） | 1（社交媒体） | 1（2D 游戏） |
| Agent 规模 | 10,000+ | 25 | 1,000,000 | ~16 |
| 模拟速度 | **0.04ms/agent/月** | 慢（每步 LLM） | 中等 | 实时 |
| LLM 成本 | 零（纯规则） | 高 | 高 | 中 |
| 认知深度 | ❌ 缺失 | ✅ 四层架构 | ✅ | ✅ |

### 1.3 目标形态

**短期：** 一个能跑、能看、能演示的社会模拟系统  
**中期：** 有 LLM 灵魂的混合架构，支持商业实验  
**长期：** 开源的社会模拟平台，支持插件扩展

---

## 二、架构全景

### 2.1 当前架构（v2.0）

```
┌─────────────────────────────────────────────┐
│              Flask Web 可视化                 │
│         visualizer_v3.py (端口 5001)         │
├─────────────────────────────────────────────┤
│              Flask REST API                  │
│          api_server.py (端口 5002)           │  ← ⚠️ 有致命 bug
├───────��─────────────────────────────────────┤
│           深度集成引擎 (核心)                 │
│       deep_integration_engine.py             │
│  ┌─────────┬──────────┬──────────┐          │
│  │ 婚姻家庭 │   经济    │   企业   │          │
│  │ 住房    │   医疗    │ 社交网络 │          │
│  │ 政府    │ 深层微观  │ (集成器) │          │
│  └─────────┴──────────┴──────────┘          │
├─────────────────────────────────────────────┤
│             纯内存存储                       │  ← ⚠️ 无持久化
│        Dict[int, UnifiedAgent]               │
└─────────────────────────────────────────────┘
```

### 2.2 目标架构（v3.0）

```
┌──────────────────────────────────────────────────────┐
│                    前端展示层                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │ 可视化仪表板 │  │ 客户控制台  │  │ 演示模式   │     │
│  │ (ECharts)  │  │ (实验配置)  │  │ (90秒回放) │     │
│  └────────────┘  └────────────┘  └────────────┘     │
├──────────────────────────────────────────────────────┤
│                   API 网关层                          │
│  ┌──────────────────────────────────────────┐        │
│  │  FastAPI + WebSocket + API Key 认证       │        │
│  │  /api/v2/agents  /api/v2/world  /ws      │        │
│  └───────────────────────────��──────────────┘        │
├──────────────────────────────────────────────────────┤
│                   决策引擎层 ⭐ 新��                   │
│  ┌──────────────────────────────────────────┐        │
│  │          LLM 混合决策引擎                  │        │
│  │  ┌─────────┐ ┌──────────┐ ┌───────────┐ │        │
│  │  │ L0 规则  │ │ L1 本地   │ │ L2 线上    │ │        │
│  │  │ (默认)  │ │ LLM      │ │ LLM       │ │        │
│  │  │ 0 成本  │ │ (Ollama) │ │ (API)     │ │        │
│  │  └─────────┘ └──────────┘ └───────────┘ │        │
│  └──────────────────────────────────────────┘        │
├──────────────────────────────────────────────────────┤
│                 社会模拟核心层                         │
│  ┌──────────────────────────────────────────┐        │
│  │         深度集成引擎 (重构版)              │        │
│  │  统一 Agent 档案 + 事件系统 + 子系统编排   │        │
│  └──────────────────────────────────────────┘        │
│  ┌────┐┌────┐┌────┐┌────┐┌────┐┌─���──┐┌────┐┌────┐  │
│  │婚姻││经济││企业││住房││医疗││社交││政府││微观│  │
│  └────┘└────┘└────┘└────┘└────┘└────┘└────┘└────┘  │
├──────────────────────────────────────────────────────┤
│                  数据持久层 ⭐ 新增                    │
│  ┌──────────────────────────────────────────┐        │
│  │  SQLite + 自动备份 + 存档/读档            │        │
│  └──────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────┘
```

---

## 三、模块职责划分

### 3.1 保留模块（核心资产）

| 模块 | 文件 | 大小 | 状态 | 说明 |
|------|------|------|------|------|
| 婚姻家庭 | marriage_family_system.py | 15KB | ✅ 保留 | 核心子系统 |
| 经济系统 | economic_system.py | 20KB | ✅ 保留 | 核心子系统 |
| 企业系统 | corporate_system.py | 21KB | ✅ 保留 | 核心子系统 |
| 住房系统 | housing_system.py | 18KB | ✅ 保留 | 核心子系统 |
| 医疗系统 | healthcare_system.py | 18KB | ✅ 保留 | 核心子系统 |
| 社交网络 | social_network_system.py | 18KB | ✅ 保留 | 核心子系统 |
| 政府系统 | government_system.py | 15KB | ✅ 保留 | 核心子系统 |
| 深层微观 | deep_micro_systems.py | 17KB | ✅ 保留 | 18 个子系统合并 |
| 实验模板 | experiment_templates_v2.py | 19KB | ✅ 保留 | 24 个模板 |

### 3.2 重构模块

| 模块 | 当前文件 | 问题 | 重构方向 |
|------|----------|------|----------|
| 集成引擎 | deep_integration_engine.py | Agent 创建代码重复 3 份 | 统一为唯一入口 |
| 核心集成器 | core_systems_integrator.py | 与引擎功能重叠 | 合并到引擎 |
| API 服务 | api_server.py | 引用未定义的 world_manager | 用 FastAPI 重写 |
| 可视化 | visualizer_v3.py | 与引擎断连，无实时推送 | 接入 WebSocket |

### 3.3 删除模块

| 模块 | 文件 | 原因 |
|------|------|------|
| 集成测试 | full_integration_test.py | 重复了引擎的 Agent 创建逻辑，应改为 pytest |
| 性能测试 | performance_test.py | 同上，重复代码 |

### 3.4 新增模块

| 模块 | 文件 | 职责 |
|------|------|------|
| **LLM 决策引擎** | decision_engine.py | 三级决策：规则/本地LLM/线上LLM |
| **持久化层** | storage.py | SQLite 读写 + 自动备份 |
| **叙事引擎** | narrative_engine.py | Agent 生命故事生成 |
| **事件管理器** | event_manager.py | 事件索引 + 归档 + 上限控制 |

---

## 四、LLM 混合决策引擎设计

### 4.1 三级 Agent 模型

```
┌─────────────────────────────────────────────┐
│              Agent 决策请求                   │
│  "Agent #3721 要不要换工作？"                 │
├─────────────────────────────────────────────┤
│                                              │
│   决策路由器 (DecisionRouter)                 │
│   ├── 检查决策类型 + Agent 等级               │
│   ├── 检查 LLM 可用性和预算                   │
│   └── 分发到对应引擎                         │
│                                              │
│   ┌───────────┐ ┌───────────┐ ┌───────────┐ │
│   │  L0 规则   │ │ L1 本地    │ │ L2 线上    │ │
│   │           │ │ LLM       │ │ LLM       │ │
│   ├───────────┤ ├───────────┤ ├───────────┤ │
│   │ 90% Agent │ │ 9% Agent  │ │ 1% Agent  │ │
│   │ 日常决策   │ │ 关键决策   │ │ 重大决策   │ │
│   │ 0 成本    │ │ 低成本    │ │ 按需付费   │ │
│   │ <0.01ms   │ │ ~100ms    │ │ ~1-3s     │ │
│   └───────────┘ └───────────┘ └───────────┘ │
└─────────────────────────────────────────────┘
```

### 4.2 决策类型分级

| 级别 | 决策类型 | 引擎 | 示例 |
|------|---------|------|------|
| 日常 | 消费、通勤、社交互动 | L0 规则 | 买菜花多少钱 |
| 关键 | 换工作、结婚、买房 | L1 本地 LLM | ���不要接受这个 offer |
| 重大 | 创业、移民、犯罪 | L2 线上 LLM | 要不要辞职创业 |

### 4.3 接口设计

```python
class DecisionEngine:
    """三级混合决策引擎"""
    
    def __init__(self, config: dict):
        self.mode = config.get('mode', 'rule_only')  # rule_only | hybrid | full_llm
        self.local_model = config.get('local_model', 'qwen2.5:7b')  # Ollama 模型
        self.remote_model = config.get('remote_model', 'qwen-plus')  # API 模型
        self.remote_api_key = config.get('api_key', '')
        self.budget_limit = config.get('monthly_budget', 0)  # 月预算（元）
        self.budget_used = 0
    
    def decide(self, agent: UnifiedAgent, context: DecisionContext) -> Decision:
        """统一决策入口"""
        level = self._classify_decision(context)
        
        if level == 'routine' or self.mode == 'rule_only':
            return self._rule_decide(agent, context)
        elif level == 'important' and self.mode in ('hybrid', 'full_llm'):
            return self._local_llm_decide(agent, context)
        elif level == 'critical' and self.mode == 'full_llm':
            return self._remote_llm_decide(agent, context)
        else:
            return self._rule_decide(agent, context)  # 降级
    
    def _classify_decision(self, ctx: DecisionContext) -> str:
        """决策分级：routine / important / critical"""
        ...
    
    def _rule_decide(self, agent, ctx) -> Decision:
        """L0: 纯规则引擎（现有逻辑）"""
        ...
    
    def _local_llm_decide(self, agent, ctx) -> Decision:
        """L1: 本地 LLM（Ollama）"""
        prompt = self._build_prompt(agent, ctx)
        response = ollama.generate(model=self.local_model, prompt=prompt)
        return self._parse_response(response)
    
    def _remote_llm_decide(self, agent, ctx) -> Decision:
        """L2: 线上 LLM（API）"""
        if self.budget_used >= self.budget_limit:
            return self._local_llm_decide(agent, ctx)  # 超预算降级
        ...

@dataclass
class DecisionContext:
    """决策上下文"""
    decision_type: str          # 'career_change', 'marriage', 'purchase', etc.
    options: List[str]          # 可选项
    agent_state: dict           # Agent 当前状态快照
    world_state: dict           # 世界状态快照
    urgency: float = 0.5       # 紧迫程度 0-1

@dataclass  
class Decision:
    """决策结果"""
    choice: str                 # 选择
    reasoning: str              # 理由（LLM 提供，规则引擎为空）
    confidence: float           # 置信度 0-1
    engine_used: str            # 'rule' / 'local_llm' / 'remote_llm'
    cost: float = 0            # LLM 调用成本
```

### 4.4 前端配置界面

```
┌─────────────────────────────────────┐
│  🧠 决策引擎设置                     │
│                                      │
│  模式：[● 纯规则] [○ 混合] [○ 全LLM] │
│                                      │
│  本地模型：[qwen2.5:7b      ▼]      │
│  线上模型：[qwen-plus       ▼]      │
│  API Key：  [************    ]      │
│  月预算：   [¥ 50           ]      │
│                                      │
│  ── 决策分级阈值 ──                  │
│  日常决策 (L0 规则)：  [90]%         │
│  关键决策 (L1 本地)：  [ 9]%         │
│  重大决策 (L2 线上)：  [ 1]%         │
│                                      │
│  [保存配置]  [恢复默认]              │
└─────────────────────────────────────┘
```

---

## 五、数据流设计

### 5.1 模拟循环

```
每月模拟周期：
                                    
  ┌──────────┐    ┌──────────────┐    ┌──────────────┐
  │ 读取 Agent │───▶│  子系统更新   │───▶│  决策引擎     │
  │ (SQLite)  │    │ (8 子系统)   │    │ (L0/L1/L2)  │
  └──────────┘    └──────────────┘    └──────────────┘
                         │                     │
                         ▼                     ▼
                  ┌──────────────┐    ┌──��───────────┐
                  │  事件生成     │───▶│  写入 SQLite  │
                  │ (WorldEvent) │    │  + 事件归档   │
                  └──────────────┘    └──────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ WebSocket 推送│
                  │  → 前端实时   │
                  └──────────────┘
```

### 5.2 数据模型（SQLite）

```sql
-- Agent 主表
CREATE TABLE agents (
    id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER,
    gender TEXT,
    -- 基础属性
    education_level TEXT,
    occupation TEXT,
    income REAL,
    net_worth REAL,
    -- 状态
    health_score REAL,
    happiness REAL,
    marital_status TEXT,
    -- JSON 扩展字段（子系统专用数据）
    extended_data JSON,
    updated_at TIMESTAMP
);

-- 事件表（带自动归档）
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month INTEGER,
    agent_id INTEGER,
    event_type TEXT,
    description TEXT,
    data JSON,
    created_at TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- 事件归档（超过 N 条自动转移）
CREATE TABLE events_archive (
    -- 同 events 结构
);

-- 世界快照（存档/读档）
CREATE TABLE world_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    month INTEGER,
    agent_count INTEGER,
    snapshot_data JSON,  -- 压缩的完整世界状态
    created_at TIMESTAMP
);

-- 实验记录
CREATE TABLE experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT,
    config JSON,
    status TEXT,  -- running / completed / failed
    results JSON,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

---

## 六、前端/后端边界

### 6.1 API 设计（v2）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/world/status` | GET | 世界状态概览 |
| `/api/v2/world/simulate` | POST | 执行 N 个月模拟 |
| `/api/v2/world/snapshot` | POST | 创建快照 |
| `/api/v2/world/restore/{id}` | POST | 恢复快照 |
| `/api/v2/agents` | GET | Agent 列表（分页 + 筛选） |
| `/api/v2/agents/{id}` | GET | Agent 详情 |
| `/api/v2/agents/{id}/story` | GET | Agent 生命故事（叙事引擎） |
| `/api/v2/events` | GET | 事件流（分页 + 类型筛选） |
| `/api/v2/experiments` | POST | 启动实验 |
| `/api/v2/experiments/{id}` | GET | 实验结果 |
| `/api/v2/config/decision` | GET/PUT | 决策引擎配置 |
| `/ws/events` | WS | 实时事件推送 |
| `/ws/simulation` | WS | 模拟进度推送 |

### 6.2 前端页面规划

| 页面 | 优先级 | 说明 |
|------|--------|------|
| 仪表板 | P0 | 世界概览 + 关键指标 + ECharts 图表 |
| Agent 详情 | P0 | 个人档案 + 生命故事 + 关系网络 |
| 实验控制台 | P1 | 选模板 → 配参数 → 运行 → 看结果 |
| 事件流 | P1 | 实时事件滚动 + 类型筛选 |
| 决策引擎配置 | P1 | LLM 模式选择 + 参数调节 |
| 演示模式 | P2 | 90 秒自动演绎（创世→发展→回顾） |
| 时间线 | P2 | 历史趋势图 + 回放 |

---

## 七、已知问题与修复计划

### 7.1 P0 致命问题

| # | 问题 | 文件 | 修复方案 |
|---|------|------|----------|
| 1 | api_server.py 引用未定义的 `world_manager` | api_server.py | 用 FastAPI 重写 |
| 2 | O(N×M) 公司遍历 bug | deep_integration_engine.py | 分离 Agent 更新和公司更新 |
| 3 | 事件列表无限增长 | deep_integration_engine.py | 加上限 + 归档机制 |
| 4 | 三套重复的 Agent 创建代码 | 3 个文件 | 统一到引擎 |

### 7.2 P1 安全基线

| # | 措施 | 工作量 |
|---|------|--------|
| 1 | ✅ Git 版本控制 | 已完成 |
| 2 | API Key 认证中间件 | 30 分钟 |
| 3 | SQLite 持久化 | 5-7 天 |
| 4 | 每日自动备份脚本 | 20 分钟 |
| 5 | 异常处理框架 | 1 天 |

### 7.3 丢失文件待��建

| 文件 | 功能 | 重建优先级 |
|------|------|-----------|
| ai_evolution_engine.py | LLM 混合决策 | P1（用本文档第四章设计重建） |
| 客户控制台前端 | 实验配置 UI | P1 |

---

## 八、实施路线图

```
Week 1: 急救 + 地基
├── Day 1-2: 修 P0 bug（API / O(N×M) / 重复代码）
├── Day 3-5: SQLite 持久化 + 备份脚本
├── Day 5: API Key 认证 + 异常处理
└── 里程碑: 系统能跑且不丢数据

Week 2-3: 核心功能
├── 重建 LLM 混合决策引擎 (decision_engine.py)
├── 重建客户控制台前端
├── FastAPI 重写 API 层 + WebSocket
└── 里程碑: 混合决策可用，前端能配置

Week 4: 体验层
├── ECharts 可视化升级
├── 事件流面板
├── 90 秒演示模式
└── 里程碑: 可以给人演示

Month 2: 深化
├── 叙事引擎
├── Agent 关系网络可视化
├── 实验对比框架
└── 补全文档（QUICKSTART / API 文档）

Month 3+: 开放
├── 插件系统
├── 开源准备
├── "上帝视角"交互
└── 多世界平行对比
```

---

## 九、文件结构规划

```
virtual_world/
├── README.md                    # 快速入门
├── DESIGN.md                    # 本文档
├── ARCHITECTURE.md              # 架构概述（更新）
├── CHANGELOG.md                 # 变更日志（新增）
├── requirements.txt             # 依赖清单（新增）
├── .gitignore                   # ✅ 已创建
│
├── core/                        # 核心引擎（重构）
│   ├── __init__.py
│   ├── engine.py                # 深度集成引擎（统一版）
│   ├── agent.py                 # UnifiedAgent 定义
│   ├── events.py                # 事件系统
│   └── decision_engine.py       # LLM 混合决策引擎（新增）
│
├── systems/                     # 子系统（保留）
│   ├── __init__.py
│   ├── marriage_family.py
│   ├── economic.py
│   ├── corporate.py
│   ├── housing.py
│   ├── healthcare.py
│   ├── social_network.py
│   ├── government.py
│   └── deep_micro.py
│
├── storage/                     # 持久化（新增）
│   ├── __init__.py
│   ├── sqlite_store.py
│   └── backup.py
│
├── api/                         # API 层（重写）
│   ├── __init__.py
│   ├── server.py                # FastAPI 主服务
│   ├── routes/
│   └── websocket.py
│
├── web/                         # 前端（重建）
│   ├── index.html               # 仪表板
│   ├── console.html             # 客户控制台
│   ├── demo.html                # 演示模式
│   └── assets/
│
├── experiments/                  # 实验（新增）
│   ├── templates.py
│   └── logs/                    # 实验日志
│
└── tests/                       # 测试（新增）
    ├── test_engine.py
    ├── test_systems.py
    └── test_api.py
```

---

_御龙军 · 虚拟 Agent 世界设计文档 v3.0_  
_基于六司协作分析（12 份报告）+ 代码实际审查_  
_2026-03-23_
