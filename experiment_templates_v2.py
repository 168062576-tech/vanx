"""
实验场景模板库 - Experiment Templates Library

扩展版：24 个实验场景模板

作者：御龙军
日期：2026-03-17
版本：v2.0 (扩展版)
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
        """初始化所有模板"""
        
        # ========== 教育类 (4 个) ==========
        self.add_template(ExperimentTemplate(
            template_id="edu_001",
            name="教育政策验证",
            category="education",
            description="测试不同教育政策对学生升学率和就业的影响",
            duration_months=216,  # 18 年
            agent_count=5000,
            key_metrics=["升学率", "就业率", "平均收入", "教育满意度"],
            setup_params={
                "age_range": (6, 18),
                "education_policy": "baseline",  # baseline/reform/elite
                "university_capacity": 0.5,
            },
            success_criteria={"升学率": 0.7, "就业率": 0.9}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="edu_002",
            name="教育公平性研究",
            category="education",
            description="研究不同社会经济背景学生的教育机会差异",
            duration_months=144,  # 12 年
            agent_count=10000,
            key_metrics=["阶层流动性", "教育基尼系数", "奖学金覆盖率"],
            setup_params={
                "income_inequality": 0.4,  # 基尼系数
                "scholarship_coverage": 0.3,
                "affirmative_action": True,
            },
            success_criteria={"阶层流动性": 0.3}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="edu_003",
            name="在线教育影响",
            category="education",
            description="评估在线教育对传统教育的冲击和补充作用",
            duration_months=60,  # 5 年
            agent_count=3000,
            key_metrics=["在线课程注册率", "学习效果对比", "成本效益"],
            setup_params={
                "online_platform_adoption": 0.5,
                "traditional_school_quality": 0.7,
                "internet_access": 0.9,
            },
            success_criteria={"学习效果对比": 0.8}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="edu_004",
            name="终身学习社会",
            category="education",
            description="模拟终身学习文化对职业发展的影响",
            duration_months=240,  # 20 年
            agent_count=5000,
            key_metrics=["成人学习参与率", "职业转换率", "收入增长"],
            setup_params={
                "lifelong_learning_culture": 0.7,
                "employer_training_support": 0.5,
                "government_subsidy": 0.3,
            },
            success_criteria={"成人学习参与率": 0.5}
        ))
        
        # ========== 商业类 (4 个) ==========
        self.add_template(ExperimentTemplate(
            template_id="biz_001",
            name="产品上市策略",
            category="business",
            description="测试不同产品上市策略的市场表现",
            duration_months=36,  # 3 年
            agent_count=10000,
            key_metrics=["市场渗透率", "用户增长率", "客户满意度", "利润率"],
            setup_params={
                "launch_strategy": "premium",  # premium/mass/freemium
                "marketing_budget": 1000000,
                "target_segment": "early_adopters",
            },
            success_criteria={"市场渗透率": 0.15, "利润率": 0.2}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="biz_002",
            name="营销策略对比",
            category="business",
            description="对比不同营销策略的 ROI",
            duration_months=24,
            agent_count=5000,
            key_metrics=["转化率", "客户获取成本", "品牌知名度", "ROI"],
            setup_params={
                "strategy_a": "digital_marketing",
                "strategy_b": "traditional_media",
                "budget_split": 0.5,
            },
            success_criteria={"ROI": 3.0}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="biz_003",
            name="组织变革管理",
            category="business",
            description="模拟企业组织变革对员工满意度和绩效的影响",
            duration_months=18,
            agent_count=2000,  # 公司员工
            key_metrics=["员工满意度", "离职率", "生产率", "变革接受度"],
            setup_params={
                "change_type": "digital_transformation",
                "communication_quality": 0.7,
                "training_provided": True,
                "resistance_level": 0.3,
            },
            success_criteria={"员工满意度": 0.7, "离职率": 0.1}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="biz_004",
            name="创业生态系统",
            category="business",
            description="研究创业生态系统对创新和就业的影响",
            duration_months=60,
            agent_count=10000,
            key_metrics=["创业率", "初创企业存活率", "创新指数", "就业创造"],
            setup_params={
                "vc_availability": 0.5,
                "government_support": 0.6,
                "failure_tolerance": 0.7,
                "mentorship_network": 0.5,
            },
            success_criteria={"创业率": 0.05, "存活率": 0.6}
        ))
        
        # ========== 政策类 (4 个) ==========
        self.add_template(ExperimentTemplate(
            template_id="pol_001",
            name="税收政策评估",
            category="policy",
            description="评估不同税收政策对经济和社会的影响",
            duration_months=60,
            agent_count=10000,
            key_metrics=["GDP 增长", "贫富差距", "税收收入", "投资率"],
            setup_params={
                "tax_system": "progressive",  # progressive/flat/regressive
                "corporate_tax_rate": 0.25,
                "wealth_tax": 0.02,
            },
            success_criteria={"GDP 增长": 0.03, "贫富差距": 0.35}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="pol_002",
            name="全民基本收入",
            category="policy",
            description="模拟 UBI 对就业、贫困和幸福感的影响",
            duration_months=60,
            agent_count=10000,
            key_metrics=["就业率", "贫困率", "幸福感", "创业率"],
            setup_params={
                "ubi_amount": 2000,  # 每月
                "funding_source": "income_tax",
                "welfare_replacement": 0.5,
            },
            success_criteria={"贫困率": 0.05, "幸福感": 70}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="pol_003",
            name="住房政策研究",
            category="policy",
            description="研究住房政策对房价和自有率的影响",
            duration_months=120,
            agent_count=5000,
            key_metrics=["房价收入比", "住房自有率", "租房负担", "无家可归率"],
            setup_params={
                "policy_type": "affordable_housing",  # rent_control/subsidy/zoning
                "public_housing_ratio": 0.2,
                "mortgage_support": 0.3,
            },
            success_criteria={"房价收入比": 5, "自有率": 0.65}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="pol_004",
            name="医疗改革方案",
            category="policy",
            description="比较不同医疗体系的成本和效果",
            duration_months=120,
            agent_count=10000,
            key_metrics=["人均医疗支出", "预期寿命", "满意度", "等待时间"],
            setup_params={
                "system_type": "single_payer",  # single_payer/insurance/mixed
                "government_funding": 0.7,
                "private_insurance": 0.3,
            },
            success_criteria={"预期寿命": 82, "满意度": 75}
        ))
        
        # ========== 社会类 (4 个) ==========
        self.add_template(ExperimentTemplate(
            template_id="soc_001",
            name="城市化进程",
            category="social",
            description="模拟城市化对经济、环境和社会的影响",
            duration_months=240,
            agent_count=20000,
            key_metrics=["城市化率", "城乡收入差距", "通勤时间", "生活质量"],
            setup_params={
                "urban_job_growth": 0.03,
                "rural_development": 0.5,
                "migration_policy": "open",  # open/restricted/managed
            },
            success_criteria={"城市化率": 0.75, "城乡收入差距": 0.2}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="soc_002",
            name="人口老龄化",
            category="social",
            description="研究老龄化社会对经济和福利系统的挑战",
            duration_months=360,  # 30 年
            agent_count=10000,
            key_metrics=["抚养比", "养老金可持续性", "医疗支出", "劳动力供给"],
            setup_params={
                "fertility_rate": 1.5,
                "retirement_age": 65,
                "immigration_policy": "moderate",
            },
            success_criteria={"抚养比": 0.4, "养老金可持续性": 0.8}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="soc_003",
            name="社会流动性",
            category="social",
            description="研究影响社会阶层流动性的因素",
            duration_months=240,
            agent_count=10000,
            key_metrics=["代际收入弹性", "教育流动性", "职业流动性"],
            setup_params={
                "meritocracy_level": 0.7,
                "network_importance": 0.3,
                "discrimination_level": 0.1,
            },
            success_criteria={"代际收入弹性": 0.3}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="soc_004",
            name="文化融合",
            category="social",
            description="模拟多元文化社会的融合过程",
            duration_months=240,
            agent_count=10000,
            key_metrics=["文化多样性指数", "社会凝聚力", "歧视事件", "通婚率"],
            setup_params={
                "immigration_rate": 0.02,
                "integration_policy": "multicultural",  # assimilation/multicultural/segregation
                "language_support": 0.7,
            },
            success_criteria={"社会凝聚力": 70, "歧视事件": 0.05}
        ))
        
        # ========== 健康类 (4 个) ==========
        self.add_template(ExperimentTemplate(
            template_id="hlt_001",
            name="流行病传播",
            category="health",
            description="模拟传染病传播和防控措施效果",
            duration_months=24,
            agent_count=10000,
            key_metrics=["感染率", "死亡率", "医疗挤兑", "经济损失"],
            setup_params={
                "disease_type": "respiratory",  # respiratory/blood/contact
                "r0": 2.5,
                "fatality_rate": 0.02,
                "intervention": "lockdown",  # none/mask/lockdown/vaccine
            },
            success_criteria={"感染率": 0.3, "死亡率": 0.01}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="hlt_002",
            name="心理健康危机",
            category="health",
            description="研究社会压力对心理健康的影响",
            duration_months=60,
            agent_count=5000,
            key_metrics=["抑郁率", "焦虑率", "自杀率", "治疗覆盖率"],
            setup_params={
                "social_pressure": 0.7,
                "work_life_balance": 0.5,
                "mental_health_services": 0.6,
                "stigma_level": 0.3,
            },
            success_criteria={"抑郁率": 0.1, "治疗覆盖率": 0.7}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="hlt_003",
            name="健康生活方式推广",
            category="health",
            description="评估健康生活方式干预的效果",
            duration_months=60,
            agent_count=5000,
            key_metrics=["肥胖率", "运动参与率", "慢性病发病率", "医疗支出"],
            setup_params={
                "intervention_type": "education",  # education/incentive/regulation
                "healthy_food_access": 0.7,
                "exercise_facilities": 0.6,
            },
            success_criteria={"肥胖率": 0.2, "运动参与率": 0.6}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="hlt_004",
            name="医疗资源分配",
            category="health",
            description="优化医疗资源分配策略",
            duration_months=120,
            agent_count=10000,
            key_metrics=["等待时间", "治疗可及性", "健康结果", "成本效益"],
            setup_params={
                "allocation_method": "need_based",  # need_based/ability_to_pay/first_come
                "hospital_density": 0.5,
                "telemedicine_adoption": 0.6,
            },
            success_criteria={"等待时间": 30, "治疗可及性": 0.9}
        ))
        
        # ========== 科技类 (4 个) ==========
        self.add_template(ExperimentTemplate(
            template_id="tech_001",
            name="技术扩散模式",
            category="tech",
            description="研究新技术在社会中的扩散规律",
            duration_months=120,
            agent_count=10000,
            key_metrics=["采用率", "扩散速度", "创新者比例", "数字鸿沟"],
            setup_params={
                "innovation_type": "disruptive",  # incremental/disruptive/radical
                "network_effect": 0.7,
                "price_decline_rate": 0.1,
            },
            success_criteria={"采用率": 0.7, "扩散速度": 36}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="tech_002",
            name="AI 自动化影响",
            category="tech",
            description="评估 AI 自动化对就业和经济的影响",
            duration_months=120,
            agent_count=10000,
            key_metrics=["失业率", "生产率", "收入不平等", "新岗位创造"],
            setup_params={
                "automation_rate": 0.03,
                "affected_sectors": ["manufacturing", "service", "office"],
                "reskilling_program": 0.5,
                "ubi_introduction": False,
            },
            success_criteria={"失业率": 0.06, "生产率": 0.04}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="tech_003",
            name="社交媒体影响",
            category="tech",
            description="研究社交媒体对信息传播和社会舆论的影响",
            duration_months=36,
            agent_count=10000,
            key_metrics=["信息传播速度", "极化程度", "假新闻传播", "社会信任"],
            setup_params={
                "platform_penetration": 0.7,
                "algorithm_bias": 0.5,
                "fact_checking": 0.6,
                "media_literacy": 0.5,
            },
            success_criteria={"极化程度": 0.4, "社会信任": 60}
        ))
        
        self.add_template(ExperimentTemplate(
            template_id="tech_004",
            name="绿色技术转型",
            category="tech",
            description="模拟绿色技术转型的经济和环境效应",
            duration_months=240,
            agent_count=10000,
            key_metrics=["碳排放", "绿色就业", "转型成本", "能源独立性"],
            setup_params={
                "carbon_tax": 50,
                "renewable_subsidy": 0.3,
                "fossil_fuel_phaseout": 2040,
                "green_innovation": 0.7,
            },
            success_criteria={"碳排放": 0.5, "绿色就业": 0.2}
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
    print("实验模板库 v2.0 - 扩展版")
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
            'education': '📚 教育',
            'business': '💼 商业',
            'policy': '🏛️ 政策',
            'social': '👥 社会',
            'health': '🏥 健康',
            'tech': '💻 科技',
        }
        print(f"   {category_names.get(category, category)}: {count}个")
    
    # 列出所有模板
    print(f"\n📋 模板清单:")
    for template in library.list_templates():
        print(f"   [{template.template_id}] {template.name}")
        print(f"      {template.description[:50]}...")
        print(f"      {template.duration_months}个月，{template.agent_count}人，{len(template.key_metrics)}个指标")
    
    print(f"\n✅ 实验模板库 v2.0 - 24 个模板完成!")
