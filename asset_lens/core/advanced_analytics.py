"""
Advanced analytics for investment portfolio.
投资组合高级分析模块
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from ..data.models import InvestmentProduct, Portfolio


@dataclass
class DrawdownResult:
    """回撤结果"""

    max_drawdown: Decimal
    max_drawdown_percent: Decimal
    peak_date: date | None
    trough_date: date | None
    recovery_date: date | None
    drawdown_duration: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "最大回撤金额": str(self.max_drawdown),
            "最大回撤比例": f"{self.max_drawdown_percent:.2f}%",
            "峰值日期": str(self.peak_date) if self.peak_date else "-",
            "谷底日期": str(self.trough_date) if self.trough_date else "-",
            "恢复日期": str(self.recovery_date) if self.recovery_date else "-",
            "回撤持续天数": self.drawdown_duration,
        }


@dataclass
class SharpeResult:
    """夏普比率结果"""

    sharpe_ratio: Decimal
    annualized_return: Decimal
    risk_free_rate: Decimal
    volatility: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "夏普比率": f"{self.sharpe_ratio:.4f}",
            "年化收益率": f"{self.annualized_return:.2f}%",
            "无风险利率": f"{self.risk_free_rate:.2f}%",
            "波动率": f"{self.volatility:.2f}%",
        }


@dataclass
class VolatilityResult:
    """波动率结果"""

    daily_volatility: Decimal
    weekly_volatility: Decimal
    monthly_volatility: Decimal
    annualized_volatility: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "日波动率": f"{self.daily_volatility:.4f}%",
            "周波动率": f"{self.weekly_volatility:.4f}%",
            "月波动率": f"{self.monthly_volatility:.4f}%",
            "年化波动率": f"{self.annualized_volatility:.2f}%",
        }


@dataclass
class PortfolioAnalytics:
    """投资组合分析结果"""

    total_value: Decimal
    total_initial: Decimal
    total_profit: Decimal
    return_rate: Decimal
    max_drawdown: DrawdownResult | None
    sharpe_ratio: SharpeResult | None
    volatility: VolatilityResult | None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "总资产": str(self.total_value),
            "总成本": str(self.total_initial),
            "总收益": str(self.total_profit),
            "收益率": f"{self.return_rate:.2f}%",
        }
        if self.max_drawdown:
            result["回撤分析"] = self.max_drawdown.to_dict()
        if self.sharpe_ratio:
            result["夏普分析"] = self.sharpe_ratio.to_dict()
        if self.volatility:
            result["波动率分析"] = self.volatility.to_dict()
        return result


class AdvancedAnalytics:
    """高级分析器"""

    RISK_FREE_RATE = Decimal("3.0")

    TRADING_DAYS_PER_YEAR = 252

    def __init__(self, risk_free_rate: Decimal | None = None):
        self.risk_free_rate = risk_free_rate or self.RISK_FREE_RATE

    def calculate_max_drawdown(
        self,
        values: list[Decimal],
        dates: list[date] | None = None,
    ) -> DrawdownResult:
        if not values or len(values) < 2:
            return DrawdownResult(
                max_drawdown=Decimal("0"),
                max_drawdown_percent=Decimal("0"),
                peak_date=None,
                trough_date=None,
                recovery_date=None,
                drawdown_duration=0,
            )

        peak = values[0]
        peak_idx = 0
        max_drawdown = Decimal("0")
        max_drawdown_percent = Decimal("0")
        trough_idx = 0
        peak_for_max = 0

        for i, value in enumerate(values):
            if value > peak:
                peak = value
                peak_idx = i

            drawdown = peak - value
            if peak > 0:
                drawdown_percent = (drawdown / peak) * 100
            else:
                drawdown_percent = Decimal("0")

            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_percent = drawdown_percent
                trough_idx = i
                peak_for_max = peak_idx

        recovery_idx = None
        if trough_idx < len(values) - 1:
            peak_value = values[peak_for_max]
            for i in range(trough_idx + 1, len(values)):
                if values[i] >= peak_value:
                    recovery_idx = i
                    break

        peak_date = dates[peak_for_max] if dates and peak_for_max < len(dates) else None
        trough_date = dates[trough_idx] if dates and trough_idx < len(dates) else None
        recovery_date = dates[recovery_idx] if dates and recovery_idx and recovery_idx < len(dates) else None

        if trough_date and recovery_date:
            drawdown_duration = (recovery_date - trough_date).days
        elif trough_date:
            drawdown_duration = (date.today() - trough_date).days
        else:
            drawdown_duration = 0

        return DrawdownResult(
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            peak_date=peak_date,
            trough_date=trough_date,
            recovery_date=recovery_date,
            drawdown_duration=drawdown_duration,
        )

    def calculate_sharpe_ratio(
        self,
        returns: list[Decimal],
        annualized: bool = True,
    ) -> SharpeResult:
        if not returns or len(returns) < 2:
            return SharpeResult(
                sharpe_ratio=Decimal("0"),
                annualized_return=Decimal("0"),
                risk_free_rate=self.risk_free_rate,
                volatility=Decimal("0"),
            )

        avg_return = sum(returns) / len(returns)

        variance = Decimal(str(sum((float(r) - float(avg_return)) ** 2 for r in returns))) / Decimal(str(len(returns)))
        std_dev = Decimal(str(float(variance) ** 0.5)) if variance > 0 else Decimal("0")

        if annualized:
            annualized_return = avg_return * self.TRADING_DAYS_PER_YEAR
            annualized_std = std_dev * Decimal(str(self.TRADING_DAYS_PER_YEAR**0.5))
        else:
            annualized_return = avg_return
            annualized_std = std_dev

        self.risk_free_rate / self.TRADING_DAYS_PER_YEAR

        if annualized_std > 0:
            excess_return = Decimal(str(annualized_return)) - self.risk_free_rate
            sharpe_ratio = excess_return / annualized_std
        else:
            sharpe_ratio = Decimal("0")

        return SharpeResult(
            sharpe_ratio=sharpe_ratio,
            annualized_return=Decimal(str(annualized_return)),
            risk_free_rate=self.risk_free_rate,
            volatility=annualized_std,
        )

    def calculate_volatility(
        self,
        returns: list[Decimal],
    ) -> VolatilityResult:
        if not returns or len(returns) < 2:
            return VolatilityResult(
                daily_volatility=Decimal("0"),
                weekly_volatility=Decimal("0"),
                monthly_volatility=Decimal("0"),
                annualized_volatility=Decimal("0"),
            )

        avg_return = sum(returns) / len(returns)
        variance = Decimal(str(sum((float(r) - float(avg_return)) ** 2 for r in returns))) / Decimal(str(len(returns)))
        daily_vol = Decimal(str(float(variance) ** 0.5)) if variance > 0 else Decimal("0")

        weekly_vol = daily_vol * Decimal(str(5**0.5))
        monthly_vol = daily_vol * Decimal(str(21**0.5))
        annual_vol = daily_vol * Decimal(str(self.TRADING_DAYS_PER_YEAR**0.5))

        return VolatilityResult(
            daily_volatility=daily_vol,
            weekly_volatility=weekly_vol,
            monthly_volatility=monthly_vol,
            annualized_volatility=annual_vol,
        )

    def calculate_returns_from_values(
        self,
        values: list[Decimal],
    ) -> list[Decimal]:
        if not values or len(values) < 2:
            return []

        returns = []
        for i in range(1, len(values)):
            if values[i - 1] > 0:
                ret = ((values[i] - values[i - 1]) / values[i - 1]) * 100
                returns.append(ret)
            else:
                returns.append(Decimal("0"))

        return returns

    def analyze_portfolio(
        self,
        portfolio: Portfolio,
        historical_values: list[Decimal] | None = None,
        historical_dates: list[date] | None = None,
    ) -> PortfolioAnalytics:
        total_value = portfolio.total_value or Decimal("0")
        total_initial = portfolio.total_initial or Decimal("0")
        total_profit = portfolio.total_profit or Decimal("0")

        if total_initial > 0:
            return_rate = (total_profit / total_initial) * 100
        else:
            return_rate = Decimal("0")

        max_drawdown = None
        sharpe_ratio = None
        volatility = None

        if historical_values and len(historical_values) >= 2:
            max_drawdown = self.calculate_max_drawdown(historical_values, historical_dates)

            returns = self.calculate_returns_from_values(historical_values)
            if returns:
                sharpe_ratio = self.calculate_sharpe_ratio(returns)
                volatility = self.calculate_volatility(returns)

        return PortfolioAnalytics(
            total_value=total_value,
            total_initial=total_initial,
            total_profit=total_profit,
            return_rate=return_rate,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
        )

    def analyze_product(
        self,
        product: InvestmentProduct,
        historical_values: list[Decimal] | None = None,
        historical_dates: list[date] | None = None,
    ) -> dict[str, Any]:
        current_amount = product.current_amount or Decimal("0")
        initial_amount = product.initial_amount or Decimal("0")
        profit_amount = product.profit_amount or Decimal("0")

        if initial_amount > 0:
            return_rate = (profit_amount / initial_amount) * 100
        elif current_amount > 0:
            return_rate = Decimal("0")
        else:
            return_rate = Decimal("0")

        result = {
            "名称": product.name,
            "类型": product.investment_type.value,
            "风险等级": product.risk_level.value if product.risk_level else "-",
            "当前金额": str(current_amount),
            "初始金额": str(initial_amount),
            "收益金额": str(profit_amount),
            "收益率": f"{return_rate:.2f}%",
        }

        if historical_values and len(historical_values) >= 2:
            drawdown = self.calculate_max_drawdown(historical_values, historical_dates)
            result["最大回撤"] = f"{drawdown.max_drawdown_percent:.2f}%"

            returns = self.calculate_returns_from_values(historical_values)
            if returns:
                sharpe = self.calculate_sharpe_ratio(returns)
                result["夏普比率"] = f"{sharpe.sharpe_ratio:.4f}"

                vol = self.calculate_volatility(returns)
                result["年化波动率"] = f"{vol.annualized_volatility:.2f}%"

        return result

    def calculate_correlation(
        self,
        returns1: list[Decimal],
        returns2: list[Decimal],
    ) -> Decimal:
        if not returns1 or not returns2 or len(returns1) != len(returns2):
            return Decimal("0")

        n = len(returns1)
        if n < 2:
            return Decimal("0")

        avg1 = sum(returns1) / n
        avg2 = sum(returns2) / n

        cov = Decimal(
            str(
                sum(
                    (float(r1) - float(avg1)) * (float(r2) - float(avg2))
                    for r1, r2 in zip(returns1, returns2, strict=False)
                )
            )
        ) / Decimal(str(n))

        var1 = Decimal(str(sum((float(r) - float(avg1)) ** 2 for r in returns1))) / Decimal(str(n))
        var2 = Decimal(str(sum((float(r) - float(avg2)) ** 2 for r in returns2))) / Decimal(str(n))

        std1 = Decimal(str(float(var1) ** 0.5)) if var1 > 0 else Decimal("0")
        std2 = Decimal(str(float(var2) ** 0.5)) if var2 > 0 else Decimal("0")

        if std1 > 0 and std2 > 0:
            correlation = cov / (std1 * std2)
        else:
            correlation = Decimal("0")

        return correlation

    def calculate_beta(
        self,
        portfolio_returns: list[Decimal],
        market_returns: list[Decimal],
    ) -> Decimal:
        if not portfolio_returns or not market_returns or len(portfolio_returns) != len(market_returns):
            return Decimal("0")

        n = len(portfolio_returns)
        if n < 2:
            return Decimal("0")

        avg_portfolio = sum(portfolio_returns) / n
        avg_market = sum(market_returns) / n

        cov = Decimal(
            str(
                sum(
                    (float(pr) - float(avg_portfolio)) * (float(mr) - float(avg_market))
                    for pr, mr in zip(portfolio_returns, market_returns, strict=False)
                )
            )
        ) / Decimal(str(n))

        var_market = Decimal(str(sum((float(r) - float(avg_market)) ** 2 for r in market_returns))) / Decimal(str(n))

        if var_market > 0:
            beta = cov / var_market
        else:
            beta = Decimal("0")

        return beta

    def calculate_alpha(
        self,
        portfolio_return: Decimal,
        market_return: Decimal,
        beta: Decimal,
    ) -> Decimal:
        alpha = portfolio_return - (self.risk_free_rate + beta * (market_return - self.risk_free_rate))
        return alpha


advanced_analytics = AdvancedAnalytics()
