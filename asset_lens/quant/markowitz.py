"""Markowitz 均值-方差组合优化。

基于 ``scipy.optimize.minimize(SLSQP)``，不引入 cvxpy。提供三种目标：

* :func:`min_variance` — 全局最小方差组合。
* :func:`max_sharpe` — 最大夏普比率组合。
* :func:`target_return` — 给定最低单期收益下的最小方差组合。
* :func:`efficient_frontier` — 沿收益轴扫描得到有效前沿。

优化使用样本均值与样本协方差（:mod:`asset_lens.quant.base`），单位均为**单期**。
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .base import (
    Constraints,
    OptimizationResult,
    ReturnsLike,
    as_returns_matrix,
    covariance,
    expected_returns,
    portfolio_returns,
)


def _max_achievable_return(mu: np.ndarray, constraints: Constraints) -> float:
    """权重上下界与 sum=1 约束下可达到的最大组合期望收益。

    按收益从高到低贪心分配：先给每个资产铺 min_weight，再把剩余额度依次堆给收益最高的资产，
    直到触及 max_weight 或用完额度。``target_return`` 的可达性预检与 ``efficient_frontier``
    的收益轴上界共用此口径，避免「用无约束 max(mu) 当上界、再用有约束上限校验」的自相矛盾。
    """
    remaining = 1.0 - len(mu) * constraints.min_weight
    extra = np.zeros_like(mu)
    room = np.full_like(mu, max(0.0, constraints.max_weight - constraints.min_weight))
    for index in np.argsort(-mu):
        allocation = min(remaining, room[index])
        extra[index] = allocation
        remaining -= allocation
        if remaining <= 1e-12:
            break
    return float(np.dot(mu, constraints.min_weight + extra))


def _solve(
    mu: np.ndarray,
    cov: np.ndarray,
    constraints: Constraints,
    objective: str,
    risk_free_rate: float,
    target: float | None,
) -> OptimizationResult:
    """统一的 SLSQP 求解入口。"""
    n_assets = len(mu)
    x0 = np.full(n_assets, 1.0 / n_assets)
    bounds = constraints.bounds(n_assets)

    # 夏普比率在「超额收益全非正」或「组合无波动」时数学上无定义。
    # 若放任分母钳位到 sqrt(1e-12)，会得到 1000 量级的假夏普且 success=True。
    if objective == "max_sharpe":
        equal_variance = max(float(x0 @ cov @ x0), 0.0)
        if np.all(mu - risk_free_rate <= 0.0) or equal_variance <= 1e-18:
            return OptimizationResult(
                weights=x0.copy(),
                expected_return=float(x0 @ mu),
                volatility=float(np.sqrt(equal_variance)),
                objective_value=float("nan"),
                success=False,
                message="超额收益全非正或收益率无波动，最大夏普比率无定义",
            )

    scipy_constraints: list[dict[str, object]] = [
        {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0), "jac": lambda w: np.ones(n_assets)}
    ]
    if objective == "target_return":
        if target is None:
            raise ValueError("target_return 目标必须提供 target 参数")
        scipy_constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: float(w @ mu - target),
                "jac": lambda _: mu,
            }
        )

    def variance(w: np.ndarray) -> float:
        return float(w @ cov @ w)

    def variance_jac(w: np.ndarray) -> np.ndarray:
        return 2.0 * cov @ w

    if objective == "max_sharpe":

        def loss(w: np.ndarray) -> float:
            variance_value = float(w @ cov @ w)
            vol = np.sqrt(max(variance_value, 1e-12))
            return -float((w @ mu - risk_free_rate) / vol)

        def loss_jac(w: np.ndarray) -> np.ndarray:
            variance_value = float(w @ cov @ w)
            vol = np.sqrt(max(variance_value, 1e-12))
            excess = float(w @ mu - risk_free_rate)
            # d/dw [-(excess/vol)] = -(mu/vol - excess * cov·w / vol^3)
            return -(mu / vol - excess * (cov @ w) / (vol**3))

        fun, jac = loss, loss_jac
    else:
        fun, jac = variance, variance_jac

    solution = minimize(
        fun,
        x0,
        jac=jac,
        method="SLSQP",
        bounds=bounds,
        constraints=scipy_constraints,
        options={"maxiter": 500, "ftol": 1e-12},
    )

    weights = np.asarray(solution.x, dtype=float)
    # 未收敛或含 NaN/Inf 时不能把垃圾解裁剪归一化后当成功结果返回。
    if not solution.success or not np.all(np.isfinite(weights)):
        return OptimizationResult(
            weights=x0.copy(),
            expected_return=float(x0 @ mu),
            volatility=float(np.sqrt(max(float(x0 @ cov @ x0), 0.0))),
            objective_value=float("nan"),
            success=False,
            message=f"优化未收敛: {solution.message}",
        )
    weights = np.clip(weights, constraints.min_weight, constraints.max_weight)
    weights /= weights.sum()
    series_variance = max(float(weights @ cov @ weights), 0.0)
    volatility = float(np.sqrt(series_variance))

    if objective == "max_sharpe":
        if volatility <= 1e-12:
            objective_value = float("nan")
            success = False
            message = "最优组合波动率接近 0，夏普比率无定义"
        else:
            objective_value = float((weights @ mu - risk_free_rate) / volatility)
            success = bool(solution.success)
            message = solution.message or ""
    else:
        objective_value = series_variance
        success = bool(solution.success)
        message = solution.message or ""

    return OptimizationResult(
        weights=weights,
        expected_return=float(weights @ mu),
        volatility=volatility,
        objective_value=objective_value,
        success=success,
        message=message,
    )


def min_variance(returns: ReturnsLike, constraints: Constraints | None = None) -> OptimizationResult:
    """求全局最小方差组合。"""
    matrix = as_returns_matrix(returns)
    mu = expected_returns(matrix)
    cov = covariance(matrix)
    constraints = constraints or Constraints()
    constraints.validate(matrix.shape[1], mu)
    return _solve(mu, cov, constraints, "min_variance", 0.0, None)


def max_sharpe(
    returns: ReturnsLike,
    risk_free_rate: float = 0.0,
    constraints: Constraints | None = None,
) -> OptimizationResult:
    """求最大夏普比率组合。``risk_free_rate`` 为**单期**无风险利率。"""
    matrix = as_returns_matrix(returns)
    mu = expected_returns(matrix)
    cov = covariance(matrix)
    constraints = constraints or Constraints()
    constraints.validate(matrix.shape[1], mu)
    return _solve(mu, cov, constraints, "max_sharpe", risk_free_rate, None)


def target_return(
    returns: ReturnsLike,
    target: float,
    constraints: Constraints | None = None,
) -> OptimizationResult:
    """在 ``sum(w·mu) >= target`` 下求最小方差组合。``target`` 为**单期**收益。"""
    matrix = as_returns_matrix(returns)
    mu = expected_returns(matrix)
    cov = covariance(matrix)
    constraints = constraints or Constraints()
    constraints.validate(matrix.shape[1], mu)
    max_achievable = _max_achievable_return(mu, constraints)
    if target > max_achievable + 1e-12:
        raise ValueError(f"目标单期收益 {target:.6f} 超过约束下可达上限 {max_achievable:.6f}，不可达")
    return _solve(mu, cov, constraints, "target_return", 0.0, target)


def efficient_frontier(
    returns: ReturnsLike,
    n_points: int = 10,
    constraints: Constraints | None = None,
) -> list[OptimizationResult]:
    """扫描有效前沿：从全局最小方差收益到约束下最高可达收益之间等分取点。

    Args:
        returns: ``(T, N)`` 收益率矩阵。
        n_points: 前沿上的点数，至少 2。
        constraints: 权重约束。

    Returns:
        按预期收益升序排列的 :class:`OptimizationResult` 列表，每项为对应收益下的最小方差解。
    """
    if n_points < 2:
        raise ValueError("有效前沿至少需要 2 个点")
    matrix = as_returns_matrix(returns)
    mu = expected_returns(matrix)
    constraints = constraints or Constraints()
    constraints.validate(matrix.shape[1], mu)

    lower = float(min_variance(matrix, constraints).expected_return)
    upper = _max_achievable_return(mu, constraints)
    if upper <= lower + 1e-12:
        raise ValueError("约束下最高可达收益不超过最小方差组合收益，无法构造前沿")

    targets = np.linspace(lower, upper, n_points)
    return [target_return(matrix, float(t), constraints) for t in targets]


__all__ = ["efficient_frontier", "max_sharpe", "min_variance", "portfolio_returns", "target_return"]
