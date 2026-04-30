"""
Advanced Analysis Tools - 高级分析工具
包含技术分析、风险分析、组合分析等工具
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """分析结果"""

    metric: str
    value: float
    unit: str
    timestamp: str
    metadata: dict[str, Any]


class TechnicalAnalysis:
    """技术分析工具"""

    @staticmethod
    def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
        """计算简单移动平均"""
        return prices.rolling(window=window).mean()

    @staticmethod
    def calculate_ema(prices: pd.Series, span: int) -> pd.Series:
        """计算指数移动平均"""
        return prices.ewm(span=span, adjust=False).mean()

    @staticmethod
    def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """计算相对强弱指数"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(
        prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """计算 MACD"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series, window: int = 20, num_std: int = 2
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带"""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()

        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)

        return upper_band, sma, lower_band

    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """计算平均真实波幅"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()

        return atr

    def full_analysis(self, prices: pd.DataFrame) -> dict[str, Any]:
        """
        完整技术分析

        Args:
            prices: OHLCV 数据

        Returns:
            分析结果
        """
        close = prices["close"]
        high = prices["high"]
        low = prices["low"]

        # 计算各种指标
        sma_20 = self.calculate_sma(close, 20)
        sma_50 = self.calculate_sma(close, 50)
        ema_12 = self.calculate_ema(close, 12)
        ema_26 = self.calculate_ema(close, 26)
        rsi = self.calculate_rsi(close)
        macd, signal, hist = self.calculate_macd(close)
        upper, middle, lower = self.calculate_bollinger_bands(close)
        atr = self.calculate_atr(high, low, close)

        return {
            "sma_20": sma_20.iloc[-1] if not sma_20.empty else None,
            "sma_50": sma_50.iloc[-1] if not sma_50.empty else None,
            "ema_12": ema_12.iloc[-1] if not ema_12.empty else None,
            "ema_26": ema_26.iloc[-1] if not ema_26.empty else None,
            "rsi": rsi.iloc[-1] if not rsi.empty else None,
            "macd": macd.iloc[-1] if not macd.empty else None,
            "signal": signal.iloc[-1] if not signal.empty else None,
            "histogram": hist.iloc[-1] if not hist.empty else None,
            "bollinger_upper": upper.iloc[-1] if not upper.empty else None,
            "bollinger_middle": middle.iloc[-1] if not middle.empty else None,
            "bollinger_lower": lower.iloc[-1] if not lower.empty else None,
            "atr": atr.iloc[-1] if not atr.empty else None,
        }


class RiskAnalysis:
    """风险分析工具"""

    def __init__(self, risk_free_rate: float = 0.03):
        """
        初始化风险分析工具

        Args:
            risk_free_rate: 无风险利率
        """
        self.risk_free_rate = risk_free_rate

    def calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        计算风险价值

        Args:
            returns: 收益率序列
            confidence: 置信水平

        Returns:
            VaR 值
        """
        return float(np.percentile(returns, (1 - confidence) * 100))

    def calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        计算条件风险价值

        Args:
            returns: 收益率序列
            confidence: 置信水平

        Returns:
            CVaR 值
        """
        var = self.calculate_var(returns, confidence)
        return float(returns[returns <= var].mean())

    def calculate_max_drawdown(self, prices: pd.Series) -> float:
        """
        计算最大回撤

        Args:
            prices: 价格序列

        Returns:
            最大回撤
        """
        peak = prices.expanding(min_periods=1).max()
        drawdown = (prices - peak) / peak
        return float(drawdown.min())

    def calculate_sharpe_ratio(self, returns: pd.Series, periods: int = 252) -> float:
        """
        计算夏普比率

        Args:
            returns: 收益率序列
            periods: 年化周期数

        Returns:
            夏普比率
        """
        excess_returns = returns - self.risk_free_rate / periods
        return float(np.sqrt(periods) * excess_returns.mean() / excess_returns.std())

    def calculate_sortino_ratio(self, returns: pd.Series, periods: int = 252) -> float:
        """
        计算索提诺比率

        Args:
            returns: 收益率序列
            periods: 年化周期数

        Returns:
            索提诺比率
        """
        excess_returns = returns - self.risk_free_rate / periods
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()

        return float(np.sqrt(periods) * excess_returns.mean() / downside_std)

    def calculate_calmar_ratio(self, returns: pd.Series, periods: int = 252) -> float:
        """
        计算卡尔马比率

        Args:
            returns: 收益率序列
            periods: 年化周期数

        Returns:
            卡尔马比率
        """
        annual_return = returns.mean() * periods
        prices = (1 + returns).cumprod()
        max_dd = abs(self.calculate_max_drawdown(prices))

        return float(annual_return / max_dd) if max_dd > 0 else 0.0

    def full_risk_analysis(self, returns: pd.Series, prices: pd.Series | None = None) -> dict[str, float]:
        """
        完整风险分析

        Args:
            returns: 收益率序列
            prices: 价格序列

        Returns:
            风险分析结果
        """
        results = {
            "var_95": self.calculate_var(returns, 0.95),
            "var_99": self.calculate_var(returns, 0.99),
            "cvar_95": self.calculate_cvar(returns, 0.95),
            "cvar_99": self.calculate_cvar(returns, 0.99),
            "sharpe_ratio": self.calculate_sharpe_ratio(returns),
            "sortino_ratio": self.calculate_sortino_ratio(returns),
            "calmar_ratio": self.calculate_calmar_ratio(returns),
            "volatility": returns.std() * np.sqrt(252),
            "skewness": returns.skew(),
            "kurtosis": returns.kurtosis(),
        }

        if prices is not None:
            results["max_drawdown"] = self.calculate_max_drawdown(prices)

        return results


class PortfolioAnalysis:
    """投资组合分析工具"""

    def __init__(self):
        self.technical = TechnicalAnalysis()
        self.risk = RiskAnalysis()

    def analyze_portfolio(self, holdings: dict[str, float], prices: pd.DataFrame) -> dict[str, Any]:
        """
        分析投资组合

        Args:
            holdings: 持仓 {股票代码: 数量}
            prices: 价格数据

        Returns:
            分析结果
        """
        # 计算投资组合价值
        portfolio_value = sum(holdings.get(code, 0) * prices["close"].iloc[-1] for code in holdings)

        # 计算持仓权重
        weights = {code: (holdings.get(code, 0) * prices["close"].iloc[-1]) / portfolio_value for code in holdings}

        # 计算收益率
        returns = prices["close"].pct_change()

        # 计算风险指标
        risk_metrics = self.risk.full_risk_analysis(returns, prices["close"])

        return {
            "portfolio_value": portfolio_value,
            "weights": weights,
            "risk_metrics": risk_metrics,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def calculate_correlation_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """
        计算相关性矩阵

        Args:
            returns: 收益率数据

        Returns:
            相关性矩阵
        """
        return returns.corr()

    def calculate_beta(self, stock_returns: pd.Series, market_returns: pd.Series) -> float:
        """
        计算贝塔系数

        Args:
            stock_returns: 股票收益率
            market_returns: 市场收益率

        Returns:
            贝塔系数
        """
        covariance = np.cov(stock_returns, market_returns)[0][1]
        market_variance = np.var(market_returns)

        return float(covariance / market_variance) if market_variance > 0 else 0.0

    def calculate_alpha(
        self, stock_returns: pd.Series, market_returns: pd.Series, risk_free_rate: float = 0.03
    ) -> float:
        """
        计算阿尔法

        Args:
            stock_returns: 股票收益率
            market_returns: 市场收益率
            risk_free_rate: 无风险利率

        Returns:
            阿尔法
        """
        beta = self.calculate_beta(stock_returns, market_returns)

        expected_return = risk_free_rate + beta * (market_returns.mean() - risk_free_rate)
        actual_return = stock_returns.mean()

        return float(actual_return - expected_return)

    def calculate_tracking_error(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        计算跟踪误差

        Args:
            portfolio_returns: 投资组合收益率
            benchmark_returns: 基准收益率

        Returns:
            跟踪误差
        """
        return float((portfolio_returns - benchmark_returns).std() * np.sqrt(252))

    def calculate_information_ratio(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        计算信息比率

        Args:
            portfolio_returns: 投资组合收益率
            benchmark_returns: 基准收益率

        Returns:
            信息比率
        """
        excess_returns = portfolio_returns - benchmark_returns
        tracking_error = self.calculate_tracking_error(portfolio_returns, benchmark_returns)

        return float(excess_returns.mean() / tracking_error) if tracking_error > 0 else 0.0
