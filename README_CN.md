# 🌍 VanX · 万象界

> **高保真社会模拟系统** — **万人万相，自成一界**  
> **A high-fidelity social simulation system** — *ten thousand agents, ten thousand faces, one world of your own*

[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Agents](https://img.shields.io/badge/Agents-10,000+-purple.svg)]()

[English](README.md) | [简体中文](README_CN.md)

---

## 🎬 快速演示

```bash
# 3 条命令启动你的第一个模拟
git clone https://github.com/168062576-tech/vanx.git
cd vanx
pip install -r requirements.txt
python run.py
# → 打开 http://localhost:5001
```

**10,000 个 Agent × 8 个核心社会系统 × 零 LLM 成本 = 社会涌现动态**

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| **🏙️ 8 个核心子系统** | 经济/婚姻/住房/医疗/企业/社交/政府/微观行为 |
| **👥 10,000+ Agent** | 每个都有姓名/性格/职业/关系/记忆 |
| **⚡ 零 LLM 成本** | 纯规则引擎，0.04ms/agent/月 |
| **📊 实时可视化** | 仪表盘/世界地图/事件流/趋势图 |
| **🧪 实验模板** | 经济危机/流行病/人口老龄化/政策模拟 |
| **💾 SQLite 持久化** | 随时保存/读取世界状态 |

---

## 🏆 为什么选择 VanX · 万象界？

| | **VanX 万象界** | Stanford GenAI | OASIS | AI Town |
|---|---|---|---|---|
| **子系统数** | **8 个核心** | 1 个 | 1 个 | 1 个 |
| **Agent 规模** | **10,000+** | 25 | 100 万 | ~16 |
| **模拟速度** | **0.04ms/agent/月** | 慢 | 中等 | 实时 |
| **LLM 成本** | **¥0（纯规则）** | 高 | 高 | 高 |

> **我们不是最像人的 AI，我们是最像社会的模拟。**

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- pip（Python 包管理器）

### 安装

```bash
# 克隆仓库
git clone https://github.com/168062576-tech/vanx.git
cd vanx

# 安装依赖
pip install -r requirements.txt

# 启动模拟
python run.py

# 打开浏览器
# Web 界面：http://localhost:5001
# API 端点：http://localhost:5002
```

### 第一次模拟

1. 打开 http://localhost:5001
2. 观看 10,000 个 Agent 开始生活
3. 点击"模拟 1 个月"观察社会动态
4. 查看事件流中的生命故事

### 运行第一个实验

```python
from deep_integration_engine import DeepIntegrationEngine
from experiment_runner import ExperimentRunner

# 创建引擎
engine = DeepIntegrationEngine()
engine.initialize(agents=10000)

# 运行实验
runner = ExperimentRunner(engine)
result = runner.run_template('economic_crisis')

# 查看结果
print(f"失业率：{result['unemployment_rate']:.1%}")
print(f"基尼系数：{result['gini']:.3f}")
```

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [快速开始](QUICKSTART.md) | 5 分钟入门指南 |
| [用户指南](USER_GUIDE.md) | 完整 API 参考和示例 |
| [架构文档](ARCHITECTURE_V5.md) | 系统设计和数据流 |
| [实验模板](docs/experiments.md) | 24 个内置实验场景 |

---

## 🧪 实验模板

### 开源版包含（3 个）

| 模板 | 说明 |
|------|------|
| **经济危机** | 触发经济衰退 → 观察失业率/犯罪率/心理健康变化 |
| **流行病爆发** | 模拟疫情传播 → 医疗系统压力/政策效果 |
| **人口老龄化** | 加速 30 年 → 劳动力短缺/养老金压力 |

### 专业版包含（21 个）

- 住房政策对比
- 教育投资回报率
- 贫富分化研究
- 城市化进程
- 股票市场崩盘
- 全民基本收入实验
- 医疗改革
- 移民影响
- 还有 13 个...

---

## 🏗️ 系统架构

### 开源版核心子系统（8 个）

1. **经济系统** — 收入/消费/财富分配
2. **婚姻家庭系统** — 匹配/离婚/育儿
3. **住房系统** — 买房/租房/房贷/市场动态
4. **医疗健康系统** — 健康衰减/诊断/治疗
5. **企业系统** — 招聘/解雇/晋升/产业结构
6. **社交网络系统** — 友谊/影响力/信息传播
7. **政府系统** — 税收/福利/政策干预
8. **深层微观行为** — 日常作息/风险偏好/习惯

### 专业版高级子系统（18 个）

- 股票市场、金融系统、群体智能
- 因果推断、产品市场模拟器
- 多世界管理、租户系统
- 增强版教育/职业/医疗
- AI 演化引擎（LLM 混合决策）
- 还有 8 个...

> 💡 **想要全部 26+ 子系统？** 查看 [Agent World Pro](https://agentworld.pro)

---

## 🤝 参与贡献

欢迎贡献！你可以这样帮助：

### 适合新手的任务

- [ ] 为你的文化添加新的 Agent 姓名
- [ ] 翻译文档到你的语言
- [ ] 报告 Bug 或建议功能
- [ ] 分享你的实验结果

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📜 许可证

Apache License 2.0 — 个人和商业使用均免费。

详见 [LICENSE](LICENSE)。

---

## 🙏 致谢

- 灵感来自 Stanford 的 [Generative Agents](https://arxiv.org/abs/2304.03442)
- 使用 [Flask](https://flask.palletsprojects.com/) 和 [ECharts](https://echarts.apache.org/) 构建
- 姓名数据来自全球 124 种文化

---

## 📬 联系方式

- **GitHub Issues:** [报告 Bug / 请求功能](https://github.com/YOUR_USERNAME/agent-world-engine/issues)
- **Discord:** [加入社区](https://discord.gg/xxx)
- **Twitter:** [@AgentWorldEng](https://twitter.com/AgentWorldEng)
- **邮箱:** hello@agentworld.pro

---

_用 🐉 由御龙军构建_
