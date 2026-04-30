"""
IRR Calculator - 内部收益率计算器
支持多种算法和缓存优化
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache

logger = logging.getLogger(__name__)

try:
    from numpy import irr as numpy_irr  # type: ignore
    from numpy_financial import xirr as numpy_xirr  # type: ignore

    HAS_NUMPY = True
    HAS_NUMPY_FINANCIAL = True
except ImportError:
    HAS_NUMPY = False
    HAS_NUMPY_FINANCIAL = False

from ..data.models import Transaction


@dataclass
class YearlyIRRResult:
    """年度 IRR 结果"""

    year: int
    irr: float | None
    total_investment: float
    total_return: float
    cashflow_count: int
    start_date: date
    end_date: date


@dataclass
class IRRComparisonResult:
    """IRR 对比结果"""

    years: list[YearlyIRRResult]
    average_irr: float | None
    best_year: int | None
    worst_year: int | None
    trend: str  # "上升", "下降", "稳定"


def _hash_cashflows_with_days(cashflows: list[dict]) -> tuple:
    """将现金流列表转换为可哈希的元组，用于缓存"""
    return tuple((cf["amount"], cf["days"]) for cf in cashflows)


def _hash_cashflows(cashflows: list[float]) -> tuple[float, ...]:
    """将现金流列表转换为可哈希的元组，用于缓存"""
    return tuple(cashflows)


@lru_cache(maxsize=256)
def _calculate_irr_with_days_cached(
    cashflows_hash: tuple,
    guess: float = 0.1,
    tolerance: float = 1e-6,
    max_iterations: int = 200,
) -> float | None:
    """
    带缓存的 IRR 计算（使用带天数的现金流）
    """
    cashflows = [{"amount": cf[0], "days": cf[1]} for cf in cashflows_hash]
    rate = guess
    for _ in range(max_iterations):
        npv = 0.0
        dnpv = 0.0
        for cf in cashflows:
            factor = (1 + rate) ** (cf["days"] / 360)
            npv += cf["amount"] / factor
            dnpv -= (cf["amount"] * cf["days"]) / 360 / (factor * (1 + rate))

        if abs(npv) < tolerance:
            return rate

        if abs(dnpv) < tolerance:
            rate += 0.01
            continue

        new_rate = rate - npv / dnpv
        clamped_rate = max(-0.99, min(10, new_rate))

        if abs(clamped_rate - rate) < tolerance:
            return clamped_rate

        rate = clamped_rate

    return rate


@lru_cache(maxsize=256)
def _calculate_irr_numpy_cached(cashflows_hash: tuple[float, ...]) -> float | None:
    """
    带缓存的 numpy IRR 计算
    """
    if not HAS_NUMPY:
        return None
    cashflows = list(cashflows_hash)
    try:
        irr_value = numpy_irr(cashflows)
        return irr_value * 100 if irr_value is not None else None
    except Exception as e:
        logger.warning(f"numpy IRR 计算失败: {e}")
        return None


class IRRCalculator:
    """IRR 计算器（带缓存优化）"""

    _cache_hits = 0
    _cache_misses = 0

    def __init__(self) -> None:
        self.use_numpy = HAS_NUMPY

    @classmethod
    def get_cache_stats(cls) -> dict:
        """获取缓存统计信息"""
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
        """清除所有缓存"""
        _calculate_irr_with_days_cached.cache_clear()
        _calculate_irr_numpy_cached.cache_clear()

    @staticmethod
    def calculate_irr_with_days(
        cashflows: list[dict],
        guess: float = 0.1,
        tolerance: float = 1e-6,
        max_iterations: int = 200,
    ) -> float | None:
        """
        使用带天数的现金流计算 IRR（与 ts-demo 保持一致）
        Args:
            cashflows: 现金流列表，格式为 [{"amount": float, "days": int}, ...]
            guess: 初始猜测值
            tolerance: 容忍误差
            max_iterations: 最大迭代次数
        Returns:
            IRR 值（小数形式，如 0.1 表示 10%）
        """
        if not cashflows:
            return None
        cashflows_hash = _hash_cashflows_with_days(cashflows)
        return _calculate_irr_with_days_cached(cashflows_hash, guess, tolerance, max_iterations)

    @staticmethod
    def calculate_irr_numpy(cashflows: list[float]) -> float | None:
        """
        使用 numpy 计算IRR
        Args:
            cashflows: 现金流列表，负数表示投入，正数表示收回
        Returns:
            IRR 值（百分比），如果计算失败则返回 None
        """
        try:
            irr_value = numpy_irr(cashflows)
            return float(irr_value * 100)  # 转换为百分比
        except Exception:
            return None

    @staticmethod
    def calculate_irr_newton(cashflows: list[float], max_iter: int = 100, tol: float = 1e-6) -> float | None:
        """
        使用牛顿法计算IRR

        Args:
            cashflows: 现金流列表
            max_iter: 最大迭代次数
            tol: 容忍误差

        Returns:
            IRR 值（百分比），如果计算失败则返回 None
        """
        # 检查现金流
        if len(cashflows) < 2:
            return None

        # 确保有正有负的现金流
        has_positive = any(c > 0 for c in cashflows)
        has_negative = any(c < 0 for c in cashflows)
        if not (has_positive and has_negative):
            return None

        # NPV 函数（添加数值稳定性检查）
        def npv(rate: float) -> float:
            total = 0.0
            for i, cf in enumerate(cashflows):
                # 添加数值稳定性检查
                if abs(rate) > 10:  # 如果 rate 太大，直接返回一个大值
                    return float("inf") if cf > 0 else float("-inf")

                denominator = (1 + rate) ** i
                # 检查分母是否过大
                if abs(denominator) > 1e100:
                    break

                total += cf / denominator
            return total

        # NPV 的导数（添加数值稳定性检查）
        def npv_derivative(rate: float) -> float:
            total = 0.0
            for i, cf in enumerate(cashflows):
                # 添加数值稳定性检查
                if abs(rate) > 10:
                    return float("inf") if cf > 0 else float("-inf")

                denominator = (1 + rate) ** (i + 1)
                # 检查分母是否过大
                if abs(denominator) > 1e100:
                    break

                total += -i * cf / denominator
            return total

        # 牛顿法迭代
        rate = 0.1  # 初始猜测值 10%
        for _ in range(max_iter):
            try:
                npv_value = npv(rate)
                npv_derivative_value = npv_derivative(rate)

                # 检查数值是否有效
                if not (abs(npv_derivative_value) > 1e-10 and abs(npv_derivative_value) < 1e100):
                    break

                new_rate = rate - npv_value / npv_derivative_value

                # 检查新利率是否在合理范围内
                if not (-1 < new_rate < 10):  # IRR 应该在 -100% 到 1000% 之间
                    break

                if abs(new_rate - rate) < tol:
                    irr_value = new_rate
                    return irr_value * 100  # 转换为百分比

                rate = new_rate
            except (OverflowError, ValueError, ZeroDivisionError):
                # 如果出现数值错误，尝试使用 numpy 的 IRR 计算
                if HAS_NUMPY:
                    try:
                        irr_value = numpy_irr(cashflows)
                        return irr_value * 100 if irr_value is not None else None
                    except Exception:
                        return None
                return None

        # 如果牛顿法失败，尝试使用 numpy 的 IRR 计算
        if HAS_NUMPY:
            try:
                irr_value = numpy_irr(cashflows)
                return irr_value * 100 if irr_value is not None else None
            except Exception:
                return None

        return None

        return None

    def calculate_irr(self, cashflows: list[float]) -> float | None:
        """
        计算 IRR（内部收益率）
        Args:
            cashflows: 现金流列表，负数表示投入，正数表示收回
        Returns:
            IRR 值（百分比），如果计算失败则返回 None
        """
        if len(cashflows) < 2:
            return None

        # 优先使用 numpy
        if self.use_numpy:
            irr_value = self.calculate_irr_numpy(cashflows)
            if irr_value is not None:
                return irr_value

        # 回退到牛顿法
        return self.calculate_irr_newton(cashflows)

    def calculate_annualized_irr(
        self,
        transactions: list[Transaction],
        current_value: Decimal,
        reference_date: datetime,
    ) -> Decimal | None:
        """
        计算年化 IRR
        Args:
            transactions: 交易记录列表
            current_value: 当前价值（作为最后的正向现金流）
            reference_date: 参考日期（用于计算时间间隔）
        Returns:
            年化 IRR 值（百分比）
        """
        if not transactions:
            return None

        # 转换交易记录为现金流
        cashflows = []
        base_date = min(t.transaction_date for t in transactions)

        # 确保 base_date 是 datetime 对象
        if isinstance(base_date, date):
            base_date = datetime.combine(base_date, datetime.min.time())

        for t in transactions:
            # 计算从基准日期到交易日期的天数
            tx_date = t.transaction_date
            if isinstance(tx_date, date):
                tx_date = datetime.combine(tx_date, datetime.min.time())
            days = (tx_date - base_date).days
            period = days / 360.0  # 转换为年（使用 360 天，与 ts-demo 一致）
            # 买入为负，卖出为正
            if t.action.lower() in ["buy", "买入"]:
                cashflows.append(-float(t.amount) * period)
            elif t.action.lower() in ["sell", "卖出"]:
                cashflows.append(float(t.amount) * period)

        # 添加当前价值（作为最后的正向现金流）
        last_date = max(t.transaction_date for t in transactions)
        if isinstance(last_date, date):
            last_date = datetime.combine(last_date, datetime.min.time())
        last_period = (reference_date - base_date).days / 360.0
        cashflows.append(float(current_value) * last_period)

        # 计算 IRR
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
        """
        计算简单年化收益率
        Args:
            initial_amount: 初始金额
            current_amount: 当前金额
            days: 投资天数
        Returns:
            年化收益率（百分比）
        """
        if initial_amount <= 0:
            return None

        total_return = current_amount - initial_amount
        return_rate = (total_return / initial_amount) * Decimal("100")

        if days <= 0:
            return return_rate

        # 年化收益率 = (1 + 收益率)^(360/天数) - 1（使用 360 天，与 ts-demo 一致）
        years = Decimal(days) / Decimal("360")
        if years == 0:
            return return_rate

        try:
            annual_return = (
                (Decimal("1") + return_rate / Decimal("100")) ** (Decimal("1") / years) - Decimal("1")
            ) * Decimal("100")
            return annual_return
        except Exception:
            # 如果计算失败，使用简单线性年化
            annual_return = return_rate * Decimal("360") / Decimal(days)
            return annual_return

    def calculate_compound_return(
        self,
        initial_amount: Decimal,
        current_amount: Decimal,
        days: int,
    ) -> Decimal | None:
        """
        计算复利年化收益率
        Args:
            initial_amount: 初始金额
            current_amount: 当前金额
            days: 投资天数
        Returns:
            复利年化收益率（百分比）
        """
        return self.calculate_simple_annual_return(initial_amount, current_amount, days)

    @staticmethod
    def calculate_irr_bisection(
        cashflows: list[float],
        tol: float = 1e-10,
        max_iter: int = 1000,
    ) -> float | None:
        """
        使用二分法计算 IRR（更高精度）

        Args:
            cashflows: 现金流列表
            tol: 容忍误差
            max_iter: 最大迭代次数

        Returns:
            IRR 值（百分比）
        """
        if len(cashflows) < 2:
            return None

        has_positive = any(c > 0 for c in cashflows)
        has_negative = any(c < 0 for c in cashflows)
        if not (has_positive and has_negative):
            return None

        def npv(rate: float) -> float:
            total = 0.0
            for i, cf in enumerate(cashflows):
                total += cf / ((1 + rate) ** i)
            return total

        low, high = -0.99, 10.0

        if npv(low) * npv(high) > 0:
            return None

        for _ in range(max_iter):
            mid = (low + high) / 2
            npv_mid = npv(mid)

            if abs(npv_mid) < tol:
                return mid * 100

            if npv(low) * npv_mid < 0:
                high = mid
            else:
                low = mid

        return ((low + high) / 2) * 100

    @staticmethod
    def calculate_xirr(
        cashflows: list[tuple[date, float]],
        guess: float = 0.1,
        tol: float = 1e-10,
        max_iter: int = 1000,
    ) -> float | None:
        """
        计算 XIRR（不规则现金流内部收益率）

        Args:
            cashflows: 现金流列表，格式为 [(日期, 金额), ...]
            guess: 初始猜测值
            tol: 容忍误差
            max_iter: 最大迭代次数

        Returns:
            年化 IRR 值（百分比）
        """
        if len(cashflows) < 2:
            return None

        if HAS_NUMPY_FINANCIAL:
            try:
                dates = [cf[0] for cf in cashflows]
                amounts = [cf[1] for cf in cashflows]
                result = numpy_xirr(amounts, dates)
                return result * 100 if result is not None else None
            except Exception:
                pass

        sorted_cfs = sorted(cashflows, key=lambda x: x[0])
        base_date = sorted_cfs[0][0]

        def days_between(d1: date, d2: date) -> int:
            return (d2 - d1).days

        def xnpv(rate: float) -> float:
            total = 0.0
            for d, amount in sorted_cfs:
                days = days_between(base_date, d)
                total += amount / ((1 + rate) ** (days / 365.0))
            return total

        def xnpv_derivative(rate: float) -> float:
            total = 0.0
            for d, amount in sorted_cfs:
                days = days_between(base_date, d)
                years = days / 365.0
                total -= amount * years / ((1 + rate) ** (years + 1))
            return total

        rate = guess
        for _ in range(max_iter):
            npv = xnpv(rate)
            if abs(npv) < tol:
                return rate * 100

            dnpv = xnpv_derivative(rate)
            if abs(dnpv) < 1e-15:
                break

            new_rate = rate - npv / dnpv
            if new_rate <= -1:
                new_rate = -0.99
            elif new_rate > 10:
                new_rate = 10.0

            if abs(new_rate - rate) < tol:
                return new_rate * 100

            rate = new_rate

        return rate * 100 if -1 < rate < 10 else None

    def calculate_irr_high_precision(
        self,
        cashflows: list[float],
    ) -> float | None:
        """
        高精度 IRR 计算（尝试多种算法）

        Args:
            cashflows: 现金流列表

        Returns:
            IRR 值（百分比）
        """
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
        """
        计算年度 IRR 对比分析

        Args:
            transactions: 交易记录列表
            current_value: 当前价值
            reference_date: 参考日期

        Returns:
            IRR 对比结果
        """
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


# 全局 IRR 计算器实例
irr_calculator = IRRCalculator()
