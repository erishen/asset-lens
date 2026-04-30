"""
Portfolio Analytics module for asset-lens.
专业的投资组合分析模块
"""

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class PortfolioMetrics:
    """投资组合指标"""

    total_return: float  # 总收益率
    annualized_return: float  # 年化收益率
    volatility: float  # 波动率
    sharpe_ratio: float  # 夏普比率
    max_drawdown: float  # 最大回撤
    win_rate: float  # 胜率
    profit_loss_ratio: float  # 盈亏比
    calmar_ratio: float  # 卡玛比率
    sortino_ratio: float  # 索提诺比率


@dataclass
class RiskMetrics:
    """风险指标"""

    value_at_risk_95: float  # 95% VaR
    value_at_risk_99: float  # 99% VaR
    expected_shortfall: float  # 预期亏损 (CVaR)
    beta: float  # 贝塔系数
    tracking_error: float  # 跟踪误差
    information_ratio: float  # 信息比率


class PortfolioAnalytics:
    """投资组合分析器"""

    RISK_FREE_RATE = 0.02  # 无风险利率 2%
    TRADING_DAYS_PER_YEAR = 252  # 每年交易日

    def __init__(self, risk_free_rate: float = 0.02):
        """
        初始化投资组合分析器

        Args:
            risk_free_rate: 无风险利率
        """
        self.risk_free_rate = risk_free_rate

    def calculate_metrics(
        self,
        returns: list[float],
        benchmark_returns: list[float] | None = None,
    ) -> PortfolioMetrics:
        """
        计算投资组合指标

        Args:
            returns: 收益率序列
            benchmark_returns: 基准收益率序列（可选）

        Returns:
            投资组合指标
        """
        if not returns:
            return PortfolioMetrics(
                total_return=0.0,
                annualized_return=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_loss_ratio=0.0,
                calmar_ratio=0.0,
                sortino_ratio=0.0,
            )

        # 总收益率
        total_return = self._calculate_total_return(returns)

        # 年化收益率
        annualized_return = self._calculate_annualized_return(returns)

        # 波动率
        volatility = self._calculate_volatility(returns)

        # 夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio(returns, volatility)

        # 最大回撤
        max_drawdown = self._calculate_max_drawdown(returns)

        # 胜率
        win_rate = self._calculate_win_rate(returns)

        # 盈亏比
        profit_loss_ratio = self._calculate_profit_loss_ratio(returns)

        # 卡玛比率
        calmar_ratio = self._calculate_calmar_ratio(annualized_return, max_drawdown)

        # 索提诺比率
        sortino_ratio = self._calculate_sortino_ratio(returns)

        return PortfolioMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
        )

    def calculate_risk_metrics(
        self,
        returns: list[float],
        benchmark_returns: list[float] | None = None,
    ) -> RiskMetrics:
        """
        计算风险指标

        Args:
            returns: 收益率序列
            benchmark_returns: 基准收益率序列（可选）

        Returns:
            风险指标
        """
        if not returns:
            return RiskMetrics(
                value_at_risk_95=0.0,
                value_at_risk_99=0.0,
                expected_shortfall=0.0,
                beta=1.0,
                tracking_error=0.0,
                information_ratio=0.0,
            )

        # VaR
        var_95 = self._calculate_var(returns, 0.95)
        var_99 = self._calculate_var(returns, 0.99)

        # CVaR (Expected Shortfall)
        es = self._calculate_expected_shortfall(returns, 0.95)

        # Beta
        beta = self._calculate_beta(returns, benchmark_returns) if benchmark_returns else 1.0

        # 跟踪误差
        tracking_error = self._calculate_tracking_error(returns, benchmark_returns) if benchmark_returns else 0.0

        # 信息比率
        information_ratio = self._calculate_information_ratio(returns, benchmark_returns) if benchmark_returns else 0.0

        return RiskMetrics(
            value_at_risk_95=var_95,
            value_at_risk_99=var_99,
            expected_shortfall=es,
            beta=beta,
            tracking_error=tracking_error,
            information_ratio=information_ratio,
        )

    def _calculate_total_return(self, returns: list[float]) -> float:
        """计算总收益率"""
        if not returns:
            return 0.0
        cumulative = 1.0
        for r in returns:
            cumulative *= 1 + r
        return (cumulative - 1) * 100

    def _calculate_annualized_return(self, returns: list[float]) -> float:
        """计算年化收益率"""
        if not returns:
            return 0.0
        total_return = self._calculate_total_return(returns) / 100
        n_years = len(returns) / self.TRADING_DAYS_PER_YEAR
        if n_years <= 0:
            return 0.0
        return float(((1 + total_return) ** (1 / n_years) - 1) * 100)

    def _calculate_volatility(self, returns: list[float]) -> float:
        """计算波动率（年化）"""
        if len(returns) < 2:
            return 0.0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        daily_vol = math.sqrt(variance)
        return daily_vol * math.sqrt(self.TRADING_DAYS_PER_YEAR) * 100

    def _calculate_sharpe_ratio(self, returns: list[float], volatility: float) -> float:
        """计算夏普比率"""
        if volatility == 0:
            return 0.0
        annualized_return = self._calculate_annualized_return(returns) / 100
        return (annualized_return - self.risk_free_rate) / (volatility / 100)

    def _calculate_max_drawdown(self, returns: list[float]) -> float:
        """计算最大回撤"""
        if not returns:
            return 0.0

        cumulative = 1.0
        peak = 1.0
        max_dd = 0.0

        for r in returns:
            cumulative *= 1 + r
            if cumulative > peak:
                peak = cumulative
            drawdown = (peak - cumulative) / peak
            if drawdown > max_dd:
                max_dd = drawdown

        return max_dd * 100

    def _calculate_win_rate(self, returns: list[float]) -> float:
        """计算胜率"""
        if not returns:
            return 0.0
        wins = sum(1 for r in returns if r > 0)
        return wins / len(returns) * 100

    def _calculate_profit_loss_ratio(self, returns: list[float]) -> float:
        """计算盈亏比"""
        profits = [r for r in returns if r > 0]
        losses = [abs(r) for r in returns if r < 0]

        if not profits or not losses:
            return 0.0

        avg_profit = sum(profits) / len(profits)
        avg_loss = sum(losses) / len(losses)

        if avg_loss == 0:
            return 0.0

        return avg_profit / avg_loss

    def _calculate_calmar_ratio(self, annualized_return: float, max_drawdown: float) -> float:
        """计算卡玛比率"""
        if max_drawdown == 0:
            return 0.0
        return annualized_return / max_drawdown

    def _calculate_sortino_ratio(self, returns: list[float]) -> float:
        """计算索提诺比率"""
        if not returns:
            return 0.0

        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            return float("inf")

        # 计算下行波动率
        mean = sum(returns) / len(returns)
        downside_variance = sum((r - mean) ** 2 for r in negative_returns) / len(negative_returns)
        downside_vol = math.sqrt(downside_variance) * math.sqrt(self.TRADING_DAYS_PER_YEAR)

        if downside_vol == 0:
            return 0.0

        annualized_return = self._calculate_annualized_return(returns) / 100
        return (annualized_return - self.risk_free_rate) / downside_vol

    def _calculate_var(self, returns: list[float], confidence: float) -> float:
        """计算 VaR（历史模拟法）"""
        if not returns:
            return 0.0
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return abs(sorted_returns[index]) * 100

    def _calculate_expected_shortfall(self, returns: list[float], confidence: float) -> float:
        """计算预期亏损（CVaR）"""
        if not returns:
            return 0.0
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        tail_returns = sorted_returns[: index + 1]
        return abs(sum(tail_returns) / len(tail_returns)) * 100

    def _calculate_beta(self, returns: list[float], benchmark_returns: list[float]) -> float:
        """计算贝塔系数"""
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return 1.0

        mean_r = sum(returns) / len(returns)
        mean_b = sum(benchmark_returns) / len(benchmark_returns)

        covariance = sum((r - mean_r) * (b - mean_b) for r, b in zip(returns, benchmark_returns, strict=False)) / (
            len(returns) - 1
        )
        benchmark_variance = sum((b - mean_b) ** 2 for b in benchmark_returns) / (len(benchmark_returns) - 1)

        if benchmark_variance == 0:
            return 1.0

        return covariance / benchmark_variance

    def _calculate_tracking_error(self, returns: list[float], benchmark_returns: list[float]) -> float:
        """计算跟踪误差"""
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return 0.0

        differences = [r - b for r, b in zip(returns, benchmark_returns, strict=False)]
        mean_diff = sum(differences) / len(differences)
        variance = sum((d - mean_diff) ** 2 for d in differences) / (len(differences) - 1)

        return math.sqrt(variance) * math.sqrt(self.TRADING_DAYS_PER_YEAR) * 100

    def _calculate_information_ratio(self, returns: list[float], benchmark_returns: list[float]) -> float:
        """计算信息比率"""
        tracking_error = self._calculate_tracking_error(returns, benchmark_returns)
        if tracking_error == 0:
            return 0.0

        excess_return = (sum(returns) - sum(benchmark_returns)) / len(returns) * self.TRADING_DAYS_PER_YEAR * 100
        return excess_return / tracking_error

    def generate_report(
        self,
        returns: list[float],
        benchmark_returns: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        生成完整的分析报告

        Args:
            returns: 收益率序列
            benchmark_returns: 基准收益率序列（可选）

        Returns:
            分析报告字典
        """
        metrics = self.calculate_metrics(returns, benchmark_returns)
        risk_metrics = self.calculate_risk_metrics(returns, benchmark_returns)

        return {
            "performance": {
                "total_return": f"{metrics.total_return:.2f}%",
                "annualized_return": f"{metrics.annualized_return:.2f}%",
                "volatility": f"{metrics.volatility:.2f}%",
                "sharpe_ratio": f"{metrics.sharpe_ratio:.2f}",
                "max_drawdown": f"{metrics.max_drawdown:.2f}%",
                "win_rate": f"{metrics.win_rate:.1f}%",
                "profit_loss_ratio": f"{metrics.profit_loss_ratio:.2f}",
                "calmar_ratio": f"{metrics.calmar_ratio:.2f}",
                "sortino_ratio": f"{metrics.sortino_ratio:.2f}",
            },
            "risk": {
                "var_95": f"{risk_metrics.value_at_risk_95:.2f}%",
                "var_99": f"{risk_metrics.value_at_risk_99:.2f}%",
                "expected_shortfall": f"{risk_metrics.expected_shortfall:.2f}%",
                "beta": f"{risk_metrics.beta:.2f}",
                "tracking_error": f"{risk_metrics.tracking_error:.2f}%",
                "information_ratio": f"{risk_metrics.information_ratio:.2f}",
            },
            "evaluation": self._generate_evaluation(metrics, risk_metrics),
        }

    def _generate_evaluation(self, metrics: PortfolioMetrics, risk_metrics: RiskMetrics) -> str:
        """生成评价"""
        evaluations = []

        # 收益评价
        if metrics.annualized_return > 10:
            evaluations.append("收益率优秀")
        elif metrics.annualized_return > 5:
            evaluations.append("收益率良好")
        elif metrics.annualized_return > 2:
            evaluations.append("收益率一般")
        else:
            evaluations.append("收益率较低")

        # 风险评价
        if metrics.volatility < 10:
            evaluations.append("波动率低")
        elif metrics.volatility < 20:
            evaluations.append("波动率适中")
        else:
            evaluations.append("波动率较高")

        # 夏普比率评价
        if metrics.sharpe_ratio > 1:
            evaluations.append("风险调整后收益优秀")
        elif metrics.sharpe_ratio > 0.5:
            evaluations.append("风险调整后收益良好")
        else:
            evaluations.append("风险调整后收益一般")

        # 回撤评价
        if metrics.max_drawdown < 10:
            evaluations.append("回撤控制良好")
        elif metrics.max_drawdown < 20:
            evaluations.append("回撤适中")
        else:
            evaluations.append("回撤较大")

        return "；".join(evaluations)


portfolio_analytics = PortfolioAnalytics()
