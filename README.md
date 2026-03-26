# 🌍 VanX · 万象界

> **A high-fidelity social simulation system** — *ten thousand agents, ten thousand faces, one world of your own*  
> **万人万相，自成一界**

[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Agents](https://img.shields.io/badge/Agents-10,000+-purple.svg)]()

[English](README.md) | [简体中文](README_CN.md)

---

## 🎬 See it in Action

```bash
# 3 commands to start your first simulation
git clone https://github.com/168062576-tech/vanx.git
cd vanx
pip install -r requirements.txt
python run.py
# → Open http://localhost:5001
```

**10,000 agents × 8 core social systems × zero LLM cost = emergent social dynamics**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🏙️ 8 Core Subsystems** | Economy, Marriage, Housing, Healthcare, Corporate, Social Networks, Government, Micro-behaviors |
| **👥 10,000+ Agents** | Each with unique name, personality, career, relationships, memories |
| **⚡ Zero LLM Cost** | Pure rule-based engine runs at 0.04ms/agent/month |
| **📊 Real-time Visualization** | Dashboard, world map, event stream, trend charts |
| **🧪 Experiment Templates** | Economic crisis, epidemic, aging population, policy simulation |
| **💾 SQLite Persistence** | Save/load worlds, continue simulations anytime |

---

## 🏆 Why VanX · 万象界?

| | **VanX** | Stanford GenAI | OASIS | AI Town |
|---|---|---|---|---|
| **Subsystems** | **8 core** | 1 (sandbox) | 1 (social) | 1 (2D game) |
| **Agent Scale** | **10,000+** | 25 | 1M | ~16 |
| **Speed** | **0.04ms/agent/month** | Slow | Medium | Realtime |
| **LLM Cost** | **$0 (rule-based)** | High | High | High |

> **We're not the most human-like AI. We're the most society-like simulation.**

---

## 📸 Screenshots

### Dashboard — Real-time Social Metrics
![Dashboard](docs/screenshots/dashboard.png)

### World Map — Agent Distribution by Region
![World Map](docs/screenshots/worldmap.png)

### Event Stream — Life Stories Unfolding
![Event Stream](docs/screenshots/events.png)

### Experiment Console — Policy Simulation
![Experiments](docs/screenshots/experiments.png)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Frontend                          │
│         (Dashboard / Map / Demo / Reports)              │
└────────────────────┬────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────┐
│                   API Server (Flask)                     │
│              ┌─────────────────────────┐                │
│              │   Deep Integration      │                │
│              │        Engine           │                │
│              └───────────┬─────────────┘                │
│                          │                               │
│    ┌─────────────────────┼─────────────────────┐        │
│    │                     │                     │        │
│ ┌──▼────┐ ┌─────────────▼─┐ ┌──────────────┐  │        │
│ │Economy│ │Marriage/Family│ │Healthcare    │  │ ...    │
│ └───────┘ └───────────────┘ └──────────────┘  │        │
│                                                 │        │
│ ┌─────────────────────────────────────────────┐│        │
│ │         SQLite Persistence Layer            ││        │
│ └─────────────────────────────────────────────┘│        │
└─────────────────────────────────────────────────┘        │
```

### Core Subsystems (Open Source)

1. **Economic System** — Income, consumption, wealth distribution
2. **Marriage & Family** — Matching, divorce, child-rearing
3. **Housing System** — Buying, renting, mortgage, market dynamics
4. **Healthcare System** — Health decay, diagnosis, treatment
5. **Corporate System** — Hiring, firing, promotion, industry structure
6. **Social Networks** — Friendships, influence, information spread
7. **Government System** — Taxes, welfare, policy interventions
8. **Deep Micro-behaviors** — Daily routines, risk tolerance, habits

### Advanced Subsystems (Commercial)

- Stock Market, Financial System, Swarm Intelligence
- Causal Inference, Product Market Simulator
- Multi-world Management, Tenant System
- Enhanced Education/Career/Healthcare
- AI Evolution Engine (LLM hybrid decision)
- And 8 more...

> 💡 **Want all 26+ subsystems?** Check out VanX Pro

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/168062576-tech/vanx.git
cd vanx

# Install dependencies
pip install -r requirements.txt

# Start the simulation
python run.py

# Open your browser
# Web UI: http://localhost:5001
# API:    http://localhost:5002
```

### First Simulation

1. Open http://localhost:5001
2. Watch 10,000 agents come to life
3. Click "Simulate 1 Month" to see social dynamics unfold
4. Check the event stream for life stories

### Run Your First Experiment

```python
from deep_integration_engine import DeepIntegrationEngine
from experiment_runner import ExperimentRunner

# Create engine
engine = DeepIntegrationEngine()
engine.initialize(agents=10000)

# Run experiment
runner = ExperimentRunner(engine)
result = runner.run_template('economic_crisis')

# View results
print(f"Unemployment: {result['unemployment_rate']:.1%}")
print(f"Gini coefficient: {result['gini']:.3f}")
```

---

## 📖 Documentation

| Doc | Description |
|-----|-------------|
| [Quick Start](QUICKSTART.md) | 5-minute getting started guide |
| [User Guide](USER_GUIDE.md) | Full API reference and examples |
| [Architecture](ARCHITECTURE_V5.md) | System design and data flow |
| [Experiment Templates](docs/experiments.md) | 24 built-in experiment scenarios |

---

## 🧪 Experiment Templates

### Included in Open Source (3)

| Template | Description |
|----------|-------------|
| **Economic Crisis** | Trigger recession → observe unemployment, crime, mental health |
| **Epidemic Outbreak** | Simulate disease spread → healthcare overload, policy effects |
| **Aging Population** | Fast-forward 30 years → labor shortage, pension pressure |

### Available in Pro (21)

- Housing Policy Comparison
- Education Investment ROI
- Wealth Inequality Study
- Urbanization Dynamics
- Stock Market Crash
- Universal Basic Income Trial
- Healthcare Reform
- Immigration Impact
- And 13 more...

---

## 🤝 Contributing

We welcome contributions! Here's how to help:

### Good First Issues

- [ ] Add a new agent name for your culture
- [ ] Translate documentation to your language
- [ ] Report bugs or suggest features
- [ ] Share your experiment results

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Code of Conduct

Please be respectful and inclusive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## 📜 License

Apache License 2.0 — free for personal and commercial use.

See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- Inspired by Stanford's [Generative Agents](https://arxiv.org/abs/2304.03442)
- Built with [Flask](https://flask.palletsprojects.com/) and [ECharts](https://echarts.apache.org/)
- Name data from 124 cultures worldwide

---

## 📬 Contact

- **GitHub Issues:** [Report bugs / Request features](https://github.com/168062576-tech/vanx/issues)
- **Discord:** [Join our community](https://discord.gg/xxx)
- **Email:** yulong@vanx.tech

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=168062576-tech/vanx&type=Date)](https://star-history.com/)

---

_Built with 🐉 by YulongLegion_  
**VanX · 万象界** — 万人万相，自成一界
