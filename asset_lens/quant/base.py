"""量化模块公共类型与工具。

统一约定（后续四个子模块全部遵守）：

* 收益率矩阵 shape = ``(T, N)``：``T`` 个时间样本、``N`` 个资产；单资产为 ``(T, 1)``。
* 风险度量（VaR / CVaR）一律返回**正数表示损失幅度**：``cvar=0.03`` 表示尾部平均亏损 3%。
* 权重向量长度 ``N``，默认要求 ``sum(weights) == 1`` 且分量落在 ``[0, 1]``（只做多）。
* 期望收益与波动率默认都是**单期**值；年化请用 :func:`annualize_return` / :func:`annualize_vol`。

与项目内另外两处 CVaR 实现的关系（共三套口径，**数值不可直接混用**）：

* ``core.advanced_analysis.RiskAnalysis.calculate_cvar``：返回**负的**尾部收益均值（小数）。
* ``core.portfolio_analytics._calculate_expected_shortfall``：返回 ``abs(...) * 100``，即**正数百分数**，
  且尾部用 ``sorted[:index+1]`` 多取一个样本。
* 本模块：返回**正数小数**（损失幅度），采用与 Rockafellar-Uryasev LP 一致的加权历史 ES。

换算时除符号/量纲外，还要注意尾部样本口径差异。旧接口保留不动以免回归，
但新代码建议统一走本模块，避免 100 倍量级误用。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

TRADING_DAYS = 252

ReturnsLike = np.ndarray | pd.DataFrame | pd.Series | list[float] | list[list[float]]


def as_returns_matrix(returns: ReturnsLike) -> np.ndarray:
    """把各种收益率输入统一成 ``(T, N)`` 的 float 矩阵。

    Args:
        returns: DataFrame（列=资产）、Series（单资产）、ndarray 或嵌套 list。

    Returns:
        shape ``(T, N)`` 的矩阵。

    Raises:
        ValueError: 空输入、维度不是 1/2、或含 NaN/Inf。
    """
    if isinstance(returns, pd.DataFrame):
        matrix = returns.to_numpy(dtype=float)
    elif isinstance(returns, pd.Series):
        matrix = returns.to_numpy(dtype=float).reshape(-1, 1)
    else:
        matrix = np.asarray(returns, dtype=float)
        if matrix.ndim == 1:
            matrix = matrix.reshape(-1, 1)

    if matrix.ndim != 2:
        raise ValueError(f"收益率必须是 1D 或 2D，实际 ndim={matrix.ndim}")
    if matrix.size == 0:
        raise ValueError("收益率不能为空")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("收益率含 NaN 或 Inf，请先清洗")
    return matrix


def infer_names(returns: ReturnsLike) -> list[str] | None:
    """尽量从输入推断资产名；无法推断时返回 ``None``。"""
    if isinstance(returns, pd.DataFrame):
        return [str(column) for column in returns.columns]
    if isinstance(returns, pd.Series) and returns.name is not None:
        return [str(returns.name)]
    return None


def load_returns_csv(path: str | Path) -> pd.DataFrame:
    """读取收益率 CSV：首列为日期索引，其余列为各资产的单期收益率。

    这是 CLI 与测试共用的输入格式，例如::

        date,股票,债券,黄金
        2026-01-02,0.012,0.0003,-0.004
        2026-01-03,-0.008,0.0002,0.005
    """
    frame = pd.read_csv(path, index_col=0)
    if frame.empty:
        raise ValueError(f"收益率文件为空: {path}")
    frame.index = pd.to_datetime(frame.index)
    return frame.apply(pd.to_numeric, errors="raise")


def expected_returns(returns: np.ndarray) -> np.ndarray:
    """各资产的样本平均单期收益。"""
    return returns.mean(axis=0)


def covariance(returns: np.ndarray) -> np.ndarray:
    """样本协方差矩阵；自动处理单资产退化的标量情况。"""
    if returns.shape[0] < 2:
        raise ValueError("协方差至少需要 2 个时间样本")
    return np.atleast_2d(np.cov(returns, rowvar=False, ddof=1))


def portfolio_returns(returns: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """按权重合成组合的单期收益序列。"""
    weights_array = np.asarray(weights, dtype=float)
    if weights_array.shape[-1] != returns.shape[1]:
        raise ValueError(f"权重长度 {weights_array.shape[-1]} 与资产数 {returns.shape[1]} 不一致")
    return returns @ weights_array


def annualize_return(periodic: float, periods_per_year: int = TRADING_DAYS) -> float:
    """单期收益线性年化（算术口径，用于期望收益）。"""
    return float(periodic) * periods_per_year


def annualize_vol(periodic: float, periods_per_year: int = TRADING_DAYS) -> float:
    """单期波动率按平方根法则年化。"""
    return float(periodic) * np.sqrt(periods_per_year)


@dataclass(frozen=True)
class Constraints:
    """优化问题的通用约束（收益阈值用**单期**值）。"""

    min_weight: float = 0.0
    max_weight: float = 1.0
    min_return: float | None = None

    def bounds(self, n_assets: int) -> list[tuple[float, float]]:
        """生成 scipy 使用的权重边界。"""
        return [(self.min_weight, self.max_weight)] * n_assets

    def validate(self, n_assets: int, mu: np.ndarray) -> None:
        """在求解前做可行性预检，尽早给出人话错误。"""
        if not 0.0 <= self.min_weight <= self.max_weight:
            raise ValueError("权重下界必须 >= 0 且不超过上界")
        if n_assets * self.min_weight > 1.0 or n_assets * self.max_weight < 1.0:
            raise ValueError(f"权重边界 [{self.min_weight}, {self.max_weight}] 在 {n_assets} 个资产上无法满足 sum=1")
        if self.min_return is not None and self.min_return > float(np.max(mu)):
            raise ValueError(f"目标单期收益 {self.min_return:.6f} 超过最高资产收益 {float(np.max(mu)):.6f}，不可达")


@dataclass(frozen=True)
class OptimizationResult:
    """一次组合优化的结果。

    ``objective_value`` 的含义随目标而变：最小方差=方差、最大夏普=夏普比率、最小 CVaR=CVaR 损失。
    """

    weights: np.ndarray
    expected_return: float
    volatility: float
    objective_value: float
    success: bool = True
    message: str = ""

    def as_dict(self, names: list[str] | None = None) -> dict[str, Any]:
        """转成可 JSON 序列化的字典。"""
        keys = names or [f"asset_{i}" for i in range(len(self.weights))]
        # JSON（RFC 8259）不接受 NaN/Inf；优化无定义时用 NaN 表示，序列化必须转成 null，
        # 否则 starlette JSONResponse 在路由 try/except 之外抛 ValueError 直接 500。
        objective: float | None = float(self.objective_value)
        if not math.isfinite(objective):
            objective = None
        return {
            "weights": {name: float(weight) for name, weight in zip(keys, self.weights, strict=True)},
            "expected_return": float(self.expected_return),
            "volatility": float(self.volatility),
            "objective_value": objective,
            "success": bool(self.success),
            "message": self.message,
        }

    def format_text(self, names: list[str] | None = None) -> str:
        """人读的多行摘要。"""
        data = self.as_dict(names)
        lines = [f"优化成功: {self.success}", f"目标值: {self.objective_value:.6f}", "权重:"]
        lines.extend(f"  {name}: {weight:.2%}" for name, weight in data["weights"].items())
        lines.append(f"预期单期收益: {self.expected_return:.4%}")
        lines.append(f"单期波动率:   {self.volatility:.4%}")
        if self.message:
            lines.append(f"提示: {self.message}")
        return "\n".join(lines)


def _normalize_weights(weights: np.ndarray, n_assets: int) -> np.ndarray:
    """校验并归一化权重，保证和为 1。"""
    array = np.asarray(weights, dtype=float).reshape(-1)
    if array.shape[0] != n_assets:
        raise ValueError(f"权重长度 {array.shape[0]} 与资产数 {n_assets} 不一致")
    total = float(array.sum())
    if not np.isclose(total, 1.0):
        raise ValueError(f"权重之和必须为 1，实际为 {total:.6f}")
    return array
