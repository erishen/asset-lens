import logging
from datetime import date
from functools import lru_cache

logger = logging.getLogger(__name__)

try:
    import numpy as _np

    numpy_irr = getattr(_np, "irr", None)
    from numpy_financial import xirr as numpy_xirr

    HAS_NUMPY = numpy_irr is not None
    HAS_NUMPY_FINANCIAL = True
except ImportError:
    HAS_NUMPY = False
    HAS_NUMPY_FINANCIAL = False


def _hash_cashflows_with_days(cashflows: list[dict[str, float]]) -> tuple[tuple[float, float], ...]:
    return tuple((cf["amount"], cf["days"]) for cf in cashflows)


def _hash_cashflows(cashflows: list[float]) -> tuple[float, ...]:
    return tuple(cashflows)


@lru_cache(maxsize=256)
def _calculate_irr_with_days_cached(
    cashflows_hash: tuple[tuple[float, float], ...],
    guess: float = 0.1,
    tolerance: float = 1e-6,
    max_iterations: int = 200,
) -> float | None:
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
    if not HAS_NUMPY or numpy_irr is None:
        return None
    cashflows = list(cashflows_hash)
    try:
        irr_value = numpy_irr(cashflows)
        return irr_value * 100 if irr_value is not None else None
    except (ValueError, OverflowError, ZeroDivisionError) as e:
        logger.warning(f"numpy IRR 计算失败: {e}")
        return None


class IRRAlgorithmsMixin:
    @staticmethod
    def calculate_irr_with_days(
        cashflows: list[dict[str, float]],
        guess: float = 0.1,
        tolerance: float = 1e-6,
        max_iterations: int = 200,
    ) -> float | None:
        if not cashflows:
            return None
        cashflows_hash = _hash_cashflows_with_days(cashflows)
        return _calculate_irr_with_days_cached(cashflows_hash, guess, tolerance, max_iterations)

    @staticmethod
    def calculate_irr_numpy(cashflows: list[float]) -> float | None:
        try:
            if numpy_irr is None:
                return None
            irr_value = numpy_irr(cashflows)
            return float(irr_value * 100)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def calculate_irr_newton(cashflows: list[float], max_iter: int = 100, tol: float = 1e-6) -> float | None:
        if len(cashflows) < 2:
            return None

        has_positive = any(c > 0 for c in cashflows)
        has_negative = any(c < 0 for c in cashflows)
        if not (has_positive and has_negative):
            return None

        def npv(rate: float) -> float:
            total = 0.0
            for i, cf in enumerate(cashflows):
                if abs(rate) > 10:
                    return float("inf") if cf > 0 else float("-inf")

                denominator = (1 + rate) ** i
                if abs(denominator) > 1e100:
                    break

                total += cf / denominator
            return total

        def npv_derivative(rate: float) -> float:
            total = 0.0
            for i, cf in enumerate(cashflows):
                if abs(rate) > 10:
                    return float("inf") if cf > 0 else float("-inf")

                denominator = (1 + rate) ** (i + 1)
                if abs(denominator) > 1e100:
                    break

                total += -i * cf / denominator
            return total

        rate = 0.1
        for _ in range(max_iter):
            try:
                npv_value = npv(rate)
                npv_derivative_value = npv_derivative(rate)

                if not (abs(npv_derivative_value) > 1e-10 and abs(npv_derivative_value) < 1e100):
                    break

                new_rate = rate - npv_value / npv_derivative_value

                if not (-1 < new_rate < 10):
                    break

                if abs(new_rate - rate) < tol:
                    irr_value = new_rate
                    return irr_value * 100

                rate = new_rate
            except (OverflowError, ValueError, ZeroDivisionError):
                if HAS_NUMPY and numpy_irr is not None:
                    try:
                        irr_value = numpy_irr(cashflows)
                        return irr_value * 100 if irr_value is not None else None
                    except (ValueError, OverflowError, ZeroDivisionError) as e:
                        logger.debug(f"忽略异常: {e}")
                        return None
                return None

        if HAS_NUMPY and numpy_irr is not None:
            try:
                irr_value = numpy_irr(cashflows)
                return irr_value * 100 if irr_value is not None else None
            except (ValueError, OverflowError, ZeroDivisionError) as e:
                logger.debug(f"忽略异常: {e}")
                return None

        return None

    @staticmethod
    def calculate_irr_bisection(
        cashflows: list[float],
        tol: float = 1e-10,
        max_iter: int = 1000,
    ) -> float | None:
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
        if len(cashflows) < 2:
            return None

        if HAS_NUMPY_FINANCIAL:
            try:
                dates = [cf[0] for cf in cashflows]
                amounts = [cf[1] for cf in cashflows]
                result = numpy_xirr(amounts, dates)
                return result * 100 if result is not None else None
            except (ValueError, OverflowError, ZeroDivisionError) as e:
                logger.debug(f"忽略异常: {e}")

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
