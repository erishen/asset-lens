from decimal import Decimal
from typing import Any

from ..data.models import Portfolio, SellRecord


class AnalysisEvaluationMixin:
    def generate_comprehensive_evaluation(
        self,
        portfolio: Portfolio,
        sell_records: list[SellRecord] | None = None,
    ) -> dict[str, Any]:
        total_initial = Decimal("0")
        total_profit = Decimal("0")
        total_value = Decimal("0")

        def _is_usd_product(product):
            from ..data.models import InvestmentType

            if product.investment_type in [InvestmentType.US_STOCK, InvestmentType.USD_FUND]:
                return True
            type_str = product.investment_type.value if product.investment_type else ""
            name_str = product.name or ""
            return "美元" in type_str or "美元" in name_str or "USD" in name_str.upper()

        def _is_hkd_product(product):
            from ..data.models import InvestmentType

            if product.investment_type in [
                InvestmentType.HK_STOCK,
                InvestmentType.HK_CASH,
                InvestmentType.HK_DIVIDEND_FUND,
            ]:
                return True
            type_str = product.investment_type.value if product.investment_type else ""
            name_str = product.name or ""
            return "港元" in type_str or "港元" in name_str or "HKD" in name_str.upper()

        for product in portfolio.products:
            if product.current_amount:
                current = product.current_amount
                if _is_usd_product(product):
                    current = current * (product.usd_rate or portfolio.usd_rate)
                elif _is_hkd_product(product):
                    current = current * (product.hkd_rate or portfolio.hkd_rate)
                total_value += current

            if product.profit_amount:
                total_profit += product.profit_amount

            if product.start_date and product.initial_amount:
                net_invest = portfolio._calculate_net_invest(product)
                initial = net_invest if net_invest else product.initial_amount
            elif product.current_amount:
                initial = product.current_amount
            else:
                continue

            if _is_usd_product(product):
                rate = product.usd_rate or portfolio.usd_rate
                initial = initial * rate
            elif _is_hkd_product(product):
                rate = product.hkd_rate or portfolio.hkd_rate
                initial = initial * rate

            total_initial += initial

        realized_profit = Decimal("0")
        realized_initial = Decimal("0")
        if sell_records:
            for record in sell_records:
                if record.profit_amount:
                    realized_profit += record.profit_amount
                if record.initial_amount:
                    realized_initial += record.initial_amount

        unrealized_profit = total_value - total_initial

        total_investment = total_initial

        total_current_amount = total_value

        if total_investment > Decimal("0"):
            total_profit_all = unrealized_profit + realized_profit
            overall_return_rate = (total_profit_all / total_investment) * 100
        else:
            overall_return_rate = Decimal("0")

        weighted_annual_return = Decimal("0")
        total_weight = Decimal("0")

        for product in portfolio.products:
            has_interest = product.interest_payment and product.interest_payment > 0
            if has_interest:
                annual_value = product.annual_return if product.annual_return else product.compound_return
            else:
                annual_value = product.compound_return if product.compound_return else product.annual_return
            if annual_value is not None and product.initial_amount:
                net_invest = portfolio._calculate_net_invest(product)
                weight = net_invest if net_invest else product.initial_amount
                if _is_usd_product(product):
                    rate = product.usd_rate or portfolio.usd_rate
                    weight = weight * rate
                elif _is_hkd_product(product):
                    rate = product.hkd_rate or portfolio.hkd_rate
                    weight = weight * rate
                if weight <= 0:
                    continue
                weighted_annual_return += annual_value * weight
                total_weight += weight
            elif product.current_amount and product.current_amount > 0 and not product.start_date:
                weight = product.current_amount
                if _is_usd_product(product):
                    rate = product.usd_rate or portfolio.usd_rate
                    weight = weight * rate
                elif _is_hkd_product(product):
                    rate = product.hkd_rate or portfolio.hkd_rate
                    weight = weight * rate
                if weight > 0:
                    total_weight += weight

        if sell_records:
            for record in sell_records:
                has_interest = record.interest_payment and record.interest_payment > 0
                if has_interest:
                    annual_value = record.annual_return if record.annual_return else record.compound_return
                else:
                    annual_value = record.compound_return if record.compound_return else record.annual_return
                if annual_value and record.initial_amount:
                    weight = record.initial_amount
                    weighted_annual_return += annual_value * weight
                    total_weight += weight

        weighted_annual_return = weighted_annual_return / total_weight if total_weight > Decimal("0") else Decimal("0")

        avg_investment_days = Decimal("0")
        products_with_amount = [p for p in portfolio.products if p.current_amount and p.current_amount > 0]
        if products_with_amount:
            avg_investment_days = Decimal(
                str(sum(p.investment_days or 0 for p in products_with_amount) / len(products_with_amount))
            )

        if avg_investment_days > Decimal("0") and overall_return_rate > Decimal("0"):
            avg_investment_years = avg_investment_days / Decimal("360")
            if avg_investment_years > Decimal("0"):
                time_weighted_return = (
                    (Decimal("1") + overall_return_rate / Decimal("100")) ** (Decimal("1") / avg_investment_years)
                    - Decimal("1")
                ) * Decimal("100")
            else:
                time_weighted_return = Decimal("0")
        else:
            time_weighted_return = Decimal("0")

        current_annualized_rate = max(weighted_annual_return / Decimal("100"), Decimal("0.02"))
        expected_annual_return = total_current_amount * current_annualized_rate

        return {
            "total_investment": str(total_investment),
            "total_current_amount": str(total_current_amount),
            "realized_profit": str(realized_profit),
            "unrealized_profit": str(unrealized_profit),
            "overall_return_rate": f"{overall_return_rate:.2f}%",
            "weighted_annual_return": f"{weighted_annual_return:.2f}%",
            "time_weighted_return": f"{time_weighted_return:.2f}%",
            "avg_investment_days": round(avg_investment_days, 1),
            "expected_annual_return": str(expected_annual_return),
            "current_annualized_rate": f"{float(current_annualized_rate) * 100:.1f}",
            "evaluation": self._get_evaluation_text(overall_return_rate, time_weighted_return),
        }

    def _get_evaluation_text(self, return_rate: Decimal, time_weighted: Decimal) -> str:
        if return_rate > Decimal("10"):
            return "✅ 整体投资表现优秀，跑赢银行定期"
        elif return_rate > Decimal("5"):
            return "✅ 整体投资表现良好，跑赢银行定期"
        elif return_rate > Decimal("2"):
            advice = "✅ 整体投资表现尚可，跑赢银行定期"
            if time_weighted > Decimal("5"):
                advice += f"\n💡 投资时机把握较好（时间加权年化{time_weighted:.1f}%），建议优化资金配置提升整体收益"
            return advice
        else:
            return "⚠️  整体投资表现较低，建议优化投资策略"

    def generate_investment_efficiency(
        self, portfolio: Portfolio, sell_records: list[Any] | None = None
    ) -> dict[str, Any]:
        from ..data.models import SellRecord

        total_value = portfolio.total_value or Decimal("0")
        total_initial = portfolio.total_initial or Decimal("0")

        capital_efficiency = total_value / total_initial * 100 if total_initial > Decimal("0") else Decimal("100")

        avg_investment_days = Decimal("0")
        products_with_amount = [p for p in portfolio.products if p.current_amount and p.current_amount > 0]
        if products_with_amount:
            avg_investment_days = Decimal(
                str(sum(p.investment_days or 0 for p in products_with_amount) / len(products_with_amount))
            )

        avg_investment_years = (
            avg_investment_days / Decimal("360") if avg_investment_days > Decimal("0") else Decimal("0")
        )

        unrealized_profit = portfolio.total_profit or Decimal("0")
        realized_profit = Decimal("0")
        if sell_records:
            for record in sell_records:
                if isinstance(record, SellRecord) and record.profit_amount:
                    realized_profit += record.profit_amount

        total_profit_all = unrealized_profit + realized_profit

        if avg_investment_years > Decimal("0") and total_initial > Decimal("0"):
            overall_return_rate = (total_profit_all / total_initial) * Decimal("100")
            overall_return = Decimal("1") + overall_return_rate / Decimal("100")
            annual_growth_rate = (overall_return ** (Decimal("1") / avg_investment_years) - Decimal("1")) * Decimal(
                "100"
            )
        else:
            annual_growth_rate = Decimal("0")

        return {
            "capital_efficiency": f"{capital_efficiency:.1f}%",
            "annual_growth_rate": f"{annual_growth_rate:.2f}%",
            "avg_investment_years": float(avg_investment_years),
        }
