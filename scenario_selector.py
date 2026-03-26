# -*- coding: utf-8 -*-
"""
御龙军虚拟世界 v5 - 场景选择器
移植自 v1.0，适配 v5 架构
功能：在主世界/实验世界基础上选择并配置场景（纯 API，无 input() 交互）
"""

from typing import Dict, List, Optional


class WorldTemplate:
    """世界模板"""

    TEMPLATES = {
        'alpha': {'name': 'world_alpha', 'time_scale': 0.00001157, 'desc': '主世界（真实时间）'},
        'beta':  {'name': 'world_beta',  'time_scale': 1.0,        'desc': '实验世界（1秒=1天）'},
        'gamma': {'name': 'world_gamma', 'time_scale': 10.0,       'desc': '实验世界（1秒=10天）'},
        'delta': {'name': 'world_delta', 'time_scale': 60.0,       'desc': '实验世界（1秒=60天）'},
    }

    @classmethod
    def get(cls, key: str) -> Dict:
        return cls.TEMPLATES.get(key, cls.TEMPLATES['beta'])

    @classmethod
    def list_all(cls) -> List[Dict]:
        return [{'key': k, **v} for k, v in cls.TEMPLATES.items()]


class ScenarioTemplate:
    """场景模板"""

    TEMPLATES = {
        'product_test':       {'name': '产品市场测试', 'desc': '新产品上市验证'},
        'policy_eval':        {'name': '政策效果评估', 'desc': '政策实施影响分析'},
        'marketing_compare':  {'name': '营销策略对比', 'desc': '多渠道营销效果对比'},
        'org_change':         {'name': '组织变革模拟', 'desc': '公司重组影响评估'},
        'custom':             {'name': '自定义场景',   'desc': '用户自定义需求'},
        'discussion':         {'name': 'Agent讨论会',  'desc': '虚拟 Agent 讨论问题'},
    }

    @classmethod
    def get(cls, key: str) -> Dict:
        return cls.TEMPLATES.get(key, cls.TEMPLATES['custom'])

    @classmethod
    def list_all(cls) -> List[Dict]:
        return [{'key': k, **v} for k, v in cls.TEMPLATES.items()]


class ScenarioSelector:
    """场景选择器（v5 适配版）

    纯 API 模式，不依赖 input()。
    """

    def __init__(self, config: dict = None):
        self.config = config or {}

    def select(self, world_key: str = "beta", scenario_key: str = "custom",
               **overrides) -> Dict:
        """选择世界 + 场景组合

        Args:
            world_key: alpha / beta / gamma / delta
            scenario_key: product_test / policy_eval / marketing_compare / org_change / custom / discussion
            **overrides: 额外覆盖参数（name, duration_days, metrics 等）

        Returns:
            {
              'world': {...},
              'scenario': {...},
              'ready': True,
            }
        """
        world = WorldTemplate.get(world_key)
        scenario = ScenarioTemplate.get(scenario_key)

        # 合并 overrides
        merged = {**scenario, 'scenario_type': scenario_key, **overrides}

        return {
            'world': world,
            'scenario': merged,
            'ready': True,
        }

    def list_worlds(self) -> List[Dict]:
        return WorldTemplate.list_all()

    def list_scenarios(self) -> List[Dict]:
        return ScenarioTemplate.list_all()


# ============ 测试 ============
if __name__ == "__main__":
    selector = ScenarioSelector()

    print("可用世界:")
    for w in selector.list_worlds():
        print(f"  {w['key']}: {w['desc']}")

    print("\n可用场景:")
    for s in selector.list_scenarios():
        print(f"  {s['key']}: {s['name']} - {s['desc']}")

    selection = selector.select("beta", "product_test", name="智能手表测试")
    print(f"\n选择: {selection['world']['desc']} + {selection['scenario']['name']}")
    print("OK")
