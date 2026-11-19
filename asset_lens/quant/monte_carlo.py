"""蒙特卡洛模拟：相关路径生成与组合终值分布。

两种路径来源：

* :func:`gbm_paths` — 几何布朗运动（均值/协方差驱动），适合做前瞻情景。
* :func:`bootstrap_paths` — 对历史收益率按块重采样，保留厚尾与相关性，不依赖正态分布假设。

所有随机源都用 ``np.random.default_rng(seed)``，同一 seed 结果完全可复现。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .base import (
    TRADING_DAYS,
    ReturnsLike,
    as_returns_matrix,
    covariance,
    expected_returns,
)


@dataclass(frozen=True)
class SimulationSummary:
    """终值分布的统计量（终值以 1.0 为起始本金）。"""

    mean: float
    median: float
    p05: float
    p95: float
    var: float
    cvar: float
    prob_loss: float
    horizon: int
    n_paths: int

    def as_dict(self) -> dict[str, float | int]:
        """转成可 JSON 序列化的字典。"""
        return {
            "mean_terminal": float(self.mean),
            "median_terminal": float(self.median),
            "p05": float(self.p05),
            "p95": float(self.p95),
            "var": float(self.var),
            "cvar": float(self.cvar),
            "prob_loss": float(self.prob_loss),
            "horizon": int(self.horizon),
            "n_paths": int(self.n_paths),
        }

    def format_text(self) -> str:
        """人读的多行摘要。"""
        return "\n".join(
            [
                f"蒙特卡洛路径: {self.n_paths} 条 × {self.horizon} 期",
                f"终值均值:   {self.mean:.4f}",
                f"终值中位数: {self.median:.4f}",
                f"5% 分位:    {self.p05:.4f}",
                f"95% 分位:   {self.p95:.4f}",
                f"VaR(95%):   {self.var:.4f}",
                f"CVaR(95%):  {self.cvar:.4f}",
                f"亏损概率:   {self.prob_loss:.2%}",
            ]
        )


def simulate_paths(
    paths: np.ndarray,
    level: float = 0.95,
) -> SimulationSummary:
    """从路径矩阵汇总终值分布。

    Args:
        paths: shape ``(n_steps, n_paths)``，每条路径从 1.0 起步（累计净值）。
        level: 置信水平，用于 VaR / CVaR。

    Returns:
        :class:`SimulationSummary`。
    """
    if not 0.0 < level < 1.0:
        raise ValueError(f"置信水平必须落在 (0, 1)，实际为 {level}")
    paths = np.asarray(paths, dtype=float)
    if paths.ndim != 2:
        raise ValueError(
            f"simulate_paths 只接受 (n_steps, n_paths) 的 2D 净值路径，实际 ndim={paths.ndim}；"
            "多资产路径请先用 portfolio_paths 合成"
        )
    terminal = paths[-1]
    var_cutoff = float(np.quantile(terminal, 1.0 - level))
    tail = terminal[terminal <= var_cutoff]
    tail_mean = float(tail.mean()) if tail.size else var_cutoff
    return SimulationSummary(
        mean=float(terminal.mean()),
        median=float(np.median(terminal)),
        p05=float(np.quantile(terminal, 0.05)),
        p95=float(np.quantile(terminal, 0.95)),
        var=max(0.0, 1.0 - var_cutoff),
        cvar=max(0.0, 1.0 - tail_mean),
        prob_loss=float(np.mean(terminal < 1.0)),
        horizon=int(paths.shape[0] - 1),
        n_paths=int(paths.shape[1]),
    )


def gbm_paths(
    returns: ReturnsLike,
    horizon: int = TRADING_DAYS,
    n_paths: int = 1000,
    seed: int | None = 42,
    periods_per_year: int = TRADING_DAYS,
) -> np.ndarray:
    """用历史均值/协方差驱动的多资产几何布朗运动路径。

    Returns:
        shape ``(horizon + 1, n_paths, n_assets)`` 的累计净值路径（起点 1.0）。
    """
    if horizon < 1 or n_paths < 1:
        raise ValueError("horizon 与 n_paths 必须为正整数")
    if periods_per_year < 1:
        raise ValueError("periods_per_year 必须 >= 1")
    matrix = as_returns_matrix(returns)
    mu = expected_returns(matrix) * periods_per_year
    cov = covariance(matrix) * periods_per_year

    n_assets = matrix.shape[1]
    # ridge 必须随协方差尺度缩放：固定 1e-12 在收益缩到 1e-6 量级时会反客为主、抹掉相关性。
    avg_var = float(np.trace(cov)) / n_assets
    ridge = 1e-12 * avg_var if avg_var > 0.0 else 1e-12
    min_eig = float(np.linalg.eigvalsh(cov).min())
    if min_eig <= 0.0:  # 样本不足/共线导致半负定时，抬到刚好正定
        ridge = max(ridge, -min_eig + ridge)
    chol = np.linalg.cholesky(cov + np.eye(n_assets) * ridge)
    dt = 1.0 / periods_per_year
    rng = np.random.default_rng(seed)
    shocks = rng.standard_normal((horizon, n_paths, n_assets)) @ chol.T
    # mu/cov 已年化：漂移项乘 dt，扩散项乘 sqrt(dt)，不能重复缩放。
    drift = (mu - 0.5 * np.diag(cov)) * dt
    log_returns = drift + shocks * np.sqrt(dt)

    paths = np.empty((horizon + 1, n_paths, n_assets), dtype=float)
    paths[0] = 1.0
    paths[1:] = np.exp(np.cumsum(log_returns, axis=0))
    return paths


def bootstrap_paths(
    returns: ReturnsLike,
    horizon: int = TRADING_DAYS,
    n_paths: int = 1000,
    block_size: int = 5,
    seed: int | None = 42,
) -> np.ndarray:
    """按块重采样历史收益率（保留短期相关与厚尾），生成多资产路径。

    Returns:
        shape ``(horizon + 1, n_paths, n_assets)`` 的累计净值路径（起点 1.0）。
    """
    if horizon < 1 or n_paths < 1 or block_size < 1:
        raise ValueError("horizon、n_paths、block_size 必须为正整数")
    matrix = as_returns_matrix(returns)
    n_periods, n_assets = matrix.shape
    if block_size > n_periods:
        raise ValueError(f"block_size={block_size} 不能超过历史样本数 {n_periods}")

    rng = np.random.default_rng(seed)
    sampled = np.empty((horizon, n_paths, n_assets), dtype=float)
    n_blocks = int(np.ceil(horizon / block_size))
    for block in range(n_blocks):
        starts = rng.integers(0, n_periods - block_size + 1, size=n_paths)
        # fancy-index 一次性取出全部块，避免 n_paths 次 Python 切片与栈叠。
        chunk = matrix[starts[:, None] + np.arange(block_size)]  # (n_paths, block, N)
        take = min(block_size, horizon - block * block_size)
        sampled[block * block_size : block * block_size + take] = chunk[:, :take, :].transpose(1, 0, 2)

    paths = np.empty((horizon + 1, n_paths, n_assets), dtype=float)
    paths[0] = 1.0
    paths[1:] = np.cumprod(1.0 + sampled, axis=0)
    return paths


def portfolio_paths(paths: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """把多资产路径按权重合成为组合净值路径。

    Args:
        paths: ``(n_steps, n_paths, n_assets)``。
        weights: 长度 ``n_assets`` 的权重，不要求和为 1（内部归一化）。

    Returns:
        shape ``(n_steps, n_paths)`` 的组合净值路径。
    """
    array = np.asarray(weights, dtype=float).reshape(-1)
    if array.shape[0] != paths.shape[2]:
        raise ValueError(f"权重长度 {array.shape[0]} 与资产数 {paths.shape[2]} 不一致")
    if not np.all(np.isfinite(array)):
        raise ValueError("权重含 NaN 或 Inf")
    total = float(array.sum())
    if abs(total) <= 1e-12:
        raise ValueError(f"权重之和为 {total:.6g}，无法归一化；请避免多空权重恰好抵消")
    array = array / total
    return paths @ array


def simulate(
    returns: ReturnsLike,
    weights: np.ndarray,
    method: str = "bootstrap",
    horizon: int = TRADING_DAYS,
    n_paths: int = 1000,
    seed: int | None = 42,
    level: float = 0.95,
    **kwargs: object,
) -> SimulationSummary:
    """一步到位的组合蒙特卡洛：生成路径 → 合成组合 → 汇总分布。

    Args:
        returns: ``(T, N)`` 历史收益率矩阵。
        weights: 组合权重。
        method: ``"bootstrap"`` 或 ``"gbm"``。
        horizon: 模拟期数。
        n_paths: 路径条数。
        seed: 随机种子，``None`` 表示不固定。
        level: VaR / CVaR 置信水平。
        **kwargs: 透传给路径生成器：``bootstrap`` 接受 ``block_size``，``gbm`` 接受
            ``periods_per_year``；传入不属于当前方法的参数会抛 ValueError。
    """
    generators = {
        "bootstrap": bootstrap_paths,
        "gbm": gbm_paths,
    }
    if method not in generators:
        raise ValueError(f"未知 method={method!r}，可选: {sorted(generators)}")
    allowed = {"bootstrap": {"block_size"}, "gbm": {"periods_per_year"}}
    unexpected = set(kwargs) - allowed[method]
    if unexpected:
        raise ValueError(f"method={method!r} 不接受参数 {sorted(unexpected)}；可用: {sorted(allowed[method])}")
    paths = generators[method](returns, horizon=horizon, n_paths=n_paths, seed=seed, **kwargs)
    combined = portfolio_paths(paths, weights)
    return simulate_paths(combined, level)


__all__ = ["SimulationSummary", "bootstrap_paths", "gbm_paths", "portfolio_paths", "simulate", "simulate_paths"]
