# -*- coding: utf-8 -*-
"""
御龙军虚拟世界 v5 - 场景应用器
移植自 v1.0，适配 v5 UnifiedAgent + DeepIntegrationEngine
功能：将自定义场景配置应用到引擎的 Agent 群体
"""

import random
from typing import Dict, List, Optional


class ScenarioApplier:
    """场景应用器（v5 适配版）

    将 ScenarioConfig 应用到 DeepIntegrationEngine 的 agents 上，
    为每个 Agent 设置场景相关属性。
    """

    def __init__(self, config: dict = None):
        self.config = config or {}

    def apply(self, agents: dict, scenario_config: dict) -> Dict:
        """将场景应用到 Agent 群体

        Args:
            agents: {agent_id: UnifiedAgent}
            scenario_config: ScenarioConfig.to_dict()

        Returns:
            {'applied_count': int, 'scenario_type': str, 'details': str}
        """
        st = scenario_config.get('scenario_type', 'custom')
        applied = 0

        for agent_id, agent in agents.items():
            if not getattr(agent, 'is_alive', True):
                continue

            if st == 'product_test':
                self._apply_product_test(agent, scenario_config)
            elif st == 'policy_eval':
                self._apply_policy_eval(agent, scenario_config)
            elif st == 'marketing_compare':
                self._apply_marketing_compare(agent, scenario_config)
            elif st == 'org_change':
                self._apply_org_change(agent, scenario_config)
            elif st == 'discussion':
                self._apply_discussion(agent, scenario_config)
            else:
                self._apply_custom(agent, scenario_config)

            applied += 1

        return {
            'applied_count': applied,
            'scenario_type': st,
            'details': f"已将 {scenario_config.get('name', '场景')} 应用到 {applied} 个 Agent",
        }

    # ------------------------------------------------------------------

    def _apply_product_test(self, agent, config: dict):
        if not hasattr(agent, 'scenario_data'):
            agent.scenario_data = {}
        agent.scenario_data['role'] = 'consumer'
        agent.scenario_data['purchase_willingness'] = 0.0
        agent.scenario_data['product_satisfaction'] = 0.0
        features = config.get('features', [])
        agent.scenario_data['preferences'] = {f: random.uniform(1, 5) for f in features}

    def _apply_policy_eval(self, agent, config: dict):
        if not hasattr(agent, 'scenario_data'):
            agent.scenario_data = {}
        agent.scenario_data['role'] = 'citizen'
        agent.scenario_data['policy_satisfaction'] = 0.0
        agent.scenario_data['employment_status'] = 'employed'

    def _apply_marketing_compare(self, agent, config: dict):
        if not hasattr(agent, 'scenario_data'):
            agent.scenario_data = {}
        channels = config.get('channels', ['渠道A', '渠道B', '渠道C'])
        agent.scenario_data['role'] = 'customer'
        agent.scenario_data['marketing_channel'] = random.choice(channels)
        agent.scenario_data['conversion_status'] = False

    def _apply_org_change(self, agent, config: dict):
        if not hasattr(agent, 'scenario_data'):
            agent.scenario_data = {}
        agent.scenario_data['role'] = 'employee'
        agent.scenario_data['job_satisfaction'] = getattr(agent, 'happiness', 60) / 20
        agent.scenario_data['turnover_risk'] = 0.0

    def _apply_discussion(self, agent, config: dict):
        if not hasattr(agent, 'scenario_data'):
            agent.scenario_data = {}
        questions = config.get('questions', ['默认讨论问题'])
        agent.scenario_data['role'] = 'discussant'
        agent.scenario_data['opinions'] = {
            q: {'stance': random.choice(['支持', '中立', '反对']), 'confidence': 0.5}
            for q in questions
        }

    def _apply_custom(self, agent, config: dict):
        if not hasattr(agent, 'scenario_data'):
            agent.scenario_data = {}
        agent.scenario_data['role'] = 'participant'


# ============ 测试 ============
if __name__ == "__main__":
    applier = ScenarioApplier()
    print("场景应用器 v5 已加载")
    print("调用方式: applier.apply(agents, scenario_config)")
    print("OK")
