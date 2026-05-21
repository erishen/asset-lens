"""
Portfolio Calculator - 投资组合计算服务
将计算逻辑从 Portfolio 数据模型中分离，提供缓存优化
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import InvestmentProduct, Portfolio

_US_INVESTMENT_TYPES = None
_HK_INVESTMENT_TYPES = None


def _get_us_investment_types() -> list:
    global _US_INVESTMENT_TYPES
    if _US_INVESTMENT_TYPES is None:
        from .models import InvestmentType

        _US_INVESTMENT_TYPES = [InvestmentType.US_STOCK, InvestmentType.USD_FUND]
    return _US_INVESTMENT_TYPES


def _get_hk_investment_types() -> list:
    global _HK_INVESTMENT_TYPES
    if _HK_INVESTMENT_TYPES is None:
        from .models import InvestmentType

        _HK_INVESTMENT_TYPES = [
            InvestmentType.HK_STOCK,
            InvestmentType.HK_CASH,
            InvestmentType.HK_DIVIDEND_FUND,
        ]
    return _HK_INVESTMENT_TYPES


class PortfolioCalculator:
    """投资组合计算服务（带缓存优化）"""

    def __init__(self, portfolio: "Portfolio"):
        self._portfolio = portfolio
        self._cache: dict[str, Any] = {}

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()

    def _get_cache_key(self, method: str, *args) -> str:
        """生成缓存键"""
        return f"{method}:{hash(args)}"

    def _convert_amount(
        self,
        amount: Decimal,
        product: "InvestmentProduct",
        usd_rate: Decimal | None = None,
        hkd_rate: Decimal | None = None,
    ) -> Decimal:
        """统一汇率转换逻辑"""

        usd_rate = usd_rate or self._portfolio.usd_rate
        hkd_rate = hkd_rate or self._portfolio.hkd_rate

        if product.investment_type in _get_us_investment_types():
            return amount * (product.usd_rate or usd_rate)
        elif product.investment_type in _get_hk_investment_types():
            return amount * (product.hkd_rate or hkd_rate)
        return amount

    def calculate_total_value(self) -> Decimal:
        """计算总资产（带缓存）"""
        cache_key = "total_value"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore

        total = Decimal("0")
        for product in self._portfolio.products:
            if not product.start_date:
                continue
            if product.current_amount:
                amount = self._convert_amount(product.current_amount, product)
                total += amount

        self._cache[cache_key] = total
        return total

    def calculate_total_initial(self) -> Decimal:
        """计算总初始投资（带缓存）"""
        cache_key = "total_initial"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore

        total = Decimal("0")
        for product in self._portfolio.products:
            if not product.start_date:
                continue

            net_invest = self._calculate_net_invest(product)

            if net_invest and net_invest > 0:
                amount = self._convert_amount(net_invest, product)
                total += amount
            elif product.initial_amount:
                amount = self._convert_amount(product.initial_amount, product)
                total += amount

        self._cache[cache_key] = total
        return total

    def calculate_total_profit(self) -> Decimal:
        """计算总收益（带缓存）"""
        cache_key = "total_profit"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore

        total = Decimal("0")
        for product in self._portfolio.products:
            if not product.start_date:
                continue

            net_invest = self._calculate_net_invest(product)

            if net_invest and net_invest > 0:
                initial = net_invest
            elif product.initial_amount:
                initial = product.initial_amount
            else:
                continue

            if product.current_amount:
                current = self._convert_amount(product.current_amount, product)
                initial_converted = self._convert_amount(initial, product)
                total += current - initial_converted

        self._cache[cache_key] = total
        return total

    def calculate_overall_return_rate(self) -> Decimal | None:
        """计算整体收益率"""
        total_initial = self.calculate_total_initial()
        if total_initial == Decimal("0"):
            return None
        total_profit = self.calculate_total_profit()
        return (total_profit / total_initial) * Decimal("100")

    def get_type_distribution(self) -> dict[str, Any]:
        """获取类型分布（带缓存）"""
        cache_key = "type_distribution"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore

        type_stats: dict[str, dict[str, Any]] = {}
        for product in self._portfolio.products:
            type_name = product.investment_type.value
            if type_name not in type_stats:
                type_stats[type_name] = {
                    "count": 0,
                    "total_value": Decimal("0"),
                    "products": [],
                }
            type_stats[type_name]["count"] += 1
            type_stats[type_name]["total_value"] += self._convert_amount(
                product.current_amount or Decimal("0"), product
            )
            type_stats[type_name]["products"].append(product)

        total = sum(stats["total_value"] for stats in type_stats.values())
        for stats in type_stats.values():
            if total > Decimal("0"):
                stats["percentage"] = (stats["total_value"] / total) * Decimal("100")
            else:
                stats["percentage"] = Decimal("0")

        self._cache[cache_key] = type_stats
        return type_stats

    def get_risk_distribution(self) -> dict[str, Any]:
        """获取风险分布（带缓存）"""
        cache_key = "risk_distribution"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore

        risk_stats: dict[str, dict[str, Any]] = {}
        for product in self._portfolio.products:
            risk_name = product.risk_level.value
            if risk_name not in risk_stats:
                risk_stats[risk_name] = {
                    "count": 0,
                    "total_value": Decimal("0"),
                    "products": [],
                }
            risk_stats[risk_name]["count"] += 1
            risk_stats[risk_name]["total_value"] += self._convert_amount(
                product.current_amount or Decimal("0"), product
            )
            risk_stats[risk_name]["products"].append(product)

        total = sum(stats["total_value"] for stats in risk_stats.values())
        for stats in risk_stats.values():
            if total > Decimal("0"):
                stats["percentage"] = (stats["total_value"] / total) * Decimal("100")
            else:
                stats["percentage"] = Decimal("0")

        self._cache[cache_key] = risk_stats
        return risk_stats

    def _calculate_net_invest(self, product: "InvestmentProduct") -> Decimal | None:
        """计算产品的净投入"""
        from .models import InvestmentType
        from .transaction_parser import calculate_net_invest_from_transactions

        if product.investment_type == InvestmentType.DCA_FUND:
            return product.initial_amount

        if not product.transaction_records:
            return None

        is_qdii = product.investment_type in _get_us_investment_types()
        suffix = self._get_data_suffix()

        net_invest = calculate_net_invest_from_transactions(
            product.transaction_records, suffix, is_qdii, product.initial_amount
        )

        return net_invest if net_invest > 0 else None

    def _get_data_suffix(self) -> int:
        """获取数据目录后缀"""
        from ..config import config

        data_dir = config.get_latest_data_dir()
        if data_dir and data_dir.name.startswith("money_csv_"):
            try:
                return int(data_dir.name.replace("money_csv_", ""))
            except (ValueError, TypeError):
                pass

        today = date.today()
        return today.year * 10000 + today.month * 100 + today.day


def create_calculator(portfolio: "Portfolio") -> PortfolioCalculator:
    """创建 PortfolioCalculator 实例"""
    return PortfolioCalculator(portfolio)
