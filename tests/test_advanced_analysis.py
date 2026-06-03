import numpy as np
import pandas as pd
import pytest

from asset_lens.core.advanced_analysis import (
    AnalysisResult,
    PortfolioAnalysis,
    RiskAnalysis,
    TechnicalAnalysis,
)


class TestAnalysisResult:
    def test_creation(self):
        result = AnalysisResult(
            metric="sharpe",
            value=1.5,
            unit="ratio",
            timestamp="2025-01-01",
            metadata={},
        )
        assert result.metric == "sharpe"
        assert result.value == 1.5
        assert result.unit == "ratio"
        assert result.metadata == {}


class TestTechnicalAnalysis:
    def setup_method(self):
        self.ta = TechnicalAnalysis()
        np.random.seed(42)
        self.prices = pd.Series(np.cumsum(np.random.randn(100)) + 100)
        self.high = self.prices + np.abs(np.random.randn(100))
        self.low = self.prices - np.abs(np.random.randn(100))
        self.close = self.prices

    def test_calculate_sma(self):
        sma = TechnicalAnalysis.calculate_sma(self.prices, 5)
        assert len(sma) == len(self.prices)
        assert pd.isna(sma.iloc[0])
        assert not pd.isna(sma.iloc[-1])

    def test_calculate_sma_window_1(self):
        sma = TechnicalAnalysis.calculate_sma(self.prices, 1)
        pd.testing.assert_series_equal(sma, self.prices)

    def test_calculate_ema(self):
        ema = TechnicalAnalysis.calculate_ema(self.prices, 12)
        assert len(ema) == len(self.prices)
        assert not pd.isna(ema.iloc[-1])

    def test_calculate_rsi(self):
        rsi = TechnicalAnalysis.calculate_rsi(self.prices, 14)
        assert len(rsi) == len(self.prices)
        valid = rsi.dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_calculate_macd(self):
        macd, signal, hist = TechnicalAnalysis.calculate_macd(self.prices)
        assert len(macd) == len(self.prices)
        assert len(signal) == len(self.prices)
        assert len(hist) == len(self.prices)

    def test_calculate_bollinger_bands(self):
        upper, middle, lower = TechnicalAnalysis.calculate_bollinger_bands(self.prices)
        assert len(upper) == len(self.prices)
        valid_idx = upper.dropna().index
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (lower[valid_idx] <= middle[valid_idx]).all()

    def test_calculate_atr(self):
        atr = TechnicalAnalysis.calculate_atr(self.high, self.low, self.close, 14)
        assert len(atr) == len(self.prices)
        valid = atr.dropna()
        assert (valid >= 0).all()

    def test_full_analysis(self):
        df = pd.DataFrame({
            "close": self.close,
            "high": self.high,
            "low": self.low,
        })
        result = self.ta.full_analysis(df)
        assert "sma_20" in result
        assert "rsi" in result
        assert "macd" in result
        assert "bollinger_upper" in result
        assert "atr" in result
        assert result["rsi"] is not None

    def test_full_analysis_empty(self):
        df = pd.DataFrame({"close": pd.Series([], dtype=float), "high": pd.Series([], dtype=float), "low": pd.Series([], dtype=float)})
        result = self.ta.full_analysis(df)
        assert result["sma_20"] is None


class TestRiskAnalysis:
    def setup_method(self):
        self.ra = RiskAnalysis(risk_free_rate=0.03)
        np.random.seed(42)
        self.returns = pd.Series(np.random.randn(252) * 0.02)
        self.prices = pd.Series(np.cumsum(self.returns) + 100)

    def test_init_default(self):
        ra = RiskAnalysis()
        assert ra.risk_free_rate == 0.03

    def test_init_custom(self):
        ra = RiskAnalysis(risk_free_rate=0.05)
        assert ra.risk_free_rate == 0.05

    def test_calculate_var(self):
        var = self.ra.calculate_var(self.returns, 0.95)
        assert isinstance(var, float)
        assert var < 0

    def test_calculate_cvar(self):
        cvar = self.ra.calculate_cvar(self.returns, 0.95)
        assert isinstance(cvar, float)
        assert cvar <= self.ra.calculate_var(self.returns, 0.95)

    def test_calculate_max_drawdown(self):
        dd = self.ra.calculate_max_drawdown(self.prices)
        assert isinstance(dd, float)
        assert dd <= 0

    def test_calculate_sharpe_ratio(self):
        sharpe = self.ra.calculate_sharpe_ratio(self.returns)
        assert isinstance(sharpe, float)

    def test_calculate_sortino_ratio(self):
        sortino = self.ra.calculate_sortino_ratio(self.returns)
        assert isinstance(sortino, float)

    def test_calculate_calmar_ratio(self):
        calmar = self.ra.calculate_calmar_ratio(self.returns)
        assert isinstance(calmar, float)

    def test_full_risk_analysis(self):
        result = self.ra.full_risk_analysis(self.returns, self.prices)
        assert "var_95" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        assert "volatility" in result

    def test_full_risk_analysis_no_prices(self):
        result = self.ra.full_risk_analysis(self.returns)
        assert "max_drawdown" not in result


class TestPortfolioAnalysis:
    def setup_method(self):
        self.pa = PortfolioAnalysis()
        np.random.seed(42)
        n = 100
        self.prices_df = pd.DataFrame({
            "close": pd.Series(np.cumsum(np.random.randn(n)) + 100),
            "high": pd.Series(np.cumsum(np.random.randn(n)) + 102),
            "low": pd.Series(np.cumsum(np.random.randn(n)) + 98),
        })
        self.holdings = {"sh600519": 100, "sh000858": 200}

    def test_init(self):
        assert isinstance(self.pa.technical, TechnicalAnalysis)
        assert isinstance(self.pa.risk, RiskAnalysis)

    def test_analyze_portfolio(self):
        result = self.pa.analyze_portfolio(self.holdings, self.prices_df)
        assert "portfolio_value" in result
        assert "weights" in result
        assert "risk_metrics" in result
        assert "timestamp" in result
        assert result["portfolio_value"] > 0

    def test_analyze_portfolio_empty(self):
        result = self.pa.analyze_portfolio({}, self.prices_df)
        assert result["portfolio_value"] == 0

    def test_calculate_correlation_matrix(self):
        returns = pd.DataFrame({
            "A": np.random.randn(50),
            "B": np.random.randn(50),
        })
        corr = self.pa.calculate_correlation_matrix(returns)
        assert corr.shape == (2, 2)
        assert corr.iloc[0, 0] == pytest.approx(1.0)

    def test_calculate_beta(self):
        stock = pd.Series(np.random.randn(50))
        market = pd.Series(np.random.randn(50))
        beta = self.pa.calculate_beta(stock, market)
        assert isinstance(beta, float)

    def test_calculate_beta_zero_variance(self):
        stock = pd.Series(np.random.randn(50))
        market = pd.Series([1.0] * 50)
        beta = self.pa.calculate_beta(stock, market)
        assert beta == 0.0

    def test_calculate_alpha(self):
        stock = pd.Series(np.random.randn(50) * 0.02)
        market = pd.Series(np.random.randn(50) * 0.02)
        alpha = self.pa.calculate_alpha(stock, market)
        assert isinstance(alpha, float)

    def test_calculate_tracking_error(self):
        port = pd.Series(np.random.randn(50) * 0.02)
        bench = pd.Series(np.random.randn(50) * 0.02)
        te = self.pa.calculate_tracking_error(port, bench)
        assert isinstance(te, float)
        assert te >= 0

    def test_calculate_information_ratio(self):
        port = pd.Series(np.random.randn(50) * 0.02)
        bench = pd.Series(np.random.randn(50) * 0.02)
        ir = self.pa.calculate_information_ratio(port, bench)
        assert isinstance(ir, float)
