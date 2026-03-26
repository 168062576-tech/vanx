"""
政府政策系统 - Government & Policy System

模拟真实的政府治理和社会管理：
- 法律体系/犯罪/司法
- 社会福利/救济/补贴
- 劳动法规/最低工资
- 公共服务/基础设施
- 政策影响评估

作者：御龙军
日期：2026-03-17
版本：v1.0
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class CrimeType(Enum):
    """犯罪类型"""
    THEFT = "theft"  # 盗窃
    ASSAULT = "assault"  # 袭击
    FRAUD = "fraud"  # 诈骗
    DRUG_OFFENSE = "drug_offense"  # 毒品
    VIOLENT_CRIME = "violent_crime"  # 暴力犯罪
    WHITE_COLLAR = "white_collar"  # 白领犯罪
    DUI = "dui"  # 酒驾
    VANDALISM = "vandalism"  # 破坏公物
    TRESPASSING = "trespassing"  # 非法入侵
    NONE = "none"  # 无犯罪


class WelfareType(Enum):
    """福利类型"""
    UNEMPLOYMENT = "unemployment"  # 失业救济
    FOOD_STAMPS = "food_stamps"  # 食品券
    HOUSING_ASSISTANCE = "housing_assistance"  # 住房补贴
    MEDICAID = "medicaid"  # 医疗补助
    PENSION = "pension"  # 养老金
    DISABILITY = "disability"  # 残疾补助
    CHILD_CARE = "child_care"  # 儿童保育
    EDUCATION_GRANT = "education_grant"  # 教育补助


@dataclass
class Law:
    """法律"""
    law_id: str
    name: str
    category: str  # criminal/civil/labor/tax/etc
    description: str
    penalty: float = 0.0  # 罚款金额
    prison_term_months: int = 0  # 刑期（月）
    effective_date: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class WelfareProgram:
    """福利项目"""
    program_id: str
    name: str
    type: WelfareType
    eligibility_criteria: Dict  # 资格条件
    benefit_amount: float  # 福利金额
    duration_months: int  # 持续时间
    recipients: List[int] = field(default_factory=list)  # 受益人 IDs


@dataclass
class CriminalRecord:
    """犯罪记录"""
    agent_id: int
    crime_type: CrimeType
    crime_date: datetime
    caught: bool = False
    conviction_date: Optional[datetime] = None
    sentence_months: int = 0
    served_months: int = 0
    fine_paid: float = 0.0
    is_in_prison: bool = False


class GovernmentSystem:
    """政府政策系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.laws: Dict[str, Law] = {}
        self.welfare_programs: Dict[str, WelfareProgram] = {}
        self.criminal_records: Dict[int, List[CriminalRecord]] = {}
        
        # 政府参数
        self.tax_revenue = 0.0
        self.government_spending = 0.0
        self.budget_deficit = 0.0
        
        # 犯罪统计
        self.crime_rate = 0.05  # 5% 年犯罪率
        self.clearance_rate = 0.6  # 60% 破案率
        self.prison_population = 0
        
        # 社会福利参数
        self.unemployment_benefit_rate = 0.6  # 60% 原工资
        self.min_wage = 15.0  # 最低时薪
        self.max_work_hours_weekly = 40  # 最长工作时长
        self.overtime_multiplier = 1.5  # 加班系数
        
        # 初始化默认法律和福利
        self._setup_default_laws()
        self._setup_default_welfare()
    
    def _setup_default_laws(self):
        """设置默认法律"""
        default_laws = [
            Law("criminal_theft", "盗窃罪", "criminal", "非法占有他人财物", 5000, 12),
            Law("criminal_assault", "袭击罪", "criminal", "人身攻击", 10000, 24),
            Law("criminal_fraud", "诈骗罪", "criminal", "欺诈行为", 20000, 36),
            Law("criminal_drug", "毒品罪", "criminal", "持有/贩卖毒品", 15000, 48),
            Law("criminal_violent", "暴力犯罪", "criminal", "严重暴力行为", 50000, 120),
            Law("labor_minwage", "最低工资法", "labor", "保障最低工资", 0, 0),
            Law("labor_maxhours", "工时法", "labor", "限制最长工时", 0, 0),
            Law("tax_income", "所得税法", "tax", "征收个人所得税", 0, 0),
        ]
        
        for law in default_laws:
            self.laws[law.law_id] = law
    
    def _setup_default_welfare(self):
        """设置默认福利项目"""
        welfare_programs = [
            WelfareProgram("unemployment", "失业保险", WelfareType.UNEMPLOYMENT,
                          {'min_work_months': 6, 'max_income': 3000}, 2000, 6),
            WelfareProgram("food_stamps", "食品券", WelfareType.FOOD_STAMPS,
                          {'max_income': 2000, 'has_children': None}, 500, 12),
            WelfareProgram("housing", "住房补贴", WelfareType.HOUSING_ASSISTANCE,
                          {'max_income': 2500, 'rent_burden': 0.3}, 1000, 12),
            WelfareProgram("medicaid", "医疗补助", WelfareType.MEDICAID,
                          {'max_income': 1500, 'disabled': None}, 800, 12),
            WelfareProgram("pension", "养老金", WelfareType.PENSION,
                          {'min_age': 65, 'min_work_years': 10}, 3000, 9999),
            WelfareProgram("disability", "残疾补助", WelfareType.DISABILITY,
                          {'disabled': True, 'max_income': 2000}, 2500, 9999),
        ]
        
        for program in welfare_programs:
            self.welfare_programs[program.program_id] = program
    
    def check_crime(self, agent_id: int, agent_income: float, 
                   economic_conditions: Dict) -> Optional[CriminalRecord]:
        """检查犯罪行为"""
        # 犯罪概率基于经济状况
        base_crime_rate = self.crime_rate
        
        # 失业/低收入增加犯罪概率
        if economic_conditions.get('unemployed', False):
            base_crime_rate *= 3
        if agent_income < 2000:
            base_crime_rate *= 2
        
        # 执法力度影响
        enforcement = economic_conditions.get('law_enforcement', 1.0)
        base_crime_rate /= enforcement
        
        if random.random() < base_crime_rate / 12:  # 月犯罪率
            # 随机选择犯罪类型
            crime_types = list(CrimeType)
            crime_types.remove(CrimeType.NONE)
            
            # 低收入更可能财产犯罪
            if agent_income < 2000:
                crime_type = random.choice([CrimeType.THEFT, CrimeType.FRAUD, CrimeType.DRUG_OFFENSE])
            else:
                crime_type = random.choice([CrimeType.WHITE_COLLAR, CrimeType.FRAUD, CrimeType.DUI])
            
            record = CriminalRecord(
                agent_id=agent_id,
                crime_type=crime_type,
                crime_date=datetime.now()
            )
            
            # 破案概率
            if random.random() < self.clearance_rate:
                record.caught = True
                record.conviction_date = datetime.now()
                
                # 判刑
                law = self._get_law_for_crime(crime_type)
                if law:
                    record.sentence_months = law.prison_term_months
                    record.fine_paid = law.penalty
                    
                    if record.sentence_months > 0:
                        record.is_in_prison = True
                        self.prison_population += 1
            
            # 存储记录
            if agent_id not in self.criminal_records:
                self.criminal_records[agent_id] = []
            self.criminal_records[agent_id].append(record)
            
            return record
        
        return None
    
    def _get_law_for_crime(self, crime_type: CrimeType) -> Optional[Law]:
        """根据犯罪类型获取对应法律"""
        crime_law_map = {
            CrimeType.THEFT: "criminal_theft",
            CrimeType.ASSAULT: "criminal_assault",
            CrimeType.FRAUD: "criminal_fraud",
            CrimeType.DRUG_OFFENSE: "criminal_drug",
            CrimeType.VIOLENT_CRIME: "criminal_violent",
        }
        
        law_id = crime_law_map.get(crime_type)
        return self.laws.get(law_id) if law_id else None
    
    def check_welfare_eligibility(self, agent_id: int, agent_data: Dict) -> List[str]:
        """检查福利资格"""
        eligible_programs = []
        
        for program_id, program in self.welfare_programs.items():
            if agent_id in program.recipients:
                continue  # 已在受益
            
            criteria = program.eligibility_criteria
            eligible = True
            
            # 检查收入
            if 'max_income' in criteria:
                if agent_data.get('income', 9999) > criteria['max_income']:
                    eligible = False
            
            # 检查年龄
            if 'min_age' in criteria:
                if agent_data.get('age', 0) < criteria['min_age']:
                    eligible = False
            
            # 检查工作历史
            if 'min_work_months' in criteria:
                if agent_data.get('work_months', 0) < criteria['min_work_months']:
                    eligible = False
            
            # 检查残疾状态
            if criteria.get('disabled') is True:
                if not agent_data.get('disabled', False):
                    eligible = False
            
            if eligible:
                eligible_programs.append(program_id)
                program.recipients.append(agent_id)
        
        return eligible_programs
    
    def collect_taxes(self, agents: List[Dict]) -> float:
        """征收税收"""
        total_tax = 0
        
        for agent in agents:
            income = agent.get('income', 0) * 12  # 年收入
            
            # 累进税制
            if income < 10000:
                tax = income * 0.10
            elif income < 40000:
                tax = 1000 + (income - 10000) * 0.12
            elif income < 85000:
                tax = 4600 + (income - 40000) * 0.22
            elif income < 160000:
                tax = 14500 + (income - 85000) * 0.24
            else:
                tax = 32500 + (income - 160000) * 0.32
            
            total_tax += tax / 12  # 月税收
        
        self.tax_revenue = total_tax
        return total_tax
    
    def distribute_benefits(self) -> float:
        """发放福利"""
        total_benefits = 0
        
        for program in self.welfare_programs.values():
            benefit_per_person = program.benefit_amount
            total_benefits += benefit_per_person * len(program.recipients)
        
        self.government_spending = total_benefits
        self.budget_deficit = self.government_spending - self.tax_revenue
        
        return total_benefits
    
    def update_monthly(self, agents: List[Dict], economic_conditions: Dict) -> Dict:
        """月度更新"""
        events = []
        
        # 1. 征税
        tax_revenue = self.collect_taxes(agents)
        
        # 2. 检查犯罪
        for agent in agents:
            if agent.get('in_prison', False):
                continue  # 已在监狱
            
            crime_record = self.check_crime(
                agent['id'],
                agent.get('income', 0),
                economic_conditions
            )
            
            if crime_record and crime_record.caught:
                events.append({
                    'type': 'crime_caught',
                    'agent_id': agent['id'],
                    'crime': crime_record.crime_type.value,
                    'sentence_months': crime_record.sentence_months
                })
                
                # 更新 Agent 状态
                if crime_record.is_in_prison:
                    agent['in_prison'] = True
                    from datetime import timedelta
                    agent['prison_release_date'] = datetime.now() + timedelta(days=crime_record.sentence_months * 30)
        
        # 3. 检查福利资格
        for agent in agents:
            eligible = self.check_welfare_eligibility(agent['id'], agent)
            for program_id in eligible:
                events.append({
                    'type': 'welfare_enrolled',
                    'agent_id': agent['id'],
                    'program': program_id
                })
        
        # 4. 发放福利
        benefits = self.distribute_benefits()
        
        # 5. 服刑人员释放检查
        self._process_prison_releases(agents)
        
        return {
            'tax_revenue': tax_revenue,
            'benefits_paid': benefits,
            'budget_deficit': self.budget_deficit,
            'prison_population': self.prison_population,
            'events': events,
        }
    
    def _process_prison_releases(self, agents: List[Dict]):
        """处理监狱释放"""
        now = datetime.now()
        
        for agent in agents:
            if not agent.get('in_prison', False):
                continue
            
            release_date = agent.get('prison_release_date')
            if release_date and now >= release_date:
                agent['in_prison'] = False
                agent['criminal_record'] = True
                self.prison_population -= 1
    
    def get_government_statistics(self) -> Dict:
        """获取政府统计"""
        total_recipients = sum(len(p.recipients) for p in self.welfare_programs.values())
        
        total_crimes = sum(len(records) for records in self.criminal_records.values())
        
        return {
            'tax_revenue_monthly': self.tax_revenue,
            'spending_monthly': self.government_spending,
            'budget_deficit': self.budget_deficit,
            'welfare_recipients': total_recipients,
            'welfare_programs_active': len([p for p in self.welfare_programs.values() if p.recipients]),
            'prison_population': self.prison_population,
            'total_crimes_recorded': total_crimes,
            'crime_rate': self.crime_rate,
            'clearance_rate': self.clearance_rate,
            'min_wage': self.min_wage,
            'laws_active': len([l for l in self.laws.values() if l.is_active]),
        }


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("政府政策系统测试")
    print("=" * 60)
    
    system = GovernmentSystem()
    
    # 创建测试 Agent
    test_agents = [
        {'id': 1, 'income': 5000, 'age': 30, 'work_months': 60},
        {'id': 2, 'income': 1500, 'age': 45, 'work_months': 120, 'unemployed': True},
        {'id': 3, 'income': 800, 'age': 25, 'work_months': 12},
        {'id': 4, 'income': 12000, 'age': 50, 'work_months': 300},
        {'id': 5, 'income': 2000, 'age': 67, 'work_months': 480},
    ]
    
    print(f"\n福利资格检查:")
    for agent in test_agents:
        eligible = system.check_welfare_eligibility(agent['id'], agent)
        if eligible:
            print(f"  Agent {agent['id']} (${agent['income']}/月) 符合：{eligible}")
    
    # 模拟 12 个月
    print(f"\n模拟 12 个月...")
    economic_conditions = {
        'unemployment_rate': 0.06,
        'law_enforcement': 1.0,
    }
    
    total_tax = 0
    total_benefits = 0
    crimes = 0
    
    for month in range(12):
        result = system.update_monthly(test_agents, economic_conditions)
        total_tax += result['tax_revenue']
        total_benefits += result['benefits_paid']
        crimes += len([e for e in result['events'] if e['type'] == 'crime_caught'])
        
        if (month + 1) % 3 == 0:
            print(f"  第{month+1}月：税收${result['tax_revenue']:,.0f}, "
                  f"福利${result['benefits_paid']:,.0f}, "
                  f"犯罪{len([e for e in result['events'] if e['type'] == 'crime_caught'])}起")
    
    # 统计
    stats = system.get_government_statistics()
    print(f"\n政府统计:")
    print(f"  总税收：${total_tax:,.0f}")
    print(f"  总福利：${total_benefits:,.0f}")
    print(f"  财政赤字：${stats['budget_deficit']:,.0f}")
    print(f"  福利受益人：{stats['welfare_recipients']}人")
    print(f"  监狱人口：{stats['prison_population']}人")
    print(f"  犯罪记录：{stats['total_crimes_recorded']}起")
    print(f"  最低工资：${stats['min_wage']}/小时")
    
    print("\n✅ 政府政策系统测试完成!")
