"""
核心系统集成器 - Core Systems Integrator

将婚姻家庭、经济、企业、住房四大核心系统与现有虚拟世界集成

作者：御龙军
日期：2026-03-17
版本：v1.0
"""

import random
from datetime import datetime
from typing import List, Dict, Optional

from marriage_family_system import MarriageFamilySystem
from economic_system import EconomicSystem, PersonalFinance
from corporate_system import CorporateSystem, Industry, JobLevel
from housing_system import HousingSystem, HousingType, Neighborhood


class CoreSystemsIntegrator:
    """核心系统集成器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # 初始化四大系统
        self.marriage_system = MarriageFamilySystem(config.get('marriage', {}))
        self.economic_system = EconomicSystem(config.get('economy', {}))
        self.corporate_system = CorporateSystem(config.get('corporate', {}))
        self.housing_system = HousingSystem(config.get('housing', {}))
        
        # Agent 状态追踪
        self.agent_states: Dict[int, Dict] = {}
        
        # 统计
        self.months_simulated = 0
        self.events_generated = 0
    
    def initialize_agent(self, agent: Dict):
        """初始化 Agent 的核心系统状态"""
        agent_id = agent.get('id')
        if not agent_id:
            return
        
        age = agent.get('age', 25)
        income = agent.get('income', 5000)
        gender = agent.get('gender', 'male')
        skills = agent.get('skills', {})
        
        # 1. 初始化财务
        self.economic_system.create_finance(agent_id, income, age)
        
        # 2. 初始化住房（根据年龄和收入）
        self._initialize_housing(agent_id, age, income)
        
        # 3. 初始化工作（如成年）
        if age >= 16:
            self._initialize_employment(agent_id, age, skills, income)
        
        # 4. 初始化婚姻状态（根据年龄）
        if age >= 18:
            self._initialize_marriage_status(agent_id, age, gender)
        
        self.agent_states[agent_id] = {
            'age': age,
            'gender': gender,
            'initialized': True,
            'init_date': datetime.now()
        }
    
    def _initialize_housing(self, agent_id: int, age: int, income: int):
        """初始化住房状态"""
        finance = self.economic_system.finances.get(agent_id)
        if not finance:
            return
        
        # 根据年龄和收入决定住房
        if age < 22:
            # 年轻人：租房或与家人同住
            if random.random() < 0.7:
                # 租房
                self._find_rental(agent_id, income)
            else:
                # 与家人同住（简化：标记为租房但租金低）
                self._find_rental(agent_id, income * 0.3)
        elif age < 30:
            # 青年：租房或部分买房
            if finance.savings > 50000 and random.random() < 0.3:
                self._buy_starter_home(agent_id, finance.savings * 0.8)
            else:
                self._find_rental(agent_id, income)
        else:
            # 成年：多数买房
            if finance.savings > 80000 and random.random() < 0.6:
                self._buy_home(agent_id, finance.savings * 0.5)
            else:
                self._find_rental(agent_id, income)
    
    def _find_rental(self, agent_id: int, max_rent: float):
        """寻找出租房"""
        # 创建一些出租房源
        if random.random() < 0.5:
            prop = self.housing_system.create_property(
                housing_type=random.choice([HousingType.APARTMENT, HousingType.ROOM]),
                neighborhood=random.choice([Neighborhood.URBAN, Neighborhood.SUBURB]),
                bedrooms=random.randint(1, 2),
                area_sqft=random.randint(500, 1000)
            )
            prop.is_for_rent = True
            
            if prop.rent_price_monthly <= max_rent * 1.5:
                self.housing_system.rent_property(agent_id, prop.property_id)
    
    def _buy_starter_home(self, agent_id: int, down_payment: float):
        """购买首套房"""
        prop = self.housing_system.create_property(
            housing_type=random.choice([HousingType.CONDO, HousingType.HOUSE_TOWN]),
            neighborhood=Neighborhood.SUBURB,
            bedrooms=2,
            area_sqft=random.randint(1000, 1500)
        )
        prop.is_for_sale = True
        
        if prop.market_value * 0.2 <= down_payment:
            self.housing_system.buy_property(agent_id, prop.property_id, down_payment)
    
    def _buy_home(self, agent_id: int, down_payment: float):
        """购买住房"""
        prop = self.housing_system.create_property(
            housing_type=random.choice([HousingType.HOUSE_SINGLE, HousingType.HOUSE_TOWN]),
            neighborhood=random.choice([Neighborhood.SUBURB, Neighborhood.URBAN]),
            bedrooms=random.randint(3, 4),
            area_sqft=random.randint(1500, 2500)
        )
        prop.is_for_sale = True
        
        if prop.market_value * 0.2 <= down_payment:
            self.housing_system.buy_property(agent_id, prop.property_id, down_payment)
    
    def _initialize_employment(self, agent_id: int, age: int, skills: Dict, income: int):
        """初始化就业状态"""
        # 简化：假设已有工作，记录到企业系统
        # 实际应从现有职业系统同步
        
        # 创建公司（如果没有）
        if not self.corporate_system.companies:
            self._create_sample_companies()
        
        # 随机分配到一家公司
        if self.corporate_system.companies:
            company_id = random.choice(list(self.corporate_system.companies.keys()))
            company = self.corporate_system.companies[company_id]
            
            # 找开放职位
            for pos_id, pos in company.positions.items():
                if pos.is_open:
                    self.corporate_system.hire(agent_id, company_id, pos_id, income * 12)
                    break
    
    def _create_sample_companies(self):
        """创建示例公司"""
        industries = [
            ("TechCorp", Industry.TECHNOLOGY, 500000),
            ("FinanceHub", Industry.FINANCE, 1000000),
            ("HealthCare Plus", Industry.HEALTHCARE, 800000),
            ("EduWorld", Industry.EDUCATION, 300000),
            ("RetailMart", Industry.RETAIL, 400000),
        ]
        
        for name, industry, capital in industries:
            self.corporate_system.create_company(
                name=name,
                industry=industry,
                founder_id=0,  # 系统创建
                initial_capital=capital
            )
    
    def _initialize_marriage_status(self, agent_id: int, age: int, gender: str):
        """初始化婚姻状态"""
        # 根据年龄设定婚姻概率
        marriage_prob = {
            (0, 20): 0.05,
            (21, 25): 0.20,
            (26, 30): 0.50,
            (31, 40): 0.75,
            (41, 100): 0.80,
        }
        
        prob = 0.0
        for (min_age, max_age), p in marriage_prob.items():
            if min_age <= age <= max_age:
                prob = p
                break
        
        if random.random() < prob:
            # 已婚（简化：不创建实际配偶，只标记状态）
            pass  # TODO: 创建实际关系
    
    def update_monthly(self, agents: List[Dict], months_passed: int = 1):
        """月度更新所有核心系统"""
        self.months_simulated += months_passed
        all_events = []
        
        for _ in range(months_passed):
            # 1. 更新经济系统
            self.economic_system.update_economy()
            
            for agent in agents:
                agent_id = agent.get('id')
                if not agent_id:
                    continue
                
                # 2. 更新个人财务
                finance_events = self.economic_system.update_monthly(agent_id)
                if finance_events.get('events'):
                    all_events.extend(finance_events['events'])
                
                # 3. 更新住房
                self.housing_system.update_monthly(agent_id)
                
                # 4. 更新公司
                for company in self.corporate_system.companies.values():
                    if agent_id in company.employees:
                        self.corporate_system.update_company_monthly(company.company_id)
                
                # 5. 更新婚姻/家庭
                family_events = self.marriage_system.generate_family_events(agents)
                all_events.extend(family_events)
        
        self.events_generated += len(all_events)
        
        return {
            'months_simulated': self.months_simulated,
            'events_count': len(all_events),
            'events': all_events[:100],  # 限制返回数量
            'economic_indicators': self.economic_system.indicators.__dict__,
        }
    
    def get_agent_summary(self, agent_id: int) -> Dict:
        """获取 Agent 核心系统摘要"""
        summary = {
            'agent_id': agent_id,
        }
        
        # 财务
        if agent_id in self.economic_system.finances:
            finance = self.economic_system.finances[agent_id]
            summary['finance'] = {
                'income_monthly': finance.total_monthly_income,
                'expenses_monthly': finance.total_monthly_expenses,
                'net_worth': finance.net_worth,
                'savings': finance.savings,
                'credit_score': finance.credit_score,
            }
        
        # 住房
        if agent_id in self.housing_system.residences:
            residence = self.housing_system.residences[agent_id]
            summary['housing'] = {
                'status': residence.status.value,
                'property_id': residence.property_id,
                'rent_monthly': residence.rent_monthly,
                'mortgage_balance': residence.mortgage.remaining_balance if residence.mortgage else 0,
            }
        
        # 就业
        if agent_id in self.corporate_system.employments:
            employment = self.corporate_system.employments[agent_id]
            company = self.corporate_system.companies.get(employment.company_id)
            summary['employment'] = {
                'company': company.name if company else 'Unknown',
                'salary_annual': employment.salary,
                'position_id': employment.position_id,
            }
        
        # 婚姻
        relationships = []
        for (id1, id2), rel in self.marriage_system.relationships.items():
            if agent_id in [id1, id2]:
                relationships.append({
                    'partner_id': id2 if id1 == agent_id else id1,
                    'status': rel.relationship_type,
                    'satisfaction': rel.satisfaction,
                })
        
        if relationships:
            summary['relationships'] = relationships
        
        return summary
    
    def get_system_statistics(self) -> Dict:
        """获取所有系统统计"""
        return {
            'months_simulated': self.months_simulated,
            'total_events': self.events_generated,
            'marriage': self.marriage_system.get_family_statistics(),
            'economy': self.economic_system.get_economic_statistics(),
            'corporate': self.corporate_system.get_company_statistics(),
            'housing': self.housing_system.get_housing_statistics(),
        }


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("核心系统集成器测试")
    print("=" * 60)
    
    integrator = CoreSystemsIntegrator()
    
    # 创建测试 Agent
    test_agents = [
        {'id': 1, 'age': 25, 'gender': 'male', 'income': 6000, 'skills': {'programming': 5}},
        {'id': 2, 'age': 30, 'gender': 'female', 'income': 10000, 'skills': {'finance': 7}},
        {'id': 3, 'age': 35, 'gender': 'male', 'income': 15000, 'skills': {'management': 8}},
        {'id': 4, 'age': 28, 'gender': 'female', 'income': 8000, 'skills': {'marketing': 6}},
    ]
    
    print(f"\n初始化 {len(test_agents)} 个 Agent...")
    for agent in test_agents:
        integrator.initialize_agent(agent)
        summary = integrator.get_agent_summary(agent['id'])
        print(f"  Agent {agent['id']} ({agent['age']}岁, ${agent['income']}/月):")
        if 'finance' in summary:
            print(f"    财务：净资产${summary['finance']['net_worth']:,.0f}, 信用分{summary['finance']['credit_score']:.0f}")
        if 'housing' in summary:
            print(f"    住房：{summary['housing']['status']}")
        if 'employment' in summary:
            print(f"    工作：{summary['employment']['company']} (${summary['employment']['salary_annual']:,.0f}/年)")
    
    # 模拟 12 个月
    print(f"\n模拟 12 个月...")
    for month in range(12):
        result = integrator.update_monthly(test_agents)
        
        if (month + 1) % 3 == 0:
            print(f"  第{month+1}月：生成{result['events_count']}个事件")
            print(f"    经济：GDP{result['economic_indicators']['gdp_growth_rate']*100:.1f}%, "
                  f"通胀{result['economic_indicators']['inflation_rate']*100:.1f}%, "
                  f"失业{result['economic_indicators']['unemployment_rate']*100:.1f}%")
    
    # 最终统计
    stats = integrator.get_system_statistics()
    print(f"\n系统统计:")
    print(f"  模拟月数：{stats['months_simulated']}")
    print(f"  总事件数：{stats['total_events']}")
    if stats['economy']:
        print(f"  平均收入：${stats['economy'].get('avg_income', 0):,.0f}/月")
        print(f"  平均净资产：${stats['economy'].get('avg_net_worth', 0):,.0f}")
    if stats['corporate']:
        print(f"  公司数：{stats['corporate'].get('total_companies', 0)}")
        print(f"  就业人数：{stats['corporate'].get('total_employees', 0)}")
    if stats['housing']:
        print(f"  房产数：{stats['housing'].get('total_properties', 0)}")
        print(f"  自有率：{stats['housing'].get('homeownership_rate', 0)*100:.1f}%")
    
    print("\n✅ 核心系统集成器测试完成!")
    print("\n📊 核心社会结构系统（P0）完成:")
    print("   ✅ 婚姻家庭系统")
    print("   ✅ 经济系统")
    print("   ✅ 企业系统")
    print("   ✅ 住房系统")
    print("   ✅ 集成器")
