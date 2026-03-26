"""
企业系统 - Corporate System

模拟真实的企业组织和商业活动：
- 公司创建/运营/破产/并购
- 招聘/解雇/晋升/薪资调整
- 部门架构/职位层级
- 企业绩效/股票/分红
- 创业/投资/市场竞争

作者：御龙军
日期：2026-03-17
版本：v1.0
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class CompanySize(Enum):
    """公司规模"""
    MICRO = "micro"  # 1-9 人
    SMALL = "small"  # 10-49 人
    MEDIUM = "medium"  # 50-249 人
    LARGE = "large"  # 250-999 人
    ENTERPRISE = "enterprise"  # 1000+ 人


class Industry(Enum):
    """行业类型"""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    SERVICE = "service"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    OTHER = "other"


class JobLevel(Enum):
    """职位层级"""
    ENTRY = "entry"  # 初级
    JUNIOR = "junior"  # 中级
    SENIOR = "senior"  # 高级
    LEAD = "lead"  # 主管
    MANAGER = "manager"  # 经理
    DIRECTOR = "director"  # 总监
    VP = "vp"  # 副总裁
    C_LEVEL = "c_level"  # C 级高管
    OWNER = "owner"  # 所有者


@dataclass
class Department:
    """部门"""
    dept_id: int
    name: str
    budget: float = 0.0
    employees: List[int] = field(default_factory=list)  # Agent IDs
    manager_id: Optional[int] = None
    performance: float = 1.0  # 0-2，1 为平均


@dataclass
class JobPosition:
    """职位"""
    position_id: int
    title: str
    department: str
    level: JobLevel
    min_salary: float
    max_salary: float
    required_skills: List[str] = field(default_factory=list)
    required_experience_years: int = 0
    is_open: bool = True
    employee_id: Optional[int] = None  # 当前任职者


@dataclass
class Company:
    """公司"""
    company_id: int
    name: str
    industry: Industry
    size: CompanySize = CompanySize.MICRO
    founded_date: datetime = field(default_factory=datetime.now)
    
    # 财务
    revenue: float = 0.0  # 年收入
    expenses: float = 0.0  # 年支出
    profit: float = 0.0  # 年利润
    cash: float = 0.0  # 现金
    valuation: float = 0.0  # 估值
    stock_price: float = 0.0  # 股价（如上市）
    
    # 组织
    employees: List[int] = field(default_factory=list)  # Agent IDs
    departments: Dict[int, Department] = field(default_factory=dict)
    positions: Dict[int, JobPosition] = field(default_factory=dict)
    owner_id: Optional[int] = None
    
    # 运营
    performance_score: float = 1.0  # 0-2
    growth_rate: float = 0.0  # 增长率
    turnover_rate: float = 0.0  # 员工流失率
    
    # 状态
    is_public: bool = False  # 是否上市
    is_bankrupt: bool = False
    
    @property
    def employee_count(self) -> int:
        return len(self.employees)
    
    @property
    def profit_margin(self) -> float:
        if self.revenue == 0:
            return 0
        return self.profit / self.revenue


@dataclass
class Employment:
    """雇佣关系"""
    agent_id: int
    company_id: int
    position_id: int
    start_date: datetime
    salary: float
    performance_rating: float = 3.0  # 1-5
    last_raise_date: Optional[datetime] = None
    is_terminated: bool = False
    termination_date: Optional[datetime] = None
    termination_reason: Optional[str] = None


class CorporateSystem:
    """企业系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.companies: Dict[int, Company] = {}
        self.employments: Dict[int, Employment] = {}  # agent_id -> Employment
        self.company_id_counter = 1
        self.position_id_counter = 1
        
        # 行业基准薪资
        self.industry_salary_multipliers = {
            Industry.TECHNOLOGY: 1.3,
            Industry.FINANCE: 1.4,
            Industry.HEALTHCARE: 1.2,
            Industry.EDUCATION: 0.7,
            Industry.MANUFACTURING: 1.0,
            Industry.RETAIL: 0.8,
            Industry.SERVICE: 0.9,
            Industry.GOVERNMENT: 1.0,
            Industry.NONPROFIT: 0.7,
        }
        
        # 职位层级薪资基准（年收入）
        self.level_salary_base = {
            JobLevel.ENTRY: 30000,
            JobLevel.JUNIOR: 45000,
            JobLevel.SENIOR: 65000,
            JobLevel.LEAD: 80000,
            JobLevel.MANAGER: 100000,
            JobLevel.DIRECTOR: 140000,
            JobLevel.VP: 200000,
            JobLevel.C_LEVEL: 350000,
        }
        
        # 标准部门
        self.standard_departments = [
            "Executive", "Engineering", "Product", "Sales",
            "Marketing", "Finance", "HR", "Operations", "Support"
        ]
    
    def create_company(self, name: str, industry: Industry, 
                      founder_id: int, initial_capital: float = 100000) -> Company:
        """创建公司"""
        company = Company(
            company_id=self.company_id_counter,
            name=name,
            industry=industry,
            cash=initial_capital,
            owner_id=founder_id,
            valuation=initial_capital,
        )
        
        # 根据初始资本设定规模
        if initial_capital < 50000:
            company.size = CompanySize.MICRO
        elif initial_capital < 500000:
            company.size = CompanySize.SMALL
        elif initial_capital < 5000000:
            company.size = CompanySize.MEDIUM
        else:
            company.size = CompanySize.LARGE
        
        # 创建基础部门
        self._setup_departments(company)
        
        # 创建基础职位
        self._setup_positions(company)
        
        self.companies[company.company_id] = company
        self.company_id_counter += 1
        
        return company
    
    def _setup_departments(self, company: Company):
        """设置公司部门"""
        dept_count = min(len(self.standard_departments), 
                        max(2, company.employee_count // 5 + 2))
        
        for i, dept_name in enumerate(self.standard_departments[:dept_count]):
            dept = Department(
                dept_id=i,
                name=dept_name,
                budget=company.cash / dept_count if dept_count > 0 else 0
            )
            company.departments[dept.dept_id] = dept
    
    def _setup_positions(self, company: Company):
        """设置公司职位"""
        # 根据行业和规模创建职位
        positions_to_create = []
        
        # 高管职位
        if company.size != CompanySize.MICRO:
            positions_to_create.append(("CEO", "Executive", JobLevel.C_LEVEL))
            positions_to_create.append(("CTO", "Engineering", JobLevel.C_LEVEL))
            positions_to_create.append(("CFO", "Finance", JobLevel.C_LEVEL))
        
        # 中层职位
        for dept_name in ["Engineering", "Sales", "Marketing", "Operations"]:
            if dept_name in [d.name for d in company.departments.values()]:
                positions_to_create.append((f"{dept_name} Manager", dept_name, JobLevel.MANAGER))
                positions_to_create.append((f"Senior {dept_name[:-1] if dept_name.endswith('s') else dept_name}", 
                                          dept_name, JobLevel.SENIOR))
        
        # 初级职位
        positions_to_create.append(("Junior Engineer", "Engineering", JobLevel.JUNIOR))
        positions_to_create.append(("Sales Representative", "Sales", JobLevel.ENTRY))
        
        for title, dept, level in positions_to_create:
            base_salary = self.level_salary_base.get(level, 50000)
            industry_mult = self.industry_salary_multipliers.get(company.industry, 1.0)
            
            position = JobPosition(
                position_id=self.position_id_counter,
                title=title,
                department=dept,
                level=level,
                min_salary=base_salary * industry_mult * 0.8,
                max_salary=base_salary * industry_mult * 1.2,
                required_experience_years=self._get_required_experience(level)
            )
            company.positions[position.position_id] = position
            self.position_id_counter += 1
    
    def _get_required_experience(self, level: JobLevel) -> int:
        """获取职位所需经验年限"""
        experience_map = {
            JobLevel.ENTRY: 0,
            JobLevel.JUNIOR: 2,
            JobLevel.SENIOR: 5,
            JobLevel.LEAD: 7,
            JobLevel.MANAGER: 8,
            JobLevel.DIRECTOR: 12,
            JobLevel.VP: 15,
            JobLevel.C_LEVEL: 20,
        }
        return experience_map.get(level, 0)
    
    def hire(self, agent_id: int, company_id: int, position_id: int, 
             salary: float = None) -> Optional[Employment]:
        """雇佣 Agent"""
        if company_id not in self.companies:
            return None
        
        company = self.companies[company_id]
        if position_id not in company.positions:
            return None
        
        position = company.positions[position_id]
        if not position.is_open:
            return None
        
        # 如果已有工作，先离职
        if agent_id in self.employments:
            self.terminate(agent_id, "resignation")
        
        # 确定薪资
        if salary is None:
            salary = (position.min_salary + position.max_salary) / 2
        
        # 创建雇佣关系
        employment = Employment(
            agent_id=agent_id,
            company_id=company_id,
            position_id=position_id,
            start_date=datetime.now(),
            salary=salary
        )
        
        self.employments[agent_id] = employment
        position.is_open = False
        position.employee_id = agent_id
        company.employees.append(agent_id)
        
        # 更新公司规模
        self._update_company_size(company)
        
        return employment
    
    def terminate(self, agent_id: int, reason: str = "layoff"):
        """解雇/离职"""
        if agent_id not in self.employments:
            return
        
        employment = self.employments[agent_id]
        employment.is_terminated = True
        employment.termination_date = datetime.now()
        employment.termination_reason = reason
        
        # 更新公司
        if employment.company_id in self.companies:
            company = self.companies[employment.company_id]
            if agent_id in company.employees:
                company.employees.remove(agent_id)
            
            # 释放职位
            if employment.position_id in company.positions:
                position = company.positions[employment.position_id]
                position.is_open = True
                position.employee_id = None
        
        # 更新公司规模
        self._update_company_size(company)
        
        # 从雇佣记录中移除（保留历史记录的话可以不移除）
        del self.employments[agent_id]
    
    def promote(self, agent_id: int, new_position_id: int = None, 
                raise_percentage: float = None) -> bool:
        """晋升"""
        if agent_id not in self.employments:
            return False
        
        employment = self.employments[agent_id]
        company = self.companies.get(employment.company_id)
        if not company:
            return False
        
        current_position = company.positions.get(employment.position_id)
        if not current_position:
            return False
        
        # 如果没有指定新职位，自动晋升到下一级
        if new_position_id is None:
            new_position = self._find_next_position(company, current_position)
            if not new_position:
                return False
            new_position_id = new_position.position_id
        
        new_position = company.positions[new_position_id]
        
        # 更新职位
        current_position.is_open = True
        current_position.employee_id = None
        
        employment.position_id = new_position_id
        new_position.is_open = False
        new_position.employee_id = agent_id
        
        # 加薪
        if raise_percentage is None:
            raise_percentage = random.uniform(0.10, 0.25)  # 10-25%
        
        employment.salary *= (1 + raise_percentage)
        employment.last_raise_date = datetime.now()
        
        return True
    
    def _find_next_position(self, company: Company, 
                           current: JobPosition) -> Optional[JobPosition]:
        """查找下一级职位"""
        level_order = [JobLevel.ENTRY, JobLevel.JUNIOR, JobLevel.SENIOR, 
                      JobLevel.LEAD, JobLevel.MANAGER, JobLevel.DIRECTOR, 
                      JobLevel.VP, JobLevel.C_LEVEL]
        
        try:
            current_idx = level_order.index(current.level)
            if current_idx >= len(level_order) - 1:
                return None
            
            next_level = level_order[current_idx + 1]
            
            # 找同部门或相近的下一级职位
            for pos in company.positions.values():
                if pos.level == next_level and pos.is_open:
                    return pos
        except ValueError:
            pass
        
        return None
    
    def update_company_monthly(self, company_id: int, months_passed: int = 1):
        """更新公司月度运营"""
        if company_id not in self.companies:
            return
        
        company = self.companies[company_id]
        
        for _ in range(months_passed):
            # 1. 收入（基于规模和绩效）
            base_revenue = self._calculate_base_revenue(company)
            company.revenue = base_revenue * company.performance_score
            
            # 2. 支出（主要是薪资）
            total_salary = sum(
                self.employments[emp_id].salary 
                for emp_id in company.employees 
                if emp_id in self.employments
            )
            company.expenses = total_salary * 1.5  # 薪资 + 其他成本
            
            # 3. 利润
            company.profit = company.revenue - company.expenses
            
            # 4. 现金流
            company.cash += company.profit / 12  # 月利润
            
            # 5. 估值
            if company.profit > 0:
                company.valuation = company.profit * 10  # 10 倍 PE
            else:
                company.valuation = company.cash * 2
            
            # 6. 增长率
            company.growth_rate = (company.revenue - company.expenses) / max(company.revenue, 1)
            
            # 7. 员工流失
            self._process_turnover(company)
            
            # 8. 招聘（如果有空缺且有钱）
            self._process_hiring(company)
            
            # 9. 破产检查
            if company.cash < 0 and abs(company.cash) > company.valuation:
                company.is_bankrupt = True
                self._handle_bankruptcy(company)
    
    def _calculate_base_revenue(self, company: Company) -> float:
        """计算基础收入"""
        # 基于员工数、行业、规模
        base_per_employee = {
            CompanySize.MICRO: 50000,
            CompanySize.SMALL: 80000,
            CompanySize.MEDIUM: 100000,
            CompanySize.LARGE: 120000,
            CompanySize.ENTERPRISE: 150000,
        }
        
        industry_mult = self.industry_salary_multipliers.get(company.industry, 1.0)
        
        return (base_per_employee.get(company.size, 100000) * 
                company.employee_count * industry_mult)
    
    def _process_turnover(self, company: Company):
        """处理员工流失"""
        # 基础流失率 1-3%/月
        base_turnover = 0.02
        
        # 绩效差的公司流失率高
        if company.performance_score < 0.8:
            base_turnover *= 2
        
        # 低薪流失率高
        for emp_id in company.employees[:]:
            if emp_id in self.employments:
                employment = self.employments[emp_id]
                position = company.positions.get(employment.position_id)
                
                if position:
                    market_salary = (position.min_salary + position.max_salary) / 2
                    if employment.salary < market_salary * 0.8:
                        # 薪资低于市场 80%，流失概率高
                        if random.random() < base_turnover * 3:
                            self.terminate(emp_id, "resignation")
                    elif random.random() < base_turnover:
                        self.terminate(emp_id, "resignation")
    
    def _process_hiring(self, company: Company):
        """处理招聘"""
        if company.cash < 50000:  # 现金不足不招聘
            return
        
        # 找空缺职位
        open_positions = [p for p in company.positions.values() if p.is_open]
        
        for position in open_positions[:3]:  # 每月最多招 3 人
            if random.random() < 0.3:  # 30% 概率填补每个空缺
                # 简化：随机找一个符合条件的 Agent
                # TODO: 实际应从 Agent 池中找
                pass
    
    def _handle_bankruptcy(self, company: Company):
        """处理破产"""
        # 解雇所有员工
        for emp_id in company.employees[:]:
            self.terminate(emp_id, "layoff")
        
        # 公司标记为破产
        company.is_bankrupt = True
        company.employees = []
    
    def _update_company_size(self, company: Company):
        """更新公司规模"""
        count = company.employee_count
        if count < 10:
            company.size = CompanySize.MICRO
        elif count < 50:
            company.size = CompanySize.SMALL
        elif count < 250:
            company.size = CompanySize.MEDIUM
        elif count < 1000:
            company.size = CompanySize.LARGE
        else:
            company.size = CompanySize.ENTERPRISE
    
    def get_company_statistics(self) -> Dict:
        """获取公司统计"""
        if not self.companies:
            return {}
        
        companies = [c for c in self.companies.values() if not c.is_bankrupt]
        
        return {
            'total_companies': len(companies),
            'total_employees': sum(c.employee_count for c in companies),
            'avg_company_size': sum(c.employee_count for c in companies) / len(companies) if companies else 0,
            'total_revenue': sum(c.revenue for c in companies),
            'total_profit': sum(c.profit for c in companies),
            'avg_profit_margin': sum(c.profit_margin for c in companies) / len(companies) if companies else 0,
            'bankruptcies': sum(1 for c in self.companies.values() if c.is_bankrupt),
        }


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("企业系统测试")
    print("=" * 60)
    
    system = CorporateSystem()
    
    # 创建测试公司
    tech_company = system.create_company(
        name="TechCorp",
        industry=Industry.TECHNOLOGY,
        founder_id=1,
        initial_capital=500000
    )
    
    finance_company = system.create_company(
        name="FinanceHub",
        industry=Industry.FINANCE,
        founder_id=2,
        initial_capital=1000000
    )
    
    print(f"\n创建公司:")
    print(f"  {tech_company.name}: {tech_company.size.value}, ${tech_company.cash:,.0f}, {tech_company.employee_count}人")
    print(f"  {finance_company.name}: {finance_company.size.value}, ${finance_company.cash:,.0f}, {finance_company.employee_count}人")
    
    # 模拟招聘
    test_employees = [
        {'id': 10, 'position': 1},
        {'id': 11, 'position': 2},
        {'id': 12, 'position': 3},
    ]
    
    print(f"\n招聘员工...")
    for emp in test_employees:
        # 找第一个开放职位
        for pos_id, pos in tech_company.positions.items():
            if pos.is_open:
                system.hire(emp['id'], tech_company.company_id, pos_id)
                print(f"  Agent {emp['id']} 入职 {pos.title} (${pos.min_salary/12:,.0f}/月)")
                break
    
    # 模拟 12 个月运营
    print(f"\n模拟 12 个月运营...")
    for month in range(12):
        system.update_company_monthly(tech_company.company_id)
        system.update_company_monthly(finance_company.company_id)
        
        if (month + 1) % 3 == 0:
            print(f"  第{month+1}月:")
            print(f"    {tech_company.name}: 收入${tech_company.revenue/12:,.0f}/月，利润${tech_company.profit/12:,.0f}/月，现金${tech_company.cash:,.0f}")
            print(f"    {finance_company.name}: 收入${finance_company.revenue/12:,.0f}/月，利润${finance_company.profit/12:,.0f}/月，现金${finance_company.cash:,.0f}")
    
    # 统计
    stats = system.get_company_statistics()
    print(f"\n企业统计:")
    print(f"  公司总数：{stats['total_companies']}")
    print(f"  员工总数：{stats['total_employees']}")
    print(f"  平均规模：{stats['avg_company_size']:.1f}人")
    print(f"  总收入：${stats['total_revenue']:,.0f}")
    print(f"  总利润：${stats['total_profit']:,.0f}")
    print(f"  平均利润率：{stats['avg_profit_margin']*100:.1f}%")
    
    print("\n✅ 企业系统测试完成!")
