"""
Currency converter for asset-lens.
多币种汇率转换功能
"""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from ..config import config
from ..data.models import Currency


class CurrencyConverter:
    """货币转换器"""

    def __init__(self):
        self.rates: Dict[Currency, Decimal] = {
            Currency.CNY: Decimal("1.0"),  # 人民币汇率为1
        }

        # 加载配置中的默认汇率
        self.default_rates = {
            Currency.USD: config.default_usd_rate,
            Currency.HKD: config.default_hkd_rate,
        }

        # 加载缓存的汇率
        self.load_cached_rates()

    def load_cached_rates(self) -> None:
        """从缓存加载汇率数据"""
        cache_file = config.project_root / "cache" / "exchange_rates.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    for currency_str, rate in cached_data.get("rates", {}).items():
                        try:
                            currency = Currency(currency_str)
                            self.rates[currency] = Decimal(str(rate))
                        except ValueError:
                            pass
            except Exception as e:
                print(f"加载汇率缓存失败: {e}")

    def save_cached_rates(self) -> None:
        """保存汇率数据到缓存"""
        cache_dir = config.project_root / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = cache_dir / "exchange_rates.json"

        try:
            data = {
                "rates": {
                    currency.value: str(rate) for currency, rate in self.rates.items()
                },
                "updated_at": datetime.now().isoformat(),
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存汇率缓存失败: {e}")

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
