"""
Strategy portfolio evaluation for asset-lens.
策略组合评估模块
"""

from typing import Any


class StrategyPortfolioEvaluator:
    """策略组合评估器"""

    def __init__(self, strategy_engine):
        self.engine = strategy_engine

    def evaluate_strategy_portfolio(
        self,
        stock: dict[str, Any],
        strategy_weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """
        使用策略组合评估股票

        Args:
            stock: 股票数据
            strategy_weights: 策略权重字典 {"value": 0.4, "momentum": 0.3, ...}

        Returns:
            组合评分结果
        """
        if strategy_weights is None:
            strategy_weights = {
                "value": 0.3,
                "momentum": 0.25,
                "reversal": 0.2,
                "dividend": 0.25,
            }

        total_weight = sum(strategy_weights.values())
        if total_weight == 0:
            return {"combined_score": 0, "strategies": {}}

        normalized_weights = {k: v / total_weight for k, v in strategy_weights.items()}

        strategy_scores: dict[str, dict[str, Any]] = {}
        weighted_score = 0.0

        for strategy_name, weight in normalized_weights.items():
            if strategy_name not in self.engine.strategies:
                continue

            evaluation = self.engine.evaluate_stock(stock, strategy_name)
            strategy_scores[strategy_name] = {
                "score": evaluation["score"],
                "match": evaluation["match"],
                "weight": weight,
                "weighted_score": evaluation["score"] * weight,
                "matched_conditions": evaluation["matched_conditions"],
                "total_conditions": evaluation["total_conditions"],
            }

            weighted_score += evaluation["score"] * weight

        sorted_strategies = sorted(
            strategy_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True,
        )

        best_strategy = sorted_strategies[0][0] if sorted_strategies else None

        return {
            "combined_score": weighted_score,
            "strategies": strategy_scores,
            "best_strategy": best_strategy,
            "recommendation": self._get_portfolio_recommendation(weighted_score, best_strategy),
        }

    def _get_portfolio_recommendation(self, combined_score: float, best_strategy: str | None) -> str:
        """获取组合建议"""
        if combined_score >= 0.8:
            return f"强烈推荐买入，最佳策略: {best_strategy}"
        elif combined_score >= 0.6:
            return f"推荐买入，最佳策略: {best_strategy}"
        elif combined_score >= 0.4:
            return f"可以观察，最佳策略: {best_strategy}"
        elif combined_score >= 0.2:
            return f"谨慎观望，最佳策略: {best_strategy}"
        else:
            return "不建议买入"

    def screen_with_portfolio(
        self,
        stocks: list[dict[str, Any]],
        strategy_weights: dict[str, float] | None = None,
        min_combined_score: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        使用策略组合筛选股票

        Args:
            stocks: 股票列表
            strategy_weights: 策略权重
            min_combined_score: 最小组合分数

        Returns:
            筛选结果
        """
        results = []

        for stock in stocks:
            evaluation = self.evaluate_strategy_portfolio(stock, strategy_weights)

            if evaluation["combined_score"] >= min_combined_score:
                results.append(
                    {
                        "code": stock.get("code", ""),
                        "name": stock.get("name", ""),
                        "combined_score": evaluation["combined_score"],
                        "best_strategy": evaluation["best_strategy"],
                        "recommendation": evaluation["recommendation"],
                        "strategy_details": evaluation["strategies"],
                    }
                )

        results.sort(key=lambda x: x["combined_score"], reverse=True)
        return results
