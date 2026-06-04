"""
Intelligent recommendation system for asset-lens.
智能推荐系统 - 基于历史表现和市场环境提供投资建议

功能:
1. 基于历史表现推荐策略
2. 基于市场环境推荐股票
3. 综合评分和排序
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..config import config
from .providers.cache import UnifiedCache

logger = logging.getLogger(__name__)


@dataclass
class StrategyRecommendation:
    """策略推荐结果"""

    strategy_name: str
    score: float
    reason: str
    expected_return: float
    risk_level: str
    confidence: float
    historical_performance: dict[str, Any]


@dataclass
class StockRecommendation:
    """股票推荐结果"""

    code: str
    name: str
    score: float
    reason: str
    strategy_match: list[str]
    risk_level: str
    confidence: float
    indicators: dict[str, Any]


class IntelligentRecommender:
    """智能推荐引擎"""

    def __init__(self):
        self.cache_path = config.cache_path
        self.recommendation_path = self.cache_path / "recommendations"
        self.recommendation_path.mkdir(parents=True, exist_ok=True)
        self._cache = UnifiedCache(cache_dir=self.recommendation_path)

    def recommend_strategy(
        self,
        historical_data: dict[str, list[dict[str, Any]]] | None = None,
        market_environment: dict[str, Any] | None = None,
        risk_preference: str = "moderate",
        investment_period: str = "medium",
    ) -> list[StrategyRecommendation]:
        """
        基于历史表现推荐策略

        Args:
            historical_data: 历史数据
            market_environment: 市场环境数据
            risk_preference: 风险偏好 (conservative, moderate, aggressive)
            investment_period: 投资周期 (short, medium, long)

        Returns:
            策略推荐列表
        """
        from ..strategy.engine import strategy_engine

        strategies = strategy_engine.list_strategies()
        recommendations = []

        for strategy_info in strategies:
            strategy_name = strategy_info["name"]

            score = self._calculate_strategy_score(
                strategy_name,
                historical_data,
                market_environment,
                risk_preference,
                investment_period,
            )

            if score["total_score"] < 30:
                continue

            expected_return = score.get("expected_return", 0)
            risk_level = score.get("risk_level", "medium")
            confidence = score.get("confidence", 0.5)

            reason = self._generate_strategy_reason(
                strategy_name,
                score,
                market_environment,
            )

            recommendations.append(
                StrategyRecommendation(
                    strategy_name=strategy_name,
                    score=score["total_score"],
                    reason=reason,
                    expected_return=expected_return,
                    risk_level=risk_level,
                    confidence=confidence,
                    historical_performance=score.get("performance", {}),
                )
            )

        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:5]

    def recommend_stocks(
        self,
        market_environment: dict[str, Any] | None = None,
        strategy_name: str | None = None,
        max_stocks: int = 20,
        min_score: float = 60,
    ) -> list[StockRecommendation]:
        """
        基于市场环境推荐股票

        Args:
            market_environment: 市场环境数据
            strategy_name: 策略名称
            max_stocks: 最大推荐数量
            min_score: 最小评分

        Returns:
            股票推荐列表
        """
        from ..strategy.screener import stock_screener
        from .market_stock_fetcher import market_stock_fetcher

        stocks = market_stock_fetcher.get_cached_market_stocks()
        if not stocks:
            stocks = stock_screener._load_market_stocks()

        if not stocks:
            return []

        if market_environment is None:
            market_environment = self._get_market_environment()

        recommendations = []

        for stock in stocks[:200]:
            code = stock.get("code", "")
            name = stock.get("name", "")

            score = self._calculate_stock_score(
                stock,
                market_environment,
                strategy_name,
            )

            if score["total_score"] < min_score:
                continue

            strategy_match = score.get("strategy_match", [])
            risk_level = score.get("risk_level", "medium")
            confidence = score.get("confidence", 0.5)

            reason = self._generate_stock_reason(
                stock,
                score,
                market_environment,
            )

            recommendations.append(
                StockRecommendation(
                    code=code,
                    name=name,
                    score=score["total_score"],
                    reason=reason,
                    strategy_match=strategy_match,
                    risk_level=risk_level,
                    confidence=confidence,
                    indicators=score.get("indicators", {}),
                )
            )

        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:max_stocks]

    def _calculate_strategy_score(
        self,
        strategy_name: str,
        historical_data: dict[str, list[dict[str, Any]]] | None,
        market_environment: dict[str, Any] | None,
        risk_preference: str,
        investment_period: str,
    ) -> dict[str, Any]:
        """计算策略评分"""
        from ..strategy.engine import strategy_engine

        strategy = strategy_engine.get_strategy(strategy_name)
        if not strategy:
            return {"total_score": 0}

        score: float = 0.0
        performance: dict[str, Any] = {}

        if historical_data:
            try:
                validation = strategy_engine.validate_strategy(  # type: ignore[call-arg]
                    strategy_name,  # type: ignore[arg-type]
                    historical_data,
                )

                if validation.get("valid"):
                    win_rate = validation.get("win_rate", 0)
                    total_return = validation.get("total_return", 0)
                    sharpe_ratio = validation.get("sharpe_ratio", 0)

                    score += min(win_rate * 30, 30)
                    score += min(max(total_return * 100, 0), 30)
                    score += min(max(sharpe_ratio * 10, 0), 20)

                    performance = {
                        "win_rate": win_rate,
                        "total_return": total_return,
                        "sharpe_ratio": sharpe_ratio,
                        "max_drawdown": validation.get("max_drawdown", 0),
                    }

            except (ValueError, KeyError, TypeError) as e:
                logger.debug(f"忽略异常: {e}")

        risk_score = self._calculate_risk_compatibility(
            strategy,
            risk_preference,
        )
        score += risk_score

        period_score = self._calculate_period_compatibility(
            strategy,
            investment_period,
        )
        score += period_score

        if market_environment:
            env_score = self._calculate_environment_compatibility(
                strategy,
                market_environment,
            )
            score += env_score

        return {
            "total_score": min(score, 100),
            "expected_return": performance.get("total_return", 0),
            "risk_level": self._assess_strategy_risk(strategy),
            "confidence": min(score / 100, 1.0),
            "performance": performance,
        }

    def _calculate_stock_score(
        self,
        stock: dict[str, Any],
        market_environment: dict[str, Any],
        strategy_name: str | None,
    ) -> dict[str, Any]:
        """计算股票评分"""
        from ..strategy.engine import strategy_engine

        score = 0
        strategy_match = []
        indicators = {}

        change_percent = float(stock.get("change_percent", 0))
        turnover_rate = float(stock.get("turnover_rate", 0))
        pe_ratio = float(stock.get("pe_ratio", 0)) if stock.get("pe_ratio") else 0
        pb_ratio = float(stock.get("pb_ratio", 0)) if stock.get("pb_ratio") else 0

        indicators = {
            "change_percent": change_percent,
            "turnover_rate": turnover_rate,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
        }

        if strategy_name:
            evaluation = strategy_engine.evaluate_stock(stock, strategy_name)
            if evaluation.get("match"):
                score += evaluation.get("score", 0) * 0.5
                strategy_match.append(strategy_name)

        market_type = market_environment.get("market_type", "震荡")
        if market_type == "牛市":
            if change_percent > 0:
                score += 15
            if turnover_rate > 5:
                score += 10
        elif market_type == "熊市":
            if change_percent < 0:
                score += 5
            if pe_ratio > 0 and pe_ratio < 20:
                score += 15
        else:
            if abs(change_percent) < 3:
                score += 10
            if pe_ratio > 0 and pe_ratio < 30:
                score += 10

        if pe_ratio > 0 and pe_ratio < 15:
            score += 10
        elif pe_ratio > 0 and pe_ratio < 30:
            score += 5

        if pb_ratio > 0 and pb_ratio < 2:
            score += 10
        elif pb_ratio > 0 and pb_ratio < 3:
            score += 5

        risk_level = "low"
        if pe_ratio > 50 or pb_ratio > 5:
            risk_level = "high"
        elif pe_ratio > 30 or pb_ratio > 3:
            risk_level = "medium"

        return {
            "total_score": min(score, 100),
            "strategy_match": strategy_match,
            "risk_level": risk_level,
            "confidence": min(score / 100, 1.0),
            "indicators": indicators,
        }

    def _calculate_risk_compatibility(
        self,
        strategy: Any,
        risk_preference: str,
    ) -> float:
        """计算风险兼容性评分"""
        score: float = 0.0

        if risk_preference == "conservative":
            if strategy.stop_loss and strategy.stop_loss > -0.08:
                score += 10
            if strategy.take_profit and strategy.take_profit < 0.15:
                score += 10
            if strategy.max_positions and strategy.max_positions <= 5:
                score += 10

        elif risk_preference == "moderate":
            if strategy.stop_loss and -0.15 < strategy.stop_loss <= -0.05:
                score += 10
            if strategy.take_profit and 0.1 <= strategy.take_profit <= 0.25:
                score += 10
            if strategy.max_positions and 5 <= strategy.max_positions <= 10:
                score += 10

        elif risk_preference == "aggressive":
            if strategy.stop_loss and strategy.stop_loss <= -0.1:
                score += 10
            if strategy.take_profit and strategy.take_profit >= 0.2:
                score += 10
            if strategy.max_positions and strategy.max_positions >= 10:
                score += 10

        return score

    def _calculate_period_compatibility(
        self,
        strategy: Any,
        investment_period: str,
    ) -> float:
        """计算投资周期兼容性评分"""
        score: float = 0.0

        if investment_period == "short":
            if strategy.holding_period_max and strategy.holding_period_max <= 10:
                score += 15
            elif strategy.holding_period_max and strategy.holding_period_max <= 20:
                score += 10

        elif investment_period == "medium":
            if strategy.holding_period_max and 10 <= strategy.holding_period_max <= 30:
                score += 15
            elif strategy.holding_period_max and 20 <= strategy.holding_period_max <= 40:
                score += 10

        elif investment_period == "long":
            if strategy.holding_period_max and strategy.holding_period_max >= 30:
                score += 15
            elif strategy.holding_period_max and strategy.holding_period_max >= 20:
                score += 10

        return score

    def _calculate_environment_compatibility(
        self,
        strategy: Any,
        market_environment: dict[str, Any],
    ) -> float:
        """计算市场环境兼容性评分"""
        score: float = 0.0

        market_type = market_environment.get("market_type", "震荡")
        sentiment = market_environment.get("sentiment", "neutral")

        strategy_name = strategy.name.lower()

        if market_type == "牛市":
            if "momentum" in strategy_name or "动量" in strategy_name:
                score += 15
            if "growth" in strategy_name or "成长" in strategy_name:
                score += 10

        elif market_type == "熊市":
            if "value" in strategy_name or "价值" in strategy_name:
                score += 15
            if "dividend" in strategy_name or "红利" in strategy_name:
                score += 10

        else:
            if "reversal" in strategy_name or "反转" in strategy_name:
                score += 15
            if "value" in strategy_name or "价值" in strategy_name:
                score += 10

        if sentiment == "bullish":
            if "momentum" in strategy_name:
                score += 5
        elif sentiment == "bearish" and ("value" in strategy_name or "dividend" in strategy_name):
            score += 5

        return score

    def _assess_strategy_risk(self, strategy: Any) -> str:
        """评估策略风险等级"""
        risk_score = 0

        if strategy.stop_loss:
            if strategy.stop_loss > -0.05:
                risk_score += 1
            elif strategy.stop_loss < -0.15:
                risk_score += 3

        if strategy.take_profit and strategy.take_profit > 0.3:
            risk_score += 2

        if strategy.max_positions and strategy.max_positions > 10:
            risk_score += 2

        if risk_score >= 5:
            return "high"
        elif risk_score >= 3:
            return "medium"
        else:
            return "low"

    def _generate_strategy_reason(
        self,
        strategy_name: str,
        score: dict[str, Any],
        market_environment: dict[str, Any] | None,
    ) -> str:
        """生成策略推荐原因"""
        reasons = []

        performance = score.get("performance", {})
        if performance.get("win_rate", 0) > 0.5:
            reasons.append(f"历史胜率较高 ({performance['win_rate']:.1%})")
        if performance.get("total_return", 0) > 0.1:
            reasons.append(f"历史收益良好 ({performance['total_return']:.1%})")

        if market_environment:
            market_type = market_environment.get("market_type", "震荡")
            reasons.append(f"适合{market_type}市场环境")

        if not reasons:
            reasons.append("综合评分较高")

        return "；".join(reasons)

    def _generate_stock_reason(
        self,
        stock: dict[str, Any],
        score: dict[str, Any],
        market_environment: dict[str, Any],
    ) -> str:
        """生成股票推荐原因"""
        reasons = []

        indicators = score.get("indicators", {})
        pe_ratio = indicators.get("pe_ratio", 0)
        pb_ratio = indicators.get("pb_ratio", 0)

        if pe_ratio > 0 and pe_ratio < 15:
            reasons.append(f"估值较低 (PE: {pe_ratio:.1f})")
        if pb_ratio > 0 and pb_ratio < 2:
            reasons.append(f"市净率合理 (PB: {pb_ratio:.1f})")

        if score.get("strategy_match"):
            reasons.append(f"匹配策略: {', '.join(score['strategy_match'])}")

        if not reasons:
            reasons.append("综合评分较高")

        return "；".join(reasons)

    def _get_market_environment(self) -> dict[str, Any]:
        """获取市场环境"""
        from .market_environment import market_environment_analyzer

        try:
            env = market_environment_analyzer.analyze_environment()
            return {
                "market_type": env.market_type,
                "risk_level": env.risk_level,
                "sentiment": env.sentiment,
            }
        except (ValueError, KeyError, ConnectionError) as e:
            logger.debug(f"忽略异常: {e}")
            return {
                "market_type": "震荡",
                "risk_level": "medium",
                "sentiment": "neutral",
            }

    def save_recommendations(
        self,
        recommendations: list[Any],
        filename: str | None = None,
    ) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recommendations_{timestamp}.json"

        data = {
            "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "recommendations": [
                {
                    "type": type(r).__name__,
                    **dict(r.__dict__.items()),
                }
                for r in recommendations
            ],
        }

        self._cache.save_file(filename, data, ttl=0)

        return str(self.recommendation_path / filename)


intelligent_recommender = IntelligentRecommender()
