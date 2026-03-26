"""
深层细节与微观行为系统 - Deep Details & Micro Behaviors

P2 深层细节（8 个系统）+ P3 微观行为（10 个系统）合并实施：

P2 深层细节:
- 犯罪司法、媒体娱乐、宗教文化、科技创新
- 国际贸易、环境生态、交通运输、军事国防

P3 微观行为:
- 日常作息、饮食习惯、购物行为、学习行为
- 迁移流动、财富传承、心理状态、人际关系
- 社会认同、风险行为

作者：御龙军
日期：2026-03-17
版本：v1.0
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


# ==================== P2 深层细节 ====================

class MediaConsumptionType(Enum):
    """媒体消费类型"""
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    TV = "tv"
    MOVIES = "movies"
    GAMES = "games"
    BOOKS = "books"
    MUSIC = "music"
    PODCASTS = "podcasts"


class ReligionType(Enum):
    """宗教类型"""
    CHRISTIANITY = "christianity"
    ISLAM = "islam"
    BUDDHISM = "buddhism"
    HINDUISM = "hinduism"
    JUDAISM = "judaism"
    ATHEIST = "atheist"
    AGNOSTIC = "agnostic"
    OTHER = "other"


class RiskTolerance(Enum):
    """风险承受"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class DeepProfile:
    """深层档案"""
    agent_id: int
    
    # 媒体消费
    media_consumption: Dict[MediaConsumptionType, float] = field(default_factory=dict)
    news_consumption_daily_min: float = 30.0
    social_media_hours_daily: float = 2.0
    media_literacy: float = 50.0  # 媒体素养
    
    # 宗教信仰
    religion: ReligionType = ReligionType.ATHEIST
    religiosity: float = 0.0  # 虔诚度 0-100
    religious_attendance: str = "never"  # never/rarely/monthly/weekly
    
    # 科技创新
    tech_adoption: float = 50.0  # 技术采纳度
    innovation_score: float = 30.0  # 创新能力
    
    # 环境意识
    environmental_awareness: float = 50.0
    carbon_footprint: float = 10.0  # 吨 CO2/年
    recycling_habit: bool = False
    
    # 文化参与
    cultural_participation: float = 30.0  # 文化活动参与
    arts_appreciation: float = 40.0  # 艺术鉴赏
    
    # 风险偏好
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    investment_risk: float = 0.5  # 投资风险承受
    
    # 社会认同
    social_identity: List[str] = field(default_factory=list)
    group_memberships: int = 0
    identity_strength: float = 50.0


@dataclass
class MicroBehaviorProfile:
    """微观行为档案"""
    agent_id: int
    
    # 日常作息
    wake_time: str = "07:00"
    sleep_time: str = "23:00"
    daily_routine_regularity: float = 70.0  # 作息规律度
    leisure_hours_daily: float = 4.0
    
    # 饮食习惯
    meals_per_day: int = 3
    cooking_frequency: float = 0.5  # 自己做饭比例
    healthy_eating_score: float = 60.0
    dietary_restrictions: List[str] = field(default_factory=list)
    
    # 购物行为
    shopping_frequency: str = "weekly"  # daily/weekly/monthly
    online_shopping_ratio: float = 0.5
    brand_loyalty: float = 50.0
    impulse_buying_tendency: float = 30.0
    
    # 学习行为
    learning_hours_weekly: float = 3.0
    learning_style: str = "mixed"  # visual/auditory/reading/mixed
    continuous_learning: bool = True
    certifications: int = 0
    
    # 迁移倾向
    mobility_score: float = 30.0  # 流动性
    relocation_willingness: float = 40.0
    travel_frequency: str = "yearly"  # never/yearly/monthly/weekly
    
    # 财富观念
    financial_literacy: float = 50.0
    wealth_transfer_plan: bool = False
    inheritance_expected: float = 0.0
    
    # 心理状态
    stress_level: float = 40.0  # 0-100
    happiness_level: float = 60.0  # 0-100
    life_satisfaction: float = 60.0  # 0-100
    optimism: float = 55.0
    
    # 人际关系质量
    relationship_quality: float = 60.0
    social_support: float = 50.0
    loneliness_score: float = 30.0  # 孤独感（越低越好）
    
    # 时间使用
    work_hours_daily: float = 8.0
    commute_hours_daily: float = 1.0
    exercise_hours_weekly: float = 3.0
    screen_time_hours_daily: float = 5.0


class DeepMicroSystem:
    """深层细节与微观行为系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.deep_profiles: Dict[int, DeepProfile] = {}
        self.micro_profiles: Dict[int, MicroBehaviorProfile] = {}
        
        # 国际贸易参数
        self.trade_balance = 0.0
        self.import_volume = 0.0
        self.export_volume = 0.0
        
        # 环境参数
        self.avg_carbon_footprint = 10.0
        self.recycling_rate = 0.3
        
        # 交通参数
        self.avg_commute_time = 30.0  # 分钟
        self.public_transit_usage = 0.2
        
        # 军事参数
        self.defense_budget = 0.0
        self.military_personnel = 0
        
        # 全局经济参数（simulate_month 使用）
        self._exchange_rate = 1.0
        self._price_index = 1.0
    
    def create_deep_profile(self, agent_id: int, age: int, income: float) -> DeepProfile:
        """创建深层档案"""
        profile = DeepProfile(agent_id=agent_id)
        
        # 媒体消费（年轻人更多社交媒体）
        if age < 30:
            profile.social_media_hours_daily = random.uniform(2, 5)
            profile.media_consumption[MediaConsumptionType.SOCIAL_MEDIA] = random.uniform(60, 90)
        else:
            profile.social_media_hours_daily = random.uniform(0.5, 2)
            profile.media_consumption[MediaConsumptionType.NEWS] = random.uniform(40, 70)
        
        # 宗教（年龄越大越可能信教）
        if age > 50:
            profile.religiosity = random.uniform(30, 80)
            profile.religion = random.choice([ReligionType.CHRISTIANITY, ReligionType.BUDDHISM])
            profile.religious_attendance = random.choice(["monthly", "weekly"])
        
        # 技术采纳（年轻人更高）
        profile.tech_adoption = max(20, 80 - age * 0.5 + random.gauss(0, 15))
        
        # 风险偏好
        if age < 35:
            profile.risk_tolerance = random.choice([RiskTolerance.MODERATE, RiskTolerance.HIGH])
        else:
            profile.risk_tolerance = random.choice([RiskTolerance.LOW, RiskTolerance.MODERATE])
        
        self.deep_profiles[agent_id] = profile
        return profile
    
    def create_micro_profile(self, agent_id: int, age: int, 
                            occupation: str = None) -> MicroBehaviorProfile:
        """创建微观行为档案"""
        profile = MicroBehaviorProfile(agent_id=agent_id)
        
        # 作息（上班族规律，学生较晚）
        if occupation in ['student', 'unemployed']:
            profile.wake_time = f"{random.randint(8, 10):02d}:00"
            profile.sleep_time = f"{random.randint(23, 24):02d}:00"
        else:
            profile.wake_time = f"{random.randint(6, 8):02d}:00"
            profile.sleep_time = f"{random.randint(22, 23):02d}:00"
        
        # 饮食（收入高更健康）
        profile.healthy_eating_score = 50 + random.gauss(0, 20)
        
        # 购物（年轻人更多网购）
        if age < 35:
            profile.online_shopping_ratio = random.uniform(0.5, 0.9)
        else:
            profile.online_shopping_ratio = random.uniform(0.2, 0.5)
        
        # 学习（年轻人学习更多）
        if age < 30:
            profile.learning_hours_weekly = random.uniform(3, 10)
        else:
            profile.learning_hours_weekly = random.uniform(0, 5)
        
        # 心理状态
        profile.stress_level = 40 + random.gauss(0, 20)
        profile.happiness_level = 60 + random.gauss(0, 15)
        profile.life_satisfaction = 60 + random.gauss(0, 15)
        
        # 约束范围
        profile.stress_level = max(0, min(100, profile.stress_level))
        profile.happiness_level = max(0, min(100, profile.happiness_level))
        profile.life_satisfaction = max(0, min(100, profile.life_satisfaction))
        
        self.micro_profiles[agent_id] = profile
        return profile
    
    # ================================================================
    #  simulate_month — 18 个子模拟的入口
    # ================================================================

    def simulate_month(self, agents: List[Dict], month: int) -> List[Dict]:
        """
        对所有 agent 执行 18 个深层微观子模拟。

        agents: list of dict, 每个 agent 至少含:
            id, age, gender, income, education(0-20), occupation(str),
            health_score(0-100), happiness(0-100), stress(0-100),
            net_worth, employed(bool), city(str),
            social_connections(int), children(list[int]),
            alive(bool), personality_openness(0-1), personality_neuroticism(0-1)
        month: 当前月份序号

        返回：本月事件列表 [{type, agent_id, detail, ...}, ...]
        """
        events: List[Dict] = []

        # 先做一次全局国际贸易波动（P2-5），影响 _price_index
        self._sim_international_trade(month, len(agents), events)

        for ag in agents:
            if not ag.get('alive', True):
                continue

            aid = ag['id']
            deep = self.deep_profiles.get(aid)
            micro = self.micro_profiles.get(aid)
            if not deep or not micro:
                continue

            age = ag.get('age', 30)
            income = ag.get('income', 3000)
            edu = ag.get('education', 10)
            occ = ag.get('occupation', 'worker')
            stress = ag.get('stress', micro.stress_level)
            employed = ag.get('employed', True)
            gender = ag.get('gender', 'male')
            net_worth = ag.get('net_worth', 0)
            openness = ag.get('personality_openness', 0.5)
            neuroticism = ag.get('personality_neuroticism', 0.5)

            # ---------- P2 深层细节 (8) ----------
            self._sim_crime_justice(ag, deep, micro, income, stress, employed, events)
            self._sim_media_entertainment(ag, deep, micro, age, edu, occ, events)
            self._sim_religion_culture(ag, deep, micro, age, income, events)
            self._sim_tech_innovation(ag, deep, micro, age, occ, events)
            # 国际贸易已在循环外处理
            self._sim_environment(ag, deep, micro, income, edu, events)
            self._sim_transportation(ag, deep, micro, ag.get('city', 'default'), events)
            self._sim_military(ag, deep, micro, age, gender, month, events)

            # ---------- P3 微观行为 (10) ----------
            self._sim_daily_routine(ag, micro, age, occ, events)
            self._sim_diet(ag, micro, income, edu, events)
            self._sim_shopping(ag, micro, income, openness, neuroticism, events)
            self._sim_learning(ag, micro, deep, age, edu, events)
            self._sim_migration(ag, micro, age, income, employed, events)
            self._sim_wealth_inheritance(ag, deep, micro, agents, events)
            self._sim_psychology(ag, micro, stress, income, events)
            self._sim_social_relations(ag, micro, age, occ, events)
            self._sim_social_identity(ag, deep, micro, income, edu, occ, events)
            self._sim_risk_behavior(ag, deep, micro, stress, income, neuroticism, events)

            # 回写主属性
            ag['stress'] = max(0, min(100, micro.stress_level))
            ag['happiness'] = max(0, min(100, micro.happiness_level))
            ag['health_score'] = max(0, min(100, ag.get('health_score', 70)))
            ag['net_worth'] = ag.get('net_worth', 0)

        return events

    # ---- P2-1: 犯罪司法 ----
    def _sim_crime_justice(self, ag, deep, micro, income, stress, employed, events):
        aid = ag['id']
        # 基础犯罪概率（大幅降低，更真实）
        base_prob = 0.0002
        if income < 2000:
            base_prob += 0.0005
        if stress > 80:
            base_prob += 0.0003
        if not employed:
            base_prob += 0.0005
        # 是否犯罪
        if random.random() < base_prob:
            arrest_prob = 0.4  # 被捕概率
            if random.random() < arrest_prob:
                # 入狱：标记，影响收入/压力
                ag['in_prison'] = True
                ag['income'] = 0
                micro.stress_level += 20
                micro.happiness_level -= 15
                events.append({'type': 'arrested', 'agent_id': aid, 'detail': 'committed crime and arrested'})
            else:
                events.append({'type': 'crime_unpunished', 'agent_id': aid})
        # 出狱检查（假设坐牢 6 个月后释放）
        if ag.get('in_prison'):
            ag['prison_months'] = ag.get('prison_months', 0) + 1
            if ag['prison_months'] >= 6:
                ag['in_prison'] = False
                ag['prison_months'] = 0
                micro.stress_level -= 5
                events.append({'type': 'released', 'agent_id': aid})

    # ---- P2-2: 媒体娱乐 ----
    def _sim_media_entertainment(self, ag, deep, micro, age, edu, occ, events):
        # 媒体消费时间随年龄/职业变化
        if age < 25:
            deep.social_media_hours_daily = min(6, deep.social_media_hours_daily + random.uniform(-0.1, 0.15))
        elif age > 50:
            deep.social_media_hours_daily = max(0.3, deep.social_media_hours_daily + random.uniform(-0.1, 0.05))
        else:
            deep.social_media_hours_daily += random.uniform(-0.1, 0.1)
        deep.social_media_hours_daily = max(0, min(8, deep.social_media_hours_daily))
        # 媒体素养随教育提升
        deep.media_literacy = min(100, deep.media_literacy + edu * 0.02 + random.uniform(-0.5, 0.5))
        # 过度使用影响心理
        if deep.social_media_hours_daily > 4:
            micro.stress_level += 0.5
            micro.loneliness_score += 0.3

    # ---- P2-3: 宗教文化 ----
    def _sim_religion_culture(self, ag, deep, micro, age, income, events):
        # 宗教虔诚度随年龄微增
        if age > 40:
            deep.religiosity = min(100, deep.religiosity + random.uniform(0, 0.3))
        # 文化参与随收入提升
        if income > 8000:
            deep.cultural_participation = min(100, deep.cultural_participation + random.uniform(0, 0.5))
        elif income < 3000:
            deep.cultural_participation = max(0, deep.cultural_participation - random.uniform(0, 0.2))
        # 高虔诚度 → 更高社会支持
        if deep.religiosity > 60:
            micro.social_support = min(100, micro.social_support + 0.3)
            micro.life_satisfaction += 0.2

    # ---- P2-4: 科技创新 ----
    def _sim_tech_innovation(self, ag, deep, micro, age, occ, events):
        # 技术采纳度随年龄下降，随 IT 职业提升
        age_factor = max(-0.5, (30 - age) * 0.01)
        occ_factor = 0.3 if occ in ('engineer', 'programmer', 'it', 'scientist', 'researcher') else 0.0
        deep.tech_adoption = max(0, min(100, deep.tech_adoption + age_factor + occ_factor + random.uniform(-0.3, 0.3)))
        # IT 从业者创新分更高
        if occ in ('engineer', 'programmer', 'it', 'scientist', 'researcher'):
            deep.innovation_score = min(100, deep.innovation_score + random.uniform(0.1, 0.5))
        else:
            deep.innovation_score += random.uniform(-0.1, 0.2)
        deep.innovation_score = max(0, min(100, deep.innovation_score))

    # ---- P2-5: 国际贸易（全局） ----
    def _sim_international_trade(self, month, pop, events):
        # 简化：汇率/物价随机波动
        self._exchange_rate *= random.uniform(0.98, 1.02)
        self._price_index *= random.uniform(0.995, 1.01)
        # 季度性波动
        if month % 3 == 0:
            shock = random.uniform(-0.03, 0.03)
            self._price_index *= (1 + shock)
            if abs(shock) > 0.02:
                events.append({'type': 'trade_shock', 'detail': f'price index shift {shock:+.3f}',
                               'price_index': self._price_index, 'exchange_rate': self._exchange_rate})

    # ---- P2-6: 环境生态 ----
    def _sim_environment(self, ag, deep, micro, income, edu, events):
        # 碳足迹随收入增加
        deep.carbon_footprint = max(1, 5 + income / 5000 + random.uniform(-0.5, 0.5))
        # 环保意识随教育提升
        deep.environmental_awareness = min(100, max(0, 30 + edu * 3 + random.uniform(-1, 1)))
        # 回收习惯概率
        if not deep.recycling_habit and deep.environmental_awareness > 60:
            if random.random() < 0.02:
                deep.recycling_habit = True
                events.append({'type': 'start_recycling', 'agent_id': ag['id']})
        # 回收减少碳足迹
        if deep.recycling_habit:
            deep.carbon_footprint *= 0.95

    # ---- P2-7: 交通运输 ----
    def _sim_transportation(self, ag, deep, micro, city, events):
        # 通勤时间随城市规模变化（简化用城市名hash）
        city_factor = (hash(city) % 5) * 0.1 + 0.5  # 0.5~0.9
        micro.commute_hours_daily = max(0.2, min(3.0, city_factor + random.uniform(-0.1, 0.1)))
        # 长通勤 → 增加压力，降低幸福
        if micro.commute_hours_daily > 1.5:
            micro.stress_level += 0.5
            micro.happiness_level -= 0.3
        elif micro.commute_hours_daily < 0.5:
            micro.happiness_level += 0.2

    # ---- P2-8: 军事国防 ----
    def _sim_military(self, ag, deep, micro, age, gender, month, events):
        # 简化征兵：18-25 岁男性每年有小概率被征召
        if gender == 'male' and 18 <= age <= 25:
            if random.random() < 0.002:  # ~2.4%/年
                micro.stress_level += 10
                micro.happiness_level -= 5
                ag['military_service'] = True
                events.append({'type': 'conscription', 'agent_id': ag['id'], 'detail': f'age {age}'})
        # 服役中每月压力小幅回升（适应）
        if ag.get('military_service'):
            ag['military_months'] = ag.get('military_months', 0) + 1
            micro.stress_level = max(micro.stress_level - 0.5, 30)
            if ag['military_months'] >= 24:
                ag['military_service'] = False
                ag['military_months'] = 0
                events.append({'type': 'military_discharge', 'agent_id': ag['id']})

    # ---- P3-9: 日常作息 ----
    def _sim_daily_routine(self, ag, micro, age, occ, events):
        # 睡眠时间（小时）
        if age < 18:
            ideal_sleep = 9
        elif age < 60:
            ideal_sleep = 7.5
        else:
            ideal_sleep = 7
        # 职业影响
        if occ in ('doctor', 'nurse', 'driver', 'security'):
            ideal_sleep -= 1  # 轮班工作者睡得少
        actual_sleep = ideal_sleep + random.uniform(-1, 0.5)
        # 睡眠不足影响健康
        if actual_sleep < 6:
            ag['health_score'] = ag.get('health_score', 70) - 0.5
            micro.stress_level += 0.5
        elif actual_sleep > 7:
            ag['health_score'] = ag.get('health_score', 70) + 0.1
        micro.daily_routine_regularity += random.uniform(-1, 1)
        micro.daily_routine_regularity = max(0, min(100, micro.daily_routine_regularity))

    # ---- P3-10: 饮食习惯 ----
    def _sim_diet(self, ag, micro, income, edu, events):
        # 饮食质量 = 基础 + 收入因子 + 教育因子
        income_factor = min(20, income / 1000)
        edu_factor = edu * 1.5
        micro.healthy_eating_score = max(10, min(100,
            40 + income_factor + edu_factor + random.uniform(-3, 3)))
        # 影响健康
        if micro.healthy_eating_score > 75:
            ag['health_score'] = ag.get('health_score', 70) + 0.3
        elif micro.healthy_eating_score < 35:
            ag['health_score'] = ag.get('health_score', 70) - 0.3

    # ---- P3-11: 购物行为 ----
    def _sim_shopping(self, ag, micro, income, openness, neuroticism, events):
        # 月消费 = 基础生活 + 冲动消费
        base_spending = income * 0.4
        impulse = income * 0.1 * micro.impulse_buying_tendency / 100
        # 高开放性 → 更多消费；高神经质 → 更多冲动消费
        impulse *= (1 + openness * 0.3 + neuroticism * 0.2)
        total_spending = base_spending + impulse + random.uniform(-200, 200)
        total_spending = max(0, total_spending)
        ag['net_worth'] = ag.get('net_worth', 0) - total_spending
        # 物价指数影响
        ag['net_worth'] -= total_spending * (self._price_index - 1) * 0.5
        if impulse > income * 0.15:
            events.append({'type': 'overspending', 'agent_id': ag['id'],
                           'detail': f'impulse={impulse:.0f}'})

    # ---- P3-12: 学习行为 ----
    def _sim_learning(self, ag, micro, deep, age, edu, events):
        # 自我提升概率随教育和年龄变化
        learn_drive = max(0, (edu / 20) * 0.6 + (1 - age / 80) * 0.4)
        micro.learning_hours_weekly = max(0, min(20,
            micro.learning_hours_weekly + learn_drive * random.uniform(-0.5, 1.0)))
        # 学习 > 5h/周 → 提升技能/科技采纳
        if micro.learning_hours_weekly > 5:
            deep.tech_adoption = min(100, deep.tech_adoption + 0.2)
            if random.random() < 0.05:
                micro.certifications += 1
                events.append({'type': 'certification', 'agent_id': ag['id'],
                               'detail': f'total={micro.certifications}'})

    # ---- P3-13: 迁移流动 ----
    def _sim_migration(self, ag, micro, age, income, employed, events):
        # 换城市概率
        base_prob = 0.003  # ~3.6%/年
        if not employed:
            base_prob += 0.005
        if income < 2000:
            base_prob += 0.003
        if age < 30:
            base_prob += 0.003
        elif age > 55:
            base_prob *= 0.3  # 老年人不太搬
        if random.random() < base_prob:
            old_city = ag.get('city', 'unknown')
            cities = ['Beijing', 'Shanghai', 'Shenzhen', 'Guangzhou', 'Hangzhou',
                      'Chengdu', 'Wuhan', 'Nanjing', 'Suzhou', 'Changsha']
            new_city = random.choice([c for c in cities if c != old_city] or cities)
            ag['city'] = new_city
            micro.loneliness_score = min(100, micro.loneliness_score + 15)  # 搬家增加孤独
            micro.social_support = max(0, micro.social_support - 10)
            micro.relocation_willingness *= 0.7
            events.append({'type': 'migration', 'agent_id': ag['id'],
                           'detail': f'{old_city} → {new_city}'})

    # ---- P3-14: 财富传承 ----
    def _sim_wealth_inheritance(self, ag, deep, micro, agents, events):
        # 老年人去世时（简化：>75 岁每月小概率死亡）
        age = ag.get('age', 30)
        if age < 75:
            return
        death_prob = 0.005 + (age - 75) * 0.002  # 75 岁 0.5%/月，85 岁 2.5%/月
        if random.random() < death_prob:
            ag['alive'] = False
            wealth = ag.get('net_worth', 0)
            children_ids = ag.get('children', [])
            if wealth > 0 and children_ids:
                share = wealth / len(children_ids)
                agents_map = {a['id']: a for a in agents}
                for cid in children_ids:
                    child = agents_map.get(cid)
                    if child and child.get('alive', True):
                        child['net_worth'] = child.get('net_worth', 0) + share
                        events.append({'type': 'inheritance', 'agent_id': cid,
                                       'detail': f'inherited {share:.0f} from agent {ag["id"]}'})
            events.append({'type': 'death', 'agent_id': ag['id'], 'detail': f'age {age}'})

    # ---- P3-15: 心理状态 ----
    def _sim_psychology(self, ag, micro, stress, income, events):
        aid = ag['id']
        # 焦虑概率
        anxiety_prob = 0.01
        if stress > 60:
            anxiety_prob += 0.03
        if income < 2000:
            anxiety_prob += 0.02
        if micro.social_support < 30:
            anxiety_prob += 0.02
        if random.random() < anxiety_prob:
            micro.stress_level += 5
            micro.happiness_level -= 3
            events.append({'type': 'anxiety_episode', 'agent_id': aid})
        # 抑郁概率
        depression_prob = 0.005
        if micro.loneliness_score > 60:
            depression_prob += 0.02
        if micro.happiness_level < 30:
            depression_prob += 0.02
        if random.random() < depression_prob:
            micro.happiness_level -= 8
            micro.life_satisfaction -= 5
            ag['health_score'] = ag.get('health_score', 70) - 2
            events.append({'type': 'depression_episode', 'agent_id': aid})
        # 自然恢复
        micro.happiness_level += random.uniform(-0.5, 1.0)
        micro.stress_level += random.uniform(-1.0, 0.5)

    # ---- P3-16: 人际关系 ----
    def _sim_social_relations(self, ag, micro, age, occ, events):
        # 社交圈变化
        if age < 25:
            micro.relationship_quality += random.uniform(-0.5, 1.0)  # 年轻人社交活跃
        elif age > 60:
            micro.relationship_quality += random.uniform(-1.0, 0.3)  # 老年人社交萎缩
        else:
            micro.relationship_quality += random.uniform(-0.3, 0.5)
        micro.relationship_quality = max(0, min(100, micro.relationship_quality))
        # 孤独感随社交质量反向变化
        if micro.relationship_quality > 70:
            micro.loneliness_score = max(0, micro.loneliness_score - 0.5)
        elif micro.relationship_quality < 30:
            micro.loneliness_score = min(100, micro.loneliness_score + 0.5)
        # 社会支持缓慢回复
        micro.social_support += random.uniform(-0.3, 0.5)
        micro.social_support = max(0, min(100, micro.social_support))

    # ---- P3-17: 社会认同 ----
    def _sim_social_identity(self, ag, deep, micro, income, edu, occ, events):
        # 社会阶层认同：收入 + 教育 + 职业综合
        income_tier = min(4, int(income / 5000))  # 0-4
        edu_tier = min(4, int(edu / 5))            # 0-4
        occ_tier = 2
        if occ in ('executive', 'manager', 'professor', 'doctor', 'lawyer'):
            occ_tier = 4
        elif occ in ('engineer', 'programmer', 'scientist', 'researcher'):
            occ_tier = 3
        elif occ in ('student', 'unemployed'):
            occ_tier = 1
        composite = (income_tier + edu_tier + occ_tier) / 3
        deep.identity_strength = max(20, min(100, composite * 20 + random.uniform(-2, 2)))
        # 更新社会认同标签
        labels = []
        if income > 15000:
            labels.append('upper_class')
        elif income > 8000:
            labels.append('middle_class')
        else:
            labels.append('working_class')
        if edu > 16:
            labels.append('highly_educated')
        deep.social_identity = labels

    # ---- P3-18: 风险行为 ----
    def _sim_risk_behavior(self, ag, deep, micro, stress, income, neuroticism, events):
        aid = ag['id']
        # 吸烟概率（每月开始/继续）
        smoke_prob = 0.005 + stress / 5000 + neuroticism * 0.01
        if income < 3000:
            smoke_prob += 0.005
        if random.random() < smoke_prob:
            ag['smoker'] = True
            ag['health_score'] = ag.get('health_score', 70) - 0.5
        # 饮酒
        drink_prob = 0.01 + stress / 3000
        if random.random() < drink_prob:
            ag['heavy_drinker'] = True
            ag['health_score'] = ag.get('health_score', 70) - 0.3
            if random.random() < 0.1:
                events.append({'type': 'alcohol_incident', 'agent_id': aid})
        # 赌博
        gamble_prob = 0.003 + neuroticism * 0.01
        if income < 2000:
            gamble_prob += 0.005
        if random.random() < gamble_prob:
            loss = random.uniform(100, income * 0.3) if income > 0 else random.uniform(100, 500)
            ag['net_worth'] = ag.get('net_worth', 0) - loss
            micro.stress_level += 3
            events.append({'type': 'gambling_loss', 'agent_id': aid, 'detail': f'lost {loss:.0f}'})

    # ================================================================
    #  旧版兼容方法（保留）
    # ================================================================

    def update_monthly(self, agent_id: int, age: int, income: float,
                      social_connections: int = 0, months_passed: int = 1) -> Dict:
        """月度更新"""
        events = []
        
        deep = self.deep_profiles.get(agent_id)
        micro = self.micro_profiles.get(agent_id)
        
        if not deep or not micro:
            return {}
        
        for _ in range(months_passed):
            # === 深层细节更新 ===
            
            # 1. 媒体消费影响
            if deep.social_media_hours_daily > 4:
                # 过度社交媒体使用影响心理健康
                micro.stress_level += 1
                micro.loneliness_score += 1
            
            if deep.media_consumption.get(MediaConsumptionType.NEWS, 0) > 60:
                # 大量新闻消费增加焦虑
                micro.stress_level += 0.5
            
            # 2. 宗教参与影响
            if deep.religiosity > 50 and deep.religious_attendance in ['monthly', 'weekly']:
                # 宗教参与增加社会支持
                micro.social_support += 1
                micro.life_satisfaction += 0.5
            
            # 3. 环境行为
            if deep.recycling_habit:
                deep.carbon_footprint *= 0.98  # 回收减少碳足迹
            
            # 4. 风险行为
            if deep.risk_tolerance in [RiskTolerance.HIGH, RiskTolerance.VERY_HIGH]:
                if random.random() < 0.1:
                    events.append({'type': 'risk_event', 'agent_id': agent_id})
            
            # === 微观行为更新 ===
            
            # 5. 作息规律性
            if micro.daily_routine_regularity > 70:
                micro.happiness_level += 0.3
                micro.stress_level -= 0.3
            
            # 6. 饮食习惯
            if micro.healthy_eating_score > 70:
                micro.happiness_level += 0.2
            elif micro.healthy_eating_score < 40:
                micro.stress_level += 0.3
            
            # 7. 购物行为
            if micro.impulse_buying_tendency > 50:
                # 冲动消费影响财务
                events.append({'type': 'impulse_spending', 'agent_id': agent_id})
            
            # 8. 学习行为
            if micro.learning_hours_weekly > 5:
                # 持续学习提升能力
                pass  # 在技能系统中体现
            
            # 9. 心理状态自然波动
            micro.happiness_level += random.gauss(0, 2)
            micro.stress_level += random.gauss(0, 3)
            
            # 社会连接影响心理
            if social_connections > 10:
                micro.loneliness_score -= 1
                micro.happiness_level += 0.5
            elif social_connections < 3:
                micro.loneliness_score += 1
            
            # 10. 约束范围
            for attr in ['stress_level', 'happiness_level', 'life_satisfaction', 
                        'loneliness_score', 'social_support']:
                value = getattr(micro, attr)
                setattr(micro, attr, max(0, min(100, value)))
        
        return {
            'agent_id': agent_id,
            'happiness': micro.happiness_level,
            'stress': micro.stress_level,
            'satisfaction': micro.life_satisfaction,
            'events': events,
        }
    
    def update_macro_monthly(self, population: int, economic_data: Dict) -> Dict:
        """月度宏观经济更新"""
        # 国际贸易
        self.export_volume = population * economic_data.get('avg_income', 5000) * 0.1
        self.import_volume = population * economic_data.get('avg_income', 5000) * 0.12
        self.trade_balance = self.export_volume - self.import_volume
        
        # 环境
        if self.deep_profiles:
            self.avg_carbon_footprint = sum(p.carbon_footprint for p in self.deep_profiles.values()) / len(self.deep_profiles)
            self.recycling_rate = sum(1 for p in self.deep_profiles.values() if p.recycling_habit) / len(self.deep_profiles)
        
        # 交通
        if self.micro_profiles:
            self.avg_commute_time = sum(m.commute_hours_daily for m in self.micro_profiles.values()) / len(self.micro_profiles) * 60
            self.public_transit_usage = random.uniform(0.15, 0.35)
        
        # 军事（GDP 的 2-4%）
        gdp = population * economic_data.get('avg_income', 5000) * 12
        self.defense_budget = gdp * random.uniform(0.02, 0.04) / 12
        
        return {
            'trade_balance': self.trade_balance,
            'export_volume': self.export_volume,
            'import_volume': self.import_volume,
            'avg_carbon_footprint': self.avg_carbon_footprint,
            'recycling_rate': self.recycling_rate,
            'avg_commute_time': self.avg_commute_time,
            'public_transit_usage': self.public_transit_usage,
            'defense_budget': self.defense_budget,
        }
    
    def get_statistics(self) -> Dict:
        """获取统计"""
        deep_stats = {}
        micro_stats = {}
        
        if self.deep_profiles:
            profiles = list(self.deep_profiles.values())
            deep_stats = {
                'avg_religiosity': sum(p.religiosity for p in profiles) / len(profiles),
                'avg_tech_adoption': sum(p.tech_adoption for p in profiles) / len(profiles),
                'avg_environmental_awareness': sum(p.environmental_awareness for p in profiles) / len(profiles),
                'risk_distribution': {
                    rt.value: sum(1 for p in profiles if p.risk_tolerance == rt)
                    for rt in RiskTolerance
                },
                'religion_distribution': {
                    r.value: sum(1 for p in profiles if p.religion == r)
                    for r in ReligionType
                },
            }
        
        if self.micro_profiles:
            profiles = list(self.micro_profiles.values())
            micro_stats = {
                'avg_stress': sum(p.stress_level for p in profiles) / len(profiles),
                'avg_happiness': sum(p.happiness_level for p in profiles) / len(profiles),
                'avg_satisfaction': sum(p.life_satisfaction for p in profiles) / len(profiles),
                'avg_learning_hours': sum(p.learning_hours_weekly for p in profiles) / len(profiles),
                'avg_screen_time': sum(p.screen_time_hours_daily for p in profiles) / len(profiles),
            }
        
        return {
            'deep_profiles': len(self.deep_profiles),
            'micro_profiles': len(self.micro_profiles),
            'deep_stats': deep_stats,
            'micro_stats': micro_stats,
            'macro': {
                'trade_balance': self.trade_balance,
                'avg_carbon_footprint': self.avg_carbon_footprint,
                'recycling_rate': self.recycling_rate,
                'avg_commute_time': self.avg_commute_time,
                'defense_budget': self.defense_budget,
            }
        }


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("深层细节与微观行为系统测试")
    print("=" * 60)
    
    system = DeepMicroSystem()
    
    # 创建测试 Agent
    test_agents = [
        {'id': 1, 'age': 25, 'income': 5000, 'occupation': 'engineer'},
        {'id': 2, 'age': 35, 'income': 10000, 'occupation': 'manager'},
        {'id': 3, 'age': 50, 'income': 15000, 'occupation': 'executive'},
        {'id': 4, 'age': 22, 'income': 2000, 'occupation': 'student'},
    ]
    
    print(f"\n创建档案:")
    for agent in test_agents:
        deep = system.create_deep_profile(agent['id'], agent['age'], agent['income'])
        micro = system.create_micro_profile(agent['id'], agent['age'], agent['occupation'])
        
        print(f"  Agent {agent['id']} ({agent['age']}岁, {agent['occupation']}):")
        print(f"    深层：技术采纳{deep.tech_adoption:.0f}, 风险{deep.risk_tolerance.value}")
        print(f"    微观：压力{micro.stress_level:.0f}, 幸福{micro.happiness_level:.0f}, 学习{micro.learning_hours_weekly:.1f}h/周")
    
    # 模拟 6 个月
    print(f"\n模拟 6 个月...")
    for month in range(6):
        for agent in test_agents:
            system.update_monthly(agent['id'], agent['age'], agent['income'], 
                                 social_connections=random.randint(3, 15))
        
        if (month + 1) % 2 == 0:
            macro = system.update_macro_monthly(10000, {'avg_income': 6000})
            print(f"  第{month+1}月：贸易差额${macro['trade_balance']:,.0f}, "
                  f"人均碳足迹{macro['avg_carbon_footprint']:.1f}吨，"
                  f"平均通勤{macro['avg_commute_time']:.0f}分钟")
    
    # 统计
    stats = system.get_statistics()
    print(f"\n统计:")
    if stats['deep_stats']:
        print(f"  平均技术采纳：{stats['deep_stats']['avg_tech_adoption']:.0f}")
        print(f"  平均宗教虔诚：{stats['deep_stats']['avg_religiosity']:.0f}")
    if stats['micro_stats']:
        print(f"  平均压力：{stats['micro_stats']['avg_stress']:.0f}")
        print(f"  平均幸福：{stats['micro_stats']['avg_happiness']:.0f}")
        print(f"  平均学习：{stats['micro_stats']['avg_learning_hours']:.1f}h/周")
    print(f"  贸易差额：${stats['macro']['trade_balance']:,.0f}")
    print(f"  回收率：{stats['macro']['recycling_rate']*100:.1f}%")
    
    print("\n✅ 深层细节与微观行为系统测试完成!")
    print("\n📊 全部 25+ 系统完成状态:")
    print("   ✅ P0 核心社会结构 (5 系统)")
    print("   ✅ P1 公共服务 (3 系统)")
    print("   ✅ P2 深层细节 (8 系统)")
    print("   ✅ P3 微观行为 (10 系统)")
    print("   🎯 总计：26 个子系统，约 150KB 代码")
