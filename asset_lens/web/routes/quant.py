"""量化分析 API：CVaR / Markowitz / Monte Carlo / MPC。

数据由 asset_lens.data.quant_returns 从腾讯行情（qfq 日线）实时构造，
8 个资产类别代理的 (T, N) 日收益率矩阵，带 10 分钟进程内缓存。

端点均以「等权代理组合」为默认组合口径（除非端点自身求解最优权重），
响应 meta 里标注数据源、样本区间与组合口径，避免与真实持仓市值混淆。
"""

from __future__ import annotations

import asyncio
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, Query

from ...data.quant_returns import ASSET_PROXIES, load_returns
from ...quant import (
    bootstrap_paths,
    efficient_frontier,
    gbm_paths,
    historical_cvar,
    historical_var,
    max_sharpe,
    min_variance,
    minimize_cvar,
    portfolio_cvar,
    portfolio_paths,
    portfolio_returns,
    rolling_rebalance,
    simulate_paths,
)

router = APIRouter(prefix="/api/quant", tags=["quant"])


def _meta(dataset: Any, portfolio: str) -> dict[str, Any]:
    return {
        "source": dataset.source,
        "assets": dataset.names,
        "proxies": [{"name": name, "code": code} for name, code in ASSET_PROXIES],
        "start_date": dataset.start_date,
        "end_date": dataset.end_date,
        "periods": dataset.periods,
        "portfolio": portfolio,
    }


def _fail(exc: Exception) -> None:
    raise HTTPException(status_code=500, detail=f"量化分析失败: {exc!s}") from exc


@router.get("/cvar")
async def get_cvar(
    level: float = Query(0.95, ge=0.5, lt=1.0, description="置信水平"),
    count: int = Query(260, ge=60, le=1000, description="拉取交易日数"),
):
    """各资产与等权组合的 VaR / CVaR（正数=损失幅度，单期口径）。"""
    try:
        dataset = await load_returns(count)
        matrix = dataset.returns.to_numpy(dtype=float)
        equal_weights = np.full(len(dataset.names), 1.0 / len(dataset.names))
        assets = [
            {
                "name": name,
                "var": round(float(historical_var(matrix[:, i], level)), 6),
                "cvar": round(float(historical_cvar(matrix[:, i], level)), 6),
                "mean": round(float(np.mean(matrix[:, i])), 6),
                "volatility": round(float(np.std(matrix[:, i], ddof=1)), 6),
            }
            for i, name in enumerate(dataset.names)
        ]
        portfolio = {
            "name": "等权代理组合",
            "var": round(float(historical_var(portfolio_returns(matrix, equal_weights), level)), 6),
            "cvar": round(float(portfolio_cvar(matrix, equal_weights, level)), 6),
        }
        return {
            "level": level,
            "assets": assets,
            "portfolio": portfolio,
            "meta": _meta(dataset, "等权"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        _fail(exc)


@router.get("/optimize")
async def optimize_portfolio(
    objective: str = Query("min_variance", pattern="^(min_variance|max_sharpe|min_cvar|frontier)$"),
    level: float = Query(0.95, ge=0.5, lt=1.0),
    count: int = Query(260, ge=60, le=1000),
    n_points: int = Query(12, ge=2, le=30, description="有效前沿点数"),
):
    """Markowitz 组合优化：最小方差 / 最大夏普 / 最小 CVaR / 有效前沿。"""
    try:
        dataset = await load_returns(count)
        matrix = dataset.returns.to_numpy(dtype=float)

        def compute() -> dict[str, Any]:
            if objective == "min_variance":
                result = min_variance(matrix)
            elif objective == "max_sharpe":
                result = max_sharpe(matrix)
            elif objective == "min_cvar":
                result = minimize_cvar(matrix, level=level)
            else:
                frontier = efficient_frontier(matrix, n_points=n_points)
                return {
                    "objective": objective,
                    "result": None,
                    "frontier": [
                        {
                            **point.as_dict(dataset.names),
                            "cvar": round(float(portfolio_cvar(matrix, point.weights, level)), 6),
                        }
                        for point in frontier
                    ],
                }
            return {
                "objective": objective,
                "result": {
                    **result.as_dict(dataset.names),
                    "cvar": round(float(portfolio_cvar(matrix, result.weights, level)), 6),
                },
                "frontier": [],
            }

        payload = await asyncio.to_thread(compute)
        payload["level"] = level
        payload["meta"] = _meta(dataset, objective)
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        _fail(exc)


@router.get("/simulate")
async def simulate_portfolio(
    method: str = Query("bootstrap", pattern="^(bootstrap|gbm)$"),
    horizon: int = Query(252, ge=10, le=1000, description="模拟期数（交易日）"),
    n_paths: int = Query(1000, ge=100, le=5000, description="路径条数"),
    level: float = Query(0.95, ge=0.5, lt=1.0),
    count: int = Query(260, ge=60, le=1000),
):
    """蒙特卡洛：等权组合终值分布 + 分位数带 + 少量示例路径（供前端画图）。"""
    try:
        dataset = await load_returns(count)
        matrix = dataset.returns.to_numpy(dtype=float)
        equal_weights = np.full(len(dataset.names), 1.0 / len(dataset.names))

        def compute() -> dict[str, Any]:
            generator = bootstrap_paths if method == "bootstrap" else gbm_paths
            paths = generator(matrix, horizon=horizon, n_paths=n_paths, seed=42)
            # portfolio_paths: (steps, n_paths, n_assets) -> (steps, n_paths)
            combined = portfolio_paths(paths, equal_weights)
            summary = simulate_paths(combined, level)
            # ECharts category 轴按索引对齐 series，timeline / 分位线 / 示例路径
            # 必须用同一 stride 降采样，否则分位带只覆盖前面一小段且整体错位。
            stride = max(1, (horizon + 1) // 40)
            timeline = list(range(horizon + 1))[::stride]
            quantiles = {
                "p05": [round(float(v), 5) for v in np.percentile(combined, 5, axis=1)[::stride]],
                "p50": [round(float(v), 5) for v in np.percentile(combined, 50, axis=1)[::stride]],
                "p95": [round(float(v), 5) for v in np.percentile(combined, 95, axis=1)[::stride]],
            }
            samples = [
                [round(float(v), 5) for v in combined[::stride, i]]
                for i in range(6)
            ]
            return {
                "summary": summary.as_dict(),
                # timeline 已在上面按 stride 降采样，此处不可再切一次（否则步长变 stride²）
                "timeline": timeline,
                "quantiles": quantiles,
                "sample_paths": samples,
            }

        payload = await asyncio.to_thread(compute)
        payload["method"] = method
        payload["meta"] = _meta(dataset, "等权")
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        _fail(exc)


@router.get("/mpc")
async def mpc_backtest(
    lookback: int = Query(60, ge=20, le=200, description="滚动窗口期数"),
    rebalance_every: int = Query(5, ge=1, le=60, description="再平衡间隔期数"),
    transaction_cost: float = Query(0.001, ge=0.0, le=0.05, description="成本率（按双边换手额 Σ|Δw| 计费）"),
    count: int = Query(260, ge=60, le=1000),
):
    """MPC 滚动再平衡回测：净值曲线 + 换手/成本汇总 + 最近决策。"""
    try:
        dataset = await load_returns(count)
        matrix = dataset.returns.to_numpy(dtype=float)
        if matrix.shape[0] <= lookback:
            raise ValueError(f"样本 {matrix.shape[0]} 期不足以支撑 {lookback} 期滚动窗口")

        def compute() -> dict[str, Any]:
            result = rolling_rebalance(
                matrix,
                lookback=lookback,
                rebalance_every=rebalance_every,
                transaction_cost=transaction_cost,
                objective="min_variance",
            )
            dates = ["起始", *[str(d) for d in dataset.returns.index[lookback:]]]
            recent = []
            for step in result.steps[-12:]:
                recent.append(
                    {
                        "step": int(step.step),
                        "date": str(dataset.returns.index[step.step]),
                        "turnover": round(float(step.turnover), 5),
                        "cost": round(float(step.cost), 6),
                        "portfolio_return": round(float(step.portfolio_return), 6),
                        "weights": {
                            name: round(float(weight), 4)
                            for name, weight in zip(dataset.names, step.target_weights, strict=True)
                        },
                    }
                )
            return {
                "dates": dates[: len(result.wealth)],
                "wealth": [round(float(v), 5) for v in result.wealth],
                "summary": {
                    "final_wealth": round(result.final_wealth, 5),
                    "total_return": round(result.final_wealth - 1.0, 5),
                    "total_turnover": round(result.total_turnover, 4),
                    "total_cost": round(result.total_cost, 6),
                    "n_rebalances": len(result.steps),
                    "annualized_return": round(result.final_wealth ** (252 / max(1, len(result.steps))) - 1.0, 5),
                },
                "recent_steps": recent,
            }

        payload = await asyncio.to_thread(compute)
        payload["meta"] = _meta(dataset, "MPC 最小方差滚动")
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        _fail(exc)
