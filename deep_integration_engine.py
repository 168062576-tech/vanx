"""
虚拟世界深度集成引擎 - Deep Integration Engine

将 26+ 个子系统与原有演化引擎、教育、技能系统深度集成：
- 统一 Agent 档案（所有系统共享数据）
- 统一事件系统（跨系统事件传递）
- 统一数据流（系统间自动同步）
- 统一生命周期管理

作者：御龙军
日期：2026-03-17
版本：v1.0
"""

import random
import logging
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger('virtual_world')

# 导入所有子系统
from marriage_family_system import MarriageFamilySystem
from economic_system import EconomicSystem
from corporate_system import CorporateSystem, Industry, JobLevel
from housing_system import HousingSystem
from healthcare_system import HealthcareSystem
from decision_engine import DecisionEngine, DecisionContext
from social_network_system import SocialNetworkSystem, PersonalityType
from government_system import GovernmentSystem
from deep_micro_systems import DeepMicroSystem, RiskTolerance, ReligionType
from ability_system import AbilitySystem

# 扩展子系统（容错导入，缺失不影响核心运行）
try:
    from swarm_intelligence import SwarmIntelligenceEngine
except ImportError:
    SwarmIntelligenceEngine = None
try:
    from financial_system import FinancialSystem
except ImportError:
    FinancialSystem = None

# 扩展子系统（容错导入，缺失不影响核心运行）
try:
    from cultural_inheritance_system import CulturalInheritanceSystem
except ImportError:
    CulturalInheritanceSystem = None
try:
    from retirement_system import RetirementSystem
except ImportError:
    RetirementSystem = None
try:
    from career_system_enhanced import CareerSystem
except ImportError:
    CareerSystem = None
try:
    from education_system_enhanced import EducationSystemEnhanced
except ImportError:
    EducationSystemEnhanced = None
try:
    from healthcare_system_enhanced import HealthcareSystemEnhanced
except ImportError:
    HealthcareSystemEnhanced = None
try:
    from stock_market_system import StockMarket
except ImportError:
    StockMarket = None
try:
    from work_schedule_system import WorkScheduleSystem
except ImportError:
    WorkScheduleSystem = None
try:
    from occupation_system import OccupationSystem
except ImportError:
    OccupationSystem = None
try:
    from diversity_protection import DiversityProtector
except ImportError:
    DiversityProtector = None
try:
    from multi_source_news_system import MultiSourceNewsSystem
except ImportError:
    MultiSourceNewsSystem = None
try:
    from agent_discussion import generate_discussions
except ImportError:
    generate_discussions = None

# ── AI 行为引擎（LLM 认知架构） ──
try:
    from ai_evolution_engine import AIBehaviorEngine
except ImportError:
    AIBehaviorEngine = None

# ── 新增子系统（可选，缺失不影响主流程） ──
try:
    from cultural_inheritance_system import CulturalInheritanceSystem
except ImportError:
    CulturalInheritanceSystem = None

try:
    from retirement_system import RetirementSystem
except ImportError:
    RetirementSystem = None

try:
    from career_system_enhanced import CareerSystem
except ImportError:
    CareerSystem = None

try:
    from education_system_enhanced import EducationSystemEnhanced
except ImportError:
    EducationSystemEnhanced = None

try:
    from healthcare_system_enhanced import HealthcareSystemEnhanced
except ImportError:
    HealthcareSystemEnhanced = None

try:
    from stock_market_system import StockMarket
except ImportError:
    StockMarket = None

try:
    from work_schedule_system import WorkScheduleSystem
except ImportError:
    WorkScheduleSystem = None

try:
    from occupation_system import OccupationSystem
except ImportError:
    OccupationSystem = None

try:
    from diversity_protection import DiversityProtector
except ImportError:
    DiversityProtector = None

# 以下为独立工具，不需要月度循环
try:
    from product_market_simulator import ProductMarketSimulator
except ImportError:
    ProductMarketSimulator = None

try:
    from commercial_operations_optimizer import CommercialOperationsOptimizer
except ImportError:
    CommercialOperationsOptimizer = None

try:
    from evolution_report import ScenarioReportGenerator
except ImportError:
    ScenarioReportGenerator = None

try:
    from integration_modules import AgentDiscussionSystem
except ImportError:
    AgentDiscussionSystem = None

try:
    from event_manager import EventManager
except ImportError:
    EventManager = None


@dataclass
class UnifiedAgent:
    """统一 Agent 档案 - 所有系统数据整合"""
    
    # 基础信息
    id: int
    age: int
    gender: str
    created_date: datetime = field(default_factory=datetime.now)
    
    # 教育（原有系统）
    education_level: str = "high_school"  # elementary/middle/high/college/bachelor/master/phd
    education_status: str = "none"  # none/student/graduated
    
    # 技能（原有系统）
    skills: Dict[str, float] = field(default_factory=dict)  # {skill_name: level}
    talents: Dict[str, float] = field(default_factory=dict)  # 5 维天赋
    hobbies: List[str] = field(default_factory=list)
    
    # 职业（原有系统）
    occupation: str = "unemployed"
    career_path: List[Dict] = field(default_factory=list)
    
    # 经济（新系统）
    income: float = 0.0
    net_worth: float = 0.0
    credit_score: float = 650.0
    
    # 住房（新系统）
    housing_status: str = "renting"  # renting/owning/mortgage
    housing_cost: float = 0.0
    
    # 健康（新系统）
    health_score: float = 80.0
    mental_health: float = 80.0
    life_expectancy: float = 80.0
    diseases: List[str] = field(default_factory=list)
    
    # 社交（新系统）
    relationships: int = 0
    close_friends: int = 0
    popularity: float = 50.0
    
    # 婚姻（新系统）
    marital_status: str = "single"  # single/dating/married/divorced/widowed
    spouse_id: Optional[int] = None
    children: List[int] = field(default_factory=list)
    
    # 心理（新系统）
    happiness: float = 60.0
    stress: float = 40.0
    life_satisfaction: float = 60.0
    
    # 能力系统（新）
    abilities: Dict = field(default_factory=dict)       # {skill_name: level}
    unique_talents: List[str] = field(default_factory=list)  # 稀有特质
    mbti: str = ""
    
    # 状态标记
    is_alive: bool = True
    is_in_prison: bool = False
    is_unemployed: bool = True
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'age': self.age,
            'gender': self.gender,
            'education': self.education_level,
            'skills': self.skills,
            'income': self.income,
            'net_worth': self.net_worth,
            'health': self.health_score,
            'happiness': self.happiness,
            'marital_status': self.marital_status,
            'housing_status': self.housing_status,
            'abilities': self.abilities,
            'unique_talents': self.unique_talents,
            'mbti': self.mbti,
        }


@dataclass
class WorldEvent:
    """统一事件"""
    event_id: str
    timestamp: datetime
    event_type: str
    agent_id: Optional[int]
    data: Dict
    source_system: str
    priority: int = 0  # 0=normal, 1=important, 2=critical


class DeepIntegrationEngine:
    """深度集成引擎"""
    
    def __init__(self, config: Dict = None):
        self.config = config if config else {}
        
        # 初始化所有子系统
        self.marriage_system = MarriageFamilySystem(self.config.get('marriage', {}))
        self.economic_system = EconomicSystem(self.config.get('economy', {}))
        self.corporate_system = CorporateSystem(self.config.get('corporate', {}))
        self.housing_system = HousingSystem(self.config.get('housing', {}))
        self.healthcare_system = HealthcareSystem(self.config.get('healthcare', {}))
        self.social_system = SocialNetworkSystem(self.config.get('social', {}))
        self.government_system = GovernmentSystem(self.config.get('government', {}))
        self.deep_micro_system = DeepMicroSystem(self.config.get('deep_micro', {}))
        
        # 群体智能引擎（可选，开源版本缺失不影响运行）
        self.swarm_engine = SwarmIntelligenceEngine(self.config.get('swarm', {})) if SwarmIntelligenceEngine else None
        
        # 金融系统（可选，开源版本缺失不影响运行）
        self.financial_system = FinancialSystem(self.config.get('financial', {})) if FinancialSystem else None
        
        # 决策引擎
        self.decision_engine = DecisionEngine(self.config.get('decision', {}))
        
        # 能力系统
        self.ability_system = AbilitySystem(self.config.get('ability', {}))
        
        # AI 行为引擎（LLM 认知架构 — 容错初始化）
        self.ai_engine = None
        if AIBehaviorEngine:
            try:
                ai_config = self.config.get('ai', {})
                # 支持传入配置路径或配置字典
                if isinstance(ai_config, str):
                    self.ai_engine = AIBehaviorEngine(config_path=ai_config)
                else:
                    self.ai_engine = AIBehaviorEngine()
                    if ai_config:
                        self.ai_engine._merge_config(ai_config)
            except Exception as e:
                print(f"[AI] 行为引擎初始化失败（降级到规则引擎）: {e}")
                self.ai_engine = None
        
        # 扩展子系统（容错初始化）
        self.cultural_inheritance = CulturalInheritanceSystem() if CulturalInheritanceSystem else None
        self.retirement_system = RetirementSystem() if RetirementSystem else None
        self.career_enhanced = CareerSystem() if CareerSystem else None
        self.education_enhanced = EducationSystemEnhanced() if EducationSystemEnhanced else None
        self.healthcare_enhanced = HealthcareSystemEnhanced() if HealthcareSystemEnhanced else None
        self.stock_market = StockMarket() if StockMarket else None
        self.work_schedule = WorkScheduleSystem() if WorkScheduleSystem else None
        self.occupation_sys = OccupationSystem() if OccupationSystem else None
        self.diversity_protection = DiversityProtector() if DiversityProtector else None
        self.news_system = MultiSourceNewsSystem() if MultiSourceNewsSystem else None
        
        # 涌现行为检测器
        try:
            from emergence_detector import EmergenceDetector
            self.emergence_detector = EmergenceDetector()
        except Exception:
            self.emergence_detector = None
        
        # Agent 管理
        self.agents: Dict[int, UnifiedAgent] = {}
        self.agent_id_counter = 1
        
        # 事件系统
        # ── 事件上限机制 ──
        # MAX_EVENTS: 事件列表最大长度，超过后自动归档最早的一半事件
        # archived_events_count: 已归档事件数量（只记数量，释放内存）
        # archived_events_type_counts: 已归档事件按类型统计
        self.MAX_EVENTS: int = self.config.get('max_events', 50000)
        self.events: List[WorldEvent] = []
        self.archived_events_count: int = 0
        self.archived_events_type_counts: Dict[str, int] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_id_counter = 1
        
        # 世界状态
        self.months_simulated = 0
        self.world_time = datetime.now()
        
        # 初始化公司
        self._initialize_companies()
        
        # 事件管理器（独立的发布/订阅总线）
        try:
            if EventManager:
                self.event_manager = EventManager(
                    archive_dir=str(Path(self.config.get('data_dir', './data')) / 'event_archive')
                )
            else:
                self.event_manager = None
        except Exception:
            self.event_manager = None
    
    def _initialize_companies(self):
        """初始化公司"""
        companies = [
            ("TechCorp", Industry.TECHNOLOGY, 500000),
            ("FinanceHub", Industry.FINANCE, 1000000),
            ("HealthCare Plus", Industry.HEALTHCARE, 800000),
            ("EduWorld", Industry.EDUCATION, 300000),
            ("RetailMart", Industry.RETAIL, 400000),
            ("ManufactureCo", Industry.MANUFACTURING, 600000),
        ]
        
        for name, industry, capital in companies:
            self.corporate_system.create_company(name, industry, 0, capital)
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def emit_event(self, event_type: str, agent_id: Optional[int], 
                   data: Dict, source_system: str, priority: int = 0):
        """触发事件"""
        event = WorldEvent(
            event_id=f"evt_{self.event_id_counter}",
            timestamp=self.world_time,
            event_type=event_type,
            agent_id=agent_id,
            data=data,
            source_system=source_system,
            priority=priority
        )
        
        self.events.append(event)
        self.event_id_counter += 1
        
        # ── 事件归档：超过上限时归档最早的一半事件 ──
        if len(self.events) > self.MAX_EVENTS:
            self._archive_old_events()
        
        # 调用处理器
        for handler in self.event_handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"Event handler error: {e}")
        
        # 同时发布到事件管理器（独立的发布/订阅总线）
        if hasattr(self, 'event_manager') and self.event_manager:
            try:
                self.event_manager.emit(
                    event_type, agent_id,
                    data if isinstance(data, dict) else {},
                    source_system, self.months_simulated
                )
            except Exception:
                pass
        
        return event
    
    def _archive_old_events(self):
        """归档最早的一半事件，释放内存
        
        只保留最近的事件，归档的事件只记录数量和类型统计。
        """
        half = len(self.events) // 2
        old_events = self.events[:half]
        
        # 统计被归档事件的类型数量
        for evt in old_events:
            self.archived_events_type_counts[evt.event_type] = \
                self.archived_events_type_counts.get(evt.event_type, 0) + 1
        
        self.archived_events_count += half
        self.events = self.events[half:]  # 只保留最近的一半
    
    # ── 事件查询方法 ──
    
    def get_recent_events(self, n: int = 100) -> List[WorldEvent]:
        """获取最近的 n 个事件
        
        Args:
            n: 返回事件数量，默认 100
        
        Returns:
            最近的 n 个 WorldEvent 列表（按时间正序）
        """
        return self.events[-n:] if n < len(self.events) else list(self.events)
    
    def get_events_by_type(self, event_type: str, limit: int = 50) -> List[WorldEvent]:
        """按类型获取事件（从最近的事件中筛选）
        
        Args:
            event_type: 事件类型字符串，如 "agent_created", "employment_started" 等
            limit: 最多返回的事件数量，默认 50
        
        Returns:
            匹配类型的 WorldEvent 列表（最近的在后面）
        """
        matched = [e for e in reversed(self.events) if e.event_type == event_type]
        return list(reversed(matched[:limit]))
    
    def get_event_stats(self) -> Dict:
        """获取事件统计信息
        
        Returns:
            包含以下键的字典：
            - total_events: 总事件数（含已归档）
            - active_events: 当前内存中的事件数
            - archived_events: 已归档事件数
            - max_events: 事件上限
            - type_counts: 各类型事件数量（合并当前+已归档）
        """
        # 统计当前内存中的事件类型
        active_type_counts: Dict[str, int] = {}
        for evt in self.events:
            active_type_counts[evt.event_type] = \
                active_type_counts.get(evt.event_type, 0) + 1
        
        # 合并已归档的类型统计
        merged_type_counts = dict(self.archived_events_type_counts)
        for etype, count in active_type_counts.items():
            merged_type_counts[etype] = merged_type_counts.get(etype, 0) + count
        
        return {
            'total_events': len(self.events) + self.archived_events_count,
            'active_events': len(self.events),
            'archived_events': self.archived_events_count,
            'max_events': self.MAX_EVENTS,
            'type_counts': merged_type_counts,
        }
    
    def create_agent(self, agent_data: Dict = None) -> UnifiedAgent:
        """创建统一 Agent"""
        agent_data = agent_data or {}
        
        agent_id = self.agent_id_counter
        self.agent_id_counter += 1
        
        age = agent_data.get('age', random.randint(22, 45))
        gender = agent_data.get('gender', random.choice(['male', 'female']))
        
        # 创建统一档案
        agent = UnifiedAgent(id=agent_id, age=age, gender=gender)
        
        # 教育（原有系统逻辑）
        if age < 6:
            agent.education_status = "none"
        elif age < 18:
            agent.education_status = "student"
            agent.education_level = "high_school"
        elif age < 22:
            agent.education_status = "student"
            agent.education_level = random.choice(["college", "bachelor"])
        else:
            agent.education_status = "graduated"
            agent.education_level = random.choices(
                ["high_school", "college", "bachelor", "master", "phd"],
                weights=[0.3, 0.25, 0.3, 0.1, 0.05]
            )[0]
        
        # 技能（原有系统逻辑）
        agent.skills = self._generate_skills(age, agent.education_level)
        agent.talents = self._generate_talents()
        agent.hobbies = self._generate_hobbies()
        
        # 初始化各子系统
        self._initialize_subsystems(agent, agent_data)
        
        # 能力系统初始化
        ability_profile = self.ability_system.create_profile(
            agent_id, age, agent.education_level, gender)
        sync = self.ability_system.sync_to_agent(agent_id)
        agent.abilities = sync['abilities']
        agent.unique_talents = sync['unique_talents']
        agent.mbti = sync['mbti']
        
        self.agents[agent_id] = agent
        
        # 触发创建事件
        self.emit_event("agent_created", agent_id, 
                       {'age': age, 'gender': gender}, "integration")
        
        return agent
    
    def _generate_skills(self, age: int, education: str) -> Dict[str, float]:
        """生成技能（原有系统逻辑）"""
        skills = {}
        
        # 基础技能
        base_skills = ["communication", "teamwork", "problem_solving"]
        for skill in base_skills:
            skills[skill] = min(10, 2 + age * 0.1 + random.gauss(0, 1))
        
        # 教育相关技能
        if education in ["bachelor", "master", "phd"]:
            skills["research"] = random.uniform(3, 8)
            skills["critical_thinking"] = random.uniform(4, 9)
        
        # 年龄相关
        if age > 25:
            skills["leadership"] = random.uniform(2, min(10, age * 0.15))
        
        return skills
    
    def _generate_talents(self) -> Dict[str, float]:
        """生成天赋（5 维）"""
        return {
            'logical': max(1, min(10, random.gauss(5, 2))),
            'creative': max(1, min(10, random.gauss(5, 2))),
            'social': max(1, min(10, random.gauss(5, 2))),
            'physical': max(1, min(10, random.gauss(5, 2))),
            'musical': max(1, min(10, random.gauss(5, 2))),
        }
    
    def _generate_hobbies(self) -> List[str]:
        """生成爱好"""
        all_hobbies = [
            "reading", "gaming", "sports", "music", "painting",
            "socializing", "technology", "business", "science", "travel"
        ]
        return random.sample(all_hobbies, random.randint(1, 3))
    
    def _initialize_subsystems(self, agent: UnifiedAgent, agent_data: Dict):
        """初始化各子系统"""
        agent_id = agent.id
        age = agent.age
        income = agent_data.get('income', self._estimate_income(agent.education_level, age))
        
        # 经济
        self.economic_system.create_finance(agent_id, income, age)
        agent.income = income
        
        # 企业（就业）
        if age >= 16 and agent.education_status == "graduated":
            self._assign_job(agent)
        
        # 住房
        self._initialize_housing(agent, income)
        
        # 医疗
        self.healthcare_system.create_health_record(agent_id, age, agent.gender)
        
        # 社交
        self.social_system.create_profile(agent_id, age)
        
        # 深层微观
        self.deep_micro_system.create_deep_profile(agent_id, age, income)
        self.deep_micro_system.create_micro_profile(agent_id, age, agent.occupation)
        
        # 金融系统
        try:
            self.financial_system.create_financial_profile(agent)
        except Exception as _e:
            logger.warning(f"Financial system init failed for agent: {_e}")
    
    def _estimate_income(self, education: str, age: int) -> float:
        """估算收入"""
        base_income = {
            "high_school": 3000,
            "college": 4500,
            "bachelor": 6000,
            "master": 9000,
            "phd": 12000,
        }
        
        base = base_income.get(education, 4000)
        age_multiplier = 1 + max(0, (age - 22)) * 0.02
        
        return base * age_multiplier * random.uniform(0.8, 1.2)
    
    def _assign_job(self, agent: UnifiedAgent):
        """分配工作"""
        if not self.corporate_system.companies:
            return
        
        company_id = random.choice(list(self.corporate_system.companies.keys()))
        company = self.corporate_system.companies[company_id]
        
        # 找开放职位
        for pos_id, pos in company.positions.items():
            if pos.is_open:
                salary = (pos.min_salary + pos.max_salary) / 2
                self.corporate_system.hire(agent.id, company_id, pos_id, salary)
                agent.occupation = pos.title
                agent.income = salary / 12
                agent.is_unemployed = False
                
                self.emit_event("employment_started", agent.id,
                              {'company': company.name, 'position': pos.title},
                              "corporate")
                break
    
    def _initialize_housing(self, agent: UnifiedAgent, income: float):
        """初始化住房"""
        from housing_system import HousingType, Neighborhood
        
        if agent.age < 25 or income < 4000:
            # 租房
            prop = self.housing_system.create_property(
                HousingType.APARTMENT, Neighborhood.URBAN, 1, 600
            )
            prop.is_for_rent = True
            self.housing_system.rent_property(agent.id, prop.property_id)
            agent.housing_status = "renting"
            agent.housing_cost = prop.rent_price_monthly
        else:
            # 买房
            prop = self.housing_system.create_property(
                HousingType.CONDO, Neighborhood.SUBURB, 2, 1200
            )
            prop.is_for_sale = True
            self.housing_system.buy_property(agent.id, prop.property_id, income * 6)
            agent.housing_status = "mortgage"
            agent.housing_cost = income * 0.3
    
    def simulate_month(self, months_passed: int = 1) -> Dict:
        """模拟一个月"""
        all_events = []
        
        for _ in range(months_passed):
            self.months_simulated += 1
            self.world_time = datetime.now()
            
            # 1. 宏观经济更新
            self.economic_system.update_economy()
            macro_data = self.deep_micro_system.update_macro_monthly(
                len(self.agents),
                {'avg_income': sum(a.income for a in self.agents.values()) / len(self.agents) if self.agents else 5000}
            )
            
            # 2. 每个 Agent 更新
            for agent in list(self.agents.values()):
                if not agent.is_alive:
                    continue
                
                agent_id = agent.id
                events = self._update_agent(agent)
                all_events.extend(events)
            
            # 3. 公司月度更新（所有 Agent 更新完成后，统一执行一次）
            # [BUG FIX 2026-03-23] 从 _update_agent() 的 per-agent 循环中提取出来，
            # 避免 O(N×M) 重复调用。每个公司只更新一次，复杂度降为 O(M)。
            for company_id in list(self.corporate_system.companies.keys()):
                self.corporate_system.update_company_monthly(company_id)
            
            # 4. 政府
            agents_list = [a.to_dict() for a in self.agents.values() if a.is_alive]
            gov_result = self.government_system.update_monthly(
                agents_list,
                {'unemployed': 0.05, 'law_enforcement': 1.0}
            )
            
            for event in gov_result.get('events', []):
                self.emit_event(event['type'], event.get('agent_id'), event, "government")
            
            # 5. 婚姻家庭系统
            try:
                marriage_agents = [{'id': a.id, 'age': a.age, 'gender': a.gender,
                                    'income': a.income, 'marital_status': a.marital_status}
                                   for a in self.agents.values() if a.is_alive]
                family_events = self.marriage_system.generate_family_events(marriage_agents, 1)
                for evt in family_events:
                    evt_agents = evt.get('agents', [])
                    agent_id = evt_agents[0] if evt_agents else None
                    self.emit_event(evt.get('type', 'family_event'), agent_id, evt, 'marriage')
                    all_events.append(evt)
                    # 回写婚姻状态到 Agent 对象
                    if evt.get('type') == 'relationship_married':
                        for aid in evt_agents:
                            if aid in self.agents:
                                self.agents[aid].marital_status = 'married'
                    elif evt.get('type') == 'relationship_divorced':
                        for aid in evt_agents:
                            if aid in self.agents:
                                self.agents[aid].marital_status = 'divorced'
                    elif evt.get('type') == 'relationship_started':
                        for aid in evt_agents:
                            if aid in self.agents:
                                self.agents[aid].marital_status = 'dating'
            except Exception as _e:
                logger.warning(f"Phase 5 (marriage) failed: {_e}")
            
            # 6. 深层微观系统批量模拟（18 个子系统）
            try:
                agents_dicts = [{'id': a.id, 'age': a.age, 'gender': a.gender,
                                 'income': a.income, 'occupation': a.occupation,
                                 'is_unemployed': a.is_unemployed, 'stress': a.stress,
                                 'happiness': a.happiness, 'health_score': a.health_score,
                                 'net_worth': a.net_worth, 'education_level': a.education_level,
                                 'marital_status': a.marital_status, 'children': a.children,
                                 'is_alive': a.is_alive,
                                 'in_prison': getattr(a, 'is_in_prison', False),
                                 'alive': a.is_alive,
                                 'employed': not a.is_unemployed,
                                 'education': {'high_school': 12, 'college': 14, 'bachelor': 16,
                                               'master': 18, 'phd': 20}.get(a.education_level, 12),
                                 'social_connections': a.relationships,
                                 'personality_openness': a.talents.get('creative', 5) / 10,
                                 'personality_neuroticism': max(0, min(1, a.stress / 100))}
                                for a in self.agents.values() if a.is_alive]
                micro_events = self.deep_micro_system.simulate_month(agents_dicts, self.months_simulated)
                # 将微观事件加入引擎事件列表
                for evt in micro_events:
                    self.emit_event(evt.get('type', 'micro_event'), evt.get('agent_id'), evt, 'deep_micro')
                    all_events.append(evt)
                # 回写修改到 agent 对象
                agent_map = {a['id']: a for a in agents_dicts}
                for aid, a_dict in agent_map.items():
                    if aid in self.agents:
                        agent = self.agents[aid]
                        agent.stress = a_dict.get('stress', agent.stress)
                        agent.happiness = a_dict.get('happiness', agent.happiness)
                        agent.health_score = a_dict.get('health_score', agent.health_score)
                        agent.net_worth = a_dict.get('net_worth', agent.net_worth)
                        agent.income = a_dict.get('income', agent.income)
            except Exception as _e:
                logger.warning(f"Phase 6 (deep_micro) failed: {_e}")
            
            # 7. 群体智能（信息传播、群体极化、从众效应）
            try:
                swarm_events = self.swarm_engine.update_monthly(self.agents, all_events)
                for evt in swarm_events:
                    self.emit_event(evt.get('type', 'swarm_event'), evt.get('agent_id'), evt, 'swarm')
                    all_events.append(evt)
            except Exception as _e:
                logger.warning(f"Phase 7 (swarm) failed: {_e}")
            
            # 8. 金融市场更新（股市、利率等宏观金融）
            try:
                self.financial_system.update_market()
            except Exception as _e:
                logger.warning(f"Phase 8 (financial_market) failed: {_e}")
            
            # 9. 文化传承（代际影响）
            if self.cultural_inheritance:
                try:
                    ci_events = self.cultural_inheritance.update_monthly(self.agents)
                    if ci_events:
                        for evt in (ci_events if isinstance(ci_events, list) else []):
                            self.emit_event(evt.get('type', 'cultural'), evt.get('agent_id'), evt, 'cultural')
                            all_events.append(evt)
                except Exception as _e:
                    logger.warning(f"Phase 9 (cultural) failed: {_e}")
            
            # 10. 退休检查
            if self.retirement_system:
                try:
                    for agent in list(self.agents.values()):
                        if agent.is_alive and agent.age >= 55:
                            ret_result = self.retirement_system.check_retirement_eligibility(agent)
                            if ret_result and isinstance(ret_result, dict) and ret_result.get('retired'):
                                self.emit_event('retirement', agent.id, ret_result, 'retirement')
                                all_events.append(ret_result)
                except Exception as _e:
                    logger.warning(f"Phase 10 (retirement) failed: {_e}")
            
            # 11. 增强职业（晋升/失业/转行）
            if self.career_enhanced:
                try:
                    career_events = self.career_enhanced.update_monthly(self.agents)
                    if career_events and isinstance(career_events, list):
                        for evt in career_events:
                            self.emit_event(evt.get('type', 'career'), evt.get('agent_id'), evt, 'career')
                            all_events.append(evt)
                except Exception as _e:
                    logger.warning(f"Phase 11 (career) failed: {_e}")
            
            # 12. 增强教育（GPA/考试/升学）
            if self.education_enhanced:
                try:
                    edu_events = self.education_enhanced.update_monthly(self.agents)
                    if edu_events and isinstance(edu_events, list):
                        for evt in edu_events:
                            self.emit_event(evt.get('type', 'education'), evt.get('agent_id'), evt, 'education')
                            all_events.append(evt)
                except Exception as _e:
                    logger.warning(f"Phase 12 (education) failed: {_e}")
            
            # 13. 增强医疗（疾病/诊断/治疗）
            if self.healthcare_enhanced:
                try:
                    hc_events = self.healthcare_enhanced.update_monthly(self.agents)
                    if hc_events and isinstance(hc_events, list):
                        for evt in hc_events:
                            self.emit_event(evt.get('type', 'healthcare_adv'), evt.get('agent_id'), evt, 'healthcare_adv')
                            all_events.append(evt)
                except Exception as _e:
                    logger.warning(f"Phase 13 (healthcare_adv) failed: {_e}")
            
            # 14. 股票市场月度更新
            if self.stock_market:
                try:
                    for _ in range(22):  # 约22个交易日/月
                        self.stock_market.update_daily()
                except Exception as _e:
                    logger.warning(f"Phase 14 (stock_market) failed: {_e}")
            
            # 15. 作息与职业行为
            if self.work_schedule:
                try:
                    self.work_schedule.update_monthly(self.agents)
                except Exception as _e:
                    logger.warning(f"Phase 15a (work_schedule) failed: {_e}")
            if self.occupation_sys:
                try:
                    occ_events = self.occupation_sys.update_monthly(self.agents)
                    if occ_events and isinstance(occ_events, list):
                        for evt in occ_events:
                            all_events.append(evt)
                except Exception as _e:
                    logger.warning(f"Phase 15b (occupation) failed: {_e}")
            
            # 16. 新闻系统（模拟新闻事件注入世界）
            if self.news_system:
                try:
                    news_events = self.news_system.update_monthly(self.agents) if hasattr(self.news_system, 'update_monthly') else []
                    if news_events and isinstance(news_events, list):
                        for evt in news_events:
                            self.emit_event(evt.get('type', 'news'), evt.get('agent_id'), evt, 'news')
                            all_events.append(evt)
                except Exception as _e:
                    logger.warning(f"Phase 16 (news) failed: {_e}")
            
            # 17. 涌现行为检测
            if self.emergence_detector:
                try:
                    emergence = self.emergence_detector.detect_all(self.agents, all_events, self.months_simulated)
                    for alert in emergence.get('alerts', []):
                        self.emit_event('emergence_alert', None, alert, 'emergence')
                        all_events.append(alert)
                except Exception as _e:
                    logger.warning(f"Phase 17 (emergence) failed: {_e}")
            
            # 18. 多样性保护（放在最后，防止同质化）
            if self.diversity_protection:
                try:
                    self.diversity_protection.update_monthly(self.agents)
                except Exception as _e:
                    logger.warning(f"Phase 18 (diversity) failed: {_e}")
        
        return {
            'months_simulated': self.months_simulated,
            'events_count': len(all_events),
            'macro_data': macro_data,
            'economic_indicators': self.economic_system.indicators.__dict__,
        }
    
    def _update_agent(self, agent: UnifiedAgent) -> List[Dict]:
        """更新单个 Agent"""
        events = []
        agent_id = agent.id
        
        # 经济
        finance_events = self.economic_system.update_monthly(agent_id)
        finance = self.economic_system.finances.get(agent_id)
        if finance:
            agent.net_worth = finance.net_worth
            agent.credit_score = finance.credit_score
        
        for event in finance_events.get('events', []):
            self.emit_event(event['type'], agent_id, event, "economic")
            events.append(event)
        
        # 住房
        self.housing_system.update_monthly(agent_id)
        if agent_id in self.housing_system.residences:
            residence = self.housing_system.residences[agent_id]
            agent.housing_status = residence.status.value
            agent.housing_cost = residence.rent_monthly
        
        # 公司 - 仅检查该 Agent 的企业关联状态（如薪资、晋升等）
        # [BUG FIX 2026-03-23] 公司级月度更新(update_company_monthly)已移至
        # simulate_month() 中统一执行，避免 O(N×M) 重复调用。
        # 原代码在此处对每个 Agent 遍历所有公司并调用 update_company_monthly，
        # 导致 N 个 Agent × M 个公司 = N×M 次重复更新。
        # 现在此处只保留 per-agent 级别的企业状态同步。
        for company in self.corporate_system.companies.values():
            if agent_id in company.employees:
                # 同步该 Agent 的企业相关状态
                # employees 是 List[int]（Agent ID 列表），不是 dict
                # 薪资从 Employment 记录或公司平均薪资推算
                if hasattr(self.corporate_system, 'employments') and agent_id in self.corporate_system.employments:
                    emp = self.corporate_system.employments[agent_id]
                    if hasattr(emp, 'salary') and emp.salary:
                        agent.income = emp.salary / 12
                elif company.revenue and company.employee_count > 0:
                    agent.income = (company.revenue * 0.4) / company.employee_count / 12
                break  # 一个 Agent 通常只在一家公司
        
        # 能力影响收入（限制 modifier 范围防止指数增长）
        _mod = self.ability_system.calc_income_modifier(agent_id)
        _mod = max(0.5, min(_mod, 2.0))  # 限制在0.5x-2.0x
        agent.income *= _mod
        agent.income = max(0, min(agent.income, 1000000))  # 硬上限100万/月
        
        # 金融系统月度更新
        try:
            fin_result = self.financial_system.update_agent_monthly(agent)
            fin_summary = self.financial_system.get_financial_summary(agent_id)
            if fin_summary:
                # 金融资产计入净资产
                agent.net_worth += fin_summary.get('total_investments', 0)
            for event in fin_result.get('events', []):
                self.emit_event(event.get('type', 'financial'), agent_id, event, "financial")
                events.append(event)
        except Exception as _e:
            logger.warning(f"Financial monthly update failed for agent {agent_id}: {_e}")
        
        # 医疗
        health_events = self.healthcare_system.update_monthly(agent_id, agent.age)
        health = self.healthcare_system.health_records.get(agent_id)
        if health:
            agent.health_score = health.overall_health
            agent.mental_health = health.mental_health
            agent.life_expectancy = health.life_expectancy_base
            agent.diseases = [d.value for d in health.current_diseases]
        
        for event in health_events:
            self.emit_event(event['type'], agent_id, event, "healthcare")
            events.append(event)
        
        # 社交
        self.social_system.update_monthly([agent_id])
        social = self.social_system.profiles.get(agent_id)
        if social:
            agent.relationships = social.total_connections
            agent.close_friends = social.close_friends
            agent.popularity = social.popularity
        
        # 深层微观 — 已移至 simulate_month() 阶段6批量调用，此处不再重复
        # [BUG FIX Phase3] 删除双重调用，阶段6的 simulate_month 更完整
        
        # 能力系统月度更新
        if agent_id in self.ability_system.profiles:
            self.ability_system.current_month = self.months_simulated
            ab_result = self.ability_system.update_monthly(
                agent_id, agent.age, agent.occupation,
                agent.happiness, agent.health_score)
            for event in ab_result.get('events', []):
                self.emit_event(event['type'], agent_id, event, "ability")
                events.append(event)
            # 回写到 Agent 对象
            sync = self.ability_system.sync_to_agent(agent_id)
            agent.abilities = sync['abilities']
            agent.unique_talents = sync['unique_talents']
            agent.mbti = sync['mbti']
        
        # ── 决策引擎介入 ──
        # 根据 Agent 当前状态，触发关键人生决策
        self._run_decisions(agent, events)
        
        # 年龄增长（每年）
        if self.months_simulated % 12 == 0:
            agent.age += 1
        
        return events
    
    def get_agent_status(self, agent_id: int) -> Dict:
        """获取 Agent 完整状态"""
        if agent_id not in self.agents:
            return {}
        
        agent = self.agents[agent_id]
        return agent.to_dict()
    
    def _run_decisions(self, agent, events: list):
        """为 Agent 运行决策引擎（每月触发）— 优先使用 AI 引擎"""
        agent_id = agent.id
        
        # ── AI 引擎决策（优先） ──
        if self.ai_engine and hasattr(self.ai_engine, 'decide_for_agent'):
            try:
                context = {
                    'age': agent.age,
                    'income': agent.income,
                    'income_monthly': agent.income,
                    'happiness': agent.happiness,
                    'health': agent.health_score,
                    'stress': agent.stress,
                    'occupation': agent.occupation,
                    'marital_status': agent.marital_status,
                    'mbti': getattr(agent, 'mbti', ''),
                    'abilities': getattr(agent, 'abilities', {}),
                    'education_level': agent.education_level,
                    'satisfaction': agent.life_satisfaction,
                    'life_satisfaction': agent.life_satisfaction,
                    'skills': getattr(agent, 'skills', {}),
                    'month': self.months_simulated,
                    'hour': 12,
                    'day_of_week': self.months_simulated % 7,
                }
                # 使用 AI 引擎的 v5 适配接口
                behavior = self.ai_engine.decide_for_agent(agent, context)
                # [Phase3 Fix12] 区分三种状态：
                # - None = AI 引擎不可用/出错 → 降级到规则引擎
                # - falsy (空字符串/False/0) = AI 主动决定不行动 → return，不降级
                # - truthy = 有具体行动 → 执行并 return
                if behavior is not None:
                    if behavior:
                        result = self.ai_engine.execute_for_agent(agent, behavior)
                        # 记录 AI 决策事件
                        self.emit_event(f'ai_decision_{behavior}', agent_id,
                            {'action': behavior, 'result': result,
                             'engine': self.ai_engine.llm_status.get('mode', 'rules')},
                            'ai_decision')
                        events.append({'type': f'ai_decision_{behavior}', 'agent_id': agent_id})
                        
                        # 检查重大人生选择
                        life_choice = self.ai_engine.check_life_choices(
                            {'stress': agent.stress,
                             'satisfaction': agent.life_satisfaction,
                             'life_satisfaction': agent.life_satisfaction},
                            context)
                        if life_choice:
                            self._apply_ai_life_choice(agent, life_choice, events)
                    # behavior 为空/False = AI 主动决定不行动，也 return，不降级
                    return  # AI 引擎有响应，跳过旧规则
            except Exception as e:
                pass  # AI 引擎出错，降级到规则决策
        
        # ── 降级：原有规则决策（保持不变） ──
        
        # 职业决策：不开心或低收入时考虑换工作
        if agent.happiness < 40 or (agent.income < 2000 and agent.age > 22):
            if random.random() < 0.1:  # 10% 概率触发思考
                ctx = DecisionContext(
                    decision_type="career_change",
                    options=["change_job", "stay"],
                    agent_summary={'happiness': agent.happiness, 'income': agent.income}
                )
                d = self.decision_engine.decide(agent, ctx)
                if d.choice == "change_job":
                    # 模拟换工作效果
                    agent.income *= random.uniform(1.0, 1.5)
                    agent.happiness = min(100, agent.happiness + random.uniform(5, 15))
                    self.emit_event("career_change", agent_id,
                        {"choice": d.choice, "engine": d.engine_used, "new_income": agent.income},
                        "decision")
                    events.append({"type": "career_change", "agent_id": agent_id})
        
        # 婚姻决策：适龄单身时考虑
        if (agent.marital_status == 'single' and 24 <= agent.age <= 40
                and agent.happiness > 40):
            if random.random() < 0.02:  # 2% 概率触发
                ctx = DecisionContext(
                    decision_type="marriage",
                    options=["marry", "wait"],
                    agent_summary={'age': agent.age, 'happiness': agent.happiness}
                )
                d = self.decision_engine.decide(agent, ctx)
                if d.choice == "marry":
                    agent.marital_status = 'married'
                    agent.happiness = min(100, agent.happiness + random.uniform(10, 20))
                    self.emit_event("marriage_decision", agent_id,
                        {"choice": d.choice, "engine": d.engine_used},
                        "decision")
                    events.append({"type": "marriage_decision", "agent_id": agent_id})
        
        # 犯罪决策：低收入+不开心+年轻
        if agent.income < 1500 and agent.happiness < 30 and agent.age < 35:
            if random.random() < 0.03:  # 3% 概率触发
                ctx = DecisionContext(
                    decision_type="crime_decision",
                    options=["commit_crime", "stay_legal"],
                    agent_summary={'income': agent.income, 'happiness': agent.happiness}
                )
                d = self.decision_engine.decide(agent, ctx)
                if d.choice == "commit_crime":
                    self.emit_event("crime_decision", agent_id,
                        {"choice": d.choice, "engine": d.engine_used},
                        "decision")
                    events.append({"type": "crime_decision", "agent_id": agent_id})
    
    def _apply_ai_life_choice(self, agent, life_choice: str, events: list):
        """应用 AI 引擎的重大人生决策"""
        agent_id = agent.id
        
        if life_choice == 'rest':
            agent.stress = max(0, agent.stress - random.uniform(10, 20))
            agent.happiness = min(100, agent.happiness + random.uniform(5, 10))
        elif life_choice == 'vacation':
            agent.stress = max(0, agent.stress - random.uniform(20, 40))
            agent.happiness = min(100, agent.happiness + random.uniform(10, 20))
        elif life_choice == 'quit_job':
            agent.occupation = 'unemployed'
            agent.is_unemployed = True
            agent.stress = max(0, agent.stress - random.uniform(15, 30))
            agent.income *= 0.3  # 失业后只有储蓄
        
        self.emit_event(f'ai_life_choice_{life_choice}', agent_id,
            {'choice': life_choice}, 'ai_decision')
        events.append({'type': f'ai_life_choice_{life_choice}', 'agent_id': agent_id})
    
    def get_world_statistics(self) -> Dict:
        """获取世界统计"""
        if not self.agents:
            return {}
        
        agents = list(self.agents.values())
        
        return {
            'simulation': {
                'months_simulated': self.months_simulated,
                'total_agents': len(agents),
                'total_events': len(self.events) + self.archived_events_count,
                'active_events': len(self.events),
                'archived_events': self.archived_events_count,
            },
            'demographics': {
                'avg_age': sum(a.age for a in agents) / len(agents),
                'gender_ratio': sum(1 for a in agents if a.gender == 'male') / len(agents),
                'education_distribution': self._count_by_field(agents, 'education_level'),
            },
            'economy': {
                'avg_income': sum(a.income for a in agents) / len(agents),
                'avg_net_worth': sum(a.net_worth for a in agents) / len(agents),
                'unemployment_rate': sum(1 for a in agents if a.is_unemployed) / len(agents),
            },
            'housing': {
                'status_distribution': self._count_by_field(agents, 'housing_status'),
            },
            'health': {
                'avg_health': sum(a.health_score for a in agents) / len(agents),
                'avg_mental_health': sum(a.mental_health for a in agents) / len(agents),
                'avg_life_expectancy': sum(a.life_expectancy for a in agents) / len(agents),
            },
            'social': {
                'avg_happiness': sum(a.happiness for a in agents) / len(agents),
                'avg_stress': sum(a.stress for a in agents) / len(agents),
            },
        }
    
    def _count_by_field(self, agents: List[UnifiedAgent], field: str) -> Dict:
        """按字段统计"""
        counts = {}
        for agent in agents:
            value = getattr(agent, field, 'unknown')
            counts[value] = counts.get(value, 0) + 1
        return counts


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("深度集成引擎测试")
    print("=" * 60)
    
    engine = DeepIntegrationEngine()
    
    # 创建测试 Agent
    print(f"\n创建 50 个 Agent...")
    for i in range(50):
        engine.create_agent()
    
    print(f"✅ 创建完成")
    
    # 显示样本
    print(f"\nAgent 样本 (前 5 个):")
    for i in range(1, 6):
        status = engine.get_agent_status(i)
        print(f"  Agent {i}: {status.get('age')}岁, {status.get('gender')}, "
              f"${status.get('income', 0):,.0f}/月, {status.get('education')}, "
              f"{status.get('housing_status')}")
    
    # 模拟 6 个月
    print(f"\n模拟 6 个月...")
    for month in range(6):
        result = engine.simulate_month()
        if (month + 1) % 2 == 0:
            print(f"  第{month+1}月：{result['events_count']}个事件，"
                  f"GDP {result['economic_indicators']['gdp_growth_rate']*100:.1f}%")
    
    # 世界统计
    stats = engine.get_world_statistics()
    print(f"\n世界统计:")
    print(f"  总人口：{stats['demographics'].get('avg_age', 0):.1f}岁平均")
    print(f"  平均收入：${stats['economy'].get('avg_income', 0):,.0f}/月")
    print(f"  平均健康：{stats['health'].get('avg_health', 0):.1f}/100")
    print(f"  平均幸福：{stats['social'].get('avg_happiness', 0):.1f}/100")
    
    print("\n✅ 深度集成引擎测试完成!")
