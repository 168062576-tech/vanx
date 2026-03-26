"""
住房系统 - Housing System

模拟真实的房地产市场和居住情况：
- 买房/租房/房贷
- 房价波动/地段/房产类型
- 房产税/物业/维护成本
- 搬家/换房/投资房产
-  homelessness（无家可归）

作者：御龙军
日期：2026-03-17
版本：v1.0
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class HousingType(Enum):
    """房产类型"""
    APARTMENT = "apartment"  # 公寓
    CONDO = "condo"  # 公寓（产权）
    HOUSE_SINGLE = "house_single"  # 独栋别墅
    HOUSE_TOWN = "house_town"  # 联排别墅
    ROOM = "room"  # 房间（合租）
    DORM = "dorm"  # 宿舍
    MOBILE_HOME = "mobile_home"  # 活动房屋


class HousingStatus(Enum):
    """居住状态"""
    RENTING = "renting"  # 租房
    OWNING = "owning"  # 自有（无贷款）
    MORTGAGE = "mortgage"  # 有房贷
    LIVING_WITH_FAMILY = "living_with_family"  # 与家人同住
    HOMELESS = "homeless"  # 无家可归
    DORM = "dorm"  # 宿舍


class Neighborhood(Enum):
    """地段类型"""
    DOWNTOWN = "downtown"  # 市中心
    SUBURB = "suburb"  # 郊区
    URBAN = "urban"  # 城区
    RURAL = "rural"  # 农村
    BEACHFRONT = "beachfront"  # 海滨
    MOUNTAIN = "mountain"  # 山区


@dataclass
class Property:
    """房产"""
    property_id: int
    address: str
    city: str
    neighborhood: Neighborhood
    housing_type: HousingType
    bedrooms: int
    bathrooms: int
    area_sqft: float  # 面积（平方英尺）
    
    # 价值
    market_value: float = 0.0  # 市场价值
    purchase_price: float = 0.0  # 购买价格
    property_tax_annual: float = 0.0  # 年度房产税
    hoa_fee_monthly: float = 0.0  # 物业费（如有）
    
    # 状态
    owner_id: Optional[int] = None  # 所有者 ID
    is_for_sale: bool = False
    is_for_rent: bool = False
    rent_price_monthly: float = 0.0  # 月租金
    tenant_id: Optional[int] = None  # 租客 ID
    
    # 属性
    year_built: int = 2000
    condition: float = 1.0  # 房屋状况 0-1
    amenities: List[str] = field(default_factory=list)  # 设施
    
    def __post_init__(self):
        if self.market_value == 0:
            self._calculate_value()
    
    def _calculate_value(self):
        """计算房产价值"""
        # 基础价格（按面积和类型）
        base_price_per_sqft = {
            HousingType.APARTMENT: 300,
            HousingType.CONDO: 350,
            HousingType.HOUSE_SINGLE: 400,
            HousingType.HOUSE_TOWN: 320,
            HousingType.ROOM: 200,
            HousingType.DORM: 100,
            HousingType.MOBILE_HOME: 80,
        }
        
        # 地段系数
        neighborhood_mult = {
            Neighborhood.DOWNTOWN: 2.0,
            Neighborhood.SUBURB: 1.2,
            Neighborhood.URBAN: 1.5,
            Neighborhood.RURAL: 0.6,
            Neighborhood.BEACHFRONT: 2.5,
            Neighborhood.MOUNTAIN: 1.3,
        }
        
        base = base_price_per_sqft.get(self.housing_type, 300) * self.area_sqft
        self.market_value = base * neighborhood_mult.get(self.neighborhood, 1.0) * self.condition
        
        # 卧室/卫生间加成
        self.market_value *= (1 + 0.1 * self.bedrooms + 0.05 * self.bathrooms)
        
        # 房龄折旧
        age = datetime.now().year - self.year_built
        self.market_value *= max(0.5, 1 - age * 0.005)  # 每年折旧 0.5%，最低 50%
        
        self.purchase_price = self.market_value
        self.property_tax_annual = self.market_value * 0.012  # 1.2% 年房产税
        self.rent_price_monthly = self.market_value * 0.005  # 0.5% 月租金


@dataclass
class Mortgage:
    """房贷"""
    property_id: int
    owner_id: int
    principal: float  # 本金
    interest_rate: float  # 年利率
    term_years: int  # 贷款年限
    start_date: datetime
    monthly_payment: float = 0.0
    remaining_balance: float = 0.0
    payments_made: int = 0
    
    def __post_init__(self):
        if self.monthly_payment == 0:
            self._calculate_payment()
        if self.remaining_balance == 0:
            self.remaining_balance = self.principal
    
    def _calculate_payment(self):
        """计算月供"""
        r = self.interest_rate / 12
        n = self.term_years * 12
        if r == 0:
            self.monthly_payment = self.principal / n
        else:
            self.monthly_payment = self.principal * r * (1 + r)**n / ((1 + r)**n - 1)
    
    def make_payment(self, amount: float = None) -> bool:
        """还款"""
        if amount is None:
            amount = self.monthly_payment
        
        if amount >= self.remaining_balance:
            self.remaining_balance = 0
            return True  # 还清
        
        # 先还利息
        interest = self.remaining_balance * self.interest_rate / 12
        principal_payment = amount - interest
        
        self.remaining_balance -= principal_payment
        self.payments_made += 1
        
        return False


@dataclass
class Residence:
    """居住记录"""
    agent_id: int
    property_id: int
    status: HousingStatus
    start_date: datetime
    rent_monthly: float = 0.0  # 月租金（如租房）
    mortgage: Optional[Mortgage] = None
    move_in_date: datetime = field(default_factory=datetime.now)


class HousingSystem:
    """住房系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.properties: Dict[int, Property] = {}
        self.residences: Dict[int, Residence] = {}  # agent_id -> Residence
        self.mortgages: Dict[int, Mortgage] = {}  # property_id -> Mortgage
        self.property_id_counter = 1
        
        # 市场参数
        self.housing_price_index = 100.0  # 房价指数
        self.rental_vacancy_rate = 0.07  # 空置率 7%
        self.homeownership_rate = 0.65  # 自有率 65%
        
        # 房贷参数
        self.default_down_payment = 0.2  # 默认首付 20%
        self.default_mortgage_rate = 0.04  # 默认利率 4%
        self.default_mortgage_term = 30  # 默认 30 年
    
    def create_property(self, housing_type: HousingType, neighborhood: Neighborhood,
                       bedrooms: int = 2, area_sqft: float = 1000,
                       city: str = "Metro City") -> Property:
        """创建房产"""
        property_obj = Property(
            property_id=self.property_id_counter,
            address=f"{random.randint(1, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Park'])} St",
            city=city,
            neighborhood=neighborhood,
            housing_type=housing_type,
            bedrooms=bedrooms,
            bathrooms=max(1, bedrooms - 1),
            area_sqft=area_sqft,
            year_built=random.randint(1950, 2024),
        )
        
        self.properties[property_obj.property_id] = property_obj
        self.property_id_counter += 1
        
        return property_obj
    
    def buy_property(self, agent_id: int, property_id: int, 
                    down_payment: float = None) -> Optional[Mortgage]:
        """购买房产"""
        if property_id not in self.properties:
            return None
        
        property_obj = self.properties[property_id]
        
        # 检查是否可购买
        if property_obj.is_for_rent and property_obj.tenant_id:
            return None  # 有租客
        
        # 计算首付
        if down_payment is None:
            down_payment = property_obj.market_value * self.default_down_payment
        
        if down_payment > property_obj.market_value:
            down_payment = property_obj.market_value
        
        # 贷款金额
        loan_amount = property_obj.market_value - down_payment
        
        # 创建房贷（如果需要贷款）
        mortgage = None
        if loan_amount > 0:
            mortgage = Mortgage(
                property_id=property_id,
                owner_id=agent_id,
                principal=loan_amount,
                interest_rate=self.default_mortgage_rate + random.gauss(0, 0.005),
                term_years=self.default_mortgage_term,
                start_date=datetime.now()
            )
            self.mortgages[property_id] = mortgage
        
        # 更新房产
        property_obj.owner_id = agent_id
        property_obj.is_for_sale = False
        property_obj.is_for_rent = False
        property_obj.tenant_id = None
        
        # 创建居住记录
        self._update_residence(agent_id, property_id, 
                              HousingStatus.MORTGAGE if mortgage else HousingStatus.OWNING,
                              mortgage)
        
        return mortgage
    
    def rent_property(self, agent_id: int, property_id: int) -> bool:
        """租房"""
        if property_id not in self.properties:
            return False
        
        property_obj = self.properties[property_id]
        
        # 检查是否可租
        if property_obj.owner_id and not property_obj.is_for_rent:
            return False  # 非出租房源
        
        if property_obj.tenant_id:
            return False  # 已有租客
        
        # 更新房产
        property_obj.tenant_id = agent_id
        property_obj.is_for_rent = False
        
        # 创建居住记录
        self._update_residence(agent_id, property_id, 
                              HousingStatus.RENTING,
                              None,
                              property_obj.rent_price_monthly)
        
        return True
    
    def move_out(self, agent_id: int, reason: str = "move"):
        """搬出"""
        if agent_id not in self.residences:
            return
        
        residence = self.residences[agent_id]
        property_obj = self.properties.get(residence.property_id)
        
        if property_obj:
            # 清空租客
            if property_obj.tenant_id == agent_id:
                property_obj.tenant_id = None
                property_obj.is_for_rent = True
            
            # 如卖房，标记为出售
            if property_obj.owner_id == agent_id and reason == "sell":
                property_obj.is_for_sale = True
        
        # 删除居住记录
        del self.residences[agent_id]
    
    def _update_residence(self, agent_id: int, property_id: int, 
                         status: HousingStatus, mortgage: Mortgage = None,
                         rent: float = 0.0):
        """更新居住记录"""
        # 先处理旧居住
        if agent_id in self.residences:
            self.move_out(agent_id)
        
        # 创建新居住记录
        residence = Residence(
            agent_id=agent_id,
            property_id=property_id,
            status=status,
            start_date=datetime.now(),
            rent_monthly=rent,
            mortgage=mortgage
        )
        
        self.residences[agent_id] = residence
    
    def update_monthly(self, agent_id: int, months_passed: int = 1):
        """更新月度住房"""
        if agent_id not in self.residences:
            return
        
        residence = self.residences[agent_id]
        property_obj = self.properties.get(residence.property_id)
        
        if not property_obj:
            return
        
        for _ in range(months_passed):
            # 1. 房贷还款
            if residence.mortgage:
                paid_off = residence.mortgage.make_payment()
                if paid_off:
                    residence.status = HousingStatus.OWNING
                    residence.mortgage = None
            
            # 2. 房租支付（从 Agent 财务扣除，这里只记录）
            if residence.status == HousingStatus.RENTING:
                # 租金可能随市场调整
                market_rent = property_obj.rent_price_monthly * self.housing_price_index / 100
                residence.rent_monthly = market_rent * 0.95  # 现有租客略低于市场价
            
            # 3. 房产税（房主支付）
            if residence.status in [HousingStatus.OWNING, HousingStatus.MORTGAGE]:
                # 房产税从 Agent 财务扣除，这里只记录
                pass
            
            # 4. 房屋维护
            property_obj.condition *= 0.9999  # 轻微折旧
            if random.random() < 0.01:  # 1% 概率需要维修
                property_obj.condition = min(1.0, property_obj.condition + 0.05)
    
    def update_market(self, months_passed: int = 1):
        """更新房地产市场"""
        for _ in range(months_passed):
            # 房价指数波动
            change = random.gauss(0.002, 0.01)  # 月均 0.2%，标准差 1%
            self.housing_price_index *= (1 + change)
            self.housing_price_index = max(50, min(200, self.housing_price_index))
            
            # 更新所有房产价值
            for prop in self.properties.values():
                prop.market_value = prop.purchase_price * self.housing_price_index / 100
                prop.rent_price_monthly = prop.market_value * 0.005
                prop.property_tax_annual = prop.market_value * 0.012
            
            # 空置率调整
            vacant = sum(1 for p in self.properties.values() if p.is_for_rent or p.is_for_sale)
            total = len(self.properties)
            if total > 0:
                self.rental_vacancy_rate = vacant / total
    
    def find_affordable_housing(self, agent_id: int, income_monthly: float, 
                                savings: float) -> List[Property]:
        """查找可负担的住房"""
        affordable = []
        
        # 租房：租金不超过收入 30%
        max_rent = income_monthly * 0.3
        
        # 买房：首付 + 月供不超过承受范围
        max_purchase_price = savings * 5  # 简化：最多买 5 倍储蓄的房子
        max_monthly_payment = income_monthly * 0.28  # 28% 收入用于住房
        
        for prop in self.properties.values():
            if prop.is_for_rent and prop.rent_price_monthly <= max_rent:
                affordable.append(prop)
            elif prop.is_for_sale and prop.market_value <= max_purchase_price:
                # 检查月供
                down_payment = prop.market_value * 0.2
                if savings >= down_payment:
                    loan = prop.market_value - down_payment
                    monthly_payment = loan * 0.005  # 简化月供计算
                    if monthly_payment <= max_monthly_payment:
                        affordable.append(prop)
        
        return affordable
    
    def get_housing_statistics(self) -> Dict:
        """获取住房统计"""
        if not self.properties:
            return {}
        
        # 按状态分类
        status_counts = {}
        for residence in self.residences.values():
            status = residence.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 房价统计
        values = [p.market_value for p in self.properties.values()]
        
        return {
            'total_properties': len(self.properties),
            'total_residents': len(self.residences),
            'housing_price_index': self.housing_price_index,
            'avg_property_value': sum(values) / len(values) if values else 0,
            'min_property_value': min(values) if values else 0,
            'max_property_value': max(values) if values else 0,
            'rental_vacancy_rate': self.rental_vacancy_rate,
            'homeownership_rate': sum(1 for r in self.residences.values() 
                                     if r.status in [HousingStatus.OWNING, HousingStatus.MORTGAGE]) / 
                                 len(self.residences) if self.residences else 0,
            'status_distribution': status_counts,
        }


# ============ 测试 ============
if __name__ == "__main__":
    print("=" * 60)
    print("住房系统测试")
    print("=" * 60)
    
    system = HousingSystem()
    
    # 创建测试房产
    properties = [
        system.create_property(HousingType.APARTMENT, Neighborhood.DOWNTOWN, 1, 600),
        system.create_property(HousingType.HOUSE_SINGLE, Neighborhood.SUBURB, 3, 2000),
        system.create_property(HousingType.CONDO, Neighborhood.URBAN, 2, 1200),
        system.create_property(HousingType.HOUSE_TOWN, Neighborhood.SUBURB, 2, 1500),
    ]
    
    # 标记部分出售/出租
    properties[0].is_for_rent = True
    properties[1].is_for_sale = True
    properties[2].is_for_rent = True
    properties[3].is_for_sale = True
    
    print(f"\n创建房产:")
    for prop in properties:
        print(f"  {prop.housing_type.value} @ {prop.neighborhood.value}: "
              f"${prop.market_value:,.0f}, 租金${prop.rent_price_monthly:,.0f}/月")
    
    # 模拟买房/租房
    print(f"\n住房交易:")
    
    # Agent 1 买房
    mortgage = system.buy_property(1, properties[1].property_id, down_payment=100000)
    if mortgage:
        print(f"  Agent 1 买房：${properties[1].market_value:,.0f}, "
              f"首付$100,000, 月供${mortgage.monthly_payment:,.0f}")
    
    # Agent 2 租房
    if system.rent_property(2, properties[0].property_id):
        print(f"  Agent 2 租房：${properties[0].rent_price_monthly:,.0f}/月")
    
    # 模拟 12 个月
    print(f"\n模拟 12 个月...")
    for month in range(12):
        system.update_market()
        system.update_monthly(1)
        system.update_monthly(2)
        
        if (month + 1) % 3 == 0:
            print(f"  第{month+1}月：房价指数={system.housing_price_index:.1f}")
    
    # 检查房贷余额
    if 1 in system.residences and system.residences[1].mortgage:
        remaining = system.residences[1].mortgage.remaining_balance
        print(f"\nAgent 1 房贷余额：${remaining:,.0f} (已还{system.residences[1].mortgage.payments_made}期)")
    
    # 统计
    stats = system.get_housing_statistics()
    print(f"\n住房统计:")
    print(f"  房产总数：{stats['total_properties']}")
    print(f"  平均房价：${stats['avg_property_value']:,.0f}")
    print(f"  自有率：{stats['homeownership_rate']*100:.1f}%")
    print(f"  空置率：{stats['rental_vacancy_rate']*100:.1f}%")
    
    print("\n✅ 住房系统测试完成!")
