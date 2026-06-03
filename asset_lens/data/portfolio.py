from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from .models import InvestmentProduct, InvestmentType


@dataclass
class Portfolio:
    products: list[InvestmentProduct] = field(default_factory=list)
    usd_rate: Decimal = Decimal("7.1242")
    hkd_rate: Decimal = Decimal("0.9157")
    asset_summaries: list = field(default_factory=list)
    exchange_rate_history: list = field(default_factory=list)
    sell_records: list = field(default_factory=list)

    def add_product(self, product: InvestmentProduct) -> None:
        self.products.append(product)

    def get_by_type(self, investment_type: InvestmentType) -> list[InvestmentProduct]:
        return [p for p in self.products if p.investment_type == investment_type]

    def get_by_risk(self, risk_level) -> list[InvestmentProduct]:
        return [p for p in self.products if p.risk_level == risk_level]

    @property
    def total_value(self) -> Decimal:
        total = Decimal("0")
        for product in self.products:
            if product.current_amount:
                amount = product.current_amount
                if product.investment_type in [InvestmentType.US_STOCK, InvestmentType.USD_FUND]:
                    amount = amount * (product.usd_rate or self.usd_rate)
                elif product.investment_type in [
                    InvestmentType.HK_STOCK,
                    InvestmentType.HK_CASH,
                    InvestmentType.HK_DIVIDEND_FUND,
                ]:
                    amount = amount * (product.hkd_rate or self.hkd_rate)
                total += amount
        return total

    @property
    def total_initial(self) -> Decimal:
        total = Decimal("0")
        for product in self.products:
            if product.start_date and product.initial_amount:
                amount = product.initial_amount
            elif product.current_amount:
                amount = product.current_amount
            else:
                continue

            if product.investment_type in [InvestmentType.US_STOCK, InvestmentType.USD_FUND]:
                amount = amount * (product.usd_rate or self.usd_rate)
            elif product.investment_type in [
                InvestmentType.HK_STOCK,
                InvestmentType.HK_CASH,
                InvestmentType.HK_DIVIDEND_FUND,
            ]:
                amount = amount * (product.hkd_rate or self.hkd_rate)
            total += amount
        return total

    def _calculate_net_invest(self, product: InvestmentProduct) -> Decimal | None:
        from .transaction_parser import calculate_net_invest_from_transactions

        if product.investment_type == InvestmentType.DCA_FUND:
            return product.initial_amount

        if not product.transaction_records:
            return None

        is_qdii = product.investment_type in [InvestmentType.USD_FUND]
        suffix = self._get_data_suffix()

        net_invest = calculate_net_invest_from_transactions(
            product.transaction_records, suffix, is_qdii, product.initial_amount
        )

        return net_invest if net_invest != 0 else None

    def _get_data_suffix(self) -> int:
        from ..config import config

        data_dir = config.get_latest_data_dir()
        if data_dir and data_dir.name.startswith("money_csv_"):
            try:
                return int(data_dir.name.replace("money_csv_", ""))
            except ValueError:
                pass

        today = date.today()
        return today.year * 10000 + today.month * 100 + today.day

    @property
    def total_profit(self) -> Decimal:
        total = Decimal("0")
        for product in self.products:
            if not product.current_amount:
                continue

            current = product.current_amount
            if product.start_date and product.initial_amount:
                initial = product.initial_amount
            else:
                initial = product.current_amount

            if product.investment_type in [InvestmentType.US_STOCK, InvestmentType.USD_FUND]:
                rate = product.usd_rate or self.usd_rate
                current = current * rate
                initial = initial * rate
            elif product.investment_type in [
                InvestmentType.HK_STOCK,
                InvestmentType.HK_CASH,
                InvestmentType.HK_DIVIDEND_FUND,
            ]:
                rate = product.hkd_rate or self.hkd_rate
                current = current * rate
                initial = initial * rate

            total += current - initial

        return total

    @property
    def overall_return_rate(self) -> Decimal | None:
        if self.total_initial == Decimal("0"):
            return None
        return (self.total_profit / self.total_initial) * Decimal("100")

    def get_type_distribution(self) -> dict[str, Any]:
        type_stats: dict[str, dict[str, Any]] = {}
        for product in self.products:
            type_name = product.investment_type.value
            if type_name not in type_stats:
                type_stats[type_name] = {
                    "count": 0,
                    "total_value": Decimal("0"),
                    "products": [],
                }
            type_stats[type_name]["count"] += 1
            type_stats[type_name]["total_value"] += product.get_converted_amount(self.usd_rate, self.hkd_rate)
            type_stats[type_name]["products"].append(product)

        total = sum(stats["total_value"] for stats in type_stats.values())
        for stats in type_stats.values():
            if total > Decimal("0"):
                stats["percentage"] = (stats["total_value"] / total) * Decimal("100")
            else:
                stats["percentage"] = Decimal("0")

        return type_stats

    def get_risk_distribution(self) -> dict[str, Any]:
        risk_stats: dict[str, dict[str, Any]] = {}
        for product in self.products:
            risk_name = product.risk_level.value
            if risk_name not in risk_stats:
                risk_stats[risk_name] = {
                    "count": 0,
                    "total_value": Decimal("0"),
                    "products": [],
                }
            risk_stats[risk_name]["count"] += 1
            risk_stats[risk_name]["total_value"] += product.get_converted_amount(self.usd_rate, self.hkd_rate)
            risk_stats[risk_name]["products"].append(product)

        total = sum(stats["total_value"] for stats in risk_stats.values())
        for stats in risk_stats.values():
            if total > Decimal("0"):
                stats["percentage"] = (stats["total_value"] / total) * Decimal("100")
            else:
                stats["percentage"] = Decimal("0")

        return risk_stats
