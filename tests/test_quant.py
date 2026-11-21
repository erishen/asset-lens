"""量化模块（CVaR / Markowitz / Monte Carlo / MPC）单元测试。

全部用确定性数据，不依赖网络与真实账本；固定 seed 保证可复现。
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd
import pytest

from asset_lens.quant import (
    Constraints,
    MPCController,
    as_returns_matrix,
    bootstrap_paths,
    efficient_frontier,
    gbm_paths,
    historical_cvar,
    historical_var,
    load_returns_csv,
    max_sharpe,
    min_variance,
    minimize_cvar,
    parametric_cvar,
    portfolio_cvar,
    portfolio_paths,
    portfolio_returns,
    rolling_rebalance,
    simulate,
    simulate_paths,
    target_return,
)


def _sample_returns(seed: int = 7, periods: int = 240, assets: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(
        loc=[0.0005, 0.0002, 0.0003][:assets], scale=[0.015, 0.004, 0.009][:assets], size=(periods, assets)
    )


class TestInputNormalization:
    def test_series_and_list_become_column_matrix(self):
        assert as_returns_matrix([0.01, -0.02, 0.03]).shape == (3, 1)
        assert as_returns_matrix(pd.Series([0.1, 0.2], name="x")).shape == (2, 1)

    def test_dataframe_passthrough(self):
        frame = pd.DataFrame({"a": [0.1, 0.2], "b": [0.3, 0.4]})
        result = as_returns_matrix(frame)
        assert result.shape == (2, 2)
        np.testing.assert_allclose(result, frame.to_numpy())

    def test_rejects_nan(self):
        with pytest.raises(ValueError, match="NaN"):
            as_returns_matrix([0.1, np.nan])

    def test_load_returns_csv(self, tmp_path):
        csv = tmp_path / "r.csv"
        csv.write_text("date,a,b\n2026-01-01,0.01,0.02\n2026-01-02,-0.01,0.0\n", encoding="utf-8")
        frame = load_returns_csv(csv)
        assert list(frame.columns) == ["a", "b"]
        assert as_returns_matrix(frame).shape == (2, 2)


class TestCVaR:
    def test_known_tail_average(self):
        # level=0.75 → 尾部 5*0.25=1.25 个样本：最差 1 个全额 + 第 2 个按 0.25 加权
        # ES = -( -0.05 + 0.25*(-0.04) ) / 1.25 = 0.048
        series = np.array([-0.05, -0.04, -0.01, 0.02, 0.03])
        cvar = historical_cvar(series, 0.75)
        assert cvar == pytest.approx(0.048)
        assert cvar >= historical_var(series, 0.75) - 1e-9

    def test_cvar_exceeds_var(self):
        series = _sample_returns()[:, 0]
        var = historical_var(series, 0.95)
        cvar = historical_cvar(series, 0.95)
        assert cvar >= var  # 尾部均值必然不优于分位数

    def test_higher_confidence_higher_cvar(self):
        series = _sample_returns()[:, 0]
        assert historical_cvar(series, 0.99) >= historical_cvar(series, 0.95)

    def test_parametric_matches_normal(self):
        rng = np.random.default_rng(1)
        series = rng.normal(-0.001, 0.02, 200_000)
        historical = historical_cvar(series, 0.95)
        analytic = parametric_cvar(float(series.mean()), float(series.std(ddof=1)), 0.95)
        assert abs(historical - analytic) < 0.002

    def test_invalid_level(self):
        with pytest.raises(ValueError):
            historical_cvar([0.1, 0.2], 1.0)

    def test_portfolio_cvar(self):
        matrix = _sample_returns()
        weights = np.array([0.5, 0.3, 0.2])
        expected = historical_cvar(portfolio_returns(matrix, weights), 0.95)
        assert np.isclose(portfolio_cvar(matrix, weights, 0.95), expected)

    def test_minimize_cvar_valid_weights(self):
        matrix = _sample_returns()
        result = minimize_cvar(matrix, 0.95)
        assert result.success
        assert np.isclose(result.weights.sum(), 1.0)
        assert np.all(result.weights >= -1e-9)
        # 最小 CVaR 不应差于等权组合
        equal = portfolio_cvar(matrix, np.full(3, 1 / 3), 0.95)
        assert portfolio_cvar(matrix, result.weights, 0.95) <= equal + 1e-9

    def test_lp_objective_matches_recomputed_cvar(self):
        """回归：LP 目标值与按返回权重复算的 CVaR 必须同口径（曾差 5%）。"""
        matrix = _sample_returns()
        result = minimize_cvar(matrix, 0.95)
        assert result.objective_value == pytest.approx(portfolio_cvar(matrix, result.weights, 0.95), abs=1e-12)

    def test_min_return_ignored_with_notice(self):
        """回归：min_return 声称不生效，就不能在 validate 阶段误拒合法调用。"""
        result = minimize_cvar(_sample_returns(), 0.95, Constraints(min_return=0.0004))
        assert result.success
        assert "min_return" in result.message


class TestMarkowitz:
    def test_min_variance_valid(self):
        matrix = _sample_returns()
        result = min_variance(matrix)
        assert result.success
        assert np.isclose(result.weights.sum(), 1.0)
        assert np.all(result.weights >= -1e-8)
        equal_var = float(np.var(portfolio_returns(matrix, np.full(3, 1 / 3)), ddof=1))
        assert result.objective_value <= equal_var + 1e-12

    def test_weight_bounds_respected(self):
        matrix = _sample_returns()
        result = min_variance(matrix, Constraints(min_weight=0.1, max_weight=0.6))
        assert np.all(result.weights >= 0.1 - 1e-8)
        assert np.all(result.weights <= 0.6 + 1e-8)

    def test_max_sharpe(self):
        matrix = _sample_returns()
        result = max_sharpe(matrix, risk_free_rate=0.0)
        assert result.success
        assert np.isclose(result.weights.sum(), 1.0)
        # 最大夏普不应劣于等权组合（曾因分母钳位返回假值却 success=True）
        cov = np.cov(matrix, rowvar=False, ddof=1)
        equal = np.full(matrix.shape[1], 1.0 / matrix.shape[1])
        equal_sharpe = float(equal @ matrix.mean(axis=0)) / float(np.sqrt(equal @ cov @ equal))
        assert result.objective_value >= equal_sharpe - 1e-8

    def test_degenerate_max_sharpe_reports_failure(self):
        """回归：常数收益/全负超额收益时夏普无定义，不能报 1000 且 success=True。"""
        constant = np.full((50, 3), 0.001)
        result = max_sharpe(constant)
        assert not result.success
        assert np.isnan(result.objective_value)
        assert "无定义" in result.message
        # 随机样本的均值可能仍为正，务必平移到所有资产均值都严格为负
        negative = np.random.default_rng(3).normal(0, 0.01, (50, 3)) - 0.05
        assert not max_sharpe(negative).success

    def test_nan_objective_serializes_to_null(self):
        """回归：夏普无定义时 as_dict 必须输出 None，否则 JSONResponse 抛 ValueError→500。"""
        import json

        result = max_sharpe(np.full((50, 3), 0.001))
        payload = result.as_dict(["a", "b", "c"])
        assert payload["objective_value"] is None
        assert payload["success"] is False
        assert json.loads(json.dumps(payload))["objective_value"] is None
        # 正常路径不受影响
        normal = min_variance(_sample_returns()).as_dict(["a", "b", "c"])
        assert normal["objective_value"] is not None

    def test_target_return_constraint(self):
        matrix = _sample_returns()
        mu = matrix.mean(axis=0)
        target = float(mu.max() * 0.8)
        result = target_return(matrix, target)
        assert result.success
        assert result.expected_return >= target - 1e-8

    def test_infeasible_target_raises(self):
        matrix = _sample_returns()
        with pytest.raises(ValueError, match="不可达"):
            target_return(matrix, float(matrix.mean(axis=0).max()) + 0.1)

    def test_efficient_frontier_monotonic(self):
        matrix = _sample_returns()
        frontier = efficient_frontier(matrix, n_points=5)
        returns = [item.expected_return for item in frontier]
        vols = [item.volatility for item in frontier]
        assert returns == sorted(returns)
        # 有效前沿的核心定义：同等收益下方差最低 ⇒ 波动率随收益单调不减
        assert all(a <= b + 1e-10 for a, b in pairwise(vols))
        assert all(item.success for item in frontier)

    def test_efficient_frontier_with_constraints(self):
        """回归：带权重上下界的前沿曾因上界取无约束 max(mu) 而必定崩溃。"""
        matrix = _sample_returns()
        constraints = Constraints(min_weight=0.1, max_weight=0.5)
        frontier = efficient_frontier(matrix, n_points=4, constraints=constraints)
        assert len(frontier) == 4
        assert all(item.success for item in frontier)
        for item in frontier:
            assert np.all(item.weights >= 0.1 - 1e-8)
            assert np.all(item.weights <= 0.5 + 1e-8)
        vols = [item.volatility for item in frontier]
        assert all(a <= b + 1e-10 for a, b in pairwise(vols))


class TestMonteCarlo:
    def test_reproducible_with_seed(self):
        matrix = _sample_returns()
        first = bootstrap_paths(matrix, horizon=30, n_paths=50, seed=123)
        second = bootstrap_paths(matrix, horizon=30, n_paths=50, seed=123)
        np.testing.assert_allclose(first, second)
        different = bootstrap_paths(matrix, horizon=30, n_paths=50, seed=124)
        assert not np.allclose(first, different)

    def test_paths_shape_and_start(self):
        matrix = _sample_returns()
        for generator in (gbm_paths, bootstrap_paths):
            paths = generator(matrix, horizon=20, n_paths=40, seed=1)
            assert paths.shape == (21, 40, 3)
            np.testing.assert_allclose(paths[0], 1.0)

    def test_summary_statistics(self):
        matrix = _sample_returns()
        paths = bootstrap_paths(matrix, horizon=20, n_paths=200, seed=9)
        summary = simulate_paths(paths @ np.full(3, 1 / 3), 0.95)
        assert summary.n_paths == 200
        assert summary.horizon == 20
        assert 0.0 <= summary.prob_loss <= 1.0
        assert summary.cvar >= summary.var - 1e-9
        assert summary.p05 <= summary.median <= summary.p95

    def test_simulate_end_to_end(self):
        matrix = _sample_returns()
        summary = simulate(matrix, np.full(3, 1 / 3), method="bootstrap", horizon=30, n_paths=100, seed=5)
        assert summary.n_paths == 100
        assert "蒙特卡洛路径" in summary.format_text()

    def test_unknown_method(self):
        with pytest.raises(ValueError, match="未知 method"):
            simulate(_sample_returns(), np.ones(3) / 3, method="nope")

    def test_rejects_zero_sum_weights(self):
        """回归：多空权重和为 0 曾静默产生全 NaN 路径。"""
        with pytest.raises(ValueError, match="无法归一化"):
            portfolio_paths(np.ones((5, 10, 3)), np.array([1.0, -1.0, 0.0]))

    def test_rejects_multidim_paths(self):
        """回归：3D 多资产路径曾被当成 2D 净值混算终值统计。"""
        paths = gbm_paths(_sample_returns(), horizon=10, n_paths=20, seed=1)
        with pytest.raises(ValueError, match="2D"):
            simulate_paths(paths)

    def test_rejects_mismatched_kwargs(self):
        """回归：method/kwarg 不匹配曾抛裸 TypeError。"""
        with pytest.raises(ValueError, match="不接受参数"):
            simulate(_sample_returns(), np.ones(3) / 3, method="gbm", block_size=5)

    def test_invalid_periods_per_year(self):
        with pytest.raises(ValueError, match="periods_per_year"):
            gbm_paths(_sample_returns(), horizon=10, n_paths=20, seed=1, periods_per_year=0)

    def test_gbm_correlation_scale_invariant(self):
        """回归：固定 Cholesky ridge 曾让小尺度收益的相关结构失真。"""
        rng = np.random.default_rng(11)
        base = rng.normal(0, 0.01, (400, 3))
        base[:, 1] = 0.6 * base[:, 0] + 0.8 * base[:, 1]
        corrs = []
        for scale in (1.0, 1e-6):
            log_ret = np.diff(np.log(gbm_paths(base * scale, horizon=120, n_paths=1500, seed=7)), axis=0)
            corrs.append(float(np.corrcoef(log_ret[:, :, 0].ravel(), log_ret[:, :, 1].ravel())[0, 1]))
        assert abs(corrs[0] - corrs[1]) < 0.05


class TestMPC:
    def test_short_history_returns_empty(self):
        result = rolling_rebalance(_sample_returns(periods=30), lookback=60)
        assert result.final_wealth == 1.0
        assert len(result.steps) == 0

    def test_steps_weights_and_turnover(self):
        matrix = _sample_returns()
        result = rolling_rebalance(matrix, lookback=60, rebalance_every=5, transaction_cost=0.0)
        assert len(result.steps) > 0
        history = result.weights_history()
        assert history.shape == (len(result.steps), 3)
        np.testing.assert_allclose(history.sum(axis=1), 1.0, atol=1e-8)
        assert result.total_turnover >= 0.0
        assert np.all(np.array(result.wealth) > 0)

    def test_transaction_cost_reduces_wealth(self):
        matrix = _sample_returns()
        free = rolling_rebalance(matrix, lookback=60, rebalance_every=3, transaction_cost=0.0)
        costly = rolling_rebalance(matrix, lookback=60, rebalance_every=3, transaction_cost=0.01)
        assert costly.total_cost > 0.0
        assert costly.final_wealth <= free.final_wealth + 1e-12

    def test_max_drawdown(self):
        matrix = _sample_returns()
        result = rolling_rebalance(matrix, lookback=60)
        assert 0.0 <= result.max_drawdown() <= 1.0

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            MPCController(lookback=1)
        with pytest.raises(ValueError):
            MPCController(objective="unknown")


class TestQuantRoutes:
    """路由层契约：降采样后三个 series 必须与 category 轴等长。"""

    def test_simulate_series_aligned_with_timeline(self, monkeypatch):
        import asyncio

        import pandas as pd

        from asset_lens.data.quant_returns import QuantDataset
        from asset_lens.web.routes import quant as quant_route

        matrix = _sample_returns(periods=120)
        names = ["a", "b", "c"]
        dataset = QuantDataset(
            returns=pd.DataFrame(matrix, columns=names),
            names=names,
            start_date="2026-01-01",
            end_date="2026-06-30",
            periods=len(matrix),
        )

        async def fake_load(_count):
            return dataset

        monkeypatch.setattr(quant_route, "load_returns", fake_load)
        payload = asyncio.run(quant_route.simulate_portfolio(
            method="bootstrap", horizon=252, n_paths=100, level=0.95, count=120
        ))
        n = len(payload["timeline"])
        assert n == len(payload["quantiles"]["p05"]) == len(payload["quantiles"]["p50"]) == len(payload["quantiles"]["p95"])
        assert all(len(p) == n for p in payload["sample_paths"])
        assert payload["timeline"][0] == 0 and payload["timeline"][-1] == 252
