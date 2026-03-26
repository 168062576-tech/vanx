# -*- coding: utf-8 -*-
"""
御龙军虚拟世界 v5 - 场景输入示例
移植自 v1.0，适配 v5 架构
功能：提供各类场景的预置配置示例，可直接用于 CustomScenarioEngine
"""

from typing import Dict, List


class ScenarioExamples:
    """场景示例库"""

    EXAMPLES: Dict[str, Dict] = {
        'smart_watch': {
            'name': '智能手表 X1 市场测试',
            'scenario_type': 'product_test',
            'description': '测试智能手表 X1 的市场接受度',
            'duration_days': 30,
            'agent_count': 100,
            'metrics': ['购买意愿', '满意度', '推荐率'],
            'success_criteria': {'购买意愿': 0.3, '满意度': 4.0},
            'features': ['长续航', 'AI助手', '健康监测', '防水'],
            'target_audience': '25-40岁职场人士',
            'price_range': 'RMB 1999-2999',
        },
        'housing_subsidy': {
            'name': '新住房补贴政策评估',
            'scenario_type': 'policy_eval',
            'description': '对新就业大学生每月 RMB 2000 住房补贴，期限 3 年，覆盖一线城市',
            'duration_days': 90,
            'agent_count': 200,
            'metrics': ['满意度', '就业率', '收入变化', '生活成本'],
            'success_criteria': {'满意度': 3.5, '就业率': 0.9},
        },
        '618_promotion': {
            'name': '618 大促营销对比',
            'scenario_type': 'marketing_compare',
            'description': '对比抖音/微信/小红书三渠道营销效果',
            'duration_days': 60,
            'agent_count': 150,
            'metrics': ['转化率', '获客成本', 'ROI'],
            'success_criteria': {'转化率': 0.15, 'ROI': 3.0},
            'channels': ['抖音广告', '微信朋友圈', '小红书KOL'],
        },
        'dept_restructure': {
            'name': '部门重组优化模拟',
            'scenario_type': 'org_change',
            'description': '合并销售部和市场部，成立数字化转型部',
            'duration_days': 60,
            'agent_count': 100,
            'metrics': ['员工满意度', '离职率', '工作效率'],
            'success_criteria': {'员工满意度': 3.5, '离职率': 0.1},
        },
        'ai_employment_discussion': {
            'name': 'AI对就业影响讨论会',
            'scenario_type': 'discussion',
            'description': '讨论人工智能对未来就业的影响',
            'duration_days': 10,
            'agent_count': 10,
            'metrics': ['观点多样性', '共识度', '讨论深度'],
            'success_criteria': {},
            'questions': [
                'AI会取代哪些工作岗位？',
                '如何适应AI时代？',
                '哪些新职业会出现？',
                '教育体系应该如何改革？',
            ],
        },
        'sharing_economy': {
            'name': '共享经济平台测试',
            'scenario_type': 'custom',
            'description': '测试共享闲置物品平台，平台收取10%服务费',
            'duration_days': 45,
            'agent_count': 200,
            'metrics': ['用户增长率', '交易量', '满意度'],
            'success_criteria': {'满意度': 4.0},
        },
    }

    @classmethod
    def get(cls, key: str) -> Dict:
        """获取示例配置"""
        return dict(cls.EXAMPLES.get(key, {}))

    @classmethod
    def list_all(cls) -> List[Dict]:
        """列出所有示例"""
        return [
            {'key': k, 'name': v['name'], 'type': v['scenario_type'],
             'description': v.get('description', '')}
            for k, v in cls.EXAMPLES.items()
        ]

    @classmethod
    def keys(cls) -> List[str]:
        return list(cls.EXAMPLES.keys())


# ============ 测试 ============
if __name__ == "__main__":
    print("场景示例库:")
    for item in ScenarioExamples.list_all():
        print(f"  {item['key']}: {item['name']} ({item['type']})")
    print(f"\n共 {len(ScenarioExamples.keys())} 个示例")
    print("OK")
