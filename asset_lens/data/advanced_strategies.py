"""
Advanced Stock Screening Strategies.
高级选股策略

包含多种选股策略：
1. 动量策略 - 追涨杀跌
2. 均值回归策略 - 低买高卖
3. 突破策略 - 放量突破
4. 价值策略 - 低估值
5. 成长策略 - 高增长
6. 质量策略 - 高质量
7. 技术策略 - 技术指标
8. 组合策略 - 多因子
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ScreeningResult:
    """筛选结果"""
    code: str
    name: str
    score: float
    strategy: str
    reasons: list[str]
    data: dict[str, Any]


class AdvancedStrategies:
    """高级选股策略"""

    @staticmethod
    def momentum_strategy(
        prices: list[float],
        volumes: list[float],
        period: int = 20,
        min_momentum: float = 0.05,
    ) -> dict[str, Any] | None:
        """
        动量策略
        
        选股条件：
        1. 价格突破 N 日均线
        2. 成交量放大
        3. 动量 > 阈值
        """
        if len(prices) < period:
            return None

        ma = sum(prices[-period:]) / period
        current_price = prices[-1]
        prev_price = prices[-period]

        momentum = (current_price - prev_price) / prev_price

        avg_volume = sum(volumes[-period:]) / period
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        passed = (
            current_price > ma and
            momentum > min_momentum and
            volume_ratio > 1.5
        )

        return {
            "passed": passed,
            "momentum": round(momentum * 100, 2),
            "volume_ratio": round(volume_ratio, 2),
            "price_vs_ma": round((current_price / ma - 1) * 100, 2),
        }

    @staticmethod
    def mean_reversion_strategy(
        prices: list[float],
        period: int = 20,
        oversold_threshold: float = -0.1,
    ) -> dict[str, Any] | None:
        """
        均值回归策略
        
        选股条件：
        1. 价格低于均线
        2. 超卖区域
        3. 可能反弹
        """
        if len(prices) < period:
            return None

        ma = sum(prices[-period:]) / period
        current_price = prices[-1]

        deviation = (current_price - ma) / ma

        passed = deviation < oversold_threshold

        return {
            "passed": passed,
            "deviation": round(deviation * 100, 2),
            "ma": round(ma, 2),
            "current_price": current_price,
        }

    @staticmethod
    def breakout_strategy(
        prices: list[float],
        volumes: list[float],
        high_prices: list[float],
        period: int = 20,
        volume_threshold: float = 2.0,
    ) -> dict[str, Any] | None:
        """
        突破策略
        
        选股条件：
        1. 价格突破 N 日高点
        2. 成交量放大
        3. 确认突破
        """
        if len(prices) < period:
            return None

        current_price = prices[-1]
        period_high = max(high_prices[-period:])

        avg_volume = sum(volumes[-period:]) / period
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        passed = (
            current_price > period_high and
            volume_ratio > volume_threshold
        )

        return {
            "passed": passed,
            "breakout_level": round(period_high, 2),
            "volume_ratio": round(volume_ratio, 2),
            "breakout_pct": round((current_price / period_high - 1) * 100, 2),
        }

    @staticmethod
    def value_strategy(
        pe_ratio: float | None = None,
        pb_ratio: float | None = None,
        dividend_yield: float | None = None,
        max_pe: float = 15.0,
        max_pb: float = 2.0,
        min_dividend: float = 0.03,
    ) -> dict[str, Any]:
        """
        价值策略
        
        选股条件：
        1. 低市盈率
        2. 低市净率
        3. 高股息率
        """
        scores = []
        reasons = []

        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio < max_pe:
                scores.append(1 - pe_ratio / max_pe)
                reasons.append(f"PE={pe_ratio:.1f} < {max_pe}")

        if pb_ratio is not None and pb_ratio > 0:
            if pb_ratio < max_pb:
                scores.append(1 - pb_ratio / max_pb)
                reasons.append(f"PB={pb_ratio:.1f} < {max_pb}")

        if dividend_yield is not None:
            if dividend_yield > min_dividend:
                scores.append(dividend_yield / min_dividend - 1)
                reasons.append(f"股息率={dividend_yield*100:.1f}% > {min_dividend*100:.0f}%")

        passed = len(scores) >= 2
        score = sum(scores) / len(scores) if scores else 0

        return {
            "passed": passed,
            "score": round(score, 2),
            "reasons": reasons,
        }

    @staticmethod
    def growth_strategy(
        revenue_growth: float | None = None,
        profit_growth: float | None = None,
        min_revenue_growth: float = 0.2,
        min_profit_growth: float = 0.15,
    ) -> dict[str, Any]:
        """
        成长策略
        
        选股条件：
        1. 营收增长 > 阈值
        2. 利润增长 > 阈值
        """
        scores = []
        reasons = []

        if revenue_growth is not None:
            if revenue_growth > min_revenue_growth:
                scores.append(revenue_growth / min_revenue_growth)
                reasons.append(f"营收增长={revenue_growth*100:.1f}%")

        if profit_growth is not None:
            if profit_growth > min_profit_growth:
                scores.append(profit_growth / min_profit_growth)
                reasons.append(f"利润增长={profit_growth*100:.1f}%")

        passed = len(scores) >= 1
        score = sum(scores) / len(scores) if scores else 0

        return {
            "passed": passed,
            "score": round(score, 2),
            "reasons": reasons,
        }

    @staticmethod
    def quality_strategy(
        roe: float | None = None,
        debt_ratio: float | None = None,
        current_ratio: float | None = None,
        min_roe: float = 0.15,
        max_debt: float = 0.6,
        min_current: float = 1.5,
    ) -> dict[str, Any]:
        """
        质量策略
        
        选股条件：
        1. 高 ROE
        2. 低负债率
        3. 高流动比率
        """
        scores = []
        reasons = []

        if roe is not None and roe > 0:
            if roe > min_roe:
                scores.append(roe / min_roe)
                reasons.append(f"ROE={roe*100:.1f}%")

        if debt_ratio is not None:
            if debt_ratio < max_debt:
                scores.append(1 - debt_ratio / max_debt)
                reasons.append(f"负债率={debt_ratio*100:.1f}%")

        if current_ratio is not None:
            if current_ratio > min_current:
                scores.append(current_ratio / min_current)
                reasons.append(f"流动比率={current_ratio:.1f}")

        passed = len(scores) >= 2
        score = sum(scores) / len(scores) if scores else 0

        return {
            "passed": passed,
            "score": round(score, 2),
            "reasons": reasons,
        }

    @staticmethod
    def technical_strategy(
        rsi: float | None = None,
        macd_signal: str | None = None,
        boll_position: str | None = None,
    ) -> dict[str, Any]:
        """
        技术策略
        
        选股条件：
        1. RSI 超卖
        2. MACD 金叉
        3. 布林带下轨
        """
        scores = []
        reasons = []

        if rsi is not None:
            if rsi < 30:
                scores.append((30 - rsi) / 30)
                reasons.append(f"RSI={rsi:.1f} 超卖")
            elif rsi > 70:
                scores.append((rsi - 70) / 30)
                reasons.append(f"RSI={rsi:.1f} 超买")

        if macd_signal is not None:
            if macd_signal == "golden_cross":
                scores.append(1.0)
                reasons.append("MACD 金叉")

        if boll_position is not None:
            if boll_position == "lower":
                scores.append(1.0)
                reasons.append("触及布林下轨")

        passed = len(scores) >= 1
        score = sum(scores) / len(scores) if scores else 0

        return {
            "passed": passed,
            "score": round(score, 2),
            "reasons": reasons,
        }

    @staticmethod
    def multi_factor_strategy(
        factors: dict[str, float],
        weights: dict[str, float] | None = None,
        min_score: float = 0.6,
    ) -> dict[str, Any]:
        """
        多因子策略
        
        综合多个因子评分
        """
        default_weights = {
            "momentum": 0.2,
            "value": 0.2,
            "growth": 0.2,
            "quality": 0.2,
            "technical": 0.2,
        }

        if weights is None:
            weights = default_weights

        total_score: float = 0
        total_weight: float = 0

        for factor, score in factors.items():
            weight = weights.get(factor, 0.1)
            total_score += score * weight
            total_weight += weight

        final_score = total_score / total_weight if total_weight > 0 else 0

        return {
            "passed": final_score >= min_score,
            "score": round(final_score, 2),
            "factors": factors,
        }


advanced_strategies = AdvancedStrategies()
