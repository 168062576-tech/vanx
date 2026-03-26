"""
实验场景模板库 - Experiment Templates Library

开源版：3 个核心示例模板

作者：御龙军
日期：2026-03-17
版本：v2.0 (开源版)
"""

from typing import Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExperimentTemplate:
    """实验模板"""
    template_id: str
    name: str
    category: str  # education/business/policy/social/health/tech
    description: str
    duration_months: int
    agent_count: int
    key_metrics: List[str]
    setup_params: Dict
    success_criteria: Dict


class ExperimentTemplateLibrary:
    """实验模板库"""
    
    def __init__(self):
        self.templates: Dict[str, ExperimentTemplate] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """初始化所有模板（开源版只保留 3 个核心示例）"""
        
        # ========== 示例 1：经济危机 ==========
        self.add_template(ExperimentTemplate(
            template_id="crisis_001",
            name="经济危机模拟",
            category="economic",
            description="模拟经济危机爆发后的失业率增长、贫富分化变化和社会影响",
            duration_months=120,  # 10 年
            agent_count=10000,
            key_metrics=["失业率", "基尼系数", "贫困率", "平均收入下降"],
            setup_params={
                "initial_unemployment": 0.05,
                "crisis_severity": 0.3,
                "recovery_speed": 0.02,
            },
            success_criteria={"失业率": 0.10, "基尼系数": 0.45}
        ))
        
        # ========== 示例 2：流行病 ==========
        self.add_template(ExperimentTemplate(
            template_id="epidemic_001",
            name="流行病传播",
            category="health",
            description="模拟传染病传播过程，评估不同防控措施的效果",
            duration_months=24,  # 2 年
            agent_count=10000,
            key_metrics=["感染率", "死亡率", "医疗资源负荷", "经济损失"],
            setup_params={
                "r0": 2.5,
                "fatality_rate": 0.02,
                "intervention": "moderate",  # none/mask/moderate/lockdown
            },
            success_criteria={"感染率": 0.3, "死亡率": 0.01}
        ))
        
        # ========== 示例 3：人口老龄化 ==========
        self.add_template(ExperimentTemplate(
            template_id="aging_001",
            name="人口老龄化挑战",
            category="social",
            description="研究老龄化社会对养老金系统、劳动力供给和经济增长的长期影响",
            duration_months=360,  # 30 年
            agent_count=10000,
            key_metrics=["抚养比", "养老金可持续性", "劳动力增长率", "人均GDP"],
            setup_params={
                "fertility_rate": 1.5,
                "retirement_age": 65,
                "immigration_policy": "moderate",
            },
            success_criteria={"抚养比": 0.4, "养老金可持续性": 0.8}
        ))
    
    def add_template(self, template: ExperimentTemplate):
        """添加模板"""
        self.templates[template.template_id] = template
    
    def get_template(self, template_id: str) -> ExperimentTemplate:
        """获取模板"""
        return self.templates.get(template_id)
    
    def list_templates(self, category: str = None) -> List[ExperimentTemplate]:
        """列出模板"""
        if category:
            return [t for t in self.templates.values() if t.category == category]
        return list(self.templates.values())
    
    def get_statistics(self) -> Dict:
        """获取统计"""
        templates = list(self.templates.values())
        
        category_counts = {}
        for t in templates:
            category_counts[t.category] = category_counts.get(t.category, 0) + 1
        
        return {
            'total_templates': len(templates),
            'category_distribution': category_counts,
            'avg_duration_months': sum(t.duration_months for t in templates) / len(templates),
            'avg_agent_count': sum(t.agent_count for t in templates) / len(templates),
        }


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("实验模板库 v2.0 - 开源版")
    print("=" * 60)
    
    library = ExperimentTemplateLibrary()
    
    # 统计
    stats = library.get_statistics()
    print(f"\n📊 模板统计:")
    print(f"   总模板数：{stats['total_templates']}个")
    print(f"   平均时长：{stats['avg_duration_months']:.0f}个月")
    print(f"   平均规模：{stats['avg_agent_count']:.0f}个 Agent")
    
    print(f"\n📁 分类分布:")
    for category, count in stats['category_distribution'].items():
        category_names = {
            'economic': '📊 经济',
            'health': '🏥 健康',
            'social': '👥 社会',
        }
        print(f"   {category_names.get(category, category)}: {count}个")
    
    # 列出所有模板
    print(f"\n📋 模板清单:")
    for template in library.list_templates():
        print(f"   [{template.template_id}] {template.name}")
        print(f"      {template.description}")
        print(f"      {template.duration_months}个月，{template.agent_count}人，{len(template.key_metrics)}个指标")
    
    print(f"\n✅ 实验模板库 v2.0 - 开源版 加载完成!")
