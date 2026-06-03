import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ..data.models import Transaction
from .irr_algorithms import (
    IRRAlgorithmsMixin,
    _calculate_irr_numpy_cached,
    _calculate_irr_with_days_cached,
)

logger = logging.getLogger(__name__)


@dataclass
class YearlyIRRResult:
    year: int
    irr: float | None
    total_investment: float
    total_return: float
    cashflow_count: int
    start_date: date
    end_date: date


@dataclass
class IRRComparisonResult:
    years: list[YearlyIRRResult]
    average_irr: float | None
    best_year: int | None
    worst_year: int | None
    trend: str


class IRRCalculator(IRRAlgorithmsMixin):
    _cache_hits = 0
    _cache_misses = 0

    def __init__(self) -> None:
        from .irr_algorithms import HAS_NUMPY

        self.use_numpy = HAS_NUMPY

    @classmethod
    def get_cache_stats(cls) -> dict[str, Any]:
        days_info = _calculate_irr_with_days_cached.cache_info()
        numpy_info = _calculate_irr_numpy_cached.cache_info()
        return {
            "days_cache": {
                "hits": days_info.hits,
                "misses": days_info.misses,
                "size": days_info.currsize,
                "maxsize": days_info.maxsize,
            },
            "numpy_cache": {
                "hits": numpy_info.hits,
                "misses": numpy_info.misses,
                "size": numpy_info.currsize,
                "maxsize": numpy_info.maxsize,
            },
        }

    @classmethod
    def clear_cache(cls) -> None:
        _calculate_irr_with_days_cached.cache_clear()
        _calculate_irr_numpy_cached.cache_clear()

    def calculate_irr(self, cashflows: list[float]) -> float | None:
        if len(cashflows) < 2:
            return None

        if self.use_numpy:
            irr_value = self.calculate_irr_numpy(cashflows)
            if irr_value is not None:
                return irr_value

        return self.calculate_irr_newton(cashflows)

    def calculate_annualized_irr(
        self,
        transactions: list[Transaction],
        current_value: Decimal,
        reference_date: datetime,
    ) -> Decimal | None:
        if not transactions:
            return None

        cashflows = []
        base_date = min(t.transaction_date for t in transactions)

        if isinstance(base_date, date):
            base_date = datetime.combine(base_date, datetime.min.time())

        for t in transactions:
            tx_date = t.transaction_date
            if isinstance(tx_date, date):
                tx_date = datetime.combine(tx_date, datetime.min.time())
            days = (tx_date - base_date).days
            period = days / 360.0
            if t.action.lower() in ["buy", "买入"]:
                cashflows.append(-float(t.amount) * period)
            elif t.action.lower() in ["sell", "卖出"]:
                cashflows.append(float(t.amount) * period)

        last_date = max(t.transaction_date for t in transactions)
        if isinstance(last_date, date):
            last_date = datetime.combine(last_date, datetime.min.time())
        last_period = (reference_date - base_date).days / 360.0
        cashflows.append(float(current_value) * last_period)

        irr_value = self.calculate_irr(cashflows)
        if irr_value is not None:
            return Decimal(str(irr_value))

        return None

    def calculate_simple_annual_return(
        self,
        initial_amount: Decimal,
        current_amount: Decimal,
        days: int,
    ) -> Decimal | None:
        if initial_amount <= 0:
            return None

        total_return = current_amount - initial_amount
        return_rate = (total_return / initial_amount) * Decimal("100")

        if days <= 0:
            return return_rate

        years = Decimal(days) / Decimal("360")
        if years == 0:
            return return_rate

        try:
            annual_return = (
                (Decimal("1") + return_rate / Decimal("100")) ** (Decimal("1") / years) - Decimal("1")
            ) * Decimal("100")
            return annual_return
        except (ValueError, TypeError):
            annual_return = return_rate * Decimal("360") / Decimal(days)
            return annual_return

    def calculate_compound_return(
        self,
        initial_amount: Decimal,
        current_amount: Decimal,
        days: int,
    ) -> Decimal | None:
        return self.calculate_simple_annual_return(initial_amount, current_amount, days)

    def calculate_irr_high_precision(
        self,
        cashflows: list[float],
    ) -> float | None:
        results = []

        if self.use_numpy:
            irr_numpy = self.calculate_irr_numpy(cashflows)
            if irr_numpy is not None:
                results.append(irr_numpy)

        irr_bisection = self.calculate_irr_bisection(cashflows)
        if irr_bisection is not None:
            results.append(irr_bisection)

        irr_newton = self.calculate_irr_newton(cashflows)
        if irr_newton is not None:
            results.append(irr_newton)

        if not results:
            return None

        if len(results) == 1:
            return results[0]

        filtered = [r for r in results if -100 < r < 1000]
        if not filtered:
            return results[0]

        return sum(filtered) / len(filtered)

    def calculate_yearly_irr(
        self,
        transactions: list[Transaction],
        current_value: Decimal,
        reference_date: datetime,
    ) -> IRRComparisonResult:
        if not transactions:
            return IRRComparisonResult(
                years=[],
                average_irr=None,
                best_year=None,
                worst_year=None,
                trend="稳定",
            )

        yearly_data: dict[int, list[tuple[date, float]]] = {}

        for t in transactions:
            tx_date = t.transaction_date
            if isinstance(tx_date, datetime):
                tx_date = tx_date.date()

            year = tx_date.year
            if year not in yearly_data:
                yearly_data[year] = []

            amount = float(t.amount)
            if t.action.lower() in ["buy", "买入"]:
                amount = -amount
            yearly_data[year].append((tx_date, amount))

        years_results: list[YearlyIRRResult] = []

        for year in sorted(yearly_data.keys()):
            cfs = yearly_data[year]
            if len(cfs) < 2:
                continue

            irr = self.calculate_xirr(cfs)

            total_investment = sum(-a for _, a in cfs if a < 0)
            total_return = sum(a for _, a in cfs if a > 0)

            dates = [d for d, _ in cfs]

            years_results.append(
                YearlyIRRResult(
                    year=year,
                    irr=irr,
                    total_investment=total_investment,
                    total_return=total_return,
                    cashflow_count=len(cfs),
                    start_date=min(dates),
                    end_date=max(dates),
                )
            )

        if not years_results:
            return IRRComparisonResult(
                years=[],
                average_irr=None,
                best_year=None,
                worst_year=None,
                trend="稳定",
            )

        valid_irrs = [y.irr for y in years_results if y.irr is not None]
        average_irr = sum(valid_irrs) / len(valid_irrs) if valid_irrs else None

        best_year = None
        worst_year = None
        if valid_irrs:
            best_idx = max(range(len(years_results)), key=lambda i: years_results[i].irr or float("-inf"))
            worst_idx = min(range(len(years_results)), key=lambda i: years_results[i].irr or float("inf"))
            best_year = years_results[best_idx].year
            worst_year = years_results[worst_idx].year

        trend = "稳定"
        if len(valid_irrs) >= 2:
            first_half = valid_irrs[: len(valid_irrs) // 2]
            second_half = valid_irrs[len(valid_irrs) // 2 :]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)

            if avg_second > avg_first * 1.1:
                trend = "上升"
            elif avg_second < avg_first * 0.9:
                trend = "下降"

        return IRRComparisonResult(
            years=years_results,
            average_irr=average_irr,
            best_year=best_year,
            worst_year=worst_year,
            trend=trend,
        )


irr_calculator = IRRCalculator()
