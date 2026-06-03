"""
Currency converter for asset-lens.
多币种汇率转换功能
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..config import config
from ..data.models import Currency
from .json_cache import read_json_cache, write_json_cache


class CurrencyConverter:
    """货币转换器"""

    def __init__(self) -> None:
        self.rates: dict[Currency, Decimal] = {
            Currency.CNY: Decimal("1.0"),
        }

        self.default_rates: dict[Currency, Decimal | None] = {
            Currency.USD: Decimal(str(config.default_usd_rate)),
            Currency.HKD: Decimal(str(config.default_hkd_rate)),
        }

        self.load_cached_rates()

    def load_cached_rates(self) -> None:
        """从缓存加载汇率数据"""
        cache_file = config.project_root / "cache" / "exchange_rates.json"

        cached_data = read_json_cache(cache_file)
        if cached_data is not None:
            for currency_str, rate in cached_data.get("rates", {}).items():
                try:
                    currency = Currency(currency_str)
                    self.rates[currency] = Decimal(str(rate))
                except ValueError:
                    pass

    def save_cached_rates(self) -> None:
        """保存汇率数据到缓存"""
        cache_file = config.project_root / "cache" / "exchange_rates.json"

        data = {
            "rates": {currency.value: str(rate) for currency, rate in self.rates.items()},
            "updated_at": datetime.now().isoformat(),
        }

        write_json_cache(cache_file, data)

    def get_rate(self, currency: Currency) -> Decimal:
        """
        获取指定货币的汇率（相对于CNY）
        Args:
            currency: 货币类型
        Returns:
            汇率（1 外币 = X CNY）
        """
        # 如果已有缓存汇率，直接使用
        if currency in self.rates:
            return self.rates[currency]

        # 使用配置中的默认汇率
        if currency in self.default_rates:
            rate = self.default_rates[currency]
            if rate is not None:
                self.rates[currency] = rate
                return rate

        # 未知货币，使用1.0
        return Decimal("1.0")

    def set_rate(self, currency: Currency, rate: Decimal) -> None:
        """
        设置货币汇率
        Args:
            currency: 货币类型
            rate: 汇率（1 外币 = X CNY）
        """
        self.rates[currency] = rate

    def convert_to_cny(
        self,
        amount: Decimal,
        from_currency: Currency,
        exchange_rate: Decimal | None = None,
    ) -> Decimal:
        """
        将指定货币金额转换为人民币
        Args:
            amount: 金额
            from_currency: 源货币类型
            exchange_rate: 自定义汇率（优先使用）
        Returns:
            人民币金额
        """
        if from_currency == Currency.CNY:
            return amount

        # 使用自定义汇率
        if exchange_rate is not None:
            return amount * exchange_rate

        # 使用缓存的汇率
        rate = self.get_rate(from_currency)
        return amount * rate

    def convert_from_cny(
        self,
        amount: Decimal,
        to_currency: Currency,
        exchange_rate: Decimal | None = None,
    ) -> Decimal:
        """
        将人民币转换为指定货币
        Args:
            amount: 人民币金额
            to_currency: 目标货币类型
            exchange_rate: 自定义汇率（优先使用）
        Returns:
            目标货币金额
        """
        if to_currency == Currency.CNY:
            return amount

        # 使用自定义汇率
        if exchange_rate is not None:
            return amount / exchange_rate

        # 使用缓存的汇率
        rate = self.get_rate(to_currency)
        return amount / rate

    def convert(
        self,
        amount: Decimal,
        from_currency: Currency,
        to_currency: Currency,
        from_rate: Decimal | None = None,
        to_rate: Decimal | None = None,
    ) -> Decimal:
        """
        货币转换（任意货币之间）
        Args:
            amount: 金额
            from_currency: 源货币类型
            to_currency: 目标货币类型
            from_rate: 源货币的汇率（相对于CNY）
            to_rate: 目标货币的汇率（相对于CNY）
        Returns:
            转换后的金额
        """
        if from_currency == to_currency:
            return amount

        # 先转换为CNY，再转换为目标货币
        cny_amount = self.convert_to_cny(amount, from_currency, from_rate)
        return self.convert_from_cny(cny_amount, to_currency, to_rate)


# 全局货币转换器实例
currency_converter = CurrencyConverter()


_USD_INV_TYPES = {"美股", "美元基金", "美元基金（美元）"}
_HKD_INV_TYPES = {"港股", "现金（港元）", "股息基金（港元）"}

_global_rates_cache: dict[str, float | bool | None] = {"usd": None, "hkd": None, "loaded": False}


def get_global_rates(data_dir: Path | None = None) -> tuple[float, float]:
    """获取全局汇率（从数据文件的资产汇总表格加载）

    Args:
        data_dir: 可选的数据目录路径

    Returns:
        (usd_rate, hkd_rate) 元组
    """
    if not _global_rates_cache["loaded"]:
        from ..config import config as _config
        from ..data.csv_parser import CSVParser

        if data_dir is None:
            data_dir = Path(_config.real_data_path) if _config.data_mode == "real" else Path(_config.sample_data_path)

        try:
            usd_rate, hkd_rate = CSVParser.get_exchange_rates(data_dir)
            _global_rates_cache["usd"] = usd_rate
            _global_rates_cache["hkd"] = hkd_rate
        except (ValueError, KeyError, TypeError):
            _global_rates_cache["usd"] = float(_config.default_usd_rate)
            _global_rates_cache["hkd"] = float(_config.default_hkd_rate)

        _global_rates_cache["loaded"] = True

    return _global_rates_cache["usd"] or 7.2, _global_rates_cache["hkd"] or 0.92


def get_cny_amount(product: Any) -> float:
    """获取产品的人民币金额（考虑汇率转换）

    统一的人民币金额转换函数，替代在 report.py 和 comparison.py 中的重复实现。

    Args:
        product: 投资产品对象，需包含 current_amount, investment_type, usd_rate, hkd_rate 属性

    Returns:
        人民币金额
    """
    amount = float(product.current_amount or 0)
    if amount == 0:
        return 0

    inv_type = product.investment_type.value if product.investment_type else ""
    global_usd, global_hkd = get_global_rates()

    if inv_type in _USD_INV_TYPES:
        usd_rate = float(product.usd_rate) if product.usd_rate else global_usd
        return amount * usd_rate
    elif inv_type in _HKD_INV_TYPES:
        hkd_rate = float(product.hkd_rate) if product.hkd_rate else global_hkd
        return amount * hkd_rate

    return amount


def get_initial_cny_amount(product: Any) -> float:
    """获取产品初始金额的人民币值（考虑汇率转换）

    Args:
        product: 投资产品对象

    Returns:
        人民币金额
    """
    amount = float(product.initial_amount or 0)
    if amount == 0:
        return 0

    inv_type = product.investment_type.value if product.investment_type else ""
    global_usd, global_hkd = get_global_rates()

    if inv_type in _USD_INV_TYPES:
        usd_rate = float(product.usd_rate) if product.usd_rate else global_usd
        return amount * usd_rate
    elif inv_type in _HKD_INV_TYPES:
        hkd_rate = float(product.hkd_rate) if product.hkd_rate else global_hkd
        return amount * hkd_rate

    return amount


def get_profit_cny_amount(product: Any) -> float:
    """获取产品收益的人民币值（考虑汇率转换）

    对于没有初始金额的产品（如货币基金），收益为0

    Args:
        product: 投资产品对象

    Returns:
        人民币收益金额
    """
    initial = get_initial_cny_amount(product)
    if initial == 0:
        return 0
    return get_cny_amount(product) - initial


def format_amount(product: Any) -> str:
    """格式化金额显示（美元资产显示美元和人民币）

    Args:
        product: 投资产品对象

    Returns:
        格式化的金额字符串
    """
    amount = float(product.current_amount or 0)
    if amount == 0:
        return "¥0"

    inv_type = product.investment_type.value if product.investment_type else ""
    global_usd, global_hkd = get_global_rates()

    if inv_type in _USD_INV_TYPES:
        usd_rate = float(product.usd_rate) if product.usd_rate else global_usd
        cny_amount = amount * usd_rate
        return f"${amount:,.0f} (¥{cny_amount:,.0f})"
    elif inv_type in _HKD_INV_TYPES:
        hkd_rate = float(product.hkd_rate) if product.hkd_rate else global_hkd
        cny_amount = amount * hkd_rate
        return f"HK${amount:,.0f} (¥{cny_amount:,.0f})"

    return f"¥{amount:,.0f}"
