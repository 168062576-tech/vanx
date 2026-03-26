# -*- coding: utf-8 -*-
"""
御龙军虚拟世界 v5 - 整合增强模块
移植自 v1.0，适配 v5 UnifiedAgent
功能：Agent 讨论系统 + 运营顾问 + 数据导出器 + HTML 报告生成器
"""

import random
import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


# ================================================================
# 1. Agent 讨论系统
# ================================================================

class AgentDiscussionSystem:
    """Agent 讨论系统 - 让虚拟人对产品发表意见（v5 增强版）"""

    OPINION_TEMPLATES = {
        "positive": [
            "这个产品解决了我一直以来的痛点，{reason}",
            "价格合理，我愿意购买，因为{reason}",
            "我已经推荐给朋友了，{reason}",
            "质量不错，值得信赖，{reason}",
            "用了之后效率提升了，{reason}",
            "这是市场上最好的选择之一，{reason}",
        ],
        "negative": [
            "价格太贵了，超出我的预算，{reason}",
            "我暂时不需要这个产品，{reason}",
            "功能不太符合我的需求，{reason}",
            "有更便宜的替代品，{reason}",
            "试用后觉得不值这个价，{reason}",
            "不太信任这个品牌，{reason}",
        ],
        "neutral": [
            "还在观望，需要看看别人的评价，{reason}",
            "有一些优点，但也有不足，{reason}",
            "如果能打折我可能会买，{reason}",
            "需要更多信息才能决定，{reason}",
            "看起来还行，但不急着买，{reason}",
        ]
    }

    REASON_BY_FACTOR = {
        "income_low": "我的收入不太够",
        "income_ok": "在我的承受范围内",
        "young": "我们年轻人比较喜欢尝新",
        "old": "我比较谨慎，不轻易买新东西",
        "educated": "我研究了一下觉得有道理",
        "social": "我朋友推荐的",
        "quality": "产品质量是关键",
        "price": "性价比很重要",
        "need": "确实有这个需求",
        "no_need": "目前没有这个需求",
        # v5 新增
        "stressed": "最近压力大，买点好的犒劳自己",
        "happy": "心情不错，愿意尝试新东西",
        "family": "家里人也需要这个",
        "healthy": "对健康有帮助我就支持",
    }

    def generate_discussions(self, agents: Dict, product_states: Dict,
                             product_name: str, price: float,
                             sample_size: int = 20) -> Dict:
        """
        生成 Agent 讨论内容

        Args:
            agents: {agent_id: UnifiedAgent}
            product_states: {agent_id: AgentProductState}
            product_name: 产品名称
            price: 产品价格
            sample_size: 抽样人数

        Returns: {
            "voices": [...],
            "summary": {...},
            "report_text": str,
        }
        """
        agent_list = list(agents.values())
        if len(agent_list) > sample_size:
            buyers = [a for a in agent_list if product_states.get(a.id) and product_states[a.id].purchased]
            non_buyers = [a for a in agent_list if not (product_states.get(a.id) and product_states[a.id].purchased)]

            n_buyers = min(len(buyers), sample_size // 3)
            n_non = min(len(non_buyers), sample_size - n_buyers)
            sampled = random.sample(buyers, n_buyers) + random.sample(non_buyers, n_non)
        else:
            sampled = agent_list

        voices = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}

        for agent in sampled:
            state = product_states.get(agent.id)
            is_buyer = state and state.purchased if state else False
            satisfaction = state.satisfaction if state and state.purchased else 0

            # 判断情感倾向
            if is_buyer and satisfaction > 65:
                sentiment = "positive"
            elif is_buyer and satisfaction <= 65:
                sentiment = "neutral"
            elif not is_buyer:
                income = getattr(agent, 'income', 5000)
                age = getattr(agent, 'age', 30)
                if income < price * 20 or age > 55:
                    sentiment = "negative"
                elif random.random() < 0.4:
                    sentiment = "neutral"
                else:
                    sentiment = "negative"
            else:
                sentiment = "neutral"

            sentiment_counts[sentiment] += 1

            reason = self._pick_reason(agent, price, is_buyer)
            template = random.choice(self.OPINION_TEMPLATES[sentiment])
            text = template.format(reason=reason)

            # v5: 使用 UnifiedAgent 字段（无 name 字段，用 Agent_{id}）
            name = f'Agent_{agent.id}'
            age = getattr(agent, 'age', 0)
            gender = '男' if getattr(agent, 'gender', '') == 'male' else '女'
            occ = getattr(agent, 'occupation', '未知')
            income = getattr(agent, 'income', 0)
            edu = getattr(agent, 'education_level', '未知')
            mbti = getattr(agent, 'mbti', '')

            voices.append({
                "name": name,
                "age": age,
                "gender": gender,
                "occupation": occ,
                "income": round(income),
                "education": edu,
                "mbti": mbti,
                "sentiment": sentiment,
                "is_buyer": is_buyer,
                "satisfaction": round(satisfaction, 1) if is_buyer else None,
                "text": text,
            })

        total = len(voices)
        report_text = self._build_report_text(voices, sentiment_counts, total, product_name)

        return {
            "voices": voices,
            "summary": {
                "total_sampled": total,
                "positive": sentiment_counts["positive"],
                "negative": sentiment_counts["negative"],
                "neutral": sentiment_counts["neutral"],
                "positive_rate": round(sentiment_counts["positive"] / max(total, 1) * 100, 1),
                "negative_rate": round(sentiment_counts["negative"] / max(total, 1) * 100, 1),
            },
            "report_text": report_text,
        }

    def _pick_reason(self, agent, price, is_buyer):
        income = getattr(agent, 'income', 5000)
        age = getattr(agent, 'age', 30)
        edu = getattr(agent, 'education_level', 'high_school')
        stress = getattr(agent, 'stress', 40)
        happiness = getattr(agent, 'happiness', 60)
        marital = getattr(agent, 'marital_status', 'single')
        children = getattr(agent, 'children', [])

        reasons = []
        if income < price * 15:
            reasons.append(self.REASON_BY_FACTOR["income_low"])
        else:
            reasons.append(self.REASON_BY_FACTOR["income_ok"])
        if age < 30:
            reasons.append(self.REASON_BY_FACTOR["young"])
        elif age > 50:
            reasons.append(self.REASON_BY_FACTOR["old"])
        if edu in ('bachelor', 'master', 'phd'):
            reasons.append(self.REASON_BY_FACTOR["educated"])
        if is_buyer:
            reasons.append(self.REASON_BY_FACTOR["need"])
        else:
            reasons.append(self.REASON_BY_FACTOR["no_need"])

        # v5: 压力/幸福/家庭因素
        if stress > 70:
            reasons.append(self.REASON_BY_FACTOR["stressed"])
        if happiness > 75:
            reasons.append(self.REASON_BY_FACTOR["happy"])
        if marital == 'married' and len(children) > 0:
            reasons.append(self.REASON_BY_FACTOR["family"])

        return random.choice(reasons)

    def _build_report_text(self, voices, counts, total, product_name):
        text = f"""
{'='*80}
🗣️ Agent 真实声音 — 他们怎么看「{product_name}」
{'='*80}

舆情概览：（抽样 {total} 人）
  👍 正面评价：{counts['positive']} 人 ({counts['positive']/max(total,1)*100:.1f}%)
  👎 负面评价：{counts['negative']} 人 ({counts['negative']/max(total,1)*100:.1f}%)
  😐 中立观望：{counts['neutral']} 人 ({counts['neutral']/max(total,1)*100:.1f}%)

"""
        selected = voices[:12]
        text += "—— 精选 Agent 声音 ——\n\n"
        for v in selected:
            buyer_tag = "✅已购买" if v['is_buyer'] else "❌未购买"
            sat_tag = f" 满意度:{v['satisfaction']}" if v['satisfaction'] else ""
            mbti_tag = f"/{v['mbti']}" if v.get('mbti') else ""
            text += f"  💬 {v['name']}（{v['age']}岁/{v['gender']}/{v['occupation']}/月入¥{v['income']:,}{mbti_tag}）[{buyer_tag}{sat_tag}]\n"
            text += f"     「{v['text']}」\n\n"

        return text


# ================================================================
# 2. 运营建议生成器
# ================================================================

class OperationsAdvisor:
    """运营策略建议生成器"""

    def generate_advice(self, market_metrics: Dict, product_config=None) -> str:
        """根据市场数据生成具体运营建议"""
        latest = market_metrics.get("latest_metrics", {})
        conv = market_metrics.get("conversion_rates", {})
        funnel = market_metrics.get("funnel", {})
        buyer = market_metrics.get("buyer_profile", {})

        awareness = latest.get("awareness_rate", 0)
        purchase_rate = latest.get("purchase_rate", 0)
        churn_rate = latest.get("churn_rate", 0)
        satisfaction = latest.get("avg_satisfaction", 0)
        nps = latest.get("nps", 0)
        viral = latest.get("viral_coefficient", 0)
        a2i = conv.get("awareness_to_interest", 0)
        i2t = conv.get("interest_to_trial", 0)
        t2p = conv.get("trial_to_purchase", 0)
        revenue = latest.get("total_revenue", 0)

        sections = []

        sections.append(f"""
{'='*80}
🔧 运营优化建议（基于数据诊断）
{'='*80}
""")

        if awareness < 20:
            sections.append("""
📢 【认知阶段 — 严重不足】
  问题：产品知名度极低，大部分目标用户不知道你的存在
  建议：
    1. 加大社交媒体投放（短视频/信息流广告）
    2. 与 KOL/KOC 合作推广
    3. 参加行业展会/线下活动
    4. SEO 优化 + 内容营销（博客/白皮书）
    5. 考虑限时免费试用活动引爆关注
""")
        elif awareness < 40:
            sections.append("""
📢 【认知阶段 — 有待提升】
  问题：认知度中等，增长空间大
  建议：
    1. 优化广告投放 ROI，聚焦高转化渠道
    2. 打造 1-2 个爆款内容/案例
    3. 口碑推荐计划（老带新奖励）
""")

        if a2i < 40:
            sections.append(f"""
🎯 【兴趣阶段 — 转化率低 {a2i:.1f}%】
  问题：用户知道了但不感兴趣，说明卖点没打动人
  建议：
    1. 重新提炼核心卖点（用户语言，不是技术语言）
    2. 优化落地页/产品介绍页
    3. 增加社会证明（客户案例/评价/数据）
    4. A/B 测试不同的价值主张
""")

        if i2t < 40:
            sections.append(f"""
🧪 【试用阶段 — 转化率低 {i2t:.1f}%】
  问题：用户感兴趣但不愿试用，门槛太高
  建议：
    1. 提供免费试用/演示（降低决策门槛）
    2. 简化注册/试用流程（3 步内完成）
    3. 提供新手引导（视频教程/交互式指引）
    4. 限时体验活动
""")

        if t2p < 40:
            sections.append(f"""
💳 【购买阶段 — 转化率低 {t2p:.1f}%】
  问题：试用后不买，可能是价格或体验问题
  建议：
    1. 检查定价策略（对比竞品，考虑分级定价）
    2. 首单优惠（限时折扣/优惠券）
    3. 分期付款选项
    4. 提升产品核心体验（解决试用中的痛点）
    5. 增加紧迫感（限时/限量）
""")

        if churn_rate > 20:
            sections.append(f"""
🚨 【留存阶段 — 流失率高 {churn_rate:.1f}%】
  问题：客户买了又走，产品粘性不足
  建议：
    1. 建立客户成功体系（主动关怀）
    2. 增加使用场景和功能深度
    3. 会员/积分/等级体系
    4. 定期内容推送（使用技巧/行业洞察）
    5. 流失预警机制（活跃度下降时介入）
""")

        if nps < 0:
            sections.append(f"""
👎 【口碑阶段 — NPS 为负 ({nps})】
  问题：贬损者多于推荐者，口碑有风险
  建议：
    1. 紧急收集差评原因并逐一解决
    2. 建立快速响应的客服体系
    3. 对高满意度客户激励推荐
    4. 暂缓大规模推广（先修口碑）
""")
        elif nps > 30 and viral < 0.1:
            sections.append(f"""
👍 【口碑阶段 — NPS 优秀但传播不足】
  问题：客户满意但没有主动传播
  建议：
    1. 推荐奖励计划（推荐成功双方都得奖）
    2. 让分享变简单（一键分享/生成推荐海报）
    3. 打造"值得晒"的产品体验
    4. 社区运营（用户群/论坛/UGC）
""")

        if purchase_rate > 10:
            grade = "A（优秀）"
        elif purchase_rate > 5:
            grade = "B（良好）"
        elif purchase_rate > 2:
            grade = "C（及格）"
        else:
            grade = "D（需改进）"

        sections.append(f"""
{'='*80}
📊 整体评级：{grade}
{'='*80}
  购买转化率：{purchase_rate:.1f}%
  客户满意度：{satisfaction:.1f}/100
  NPS 净推荐值：{nps}
  口碑传播系数：{viral:.3f}
  累计营收：¥{revenue:,.2f}
""")

        # v5: 增强买家画像建议（含 MBTI、幸福度、压力）
        if buyer and buyer.get("count", 0) > 0:
            mbti_info = ""
            mbti_top5 = buyer.get('mbti_top5', {})
            if mbti_top5:
                mbti_info = f"\n    • MBTI Top5：{', '.join(f'{k}:{v}' for k,v in mbti_top5.items())}"
            
            happiness_info = ""
            avg_happiness = buyer.get('avg_happiness')
            avg_stress = buyer.get('avg_stress')
            if avg_happiness is not None:
                happiness_info = f"\n    • 平均幸福度：{avg_happiness:.1f}  |  平均压力：{avg_stress:.1f}"

            sections.append(f"""
{'='*80}
👥 目标用户精准画像建议
{'='*80}
  基于购买数据，你的核心用户是：
    • 年龄：{buyer.get('avg_age', 0)} 岁（范围 {buyer.get('age_range', '-')}）
    • 月收入：¥{buyer.get('avg_income', 0):,.0f}
    • 学历分布：{buyer.get('education', {})}
    • 性别分布：{buyer.get('gender', {})}{mbti_info}{happiness_info}

  建议：
    1. 广告投放精准定向以上人群
    2. 产品功能优先满足核心用户需求
    3. 内容营销用核心用户的语言和场景
""")

        return "\n".join(sections)


# ================================================================
# 3. 数据导出器
# ================================================================

class ExperimentDataExporter:
    """实验数据导出器"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_csv(self, monthly_metrics: List[Dict], experiment_id: str) -> str:
        """导出月度数据为 CSV"""
        if not monthly_metrics:
            return ""
        filepath = os.path.join(self.output_dir, f"{experiment_id}_monthly.csv")
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=monthly_metrics[0].keys())
            writer.writeheader()
            writer.writerows(monthly_metrics)
        return filepath

    def export_json(self, data: Dict, experiment_id: str) -> str:
        """导出完整数据为 JSON"""
        filepath = os.path.join(self.output_dir, f"{experiment_id}_full.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return filepath

    def export_buyer_list(self, agents: Dict, product_states: Dict,
                          experiment_id: str) -> str:
        """导出购买者清单（v5 增强：含 MBTI、婚姻、净资产）"""
        filepath = os.path.join(self.output_dir, f"{experiment_id}_buyers.csv")
        rows = []
        for aid, state in product_states.items():
            if state.purchased:
                agent = agents.get(aid)
                if agent:
                    rows.append({
                        "ID": aid,
                        "年龄": getattr(agent, 'age', 0),
                        "性别": getattr(agent, 'gender', ''),
                        "职业": getattr(agent, 'occupation', ''),
                        "月收入": round(getattr(agent, 'income', 0)),
                        "净资产": round(getattr(agent, 'net_worth', 0)),
                        "学历": getattr(agent, 'education_level', ''),
                        "MBTI": getattr(agent, 'mbti', ''),
                        "婚姻状态": getattr(agent, 'marital_status', ''),
                        "子女数": len(getattr(agent, 'children', [])),
                        "幸福度": round(getattr(agent, 'happiness', 0), 1),
                        "压力": round(getattr(agent, 'stress', 0), 1),
                        "购买月份": state.purchase_month,
                        "累计消费": round(state.total_spent, 2),
                        "满意度": round(state.satisfaction, 1),
                        "会推荐": "是" if state.will_recommend else "否",
                        "已流失": "是" if state.churned else "否",
                    })
        if rows:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        return filepath


# ================================================================
# 4. HTML 可视化报告
# ================================================================

class HTMLReportGenerator:
    """生成可在浏览器查看的 HTML 可视化报告"""

    def generate(self, experiment_id: str, product_analysis: Dict,
                 discussion: Dict, advice_text: str,
                 product_report_text: str, user_context: Dict) -> str:
        """生成完整 HTML 报告"""
        funnel = product_analysis.get("funnel", {})
        latest = product_analysis.get("latest_metrics", {})
        monthly = product_analysis.get("monthly_metrics", [])
        buyer = product_analysis.get("buyer_profile", {})
        conv = product_analysis.get("conversion_rates", {})
        disc_summary = discussion.get("summary", {})

        months_json = json.dumps([m["month"] for m in monthly])
        awareness_json = json.dumps([m["awareness_rate"] for m in monthly])
        purchase_json = json.dumps([m["purchase_count"] for m in monthly])
        revenue_json = json.dumps([m["monthly_revenue"] for m in monthly])
        satisfaction_json = json.dumps([m["avg_satisfaction"] for m in monthly])

        desc = user_context.get("description", "")
        goals = user_context.get("goals", "")

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>实验报告 - {experiment_id}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Microsoft YaHei',sans-serif;background:#f5f5f5;padding:20px;color:#333}}
  .container{{max-width:1100px;margin:0 auto}}
  h1{{text-align:center;color:#667eea;margin-bottom:5px;font-size:1.8em}}
  .subtitle{{text-align:center;color:#999;margin-bottom:30px}}
  .card{{background:white;border-radius:12px;padding:25px;margin-bottom:20px;box-shadow:0 2px 10px rgba(0,0,0,.08)}}
  .card h2{{color:#667eea;margin-bottom:15px;font-size:1.3em;border-bottom:2px solid #667eea;padding-bottom:8px}}
  .metrics-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px;margin-bottom:20px}}
  .metric{{background:#f8f9ff;border-radius:10px;padding:18px;text-align:center}}
  .metric .val{{font-size:1.8em;font-weight:bold;color:#667eea}}
  .metric .lbl{{font-size:.85em;color:#888;margin-top:4px}}
  .funnel{{display:flex;flex-direction:column;align-items:center;gap:4px;margin:20px 0}}
  .funnel-step{{background:linear-gradient(90deg,#667eea,#764ba2);color:white;padding:10px;text-align:center;border-radius:6px;font-weight:bold}}
  .chart-container{{height:300px;margin:15px 0}}
  .voice{{background:#f8f9ff;border-radius:8px;padding:12px;margin-bottom:10px;border-left:4px solid #667eea}}
  .voice .meta{{font-size:.85em;color:#888;margin-bottom:5px}}
  .voice .text{{font-style:italic}}
  .advice{{background:#fff8e1;border-radius:8px;padding:15px;margin-bottom:10px;border-left:4px solid #ffc107}}
  pre{{background:#f5f5f5;padding:15px;border-radius:8px;white-space:pre-wrap;font-size:.9em;max-height:500px;overflow-y:auto}}
</style>
</head>
<body>
<div class="container">
  <h1>🐉 御龙军虚拟世界 v5 - 实验报告</h1>
  <div class="subtitle">{experiment_id} | 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>

  <div class="card">
    <h2>📄 项目概述</h2>
    <p>{desc}</p>
    {"<p><strong>🎯 目标：</strong>"+goals+"</p>" if goals else ""}
  </div>

  <div class="card">
    <h2>📊 核心指标</h2>
    <div class="metrics-row">
      <div class="metric"><div class="val">{funnel.get("purchased",0):,}</div><div class="lbl">付费用户</div></div>
      <div class="metric"><div class="val">¥{latest.get("total_revenue",0):,.0f}</div><div class="lbl">累计营收</div></div>
      <div class="metric"><div class="val">{latest.get("purchase_rate",0):.1f}%</div><div class="lbl">购买率</div></div>
      <div class="metric"><div class="val">{latest.get("avg_satisfaction",0):.0f}</div><div class="lbl">满意度</div></div>
      <div class="metric"><div class="val">{latest.get("nps",0)}</div><div class="lbl">NPS</div></div>
      <div class="metric"><div class="val">{100-latest.get("churn_rate",0):.0f}%</div><div class="lbl">留存率</div></div>
    </div>
  </div>

  <div class="card">
    <h2>📈 转化漏斗</h2>
    <div class="funnel">
      <div class="funnel-step" style="width:100%">总人口 {funnel.get("total_population",0):,}</div>
      <div class="funnel-step" style="width:{min(95,latest.get("awareness_rate",0)+5):.0f}%">认知 {funnel.get("aware",0):,} ({latest.get("awareness_rate",0):.1f}%)</div>
      <div class="funnel-step" style="width:{min(90,latest.get("interest_rate",0)+5):.0f}%">兴趣 {funnel.get("interested",0):,} ({conv.get("awareness_to_interest",0):.0f}%转化)</div>
      <div class="funnel-step" style="width:{min(80,latest.get("trial_rate",0)+5):.0f}%">试用 {funnel.get("tried",0):,} ({conv.get("interest_to_trial",0):.0f}%转化)</div>
      <div class="funnel-step" style="width:{min(70,latest.get("purchase_rate",0)+5):.0f}%">购买 {funnel.get("purchased",0):,} ({conv.get("trial_to_purchase",0):.0f}%转化)</div>
      <div class="funnel-step" style="width:{min(60,latest.get("purchase_rate",0)):.0f}%;background:#28a745">活跃 {funnel.get("active",0):,}</div>
    </div>
  </div>

  <div class="card">
    <h2>📈 月度趋势</h2>
    <div class="chart-container"><canvas id="chartTrend"></canvas></div>
    <div class="chart-container"><canvas id="chartRevenue"></canvas></div>
  </div>

  <div class="card">
    <h2>🗣️ Agent 真实声音（抽样 {disc_summary.get("total_sampled",0)} 人）</h2>
    <div class="metrics-row">
      <div class="metric"><div class="val" style="color:#28a745">{disc_summary.get("positive_rate",0):.0f}%</div><div class="lbl">👍 正面</div></div>
      <div class="metric"><div class="val" style="color:#dc3545">{disc_summary.get("negative_rate",0):.0f}%</div><div class="lbl">👎 负面</div></div>
      <div class="metric"><div class="val" style="color:#ffc107">{100-disc_summary.get("positive_rate",0)-disc_summary.get("negative_rate",0):.0f}%</div><div class="lbl">😐 中立</div></div>
    </div>
'''
        for v in discussion.get("voices", [])[:10]:
            tag = "✅" if v["is_buyer"] else "❌"
            sat = f" | 满意度:{v['satisfaction']}" if v["satisfaction"] else ""
            mbti_tag = f"/{v['mbti']}" if v.get('mbti') else ""
            html += f'''    <div class="voice">
      <div class="meta">{v["name"]}（{v["age"]}岁/{v["gender"]}/{v["occupation"]}/¥{v["income"]:,}{mbti_tag}）[{tag}{sat}]</div>
      <div class="text">「{v["text"]}」</div>
    </div>
'''
        html += '  </div>\n'

        html += f'''
  <div class="card">
    <h2>🔧 运营优化建议</h2>
    <pre>{advice_text}</pre>
  </div>

  <div class="card">
    <h2>📋 完整文本报告</h2>
    <pre>{product_report_text}</pre>
  </div>
</div>

<script>
new Chart(document.getElementById('chartTrend'),{{
  type:'line',
  data:{{
    labels:{months_json},
    datasets:[
      {{label:'认知率%',data:{awareness_json},borderColor:'#667eea',fill:false,tension:.3}},
      {{label:'购买人数',data:{purchase_json},borderColor:'#28a745',fill:false,tension:.3,yAxisID:'y1'}},
      {{label:'满意度',data:{satisfaction_json},borderColor:'#ffc107',fill:false,tension:.3}}
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{y:{{beginAtZero:true}},y1:{{position:'right',beginAtZero:true}}}}
  }}
}});
new Chart(document.getElementById('chartRevenue'),{{
  type:'bar',
  data:{{
    labels:{months_json},
    datasets:[{{label:'月收入 (¥)',data:{revenue_json},backgroundColor:'rgba(102,126,234,.6)'}}]
  }},
  options:{{responsive:true,maintainAspectRatio:false}}
}});
</script>
</body>
</html>'''
        return html
