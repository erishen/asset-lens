"""量化分析子包：CVaR / Markowitz / Monte Carlo / MPC。

设计原则：

* 只依赖 numpy / scipy / pandas，不引入 cvxpy 等新依赖。
* 纯计算、无 I/O（CSV 读取是 CLI 的入口函数，不在核心算法层）。
* 风险数值统一为「正数=损失」；收益率/权重统一为单期值。

快速上手::

    from asset_lens.quant import historical_cvar, min_variance, simulate, rolling_rebalance

    cvar = historical_cvar(returns[:, 0], level=0.95)
    portfolio = min_variance(returns)
    projection = simulate(returns, portfolio.weights, method="bootstrap", seed=42)
    mpc = rolling_rebalance(returns, lookback=60, rebalance_every=5)
"""

from .base import (
    TRADING_DAYS,
    Constraints,
    OptimizationResult,
    annualize_return,
    annualize_vol,
    as_returns_matrix,
    covariance,
    expected_returns,
    infer_names,
    load_returns_csv,
    portfolio_returns,
)
from .cvar import (
    historical_cvar,
    historical_var,
    minimize_cvar,
    parametric_cvar,
    portfolio_cvar,
)
from .markowitz import efficient_frontier, max_sharpe, min_variance, target_return
from .monte_carlo import (
    SimulationSummary,
    bootstrap_paths,
    gbm_paths,
    portfolio_paths,
    simulate,
    simulate_paths,
)
from .mpc import MPCController, MPCResult, MPCStep, rolling_rebalance

__all__ = [
    "TRADING_DAYS",
    "Constraints",
    "MPCController",
    "MPCResult",
    "MPCStep",
    "OptimizationResult",
    "SimulationSummary",
    "annualize_return",
    "annualize_vol",
    "as_returns_matrix",
    "bootstrap_paths",
    "covariance",
    "efficient_frontier",
    "expected_returns",
    "gbm_paths",
    "historical_cvar",
    "historical_var",
    "infer_names",
    "load_returns_csv",
    "max_sharpe",
    "min_variance",
    "minimize_cvar",
    "parametric_cvar",
    "portfolio_cvar",
    "portfolio_paths",
    "portfolio_returns",
    "rolling_rebalance",
    "simulate",
    "simulate_paths",
    "target_return",
]
