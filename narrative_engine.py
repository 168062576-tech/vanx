"""
narrative_engine.py - 叙事引擎
虚拟 Agent 世界 v3.0

将 Agent 的数据转化为可读的"生命故事"。
用途：演示、报告、用户理解。

v3.2 更新：支持 133 国文化姓名生成（通过 name_data_124 模块）
"""

import hashlib
import random
import os
import sys
from typing import Dict, List, Optional

# Import 133-culture name database
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
from name_data_124 import NAME_DATA, EASTERN_ORDER


class NarrativeEngine:
    """Agent 生命故事生成器"""

    # 支持的国籍列表（133 国）
    SUPPORTED_NATIONALITIES = list(NAME_DATA.keys())

    EDUCATION_NAMES = {
        'none': '未受教育', 'primary': '小学', 'middle_school': '初中',
        'high_school': '高中', 'college': '大专', 'bachelor': '本科',
        'master': '硕士', 'phd': '博士', 'student': '在读'
    }

    MARITAL_NAMES = {
        'single': '单身', 'married': '已婚', 'divorced': '离异', 'widowed': '丧偶'
    }

    def __init__(self):
        self._name_cache = {}

    def generate_name(self, agent_id: int, gender: str = 'male',
                      nationality: str = 'chinese') -> str:
        """基于 agent_id + gender + nationality 确定性生成姓名。

        使用 SHA-256 哈希确保同一 (agent_id, gender, nationality) 永远生成相同姓名。
        支持 133 国文化（通过 name_data_124 模块）。
        nationality 不在库中时 fallback 到 chinese。
        """
        cache_key = (agent_id, gender, nationality)
        if cache_key in self._name_cache:
            return self._name_cache[cache_key]

        seed = f"{agent_id}_{gender}_{nationality}"
        hash_bytes = hashlib.sha256(seed.encode('utf-8')).digest()

        db = NAME_DATA.get(nationality, NAME_DATA['chinese'])

        surname_list = db['surnames']
        surname_idx = hash_bytes[0] % len(surname_list)
        surname = surname_list[surname_idx]

        given_list = db['male'] if gender == 'male' else db['female']
        given_idx = hash_bytes[1] % len(given_list)
        given_name = given_list[given_idx]

        if nationality in EASTERN_ORDER:
            full_name = surname + given_name
        else:
            full_name = f"{given_name} {surname}"

        self._name_cache[cache_key] = full_name
        return full_name
    def agent_summary(self, agent) -> str:
        """一句话概括 Agent"""
        name = self.generate_name(agent.id, agent.gender)
        age = agent.age
        edu = self.EDUCATION_NAMES.get(getattr(agent, 'education_level', ''), '未知')
        marital = self.MARITAL_NAMES.get(getattr(agent, 'marital_status', 'single'), '未知')
        income = getattr(agent, 'income', 0)
        job = getattr(agent, 'occupation', '无业')

        return f"{name}，{age}岁，{edu}学历，{marital}，月收入{income:.0f}元，职业：{job}"

    def life_story(self, agent, events: List = None) -> str:
        """生成 Agent 的生命故事"""
        name = self.generate_name(agent.id, agent.gender)
        gender_str = '男' if agent.gender == 'male' else '女'
        age = agent.age
        edu = self.EDUCATION_NAMES.get(getattr(agent, 'education_level', ''), '未知')
        marital = self.MARITAL_NAMES.get(getattr(agent, 'marital_status', 'single'), '未知')
        income = getattr(agent, 'income', 0)
        happiness = getattr(agent, 'happiness', 50)
        health = getattr(agent, 'health_score', 80)
        net_worth = getattr(agent, 'net_worth', 0)

        # 基础故事
        story = f"## {name}的故事\n\n"
        story += f"**{name}**，{gender_str}，今年{age}岁。"

        # 教育背景
        if edu in ['博士', '硕士']:
            story += f"经过多年苦读，拥有{edu}学位。"
        elif edu == '本科':
            story += f"大学毕业，拥有{edu}学历。"
        elif edu in ['高中', '初中']:
            story += f"只有{edu}学历，早早步入社会。"
        else:
            story += f"学历为{edu}。"

        # 婚姻
        if marital == '已婚':
            story += "已经成家，"
        elif marital == '离异':
            story += "经历过一段婚姻，如今独自生活，"
        elif age > 35:
            story += "至今未婚，"
        else:
            story += ""

        # 经济状况
        if income > 20000:
            story += f"事业有成，月入{income:.0f}元，是同龄人中的佼佼者。"
        elif income > 8000:
            story += f"工作稳定，月入{income:.0f}元，生活还算体面。"
        elif income > 3000:
            story += f"收入一般，月入{income:.0f}元，日子过得紧巴巴。"
        elif income > 0:
            story += f"收入微薄，月入仅{income:.0f}元，生活捉襟见肘。"
        else:
            story += "目前没有收入来源，生活困难。"

        # 净资产
        story += "\n\n"
        if net_worth > 1000000:
            story += f"多年积累，净资产已达{net_worth/10000:.1f}万元。"
        elif net_worth > 100000:
            story += f"有一定积蓄，净资产{net_worth/10000:.1f}万元。"
        elif net_worth > 0:
            story += f"手头不宽裕，净资产仅{net_worth:.0f}元。"
        else:
            story += f"负债累累，净资产为{net_worth:.0f}元。"

        # 健康和幸福
        story += "\n\n"
        if health > 85 and happiness > 70:
            story += "身体健康，心情愉悦，对生活充满期待。"
        elif health > 70 and happiness > 50:
            story += "身体还行，生活也算过得去。"
        elif health < 50:
            story += "身体状况不太好，需要多注意健康。"
        elif happiness < 30:
            story += "虽然身体尚可，但内心并不快乐，时常感到迷茫。"
        else:
            story += "生活平淡，有好有坏。"

        # 事件故事
        if events:
            agent_events = [e for e in events if getattr(e, 'agent_id', None) == agent.id]
            if agent_events:
                story += "\n\n### 近期经历\n\n"
                for evt in agent_events[-5:]:  # 最近 5 个事件
                    story += f"- {self._event_to_sentence(name, evt)}\n"

        return story

    def _event_to_sentence(self, name: str, event) -> str:
        """将事件转为自然语言"""
        etype = event.event_type
        data = event.data if hasattr(event, 'data') else {}

        sentences = {
            'career_change': f"{name}决定换一份新工作，希望能有更好的发展。",
            'marriage_decision': f"{name}步入了婚姻的殿堂，开始了新的人生篇章。",
            'crime_decision': f"{name}走上了歧途，做出了不该做的选择。",
            'crime_caught': f"{name}因违法行为被抓，面临法律的制裁。",
            'medical_expense': f"{name}去了趟医院，花了一笔医疗费。",
            'debt_increase': f"{name}的债务增加了，经济压力更大了。",
            'welfare_enrolled': f"{name}申请了社会福利，获得了一些帮助。",
            'employment_started': f"{name}找到了一份新工作，生活有了新的起点。",
            'risk_event': f"{name}遭遇了一些意外情况。",
            'agent_created': f"{name}来到了这个世界。",
        }

        return sentences.get(etype, f"{name}经历了一件事（{etype}）。")

    def world_narrative(self, agents, events, month: int) -> str:
        """生成世界概况叙事"""
        n = len(agents)
        if n == 0:
            return "这是一个空旷的世界，还没有居民。"

        avg_age = sum(a.age for a in agents) / n
        avg_income = sum(getattr(a, 'income', 0) for a in agents) / n
        avg_happiness = sum(getattr(a, 'happiness', 50) for a in agents) / n
        married = sum(1 for a in agents if getattr(a, 'marital_status', '') == 'married')
        married_pct = married / n * 100

        year = month // 12 + 1
        month_in_year = month % 12 + 1

        narrative = f"## 世界纪元 第{year}年 第{month_in_year}月\n\n"
        narrative += f"这个世界有 **{n}** 位居民，平均年龄 **{avg_age:.0f}** 岁。"
        narrative += f"人均月收入 **{avg_income:.0f}** 元，"

        if avg_happiness > 70:
            narrative += "居民们总体上生活幸福，社会和谐稳定。"
        elif avg_happiness > 50:
            narrative += "生活还过得去，但也有不少人在为生计奔波。"
        else:
            narrative += "许多人对生活感到不满，社会问题不断涌现。"

        narrative += f"\n\n已婚率 **{married_pct:.1f}%**，"

        recent_events = events[-20:] if events else []
        career_changes = sum(1 for e in recent_events if e.event_type == 'career_change')
        crimes = sum(1 for e in recent_events if e.event_type in ('crime_caught', 'crime_decision'))

        if career_changes > 5:
            narrative += "就业市场活跃，不少人在寻找更好的机会。"
        if crimes > 3:
            narrative += "治安方面需要加强，近期犯罪事件有所增加。"

        return narrative
