"""
涌现行为检测框架
检测 Agent 群体中的涌现模式：群体极化、信息茧房、经济分层固化、
文化聚集、社会运动、技术扩散等
"""
import math
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter


class EmergenceDetector:
    """涌现行为检测器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.history: List[Dict] = []  # 历史检测结果
        self.alerts: List[Dict] = []   # 涌现警报
    
    def detect_all(self, agents: dict, events: list = None, month: int = 0) -> Dict:
        """运行所有检测器"""
        results = {
            'month': month,
            'detectors': {},
            'alerts': [],
            'summary': ''
        }
        
        agent_list = list(agents.values()) if isinstance(agents, dict) else agents
        if len(agent_list) < 10:
            return results
        
        # 1. 经济不平等检测（基尼系数）
        results['detectors']['economic_inequality'] = self._detect_inequality(agent_list)
        
        # 2. 群体极化检测（幸福感/压力两极分化）
        results['detectors']['polarization'] = self._detect_polarization(agent_list)
        
        # 3. 社会分层固化检测
        results['detectors']['stratification'] = self._detect_stratification(agent_list)
        
        # 4. MBTI 聚集检测（某些类型是否过度成功）
        results['detectors']['mbti_advantage'] = self._detect_mbti_advantage(agent_list)
        
        # 5. 职业集中度检测
        results['detectors']['occupation_concentration'] = self._detect_occupation_concentration(agent_list)
        
        # 6. 健康危机检测
        results['detectors']['health_crisis'] = self._detect_health_crisis(agent_list)
        
        # 7. 婚姻模式检测
        results['detectors']['marriage_patterns'] = self._detect_marriage_patterns(agent_list)
        
        # 生成警报
        for name, result in results['detectors'].items():
            if result.get('alert'):
                alert = {'detector': name, 'level': result['alert_level'], 
                         'message': result['alert_message'], 'month': month}
                results['alerts'].append(alert)
                self.alerts.append(alert)
        
        # 汇总
        alert_count = len(results['alerts'])
        results['summary'] = f"检测完成：{len(results['detectors'])}项，{alert_count}个警报"
        
        self.history.append(results)
        if len(self.history) > 120:  # [Phase3 Fix] 保留最近120个月，防止内存泄漏
            self.history = self.history[-120:]
        return results
    
    def _detect_inequality(self, agents) -> Dict:
        """基尼系数检测"""
        incomes = sorted([getattr(a, 'income', 0) for a in agents if getattr(a, 'is_alive', True)])
        n = len(incomes)
        if n < 2 or sum(incomes) == 0:
            return {'gini': 0, 'alert': False}
        
        total = sum(incomes)
        cum = 0
        area = 0
        for i, inc in enumerate(incomes):
            cum += inc
            area += cum
        gini = 1 - 2 * area / (n * total) + 1/n
        gini = max(0, min(1, gini))
        
        alert = gini > 0.5
        return {
            'gini': round(gini, 4),
            'alert': alert,
            'alert_level': 'critical' if gini > 0.65 else ('warning' if gini > 0.5 else 'info'),
            'alert_message': f'收入基尼系数 {gini:.3f}，{"严重不平等" if gini > 0.65 else "不平等加剧"}' if alert else '',
            'top10_share': round(sum(incomes[-n//10:]) / total * 100, 1) if total > 0 else 0,
            'bottom50_share': round(sum(incomes[:n//2]) / total * 100, 1) if total > 0 else 0,
        }
    
    def _detect_polarization(self, agents) -> Dict:
        """幸福感/压力极化检测"""
        happy = [getattr(a, 'happiness', 50) for a in agents if getattr(a, 'is_alive', True)]
        if not happy:
            return {'alert': False}
        
        mean_h = sum(happy) / len(happy)
        variance = sum((h - mean_h) ** 2 for h in happy) / len(happy)
        std = math.sqrt(variance)
        
        # 检测双峰分布（极化）
        low = sum(1 for h in happy if h < 30)
        high = sum(1 for h in happy if h > 70)
        mid = len(happy) - low - high
        
        is_polarized = low > len(happy) * 0.2 and high > len(happy) * 0.2
        
        return {
            'happiness_std': round(std, 2),
            'happiness_mean': round(mean_h, 2),
            'low_happiness_pct': round(low / len(happy) * 100, 1),
            'high_happiness_pct': round(high / len(happy) * 100, 1),
            'is_polarized': is_polarized,
            'alert': is_polarized,
            'alert_level': 'warning',
            'alert_message': f'社会极化：{low/len(happy)*100:.0f}%低幸福 vs {high/len(happy)*100:.0f}%高幸福' if is_polarized else ''
        }
    
    def _detect_stratification(self, agents) -> Dict:
        """社会分层固化：教育-收入相关性"""
        edu_income = defaultdict(list)
        for a in agents:
            if not getattr(a, 'is_alive', True):
                continue
            edu = getattr(a, 'education_level', 'unknown')
            inc = getattr(a, 'income', 0)
            edu_income[edu].append(inc)
        
        avgs = {k: sum(v)/len(v) for k, v in edu_income.items() if v}
        edu_order = ['elementary', 'middle', 'high_school', 'college', 'bachelor', 'master', 'phd']
        ordered = [(e, avgs.get(e, 0)) for e in edu_order if e in avgs]
        
        # 检测是否严格递增（固化）
        is_rigid = all(ordered[i][1] <= ordered[i+1][1] for i in range(len(ordered)-1)) if len(ordered) > 2 else False
        
        return {
            'education_income': avgs,
            'is_rigid': is_rigid,
            'alert': False,
            'alert_level': 'info',
            'alert_message': ''
        }
    
    def _detect_mbti_advantage(self, agents) -> Dict:
        """MBTI 类型优势检测"""
        mbti_income = defaultdict(list)
        for a in agents:
            if not getattr(a, 'is_alive', True):
                continue
            mbti = getattr(a, 'mbti', 'UNKNOWN')
            mbti_income[mbti].append(getattr(a, 'income', 0))
        
        avgs = {k: round(sum(v)/len(v), 0) for k, v in mbti_income.items() if len(v) > 5}
        if not avgs:
            return {'alert': False}
        
        overall_avg = sum(sum(v) for v in mbti_income.values()) / sum(len(v) for v in mbti_income.values())
        top = max(avgs.items(), key=lambda x: x[1])
        bottom = min(avgs.items(), key=lambda x: x[1])
        gap = (top[1] - bottom[1]) / overall_avg if overall_avg > 0 else 0
        
        return {
            'mbti_avg_income': avgs,
            'top_type': {'type': top[0], 'avg_income': top[1]},
            'bottom_type': {'type': bottom[0], 'avg_income': bottom[1]},
            'gap_ratio': round(gap, 3),
            'alert': gap > 0.5,
            'alert_level': 'warning' if gap > 0.5 else 'info',
            'alert_message': f'MBTI收入差距：{top[0]}(${top[1]:,.0f}) vs {bottom[0]}(${bottom[1]:,.0f})' if gap > 0.5 else ''
        }
    
    def _detect_occupation_concentration(self, agents) -> Dict:
        """职业集中度（赫芬达尔指数）"""
        occ_counts = Counter(getattr(a, 'occupation', 'unknown') for a in agents if getattr(a, 'is_alive', True))
        total = sum(occ_counts.values())
        if total == 0:
            return {'alert': False}
        
        hhi = sum((c/total)**2 for c in occ_counts.values())
        top3 = occ_counts.most_common(3)
        
        return {
            'hhi': round(hhi, 4),
            'top3_occupations': [{'name': k, 'count': v, 'pct': round(v/total*100, 1)} for k, v in top3],
            'total_occupations': len(occ_counts),
            'alert': hhi > 0.25,
            'alert_level': 'warning',
            'alert_message': f'职业过度集中(HHI={hhi:.3f})' if hhi > 0.25 else ''
        }
    
    def _detect_health_crisis(self, agents) -> Dict:
        """健康危机检测"""
        healths = [getattr(a, 'health_score', 80) for a in agents if getattr(a, 'is_alive', True)]
        if not healths:
            return {'alert': False}
        
        avg = sum(healths) / len(healths)
        critical = sum(1 for h in healths if h < 30)
        critical_pct = critical / len(healths) * 100
        
        return {
            'avg_health': round(avg, 1),
            'critical_count': critical,
            'critical_pct': round(critical_pct, 1),
            'alert': critical_pct > 10,
            'alert_level': 'critical' if critical_pct > 20 else 'warning',
            'alert_message': f'健康危机：{critical_pct:.0f}%人口健康值<30' if critical_pct > 10 else ''
        }
    
    def _detect_marriage_patterns(self, agents) -> Dict:
        """婚姻模式检测"""
        statuses = Counter(getattr(a, 'marital_status', 'unknown') for a in agents if getattr(a, 'is_alive', True))
        total = sum(statuses.values())
        if total == 0:
            return {'alert': False}
        
        single_rate = statuses.get('single', 0) / total * 100
        married_rate = statuses.get('married', 0) / total * 100
        divorced_rate = statuses.get('divorced', 0) / total * 100
        
        return {
            'distribution': {k: round(v/total*100, 1) for k, v in statuses.items()},
            'single_rate': round(single_rate, 1),
            'married_rate': round(married_rate, 1),
            'divorced_rate': round(divorced_rate, 1),
            'alert': divorced_rate > 20 or single_rate > 70,
            'alert_level': 'warning',
            'alert_message': f'婚姻异常：{"离婚率"+str(round(divorced_rate))+"%" if divorced_rate > 20 else "单身率"+str(round(single_rate))+"%"}' if (divorced_rate > 20 or single_rate > 70) else ''
        }
    
    def get_trend(self, detector_name: str, metric: str) -> List:
        """获取某检测器某指标的历史趋势"""
        return [
            {'month': h['month'], 'value': h['detectors'].get(detector_name, {}).get(metric)}
            for h in self.history
            if detector_name in h.get('detectors', {})
        ]
