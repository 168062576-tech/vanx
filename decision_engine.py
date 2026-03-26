"""
decision_engine.py - LLM 混合决策引擎
虚拟 Agent 世界 v3.0

三级决策模型：
  L0 规则引擎 — 日常决策（消费、通勤、社交），0 成本，<0.01ms
  L1 本地 LLM — 关键决策（换工作、结婚、买房），低成本，~100ms
  L2 线上 LLM — 重大决策（创业、移民、犯罪），按需付费，~1-3s

依赖：
  - L0: 无外部依赖
  - L1: ollama（本地运行，需提前安装）
  - L2: requests（调用线上 API）
"""

import random
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class DecisionLevel(Enum):
    ROUTINE = "routine"      # L0 规则
    IMPORTANT = "important"  # L1 本地 LLM
    CRITICAL = "critical"    # L2 线上 LLM


class EngineMode(Enum):
    RULE_ONLY = "rule_only"   # 纯规则（默认，零成本）
    HYBRID = "hybrid"         # 混合（L0 + L1）
    FULL_LLM = "full_llm"    # 全 LLM（L0 + L1 + L2）


@dataclass
class DecisionContext:
    """决策上下文"""
    decision_type: str                  # career_change, marriage, purchase, crime, migration...
    options: List[str] = field(default_factory=list)
    agent_summary: Dict = field(default_factory=dict)  # Agent 状态摘要
    world_context: Dict = field(default_factory=dict)   # 世界状态摘要
    urgency: float = 0.5               # 紧迫度 0-1
    custom_prompt: str = ""            # 自定义提示（可选）


@dataclass
class Decision:
    """决策结果"""
    choice: str                         # 选择的选项
    reasoning: str = ""                # 理由（LLM 提供）
    confidence: float = 0.8            # 置信度 0-1
    engine_used: str = "rule"          # rule / local_llm / remote_llm
    latency_ms: float = 0             # 决策耗时
    cost: float = 0                   # LLM 调用成本（元）


# ── 决策类型分级映射 ──
DECISION_LEVELS = {
    # 日常（L0 规则）
    "daily_expense": DecisionLevel.ROUTINE,
    "commute": DecisionLevel.ROUTINE,
    "social_interaction": DecisionLevel.ROUTINE,
    "meal_choice": DecisionLevel.ROUTINE,
    "entertainment": DecisionLevel.ROUTINE,
    "minor_purchase": DecisionLevel.ROUTINE,

    # 关键（L1 本地 LLM）
    "career_change": DecisionLevel.IMPORTANT,
    "marriage": DecisionLevel.IMPORTANT,
    "divorce": DecisionLevel.IMPORTANT,
    "home_purchase": DecisionLevel.IMPORTANT,
    "education_choice": DecisionLevel.IMPORTANT,
    "major_investment": DecisionLevel.IMPORTANT,
    "health_treatment": DecisionLevel.IMPORTANT,

    # 重大（L2 线上 LLM）
    "start_business": DecisionLevel.CRITICAL,
    "migration": DecisionLevel.CRITICAL,
    "crime_decision": DecisionLevel.CRITICAL,
    "life_direction": DecisionLevel.CRITICAL,
    "political_action": DecisionLevel.CRITICAL,
}


class DecisionEngine:
    """三级混合决策引擎"""

    def __init__(self, config: Dict = None):
        config = config or {}
        self.mode = EngineMode(config.get('mode', 'rule_only'))
        self.local_model = config.get('local_model', 'qwen2.5:7b')
        self.local_endpoint = config.get('local_endpoint', 'http://localhost:11434')
        self.remote_model = config.get('remote_model', 'qwen-plus')
        self.remote_api_key = config.get('api_key', '')
        self.remote_endpoint = config.get('remote_endpoint', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.monthly_budget = config.get('monthly_budget', 50.0)  # 月预算（元）
        self.budget_used = 0.0

        # 统计
        self.stats = {
            'total_decisions': 0,
            'rule_decisions': 0,
            'local_llm_decisions': 0,
            'remote_llm_decisions': 0,
            'fallback_to_rule': 0,
            'total_cost': 0.0,
            'total_latency_ms': 0.0,
        }

    def decide(self, agent, context: DecisionContext) -> Decision:
        """统一决策入口"""
        t0 = time.time()

        level = self._classify(context)
        decision = self._dispatch(agent, context, level)

        decision.latency_ms = (time.time() - t0) * 1000
        self._update_stats(decision)
        return decision

    def _classify(self, ctx: DecisionContext) -> DecisionLevel:
        """决策分级"""
        level = DECISION_LEVELS.get(ctx.decision_type, DecisionLevel.ROUTINE)
        # 高紧迫度可以升级决策级别
        if ctx.urgency > 0.8 and level == DecisionLevel.ROUTINE:
            level = DecisionLevel.IMPORTANT
        return level

    def _dispatch(self, agent, ctx: DecisionContext, level: DecisionLevel) -> Decision:
        """分发到对应引擎"""
        if level == DecisionLevel.ROUTINE or self.mode == EngineMode.RULE_ONLY:
            return self._rule_decide(agent, ctx)

        if level == DecisionLevel.IMPORTANT:
            if self.mode in (EngineMode.HYBRID, EngineMode.FULL_LLM):
                result = self._local_llm_decide(agent, ctx)
                if result:
                    return result
            return self._rule_decide(agent, ctx)  # 降级

        if level == DecisionLevel.CRITICAL:
            if self.mode == EngineMode.FULL_LLM:
                if self.budget_used < self.monthly_budget:
                    result = self._remote_llm_decide(agent, ctx)
                    if result:
                        return result
                # 超预算或失败，降级到本地
                result = self._local_llm_decide(agent, ctx)
                if result:
                    return result
            elif self.mode == EngineMode.HYBRID:
                result = self._local_llm_decide(agent, ctx)
                if result:
                    return result

        return self._rule_decide(agent, ctx)  # 最终降级

    # ── L0: 规则引擎 ──

    def _rule_decide(self, agent, ctx: DecisionContext) -> Decision:
        """纯规则决策"""
        if not ctx.options:
            return Decision(choice="maintain_status_quo", reasoning="no options", engine_used="rule")

        # 基于 Agent 属性的加权随机选择
        weights = self._calculate_weights(agent, ctx)
        if weights and len(weights) == len(ctx.options):
            total = sum(weights)
            if total > 0:
                normalized = [w / total for w in weights]
                choice = random.choices(ctx.options, weights=normalized, k=1)[0]
            else:
                choice = random.choice(ctx.options)
        else:
            choice = random.choice(ctx.options)

        return Decision(
            choice=choice,
            reasoning="rule-based weighted random",
            confidence=0.6,
            engine_used="rule"
        )

    def _calculate_weights(self, agent, ctx: DecisionContext) -> List[float]:
        """根据 Agent 状态计算选项权重"""
        n = len(ctx.options)
        weights = [1.0] * n

        happiness = getattr(agent, 'happiness', 50)
        income = getattr(agent, 'income', 0)
        age = getattr(agent, 'age', 30)
        health = getattr(agent, 'health_score', 80)

        dt = ctx.decision_type

        if dt == "career_change":
            # 不开心 + 低收入 → 更倾向换工作
            if happiness < 40 or income < 3000:
                weights[0] = 2.0  # 假设第一个选项是"换"
            else:
                weights[-1] = 2.0  # 最后一个是"不换"

        elif dt == "marriage":
            # 年龄 25-35 + 开心 → 更倾向结婚
            if 25 <= age <= 35 and happiness > 50:
                weights[0] = 2.5

        elif dt == "home_purchase":
            # 有钱 + 没房 → 更倾向买
            if income > 10000:
                weights[0] = 2.0

        elif dt == "crime_decision":
            # 低收入 + 不开心 + 年轻 → 风险更高
            risk = max(0.1, (100 - happiness) / 100 * (50000 - min(income, 50000)) / 50000)
            if age < 30:
                risk *= 1.5
            weights[0] = risk  # 犯罪选项
            weights[-1] = 1 - risk  # 不犯罪

        elif dt == "health_treatment":
            if health < 50:
                weights[0] = 3.0  # 治疗

        return weights

    # ── L1: 本地 LLM ──

    def _local_llm_decide(self, agent, ctx: DecisionContext) -> Optional[Decision]:
        """本地 LLM 决策（Ollama）"""
        try:
            import requests
            prompt = self._build_prompt(agent, ctx)
            resp = requests.post(
                f"{self.local_endpoint}/api/generate",
                json={
                    "model": self.local_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 200}
                },
                timeout=10
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                choice, reasoning = self._parse_llm_response(text, ctx.options)
                return Decision(
                    choice=choice,
                    reasoning=reasoning,
                    confidence=0.75,
                    engine_used="local_llm"
                )
        except Exception:
            self.stats['fallback_to_rule'] += 1
        return None  # 失败，调用方会降级

    # ── L2: 线上 LLM ──

    def _remote_llm_decide(self, agent, ctx: DecisionContext) -> Optional[Decision]:
        """线上 LLM 决策（API）"""
        if not self.remote_api_key:
            return None

        try:
            import requests
            prompt = self._build_prompt(agent, ctx)
            resp = requests.post(
                f"{self.remote_endpoint}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.remote_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.remote_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 200
                },
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                # 估算成本
                usage = data.get("usage", {})
                cost = (usage.get("total_tokens", 0) / 1000) * 0.002  # 大约
                self.budget_used += cost

                choice, reasoning = self._parse_llm_response(text, ctx.options)
                return Decision(
                    choice=choice,
                    reasoning=reasoning,
                    confidence=0.85,
                    engine_used="remote_llm",
                    cost=cost
                )
        except Exception:
            self.stats['fallback_to_rule'] += 1
        return None

    # ── 辅助方法 ──

    def _build_prompt(self, agent, ctx: DecisionContext) -> str:
        """构建 LLM 提示"""
        agent_info = f"""Agent Profile:
- Age: {getattr(agent, 'age', 'unknown')}, Gender: {getattr(agent, 'gender', 'unknown')}
- Income: {getattr(agent, 'income', 0):.0f}/month
- Happiness: {getattr(agent, 'happiness', 50):.0f}/100
- Health: {getattr(agent, 'health_score', 80):.0f}/100
- Education: {getattr(agent, 'education_level', 'unknown')}
- Marital Status: {getattr(agent, 'marital_status', 'single')}
- Occupation: {getattr(agent, 'occupation', 'unknown')}"""

        options_str = "\n".join(f"  {i+1}. {opt}" for i, opt in enumerate(ctx.options))

        prompt = f"""{agent_info}

Decision: {ctx.decision_type}
Options:
{options_str}

{ctx.custom_prompt if ctx.custom_prompt else ''}

Choose the most realistic option for this person. Reply with ONLY:
CHOICE: <option text>
REASON: <one sentence>"""

        return prompt

    def _parse_llm_response(self, text: str, options: List[str]) -> tuple:
        """解析 LLM 响应"""
        choice = options[0] if options else "unknown"
        reasoning = text.strip()

        # 尝试解析 CHOICE: xxx 格式
        for line in text.split("\n"):
            line = line.strip()
            if line.upper().startswith("CHOICE:"):
                raw = line[7:].strip()
                # 模糊匹配选项
                for opt in options:
                    if opt.lower() in raw.lower() or raw.lower() in opt.lower():
                        choice = opt
                        break
            elif line.upper().startswith("REASON:"):
                reasoning = line[7:].strip()

        return choice, reasoning

    def _update_stats(self, decision: Decision):
        """更新统计"""
        self.stats['total_decisions'] += 1
        self.stats['total_latency_ms'] += decision.latency_ms
        self.stats['total_cost'] += decision.cost
        if decision.engine_used == "rule":
            self.stats['rule_decisions'] += 1
        elif decision.engine_used == "local_llm":
            self.stats['local_llm_decisions'] += 1
        elif decision.engine_used == "remote_llm":
            self.stats['remote_llm_decisions'] += 1

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.stats['total_decisions']
        return {
            **self.stats,
            'avg_latency_ms': self.stats['total_latency_ms'] / max(total, 1),
            'budget_remaining': self.monthly_budget - self.budget_used,
            'mode': self.mode.value,
        }

    def get_config(self) -> Dict:
        """获取当前配置（供前端展示）"""
        return {
            'mode': self.mode.value,
            'local_model': self.local_model,
            'remote_model': self.remote_model,
            'monthly_budget': self.monthly_budget,
            'budget_used': self.budget_used,
        }

    def update_config(self, new_config: Dict) -> None:
        """更新配置（供前端调用）"""
        if 'mode' in new_config:
            self.mode = EngineMode(new_config['mode'])
        if 'local_model' in new_config:
            self.local_model = new_config['local_model']
        if 'remote_model' in new_config:
            self.remote_model = new_config['remote_model']
        if 'api_key' in new_config:
            self.remote_api_key = new_config['api_key']
        if 'monthly_budget' in new_config:
            self.monthly_budget = new_config['monthly_budget']
