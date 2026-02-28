"""
Data models for asset-lens.
数据模型定义，包括投资产品、交易记录、投资组合等
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List


class Currency(str, Enum):
    """货币类型"""

    CNY = "CNY"
    USD = "USD"
    HKD = "HKD"
    EUR = "EUR"
    JPY = "JPY"


class InvestmentType(str, Enum):
    """投资类型"""

    MONETARY = "货币"  # 货币基金
    INDEX_FUND = "指数基金"  # 指数基金
    BOND_FUND = "债券基金"  # 债券基金
    MIXED_FUND = "混合基金"  # 混合基金
    STOCK = "股票"  # 股票
    US_STOCK = "美股"  # 美股
    HK_STOCK = "港股"  # 港股
    QDII = "QDII"  # QDII 基金
    WEALTH = "理财"  # 理财产品
    FIXED_DEPOSIT = "定期存款"  # 定期存款
    BOND = "债券"  # 债券
    REITS = "REITs"  # 不动产投资信托
    GOLD = "黄金"  # 黄金
    FUND = "基金"  # 其他基金
    OTHER = "其他"  # 其他


class RiskLevel(str, Enum):
    """风险等级"""

    LOW = "低"
    MEDIUM_LOW = "中低"
    MEDIUM = "中"
    MEDIUM_HIGH = "中高"
    HIGH = "高"


class Platform(str, Enum):
    """投资平台"""

    WECHAT = "微信"
    ALIPAY = "支付宝"
    BANK = "银行"
    FUND_COMPANY = "基金公司"
    SECURITIES = "证券"
    OTHER = "其他"


@dataclass
class Transaction:
    """交易记录"""

    transaction_date: date  # 交易日期
    action: str  # 操作类型：buy/sell
    amount: Decimal  # 金额（本地货币）
    currency: Currency = Currency.CNY  # 货币类型
    exchange_rate: Decimal | None = None  # 汇率（如果是外币）

    def to_cny(self, usd_rate: Decimal, hkd_rate: Decimal) -> Decimal:
        """转换为人民币"""
        if self.currency == Currency.CNY:
            return self.amount
        elif self.currency == Currency.USD:
            rate = self.exchange_rate or usd_rate
            return self.amount * rate
        elif self.currency == Currency.HKD:
            rate = self.exchange_rate or hkd_rate
            return self.amount * rate
        else:
            # 其他货币暂时使用原始金额
            return self.amount


@dataclass
class InvestmentProduct:
    """投资产品"""

    investment_type: InvestmentType  # 投资类型
    name: str  # 产品名称
    risk_level: RiskLevel  # 风险等级
    wechat_amount: Decimal | None = None  # 微信平台金额
    zhongjin_amount: Decimal | None = None  # 中金平台金额
    alipay_amount: Decimal | None = None  # 支付宝平台金额
    futu_amount: Decimal | None = None  # 富途平台金额
    zhaoshang_amount: Decimal | None = None  # 招商平台金额
    gangzhao_amount: Decimal | None = None  # 港招平台金额
    jiaotong_amount: Decimal | None = None  # 交通平台金额
    pufa_amount: Decimal | None = None  # 浦发平台金额
    jianshe_amount: Decimal | None = None  # 建设平台金额
    zhongxin_amount: Decimal | None = None  # 中信平台金额
    minsheng_amount: Decimal | None = None  # 民生平台金额
    gongshang_amount: Decimal | None = None  # 工商平台金额
    zhongyin_amount: Decimal | None = None  # 中银平台金额
    maturity_date: date | None = None  # 到期时间
    is_rolling: bool = False  # 是否滚动
    start_date: date | None = None  # 开始日期
    initial_amount: Decimal | None = None  # 初始金额
    secondary_buy: Decimal | None = None  # 二次买入
    secondary_amount: Decimal | None = None  # 二次金额
    profit_amount: Decimal | None = None  # 收益金额
    investment_days: int | None = None  # 投资天数
    return_rate: Decimal | None = None  # 收益率
    annual_return: Decimal | None = None  # 年化收益率
    compound_return: Decimal | None = None  # 复利年化
    interest_payment: Decimal | None = None  # 利息发放
    transaction_records: str | None = None  # 交易记录字符串
    default_order: int | None = None  # 默认顺序
    usd_rate: Decimal | None = None  # 美元汇率
    hkd_rate: Decimal | None = None  # 港元汇率

    # 计算字段
    current_amount: Decimal | None = None  # 当前金额
    annualized_return_irr: Decimal | None = None  # IRR 年化收益率
    transactions: List[Transaction] = field(default_factory=list)  # 解析后的交易记录

    @property
    def total_amount(self) -> Decimal:
        """总金额"""
        total = Decimal("0")
        if self.wechat_amount:
            total += self.wechat_amount
        if self.alipay_amount:
            total += self.alipay_amount
        return total or self.current_amount or Decimal("0")

    @property
    def platform(self) -> Platform:
        """主要平台"""
        if self.wechat_amount and self.alipay_amount:
            return Platform.OTHER
        elif self.wechat_amount:
            return Platform.WECHAT
        elif self.alipay_amount:
            return Platform.ALIPAY
        else:
            return Platform.OTHER

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "投资类型": self.investment_type.value,
            "名称": self.name,
            "风险等级": self.risk_level.value,
            "微信金额": str(self.wechat_amount) if self.wechat_amount else None,
            "支付宝金额": str(self.alipay_amount) if self.alipay_amount else None,
            "到期时间": self.maturity_date.isoformat() if self.maturity_date else None,
            "是否滚动": self.is_rolling,
            "开始日期": self.start_date.isoformat() if self.start_date else None,
            "初始金额": str(self.initial_amount) if self.initial_amount else None,
            "当前金额": str(self.current_amount) if self.current_amount else None,
            "投资天数": self.investment_days,
            "收益率": f"{self.return_rate:.2f}%" if self.return_rate else None,
            "年化收益率": f"{self.annual_return:.2f}%" if self.annual_return else None,
            "IRR年化": f"{self.annualized_return_irr:.2f}%"
            if self.annualized_return_irr
            else None,
            "平台": self.platform.value,
            "交易记录": self.transaction_records,
        }


@dataclass
class AssetSummary:
    """资产汇总记录"""
    
    summary_date: date  # 汇总日期
    wechat_amount: Decimal = Decimal("0")  # 微信金额
    zhongjin_amount: Decimal = Decimal("0")  # 中金金额
    alipay_amount: Decimal = Decimal("0")  # 支付宝金额
    futu_amount: Decimal = Decimal("0")  # 富途金额
    zhaoshang_amount: Decimal = Decimal("0")  # 招商金额
    gangzhao_amount: Decimal = Decimal("0")  # 港招金额
    jiaotong_amount: Decimal = Decimal("0")  # 交通金额
    pufa_amount: Decimal = Decimal("0")  # 浦发金额
    jianshe_amount: Decimal = Decimal("0")  # 建设金额
    zhongxin_amount: Decimal = Decimal("0")  # 中信金额
    minsheng_amount: Decimal = Decimal("0")  # 民生金额
    gongshang_amount: Decimal = Decimal("0")  # 工商金额
    zhongyin_amount: Decimal = Decimal("0")  # 中银金额
    credit_card_amount: Decimal = Decimal("0")  # 信用卡金额
    jingdong_white_amount: Decimal = Decimal("0")  # 京东白条金额
    douyin_monthly_amount: Decimal = Decimal("0")  # 抖音月付金额
    duoduo_later_amount: Decimal = Decimal("0")  # 多多后付金额
    total_amount: Decimal = Decimal("0")  # 总金额
    usd_rate: Decimal = Decimal("7.1242")  # 美元汇率
    hkd_rate: Decimal = Decimal("0.9157")  # 港元汇率
    gold_amount: Decimal = Decimal("0")  # 黄金金额
    exchange_usd_amount: Decimal = Decimal("0")  # 兑换美元金额
    exchange_hkd_amount: Decimal = Decimal("0")  # 兑换港元金额
    exchange_gold_amount: Decimal = Decimal("0")  # 兑换黄金金额
    shanghai_index: Decimal = Decimal("0")  # 上证指数
    csi300_index: Decimal = Decimal("0")  # 沪深300
    csi500_index: Decimal = Decimal("0")  # 中证500
    nasdaq100_index: Decimal = Decimal("0")  # 纳指100
    sp500_index: Decimal = Decimal("0")  # 标普500
    vix_index: Decimal = Decimal("0")  # 恐慌VXX
    us_treasury_rate: Decimal = Decimal("0")  # 美联基利率
    property_value: Decimal = Decimal("0")  # 房产总价
    return_rate: Decimal = Decimal("0")  # 收益率
    
    @property
    def total_platform_amount(self) -> Decimal:
        """总平台金额"""
        return (
            self.wechat_amount + self.zhongjin_amount + self.alipay_amount +
            self.futu_amount + self.zhaoshang_amount + self.gangzhao_amount +
            self.jiaotong_amount + self.pufa_amount + self.jianshe_amount +
            self.zhongxin_amount + self.minsheng_amount + self.gongshang_amount +
            self.zhongyin_amount
        )
    
    @property
    def total_credit_amount(self) -> Decimal:
        """总信用金额"""
        return (
            self.credit_card_amount + self.jingdong_white_amount +
            self.douyin_monthly_amount + self.duoduo_later_amount
        )
    
    @property
    def total_investment_value(self) -> Decimal:
        """总投资价值"""
        return self.total_platform_amount + self.total_credit_amount + self.gold_amount
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "汇总日期": self.summary_date.isoformat(),
            "微信金额": str(self.wechat_amount),
            "中金金额": str(self.zhongjin_amount),
            "支付宝金额": str(self.alipay_amount),
            "富途金额": str(self.futu_amount),
            "招商金额": str(self.zhaoshang_amount),
            "港招金额": str(self.gangzhao_amount),
            "交通金额": str(self.jiaotong_amount),
            "浦发金额": str(self.pufa_amount),
            "建设金额": str(self.jianshe_amount),
            "中信金额": str(self.zhongxin_amount),
            "民生金额": str(self.minsheng_amount),
            "工商金额": str(self.gongshang_amount),
            "中银金额": str(self.zhongyin_amount),
            "信用卡金额": str(self.credit_card_amount),
            "京东白条金额": str(self.jingdong_white_amount),
            "抖音月付金额": str(self.douyin_monthly_amount),
            "多多后付金额": str(self.duoduo_later_amount),
            "总金额": str(self.total_amount),
            "美元汇率": str(self.usd_rate),
            "港元汇率": str(self.hkd_rate),
            "黄金金额": str(self.gold_amount),
            "兑换美元金额": str(self.exchange_usd_amount),
            "兑换港元金额": str(self.exchange_hkd_amount),
            "兑换黄金金额": str(self.exchange_gold_amount),
            "上证指数": str(self.shanghai_index),
            "沪深300": str(self.csi300_index),
            "中证500": str(self.csi500_index),
            "纳指100": str(self.nasdaq100_index),
            "标普500": str(self.sp500_index),
            "恐慌VXX": str(self.vix_index),
            "美联基利率": str(self.us_treasury_rate),
            "房产总价": str(self.property_value),
            "收益率": f"{self.return_rate:.2f}%" if self.return_rate else None,
        }


@dataclass
class ExchangeRateHistory:
    """汇率历史记录"""
    
    rate_date: date  # 汇率日期
    usd_rate: Decimal = Decimal("7.1242")  # 美元汇率
    hkd_rate: Decimal = Decimal("0.9157")  # 港元汇率
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "汇率日期": self.rate_date.isoformat(),
            "美元汇率": str(self.usd_rate),
            "港元汇率": str(self.hkd_rate),
        }


@dataclass
class SellRecord:
    """卖出记录"""
    
    sell_date: date  # 卖出日期
    name: str  # 产品名称
    risk_level: RiskLevel  # 风险等级
    maturity_date: date | None = None  # 到期时间
    is_rolling: bool = False  # 是否滚动
    start_date: date | None = None  # 开始日期
    initial_amount: Decimal | None = None  # 初始金额
    profit_amount: Decimal | None = None  # 收益金额
    return_rate: Decimal | None = None  # 收益率
    end_date: date | None = None  # 结束日期
    to_account_date: date | None = None  # 到账日期
    end_to_account_interval: int | None = None  # 结束到账间隔
    investment_days: int | None = None  # 投资天数
    annual_return: Decimal | None = None  # 年化收益
    compound_return: Decimal | None = None  # 复利年化
    interest_payment: Decimal | None = None  # 利息发放
    transaction_records: str | None = None  # 交易记录
    default_order: int | None = None  # 默认顺序
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "卖出日期": self.sell_date.isoformat(),
            "名称": self.name,
            "风险等级": self.risk_level.value,
            "到期时间": self.maturity_date.isoformat() if self.maturity_date else None,
            "是否滚动": self.is_rolling,
            "开始日期": self.start_date.isoformat() if self.start_date else None,
            "初始金额": str(self.initial_amount) if self.initial_amount else None,
            "收益金额": str(self.profit_amount) if self.profit_amount else None,
            "收益率": f"{self.return_rate:.2f}%" if self.return_rate else None,
            "结束日期": self.end_date.isoformat() if self.end_date else None,
            "到账日期": self.to_account_date.isoformat() if self.to_account_date else None,
            "结束到账间隔": self.end_to_account_interval,
            "投资天数": self.investment_days,
            "年化收益": f"{self.annual_return:.2f}%" if self.annual_return else None,
            "复利年化": f"{self.compound_return:.2f}%" if self.compound_return else None,
            "利息发放": str(self.interest_payment) if self.interest_payment else None,
            "交易记录": self.transaction_records,
            "默认顺序": self.default_order,
        }


@dataclass
class Portfolio:
    """投资组合"""
    
    products: List[InvestmentProduct] = field(default_factory=list)
    usd_rate: Decimal = Decimal("7.1242")  # 美元汇率
    hkd_rate: Decimal = Decimal("0.9157")  # 港元汇率
    asset_summaries: List[AssetSummary] = field(default_factory=list)  # 资产汇总记录
    exchange_rate_history: List[ExchangeRateHistory] = field(default_factory=list)  # 汇率历史
    sell_records: List[SellRecord] = field(default_factory=list)  # 卖出记录

    def add_product(self, product: InvestmentProduct) -> None:
        """添加投资产品"""
        self.products.append(product)

    def get_by_type(self, investment_type: InvestmentType) -> List[InvestmentProduct]:
        """按类型获取投资产品"""
        return [p for p in self.products if p.investment_type == investment_type]

    def get_by_risk(self, risk_level: RiskLevel) -> List[InvestmentProduct]:
        """按风险等级获取投资产品"""
        return [p for p in self.products if p.risk_level == risk_level]

    @property
    def total_value(self) -> Decimal:
        """总资产"""
        total = Decimal("0")
        for product in self.products:
            if product.current_amount:
                total += product.current_amount
        return total

    @property
    def total_initial(self) -> Decimal:
        """总初始投资"""
        total = Decimal("0")
        for product in self.products:
            if product.initial_amount:
                total += product.initial_amount
        return total

    @property
    def total_profit(self) -> Decimal:
        """总收益"""
        return self.total_value - self.total_initial

    @property
    def overall_return_rate(self) -> Decimal | None:
        """整体收益率"""
        if self.total_initial == Decimal("0"):
            return None
        return (self.total_profit / self.total_initial) * Decimal("100")

    def get_type_distribution(self) -> Dict[str, Any]:
        """获取类型分布"""
        type_stats: Dict[str, Dict[str, Any]] = {}
        for product in self.products:
            type_name = product.investment_type.value
            if type_name not in type_stats:
                type_stats[type_name] = {
                    "count": 0,
                    "total_value": Decimal("0"),
                    "products": [],
                }
            type_stats[type_name]["count"] += 1
            if product.current_amount:
                type_stats[type_name]["total_value"] += product.current_amount
            type_stats[type_name]["products"].append(product)

        # 计算占比
        for stats in type_stats.values():
            if self.total_value > Decimal("0"):
                stats["percentage"] = (
                    stats["total_value"] / self.total_value
                ) * Decimal("100")
            else:
                stats["percentage"] = Decimal("0")

        return type_stats

    def get_risk_distribution(self) -> Dict[str, Any]:
        """获取风险分布"""
        risk_stats: Dict[str, Dict[str, Any]] = {}
        for product in self.products:
            risk_name = product.risk_level.value
            if risk_name not in risk_stats:
                risk_stats[risk_name] = {
                    "count": 0,
                    "total_value": Decimal("0"),
                    "products": [],
                }
            risk_stats[risk_name]["count"] += 1
            if product.current_amount:
                risk_stats[risk_name]["total_value"] += product.current_amount
            risk_stats[risk_name]["products"].append(product)

        # 计算占比
        for stats in risk_stats.values():
            if self.total_value > Decimal("0"):
                stats["percentage"] = (
                    stats["total_value"] / self.total_value
                ) * Decimal("100")
            else:
                stats["percentage"] = Decimal("0")

        return risk_stats
