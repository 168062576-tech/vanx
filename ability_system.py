"""
御龙军虚拟 Agent 世界 - 三层能力系统 (AbilitySystem)

Layer 1: 基础天赋 (8维, 1-10, 正态分布)
Layer 2: 可成长技能 (7大类 35+ 技能, S型成长曲线)
Layer 3: 稀有特质 (16种, 概率触发)
+ MBTI 性格系统

作者：御龙军执行司
日期：2026-03-25
版本：v1.0
"""

import math
import random
from typing import Dict, List, Optional, Tuple


# ============================================================
# 常量与配置
# ============================================================

TALENT_DIMS = ['logical', 'creative', 'social', 'physical', 'musical',
               'emotional', 'spatial', 'linguistic']

# 技能定义: skill_name -> {category, decay_rate, talents: [(dim, weight)]}
SKILL_DEFS: Dict[str, dict] = {}

_SKILL_RAW = {
    'academic': {
        'decay': 0.02,
        'skills': {
            '数学':   [('logical', 0.7), ('spatial', 0.3)],
            '物理':   [('logical', 0.5), ('spatial', 0.3), ('creative', 0.2)],
            '化学':   [('logical', 0.5), ('spatial', 0.2), ('creative', 0.3)],
            '生物':   [('logical', 0.4), ('emotional', 0.3), ('creative', 0.3)],
            '历史':   [('linguistic', 0.5), ('emotional', 0.3), ('logical', 0.2)],
            '文学':   [('linguistic', 0.6), ('emotional', 0.3), ('creative', 0.1)],
            '外语':   [('linguistic', 0.6), ('social', 0.2), ('logical', 0.2)],
        }
    },
    'technical': {
        'decay': 0.03,
        'skills': {
            '编程':     [('logical', 0.6), ('creative', 0.2), ('spatial', 0.2)],
            '数据分析': [('logical', 0.6), ('spatial', 0.2), ('creative', 0.2)],
            '机械设计': [('spatial', 0.5), ('logical', 0.3), ('physical', 0.2)],
            '电子工程': [('logical', 0.5), ('spatial', 0.3), ('creative', 0.2)],
            '生物技术': [('logical', 0.4), ('creative', 0.3), ('emotional', 0.3)],
        }
    },
    'business': {
        'decay': 0.025,
        'skills': {
            '财务管理': [('logical', 0.6), ('linguistic', 0.2), ('emotional', 0.2)],
            '市场营销': [('social', 0.4), ('creative', 0.3), ('linguistic', 0.3)],
            '项目管理': [('logical', 0.4), ('social', 0.3), ('emotional', 0.3)],
            '战略规划': [('logical', 0.5), ('creative', 0.3), ('spatial', 0.2)],
            '谈判':     [('social', 0.4), ('emotional', 0.3), ('linguistic', 0.3)],
        }
    },
    'social': {
        'decay': 0.015,
        'skills': {
            '沟通':     [('social', 0.4), ('emotional', 0.3), ('linguistic', 0.3)],
            '领导力':   [('social', 0.4), ('emotional', 0.3), ('logical', 0.3)],
            '团队协作': [('social', 0.4), ('emotional', 0.4), ('logical', 0.2)],
            '客户服务': [('social', 0.4), ('emotional', 0.4), ('linguistic', 0.2)],
            '公共演讲': [('social', 0.3), ('linguistic', 0.4), ('emotional', 0.3)],
        }
    },
    'creative': {
        'decay': 0.02,
        'skills': {
            '设计':     [('creative', 0.5), ('spatial', 0.3), ('emotional', 0.2)],
            '写作':     [('linguistic', 0.4), ('creative', 0.4), ('emotional', 0.2)],
            '艺术创作': [('creative', 0.5), ('emotional', 0.3), ('spatial', 0.2)],
            '视频制作': [('creative', 0.4), ('spatial', 0.3), ('logical', 0.3)],
            '音乐创作': [('musical', 0.5), ('creative', 0.3), ('emotional', 0.2)],
        }
    },
    'professional': {
        'decay': 0.015,
        'skills': {
            '医疗诊断': [('logical', 0.4), ('emotional', 0.3), ('spatial', 0.3)],
            '法律实务': [('logical', 0.4), ('linguistic', 0.4), ('emotional', 0.2)],
            '教学':     [('social', 0.3), ('linguistic', 0.3), ('emotional', 0.4)],
            '研究':     [('logical', 0.5), ('creative', 0.3), ('linguistic', 0.2)],
            '咨询':     [('social', 0.3), ('emotional', 0.4), ('logical', 0.3)],
        }
    },
    'sports': {
        'decay': 0.04,
        'skills': {
            '篮球': [('physical', 0.6), ('social', 0.2), ('spatial', 0.2)],
            '足球': [('physical', 0.6), ('social', 0.2), ('spatial', 0.2)],
            '游泳': [('physical', 0.7), ('emotional', 0.2), ('spatial', 0.1)],
            '跑步': [('physical', 0.7), ('emotional', 0.3)],
            '健身': [('physical', 0.7), ('emotional', 0.2), ('logical', 0.1)],
        }
    },
}

# 构建扁平的 SKILL_DEFS
for _cat, _cdata in _SKILL_RAW.items():
    for _sk, _talents in _cdata['skills'].items():
        SKILL_DEFS[_sk] = {
            'category': _cat,
            'decay_rate': _cdata['decay'],
            'talents': _talents,
        }

ALL_SKILL_NAMES = list(SKILL_DEFS.keys())

# 职业 → 使用中技能映射
OCCUPATION_SKILLS: Dict[str, List[str]] = {
    # 通用
    'unemployed': [],
    'student': ['数学', '文学', '外语'],
    # 技术类
    'Software Engineer': ['编程', '数据分析'],
    'Engineer': ['编程', '机械设计', '电子工程'],
    'Data Analyst': ['数据分析', '编程', '数学'],
    'Researcher': ['研究', '数学', '数据分析'],
    # 商业类
    'Accountant': ['财务管理', '数学'],
    'Marketing Manager': ['市场营销', '沟通', '写作'],
    'Project Manager': ['项目管理', '沟通', '领导力'],
    'Sales': ['谈判', '沟通', '客户服务'],
    'Consultant': ['咨询', '沟通', '数据分析'],
    # 专业类
    'Doctor': ['医疗诊断', '研究', '沟通'],
    'Lawyer': ['法律实务', '沟通', '写作'],
    'Teacher': ['教学', '沟通', '公共演讲'],
    'Professor': ['教学', '研究', '写作'],
    # 创意类
    'Designer': ['设计', '艺术创作'],
    'Writer': ['写作', '文学'],
    'Musician': ['音乐创作'],
    'Video Producer': ['视频制作', '设计'],
    # 管理类
    'Manager': ['领导力', '项目管理', '沟通'],
    'CEO': ['战略规划', '领导力', '谈判'],
}

# 技能协同效应
SKILL_SYNERGIES: Dict[Tuple[str, str], dict] = {
    ('编程', '数据分析'):     {'name': '数据科学',   'bonus': 0.20},
    ('编程', '机械设计'):     {'name': '自动化',     'bonus': 0.15},
    ('沟通', '领导力'):       {'name': '管理能力',   'bonus': 0.20},
    ('写作', '沟通'):         {'name': '表达能力',   'bonus': 0.15},
    ('财务管理', '数据分析'): {'name': '财务分析',   'bonus': 0.20},
    ('市场营销', '沟通'):     {'name': '营销能力',   'bonus': 0.15},
    ('设计', '艺术创作'):     {'name': '创意设计',   'bonus': 0.20},
    ('医疗诊断', '研究'):     {'name': '医学研究',   'bonus': 0.25},
    ('教学', '沟通'):         {'name': '教育能力',   'bonus': 0.20},
    ('编程', '设计'):         {'name': '全栈开发',   'bonus': 0.15},
    ('战略规划', '数据分析'): {'name': '商业智能',   'bonus': 0.20},
    ('谈判', '领导力'):       {'name': '高管能力',   'bonus': 0.20},
    ('音乐创作', '艺术创作'): {'name': '艺术全才',   'bonus': 0.15},
    ('法律实务', '谈判'):     {'name': '诉讼能力',   'bonus': 0.20},
    ('研究', '写作'):         {'name': '学术产出',   'bonus': 0.15},
}

# ── 稀有特质定义 ──
# rarity: legendary(0.001), epic(0.002~0.005), rare(0.01~0.02)
RARE_TRAITS: Dict[str, dict] = {
    # 传奇 (0.5%) — [Phase3 Fix] 从0.1%提升到0.5%，千人规模下约5人可触发
    '过目不忘': {
        'rarity': 'legendary', 'prob': 0.005,
        'require': {'logical': 7, 'linguistic': 7},
        'effect': {'learn_speed': 2.0, 'academic_mult': 1.5},
    },
    '幸运体质': {
        'rarity': 'legendary', 'prob': 0.005,
        'require': {},
        'effect': {'income_mult': 1.3, 'luck': 2.0, 'health_bonus': 10},
    },
    '跨域直觉': {
        'rarity': 'legendary', 'prob': 0.005,
        'require': {'creative': 7, 'logical': 6},
        'effect': {'learn_speed': 1.5, 'synergy_mult': 2.0},
    },
    # 极稀有 (0.2-0.5%)
    '天生领袖': {
        'rarity': 'epic', 'prob': 0.005,
        'require': {'social': 8, 'emotional': 7},
        'effect': {'social_charm': 1.5, 'leadership_mult': 1.5, 'income_mult': 1.2},
    },
    '直觉推演': {
        'rarity': 'epic', 'prob': 0.003,
        'require': {'logical': 8, 'spatial': 7},
        'effect': {'learn_speed': 1.3, 'research_mult': 1.5},
    },
    '绝对音感': {
        'rarity': 'epic', 'prob': 0.002,
        'require': {'musical': 9},
        'effect': {'music_mult': 2.0, 'creative_mult': 1.3},
    },
    '不眠者': {
        'rarity': 'epic', 'prob': 0.003,
        'require': {'physical': 8, 'emotional': 7},
        'effect': {'learn_speed': 1.3, 'work_hours_mult': 1.3},
    },
    '时间感知': {
        'rarity': 'epic', 'prob': 0.004,
        'require': {'spatial': 8, 'logical': 7},
        'effect': {'efficiency_mult': 1.4, 'project_mult': 1.3},
    },
    '天生说客': {
        'rarity': 'epic', 'prob': 0.005,
        'require': {'social': 8, 'linguistic': 7},
        'effect': {'social_charm': 1.8, 'negotiation_mult': 1.5},
    },
    # 稀有 (1-2%)
    '模式识别': {
        'rarity': 'rare', 'prob': 0.015,
        'require': {'logical': 7, 'spatial': 6},
        'effect': {'learn_speed': 1.2, 'data_mult': 1.3},
    },
    '共情天赋': {
        'rarity': 'rare', 'prob': 0.02,
        'require': {'emotional': 7, 'social': 6},
        'effect': {'social_charm': 1.3, 'counseling_mult': 1.5},
    },
    '铁人体质': {
        'rarity': 'rare', 'prob': 0.015,
        'require': {'physical': 8},
        'effect': {'health_bonus': 15, 'sports_mult': 1.5, 'stamina': 1.5},
    },
    '压力免疫': {
        'rarity': 'rare', 'prob': 0.02,
        'require': {'emotional': 8},
        'effect': {'stress_resist': 0.5, 'crisis_mult': 1.3},
    },
    '社交记忆': {
        'rarity': 'rare', 'prob': 0.015,
        'require': {'social': 7, 'linguistic': 6},
        'effect': {'social_charm': 1.2, 'networking_mult': 1.5},
    },
    '多线程思维': {
        'rarity': 'rare', 'prob': 0.01,
        'require': {'logical': 7, 'creative': 6},
        'effect': {'learn_speed': 1.2, 'efficiency_mult': 1.3},
    },
    '艺术直觉': {
        'rarity': 'rare', 'prob': 0.02,
        'require': {'creative': 7, 'emotional': 6},
        'effect': {'creative_mult': 1.4, 'art_mult': 1.5},
    },
}

# MBTI 学习速度修正
MBTI_SKILL_MODIFIERS: Dict[str, Dict[str, float]] = {
    'INTJ': {'technical': 1.20, 'academic': 1.15, 'business': 1.10},
    'INTP': {'technical': 1.20, 'academic': 1.20},
    'ENTJ': {'business': 1.20, 'social': 1.10},
    'ENTP': {'creative': 1.15, 'technical': 1.10, 'business': 1.10},
    'INFJ': {'creative': 1.15, 'professional': 1.15},
    'INFP': {'creative': 1.20, 'academic': 1.10},
    'ENFJ': {'social': 1.20, 'professional': 1.15},
    'ENFP': {'creative': 1.20, 'social': 1.15},
    'ISTJ': {'business': 1.15, 'professional': 1.10},
    'ISFJ': {'professional': 1.15, 'social': 1.10},
    'ESTJ': {'business': 1.15, 'social': 1.10},
    'ESFJ': {'social': 1.20, 'professional': 1.10},
    'ISTP': {'technical': 1.15, 'sports': 1.10},
    'ISFP': {'creative': 1.15, 'sports': 1.10},
    'ESTP': {'business': 1.10, 'sports': 1.15, 'social': 1.10},
    'ESFP': {'creative': 1.10, 'social': 1.15, 'sports': 1.10},
}

# MBTI 社交兼容性矩阵（互补加分）
MBTI_COMPATIBILITY: Dict[str, List[str]] = {
    'INTJ': ['ENFP', 'ENTP'],
    'INTP': ['ENTJ', 'ENFJ'],
    'ENTJ': ['INTP', 'INFP'],
    'ENTP': ['INTJ', 'INFJ'],
    'INFJ': ['ENTP', 'ENFP'],
    'INFP': ['ENTJ', 'ENFJ'],
    'ENFJ': ['INTP', 'INFP'],
    'ENFP': ['INTJ', 'INFJ'],
    'ISTJ': ['ESFP', 'ESTP'],
    'ISFJ': ['ESTP', 'ESFP'],
    'ESTJ': ['ISFP', 'ISTP'],
    'ESFJ': ['ISTP', 'ISFP'],
    'ISTP': ['ESFJ', 'ESTJ'],
    'ISFP': ['ESTJ', 'ESFJ'],
    'ESTP': ['ISTJ', 'ISFJ'],
    'ESFP': ['ISTJ', 'ISFJ'],
}

# 职业门槛（技能名 → 最低 level）
JOB_REQUIREMENTS: Dict[str, Dict[str, float]] = {
    'Software Engineer': {'编程': 30},
    'Data Analyst': {'数据分析': 25, '数学': 20},
    'Doctor': {'医疗诊断': 40, '生物': 25},
    'Lawyer': {'法律实务': 35},
    'Teacher': {'教学': 25, '沟通': 20},
    'Professor': {'教学': 40, '研究': 35},
    'Designer': {'设计': 30},
    'Writer': {'写作': 30},
    'Musician': {'音乐创作': 35},
    'Accountant': {'财务管理': 30, '数学': 20},
    'Marketing Manager': {'市场营销': 30, '沟通': 20},
    'Project Manager': {'项目管理': 30, '领导力': 20},
    'CEO': {'战略规划': 45, '领导力': 40},
    'Manager': {'领导力': 25, '沟通': 20},
    'Consultant': {'咨询': 30, '沟通': 25},
    'Sales': {'谈判': 20, '沟通': 20},
    'Engineer': {'机械设计': 30},
    'Researcher': {'研究': 35, '数学': 25},
    'Video Producer': {'视频制作': 30},
}

# S 型曲线参数
SIGMOID_SCALE = 500.0  # exp 达到约 500 时 level≈73, 达到 1000 时≈88


# ============================================================
# 辅助函数
# ============================================================

def _sigmoid(x: float) -> float:
    """标准 sigmoid, 值域 (0,1)"""
    if x > 500:
        return 1.0
    if x < -500:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def _exp_to_level(exp: float) -> float:
    """S 型成长曲线: level = 100 * sigmoid((exp - scale) / (scale * 0.4))
    exp=0 → level≈0.7, exp=SIGMOID_SCALE → level=50, exp=2*SIGMOID_SCALE → level≈99
    """
    centered = (exp - SIGMOID_SCALE) / (SIGMOID_SCALE * 0.4)
    return 100.0 * _sigmoid(centered)


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


# ============================================================
# 能力档案 (per-agent)
# ============================================================

class AbilityProfile:
    """单个 Agent 的完整能力档案"""

    __slots__ = ('agent_id', 'talents', 'skills', 'rare_traits', 'mbti')

    def __init__(self, agent_id: int):
        self.agent_id: int = agent_id
        self.talents: Dict[str, float] = {}          # dim -> 1~10
        self.skills: Dict[str, dict] = {}             # skill_name -> {exp, last_used_month}
        self.rare_traits: List[str] = []              # trait names
        self.mbti: str = ''

    # ── 技能便捷方法 ──

    def skill_level(self, name: str) -> float:
        """获取某技能的 level (0-100)"""
        s = self.skills.get(name)
        if s is None:
            return 0.0
        return _exp_to_level(s['exp'])

    def skill_levels_dict(self) -> Dict[str, float]:
        """返回 {skill_name: level} 字典"""
        return {name: _exp_to_level(s['exp']) for name, s in self.skills.items()}

    def to_dict(self) -> dict:
        """JSON 可序列化的完整档案"""
        return {
            'agent_id': self.agent_id,
            'talents': {k: round(v, 2) for k, v in self.talents.items()},
            'skills': {
                name: {
                    'level': round(_exp_to_level(s['exp']), 1),
                    'exp': round(s['exp'], 1),
                    'last_used_month': s['last_used_month'],
                }
                for name, s in self.skills.items()
            },
            'rare_traits': list(self.rare_traits),
            'mbti': self.mbti,
        }


# ============================================================
# AbilitySystem 主类
# ============================================================

class AbilitySystem:
    """三层能力系统 + MBTI"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.enabled: bool = True                     # feature_flag: 一键关闭
        self.profiles: Dict[int, AbilityProfile] = {}

        # 全局传奇特质配额计数器
        self._legendary_count: int = 0
        self._legendary_max: int = self.config.get('legendary_max', 10)

        # 当前模拟月份（由外部同步）
        self.current_month: int = 0

    # ================================================================
    # 创建档案
    # ================================================================

    def create_profile(self, agent_id: int, age: int = 25,
                       education: str = 'bachelor', gender: str = 'male') -> AbilityProfile:
        """为新 Agent 创建完整能力档案"""
        p = AbilityProfile(agent_id)

        # Layer 1: 基础天赋 (8维, μ=5, σ=2, 范围1-10)
        for dim in TALENT_DIMS:
            p.talents[dim] = _clamp(random.gauss(5, 2), 1.0, 10.0)

        # Layer 2: 初始技能
        self._init_skills(p, age, education)

        # MBTI 推导
        p.mbti = self._derive_mbti(p.talents)

        # Layer 3: 稀有特质
        self._roll_rare_traits(p)

        self.profiles[agent_id] = p
        return p

    # ── Layer 2: 初始技能生成 ──

    def _init_skills(self, p: AbilityProfile, age: int, education: str):
        """基于年龄和教育生成初始技能 exp"""
        edu_years = {
            'elementary': 6, 'middle': 9, 'high_school': 12,
            'college': 14, 'bachelor': 16, 'master': 18, 'phd': 20,
        }.get(education, 12)

        # 基础学术技能（所有人都有一些）
        base_academic = ['数学', '文学', '外语']
        for sk in base_academic:
            base_exp = max(0, (edu_years - 6) * 15 + random.gauss(0, 20))
            p.skills[sk] = {'exp': max(0, base_exp), 'last_used_month': 0}

        # 教育程度越高，额外学术/专业技能
        if edu_years >= 12:
            extras = random.sample(['物理', '化学', '生物', '历史'], k=random.randint(1, 2))
            for sk in extras:
                p.skills[sk] = {'exp': max(0, (edu_years - 10) * 12 + random.gauss(0, 15)),
                                'last_used_month': 0}

        if edu_years >= 16:
            # 大学+: 添加 1-3 个专业/技术技能
            pool = [s for s in ALL_SKILL_NAMES if s not in p.skills]
            n = random.randint(1, 3)
            for sk in random.sample(pool, min(n, len(pool))):
                p.skills[sk] = {'exp': max(0, (edu_years - 14) * 18 + random.gauss(0, 20)),
                                'last_used_month': 0}

        # 年龄带来的工作经验技能
        work_years = max(0, age - edu_years - 6)
        if work_years > 0:
            # 随机选 1-2 个已有技能增加经验
            existing = list(p.skills.keys())
            for sk in random.sample(existing, min(2, len(existing))):
                p.skills[sk]['exp'] += work_years * random.uniform(15, 30)

        # 沟通是普遍技能
        if '沟通' not in p.skills and age >= 16:
            p.skills['沟通'] = {'exp': max(0, (age - 16) * 8 + random.gauss(0, 10)),
                               'last_used_month': 0}

    # ── MBTI 推导 ──

    def _derive_mbti(self, talents: Dict[str, float]) -> str:
        # [Phase3 Fix9] 加随机扰动防止阈值效应，J/P 用独立计算避免和 T/F 都依赖 logical
        noise = random.gauss(0, 0.3)
        e_i = 'E' if talents.get('social', 5) + noise > 5.5 else 'I'
        noise = random.gauss(0, 0.3)
        s_n = 'N' if talents.get('spatial', 5) + noise > 5.5 else 'S'
        # T/F: logical vs emotional（独占 logical）
        noise = random.gauss(0, 0.3)
        t_f = 'T' if talents.get('logical', 5) + noise > talents.get('emotional', 5) else 'F'
        # J/P: (spatial + logical) vs (creative + emotional)，多维度综合避免与 T/F 完全重叠
        noise = random.gauss(0, 0.5)
        j_score = talents.get('spatial', 5) + talents.get('logical', 5)
        p_score = talents.get('creative', 5) + talents.get('emotional', 5)
        j_p = 'J' if j_score + noise > p_score else 'P'
        return e_i + s_n + t_f + j_p

    # ── Layer 3: 稀有特质 ──

    def _roll_rare_traits(self, p: AbilityProfile):
        """创建时掷骰稀有特质"""
        for trait_name, tdef in RARE_TRAITS.items():
            if len(p.rare_traits) >= 3:
                break
            # 检查天赋门槛
            if not self._meets_talent_req(p.talents, tdef['require']):
                continue
            # 传奇配额检查
            if tdef['rarity'] == 'legendary' and self._legendary_count >= self._legendary_max:
                continue
            # 概率掷骰
            if random.random() < tdef['prob']:
                p.rare_traits.append(trait_name)
                if tdef['rarity'] == 'legendary':
                    self._legendary_count += 1

    @staticmethod
    def _meets_talent_req(talents: Dict[str, float], require: dict) -> bool:
        for dim, threshold in require.items():
            if talents.get(dim, 0) < threshold:
                return False
        return True

    # ================================================================
    # 月度更新
    # ================================================================

    def update_monthly(self, agent_id: int, age: int, occupation: str,
                       happiness: float, health_score: float) -> dict:
        """
        月度能力更新，返回 {events: [...]}

        阶段 1: 使用中技能成长
        阶段 2: 未使用技能衰减
        阶段 3: 5% 概率学新技能
        阶段 4: 1% 概率顿悟 (天赋微调)
        阶段 5: 0.5% 概率传奇觉醒
        """
        if not self.enabled:
            return {'events': []}

        p = self.profiles.get(agent_id)
        if p is None:
            return {'events': []}

        events: List[dict] = []
        self.current_month += 0  # 外部同步

        # 查找职业使用的技能
        active_skills = set()
        for occ_key, occ_skills in OCCUPATION_SKILLS.items():
            if occ_key.lower() in occupation.lower() or occupation.lower() in occ_key.lower():
                active_skills.update(occ_skills)
                break
        # 若未匹配到具体职业，默认使用已有技能中的前 2 个
        if not active_skills and p.skills:
            active_skills = set(list(p.skills.keys())[:2])

        # MBTI 学习速度修正表
        mbti_mods = MBTI_SKILL_MODIFIERS.get(p.mbti, {})

        # 健康/幸福修正
        condition_mult = _clamp(happiness / 60.0, 0.5, 1.5) * _clamp(health_score / 80.0, 0.5, 1.3)

        # ── 阶段 1: 使用中技能成长 ──
        for sk_name in active_skills:
            if sk_name not in p.skills:
                # 开始学习新的职业技能
                p.skills[sk_name] = {'exp': 0, 'last_used_month': self.current_month}
            sk = p.skills[sk_name]
            sk['last_used_month'] = self.current_month

            # 基础 exp 增量
            base_gain = random.uniform(8, 18)

            # 天赋加速
            talent_mult = self._calc_talent_multiplier(p.talents, sk_name)

            # MBTI 修正
            cat = SKILL_DEFS.get(sk_name, {}).get('category', '')
            mbti_mult = mbti_mods.get(cat, 1.0)

            # 特质修正
            trait_mult = self._calc_trait_learn_mult(p.rare_traits)

            # 年龄修正（年轻人学得快）
            age_mult = 1.2 if age < 25 else (1.0 if age < 40 else 0.85)

            total_gain = base_gain * talent_mult * mbti_mult * trait_mult * age_mult * condition_mult
            old_level = _exp_to_level(sk['exp'])
            sk['exp'] += total_gain
            new_level = _exp_to_level(sk['exp'])

            # 技能升级事件（每跨 10 级报告一次）
            if int(new_level / 10) > int(old_level / 10):
                events.append({
                    'type': 'skill_levelup',
                    'agent_id': agent_id,
                    'skill': sk_name,
                    'old_level': round(old_level, 1),
                    'new_level': round(new_level, 1),
                })

        # ── 阶段 2: 未使用技能衰减 ──
        for sk_name, sk in list(p.skills.items()):
            if sk_name in active_skills:
                continue
            months_idle = max(0, self.current_month - sk.get('last_used_month', 0))
            if months_idle < 1:
                months_idle = 1  # 至少 1 个月不用才衰减
            decay_rate = SKILL_DEFS.get(sk_name, {}).get('decay_rate', 0.02)
            # 衰减量与当前 exp 成比例
            decay = sk['exp'] * decay_rate * min(months_idle, 3)
            if decay > 0.1:
                sk['exp'] = max(0, sk['exp'] - decay)

        # ── 阶段 3: 5% 概率学新技能 ──
        if random.random() < 0.05:
            known = set(p.skills.keys())
            unknown = [s for s in ALL_SKILL_NAMES if s not in known]
            if unknown:
                new_sk = random.choice(unknown)
                p.skills[new_sk] = {'exp': random.uniform(5, 25), 'last_used_month': self.current_month}
                events.append({
                    'type': 'new_skill_learned',
                    'agent_id': agent_id,
                    'skill': new_sk,
                })

        # ── 阶段 4: 1% 概率顿悟 (天赋微调 +0.3) ──
        if random.random() < 0.01:
            dim = random.choice(TALENT_DIMS)
            old_val = p.talents[dim]
            p.talents[dim] = _clamp(old_val + 0.3, 1.0, 10.0)
            # 重新推导 MBTI（天赋变了可能导致 MBTI 变化）
            new_mbti = self._derive_mbti(p.talents)
            mbti_changed = new_mbti != p.mbti
            p.mbti = new_mbti
            events.append({
                'type': 'talent_epiphany',
                'agent_id': agent_id,
                'dimension': dim,
                'old_value': round(old_val, 2),
                'new_value': round(p.talents[dim], 2),
                'mbti_changed': mbti_changed,
            })

        # ── 阶段 5: 0.5% 概率传奇觉醒 ──
        if random.random() < 0.005 and len(p.rare_traits) < 3:
            # 尝试获得新特质
            for trait_name, tdef in RARE_TRAITS.items():
                if trait_name in p.rare_traits:
                    continue
                if not self._meets_talent_req(p.talents, tdef['require']):
                    continue
                if tdef['rarity'] == 'legendary' and self._legendary_count >= self._legendary_max:
                    continue
                # 觉醒概率是正常的 10 倍（因为已经通过了 0.5% 的大门）
                if random.random() < min(1.0, tdef['prob'] * 10):
                    p.rare_traits.append(trait_name)
                    if tdef['rarity'] == 'legendary':
                        self._legendary_count += 1
                    events.append({
                        'type': 'rare_trait_awakened',
                        'agent_id': agent_id,
                        'trait': trait_name,
                        'rarity': tdef['rarity'],
                    })
                    break

        return {'events': events}

    # ── 天赋对技能的加速倍率 ──

    @staticmethod
    def _calc_talent_multiplier(talents: Dict[str, float], skill_name: str) -> float:
        """计算天赋对某技能的学习加速"""
        sdef = SKILL_DEFS.get(skill_name)
        if not sdef:
            return 1.0
        weighted_talent = 0.0
        for dim, weight in sdef['talents']:
            weighted_talent += talents.get(dim, 5.0) * weight
        # talent 5 → mult 1.0, talent 8 → mult 1.3, talent 10 → mult 1.5
        return 0.7 + weighted_talent * 0.06

    @staticmethod
    def _calc_trait_learn_mult(traits: List[str]) -> float:
        """稀有特质对学习速度的总修正"""
        mult = 1.0
        for t in traits:
            tdef = RARE_TRAITS.get(t, {})
            mult *= tdef.get('effect', {}).get('learn_speed', 1.0)
        return mult

    # ================================================================
    # 子系统交互接口
    # ================================================================

    def calc_income_modifier(self, agent_id: int) -> float:
        """收入修正（基于技能等级 + 协同效应 + 稀有特质）"""
        if not self.enabled:
            return 1.0
        p = self.profiles.get(agent_id)
        if not p:
            return 1.0

        # 基础技能加成: 所有技能 level 加权平均
        levels = p.skill_levels_dict()
        if levels:
            avg_level = sum(levels.values()) / len(levels)
            # avg_level 50 → mult 1.0, 80 → mult 1.3
            skill_mult = 0.7 + avg_level * 0.006
        else:
            skill_mult = 1.0

        # 协同加成
        synergy_mult = 1.0
        synergy_trait_boost = 1.0
        for t in p.rare_traits:
            synergy_trait_boost *= RARE_TRAITS.get(t, {}).get('effect', {}).get('synergy_mult', 1.0)
        for (s1, s2), syn in SKILL_SYNERGIES.items():
            l1, l2 = p.skill_level(s1), p.skill_level(s2)
            if l1 >= 30 and l2 >= 30:
                synergy_mult += syn['bonus'] * min(l1, l2) / 100 * synergy_trait_boost

        # 稀有特质收入倍率
        trait_mult = 1.0
        for t in p.rare_traits:
            trait_mult *= RARE_TRAITS.get(t, {}).get('effect', {}).get('income_mult', 1.0)

        return skill_mult * synergy_mult * trait_mult

    def calc_social_attractiveness(self, agent_id: int) -> float:
        """社交魅力值 (0-100)"""
        if not self.enabled:
            return 50.0
        p = self.profiles.get(agent_id)
        if not p:
            return 50.0

        # 基础: social + emotional 天赋
        base = (p.talents.get('social', 5) + p.talents.get('emotional', 5)) * 5  # 0-100

        # 社交技能加成
        social_skills = ['沟通', '领导力', '团队协作', '客户服务', '公共演讲']
        skill_bonus = sum(p.skill_level(s) for s in social_skills) / len(social_skills) * 0.3

        # 特质加成
        charm_mult = 1.0
        for t in p.rare_traits:
            charm_mult *= RARE_TRAITS.get(t, {}).get('effect', {}).get('social_charm', 1.0)

        return _clamp(base * charm_mult + skill_bonus, 0, 100)

    def calc_marriage_compatibility(self, id_a: int, id_b: int) -> float:
        """婚配兼容度 (0-1)"""
        if not self.enabled:
            return 0.5
        pa = self.profiles.get(id_a)
        pb = self.profiles.get(id_b)
        if not pa or not pb:
            return 0.5

        score = 0.5  # 基础

        # MBTI 兼容性
        compatible_types = MBTI_COMPATIBILITY.get(pa.mbti, [])
        if pb.mbti in compatible_types:
            score += 0.2
        elif pb.mbti == pa.mbti:
            score += 0.05

        # 天赋互补性（差异适中最好）
        talent_diff = 0.0
        for dim in TALENT_DIMS:
            diff = abs(pa.talents.get(dim, 5) - pb.talents.get(dim, 5))
            talent_diff += diff
        avg_diff = talent_diff / len(TALENT_DIMS)
        # 差异 2-4 最佳
        if 2 <= avg_diff <= 4:
            score += 0.15
        elif avg_diff < 2:
            score += 0.05

        # 共同技能（有共同话题）
        shared = set(pa.skills.keys()) & set(pb.skills.keys())
        score += min(0.15, len(shared) * 0.03)

        return _clamp(score, 0, 1)

    def get_job_eligible(self, agent_id: int) -> List[str]:
        """返回该 Agent 有资格胜任的职业列表"""
        if not self.enabled:
            return list(JOB_REQUIREMENTS.keys())
        p = self.profiles.get(agent_id)
        if not p:
            return []

        eligible = []
        for job, reqs in JOB_REQUIREMENTS.items():
            qualified = True
            for sk, min_level in reqs.items():
                if p.skill_level(sk) < min_level:
                    qualified = False
                    break
            if qualified:
                eligible.append(job)
        return eligible

    # ================================================================
    # 序列化
    # ================================================================

    def get_profile_dict(self, agent_id: int) -> dict:
        """返回可 JSON 序列化的完整能力档案"""
        p = self.profiles.get(agent_id)
        if not p:
            return {}
        return p.to_dict()

    # ================================================================
    # 批量同步（引擎调用）
    # ================================================================

    def sync_to_agent(self, agent_id: int) -> dict:
        """返回用于写回 UnifiedAgent 的精简字段"""
        p = self.profiles.get(agent_id)
        if not p:
            return {'abilities': {}, 'unique_talents': [], 'mbti': ''}
        return {
            'abilities': p.skill_levels_dict(),
            'unique_talents': list(p.rare_traits),
            'mbti': p.mbti,
        }


# ============================================================
# 独立测试
# ============================================================

if __name__ == '__main__':
    print('=' * 60)
    print('能力系统独立测试')
    print('=' * 60)

    sys = AbilitySystem()

    # 创建 100 个测试档案
    for i in range(1, 101):
        age = random.randint(20, 50)
        edu = random.choice(['high_school', 'bachelor', 'master', 'phd'])
        sys.create_profile(i, age, edu)

    # 统计 MBTI 分布
    mbti_counts: Dict[str, int] = {}
    for p in sys.profiles.values():
        mbti_counts[p.mbti] = mbti_counts.get(p.mbti, 0) + 1
    print(f'\nMBTI 分布 (100人):')
    for m, c in sorted(mbti_counts.items(), key=lambda x: -x[1]):
        print(f'  {m}: {c}')

    # 稀有特质统计
    trait_count = sum(len(p.rare_traits) for p in sys.profiles.values())
    with_traits = sum(1 for p in sys.profiles.values() if p.rare_traits)
    print(f'\n稀有特质: {trait_count} 个, {with_traits} 人拥有 ({with_traits}%)')
    print(f'传奇特质全局: {sys._legendary_count}')

    # 月度更新测试
    all_events = []
    for month in range(12):
        sys.current_month = month
        for pid in list(sys.profiles.keys()):
            r = sys.update_monthly(pid, 30, 'Software Engineer', 65.0, 80.0)
            all_events.extend(r['events'])
    print(f'\n12个月模拟事件: {len(all_events)}')

    # 样本输出
    p1 = sys.profiles[1]
    print(f'\nAgent 1 档案:')
    print(f'  MBTI: {p1.mbti}')
    print(f'  天赋: {p1.talents}')
    print(f'  技能: {p1.skill_levels_dict()}')
    print(f'  特质: {p1.rare_traits}')
    print(f'  收入修正: {sys.calc_income_modifier(1):.2f}')
    print(f'  社交魅力: {sys.calc_social_attractiveness(1):.1f}')

    print('\n[OK] 能力系统独立测试完成!')
