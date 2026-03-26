"""
医疗健康系统 - Healthcare System

模拟真实的健康和医疗：
- 健康状况/疾病/慢性病
- 医疗支出/保险/预期寿命
- 心理健康/压力/抑郁
- 传染病传播/疫苗
- 医疗资源/医院/医生

作者：御龙军
日期：2026-03-17
版本：v1.0
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class HealthCondition(Enum):
    """健康状况"""
    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    FAIR = "fair"  # 一般
    POOR = "poor"  # 较差
    CRITICAL = "critical"  # 危急


class DiseaseType(Enum):
    """疾病类型"""
    COMMON_COLD = "common_cold"  # 普通感冒
    FLU = "flu"  # 流感
    PNEUMONIA = "pneumonia"  # 肺炎
    DIABETES = "diabetes"  # 糖尿病（慢性）
    HYPERTENSION = "hypertension"  # 高血压（慢性）
    HEART_DISEASE = "heart_disease"  # 心脏病
    CANCER = "cancer"  # 癌症
    DEPRESSION = "depression"  # 抑郁症
    ANXIETY = "anxiety"  # 焦虑症
    OBESITY = "obesity"  # 肥胖
    ARTHRITIS = "arthritis"  # 关节炎
    ASTHMA = "asthma"  # 哮喘
    COVID19 = "covid19"  # 新冠肺炎
    NONE = "none"  # 健康


class TreatmentType(Enum):
    """治疗类型"""
    SELF_CARE = "self_care"  # 自我护理
    MEDICATION = "medication"  # 药物治疗
    OUTPATIENT = "outpatient"  # 门诊
    HOSPITALIZATION = "hospitalization"  # 住院
    SURGERY = "surgery"  # 手术
    THERAPY = "therapy"  # 心理治疗
    EMERGENCY = "emergency"  # 急诊


@dataclass
class HealthRecord:
    """健康记录"""
    agent_id: int
    
    # 基本健康
    overall_health: float = 80.0  # 0-100
    mental_health: float = 80.0  # 0-100
    energy_level: float = 70.0  # 0-100
    immune_system: float = 70.0  # 0-100
    
    # 身体指标
    height_cm: float = 170.0
    weight_kg: float = 70.0
    bmi: float = 24.2
    
    # 生命体征
    blood_pressure_systolic: int = 120  # 收缩压
    blood_pressure_diastolic: int = 80  # 舒张压
    heart_rate: int = 72  # 心率
    blood_sugar: float = 90.0  # 血糖
    
    # 疾病
    current_diseases: List[DiseaseType] = field(default_factory=list)
    chronic_diseases: List[DiseaseType] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    
    # 医疗历史
    medical_history: List[Dict] = field(default_factory=list)
    hospitalizations: int = 0
    surgeries: int = 0
    
    # 生活习惯
    exercise_hours_weekly: float = 3.0
    sleep_hours_daily: float = 7.0
    smoking: bool = False
    alcohol_consumption: str = "moderate"  # none/moderate/heavy
    
    # 医疗
    has_insurance: bool = True
    insurance_coverage: float = 0.8  # 80% 报销
    last_checkup_date: Optional[datetime] = None
    
    def __post_init__(self):
        self._calculate_bmi()
    
    def _calculate_bmi(self):
        """计算 BMI"""
        if self.height_cm > 0:
            height_m = self.height_cm / 100
            self.bmi = self.weight_kg / (height_m ** 2)
    
    @property
    def life_expectancy_base(self) -> float:
        """基础预期寿命"""
        base = 80.0  # 基础 80 岁
        
        # BMI 影响
        if 18.5 <= self.bmi <= 24.9:
            base += 2
        elif self.bmi < 18.5 or self.bmi > 30:
            base -= 3
        
        # 生活习惯影响
        if self.exercise_hours_weekly >= 5:
            base += 3
        elif self.exercise_hours_weekly < 1:
            base -= 2
        
        if self.sleep_hours_daily >= 7:
            base += 1
        elif self.sleep_hours_daily < 5:
            base -= 3
        
        if self.smoking:
            base -= 10
        
        if self.alcohol_consumption == "heavy":
            base -= 5
        
        # 健康状况影响
        base += (self.overall_health - 50) * 0.1
        base += (self.mental_health - 50) * 0.05
        
        # 慢性病影响
        base -= len(self.chronic_diseases) * 3
        
        return max(50, min(100, base))


@dataclass
class MedicalVisit:
    """医疗就诊记录"""
    visit_id: int
    agent_id: int
    date: datetime
    reason: str
    diagnosis: DiseaseType
    treatment: TreatmentType
    cost: float
    insurance_covered: float = 0.0
    follow_up_required: bool = False


class HealthcareSystem:
    """医疗健康系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.health_records: Dict[int, HealthRecord] = {}
        self.medical_visits: List[MedicalVisit] = []
        self.visit_id_counter = 1
        
        # 疾病参数
        self.disease_params = {
            DiseaseType.COMMON_COLD: {'severity': 0.2, 'duration_days': 7, 'contagious': True, 'cost': 50},
            DiseaseType.FLU: {'severity': 0.4, 'duration_days': 14, 'contagious': True, 'cost': 200},
            DiseaseType.PNEUMONIA: {'severity': 0.7, 'duration_days': 30, 'contagious': True, 'cost': 5000},
            DiseaseType.DIABETES: {'severity': 0.5, 'duration_days': 9999, 'contagious': False, 'cost': 500},
            DiseaseType.HYPERTENSION: {'severity': 0.4, 'duration_days': 9999, 'contagious': False, 'cost': 300},
            DiseaseType.HEART_DISEASE: {'severity': 0.8, 'duration_days': 9999, 'contagious': False, 'cost': 1000},
            DiseaseType.CANCER: {'severity': 0.9, 'duration_days': 9999, 'contagious': False, 'cost': 50000},
            DiseaseType.DEPRESSION: {'severity': 0.5, 'duration_days': 9999, 'contagious': False, 'cost': 400},
            DiseaseType.ANXIETY: {'severity': 0.4, 'duration_days': 9999, 'contagious': False, 'cost': 300},
            DiseaseType.OBESITY: {'severity': 0.3, 'duration_days': 9999, 'contagious': False, 'cost': 200},
            DiseaseType.ARTHRITIS: {'severity': 0.4, 'duration_days': 9999, 'contagious': False, 'cost': 400},
            DiseaseType.ASTHMA: {'severity': 0.3, 'duration_days': 9999, 'contagious': False, 'cost': 300},
            DiseaseType.COVID19: {'severity': 0.6, 'duration_days': 21, 'contagious': True, 'cost': 3000},
        }
        
        # 医疗资源
        self.hospital_beds = 1000
        self.available_beds = 1000
        self.icu_beds = 100
        self.available_icu = 100
        
        # 流行病状态
        self.epidemic_active = False
        self.infection_rate = 0.0
    
    def create_health_record(self, agent_id: int, age: int, gender: str) -> HealthRecord:
        """创建健康记录"""
        # 根据年龄和性别设置基础数据
        if gender == 'male':
            height = random.gauss(175, 7)
            base_weight = 70
        else:
            height = random.gauss(162, 6)
            base_weight = 58
        
        # 年龄影响
        if age < 20:
            health_base = 90
        elif age < 40:
            health_base = 85
        elif age < 60:
            health_base = 75
        else:
            health_base = 65
        
        record = HealthRecord(
            agent_id=agent_id,
            height_cm=height,
            weight_kg=base_weight + random.gauss(0, 10),
            overall_health=health_base + random.gauss(0, 10),
            mental_health=health_base + random.gauss(0, 15),
        )
        
        # 年轻人更可能有良好习惯
        if age < 30:
            record.exercise_hours_weekly = random.uniform(2, 8)
            record.sleep_hours_daily = random.uniform(7, 9)
        else:
            record.exercise_hours_weekly = random.uniform(1, 5)
            record.sleep_hours_daily = random.uniform(6, 8)
        
        # 年龄相关疾病概率
        if age > 40:
            if random.random() < 0.2:
                record.chronic_diseases.append(DiseaseType.HYPERTENSION)
            if random.random() < 0.15:
                record.chronic_diseases.append(DiseaseType.DIABETES)
        
        if age > 50:
            if random.random() < 0.1:
                record.chronic_diseases.append(DiseaseType.HEART_DISEASE)
            if random.random() < 0.1:
                record.chronic_diseases.append(DiseaseType.ARTHRITIS)
        
        # 心理健康（年轻人压力大）
        if 20 <= age <= 35:
            if random.random() < 0.15:
                record.chronic_diseases.append(DiseaseType.ANXIETY)
            if random.random() < 0.1:
                record.chronic_diseases.append(DiseaseType.DEPRESSION)
        
        self.health_records[agent_id] = record
        return record
    
    def update_monthly(self, agent_id: int, age: int, months_passed: int = 1) -> List[Dict]:
        """月度健康更新"""
        if agent_id not in self.health_records:
            return []
        
        record = self.health_records[agent_id]
        events = []
        
        for _ in range(months_passed):
            # 1. 年龄增长影响
            if age >= 50:
                record.overall_health -= 0.2
                record.energy_level -= 0.3
            if age >= 60:
                record.overall_health -= 0.3
                record.immune_system -= 0.2
            
            # 2. 生活习惯影响
            if record.exercise_hours_weekly >= 3:
                record.overall_health = min(100, record.overall_health + 0.3)
                record.mental_health = min(100, record.mental_health + 0.2)
            else:
                record.overall_health = max(0, record.overall_health - 0.2)
            
            if record.sleep_hours_daily >= 7:
                record.energy_level = min(100, record.energy_level + 0.3)
            elif record.sleep_hours_daily < 5:
                record.energy_level = max(0, record.energy_level - 0.5)
                record.mental_health = max(0, record.mental_health - 0.3)
            
            # 3. BMI 变化
            if record.exercise_hours_weekly < 2:
                record.weight_kg += random.uniform(0.1, 0.5)
            elif record.exercise_hours_weekly > 5:
                record.weight_kg -= random.uniform(0.1, 0.3)
            record._calculate_bmi()
            
            # 4. 疾病发生概率
            self._check_disease_onset(record, age)
            
            # 5. 慢性病管理
            for disease in record.chronic_diseases:
                self._manage_chronic_disease(record, disease)
            
            # 6. 传染病风险
            if self.epidemic_active:
                self._check_infection(record)
            
            # 7. 心理健康
            stress_factor = random.gauss(0, 5)
            if age >= 25 and age <= 45:
                stress_factor += 3  # 中年压力大
            record.mental_health = max(0, min(100, record.mental_health - stress_factor * 0.1))
            
            # 8. 医疗支出
            if record.current_diseases:
                medical_cost = self._calculate_medical_cost(record)
                events.append({
                    'type': 'medical_expense',
                    'amount': medical_cost,
                    'diseases': [d.value for d in record.current_diseases]
                })
        
        # 清除已治愈的临时疾病
        record.current_diseases = [d for d in record.current_diseases 
                                   if d in record.chronic_diseases or 
                                   random.random() < 0.9]  # 10% 自愈概率
        
        return events
    
    def _check_disease_onset(self, record: HealthRecord, age: int):
        """检查疾病发生"""
        # 基础发病率
        base_rate = 0.02
        
        # 年龄增加风险
        age_factor = 1 + (age - 30) * 0.02 if age > 30 else 1
        
        # 健康状况差增加风险
        health_factor = 1 + (100 - record.overall_health) * 0.01
        
        # 生活习惯影响
        lifestyle_factor = 1.0
        if record.smoking:
            lifestyle_factor += 0.5
        if record.alcohol_consumption == "heavy":
            lifestyle_factor += 0.3
        if record.exercise_hours_weekly < 2:
            lifestyle_factor += 0.2
        
        total_risk = base_rate * age_factor * health_factor * lifestyle_factor
        
        if random.random() < total_risk:
            # 随机选择一种疾病
            possible_diseases = list(DiseaseType)
            possible_diseases.remove(DiseaseType.NONE)
            new_disease = random.choice(possible_diseases)
            
            if new_disease not in record.current_diseases:
                record.current_diseases.append(new_disease)
                
                # 慢性病加入慢性列表
                params = self.disease_params.get(new_disease, {})
                if params.get('duration_days', 0) > 365:
                    if new_disease not in record.chronic_diseases:
                        record.chronic_diseases.append(new_disease)
                
                record.overall_health -= params.get('severity', 0.3) * 20
    
    def _manage_chronic_disease(self, record: HealthRecord, disease: DiseaseType):
        """管理慢性病"""
        params = self.disease_params.get(disease, {})
        
        # 定期医疗支出
        monthly_cost = params.get('cost', 100) / 12
        
        # 疾病进展
        if record.overall_health < 50:
            # 健康状况差，疾病恶化
            record.overall_health -= 0.1
        else:
            # 健康状况好，疾病稳定
            record.overall_health += 0.05
    
    def _check_infection(self, record: HealthRecord):
        """检查传染病感染"""
        if DiseaseType.COVID19 in record.current_diseases:
            return  # 已感染
        
        # 感染概率基于免疫系统和感染率
        infection_prob = self.infection_rate * (1 - record.immune_system / 100)
        
        if random.random() < infection_prob:
            record.current_diseases.append(DiseaseType.COVID19)
            record.overall_health -= 15
            record.immune_system -= 10
    
    def _calculate_medical_cost(self, record: HealthRecord) -> float:
        """计算医疗支出"""
        total_cost = 0
        
        for disease in record.current_diseases:
            params = self.disease_params.get(disease, {})
            monthly_cost = params.get('cost', 100) / 12
            
            # 急性病一次性费用
            if params.get('duration_days', 0) < 30:
                monthly_cost *= 3
            
            total_cost += monthly_cost
        
        # 保险报销
        if record.has_insurance:
            out_of_pocket = total_cost * (1 - record.insurance_coverage)
        else:
            out_of_pocket = total_cost
        
        return out_of_pocket
    
    def get_treatment(self, agent_id: int, disease: DiseaseType) -> TreatmentType:
        """获取治疗方案"""
        params = self.disease_params.get(disease, {})
        severity = params.get('severity', 0.5)
        
        if severity < 0.3:
            return TreatmentType.SELF_CARE
        elif severity < 0.5:
            return TreatmentType.MEDICATION
        elif severity < 0.7:
            return TreatmentType.OUTPATIENT
        elif severity < 0.8:
            return TreatmentType.HOSPITALIZATION
        else:
            return TreatmentType.SURGERY
    
    def start_epidemic(self, disease: DiseaseType = DiseaseType.COVID19, 
                      infection_rate: float = 0.1):
        """开始流行病"""
        self.epidemic_active = True
        self.infection_rate = infection_rate
    
    def end_epidemic(self):
        """结束流行病"""
        self.epidemic_active = False
        self.infection_rate = 0.0
    
    def get_health_statistics(self) -> Dict:
        """获取健康统计"""
        if not self.health_records:
            return {}
        
        records = list(self.health_records.values())
        
        # 疾病分布
        disease_counts = {}
        for record in records:
            for disease in record.current_diseases + record.chronic_diseases:
                disease_counts[disease.value] = disease_counts.get(disease.value, 0) + 1
        
        # 平均指标
        avg_health = sum(r.overall_health for r in records) / len(records)
        avg_mental = sum(r.mental_health for r in records) / len(records)
        avg_bmi = sum(r.bmi for r in records) / len(records)
        avg_life_exp = sum(r.life_expectancy_base for r in records) / len(records)
        
        return {
            'total_population': len(records),
            'avg_overall_health': avg_health,
            'avg_mental_health': avg_mental,
            'avg_bmi': avg_bmi,
            'avg_life_expectancy': avg_life_exp,
            'disease_distribution': disease_counts,
            'chronic_disease_rate': sum(len(r.chronic_diseases) for r in records) / len(records),
            'epidemic_active': self.epidemic_active,
            'infection_rate': self.infection_rate,
        }


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("医疗健康系统测试")
    print("=" * 60)
    
    system = HealthcareSystem()
    
    # 创建测试 Agent
    test_agents = [
        {'id': 1, 'age': 25, 'gender': 'male'},
        {'id': 2, 'age': 35, 'gender': 'female'},
        {'id': 3, 'age': 50, 'gender': 'male'},
        {'id': 4, 'age': 65, 'gender': 'female'},
    ]
    
    print(f"\n创建健康记录:")
    for agent in test_agents:
        record = system.create_health_record(agent['id'], agent['age'], agent['gender'])
        print(f"  Agent {agent['id']} ({agent['age']}岁, {agent['gender']}):")
        print(f"    健康：{record.overall_health:.1f}/100, 心理：{record.mental_health:.1f}/100")
        print(f"    BMI: {record.bmi:.1f}, 预期寿命：{record.life_expectancy_base:.1f}岁")
        if record.chronic_diseases:
            print(f"    慢性病：{[d.value for d in record.chronic_diseases]}")
    
    # 模拟 12 个月
    print(f"\n模拟 12 个月...")
    total_medical_cost = 0
    for month in range(12):
        for agent in test_agents:
            events = system.update_monthly(agent['id'], agent['age'])
            for event in events:
                if event['type'] == 'medical_expense':
                    total_medical_cost += event['amount']
        
        if (month + 1) % 3 == 0:
            print(f"  第{month+1}月累计医疗支出：${total_medical_cost:,.0f}")
    
    # 统计
    stats = system.get_health_statistics()
    print(f"\n健康统计:")
    print(f"  平均健康：{stats['avg_overall_health']:.1f}/100")
    print(f"  平均心理：{stats['avg_mental_health']:.1f}/100")
    print(f"  平均 BMI: {stats['avg_bmi']:.1f}")
    print(f"  平均预期寿命：{stats['avg_life_expectancy']:.1f}岁")
    print(f"  人均慢性病：{stats['chronic_disease_rate']:.2f}种")
    
    print("\n✅ 医疗健康系统测试完成!")
