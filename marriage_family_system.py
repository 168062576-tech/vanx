"""
婚姻家庭系统 - Marriage & Family System

模拟真实的婚姻家庭关系：
- 恋爱/结婚/离婚/再婚
- 子女抚养/单亲家庭/同性婚姻
- 家庭资产/家庭决策/家务分配
- 婚姻满意度/离婚率/结婚年龄

作者：御龙军
日期：2026-03-17
版本：v1.0
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta


@dataclass
class Relationship:
    """关系对象 - 记录两人之间的关系"""
    person1_id: int
    person2_id: int
    relationship_type: str  # "single", "dating", "engaged", "married", "divorced", "widowed"
    start_date: Optional[datetime] = None
    marriage_date: Optional[datetime] = None
    divorce_date: Optional[datetime] = None
    satisfaction: float = 5.0  # 1-10 分
    compatibility: float = 0.5  # 0-1 匹配度
    
    # 关系动态
    love_level: float = 5.0  # 爱情水平 1-10
    trust_level: float = 5.0  # 信任水平 1-10
    communication_quality: float = 5.0  # 沟通质量 1-10
    
    # 共同资产
    joint_assets: float = 0.0  # 共同资产
    joint_debts: float = 0.0  # 共同债务
    
    def __post_init__(self):
        if self.start_date is None:
            self.start_date = datetime.now()


@dataclass
class Family:
    """家庭对象"""
    family_id: int
    family_type: str  # "single", "couple", "nuclear", "single_parent", "extended", "blended"
    members: List[int] = field(default_factory=list)  # Agent IDs
    children: List[int] = field(default_factory=list)  # 子女 IDs
    assets: float = 0.0  # 家庭总资产
    debts: float = 0.0  # 家庭总债务
    monthly_income: float = 0.0  # 家庭月收入
    monthly_expenses: float = 0.0  # 家庭月支出
    housing_type: str = "rent"  # "rent", "own", "mortgage"
    
    # 家庭决策
    decision_maker: int = 0  # 主要决策者 ID
    household_division: Dict[str, int] = field(default_factory=dict)  # 家务分配
    
    # 家庭文化
    values: Dict[str, float] = field(default_factory=dict)  # 家庭价值观
    traditions: List[str] = field(default_factory=list)  # 家庭传统


class MarriageFamilySystem:
    """婚姻家庭系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.relationships: Dict[Tuple[int, int], Relationship] = {}
        self.families: Dict[int, Family] = {}
        self.family_id_counter = 1
        
        # 社会参数（可配置）
        self.min_marriage_age = self.config.get('min_marriage_age', 18)
        self.avg_marriage_age_male = self.config.get('avg_marriage_age_male', 28)
        self.avg_marriage_age_female = self.config.get('avg_marriage_age_female', 26)
        self.divorce_rate = self.config.get('divorce_rate', 0.4)  # 40% 离婚率
        self.remarriage_rate = self.config.get('remarriage_rate', 0.6)  # 60% 再婚率
        self.same_sex_marriage = self.config.get('same_sex_marriage', True)
        self.single_parent_rate = self.config.get('single_parent_rate', 0.15)  # 15% 单亲家庭
        
        # 恋爱参数
        self.dating_period_months = self.config.get('dating_period_months', 18)  # 平均恋爱 18 个月
        self.engagement_period_months = self.config.get('engagement_period_months', 12)  # 订婚 12 个月
        
    def get_relationship(self, id1: int, id2: int) -> Optional[Relationship]:
        """获取两人关系"""
        key = tuple(sorted([id1, id2]))
        return self.relationships.get(key)
    
    def create_relationship(self, id1: int, id2: int, relationship_type: str = "dating") -> Relationship:
        """创建关系"""
        key = tuple(sorted([id1, id2]))
        
        if key in self.relationships:
            return self.relationships[key]
        
        # 计算匹配度（基于性格、爱好、价值观）
        compatibility = self._calculate_compatibility(id1, id2)
        
        relationship = Relationship(
            person1_id=id1,
            person2_id=id2,
            relationship_type=relationship_type,
            satisfaction=5.0 + random.gauss(0, 1.5),
            compatibility=compatibility,
            love_level=5.0 + random.gauss(0, 1.5),
            trust_level=5.0 + random.gauss(0, 1.5),
            communication_quality=5.0 + random.gauss(0, 1.5)
        )
        
        self.relationships[key] = relationship
        return relationship
    
    def _calculate_compatibility(self, id1: int, id2: int) -> float:
        """计算两人匹配度（0-1）"""
        # TODO: 从 agent 数据获取性格、爱好、价值观
        # 简化版本：随机 + 少量基于特征
        base_compatibility = random.gauss(0.5, 0.15)
        
        # 性格互补加分（内向 + 外向）
        # 爱好相似加分
        # 价值观相似加分
        
        return max(0.0, min(1.0, base_compatibility))
    
    def update_relationship(self, id1: int, id2: int, months_passed: int = 1) -> str:
        """
        更新关系状态（每月调用）
        返回：关系变化事件（如 "married", "divorced", "breakup"）
        """
        key = tuple(sorted([id1, id2]))
        if key not in self.relationships:
            return "none"
        
        rel = self.relationships[key]
        event = "none"
        
        # 更新关系动态
        self._update_relationship_dynamics(rel, months_passed)
        
        # 关系进展逻辑
        if rel.relationship_type == "dating":
            # 恋爱 → 订婚 或 分手
            dating_months = (datetime.now() - rel.start_date).days / 30
            if dating_months >= self.dating_period_months:
                if rel.satisfaction >= 7.0 and rel.love_level >= 7.0:
                    rel.relationship_type = "engaged"
                    event = "engaged"
                elif rel.satisfaction < 4.0:
                    del self.relationships[key]
                    event = "breakup"
        
        elif rel.relationship_type == "engaged":
            # 订婚 → 结婚 或 分手
            engagement_months = (datetime.now() - rel.marriage_date).days / 30 if rel.marriage_date else 0
            if engagement_months >= self.engagement_period_months:
                if rel.satisfaction >= 6.5:
                    rel.relationship_type = "married"
                    rel.marriage_date = datetime.now()
                    event = "married"
                    self._create_family(id1, id2)
                elif rel.satisfaction < 4.0:
                    del self.relationships[key]
                    event = "breakup"
        
        elif rel.relationship_type == "married":
            # 婚姻维持或离婚
            if rel.satisfaction < 3.0:
                divorce_prob = self.divorce_rate * (3.0 - rel.satisfaction) / 3.0
                if random.random() < divorce_prob:
                    rel.relationship_type = "divorced"
                    rel.divorce_date = datetime.now()
                    event = "divorced"
                    self._handle_divorce(id1, id2)
        
        return event
    
    def _update_relationship_dynamics(self, rel: Relationship, months_passed: int):
        """更新关系动态（爱情、信任、沟通）"""
        for _ in range(months_passed):
            # 爱情水平：随时间自然衰减，但高质量关系衰减慢
            decay_rate = 0.02 if rel.satisfaction >= 7.0 else 0.05
            rel.love_level = max(1.0, rel.love_level * (1 - decay_rate))
            
            # 信任水平：基于沟通质量
            if rel.communication_quality >= 7.0:
                rel.trust_level = min(10.0, rel.trust_level + 0.05)
            else:
                rel.trust_level = max(1.0, rel.trust_level - 0.03)
            
            # 沟通质量：受满意度影响
            target_comm = rel.satisfaction * 0.8
            rel.communication_quality += (target_comm - rel.communication_quality) * 0.1
            
            # 满意度：综合因素
            rel.satisfaction = (
                rel.love_level * 0.3 +
                rel.trust_level * 0.3 +
                rel.communication_quality * 0.2 +
                rel.compatibility * 10 * 0.2
            )
    
    def _create_family(self, id1: int, id2: int) -> Family:
        """创建新家庭"""
        family = Family(
            family_id=self.family_id_counter,
            family_type="couple",
            members=[id1, id2],
            assets=self._get_agent_assets(id1) + self._get_agent_assets(id2),
            monthly_income=self._get_agent_income(id1) + self._get_agent_income(id2)
        )
        
        self.families[family.family_id] = family
        self.family_id_counter += 1
        
        return family
    
    def can_have_children(self, id1: int, id2: int, agents: Dict) -> Tuple[bool, str]:
        """检查是否可以生育子女"""
        agent1 = agents.get(id1, {})
        agent2 = agents.get(id2, {})
        
        # 同性伴侣无法自然生育
        if agent1.get('gender') == agent2.get('gender'):
            return False, "同性伴侣无法自然生育（可考虑领养）"
        
        # 年龄检查
        age1 = agent1.get('age', 0)
        age2 = agent2.get('age', 0)
        
        if age1 < 18 or age2 < 18:
            return False, "年龄不足 18 岁"
        
        # 女性生育年龄上限（医学建议）
        female_age = age1 if agent1.get('gender') == 'female' else age2
        if female_age > 45:
            return False, "超过自然生育年龄（可考虑领养）"
        
        return True, "可以生育"
    
    def _handle_divorce(self, id1: int, id2: int):
        """处理离婚：财产分割、子女抚养"""
        # 找到家庭
        family = None
        for f in self.families.values():
            if id1 in f.members and id2 in f.members:
                family = f
                break
        
        if family:
            # 财产平分
            family.assets /= 2
            family.debts /= 2
            family.monthly_income = self._get_agent_income(id1)
            
            # 子女抚养权（简化：主要给收入高的一方）
            if family.children:
                income1 = self._get_agent_income(id1)
                income2 = self._get_agent_income(id2)
                custodian = id1 if income1 > income2 else id2
                # TODO: 更新子女与父母的关系
    
    def _get_agent_assets(self, agent_id: int) -> float:
        """获取 Agent 资产（从主系统）"""
        # TODO: 从主系统获取
        return random.uniform(10000, 100000)
    
    def _get_agent_income(self, agent_id: int) -> float:
        """获取 Agent 收入（从主系统）"""
        # TODO: 从主系统获取
        return random.uniform(3000, 15000)
    
    def can_marry(self, agent1: dict, agent2: dict) -> Tuple[bool, str]:
        """检查是否可以结婚"""
        # 年龄检查
        if agent1.get('age', 0) < self.min_marriage_age:
            return False, f"年龄不足（最小{self.min_marriage_age}岁）"
        if agent2.get('age', 0) < self.min_marriage_age:
            return False, f"年龄不足（最小{self.min_marriage_age}岁）"
        
        # 现有关系检查
        for rel in self.relationships.values():
            if rel.relationship_type == "married":
                if agent1['id'] in [rel.person1_id, rel.person2_id]:
                    return False, "已已婚"
                if agent2['id'] in [rel.person1_id, rel.person2_id]:
                    return False, "已已婚"
        
        # 同性婚姻检查
        if agent1.get('gender') == agent2.get('gender'):
            if not self.same_sex_marriage:
                return False, "不支持同性婚姻"
        
        return True, "可以结婚"
    
    def get_family_statistics(self) -> Dict:
        """获取家庭统计"""
        total_families = len(self.families)
        if total_families == 0:
            return {}
        
        family_types = {}
        for f in self.families.values():
            family_types[f.family_type] = family_types.get(f.family_type, 0) + 1
        
        avg_assets = sum(f.assets for f in self.families.values()) / total_families
        avg_income = sum(f.monthly_income for f in self.families.values()) / total_families
        
        return {
            'total_families': total_families,
            'family_types': family_types,
            'avg_assets': avg_assets,
            'avg_income': avg_income,
            'divorce_rate': self.divorce_rate,
            'remarriage_rate': self.remarriage_rate
        }
    
    def generate_family_events(self, agents: List[dict], months_passed: int = 1) -> List[dict]:
        """生成家庭相关事件（结婚、离婚、生子等）"""
        events = []
        
        # 1. 更新现有关系
        for (id1, id2), rel in list(self.relationships.items()):
            event = self.update_relationship(id1, id2, months_passed)
            if event != "none":
                events.append({
                    'type': f'relationship_{event}',
                    'agents': [id1, id2],
                    'details': {'relationship_type': rel.relationship_type}
                })
        
        # 2. 新恋爱关系（适龄单身 Agent）
        single_agents = [a for a in agents if self._is_single(a['id']) and a.get('age', 0) >= 18]
        if len(single_agents) >= 2:
            # 每月有一定概率开始新恋情
            dating_prob = 0.05 * months_passed  # 5% 每月
            if random.random() < dating_prob:
                # 选择两个随机单身 Agent
                new_couple = random.sample(single_agents, min(2, len(single_agents)))
                if len(new_couple) == 2:
                    self.create_relationship(new_couple[0]['id'], new_couple[1]['id'])
                    events.append({
                        'type': 'relationship_started',
                        'agents': [new_couple[0]['id'], new_couple[1]['id']],
                        'details': {'relationship_type': 'dating'}
                    })
        
        return events
    
    def _is_single(self, agent_id: int) -> bool:
        """检查 Agent 是否单身"""
        for rel in self.relationships.values():
            if rel.relationship_type in ['dating', 'engaged', 'married']:
                if agent_id in [rel.person1_id, rel.person2_id]:
                    return False
        return True


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("婚姻家庭系统测试")
    print("=" * 60)
    
    system = MarriageFamilySystem({
        'min_marriage_age': 18,
        'divorce_rate': 0.35,
        'same_sex_marriage': True
    })
    
    # 创建测试 Agent
    agents = [
        {'id': 1, 'age': 25, 'gender': 'male'},
        {'id': 2, 'age': 24, 'gender': 'female'},
        {'id': 3, 'age': 30, 'gender': 'male'},
        {'id': 4, 'age': 28, 'gender': 'female'},
    ]
    
    # 创建恋爱关系
    rel1 = system.create_relationship(1, 2, "dating")
    rel2 = system.create_relationship(3, 4, "engaged")
    
    print(f"\n初始关系:")
    print(f"  Agent 1 & 2: {rel1.relationship_type} (满意度：{rel1.satisfaction:.1f})")
    print(f"  Agent 3 & 4: {rel2.relationship_type} (满意度：{rel2.satisfaction:.1f})")
    
    # 模拟 24 个月
    print(f"\n模拟 24 个月...")
    for month in range(24):
        for (id1, id2), rel in list(system.relationships.items()):
            event = system.update_relationship(id1, id2)
            if event != "none":
                print(f"  第{month+1}月：Agent {id1} & {id2} {event}")
    
    # 统计
    stats = system.get_family_statistics()
    print(f"\n家庭统计:")
    print(f"  总家庭数：{stats.get('total_families', 0)}")
    print(f"  平均资产：${stats.get('avg_assets', 0):,.0f}")
    print(f"  平均月收入：${stats.get('avg_income', 0):,.0f}")
    
    print("\n✅ 婚姻家庭系统测试完成!")
