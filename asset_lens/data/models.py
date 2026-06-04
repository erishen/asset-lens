"""
Data models for asset-lens.
数据模型定义，包括投资产品、交易记录、投资组合等
"""

import contextlib
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


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
    CASH = "现金"  # 现金
    INDEX_FUND = "指数基金"  # 指数基金
    BOND_FUND = "债券基金"  # 债券基金
    MIXED_FUND = "混合基金"  # 混合基金
    STOCK = "股票"  # 股票
    US_STOCK = "美股"  # 美股
    HK_STOCK = "港股"  # 港股
    HK_CASH = "现金（港元）"  # 港元现金
    HK_DIVIDEND_FUND = "股息基金（港元）"  # 港元股息基金
    QDII = "QDII"  # QDII 基金
    WEALTH = "理财"  # 理财产品
    HIGH_END_WEALTH = "高端理财"  # 高端理财
    BROKER_WEALTH = "券商理财"  # 券商理财
    PUBLIC_FIXED_INCOME = "公募固收"  # 公募固收
    FIXED_DEPOSIT = "定期存款"  # 定期存款
    BOND = "债券"  # 债券
    SPECIAL_TREASURY_BOND = "特别国债"  # 特别国债
    REITS = "REITs"  # 不动产投资信托
    GOLD = "黄金"  # 黄金
    FUND = "基金"  # 其他基金
    DCA_FUND = "定投基金"  # 定投基金
    PENSION = "个人养老金"  # 个人养老金
    ETF = "ETF"  # ETF
    USD_FUND = "美元基金（美元）"  # 美元基金
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

    THIRD_PARTY = "第三方平台"
    BANK = "银行"
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
    platform_amounts: dict[str, Decimal] = field(default_factory=dict)  # 平台金额字典
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
    owner: str = "personal"  # 所有者: personal, family, shared

    # 计算字段
    current_amount: Decimal | None = None  # 当前金额
    annualized_return_irr: Decimal | None = None  # IRR 年化收益率
    transactions: list[Transaction] = field(default_factory=list)  # 解析后的交易记录

    def get_amount(self, platform_id: str) -> Decimal:
        """获取平台金额"""
        return self.platform_amounts.get(platform_id, Decimal("0"))

    def set_amount(self, platform_id: str, amount: Decimal) -> None:
        """设置平台金额"""
        self.platform_amounts[platform_id] = amount

    @property
    def total_amount(self) -> Decimal:
        """总金额"""
        total = sum(self.platform_amounts.values())
        return total or self.current_amount or Decimal("0")

    def get_converted_amount(self, usd_rate: Decimal, hkd_rate: Decimal) -> Decimal:
        """获取汇率转换后的当前金额（人民币），包含利息发放"""
        amount = self.current_amount or Decimal("0")
        interest = self.interest_payment or Decimal("0")

        # 检查是否需要汇率转换
        if self.investment_type in [
            InvestmentType.US_STOCK,
            InvestmentType.USD_FUND,
        ]:
            rate = self.usd_rate or usd_rate
            return amount * rate + interest * rate
        elif self.investment_type in [
            InvestmentType.HK_STOCK,
            InvestmentType.HK_CASH,
            InvestmentType.HK_DIVIDEND_FUND,
        ]:
            rate = self.hkd_rate or hkd_rate
            return amount * rate + interest * rate
        return amount + interest

    @property
    def platform(self) -> Platform:
        """主要平台"""
        if len(self.platform_amounts) > 1:
            return Platform.OTHER
        elif len(self.platform_amounts) == 1:
            return Platform.THIRD_PARTY
        else:
            return Platform.OTHER

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（与 ts-demo 格式一致）"""
        result = {
            "名称": self.name,
            "类型": self.investment_type.value,
            "所属平台": self._get_main_platform(),
            "投资天数": self.investment_days,
            "年化收益率(%)": f"{self.annual_return:.2f}" if self.annual_return else None,
            "实际收益率(%)": f"{self.return_rate:.2f}" if self.return_rate else None,
            "当前金额": str(self.current_amount) if self.current_amount else None,
            "净投入/初始金额": str(self.initial_amount) if self.initial_amount else None,
            "总买入": self._get_total_buy(),
            "总卖出": self._get_total_sell(),
            "开始日期": self.start_date.isoformat() if self.start_date else None,
            "风险情况": self.risk_level.value,
        }
        return result

    def _get_main_platform(self) -> str:
        """获取主平台名称"""
        from asset_lens.core.platform_loader import PlatformLoader

        amounts = {}
        for platform in PlatformLoader.get_all_platforms():
            amount = self.platform_amounts.get(platform.id, Decimal("0"))
            if amount and amount > Decimal("0"):
                amounts[platform.name] = amount

        if amounts:
            return str(max(amounts, key=lambda k: amounts[k] or Decimal("0")))
        return "未知"

    def _get_total_buy(self) -> str | None:
        """获取总买入金额"""
        if not self.transaction_records:
            return None
        try:
            total = Decimal("0")
            for line in self.transaction_records.strip().split("\n"):
                if "买入" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "买入" and i + 1 < len(parts):
                            amount_str = parts[i + 1].replace("¥", "").replace(",", "")
                            with contextlib.suppress(ValueError, InvalidOperation):
                                total += Decimal(amount_str)
            return str(total) if total > 0 else None
        except (ValueError, InvalidOperation, AttributeError):
            return None

    def _get_total_sell(self) -> str | None:
        """获取总卖出金额"""
        if not self.transaction_records:
            return None
        try:
            total = Decimal("0")
            for line in self.transaction_records.strip().split("\n"):
                if "卖出" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "卖出" and i + 1 < len(parts):
                            amount_str = parts[i + 1].replace("¥", "").replace(",", "")
                            with contextlib.suppress(ValueError, InvalidOperation):
                                total += Decimal(amount_str)
            return str(total) if total > 0 else None
        except (ValueError, InvalidOperation, AttributeError):
            return None


@dataclass
class AssetSummary:
    """资产汇总记录"""

    summary_date: date  # 汇总日期
    platform_amounts: dict[str, Decimal] = field(default_factory=dict)  # 平台金额字典
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

    def get_amount(self, platform_id: str) -> Decimal:
        """获取平台金额"""
        return self.platform_amounts.get(platform_id, Decimal("0"))

    def set_amount(self, platform_id: str, amount: Decimal) -> None:
        """设置平台金额"""
        self.platform_amounts[platform_id] = amount

    @property
    def total_platform_amount(self) -> Decimal:
        """总平台金额"""
        if not self.platform_amounts:
            return Decimal("0")
        return sum(self.platform_amounts.values(), Decimal("0"))

    @property
    def total_credit_amount(self) -> Decimal:
        """总信用金额"""
        return (
            self.credit_card_amount + self.jingdong_white_amount + self.douyin_monthly_amount + self.duoduo_later_amount
        )

    @property
    def total_investment_value(self) -> Decimal:
        """总投资价值"""
        return self.total_platform_amount + self.total_credit_amount + self.gold_amount

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {
            "汇总日期": self.summary_date.isoformat(),
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
        # 添加平台金额（使用平台名称作为字段名）
        from asset_lens.core.platform_loader import PlatformLoader

        for platform in PlatformLoader.get_all_platforms():
            amount = self.platform_amounts.get(platform.id, Decimal("0"))
            result[f"{platform.name}金额"] = str(amount)
        return result


@dataclass
class ExchangeRateHistory:
    """汇率历史记录"""

    rate_date: date  # 汇率日期
    usd_rate: Decimal | None = None  # 美元汇率
    hkd_rate: Decimal | None = None  # 港元汇率

    def to_dict(self) -> dict[str, Any]:
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

    def to_dict(self) -> dict[str, Any]:
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


from .portfolio import Portfolio  # noqa: F401


