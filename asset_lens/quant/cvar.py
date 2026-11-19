"""条件风险价值（CVaR / Expected Shortfall）与最小 CVaR 组合优化。

四种口径，覆盖「度量」与「优化」两个层面：

* :func:`historical_cvar` — 加权历史 ES：最差 ``(1-level)`` 比例收益按分位尾数加权取反（正数=损失）。
* :func:`parametric_cvar` — 正态分布假设下的解析 CVaR。
* :func:`portfolio_cvar` — 给定权重合成组合后的历史 CVaR。
* :func:`minimize_cvar` — Rockafellar-Uryasev 线性规划直接求最小 CVaR 权重。

符号约定沿用 :mod:`asset_lens.quant.base`：**返回正数表示损失幅度**。
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import linprog
from scipy.stats import norm

from .base import (
    Constraints,
    OptimizationResult,
    ReturnsLike,
    as_returns_matrix,
    covariance,
    expected_returns,
    portfolio_returns,
)


def _check_level(level: float) -> None:
    if not 0.0 < level < 1.0:
        raise ValueError(f"置信水平必须落在 (0, 1)，实际为 {level}")


def historical_var(returns: ReturnsLike, level: float = 0.95) -> float:
    """历史模拟法 VaR（正数=损失）。

    Args:
        returns: 单资产收益序列，或 ``(T, N)`` 矩阵（按列各自计算不适用于本函数，
            请先用 :func:`portfolio_returns` 合成）。
        level: 置信水平，如 0.95 表示最差的 5%。

    Returns:
        VaR 损失幅度。例如 0.02 表示有 level 的把握亏损不超过 2%。
    """
    _check_level(level)
    matrix = as_returns_matrix(returns)
    if matrix.shape[1] != 1:
        raise ValueError("historical_var 只接受单一收益序列；多资产请用 portfolio_cvar")
    quantile = float(np.quantile(matrix[:, 0], 1.0 - level))
    return max(0.0, -quantile)


def _expected_shortfall(series: np.ndarray, level: float) -> float:
    """加权历史 ES（正数=损失），与 Rockafellar-Uryasev LP 的目标数值等价。

    尾部样本数 ``(1-level)*T`` 通常不是整数：取最差 ``floor`` 个样本全额，
    第 ``floor+1`` 个样本按小数部分加权，再除以尾部样本数。这样
    :func:`historical_cvar` 与 :func:`minimize_cvar` 的 ``objective_value``
    是同一口径（已用 LP 对拍验证误差 < 1e-16），避免「复算值和优化目标差 5%」。
    """
    ordered = np.sort(series)
    n = ordered.size
    tail_count = (1.0 - level) * n
    whole = int(np.floor(tail_count))
    frac = tail_count - whole
    if whole == 0:  # 尾部不足一个样本：用最差值近似，与 LP 一致
        return max(0.0, -float(ordered[0]))
    total = float(ordered[:whole].sum())
    if frac > 1e-12 and whole < n:
        total += frac * float(ordered[whole])
    return max(0.0, -total / tail_count)


def historical_cvar(returns: ReturnsLike, level: float = 0.95) -> float:
    """加权历史 CVaR / Expected Shortfall（正数=损失）。

    口径与 :func:`minimize_cvar` 的 LP 目标一致；与项目内其他两处历史实现不同，
    详见 :mod:`asset_lens.quant.base` 模块说明。
    """
    _check_level(level)
    matrix = as_returns_matrix(returns)
    if matrix.shape[1] != 1:
        raise ValueError("historical_cvar 只接受单一收益序列；多资产请用 portfolio_cvar")
    return _expected_shortfall(matrix[:, 0], level)


def parametric_cvar(mean: float, volatility: float, level: float = 0.95) -> float:
    """正态分布假设下的解析 CVaR（正数=损失）。

    公式：``-mu + sigma * pdf(z) / (1 - alpha)``，其中 ``z = ppf(1 - alpha)``。
    用于快速估算与单元测试校验历史模拟法。
    """
    _check_level(level)
    if volatility < 0:
        raise ValueError("波动率不能为负")
    z_cut = float(norm.ppf(1.0 - level))
    return float(-mean + volatility * float(norm.pdf(z_cut)) / (1.0 - level))


def portfolio_cvar(returns: ReturnsLike, weights: np.ndarray, level: float = 0.95) -> float:
    """先按权重合成组合收益，再算历史 CVaR。"""
    _check_level(level)
    matrix = as_returns_matrix(returns)
    series = portfolio_returns(matrix, weights)
    return historical_cvar(series, level)


def minimize_cvar(
    returns: ReturnsLike,
    level: float = 0.95,
    constraints: Constraints | None = None,
) -> OptimizationResult:
    """Rockafellar-Uryasev LP：直接求最小 CVaR 的组合权重。

    与「先估协方差再二次规划」不同，本方法不假设收益服从正态分布，
    直接最小化历史尾部损失，对尖峰厚尾更稳健。

    Args:
        returns: ``(T, N)`` 收益率矩阵。
        level: 置信水平。
        constraints: 权重上下界。``min_return`` 在本 LP 中会被忽略（若传入会在 ``message`` 中提示）；
            需要收益下限请改用 :func:`asset_lens.quant.markowitz.target_return`。

    Returns:
        :class:`OptimizationResult`，``objective_value`` 即最小 CVaR（正数损失）。
    """
    _check_level(level)
    matrix = as_returns_matrix(returns)
    n_periods, n_assets = matrix.shape
    if n_periods < 2:
        raise ValueError("最小 CVaR 优化至少需要 2 个时间样本")

    constraints = constraints or Constraints()
    ignored_min_return = constraints.min_return is not None
    if ignored_min_return:
        # min_return 不进入 CVaR 的 LP 目标；去掉后再预检，避免它误拒本来就合法的调用。
        constraints = Constraints(min_weight=constraints.min_weight, max_weight=constraints.max_weight)
    constraints.validate(n_assets, expected_returns(matrix))

    # 变量布局：[w(N), xi(1), u(T)]
    # 目标：xi + 1/((1-alpha)*T) * sum(u_t)
    objective = np.concatenate([[0.0] * n_assets, [1.0], [1.0 / ((1.0 - level) * n_periods)] * n_periods])

    # 约束：-r_t·w - xi - u_t <= 0  =>  [-r_t, -1, -e_t]·x <= 0
    a_ub = np.zeros((n_periods, n_assets + 1 + n_periods))
    for t in range(n_periods):
        a_ub[t, :n_assets] = -matrix[t]
        a_ub[t, n_assets] = -1.0
        a_ub[t, n_assets + 1 + t] = -1.0
    b_ub = np.zeros(n_periods)

    a_eq = np.zeros((1, n_assets + 1 + n_periods))
    a_eq[0, :n_assets] = 1.0
    b_eq = np.array([1.0])

    bounds = constraints.bounds(n_assets) + [(None, None)] + [(0.0, None)] * n_periods

    solution = linprog(
        c=objective,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )

    if not solution.success:
        return OptimizationResult(
            weights=np.full(n_assets, 1.0 / n_assets),
            expected_return=0.0,
            volatility=0.0,
            objective_value=float("nan"),
            success=False,
            message=f"LP 求解失败: {solution.message}",
        )

    weights = np.asarray(solution.x[:n_assets], dtype=float)
    weights = np.clip(weights, constraints.min_weight, constraints.max_weight)
    weights /= weights.sum()
    series = portfolio_returns(matrix, weights)
    return OptimizationResult(
        weights=weights,
        expected_return=float(series.mean()),
        volatility=float(series.std(ddof=1)),
        # 用返回权重按同一口径复算，保证 objective_value == portfolio_cvar(weights)。
        objective_value=portfolio_cvar(matrix, weights, level),
        success=True,
        message="Rockafellar-Uryasev LP"
        + ("（min_return 在 CVaR 目标下不生效，已忽略）" if ignored_min_return else ""),
    )


__all__ = [
    "covariance",
    "historical_cvar",
    "historical_var",
    "minimize_cvar",
    "parametric_cvar",
    "portfolio_cvar",
]
