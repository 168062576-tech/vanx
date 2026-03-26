"""
社交网络系统 - Social Network System

模拟真实的社会关系和信息传播：
- 朋友关系/熟人/陌生人
- 社交影响力/人气度
- 信息传播/舆论形成
- 社交活动/聚会
- 社交资本/人脉资源

作者：御龙军
日期：2026-03-17
版本：v1.0
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
from enum import Enum


class RelationshipLevel(Enum):
    """关系等级"""
    STRANGER = "stranger"  # 陌生人
    ACQUAINTANCE = "acquaintance"  # 熟人
    FRIEND = "friend"  # 朋友
    CLOSE_FRIEND = "close_friend"  # 密友
    BEST_FRIEND = "best_friend"  # 挚友
    FAMILY = "family"  # 家人
    COLLEAGUE = "colleague"  # 同事
    PARTNER = "partner"  # 伴侣


class PersonalityType(Enum):
    """性格类型（社交维度）"""
    INTROVERT = "introvert"  # 内向
    AMBIVERT = "ambivert"  # 中间
    EXTROVERT = "extrovert"  # 外向


@dataclass
class SocialConnection:
    """社交连接"""
    person1_id: int
    person2_id: int
    relationship_level: RelationshipLevel = RelationshipLevel.STRANGER
    trust_level: float = 0.0  # 0-100
    closeness: float = 0.0  # 0-100
    interaction_frequency: float = 0.0  # 次/月
    last_interaction: Optional[datetime] = None
    connection_date: datetime = field(default_factory=datetime.now)
    
    # 社交资本
    favors_owed: Dict[int, int] = field(default_factory=dict)  # {person_id: count}
    shared_secrets: int = 0
    shared_experiences: int = 0


@dataclass
class SocialProfile:
    """社交档案"""
    agent_id: int
    
    # 性格
    personality: PersonalityType = PersonalityType.AMBIVERT
    extraversion_score: float = 50.0  # 0-100
    
    # 社交指标
    popularity: float = 50.0  # 人气度 0-100
    influence: float = 30.0  # 影响力 0-100
    reputation: float = 50.0  # 声誉 0-100
    
    # 社交能力
    communication_skill: float = 50.0  # 沟通能力
    empathy: float = 50.0  # 共情能力
    leadership: float = 30.0  # 领导力
    
    # 社交网络统计
    total_connections: int = 0
    close_friends: int = 0
    acquaintances: int = 0
    
    # 社交活动
    social_events_attended: int = 0
    events_hosted: int = 0
    
    # 在线社交
    social_media_followers: int = 0
    online_presence: float = 0.0  # 0-100


@dataclass
class SocialEvent:
    """社交活动"""
    event_id: int
    host_id: int
    event_type: str  # party/dinner/meeting/networking/etc
    date: datetime
    location: str
    attendees: List[int] = field(default_factory=list)
    max_capacity: int = 20
    satisfaction_avg: float = 0.0


class SocialNetworkSystem:
    """社交网络系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.profiles: Dict[int, SocialProfile] = {}
        self.connections: Dict[Tuple[int, int], SocialConnection] = {}
        self.events: List[SocialEvent] = []
        self.event_id_counter = 1
        
        # 信息传播
        self.active_information: Dict[str, Dict] = {}  # {info_id: {content, spreaders, reach}}
        
        # 社交参数
        self.max_dunbar_number = 150  # 邓巴数字上限
        self.close_circle_size = 15  # 核心圈子
        self.avg_friendship_duration_months = 60  # 平均友谊持续时间
    
    def create_profile(self, agent_id: int, age: int, 
                      personality: PersonalityType = None) -> SocialProfile:
        """创建社交档案"""
        if personality is None:
            # 根据年龄和随机分配性格
            if age < 25:
                extraversion = random.gauss(55, 20)
            elif age > 50:
                extraversion = random.gauss(45, 20)
            else:
                extraversion = random.gauss(50, 20)
            
            extraversion = max(0, min(100, extraversion))
            
            if extraversion < 35:
                personality = PersonalityType.INTROVERT
            elif extraversion > 65:
                personality = PersonalityType.EXTROVERT
            else:
                personality = PersonalityType.AMBIVERT
        else:
            if personality == PersonalityType.INTROVERT:
                extraversion = random.gauss(25, 10)
            elif personality == PersonalityType.EXTROVERT:
                extraversion = random.gauss(75, 10)
            else:
                extraversion = random.gauss(50, 15)
        
        profile = SocialProfile(
            agent_id=agent_id,
            personality=personality,
            extraversion_score=extraversion,
            popularity=50 + random.gauss(0, 15),
            influence=30 + random.gauss(0, 15),
            communication_skill=40 + random.gauss(0, 20),
            empathy=50 + random.gauss(0, 20),
        )
        
        self.profiles[agent_id] = profile
        return profile
    
    def create_connection(self, id1: int, id2: int, 
                         initial_level: RelationshipLevel = RelationshipLevel.STRANGER) -> SocialConnection:
        """创建社交连接"""
        key = tuple(sorted([id1, id2]))
        
        if key in self.connections:
            return self.connections[key]
        
        connection = SocialConnection(
            person1_id=id1,
            person2_id=id2,
            relationship_level=initial_level,
            trust_level=random.uniform(10, 40),
            closeness=random.uniform(5, 30),
        )
        
        self.connections[key] = connection
        
        # 更新档案统计
        self._update_profile_stats(id1)
        self._update_profile_stats(id2)
        
        return connection
    
    def interact(self, id1: int, id2: int, interaction_type: str = "casual",
                quality: float = None) -> Dict:
        """两人互动"""
        key = tuple(sorted([id1, id2]))
        
        if key not in self.connections:
            # 陌生人先建立连接
            self.create_connection(id1, id2, RelationshipLevel.ACQUAINTANCE)
        
        connection = self.connections[key]
        
        # 互动质量（-1 到 1）
        if quality is None:
            # 基于性格匹配和现有关系
            profile1 = self.profiles.get(id1)
            profile2 = self.profiles.get(id2)
            
            if profile1 and profile2:
                # 性格相似度高，互动质量好
                similarity = 1 - abs(profile1.extraversion_score - profile2.extraversion_score) / 100
                quality = random.gauss(similarity * 0.5, 0.3)
            else:
                quality = random.gauss(0, 0.3)
        
        quality = max(-1, min(1, quality))
        
        # 更新关系
        connection.closeness += quality * 5
        connection.trust_level += quality * 3
        connection.interaction_frequency += 1
        connection.last_interaction = datetime.now()
        connection.shared_experiences += 1
        
        # 关系升级
        self._update_relationship_level(connection)
        
        # 更新档案
        if id1 in self.profiles:
            self.profiles[id1].social_events_attended += 1
        if id2 in self.profiles:
            self.profiles[id2].social_events_attended += 1
        
        self._update_profile_stats(id1)
        self._update_profile_stats(id2)
        
        return {
            'quality': quality,
            'new_closeness': connection.closeness,
            'new_trust': connection.trust_level,
            'relationship_level': connection.relationship_level.value,
        }
    
    def _update_relationship_level(self, connection: SocialConnection):
        """更新关系等级"""
        closeness = connection.closeness
        trust = connection.trust_level
        combined = (closeness + trust) / 2
        
        if combined >= 90:
            connection.relationship_level = RelationshipLevel.BEST_FRIEND
        elif combined >= 70:
            connection.relationship_level = RelationshipLevel.CLOSE_FRIEND
        elif combined >= 50:
            connection.relationship_level = RelationshipLevel.FRIEND
        elif combined >= 30:
            connection.relationship_level = RelationshipLevel.ACQUAINTANCE
        else:
            connection.relationship_level = RelationshipLevel.STRANGER
    
    def _update_profile_stats(self, agent_id: int):
        """更新档案统计"""
        if agent_id not in self.profiles:
            return
        
        profile = self.profiles[agent_id]
        
        # 统计连接
        total = 0
        close = 0
        acquaintances = 0
        
        for (id1, id2), conn in self.connections.items():
            if agent_id in [id1, id2]:
                total += 1
                if conn.relationship_level in [RelationshipLevel.CLOSE_FRIEND, RelationshipLevel.BEST_FRIEND]:
                    close += 1
                elif conn.relationship_level == RelationshipLevel.ACQUAINTANCE:
                    acquaintances += 1
        
        profile.total_connections = total
        profile.close_friends = close
        profile.acquaintances = acquaintances
        
        # 人气度基于连接数和质量
        profile.popularity = min(100, total * 2 + close * 5)
        
        # 影响力基于人气和领导力
        profile.influence = (profile.popularity * 0.6 + profile.leadership * 0.4)
    
    def host_event(self, host_id: int, event_type: str, 
                   guest_list: List[int], location: str = "Home") -> SocialEvent:
        """举办社交活动"""
        event = SocialEvent(
            event_id=self.event_id_counter,
            host_id=host_id,
            event_type=event_type,
            date=datetime.now(),
            location=location,
            attendees=guest_list[:20],  # 最多 20 人
            max_capacity=20,
        )
        
        self.events.append(event)
        self.event_id_counter += 1
        
        # 更新主办者档案
        if host_id in self.profiles:
            self.profiles[host_id].events_hosted += 1
            self.profiles[host_id].popularity += 2
        
        # 参与者之间产生互动
        for i, guest1 in enumerate(event.attendees):
            for guest2 in event.attendees[i+1:]:
                if random.random() < 0.7:  # 70% 概率互动
                    self.interact(guest1, guest2, "event")
        
        return event
    
    def spread_information(self, info_id: str, content: str, 
                          starter_id: int, agents: List[int]) -> Dict:
        """传播信息"""
        if info_id not in self.active_information:
            self.active_information[info_id] = {
                'content': content,
                'starter': starter_id,
                'spreaders': {starter_id},
                'reach': {starter_id},
                'start_date': datetime.now(),
            }
        
        info = self.active_information[info_id]
        new_reach = set()
        
        # 信息从已知者传播给他们的连接
        for spreader_id in list(info['spreaders']):
            spreader_profile = self.profiles.get(spreader_id)
            if not spreader_profile:
                continue
            
            # 影响力高的人传播更广
            spread_probability = 0.1 + spreader_profile.influence / 200
            
            for agent_id in agents:
                if agent_id in info['reach']:
                    continue
                
                # 检查是否有连接
                key = tuple(sorted([spreader_id, agent_id]))
                if key in self.connections:
                    conn = self.connections[key]
                    # 关系越亲密，传播概率越高
                    prob = spread_probability * (1 + conn.closeness / 50)
                    
                    if random.random() < prob:
                        info['spreaders'].add(agent_id)
                        info['reach'].add(agent_id)
                        new_reach.add(agent_id)
        
        return {
            'info_id': info_id,
            'total_reach': len(info['reach']),
            'new_reach': len(new_reach),
            'spreaders': len(info['spreaders']),
        }
    
    def update_monthly(self, agents: List[int], months_passed: int = 1):
        """月度更新"""
        for _ in range(months_passed):
            for agent_id in agents:
                profile = self.profiles.get(agent_id)
                if not profile:
                    continue
                
                # 1. 关系自然衰减
                self._decay_relationships(agent_id)
                
                # 2. 主动社交（外向者更活跃）
                social_drive = profile.extraversion_score / 100
                if random.random() < social_drive * 0.5:
                    self._initiate_social_activity(agent_id, agents)
                
                # 3. 人气自然变化
                if profile.total_connections > 0:
                    profile.popularity += random.gauss(0.5, 2)
                else:
                    profile.popularity -= 1
                profile.popularity = max(0, min(100, profile.popularity))
    
    def _decay_relationships(self, agent_id: int):
        """关系衰减"""
        for (id1, id2), conn in self.connections.items():
            if agent_id not in [id1, id2]:
                continue
            
            # 长时间不互动，关系衰减
            if conn.last_interaction:
                months_since = (datetime.now() - conn.last_interaction).days / 30
                if months_since > 3:
                    conn.closeness -= months_since * 0.5
                    conn.trust_level -= months_since * 0.3
    
    def _initiate_social_activity(self, agent_id: int, agents: List[int]):
        """发起社交活动"""
        profile = self.profiles.get(agent_id)
        if not profile:
            return
        
        # 选择一些朋友/熟人
        potential_guests = []
        for (id1, id2), conn in self.connections.items():
            if agent_id in [id1, id2]:
                other_id = id2 if id1 == agent_id else id1
                if conn.relationship_level != RelationshipLevel.STRANGER:
                    potential_guests.append(other_id)
        
        if potential_guests:
            # 随机选择一些客人
            guest_count = min(len(potential_guests), random.randint(2, 8))
            guests = random.sample(potential_guests, guest_count)
            
            # 举办活动
            event_types = ["dinner", "party", "game_night", "coffee"]
            self.host_event(agent_id, random.choice(event_types), guests)
    
    def get_social_statistics(self) -> Dict:
        """获取社交统计"""
        if not self.profiles:
            return {}
        
        profiles = list(self.profiles.values())
        
        return {
            'total_agents': len(profiles),
            'total_connections': len(self.connections),
            'avg_connections_per_person': len(self.connections) * 2 / len(profiles),
            'avg_popularity': sum(p.popularity for p in profiles) / len(profiles),
            'avg_influence': sum(p.influence for p in profiles) / len(profiles),
            'total_events': len(self.events),
            'active_information': len(self.active_information),
            'personality_distribution': {
                'introvert': sum(1 for p in profiles if p.personality == PersonalityType.INTROVERT),
                'ambivert': sum(1 for p in profiles if p.personality == PersonalityType.AMBIVERT),
                'extrovert': sum(1 for p in profiles if p.personality == PersonalityType.EXTROVERT),
            }
        }


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("社交网络系统测试")
    print("=" * 60)
    
    system = SocialNetworkSystem()
    
    # 创建测试 Agent
    test_agents = [
        {'id': 1, 'age': 25},
        {'id': 2, 'age': 30},
        {'id': 3, 'age': 28},
        {'id': 4, 'age': 35},
        {'id': 5, 'age': 22},
    ]
    
    print(f"\n创建社交档案:")
    for agent in test_agents:
        profile = system.create_profile(agent['id'], agent['age'])
        print(f"  Agent {agent['id']} ({agent['age']}岁):")
        print(f"    性格：{profile.personality.value}, 外向度：{profile.extraversion_score:.1f}")
        print(f"    人气：{profile.popularity:.1f}, 影响力：{profile.influence:.1f}")
    
    # 创建一些连接
    print(f"\n建立社交连接:")
    system.create_connection(1, 2, RelationshipLevel.FRIEND)
    system.create_connection(1, 3, RelationshipLevel.CLOSE_FRIEND)
    system.create_connection(2, 3, RelationshipLevel.ACQUAINTANCE)
    system.create_connection(2, 4, RelationshipLevel.FRIEND)
    system.create_connection(3, 5, RelationshipLevel.FRIEND)
    system.create_connection(4, 5, RelationshipLevel.ACQUAINTANCE)
    
    # 互动
    print(f"\n社交互动:")
    result = system.interact(1, 2, "casual", quality=0.8)
    print(f"  Agent 1 & 2 互动：质量{result['quality']:.2f}, 亲密度→{result['new_closeness']:.1f}")
    
    result = system.interact(3, 5, "deep_talk", quality=0.9)
    print(f"  Agent 3 & 5 深谈：质量{result['quality']:.2f}, 关系→{result['relationship_level']}")
    
    # 举办活动
    print(f"\n举办活动:")
    event = system.host_event(1, "dinner_party", [2, 3, 4], "Home")
    print(f"  Agent 1 举办晚宴，{len(event.attendees)}人参加")
    
    # 模拟 6 个月
    print(f"\n模拟 6 个月...")
    agent_ids = [a['id'] for a in test_agents]
    for month in range(6):
        system.update_monthly(agent_ids)
    
    # 信息传播测试
    print(f"\n信息传播测试:")
    result = system.spread_information("news_001", "公司要涨工资了！", 1, agent_ids)
    print(f"  信息\"{result['info_id']}\"传播：覆盖{result['total_reach']}人，新增{result['new_reach']}人")
    
    # 统计
    stats = system.get_social_statistics()
    print(f"\n社交统计:")
    print(f"  总连接数：{stats['total_connections']}")
    print(f"  人均连接：{stats['avg_connections_per_person']:.1f}")
    print(f"  平均人气：{stats['avg_popularity']:.1f}")
    print(f"  平均影响力：{stats['avg_influence']:.1f}")
    print(f"  举办活动：{stats['total_events']}次")
    
    print("\n✅ 社交网络系统测试完成!")
