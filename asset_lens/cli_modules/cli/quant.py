"""量化分析 CLI：CVaR / Markowitz / Monte Carlo / MPC。

所有命令都接受 ``--returns <csv>``（首列日期、其余列为各资产单期收益率）。
不传文件时用内置的确定性演示数据（固定 seed），方便零配置试用。
"""

from __future__ import annotations

from pathlib import Path

import click
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

from asset_lens.quant import (
    Constraints,
    as_returns_matrix,
    efficient_frontier,
    historical_cvar,
    historical_var,
    infer_names,
    load_returns_csv,
    max_sharpe,
    min_variance,
    minimize_cvar,
    parametric_cvar,
    rolling_rebalance,
    simulate,
    target_return,
)

console = Console()


def _demo_returns() -> pd.DataFrame:
    """生成确定性的演示收益率（3 资产 × 252 期），仅用于 CLI 试用。"""
    rng = np.random.default_rng(20261118)
    data = {
        "股票": rng.normal(0.0004, 0.015, 252),
        "债券": rng.normal(0.0001, 0.003, 252),
        "黄金": rng.normal(0.0002, 0.009, 252),
    }
    return pd.DataFrame(data, index=pd.bdate_range("2025-01-01", periods=252, name="date"))


def _load(returns_path: str | None) -> pd.DataFrame:
    """加载收益率：显式文件优先，否则回退到演示数据。"""
    if returns_path:
        path = Path(returns_path).expanduser()
        if not path.is_file():
            raise click.ClickException(f"收益率文件不存在: {path}")
        try:
            return load_returns_csv(path)
        except (ValueError, OSError) as exc:
            raise click.ClickException(f"读取收益率文件失败: {exc}") from exc
    console.print("[dim]未提供 --returns，使用内置演示数据（固定 seed）。[/dim]")
    return _demo_returns()


def _weights_table(result: object, names: list[str], objective: str) -> Table:
    """把优化结果渲染成权重表。"""
    table = Table(title=f"{objective} — 最优权重")
    table.add_column("资产", style="cyan")
    table.add_column("权重", justify="right", style="green")
    for name, weight in zip(names, result.weights, strict=True):  # type: ignore[attr-defined]
        table.add_row(name, f"{float(weight):.2%}")
    table.add_row("—", "—")
    table.add_row("预期单期收益", f"{result.expected_return:.4%}")  # type: ignore[attr-defined]
    table.add_row("单期波动率", f"{result.volatility:.4%}")  # type: ignore[attr-defined]
    table.add_row("目标值", f"{result.objective_value:.6f}")  # type: ignore[attr-defined]
    return table


@click.group()
def quant():
    """量化分析命令：CVaR / Markowitz / Monte Carlo / MPC"""
    pass


@quant.command("cvar")
@click.option("--returns", "returns_path", type=click.Path(), default=None, help="收益率 CSV 路径")
@click.option("--level", default=0.95, show_default=True, help="置信水平 (0, 1)")
@click.option("--asset", default=None, help="只算某一资产；缺省时按等权组合计算")
def cvar_command(returns_path: str | None, level: float, asset: str | None) -> None:
    """计算 CVaR / VaR（正数=损失幅度）。"""
    frame = _load(returns_path)
    matrix = as_returns_matrix(frame)
    names = infer_names(frame) or [f"asset_{i}" for i in range(matrix.shape[1])]

    if not 0.0 < level < 1.0:
        raise click.ClickException("--level 必须落在 (0, 1)")

    if asset:
        if asset not in names:
            raise click.ClickException(f"找不到资产 {asset!r}，可选: {', '.join(names)}")
        series = matrix[:, names.index(asset)]
        label = asset
    else:
        series = matrix.mean(axis=1)
        label = "等权组合"

    var_value = historical_var(series, level)
    cvar_value = historical_cvar(series, level)
    mean = float(series.mean())
    std = float(series.std(ddof=1))
    normal_cvar = parametric_cvar(mean, std, level)

    table = Table(title=f"CVaR 分析 — {label}")
    table.add_column("指标", style="cyan")
    table.add_column("数值", justify="right", style="green")
    table.add_row(f"VaR({level:.0%})", f"{var_value:.4%}")
    table.add_row(f"CVaR({level:.0%}) 历史模拟", f"{cvar_value:.4%}")
    table.add_row(f"CVaR({level:.0%}) 正态假设", f"{normal_cvar:.4%}")
    console.print(table)


@quant.command("optimize")
@click.option("--returns", "returns_path", type=click.Path(), default=None, help="收益率 CSV 路径")
@click.option(
    "--objective",
    type=click.Choice(["min_variance", "max_sharpe", "min_cvar", "target_return", "frontier"]),
    default="min_variance",
    show_default=True,
)
@click.option("--target", type=float, default=None, help="target_return 的单期收益下限")
@click.option("--risk-free", type=float, default=0.0, show_default=True, help="max_sharpe 的单期无风险利率")
@click.option("--level", default=0.95, show_default=True, help="min_cvar 的置信水平")
@click.option("--min-weight", default=0.0, show_default=True)
@click.option("--max-weight", default=1.0, show_default=True)
@click.option("--points", default=5, show_default=True, help="frontier 的点数")
def optimize_command(
    returns_path: str | None,
    objective: str,
    target: float | None,
    risk_free: float,
    level: float,
    min_weight: float,
    max_weight: float,
    points: int,
) -> None:
    """Markowitz / 最小 CVaR 组合优化。"""
    frame = _load(returns_path)
    matrix = as_returns_matrix(frame)
    names = infer_names(frame) or [f"asset_{i}" for i in range(matrix.shape[1])]

    try:
        constraints = Constraints(min_weight=min_weight, max_weight=max_weight)
        if objective == "min_variance":
            result = min_variance(matrix, constraints)
        elif objective == "max_sharpe":
            result = max_sharpe(matrix, risk_free, constraints)
        elif objective == "min_cvar":
            result = minimize_cvar(matrix, level, constraints)
        elif objective == "target_return":
            if target is None:
                raise click.ClickException("target_return 目标需要 --target 参数")
            result = target_return(matrix, target, constraints)
        else:
            frontier = efficient_frontier(matrix, points, constraints)
            table = Table(title="有效前沿")
            table.add_column("#", style="cyan")
            table.add_column("预期单期收益", justify="right")
            table.add_column("单期波动率", justify="right")
            for index, item in enumerate(frontier, 1):
                table.add_row(str(index), f"{item.expected_return:.4%}", f"{item.volatility:.4%}")
            console.print(table)
            return
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.success:
        raise click.ClickException(f"优化失败: {result.message}")
    console.print(_weights_table(result, names, objective))


@quant.command("simulate")
@click.option("--returns", "returns_path", type=click.Path(), default=None, help="收益率 CSV 路径")
@click.option("--method", type=click.Choice(["bootstrap", "gbm"]), default="bootstrap", show_default=True)
@click.option("--horizon", default=252, show_default=True, help="模拟期数")
@click.option("--paths", "n_paths", default=1000, show_default=True, help="路径条数")
@click.option("--seed", default=42, show_default=True, help="随机种子")
@click.option("--level", default=0.95, show_default=True)
@click.option("--weights", default=None, help="逗号分隔的权重，如 0.5,0.3,0.2；缺省用等权")
def simulate_command(
    returns_path: str | None,
    method: str,
    horizon: int,
    n_paths: int,
    seed: int,
    level: float,
    weights: str | None,
) -> None:
    """蒙特卡洛模拟组合终值分布。"""
    frame = _load(returns_path)
    matrix = as_returns_matrix(frame)
    n_assets = matrix.shape[1]

    if weights:
        try:
            weight_array = np.array([float(x) for x in weights.split(",")])
        except ValueError as exc:
            raise click.ClickException("--weights 必须是逗号分隔的数字") from exc
        if weight_array.size != n_assets:
            raise click.ClickException(f"--weights 给了 {weight_array.size} 个值，但资产数为 {n_assets}")
    else:
        weight_array = np.full(n_assets, 1.0 / n_assets)

    try:
        summary = simulate(
            matrix,
            weight_array,
            method=method,
            horizon=horizon,
            n_paths=n_paths,
            seed=seed,
            level=level,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(summary.format_text())


@quant.command("mpc")
@click.option("--returns", "returns_path", type=click.Path(), default=None, help="收益率 CSV 路径")
@click.option("--lookback", default=60, show_default=True, help="滚动窗口长度")
@click.option("--rebalance-every", default=5, show_default=True, help="每隔多少期再平衡")
@click.option("--cost", "transaction_cost", default=0.001, show_default=True, help="单边换手成本率")
@click.option("--objective", type=click.Choice(["min_variance", "max_sharpe"]), default="min_variance")
def mpc_command(
    returns_path: str | None,
    lookback: int,
    rebalance_every: int,
    transaction_cost: float,
    objective: str,
) -> None:
    """MPC 滚动再平衡回测（含交易成本）。"""
    frame = _load(returns_path)
    matrix = as_returns_matrix(frame)
    try:
        result = rolling_rebalance(
            matrix,
            lookback=lookback,
            rebalance_every=rebalance_every,
            transaction_cost=transaction_cost,
            objective=objective,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(result.format_text())


def register_quant_commands(cli: click.Group) -> None:
    """把 quant 命令组挂到主 CLI。"""
    cli.add_command(quant)


__all__ = ["quant", "register_quant_commands"]
