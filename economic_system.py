"""
经济系统 - Economic System

模拟真实的宏观经济和微观经济行为：
- 个人财务（收入/支出/储蓄/投资/贷款）
- 消费行为（必需品/奢侈品/品牌偏好）
- 税收系统（累进税/财产税/消费税）
- 通货膨胀/利率/经济周期
- 银行系统（存款/贷款/信用卡）

作者：御龙军
日期：2026-03-17
版本：v1.0
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class ExpenseCategory(Enum):
    """支出类别"""
    HOUSING = "housing"  # 住房
    FOOD = "food"  # 食品
    TRANSPORTATION = "transportation"  # 交通
    UTILITIES = "utilities"  # 水电煤
    HEALTHCARE = "healthcare"  # 医疗
    EDUCATION = "education"  # 教育
    ENTERTAINMENT = "entertainment"  # 娱乐
    SHOPPING = "shopping"  # 购物
    INSURANCE = "insurance"  # 保险
    SAVINGS = "savings"  # 储蓄
    INVESTMENT = "investment"  # 投资
    TAXES = "taxes"  # 税收
    OTHER = "other"  # 其他


class InvestmentType(Enum):
    """投资类型"""
    SAVINGS_ACCOUNT = "savings"  # 储蓄账户
    STOCKS = "stocks"  # 股票
    BONDS = "bonds"  # 债券
    REAL_ESTATE = "real_estate"  # 房地产
    CRYPTO = "crypto"  # 加密货币
    MUTUAL_FUNDS = "mutual_funds"  # 基金
    BUSINESS = "business"  # 创业


@dataclass
class PersonalFinance:
    """个人财务"""
    agent_id: int
    
    # 收入
    monthly_income: float = 0.0  # 月收入
    passive_income: float = 0.0  # 被动收入
    other_income: float = 0.0  # 其他收入
    
    # 资产
    cash: float = 0.0  # 现金
    savings: float = 0.0  # 储蓄
    investments: Dict[str, float] = field(default_factory=dict)  # 投资
    real_estate: float = 0.0  # 房产价值
    vehicles: float = 0.0  # 车辆价值
    other_assets: float = 0.0  # 其他资产
    
    # 负债
    mortgage: float = 0.0  # 房贷
    car_loan: float = 0.0  # 车贷
    student_loan: float = 0.0  # 学生贷款
    credit_card_debt: float = 0.0  # 信用卡债务
    personal_loan: float = 0.0  # 个人贷款
    
    # 支出（月度）
    monthly_expenses: Dict[str, float] = field(default_factory=dict)
    
    # 信用评分
    credit_score: float = 650.0  # 300-850
    
    # 财务行为
    savings_rate: float = 0.1  # 储蓄率 0-1
    risk_tolerance: float = 0.5  # 风险承受 0-1
    spending_habit: str = "moderate"  # frugal/moderate/extravagant
    
    @property
    def total_assets(self) -> float:
        """总资产"""
        return (
            self.cash +
            self.savings +
            sum(self.investments.values()) +
            self.real_estate +
            self.vehicles +
            self.other_assets
        )
    
    @property
    def total_liabilities(self) -> float:
        """总负债"""
        return (
            self.mortgage +
            self.car_loan +
            self.student_loan +
            self.credit_card_debt +
            self.personal_loan
        )
    
    @property
    def net_worth(self) -> float:
        """净资产"""
        return self.total_assets - self.total_liabilities
    
    @property
    def total_monthly_income(self) -> float:
        """月总收入"""
        return self.monthly_income + self.passive_income + self.other_income
    
    @property
    def total_monthly_expenses(self) -> float:
        """月总支出"""
        return sum(self.monthly_expenses.values())
    
    @property
    def monthly_cash_flow(self) -> float:
        """月现金流"""
        return self.total_monthly_income - self.total_monthly_expenses
    
    @property
    def debt_to_income_ratio(self) -> float:
        """债务收入比"""
        if self.total_monthly_income == 0:
            return 0
        return self.total_liabilities / (self.total_monthly_income * 12)
    
    @property
    def savings_rate_actual(self) -> float:
        """实际储蓄率"""
        if self.total_monthly_income == 0:
            return 0
        return self.monthly_cash_flow / self.total_monthly_income


@dataclass
class EconomicIndicators:
    """经济指标"""
    # 宏观经济
    gdp_growth_rate: float = 0.025  # GDP 增长率 2.5%
    unemployment_rate: float = 0.05  # 失业率 5%
    inflation_rate: float = 0.02  # 通胀率 2%
    interest_rate: float = 0.03  # 利率 3%
    
    # 市场
    stock_market_index: float = 1000.0  # 股票市场指数
    housing_price_index: float = 100.0  # 房价指数
    consumer_confidence: float = 100.0  # 消费者信心
    
    # 税收
    tax_brackets: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.tax_brackets:
            # 美国式累进税制（简化）
            self.tax_brackets = [
                {'min': 0, 'max': 10000, 'rate': 0.10},
                {'min': 10000, 'max': 40000, 'rate': 0.12},
                {'min': 40000, 'max': 85000, 'rate': 0.22},
                {'min': 85000, 'max': 160000, 'rate': 0.24},
                {'min': 160000, 'max': 200000, 'rate': 0.32},
                {'min': 200000, 'max': 500000, 'rate': 0.35},
                {'min': 500000, 'max': float('inf'), 'rate': 0.37},
            ]


class EconomicSystem:
    """经济系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.finances: Dict[int, PersonalFinance] = {}
        self.indicators = EconomicIndicators()
        
        # 经济周期参数
        self.economic_phase = "expansion"  # expansion/peak/contraction/trough
        self.cycle_months = 0
        self.cycle_length_months = random.randint(60, 120)  # 5-10 年周期
        
        # 价格水平
        self.price_level = 1.0
        self.base_prices = {
            ExpenseCategory.HOUSING: 1500,
            ExpenseCategory.FOOD: 400,
            ExpenseCategory.TRANSPORTATION: 300,
            ExpenseCategory.UTILITIES: 150,
            ExpenseCategory.HEALTHCARE: 300,
            ExpenseCategory.EDUCATION: 200,
            ExpenseCategory.ENTERTAINMENT: 200,
            ExpenseCategory.SHOPPING: 300,
            ExpenseCategory.INSURANCE: 200,
            ExpenseCategory.OTHER: 100,
        }
    
    def create_finance(self, agent_id: int, income: float, age: int) -> PersonalFinance:
        """为 Agent 创建财务档案"""
        finance = PersonalFinance(agent_id=agent_id)
        finance.monthly_income = income
        
        # 根据年龄设置初始资产
        if age < 25:
            finance.cash = random.uniform(500, 5000)
            finance.student_loan = random.uniform(10000, 50000)
        elif age < 35:
            finance.cash = random.uniform(2000, 20000)
            finance.savings = random.uniform(5000, 50000)
            finance.mortgage = random.uniform(100000, 300000)
        elif age < 50:
            finance.cash = random.uniform(5000, 50000)
            finance.savings = random.uniform(20000, 200000)
            finance.investments = {'stocks': random.uniform(10000, 100000)}
            finance.real_estate = random.uniform(200000, 500000)
        else:
            finance.cash = random.uniform(10000, 100000)
            finance.savings = random.uniform(50000, 500000)
            finance.investments = {
                'stocks': random.uniform(50000, 300000),
                'bonds': random.uniform(20000, 100000)
            }
            finance.real_estate = random.uniform(300000, 1000000)
        
        # 设置支出
        self._calculate_expenses(finance, age)
        
        self.finances[agent_id] = finance
        return finance
    
    def _calculate_expenses(self, finance: PersonalFinance, age: int):
        """计算月度支出"""
        income = finance.monthly_income
        
        # 基础支出（占收入比例）
        expense_ratios = {
            ExpenseCategory.HOUSING: 0.30,
            ExpenseCategory.FOOD: 0.12,
            ExpenseCategory.TRANSPORTATION: 0.10,
            ExpenseCategory.UTILITIES: 0.05,
            ExpenseCategory.HEALTHCARE: 0.08,
            ExpenseCategory.EDUCATION: 0.05 if age < 30 else 0.02,
            ExpenseCategory.ENTERTAINMENT: 0.05,
            ExpenseCategory.SHOPPING: 0.08,
            ExpenseCategory.INSURANCE: 0.05,
            ExpenseCategory.OTHER: 0.05,
        }
        
        # 根据消费习惯调整
        if finance.spending_habit == "frugal":
            multiplier = 0.8
        elif finance.spending_habit == "extravagant":
            multiplier = 1.3
        else:
            multiplier = 1.0
        
        for category, ratio in expense_ratios.items():
            finance.monthly_expenses[category.value] = income * ratio * multiplier
        
        # 税收
        finance.monthly_expenses['taxes'] = self._calculate_tax(income * 12) / 12
        
        # 储蓄（根据储蓄率）
        savings_amount = income * finance.savings_rate
        finance.monthly_expenses['savings'] = savings_amount
    
    def _calculate_tax(self, annual_income: float) -> float:
        """计算年度所得税（累进税制）"""
        tax = 0.0
        remaining_income = annual_income
        
        for bracket in self.indicators.tax_brackets:
            if remaining_income <= 0:
                break
            
            taxable_in_bracket = min(
                remaining_income,
                bracket['max'] - bracket['min']
            )
            tax += taxable_in_bracket * bracket['rate']
            remaining_income -= taxable_in_bracket
        
        return tax
    
    def update_monthly(self, agent_id: int, months_passed: int = 1) -> Dict:
        """更新月度财务"""
        if agent_id not in self.finances:
            return {}
        
        finance = self.finances[agent_id]
        events = []
        
        for _ in range(months_passed):
            # 1. 收入
            income = finance.total_monthly_income
            
            # 2. 支出
            expenses = finance.total_monthly_expenses
            
            # 3. 现金流
            cash_flow = income - expenses
            
            # 4. 更新现金
            finance.cash += cash_flow
            
            # 5. 如果现金不足，使用储蓄或增加债务
            if finance.cash < 0:
                shortage = abs(finance.cash)
                
                # 先用储蓄
                if finance.savings >= shortage:
                    finance.savings -= shortage
                    finance.cash = 0
                else:
                    finance.cash = 0
                    remaining = shortage - finance.savings
                    finance.savings = 0
                    
                    # 剩余部分计入信用卡债务
                    finance.credit_card_debt += remaining
                    events.append({
                        'type': 'debt_increase',
                        'amount': remaining,
                        'reason': 'insufficient_cash'
                    })
            
            # 6. 贷款还款
            self._process_loan_payments(finance)
            
            # 7. 投资回报
            self._process_investment_returns(finance)
            
            # 8. 更新信用评分
            self._update_credit_score(finance)
        
        return {'events': events, 'net_worth': finance.net_worth}
    
    def _process_loan_payments(self, finance: PersonalFinance):
        """处理贷款还款"""
        # 房贷（30 年，利率 4%）
        if finance.mortgage > 0:
            monthly_payment = finance.mortgage * 0.005  # 简化
            finance.cash -= monthly_payment
            finance.mortgage *= (1 + self.indicators.interest_rate / 12)
            finance.mortgage -= monthly_payment
            if finance.mortgage < 0:
                finance.mortgage = 0
        
        # 车贷（5 年，利率 5%）
        if finance.car_loan > 0:
            monthly_payment = finance.car_loan * 0.018
            finance.cash -= monthly_payment
            finance.car_loan *= (1 + 0.05 / 12)
            finance.car_loan -= monthly_payment
            if finance.car_loan < 0:
                finance.car_loan = 0
        
        # 信用卡（最低还款或全额）
        if finance.credit_card_debt > 0:
            min_payment = finance.credit_card_debt * 0.03
            if finance.cash >= finance.credit_card_debt:
                finance.cash -= finance.credit_card_debt
                finance.credit_card_debt = 0
            elif finance.cash >= min_payment:
                finance.cash -= min_payment
                finance.credit_card_debt *= (1 + 0.18 / 12)  # 18% 年利率
                finance.credit_card_debt -= min_payment
            else:
                finance.credit_card_debt *= (1 + 0.18 / 12)
                # 逾期，信用评分下降
                finance.credit_score -= 20
    
    def _process_investment_returns(self, finance: PersonalFinance):
        """处理投资回报"""
        # 储蓄账户利息
        finance.savings *= (1 + self.indicators.interest_rate / 12)
        
        # 股票回报（年化 7-10%，波动大）
        if 'stocks' in finance.investments:
            monthly_return = random.gauss(0.007, 0.05)  # 月均 0.7%，标准差 5%
            finance.investments['stocks'] *= (1 + monthly_return)
        
        # 债券回报（年化 3-5%，稳定）
        if 'bonds' in finance.investments:
            finance.investments['bonds'] *= (1 + 0.003)
        
        # 房产增值（年化 3-4%）
        if finance.real_estate > 0:
            finance.real_estate *= (1 + self.indicators.inflation_rate / 12 + 0.002)
    
    def _update_credit_score(self, finance: PersonalFinance):
        """更新信用评分"""
        # 基础分
        score = 650
        
        # 债务收入比（好：-100 分）
        if finance.debt_to_income_ratio < 0.5:
            score += 50
        elif finance.debt_to_income_ratio > 2.0:
            score -= 100
        
        # 信用利用率（信用卡债务/额度，假设额度=月收入*3）
        credit_limit = finance.monthly_income * 3
        if credit_limit > 0:
            utilization = finance.credit_card_debt / credit_limit
            if utilization < 0.3:
                score += 30
            elif utilization > 0.8:
                score -= 50
        
        # 净资产（正相关）
        if finance.net_worth > 100000:
            score += 50
        elif finance.net_worth < -50000:
            score -= 50
        
        # 平滑更新
        finance.credit_score += (score - finance.credit_score) * 0.1
        finance.credit_score = max(300, min(850, finance.credit_score))
    
    def update_economy(self, months_passed: int = 1):
        """更新宏观经济指标"""
        for _ in range(months_passed):
            self.cycle_months += 1
            
            # 经济周期
            if self.cycle_months >= self.cycle_length_months:
                self._change_economic_phase()
                self.cycle_months = 0
            
            # 根据周期调整指标
            phase_multipliers = {
                'expansion': {'gdp': 1.2, 'unemployment': 0.9, 'inflation': 1.1},
                'peak': {'gdp': 1.0, 'unemployment': 0.8, 'inflation': 1.3},
                'contraction': {'gdp': 0.8, 'unemployment': 1.3, 'inflation': 0.9},
                'trough': {'gdp': 0.9, 'unemployment': 1.5, 'inflation': 0.8},
            }
            
            mult = phase_multipliers[self.economic_phase]
            
            # GDP 增长率
            self.indicators.gdp_growth_rate = 0.025 * mult['gdp'] + random.gauss(0, 0.01)
            
            # 失业率
            self.indicators.unemployment_rate = 0.05 * mult['unemployment'] + random.gauss(0, 0.01)
            self.indicators.unemployment_rate = max(0.02, min(0.25, self.indicators.unemployment_rate))
            
            # 通胀率
            self.indicators.inflation_rate = 0.02 * mult['inflation'] + random.gauss(0, 0.005)
            self.indicators.inflation_rate = max(-0.02, min(0.15, self.indicators.inflation_rate))
            
            # 利率（央行调控）
            target_rate = self.indicators.inflation_rate + 0.01
            self.indicators.interest_rate += (target_rate - self.indicators.interest_rate) * 0.1
            
            # 股票市场
            stock_return = self.indicators.gdp_growth_rate / 12 + random.gauss(0, 0.04)
            self.indicators.stock_market_index *= (1 + stock_return)
            
            # 房价
            housing_return = self.indicators.inflation_rate / 12 + 0.002 + random.gauss(0, 0.01)
            self.indicators.housing_price_index *= (1 + housing_return)
            
            # 价格水平（通胀）
            self.price_level *= (1 + self.indicators.inflation_rate / 12)
    
    def _change_economic_phase(self):
        """改变经济周期阶段"""
        phases = ['expansion', 'peak', 'contraction', 'trough']
        current_idx = phases.index(self.economic_phase)
        self.economic_phase = phases[(current_idx + 1) % 4]
    
    def get_economic_statistics(self) -> Dict:
        """获取经济统计"""
        if not self.finances:
            return {}
        
        finances = list(self.finances.values())
        
        return {
            'total_agents': len(finances),
            'avg_income': sum(f.total_monthly_income for f in finances) / len(finances),
            'avg_net_worth': sum(f.net_worth for f in finances) / len(finances),
            'avg_savings_rate': sum(f.savings_rate_actual for f in finances) / len(finances),
            'avg_credit_score': sum(f.credit_score for f in finances) / len(finances),
            'gdp_growth': self.indicators.gdp_growth_rate,
            'unemployment': self.indicators.unemployment_rate,
            'inflation': self.indicators.inflation_rate,
            'interest_rate': self.indicators.interest_rate,
            'economic_phase': self.economic_phase,
            'stock_index': self.indicators.stock_market_index,
            'housing_index': self.indicators.housing_price_index,
        }
    
    def apply_raise(self, agent_id: int, percentage: float):
        """给 Agent 加薪"""
        if agent_id in self.finances:
            finance = self.finances[agent_id]
            finance.monthly_income *= (1 + percentage)
            self._calculate_expenses(finance, 35)  # 重新计算支出
    
    def give_unemployment_benefit(self, agent_id: int, months: int = 6):
        """发放失业救济"""
        if agent_id in self.finances:
            finance = self.finances[agent_id]
            benefit = finance.monthly_income * 0.6  # 60% 工资
            finance.other_income += benefit / months


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("经济系统测试")
    print("=" * 60)
    
    system = EconomicSystem()
    
    # 创建测试 Agent
    test_agents = [
        {'id': 1, 'income': 5000, 'age': 25},
        {'id': 2, 'income': 12000, 'age': 35},
        {'id': 3, 'income': 25000, 'age': 45},
        {'id': 4, 'income': 8000, 'age': 30},
    ]
    
    for agent in test_agents:
        system.create_finance(agent['id'], agent['income'], agent['age'])
    
    print(f"\n初始财务状况:")
    for agent in test_agents:
        finance = system.finances[agent['id']]
        print(f"  Agent {agent['id']} (${agent['income']}/月):")
        print(f"    净资产：${finance.net_worth:,.0f}")
        print(f"    储蓄率：{finance.savings_rate_actual*100:.1f}%")
        print(f"    信用分：{finance.credit_score:.0f}")
    
    # 模拟 12 个月
    print(f"\n模拟 12 个月...")
    for month in range(12):
        system.update_economy()
        for agent in test_agents:
            system.update_monthly(agent['id'])
        
        if (month + 1) % 3 == 0:
            print(f"  第{month+1}月：经济阶段={system.economic_phase}, "
                  f"通胀={system.indicators.inflation_rate*100:.1f}%, "
                  f"失业={system.indicators.unemployment_rate*100:.1f}%")
    
    # 最终统计
    stats = system.get_economic_statistics()
    print(f"\n经济统计:")
    print(f"  平均收入：${stats['avg_income']:,.0f}/月")
    print(f"  平均净资产：${stats['avg_net_worth']:,.0f}")
    print(f"  平均储蓄率：{stats['avg_savings_rate']*100:.1f}%")
    print(f"  平均信用分：{stats['avg_credit_score']:.0f}")
    print(f"  GDP 增长：{stats['gdp_growth']*100:.1f}%")
    print(f"  通胀率：{stats['inflation']*100:.1f}%")
    
    print("\n✅ 经济系统测试完成!")
