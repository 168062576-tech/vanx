"""
实验场景模板库 - Experiment Templates Library

开源版：3 个核心示例模板 + 21 个专业版模板（锁定）

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
    locked: bool = False  # 是否锁定（开源版不可用）
    lock_reason: str = ""  # 锁定原因


class ExperimentTemplateLibrary:
    """实验模板库"""
    
    def __init__(self):
        self.templates: Dict[str, ExperimentTemplate] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """初始化所有模板（3 个免费 + 21 个锁定 = 24 个）"""
        
        # ========== 免费模板（3 个）==========
        # 1. 经济危机
        self.add_template(ExperimentTemplate(
            template_id="crisis_001",
            name="经济危机模拟",
            category="economic",
            description="模拟经济危机爆发后的失业率增长、贫富分化变化和社会影响",
            duration_months=120,
            agent_count=10000,
            key_metrics=["失业率", "基尼系数", "贫困率", "平均收入下降"],
            setup_params={"initial_unemployment": 0.05, "crisis_severity": 0.3, "recovery_speed": 0.02},
            success_criteria={"失业率": 0.10, "基尼系数": 0.45}
        ))
        
        # 2. 流行病
        self.add_template(ExperimentTemplate(
            template_id="epidemic_001",
            name="流行病传播",
            category="health",
            description="模拟传染病传播过程，评估不同防控措施的效果",
            duration_months=24,
            agent_count=10000,
            key_metrics=["感染率", "死亡率", "医疗资源负荷", "经济损失"],
            setup_params={"r0": 2.5, "fatality_rate": 0.02, "intervention": "moderate"},
            success_criteria={"感染率": 0.3, "死亡率": 0.01}
        ))
        
        # 3. 人口老龄化
        self.add_template(ExperimentTemplate(
            template_id="aging_001",
            name="人口老龄化挑战",
            category="social",
            description="研究老龄化社会对养老金系统、劳动力供给和经济增长的长期影响",
            duration_months=360,
            agent_count=10000,
            key_metrics=["抚养比", "养老金可持续性", "劳动力增长率", "人均 GDP"],
            setup_params={"fertility_rate": 1.5, "retirement_age": 65, "immigration_policy": "moderate"},
            success_criteria={"抚养比": 0.4, "养老金可持续性": 0.8}
        ))
        
        # ========== 锁定模板（21 个）==========
        # 教育类 (4 个)
        self.add_template(ExperimentTemplate(template_id="edu_001", name="教育资源分配改革", category="education", description="模拟不同教育政策对教育公平性和质量的影响", duration_months=240, agent_count=10000, key_metrics=["平均受教育年限", "教育基尼系数", "升学率"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="edu_002", name="高等教育扩招效应", category="education", description="研究大学扩招对就业市场和社会流动性的影响", duration_months=300, agent_count=10000, key_metrics=["大学入学率", "学历溢价", "失业率"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="edu_003", name="职业教育发展", category="education", description="职业教育投入对技能匹配和就业的影响", duration_months=180, agent_count=10000, key_metrics=["技能培训率", "技能匹配度", "工资增长"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="edu_004", name="在线教育普及", category="education", description="在线教育对传统教育和学习成果的影响", duration_months=120, agent_count=10000, key_metrics=["在线学习率", "学习效果", "教育成本"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        
        # 商业类 (4 个)
        self.add_template(ExperimentTemplate(template_id="biz_001", name="市场竞争政策", category="business", description="反垄断政策对市场竞争和创新的影响", duration_months=180, agent_count=10000, key_metrics=["市场集中度", "创新投入", "消费者福利"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="biz_002", name="创业扶持政策", category="business", description="创业补贴和税收优惠对创业率的影响", duration_months=120, agent_count=10000, key_metrics=["创业率", "企业存活率", "就业增长"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="biz_003", name="数字化转型", category="business", description="企业数字化对生产率和就业结构的影响", duration_months=180, agent_count=10000, key_metrics=["数字化率", "生产率", "技能需求变化"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="biz_004", name="全球化贸易", category="business", description="贸易自由化对国内产业和就业的影响", duration_months=240, agent_count=10000, key_metrics=["贸易额", "产业竞争力", "工资水平"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        
        # 政策类 (4 个)
        self.add_template(ExperimentTemplate(template_id="pol_001", name="税收制度改革", category="policy", description="累进税制对收入分配和经济活力的影响", duration_months=240, agent_count=10000, key_metrics=["基尼系数", "税收收入", "投资率"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="pol_002", name="社会保障体系", category="policy", description="福利政策对贫困率和工作激励的影响", duration_months=300, agent_count=10000, key_metrics=["贫困率", "劳动参与率", "财政支出"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="pol_003", name="住房政策改革", category="policy", description="保障房和限购政策对房价和居住质量的影响", duration_months=180, agent_count=10000, key_metrics=["房价收入比", "住房自有率", "居住满意度"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="pol_004", name="移民政策", category="policy", description="移民政策对劳动力市场和文化多样性的影响", duration_months=360, agent_count=10000, key_metrics=["移民比例", "工资水平", "文化多样性"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        
        # 社会类 (3 个，不含 aging_001)
        self.add_template(ExperimentTemplate(template_id="soc_002", name="性别平等政策", category="social", description="性别平等政策对就业和收入差距的影响", duration_months=240, agent_count=10000, key_metrics=["性别工资差距", "女性就业率", "管理层比例"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="soc_003", name="代际流动性", category="social", description="社会流动性对机会公平和经济增长的影响", duration_months=480, agent_count=10000, key_metrics=["代际收入弹性", "教育流动性", "职业流动性"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="soc_004", name="城乡一体化发展", category="social", description="城乡融合政策对人口流动和经济发展的影响", duration_months=360, agent_count=10000, key_metrics=["城镇化率", "城乡收入比", "人口流动率"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        
        # 健康类 (3 个，不含 epidemic_001)
        self.add_template(ExperimentTemplate(template_id="hlt_002", name="医疗资源分配", category="health", description="医疗资源分布对健康公平和效率的影响", duration_months=180, agent_count=10000, key_metrics=["医疗可及性", "健康差异", "医疗支出"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="hlt_003", name="慢性病管理", category="health", description="慢性病预防和管理体系对健康和经济的影响", duration_months=300, agent_count=10000, key_metrics=["慢性病发病率", "医疗负担", "预期寿命"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="hlt_004", name="心理健康促进", category="health", description="心理健康政策对社会福祉和医疗负担的影响", duration_months=240, agent_count=10000, key_metrics=["抑郁发病率", "心理咨询率", "社会幸福感"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        
        # 科技类 (3 个)
        self.add_template(ExperimentTemplate(template_id="tech_001", name="人工智能替代", category="tech", description="AI 自动化对就业结构和收入分配的影响", duration_months=240, agent_count=10000, key_metrics=["自动化率", "失业率", "工资极化"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="tech_002", name="科技创新政策", category="tech", description="研发投入和专利政策对创新和经济的影响", duration_months=300, agent_count=10000, key_metrics=["研发投入", "专利数量", "生产率增长"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
        self.add_template(ExperimentTemplate(template_id="tech_003", name="数字经济崛起", category="tech", description="数字平台经济对传统行业和就业的影响", duration_months=180, agent_count=10000, key_metrics=["数字化率", "平台就业", "行业集中度"], setup_params={}, success_criteria={}, locked=True, lock_reason="专业版功能"))
    
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
    stats = library.get_statistics()
    print(f"\n📊 模板统计:")
    print(f"   总模板数：{stats['total_templates']}个")
    print(f"   平均时长：{stats['avg_duration_months']:.0f}个月")
    print(f"   平均规模：{stats['avg_agent_count']:.0f}个 Agent")
    
    print(f"\n📁 分类分布:")
    for category, count in stats['category_distribution'].items():
        print(f"   {category}: {count}个")
    
    locked = sum(1 for t in library.list_templates() if t.locked)
    unlocked = sum(1 for t in library.list_templates() if not t.locked)
    print(f"\n🔓 免费：{unlocked}个 | 🔒 锁定：{locked}个")
    
    print("\n✅ 加载完成!")
