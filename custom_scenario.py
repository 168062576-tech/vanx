# -*- coding: utf-8 -*-
"""
御龙军虚拟世界 v5 - 自定义场景创建
移植自 v1.0，适配 v5 UnifiedAgent
功能：创建自定义场景，支持产品测试/政策评估/营销对比/组织变革/自由讨论
"""

import random
from datetime import datetime
from typing import Dict, List, Optional


class ScenarioConfig:
    """场景配置"""

    def __init__(self, name: str = "", scenario_type: str = "custom",
                 description: str = "", duration_days: int = 30,
                 agent_count: int = 100, metrics: List[str] = None,
                 success_criteria: Dict[str, float] = None, **kwargs):
        self.name = name or "自定义场景"
        self.scenario_type = scenario_type
        self.description = description
        self.duration_days = duration_days
        self.agent_count = agent_count
        self.metrics = metrics or ['满意度', '效率', '成本']
        self.success_criteria = success_criteria or {}
        self.extra = kwargs  # features, channels, questions 等

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'scenario_type': self.scenario_type,
            'description': self.description,
            'duration_days': self.duration_days,
            'agent_count': self.agent_count,
            'metrics': self.metrics,
            'success_criteria': self.success_criteria,
            **self.extra,
        }


class CustomScenarioEngine:
    """自定义场景引擎（v5 适配版）

    不再依赖 input() 交互，改为纯 API 调用。
    """

    # 预置场景模板
    TEMPLATES = {
        'product_test': {
            'scenario_type': 'product_test',
            'metrics': ['购买意愿', '满意度', '推荐率', '复购率'],
            'success_criteria': {'购买意愿': 0.3, '满意度': 4.0, '推荐率': 0.2},
            'duration_days': 30,
        },
        'policy_eval': {
            'scenario_type': 'policy_eval',
            'metrics': ['满意度', '就业率', '收入变化', '生活成本'],
            'success_criteria': {'满意度': 3.5, '就业率': 0.9},
            'duration_days': 90,
        },
        'marketing_compare': {
            'scenario_type': 'marketing_compare',
            'metrics': ['转化率', '获客成本', 'ROI', '品牌认知'],
            'success_criteria': {'转化率': 0.15},
            'duration_days': 60,
        },
        'org_change': {
            'scenario_type': 'org_change',
            'metrics': ['员工满意度', '离职率', '工作效率', '团队协作'],
            'success_criteria': {'员工满意度': 3.5, '离职率': 0.1},
            'duration_days': 60,
        },
        'discussion': {
            'scenario_type': 'discussion',
            'metrics': ['观点多样性', '共识度', '讨论深度'],
            'success_criteria': {},
            'duration_days': 10,
        },
    }

    def __init__(self, config: dict = None):
        self.config = config or {}

    def create_scenario(self, template: str = "custom", **kwargs) -> ScenarioConfig:
        """创建场景

        Args:
            template: 模板名称 (product_test / policy_eval / marketing_compare /
                      org_change / discussion / custom)
            **kwargs: 覆盖模板默认值的参数

        Returns:
            ScenarioConfig 实例
        """
        base = dict(self.TEMPLATES.get(template, {}))
        base.update(kwargs)
        return ScenarioConfig(**base)

    def run_scenario(self, scenario: ScenarioConfig, agents: dict) -> Dict:
        """执行场景模拟

        Args:
            scenario: 场景配置
            agents: {agent_id: UnifiedAgent} 字典

        Returns:
            {
              'scenario': dict,
              'daily_metrics': {day: {metric: value}},
              'final_results': {metric: value},
              'success_evaluation': {metric: {actual, target, passed}},
              'trend_analysis': {metric: {first, last, change_pct}},
            }
        """
        agent_list = list(agents.values())
        n = min(scenario.agent_count, len(agent_list))
        sample = random.sample(agent_list, n) if n < len(agent_list) else agent_list

        daily_metrics: Dict[int, Dict[str, float]] = {}

        for day in range(1, scenario.duration_days + 1):
            day_data = self._simulate_day(scenario, sample, day)
            daily_metrics[day] = day_data

        # 最终结果 = 最后一天
        final = daily_metrics.get(scenario.duration_days, {})

        # 趋势分析
        first = daily_metrics.get(1, {})
        trend = {}
        for metric in scenario.metrics:
            f_val = first.get(metric, 0)
            l_val = final.get(metric, 0)
            change = ((l_val - f_val) / f_val * 100) if f_val else 0
            trend[metric] = {'first': round(f_val, 3), 'last': round(l_val, 3),
                             'change_pct': round(change, 1)}

        # 成功评估
        evaluation = {}
        for metric, target in scenario.success_criteria.items():
            actual = final.get(metric, 0)
            evaluation[metric] = {
                'actual': round(actual, 3),
                'target': target,
                'passed': actual >= target,
            }

        return {
            'scenario': scenario.to_dict(),
            'daily_metrics': daily_metrics,
            'final_results': final,
            'success_evaluation': evaluation,
            'trend_analysis': trend,
        }

    # ------------------------------------------------------------------
    # 内部模拟逻辑
    # ------------------------------------------------------------------

    def _simulate_day(self, scenario: ScenarioConfig, agents: list, day: int) -> Dict[str, float]:
        """模拟一天的场景"""
        metrics: Dict[str, List[float]] = {m: [] for m in scenario.metrics}

        for agent in agents:
            values = self._agent_day_values(scenario, agent, day)
            for m, v in values.items():
                if m in metrics:
                    metrics[m].append(v)

        return {m: (sum(v) / len(v) if v else 0) for m, v in metrics.items()}

    def _agent_day_values(self, scenario: ScenarioConfig, agent, day: int) -> Dict[str, float]:
        """计算 Agent 某天各指标值"""
        values: Dict[str, float] = {}
        st = scenario.scenario_type

        satisfaction = getattr(agent, 'satisfaction', None) or getattr(agent, 'happiness', 60) / 20
        income = getattr(agent, 'income', 5000)

        if st == 'product_test':
            base_will = random.uniform(0.2, 0.5) + income / 100000
            values['购买意愿'] = min(1.0, base_will + day * 0.002)
            values['满意度'] = satisfaction + random.uniform(-0.05, 0.1)
            values['推荐率'] = max(0, min(1, (satisfaction - 3) / 2 + random.uniform(-0.1, 0.1)))
            values['复购率'] = max(0, min(1, values['购买意愿'] * 0.5 + random.uniform(-0.05, 0.05)))
        elif st == 'policy_eval':
            values['满意度'] = satisfaction + random.uniform(-0.1, 0.15)
            values['就业率'] = max(0, min(1, 0.9 + random.uniform(-0.05, 0.05)))
            values['收入变化'] = income * random.uniform(-0.02, 0.03)
            values['生活成本'] = random.uniform(3000, 8000)
        elif st == 'marketing_compare':
            values['转化率'] = random.uniform(0.05, 0.25)
            values['获客成本'] = random.uniform(10, 100)
            values['ROI'] = random.uniform(0.5, 5.0)
            values['品牌认知'] = random.uniform(0.3, 0.9)
        elif st == 'org_change':
            values['员工满意度'] = satisfaction + random.uniform(-0.15, 0.1)
            values['离职率'] = max(0, random.uniform(0.0, 0.15))
            values['工作效率'] = random.uniform(0.6, 1.2)
            values['团队协作'] = random.uniform(0.5, 1.0)
        elif st == 'discussion':
            values['观点多样性'] = random.uniform(0.5, 1.0)
            values['共识度'] = random.uniform(0.3, 0.9)
            values['讨论深度'] = random.uniform(0.4, 1.0)
        else:
            # 自定义场景：每个指标随机
            for m in scenario.metrics:
                values[m] = random.uniform(0, 5)

        return values


# ============ 测试 ============
if __name__ == "__main__":
    engine = CustomScenarioEngine()
    scenario = engine.create_scenario("product_test", name="智能手表测试", duration_days=5)
    print(f"场景: {scenario.name}, 类型: {scenario.scenario_type}")
    print(f"指标: {scenario.metrics}")

    # 模拟简单 Agent
    class FakeAgent:
        def __init__(self):
            self.happiness = random.uniform(40, 80)
            self.income = random.uniform(3000, 20000)

    agents = {i: FakeAgent() for i in range(50)}
    result = engine.run_scenario(scenario, agents)
    for metric, ev in result['success_evaluation'].items():
        print(f"  {metric}: {ev['actual']} vs {ev['target']} -> {'PASS' if ev['passed'] else 'FAIL'}")
    print("OK")
