"""固收+ 风险视图。

为什么单独做：asset-lens 的行情层（stock_klines）只覆盖 A 股，而个人固收类持仓占了市值的大头
（理财/债券/货币/特别国债）——这些**没有交易所行情源**。所以固收部分的风险不能靠
price/vol/beta 算，只能从 CSV 已有字段派生：

    1. 到期梯队（maturity ladder）—— 哪天有多少钱到期，含已逾期未回款
    2. 发行方/渠道集中度 —— 信用风险的核心，HHI 度量
    3. 收益合理性 —— 抓 CSV 手填的荒谬年化值和年化/复利背离
    4. 数据完整度 —— 86% 产品没有到期日，梯队不可信时必须自己说出来

本模块是纯函数：输入 product 列表 + as_of，输出 dataclass。不读文件、不打网络。
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from ..data.models import InvestmentType

# 固收+ 口径：不含股票/权益型基金/黄金/现金以外的权益敞口。
# 注意：这里刻意不含 FUND / ETF / QDII 等波动率资产——它们由 portfolio 视角管。
FIXED_INCOME_TYPES: frozenset[InvestmentType] = frozenset(
    {
        InvestmentType.WEALTH,  # 理财
        InvestmentType.HIGH_END_WEALTH,  # 高端理财
        InvestmentType.BROKER_WEALTH,  # 券商理财
        InvestmentType.BOND,  # 债券
        InvestmentType.SPECIAL_TREASURY_BOND,  # 特别国债
        InvestmentType.PUBLIC_FIXED_INCOME,  # 公募固收
        InvestmentType.BOND_FUND,  # 债券基金
        InvestmentType.FIXED_DEPOSIT,  # 定存
        InvestmentType.MONETARY,  # 货币
        InvestmentType.USD_FUND,  # 美元货币基金（现金等价物）
        InvestmentType.CASH,  # 现金
        InvestmentType.PENSION,  # 个人养老金
        InvestmentType.REITS,  # 产权类（准固收）
    }
)

# 发行方识别关键词 → 规范机构名。
#
# 关键：同一机构在 CSV 里有多种叫法（「招银理财」/「招商银行」），必须归一到同一个 canonical
# label，否则集中度会被低估、top3 家数被高估。规范名用「X行」而不是理财产品品牌名。
# 建信理财是建行的全资子公司但独立法人，单独归类，不并进建行。
ISSUER_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("农业银行", "农行"),
    ("建设银行", "建行"),
    ("工商银行", "工行"),
    ("邮储银行", "邮储"),
    ("交通银行", "交行"),
    ("招商银行", "招行"),
    ("浦发银行", "浦发"),
    ("民生银行", "民生"),
    ("中信银行", "中信"),
    ("光大银行", "光大"),
    ("平安银行", "平安"),
    ("兴业银行", "兴业"),
    ("广发银行", "广发"),
    ("华夏银行", "华夏"),
    # 品牌/简称 → 同一 canonical
    ("招银", "招行"),
    ("招商", "招行"),
    ("工银", "工行"),
    ("农行", "农行"),
    ("农银", "农行"),
    ("中银", "中行"),
    ("交银", "交行"),
    ("建信", "建信"),
    ("浦发", "浦发"),
    ("民生", "民生"),
    ("中信", "中信"),
    ("光大", "光大"),
    ("平安", "平安"),
    ("兴业", "兴业"),
    ("广发", "广发"),
    ("华夏", "华夏"),
)

PLATFORM_LABELS: dict[str, str] = {
    # 招行
    "cmb": "招行",
    "cmbchina": "招行",
    "cmbcz": "招行",
    "cmb_w": "招行",
    # 工行
    "icbc": "工行",
    "icbc_w": "工行",
    # 建行
    "ccb": "建行",
    "ccb_w": "建行",
    # 农行
    "abchina": "农行",
    "abc": "农行",
    # 中行
    "boc": "中行",
    "boc_w": "中行",
    # 交行
    "comm": "交行",
    "bocom": "交行",
    "bocom_w": "交行",
    # 其他银行
    "citic": "中信",
    "spdb": "浦发",
    "ceb": "光大",
    "psbc": "邮储",
    "cgb": "广发",
    "cmbcz2": "招行",
    # 非银行渠道
    "alipay": "支付宝",
    "wechat": "微信",
    "futu": "富途",
    "futuhk": "富途",
    "tonghuashun": "同花顺",
    "htsec": "华泰",
    "csc": "中信证券",
}

# 含权益敞口的产品名关键词。
#
# 关键：CSV 的『类型』列说不了这个。实测『个人养老金』账户里装的是 ETF联接
# （广发创业板ETF联接Y、易方达中证红利ETF联接发起式Y），『理财』里也有指数/混合类
# （鹏华弘康灵活配置混合C、中银理财ESG优享混合类日日开）。把这些当成纯固收，
# 沪深300 指数增强跌 17% 就会被报成「固收+ 收益异常」——把权益波动说成信用事件。
#
# 沿用 web/routes/wealth.py 的 EQUITY_FUND_KEYWORDS 口径，不另造一套。
# 注意「增利/增强收益」类的固收+ 产品不算在这里——它们以债券打底，权益敞口小。
EQUITY_EXPOSURE_KEYWORDS: tuple[str, ...] = (
    "指数",
    "增强",
    "混合",
    "股票",
    "沪深300",
    "ETF联接",
    "沪深300",
    "中证500",
    "中证1000",
    "创业板",
    "科创",
    "红利",
    "QDII",
    "FOF",
    "权益",
    "环球",
    "全球",
    "纳斯达克",
    "标普",
    "恒生",
    "双利",
    "多元",
    "配置",
)


def has_equity_exposure(name: str) -> bool:
    """产品名是否暗示含权益敞口。"""
    return any(kw in name for kw in EQUITY_EXPOSURE_KEYWORDS)


# 固定收益的合理年化上限。超过基本可以断定是 CSV 手填错（把累计收益当成了年化）。
# 固收+ 里含权益敞口的产品给到 8% 已经很激进，15% 只可能是数据错误。
PLAUSIBLE_ANNUALIZED_CEILING = Decimal("15")
# 年化 vs 复利年化的允许背离。正常差异来自费用/计息天数，>0.5pct 通常是填错了一列。
COMPOUND_DIVERGENCE_TOLERANCE = Decimal("0.5")

MaturityStatus = Literal["dated", "open_ended", "missing", "dirty"]

_OPEN_ENDED_SENTINELS = {"可赎", "随时", "T+0", "开放", "活期", "无固定期限"}


# ---------------------------------------------------------------------------
# 脏值解析
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MaturityParseResult:
    """一个『到期时间』字段的解析结论。

    必须区分 dirty 和 missing：前者说明用户填错了（可修），后者是没填（要问）。
    混为一谈会让『到期日填写质量』这个指标永久失真。
    """

    status: MaturityStatus
    maturity: date | None = None
    raw: str | None = None

    @property
    def is_dated(self) -> bool:
        return self.status == "dated" and self.maturity is not None


def parse_maturity_raw(raw: str | None) -> MaturityParseResult:
    """解析 CSV『到期时间』。

    实测脏值有三类：
      - ``可赎``        开放型哨兵，不是日期
      - ``2938146``     有人把基金代码填进了这一列（若当数字日期解析会得到 1902 年，
                        进而把产品误判成「逾期 4 万天」）
      - ``2026/13/45``  非法日期
    """
    if raw is None:
        return MaturityParseResult("missing", None, None)
    text = str(raw).strip()
    if not text:
        return MaturityParseResult("missing", None, raw)

    if text in _OPEN_ENDED_SENTINELS:
        return MaturityParseResult("open_ended", None, raw)

    normalized = text.replace("/", "-").replace(".", "-").replace("年", "-").replace("月", "-")
    normalized = normalized.replace("日", "").strip("-")
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y%m%d"):
        try:
            parsed = datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue
        # 明显不是日期的量级：证券代码/序号。1~9999 年的一定是人/程序填错列了。
        if not (1990 <= parsed.year <= 2100):
            return MaturityParseResult("dirty", None, raw)
        return MaturityParseResult("dated", parsed, raw)

    return MaturityParseResult("dirty", None, raw)


# ---------------------------------------------------------------------------
# 到期梯队
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LadderBucket:
    key: str
    label: str
    count: int
    amount: Decimal
    share: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["amount"] = float(self.amount)
        return d


@dataclass(frozen=True)
class MaturityLadder:
    as_of: date
    total_amount: Decimal
    buckets: tuple[LadderBucket, ...]
    overdue_count: int = 0
    overdue_amount: Decimal = Decimal(0)
    overdue_share: float = 0.0
    dirty_count: int = 0
    dirty_amount: Decimal = Decimal(0)
    open_ended_amount: Decimal = Decimal(0)
    open_ended_count: int = 0
    no_maturity_count: int = 0
    # dated/总产品数 的分档：<40% → low
    confidence: Literal["high", "medium", "low"] = "low"
    coverage: float = 0.0

    @property
    def bucket_total(self) -> Decimal:
        return sum((b.amount for b in self.buckets), Decimal(0))

    def buckets_count(self, key: str) -> int:
        for b in self.buckets:
            if b.key == key:
                return b.count
        return 0

    def bucket_of(self, *, product) -> LadderBucket:
        """按 product 的到期状态返回它落进的桶（测试和明细弹窗用）。"""
        maturity = product.maturity_date
        status: MaturityStatus = "dated" if maturity is not None else "missing"
        return self._classify(status, maturity)

    def _classify(self, status: MaturityStatus, maturity: date | None) -> LadderBucket:
        by_key = {b.key: b for b in self.buckets}
        if status == "open_ended":
            return by_key["open_ended"]
        if status in ("missing", "dirty"):
            return by_key["no_maturity"] if status == "missing" else by_key["dirty"]
        if maturity is None:
            return by_key["no_maturity"]
        days = (maturity - self.as_of).days
        if days < 0:
            return by_key["overdue"]
        if days <= 30:
            return by_key["d30"]
        if days <= 90:
            return by_key["d90"]
        if days <= 180:
            return by_key["d180"]
        if days <= 365:
            return by_key["d365"]
        return by_key["beyond"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "as_of": self.as_of.isoformat(),
            "total_amount": float(self.total_amount),
            "overdue_count": self.overdue_count,
            "overdue_amount": float(self.overdue_amount),
            "overdue_share": self.overdue_share,
            "dirty_count": self.dirty_count,
            "dirty_amount": float(self.dirty_amount),
            "open_ended_amount": float(self.open_ended_amount),
            "open_ended_count": self.open_ended_count,
            "no_maturity_count": self.no_maturity_count,
            "coverage": self.coverage,
            "confidence": self.confidence,
            "buckets": [b.to_dict() for b in self.buckets],
        }


_LADDER_SPEC: tuple[tuple[str, str], ...] = (
    ("overdue", "已逾期未回款"),
    ("d30", "30 天内到期"),
    ("d90", "90 天内"),
    ("d180", "180 天内"),
    ("d365", "1 年内"),
    ("beyond", "1 年以上"),
    ("open_ended", "开放型（可赎）"),
    ("no_maturity", "未填到期日"),
    ("dirty", "到期日填错"),
)


# ---------------------------------------------------------------------------
# 发行方集中度
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class InstitutionExposure:
    name: str
    amount: Decimal
    share: float = 0.0
    count: int = 0
    via_platform_fallback: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "amount": float(self.amount),
            "share": self.share,
            "count": self.count,
            "via_platform_fallback": self.via_platform_fallback,
        }


@dataclass(frozen=True)
class InstitutionConcentration:
    """信用敞口集中度。

    **刻意把「发行方」和「代销渠道」拆成两个维度。** 实测支付宝渠道下同时挂着货币基金、
    债券、券商理财、高端理财——支付宝≈货基，信用风险接近存款，跟招行理财完全不是一个量级。
    把渠道名当发行方算 HHI 会得出「支付宝占固收 15%」这种误导性结论。

    - issuer_*：从产品名识别的机构（高置信），这才是信用风险敞口
    - channel_*：购买渠道，反映的是**赎回通道依赖**，不是信用
    """

    total_amount: Decimal
    exposures: tuple[InstitutionExposure, ...]
    top1_name: str | None = None
    top1_amount: Decimal = Decimal(0)
    top1_share: float = 0.0
    top3_share: float = 0.0
    # 归一化 HHI（只算发行方）：0 = 完全分散，1 = 全部押在一个发行方
    hhi: float = 0.0
    issuer_hhi: float = 0.0
    issuer_top1_share: float = 0.0
    issuer_attribution_rate: float = 0.0
    channel_exposures: tuple[InstitutionExposure, ...] = ()
    channel_hhi: float = 0.0
    channel_top1_name: str | None = None
    channel_top1_amount: Decimal = Decimal(0)
    channel_top1_share: float = 0.0
    unattributed_count: int = 0
    unattributed_amount: Decimal = Decimal(0)
    attribution_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_amount": float(self.total_amount),
            "top1_name": self.top1_name,
            "top1_amount": float(self.top1_amount),
            "top1_share": self.top1_share,
            "top3_share": self.top3_share,
            "hhi": self.hhi,
            "issuer_hhi": self.issuer_hhi,
            "issuer_top1_share": self.issuer_top1_share,
            "issuer_attribution_rate": self.issuer_attribution_rate,
            "unattributed_count": self.unattributed_count,
            "unattributed_amount": float(self.unattributed_amount),
            "attribution_rate": self.attribution_rate,
            "channel_top1_name": self.channel_top1_name,
            "channel_top1_amount": float(self.channel_top1_amount),
            "channel_top1_share": self.channel_top1_share,
            "channel_hhi": self.channel_hhi,
            "exposures": [e.to_dict() for e in self.exposures],
            "channel_exposures": [e.to_dict() for e in self.channel_exposures],
        }


# ---------------------------------------------------------------------------
# 收益异常
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class YieldAnomaly:
    name: str
    kind: str
    severity: int
    message: str
    annual_return: float | None = None
    compound_return: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 数据完整度
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DataQualityReport:
    total_count: int
    missing_maturity_count: int
    missing_start_date_count: int
    missing_days_count: int
    missing_annual_count: int
    # 开放型（CSV 写『可赎』）不是缺失——它们本来就没有到期日
    open_ended_count: int = 0
    dirty_maturity_count: int = 0
    dated_count: int = 0
    missing_maturity_rate: float = 0.0
    missing_start_date_rate: float = 0.0
    missing_days_rate: float = 0.0
    missing_annual_rate: float = 0.0
    open_ended_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 提示
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RiskAlert:
    kind: str
    priority: Literal["high", "medium", "low"]
    title: str
    detail: str
    amount: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 顶层
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FixedIncomeRiskView:
    as_of: date
    total_amount: Decimal
    fixed_income_count: int
    equity_or_fund_excluded_amount: Decimal
    ladder: MaturityLadder
    concentration: InstitutionConcentration
    # 固收口径内、但产品名含权益敞口的（养老金账户里的 ETF联接、理财里的混合类等）
    equity_exposure_count: int = 0
    equity_exposure_amount: Decimal = Decimal(0)
    equity_exposure_losing_count: int = 0
    yield_anomalies: tuple[YieldAnomaly, ...] = ()
    data_quality: DataQualityReport | None = None
    alerts: tuple[RiskAlert, ...] = ()
    rolling_amount: Decimal = Decimal(0)
    rolling_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "as_of": self.as_of.isoformat(),
            "total_amount": float(self.total_amount),
            "fixed_income_count": self.fixed_income_count,
            "equity_or_fund_excluded_amount": float(self.equity_or_fund_excluded_amount),
            "equity_exposure_count": self.equity_exposure_count,
            "equity_exposure_amount": float(self.equity_exposure_amount),
            "equity_exposure_losing_count": self.equity_exposure_losing_count,
            "rolling_amount": float(self.rolling_amount),
            "rolling_count": self.rolling_count,
            "ladder": self.ladder.to_dict(),
            "concentration": self.concentration.to_dict(),
            "yield_anomalies": [a.to_dict() for a in self.yield_anomalies],
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "alerts": [a.to_dict() for a in self.alerts],
        }


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------
def _raw_hint(product) -> str | None:
    """优先用 model 自己的 maturity_date；raw_maturity 覆盖表在调用方提供脏值时用。"""
    return getattr(product, "_raw_maturity", None)


def _is_fx(product) -> bool:
    return _product_currency(product) != "CNY"


def _product_currency(product) -> str:
    """币种由 investment_type 隐含——InvestmentProduct 没有 currency 字段。

    口径和 data/portfolio.py 的 total_value 保持一致，否则这里的金额会和总资产视图对不上。
    """
    it = product.investment_type
    if it in (InvestmentType.US_STOCK, InvestmentType.USD_FUND):
        return "USD"
    if it in (InvestmentType.HK_STOCK, InvestmentType.HK_CASH, InvestmentType.HK_DIVIDEND_FUND):
        return "HKD"
    return "CNY"


def _to_cny(amount, product, usd_rate: Decimal, hkd_rate: Decimal) -> Decimal:
    if not amount:
        return Decimal(0)
    cur = _product_currency(product)
    if cur == "USD":
        return amount * (getattr(product, "usd_rate", None) or usd_rate)
    if cur == "HKD":
        return amount * (getattr(product, "hkd_rate", None) or hkd_rate)
    return amount


def _attr_amount(product, usd_rate: Decimal, hkd_rate: Decimal) -> Decimal:
    raw = getattr(product, "current_amount", None) or getattr(product, "initial_amount", None) or Decimal(0)
    return _to_cny(Decimal(raw), product, usd_rate, hkd_rate)


def _identify_issuer(name: str) -> str | None:
    """从产品名识别发行机构（只认名称，不回落渠道——渠道不是信用敞口）。

    实测 69 只固收产品里只有 16 只名称含机构名，命中率约 23%。剩下的靠名称认不出来，
    计入 unattributed 而不是猜——猜出来的集中度会让人误判信用风险。
    """
    for keyword, label in ISSUER_KEYWORDS:
        if keyword in name:
            return label
    return None


# ---------------------------------------------------------------------------
# 组装
# ---------------------------------------------------------------------------
def build_fixed_income_risk_view(
    products: Iterable,
    *,
    as_of: date | None = None,
    raw_maturity: dict[str, str] | None = None,
    usd_rate: Decimal = Decimal("7.0"),
    hkd_rate: Decimal = Decimal("0.9"),
) -> FixedIncomeRiskView:
    """构建固收+ 风险视图。

    Args:
        products: InvestmentProduct 序列；非固收类型会被排除并单独统计金额。
        as_of: 基准日。**必须显式传入或接受默认值后落进输出**——到期梯队对日期敏感，
            跨日重跑会得出不同结论，结果里带 as_of 才能在合并数据源时对齐。
        raw_maturity: {产品名: CSV 原始到期时间字符串}。用于识别「可赎」哨兵和脏值；
            解析后的干净日期仍以 product.maturity_date 为准。
    """
    as_of = as_of or date.today()
    raw_maturity = raw_maturity or {}
    all_products = list(products)

    in_scope = [p for p in all_products if p.investment_type in FIXED_INCOME_TYPES]
    # 固收口径内再按名称剔掉含权益敞口的：它们的钱也是钱，但风险来源是权益波动不是信用
    equity_exposed = [p for p in in_scope if has_equity_exposure(p.name)]
    fixed = [p for p in in_scope if not has_equity_exposure(p.name)]
    # 被排除的非固收金额要单独报出来——否则「固收只占总资产 16%」这个事实会被这个视图藏起来
    excluded = sum(
        (_attr_amount(p, usd_rate, hkd_rate) for p in all_products if p.investment_type not in FIXED_INCOME_TYPES),
        Decimal(0),
    )

    total = sum((_attr_amount(p, usd_rate, hkd_rate) for p in fixed), Decimal(0))

    ladder = _build_ladder(fixed, as_of=as_of, raw_maturity=raw_maturity, usd_rate=usd_rate, hkd_rate=hkd_rate)
    concentration = _build_concentration(fixed, usd_rate=usd_rate, hkd_rate=hkd_rate)
    anomalies = _find_yield_anomalies(fixed)
    dq = _build_data_quality(fixed, ladder)
    rolling_amount = sum((_attr_amount(p, usd_rate, hkd_rate) for p in fixed if p.is_rolling), Decimal(0))
    equity_amount = sum((_attr_amount(p, usd_rate, hkd_rate) for p in equity_exposed), Decimal(0))
    equity_losing = sum(
        1 for p in equity_exposed if getattr(p, "annual_return", None) is not None and float(p.annual_return) < 0
    )
    alerts = _build_alerts(
        ladder,
        concentration,
        anomalies,
        dq,
        rolling_amount,
        total,
        equity_amount=equity_amount,
        equity_losing=equity_losing,
    )

    return FixedIncomeRiskView(
        as_of=as_of,
        total_amount=total,
        fixed_income_count=len(fixed),
        equity_or_fund_excluded_amount=excluded,
        ladder=ladder,
        concentration=concentration,
        equity_exposure_count=len(equity_exposed),
        equity_exposure_amount=equity_amount,
        equity_exposure_losing_count=equity_losing,
        yield_anomalies=anomalies,
        data_quality=dq,
        alerts=alerts,
        rolling_amount=rolling_amount,
        rolling_count=sum(1 for p in fixed if p.is_rolling),
    )


def _build_ladder(products, *, as_of, raw_maturity, usd_rate, hkd_rate) -> MaturityLadder:
    amounts: dict[str, Decimal] = {k: Decimal(0) for k, _ in _LADDER_SPEC}
    counts: dict[str, int] = {k: 0 for k, _ in _LADDER_SPEC}
    dated_count = 0

    for p in products:
        raw = raw_maturity.get(p.name)
        parsed = parse_maturity_raw(raw if raw is not None else None)
        # 脏值只从 raw 覆盖表来；正常路径信任 model.maturity_date（已由 parser 规范化）
        maturity = p.maturity_date
        if raw is not None:
            status = parsed.status
            if status == "dated":
                maturity = parsed.maturity
        else:
            status = "dated" if maturity is not None else "missing"

        amount = _attr_amount(p, usd_rate, hkd_rate)
        if status == "dated" and maturity is None:
            status = "missing"
        if status == "dated":
            dated_count += 1
            days = (maturity - as_of).days
            if days < 0:
                key = "overdue"
            elif days <= 30:
                key = "d30"
            elif days <= 90:
                key = "d90"
            elif days <= 180:
                key = "d180"
            elif days <= 365:
                key = "d365"
            else:
                key = "beyond"
        elif status == "open_ended":
            key = "open_ended"
        elif status == "dirty":
            key = "dirty"
        else:
            key = "no_maturity"
        amounts[key] += amount
        counts[key] += 1

    total = sum(amounts.values(), Decimal(0))
    buckets = tuple(
        LadderBucket(
            key=key,
            label=label,
            count=counts[key],
            amount=amounts[key],
            share=float(amounts[key] / total) if total else 0.0,
        )
        for key, label in _LADDER_SPEC
    )
    coverage = dated_count / len(products) if products else 0.0
    if coverage >= 0.7:
        confidence: Literal["high", "medium", "low"] = "high"
    elif coverage >= 0.4:
        confidence = "medium"
    else:
        confidence = "low"

    return MaturityLadder(
        as_of=as_of,
        total_amount=total,
        buckets=buckets,
        overdue_count=counts["overdue"],
        overdue_amount=amounts["overdue"],
        overdue_share=float(amounts["overdue"] / total) if total else 0.0,
        dirty_count=counts["dirty"],
        dirty_amount=amounts["dirty"],
        open_ended_amount=amounts["open_ended"],
        open_ended_count=counts["open_ended"],
        no_maturity_count=counts["no_maturity"],
        confidence=confidence,
        coverage=coverage,
    )


def _build_concentration(products, *, usd_rate, hkd_rate) -> InstitutionConcentration:
    """发行方与代销渠道分开统计。"""
    issuers: dict[str, Decimal] = {}
    issuer_counts: dict[str, int] = {}
    channels: dict[str, Decimal] = {}
    channel_counts: dict[str, int] = {}
    unattributed = Decimal(0)
    unattributed_count = 0
    total = Decimal(0)

    for p in products:
        amount = _attr_amount(p, usd_rate, hkd_rate)
        total += amount

        issuer = _identify_issuer(p.name)
        if issuer is None:
            unattributed += amount
            unattributed_count += 1
        else:
            issuers[issuer] = issuers.get(issuer, Decimal(0)) + amount
            issuer_counts[issuer] = issuer_counts.get(issuer, 0) + 1

        # 渠道独立统计：反映赎回通道依赖，与信用敞口无关
        if p.platform_amounts:
            top = max(p.platform_amounts.items(), key=lambda kv: float(kv[1] or 0))
            if top[1] and float(top[1]) > 0:
                label = PLATFORM_LABELS.get(top[0], top[0])
                channels[label] = channels.get(label, Decimal(0)) + amount
                channel_counts[label] = channel_counts.get(label, 0) + 1

    def _exposures(bucket: dict[str, Decimal], counts: dict[str, int]) -> tuple:
        return tuple(
            InstitutionExposure(
                name=name,
                amount=amount,
                share=float(amount / total) if total else 0.0,
                count=counts[name],
            )
            for name, amount in sorted(bucket.items(), key=lambda kv: -kv[1])
        )

    exposures = _exposures(issuers, issuer_counts)
    channel_exposures = _exposures(channels, channel_counts)
    top1 = exposures[0] if exposures else None
    channel_top1 = channel_exposures[0] if channel_exposures else None
    issuer_total = sum(issuers.values(), Decimal(0))
    # 显式转 float：Decimal 的 ** 会保留 Decimal 类型，sum() 出来就不是 float 了
    issuer_hhi = float(sum((a / issuer_total) ** 2 for a in issuers.values())) if issuer_total else 0.0

    return InstitutionConcentration(
        total_amount=total,
        exposures=exposures,
        top1_name=top1.name if top1 else None,
        top1_amount=top1.amount if top1 else Decimal(0),
        top1_share=top1.share if top1 else 0.0,
        top3_share=sum(e.share for e in exposures[:3]),
        hhi=issuer_hhi,
        issuer_hhi=issuer_hhi,
        issuer_top1_share=top1.share if top1 else 0.0,
        issuer_attribution_rate=float(issuer_total / total) if total else 0.0,
        channel_exposures=channel_exposures,
        channel_hhi=(sum((e.share**2 for e in channel_exposures), 0.0) if channel_exposures else 0.0),
        channel_top1_name=channel_top1.name if channel_top1 else None,
        channel_top1_amount=channel_top1.amount if channel_top1 else Decimal(0),
        channel_top1_share=channel_top1.share if channel_top1 else 0.0,
        unattributed_count=unattributed_count,
        unattributed_amount=unattributed,
        attribution_rate=float(issuer_total / total) if total else 0.0,
    )


def _find_yield_anomalies(products) -> tuple[YieldAnomaly, ...]:
    found: list[YieldAnomaly] = []
    for p in products:
        annual = getattr(p, "annual_return", None)
        compound = getattr(p, "compound_return", None)
        annual_f = float(annual) if annual is not None else None
        compound_f = float(compound) if compound is not None else None

        if annual_f is not None and annual_f < 0:
            found.append(
                YieldAnomaly(
                    name=p.name,
                    kind="negative_return",
                    severity=70,
                    message=f"年化 {annual_f:.2f}% 为负，债市回撤或含权益敞口，确认是否继续持有",
                    annual_return=annual_f,
                    compound_return=compound_f,
                )
            )
        if annual_f is not None and annual_f > float(PLAUSIBLE_ANNUALIZED_CEILING):
            found.append(
                YieldAnomaly(
                    name=p.name,
                    kind="implausible_annualized",
                    severity=90,
                    message=(
                        f"年化 {annual_f:.2f}% 远超固收+ 合理上限 "
                        f"{PLAUSIBLE_ANNUALIZED_CEILING}%，多半是把累计收益填成了年化，请核对 CSV"
                    ),
                    annual_return=annual_f,
                    compound_return=compound_f,
                )
            )
        if annual_f is not None and compound_f is not None:
            diff = compound_f - annual_f
            if abs(diff) > float(COMPOUND_DIVERGENCE_TOLERANCE):
                found.append(
                    YieldAnomaly(
                        name=p.name,
                        kind="compound_divergence",
                        severity=40,
                        message=(
                            f"年化 {annual_f:.2f}% 与复利年化 {compound_f:.2f}% 相差 {diff:+.2f}pct，"
                            "超出费用/计息天数能解释的范围，核对是否填错列"
                        ),
                        annual_return=annual_f,
                        compound_return=compound_f,
                    )
                )

    found.sort(key=lambda a: -a.severity)
    return tuple(found)


def _build_data_quality(products, ladder: MaturityLadder | None = None) -> DataQualityReport:
    """数据完整度。

    「缺到期日」只统计**既没有日期、也没标开放型**的——实测 CSV 的到期时间列从不空白，
    92 行写的是「可赎」。把开放型算成缺失会虚报缺失率，让人白去补数据。
    """
    n = len(products)
    if n == 0:
        return DataQualityReport(0, 0, 0, 0, 0)
    miss_s = sum(1 for p in products if p.start_date is None)
    miss_d = sum(1 for p in products if p.investment_days is None)
    miss_a = sum(1 for p in products if p.annual_return is None)

    if ladder is not None:
        open_ended = ladder.open_ended_count
        dirty = ladder.dirty_count
        missing = ladder.no_maturity_count
        dated = sum(ladder.buckets_count(k) for k in ("overdue", "d30", "d90", "d180", "d365", "beyond"))
    else:
        open_ended = dirty = 0
        missing = sum(1 for p in products if p.maturity_date is None)
        dated = n - missing

    return DataQualityReport(
        total_count=n,
        missing_maturity_count=missing,
        missing_start_date_count=miss_s,
        missing_days_count=miss_d,
        missing_annual_count=miss_a,
        open_ended_count=open_ended,
        dirty_maturity_count=dirty,
        dated_count=dated,
        missing_maturity_rate=missing / n,
        missing_start_date_rate=miss_s / n,
        missing_days_rate=miss_d / n,
        missing_annual_rate=miss_a / n,
        open_ended_rate=open_ended / n,
    )


def _build_alerts(
    ladder,
    concentration,
    anomalies,
    dq,
    rolling_amount,
    total,
    *,
    equity_amount: Decimal = Decimal(0),
    equity_losing: int = 0,
) -> tuple[RiskAlert, ...]:
    alerts: list[RiskAlert] = []

    if equity_losing:
        alerts.append(
            RiskAlert(
                kind="equity_exposure_loss",
                priority="medium",
                title=f"{equity_losing} 只固收口径内产品含权益敞口且在亏损",
                detail=(
                    f"共 {float(equity_amount):,.0f} 元。这些是养老金/理财账户里的指数、混合、"
                    "ETF联接类，亏损来自权益波动而非信用事件——按固收+ 的信用口径读会误判，"
                    "需要单独看权益回撤。"
                ),
                amount=float(equity_amount),
            )
        )

    if ladder.overdue_amount > 0:
        alerts.append(
            RiskAlert(
                kind="overdue",
                priority="high",
                title=f"{ladder.overdue_count} 只已过到期日，共 {float(ladder.overdue_amount):,.0f} 元",
                detail=(
                    "到期日已过但仍挂在持仓里：要么 CSV 到期日没随续期更新，要么资金没回款。"
                    "这两件事都要先确认，否则到期梯队和再投资计划都建立在错误数据上。"
                ),
                amount=float(ladder.overdue_amount),
            )
        )
    if concentration.hhi >= 0.25 and concentration.top1_name:
        alerts.append(
            RiskAlert(
                kind="concentration",
                priority="high" if concentration.hhi >= 0.4 else "medium",
                title=f"{concentration.top1_name} 占固收 {concentration.top1_share * 100:.0f}%（HHI {concentration.hhi:.2f}）",
                detail="单一发行方/代销方敞口过集中，信用事件会同时冲击这些产品。",
                amount=float(concentration.top1_amount),
            )
        )
    for a in anomalies:
        if a.kind in ("implausible_annualized", "negative_return"):
            alerts.append(
                RiskAlert(
                    kind=a.kind,
                    priority="high" if a.severity >= 70 else "medium",
                    title=f"{a.name}：{a.message.split('，')[0]}",
                    detail=a.message,
                )
            )
    if ladder.dirty_amount > 0:
        alerts.append(
            RiskAlert(
                kind="dirty_maturity",
                priority="medium",
                title=f"{ladder.dirty_count} 只到期日格式非法",
                detail=(
                    f"共 {float(ladder.dirty_amount):,.0f} 元的『到期时间』列填了非日期内容"
                    "（实测见过基金代码），已单独归桶，修正后到期梯队才完整。"
                ),
                amount=float(ladder.dirty_amount),
            )
        )
    if dq and dq.missing_maturity_rate >= 0.5:
        alerts.append(
            RiskAlert(
                kind="low_coverage",
                priority="medium",
                title=f"{dq.missing_maturity_rate * 100:.0f}% 的固收产品没填到期日",
                detail=(
                    f"到期梯队覆盖率仅 {ladder.coverage * 100:.0f}%（可信度：{ladder.confidence}）。"
                    "补齐到期日才能算出再投资缺口和流动性窗口。"
                ),
                amount=float(total),
            )
        )
    if rolling_amount > 0:
        alerts.append(
            RiskAlert(
                kind="rolling",
                priority="low",
                title=f"{float(rolling_amount):,.0f} 元为滚动产品",
                detail="滚动产品到期后按当时利率重定价，收益不锁定；关注续作时的利率变化。",
                amount=float(rolling_amount),
            )
        )

    order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: (order[a.priority], -a.amount))
    return tuple(alerts)
