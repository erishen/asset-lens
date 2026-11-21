"""模型预测控制（MPC）式的滚动组合再平衡。

与一次性 Markowitz 不同，MPC 把优化放进**滚动时域**：每个再平衡日只用截至当日的
历史窗口重新求解目标权重，加上换手成本惩罚后执行一步，窗口前移后重复。
这样把「预测—优化—执行」闭环化，也能显式控制交易摩擦。

核心类 :class:`MPCController`，返回 :class:`MPCResult`（逐期目标权重、实际净值曲线、换手率）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .base import (
    Constraints,
    ReturnsLike,
    as_returns_matrix,
)
from .markowitz import max_sharpe, min_variance


@dataclass(frozen=True)
class MPCStep:
    """单个再平衡时点的决策记录。"""

    step: int
    target_weights: np.ndarray
    turnover: float  # 双边换手额 Σ|Δw|
    cost: float
    portfolio_return: float


@dataclass(frozen=True)
class MPCResult:
    """MPC 回测/滚动结果。"""

    steps: list[MPCStep] = field(default_factory=list)
    wealth: np.ndarray = field(default_factory=lambda: np.array([1.0]))
    asset_names: list[str] | None = None

    @property
    def total_turnover(self) -> float:
        """累计双边换手额（Σ|Δw|，权重和为 1 时一次全换计 2）。"""
        return float(sum(step.turnover for step in self.steps))

    @property
    def total_cost(self) -> float:
        """累计交易成本。"""
        return float(sum(step.cost for step in self.steps))

    @property
    def final_wealth(self) -> float:
        """期末净值（已扣交易成本）。"""
        return float(self.wealth[-1])

    def weights_history(self) -> np.ndarray:
        """``(n_steps, n_assets)`` 的目标权重矩阵。"""
        if not self.steps:
            return np.empty((0, 0))
        return np.stack([step.target_weights for step in self.steps])

    def as_dict(self) -> dict[str, object]:
        """转成可 JSON 序列化的摘要。"""
        return {
            "n_steps": len(self.steps),
            "final_wealth": self.final_wealth,
            "total_turnover": self.total_turnover,
            "total_cost": self.total_cost,
            "max_drawdown": self.max_drawdown(),
        }

    def max_drawdown(self) -> float:
        """净值曲线的最大回撤（正数=损失幅度）。"""
        if self.wealth.size < 2:
            return 0.0
        running_max = np.maximum.accumulate(self.wealth)
        drawdowns = 1.0 - self.wealth / np.maximum(running_max, 1e-12)
        return float(np.max(drawdowns))

    def format_text(self) -> str:
        """人读的多行摘要。"""
        return "\n".join(
            [
                f"MPC 滚动再平衡: {len(self.steps)} 次决策",
                f"期末净值:   {self.final_wealth:.4f}",
                f"最大回撤:   {self.max_drawdown():.2%}",
                f"累计双边换手: {self.total_turnover:.2%}",
                f"累计成本:   {self.total_cost:.4f}",
            ]
        )


class MPCController:
    """滚动时域组合控制器。

    Args:
        lookback: 每次优化使用的历史窗口长度。
        rebalance_every: 每隔多少期再平衡一次（其间沿用上次权重）。
        transaction_cost: 成本率，按双边换手额 Σ|Δw| 计费；0.001 表示每单位双边换手额收 0.1%。
        objective: ``"min_variance"`` 或 ``"max_sharpe"``。
        risk_free_rate: ``max_sharpe`` 目标下的单期无风险利率。
        constraints: 权重约束。
    """

    def __init__(
        self,
        lookback: int = 60,
        rebalance_every: int = 5,
        transaction_cost: float = 0.001,
        objective: str = "min_variance",
        risk_free_rate: float = 0.0,
        constraints: Constraints | None = None,
    ) -> None:
        if lookback < 2:
            raise ValueError("lookback 至少为 2")
        if rebalance_every < 1:
            raise ValueError("rebalance_every 必须为正整数")
        if transaction_cost < 0:
            raise ValueError("transaction_cost 不能为负")
        if objective not in ("min_variance", "max_sharpe"):
            raise ValueError(f"未知 objective={objective!r}，可选: min_variance / max_sharpe")
        self.lookback = lookback
        self.rebalance_every = rebalance_every
        self.transaction_cost = transaction_cost
        self.objective = objective
        self.risk_free_rate = risk_free_rate
        self.constraints = constraints or Constraints()

    def _solve(self, window: np.ndarray) -> np.ndarray:
        """在给定窗口上求目标权重。"""
        if self.objective == "max_sharpe":
            return max_sharpe(window, self.risk_free_rate, self.constraints).weights
        return min_variance(window, self.constraints).weights

    def run(self, returns: ReturnsLike) -> MPCResult:
        """在收益率序列上滚动执行 MPC。

        Args:
            returns: ``(T, N)`` 收益率矩阵，时间从早到晚。

        Returns:
            :class:`MPCResult`；若样本不足一个 lookback，返回只含起始净值的空结果。
        """
        matrix = as_returns_matrix(returns)
        n_periods, n_assets = matrix.shape
        if n_periods <= self.lookback:
            return MPCResult(wealth=np.array([1.0]))

        from .base import infer_names

        names = infer_names(returns)

        current_weights = np.full(n_assets, 1.0 / n_assets)
        wealth = [1.0]
        steps: list[MPCStep] = []

        for t in range(self.lookback, n_periods):
            if (t - self.lookback) % self.rebalance_every == 0:
                target = self._solve(matrix[t - self.lookback : t])
                # Σ|Δw| 是双边换手额（如全仓 A→B 记 2），成本按此计费，口径与 total_turnover 一致
                turnover = float(np.sum(np.abs(target - current_weights)))
                cost = turnover * self.transaction_cost
                current_weights = target
            else:
                turnover, cost = 0.0, 0.0

            period_return = float(matrix[t] @ current_weights) - cost
            wealth.append(wealth[-1] * (1.0 + period_return))
            steps.append(MPCStep(t, current_weights.copy(), turnover, cost, period_return))

        return MPCResult(steps=steps, wealth=np.array(wealth), asset_names=names)


def rolling_rebalance(
    returns: ReturnsLike,
    lookback: int = 60,
    rebalance_every: int = 5,
    transaction_cost: float = 0.001,
    objective: str = "min_variance",
    constraints: Constraints | None = None,
) -> MPCResult:
    """函数式快捷入口，等价于 ``MPCController(...).run(returns)``。"""
    controller = MPCController(
        lookback=lookback,
        rebalance_every=rebalance_every,
        transaction_cost=transaction_cost,
        objective=objective,
        constraints=constraints,
    )
    return controller.run(returns)


__all__ = ["MPCController", "MPCResult", "MPCStep", "rolling_rebalance"]
