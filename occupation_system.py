"""
御龙军虚拟 Agent 世界 v5 - 职业行为自主演化系统
版本：v5.0（从旧版 v3.0 移植）
移植日期：2026-03-25
功能：基于职业的时间表、工作状态自主决策、职业流动性

适配 v5 UnifiedAgent 字段:
  age, occupation, income, education_level, happiness, stress,
  abilities, mbti, is_unemployed
"""

import random
from typing import Dict, List, Optional, Any


class OccupationSystem:
    """职业系统 - v5 适配版（自主演化）"""

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # 职业定义
        self.occupations = {
            '农业': {
                'work_hours': (5, 18),
                'work_days': [0, 1, 2, 3, 4, 5, 6],
                'base_income': 800,
                'skill_requirement': 1,
                'education_min': 'elementary',
                'stress_level': 0.6,
                'satisfaction_base': 3.0,
                'unemployment_rate': 0.02,
                'job_openings': 5000,
            },
            '制造业': {
                'work_hours': (8, 17),
                'work_days': [0, 1, 2, 3, 4],
                'base_income': 2500,
                'skill_requirement': 3,
                'education_min': 'middle',
                'stress_level': 0.5,
                'satisfaction_base': 3.2,
                'unemployment_rate': 0.04,
                'job_openings': 8000,
            },
            '服务业': {
                'work_hours': (9, 21),
                'work_days': [0, 1, 2, 3, 4, 5, 6],
                'base_income': 2000,
                'skill_requirement': 2,
                'education_min': 'middle',
                'stress_level': 0.7,
                'satisfaction_base': 3.1,
                'unemployment_rate': 0.05,
                'job_openings': 15000,
            },
            '信息技术': {
                'work_hours': (9, 18),
                'work_days': [0, 1, 2, 3, 4],
                'base_income': 12000,
                'skill_requirement': 7,
                'education_min': 'bachelor',
                'stress_level': 0.8,
                'satisfaction_base': 3.8,
                'unemployment_rate': 0.02,
                'job_openings': 5000,
            },
            '医疗': {
                'work_hours': (8, 20),
                'work_days': [0, 1, 2, 3, 4, 5, 6],
                'base_income': 10000,
                'skill_requirement': 8,
                'education_min': 'master',
                'stress_level': 0.9,
                'satisfaction_base': 4.0,
                'unemployment_rate': 0.01,
                'job_openings': 3000,
            },
            '教育': {
                'work_hours': (8, 16),
                'work_days': [0, 1, 2, 3, 4],
                'base_income': 6000,
                'skill_requirement': 6,
                'education_min': 'bachelor',
                'stress_level': 0.5,
                'satisfaction_base': 3.7,
                'unemployment_rate': 0.02,
                'job_openings': 2500,
            },
            '金融': {
                'work_hours': (9, 17),
                'work_days': [0, 1, 2, 3, 4],
                'base_income': 15000,
                'skill_requirement': 7,
                'education_min': 'bachelor',
                'stress_level': 0.85,
                'satisfaction_base': 3.6,
                'unemployment_rate': 0.03,
                'job_openings': 2000,
            },
            '政府': {
                'work_hours': (9, 17),
                'work_days': [0, 1, 2, 3, 4],
                'base_income': 8000,
                'skill_requirement': 6,
                'education_min': 'bachelor',
                'stress_level': 0.4,
                'satisfaction_base': 3.9,
                'unemployment_rate': 0.01,
                'job_openings': 1500,
            },
            '其他': {
                'work_hours': (9, 17),
                'work_days': [0, 1, 2, 3, 4, 5, 6],
                'base_income': 1500,
                'skill_requirement': 1,
                'education_min': 'elementary',
                'stress_level': 0.6,
                'satisfaction_base': 2.8,
                'unemployment_rate': 0.15,
                'job_openings': 1000,
            },
        }

        # v5 教育等级（从低到高）
        self.education_levels = [
            'elementary', 'middle', 'high_school', 'college',
            'bachelor', 'master', 'phd',
        ]
        self._edu_to_idx = {e: i for i, e in enumerate(self.education_levels)}

        # 追踪职业变动年份
        self._last_job_change: Dict[int, int] = {}  # agent_id -> year

    # ── 辅助 ──

    def _safe(self, agent, field: str, default=None):
        if isinstance(agent, dict):
            return agent.get(field, default)
        return getattr(agent, field, default)

    def _set(self, agent, field: str, value):
        if isinstance(agent, dict):
            agent[field] = value
        else:
            setattr(agent, field, value)

    def _edu_index(self, edu: str) -> int:
        return self._edu_to_idx.get(edu, 2)

    def _get_skill_level(self, agent) -> float:
        """从 v5 abilities 推算综合技能等级（0-10）"""
        abilities = self._safe(agent, 'abilities', {})
        if not abilities:
            return 3.0
        vals = list(abilities.values())
        return sum(vals) / len(vals) if vals else 3.0

    # ── 核心功能 ──

    def is_work_time(self, agent, current_day: int, current_hour: float) -> bool:
        """判断是否是工作时间"""
        occ = self._safe(agent, 'occupation', '其他')
        occ_data = self.occupations.get(occ, self.occupations['其他'])
        work_hours = occ_data['work_hours']
        work_days = occ_data['work_days']
        if current_day % 7 not in work_days:
            return False
        return work_hours[0] <= current_hour < work_hours[1]

    def is_rest_time(self, current_hour: float) -> bool:
        """判断是否是深夜休息时间"""
        return current_hour >= 23 or current_hour < 6

    def decide_behavior(self, agent, current_day: int, current_hour: float) -> str:
        """自主决策行为"""
        if self.is_rest_time(current_hour):
            return 'rest'
        if self.is_work_time(agent, current_day, current_hour):
            happiness = self._safe(agent, 'happiness', 50)
            # 幸福感 < 30（满分 100）→ 10% 概率请假
            if happiness < 30 and random.random() < 0.1:
                return 'rest'
            return 'work'

        # 非工作时间 - 基于 mbti/性格
        mbti = self._safe(agent, 'mbti', '')
        is_extrovert = mbti.startswith('E') if mbti else random.random() > 0.5

        if is_extrovert:
            choices = ['social', 'consume', 'learn', 'rest']
            weights = [0.35, 0.30, 0.15, 0.20]
        else:
            choices = ['rest', 'learn', 'consume', 'social']
            weights = [0.35, 0.30, 0.20, 0.15]

        happiness = self._safe(agent, 'happiness', 50)
        if happiness < 30:
            weights = [w * 1.5 if c == 'rest' else w for c, w in zip(choices, weights)]

        total = sum(weights)
        weights = [w / total for w in weights]
        return random.choices(choices, weights=weights)[0]

    def can_qualify_for_job(self, agent, occupation: str) -> bool:
        """检查是否符合职位要求"""
        occ_data = self.occupations.get(occupation, {})
        if not occ_data:
            return False

        skill_level = self._get_skill_level(agent)
        if skill_level < occ_data.get('skill_requirement', 1):
            return False

        required_edu = occ_data.get('education_min', 'elementary')
        agent_edu = self._safe(agent, 'education_level', 'high_school')
        if self._edu_index(agent_edu) < self._edu_index(required_edu):
            return False

        return True

    def find_job(self, agent) -> Optional[str]:
        """为 Agent 寻找工作"""
        available = []
        for occ, data in self.occupations.items():
            if data['job_openings'] > 0 and self.can_qualify_for_job(agent, occ):
                edu_idx = self._edu_index(self._safe(agent, 'education_level', 'high_school'))
                req_idx = self._edu_index(data['education_min'])
                skill_level = self._get_skill_level(agent)
                match = (
                    skill_level / max(1, data['skill_requirement']) * 0.6 +
                    edu_idx / max(1, req_idx) * 0.4
                )
                available.append((occ, match))
        if not available:
            return None
        available.sort(key=lambda x: x[1], reverse=True)
        top = available[:min(3, len(available))]
        return random.choice(top)[0]

    # ── v5 标准接口 ──

    def update_monthly(self, agents: dict, current_year: int = 2026, **kwargs) -> Dict:
        """
        月度更新 - 职业评估、升职 / 失业 / 换工作。
        agents: {agent_id: UnifiedAgent}
        返回: {'events': [...], 'statistics': {...}}
        """
        events = []

        for agent_id, agent in agents.items():
            if not self._safe(agent, 'is_alive', True):
                continue

            occ = self._safe(agent, 'occupation', '其他')
            if occ in ('retired', '退休', 'student', '学生'):
                continue

            # 年度职业评估（每 12 个月触发一次，简化为概率）
            if random.random() > 1.0 / 12:
                continue

            last_change = self._last_job_change.get(agent_id, current_year - 2)
            if current_year - last_change < 2:
                continue

            skill_level = self._get_skill_level(agent)
            income = self._safe(agent, 'income', 0)
            edu = self._safe(agent, 'education_level', 'high_school')

            # 高技能 + 高教育 → 升职/跳槽
            if skill_level > 7 and self._edu_index(edu) >= self._edu_index('bachelor'):
                if random.random() < 0.3:
                    better_jobs = [j for j in ['信息技术', '金融', '医疗']
                                   if self.can_qualify_for_job(agent, j)]
                    if better_jobs:
                        new_job = random.choice(better_jobs)
                        factor = random.uniform(1.15, 1.35)
                        self._set(agent, 'occupation', new_job)
                        self._set(agent, 'income', income * factor)
                        self._set(agent, 'is_unemployed', False)
                        self._last_job_change[agent_id] = current_year
                        events.append({
                            'type': 'career_promotion',
                            'agent_id': agent_id,
                            'new_occupation': new_job,
                            'income_change': factor,
                        })
                        continue

            # 低技能 → 失业风险
            if skill_level < 3:
                occ_data = self.occupations.get(occ, {})
                if random.random() < occ_data.get('unemployment_rate', 0.05):
                    self._set(agent, 'occupation', '其他')
                    self._set(agent, 'income', income * random.uniform(0.2, 0.4))
                    self._set(agent, 'is_unemployed', True)
                    self._last_job_change[agent_id] = current_year
                    events.append({
                        'type': 'job_loss',
                        'agent_id': agent_id,
                    })
                    continue

            # 满意度低 → 换工作
            happiness = self._safe(agent, 'happiness', 50)
            if happiness < 25 and occ != '其他':
                if random.random() < 0.2:
                    new_job = self.find_job(agent)
                    if new_job and new_job != occ:
                        self._set(agent, 'occupation', new_job)
                        self._last_job_change[agent_id] = current_year
                        events.append({
                            'type': 'career_change',
                            'agent_id': agent_id,
                            'from': occ,
                            'to': new_job,
                        })

        # 统计
        stats = self._compute_statistics(agents)

        return {
            'events': events,
            'statistics': stats,
        }

    def _compute_statistics(self, agents: dict) -> Dict:
        """统计职业分布"""
        by_occ = {}
        employed = 0
        unemployed = 0
        students = 0

        for agent in agents.values():
            if not self._safe(agent, 'is_alive', True):
                continue
            job = self._safe(agent, 'occupation', '其他')
            age = self._safe(agent, 'age', 0)
            by_occ[job] = by_occ.get(job, 0) + 1

            if job in ('student', '学生') or age < 16:
                students += 1
            elif job in ('其他', 'unemployed') and self._safe(agent, 'is_unemployed', True):
                unemployed += 1
            else:
                employed += 1

        return {
            'by_occupation': by_occ,
            'employed': employed,
            'unemployed': unemployed,
            'students': students,
        }
