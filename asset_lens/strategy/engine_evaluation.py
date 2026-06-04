import logging
from typing import Any

logger = logging.getLogger(__name__)


class StrategyEvaluationMixin:
    def evaluate_stock(self, stock: dict[str, Any], strategy_name: str = "value") -> dict[str, Any]:
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return {"error": f"策略 {strategy_name} 不存在"}

        conditions_met = 0
        total_conditions = len(strategy.buy_conditions)
        details = []

        for condition in strategy.buy_conditions:
            field_name = condition.field
            operator = condition.operator
            target = condition.value
            weight = condition.weight

            value = self._get_field_value(stock, field_name)
            met = self._evaluate_condition(value, operator, target)

            if met:
                conditions_met += weight
            details.append(
                {
                    "field": field_name,
                    "value": value,
                    "operator": operator,
                    "target": target,
                    "met": met,
                    "weight": weight,
                }
            )

        total_weight = sum(c.weight for c in strategy.buy_conditions)
        score = conditions_met / total_weight if total_weight > 0 else 0

        recommendation = "强烈推荐" if score >= 0.8 else "推荐" if score >= 0.6 else "观望" if score >= 0.4 else "不推荐"

        return {
            "stock_code": stock.get("code", ""),
            "stock_name": stock.get("name", ""),
            "strategy": strategy_name,
            "score": round(score, 4),
            "conditions_met": conditions_met,
            "total_conditions": total_weight,
            "recommendation": recommendation,
            "details": details,
        }

    def _get_field_value(self, stock: dict[str, Any], field_name: str) -> Any:
        field_mapping = {
            "pe_ratio": ["pe_ratio", "PE", "市盈率", "pe"],
            "pb_ratio": ["pb_ratio", "PB", "市净率", "pb"],
            "roe": ["roe", "ROE", "净资产收益率"],
            "revenue_growth": ["revenue_growth", "营收增长率", "revenueGrowth"],
            "profit_growth": ["profit_growth", "利润增长率", "profitGrowth"],
            "dividend_yield": ["dividend_yield", "股息率", "dividendYield"],
            "debt_ratio": ["debt_ratio", "负债率", "debtRatio"],
            "current_price": ["current_price", "现价", "price", "close"],
            "market_cap": ["market_cap", "市值", "marketCap"],
            "turnover_rate": ["turnover_rate", "换手率", "turnoverRate"],
            "change_percent": ["change_percent", "涨跌幅", "changePercent"],
            "volume": ["volume", "成交量"],
            "amount": ["amount", "成交额"],
        }

        possible_names = field_mapping.get(field_name, [field_name])

        for name in possible_names:
            if name in stock:
                return stock[name]

        return None

    def _evaluate_condition(self, value: Any, operator: str, target: Any) -> bool:
        if value is None:
            return False

        # Handle between operator separately since target is a list
        if operator == "between":
            try:
                value = float(value)
            except (ValueError, TypeError):
                return False
            if isinstance(target, (list, tuple)) and len(target) == 2:
                try:
                    return float(target[0]) <= value <= float(target[1])
                except (ValueError, TypeError):
                    return False
            return False

        try:
            value = float(value)
            target = float(target)
        except (ValueError, TypeError):
            if operator == "eq":
                return str(value) == str(target)
            elif operator == "ne":
                return str(value) != str(target)
            elif operator == "in":
                return str(value) in str(target).split(",")
            return False

        if operator == "gt":
            return value > target
        elif operator == "gte":
            return value >= target
        elif operator == "lt":
            return value < target
        elif operator == "lte":
            return value <= target
        elif operator == "eq":
            return abs(value - target) < 0.001
        elif operator == "ne":
            return abs(value - target) >= 0.001

        return False

    def screen_stocks(
        self,
        stocks: list[dict[str, Any]],
        strategy_name: str = "value",
        min_score: float = 0.5,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        results = []

        for stock in stocks:
            evaluation = self.evaluate_stock(stock, strategy_name)
            if evaluation.get("score", 0) >= min_score:
                results.append(evaluation)

        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return results[:limit]

    def validate_strategy(
        self,
        strategy: dict[str, Any],
    ) -> dict[str, Any]:
        errors = []
        warnings = []

        if not strategy.get("name"):
            errors.append("策略名称不能为空")

        if not strategy.get("conditions"):
            errors.append("策略条件不能为空")

        for i, condition in enumerate(strategy.get("conditions", [])):
            if not condition.get("field"):
                errors.append(f"条件 {i + 1}: 字段名不能为空")

            operator = condition.get("operator", "")
            valid_operators = ["gt", "gte", "lt", "lte", "eq", "ne", "between", "in"]
            if operator not in valid_operators:
                errors.append(f"条件 {i + 1}: 无效的操作符 '{operator}'")

            if "value" not in condition and operator not in ["in"]:
                errors.append(f"条件 {i + 1}: 缺少目标值")

            weight = condition.get("weight", 1.0)
            if weight <= 0 or weight > 10:
                warnings.append(f"条件 {i + 1}: 权重值 {weight} 可能不合理 (建议0.1-5.0)")

        total_weight = sum(c.get("weight", 1.0) for c in strategy.get("conditions", []))
        if total_weight == 0:
            errors.append("总权重不能为0")

        is_valid = len(errors) == 0

        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
        }

    def optimize_strategy_params(
        self,
        strategy_name: str,
        stocks: list[dict[str, Any]],
        target_field: str = "change_percent",
        method: str = "grid_search",
    ) -> dict[str, Any]:
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return {"error": f"策略 {strategy_name} 不存在"}

        if not stocks:
            return {"error": "股票列表为空"}

        best_params = None
        best_score = -float("inf")
        results = []

        param_ranges = self._generate_param_ranges(strategy)

        import itertools

        param_combinations = list(itertools.product(*param_ranges.values()))
        param_names = list(param_ranges.keys())

        for combo in param_combinations:
            params = dict(zip(param_names, combo))

            modified_strategy = self._apply_params(strategy, params)

            screened = self.screen_stocks(stocks, strategy_name, min_score=0.3)

            if not screened:
                continue

            score = self._calculate_strategy_score(screened, stocks, target_field)

            results.append({"params": params, "score": score, "screened_count": len(screened)})

            if score > best_score:
                best_score = score
                best_params = params

        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "strategy": strategy_name,
            "best_params": best_params,
            "best_score": best_score,
            "method": method,
            "total_combinations": len(param_combinations),
            "top_results": results[:10],
        }

    def _generate_param_ranges(self, strategy: Any) -> dict[str, list]:
        ranges = {}
        for i, condition in enumerate(strategy.buy_conditions):
            field = condition.field
            value = condition.value

            if isinstance(value, (int, float)):
                ranges[f"condition_{i}_value"] = [
                    value * 0.5,
                    value * 0.75,
                    value,
                    value * 1.25,
                    value * 1.5,
                ]

        return ranges

    def _apply_params(self, strategy: Any, params: dict[str, Any]) -> Any:
        modified = strategy.model_copy(deep=True) if hasattr(strategy, "model_copy") else strategy

        for param_name, param_value in params.items():
            if param_name.startswith("condition_"):
                parts = param_name.split("_")
                if len(parts) >= 3:
                    idx = int(parts[1])
                    attr = "_".join(parts[2:])

                    if idx < len(modified.conditions):
                        modified.conditions[idx][attr] = param_value

        return modified

    def _calculate_strategy_score(
        self,
        screened: list[dict[str, Any]],
        all_stocks: list[dict[str, Any]],
        target_field: str,
    ) -> float:
        if not screened:
            return 0.0

        screened_codes = {s.get("stock_code", "") for s in screened}

        screened_returns = []
        all_returns = []

        for stock in all_stocks:
            ret = stock.get(target_field, 0)
            if ret is not None:
                try:
                    all_returns.append(float(ret))
                except (ValueError, TypeError):
                    pass

                if stock.get("code", "") in screened_codes:
                    screened_returns.append(float(ret))

        if not screened_returns or not all_returns:
            return 0.0

        avg_screened = sum(screened_returns) / len(screened_returns)
        avg_all = sum(all_returns) / len(all_returns)

        excess_return = avg_screened - avg_all

        coverage = len(screened) / len(all_stocks)

        score = excess_return * (1 - abs(coverage - 0.3) * 2)

        return score

    def combine_strategies(
        self,
        strategy_names: list[str],
        weights: list[float] | None = None,
        combination_method: str = "weighted_average",
    ) -> dict[str, Any]:
        strategies = []
        for name in strategy_names:
            strategy = self.get_strategy(name)
            if strategy:
                strategies.append(strategy)

        if not strategies:
            return {"error": "没有找到有效的策略"}

        if weights is None:
            weights = [1.0 / len(strategies)] * len(strategies)

        if len(weights) != len(strategies):
            weights = [1.0 / len(strategies)] * len(strategies)

        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        combined_conditions = []
        for strategy, weight in zip(strategies, weights):
            for condition in strategy.buy_conditions:
                combined_condition = {
                    "name": condition.name,
                    "field": condition.field,
                    "operator": condition.operator,
                    "value": condition.value,
                    "weight": condition.weight * weight,
                }
                combined_conditions.append(combined_condition)

        combined_name = "+".join(strategy_names)

        return {
            "name": combined_name,
            "strategies": strategy_names,
            "weights": weights,
            "method": combination_method,
            "conditions": combined_conditions,
            "total_conditions": len(combined_conditions),
        }

    def evaluate_strategy_portfolio(
        self,
        stocks: list[dict[str, Any]],
        strategy_names: list[str],
        weights: list[float] | None = None,
    ) -> dict[str, Any]:
        combined = self.combine_strategies(strategy_names, weights)

        if "error" in combined:
            return combined

        results = []
        for stock in stocks:
            stock_scores = {}
            for strategy_name in strategy_names:
                evaluation = self.evaluate_stock(stock, strategy_name)
                stock_scores[strategy_name] = evaluation.get("score", 0)

            if weights is None:
                w = [1.0 / len(strategy_names)] * len(strategy_names)
            else:
                total = sum(weights)
                w = [wt / total for wt in weights]

            combined_score = sum(s * w for s, w in zip(stock_scores.values(), w))

            best_strategy = max(stock_scores, key=stock_scores.get) if stock_scores else None

            results.append(
                {
                    "code": stock.get("code", ""),
                    "name": stock.get("name", ""),
                    "combined_score": combined_score,
                    "strategy_scores": stock_scores,
                    "recommendation": self._get_portfolio_recommendation(combined_score, best_strategy),
                }
            )

        results.sort(key=lambda x: x["combined_score"], reverse=True)

        return {
            "strategies": strategy_names,
            "weights": weights,
            "total_stocks": len(stocks),
            "results": results[:20],
        }

    def _get_portfolio_recommendation(self, combined_score: float, best_strategy: str | None) -> str:
        if combined_score >= 0.8:
            return f"强烈推荐 (最佳策略: {best_strategy})"
        elif combined_score >= 0.6:
            return f"推荐 (最佳策略: {best_strategy})"
        elif combined_score >= 0.4:
            return "观望"
        else:
            return "不推荐"

    def screen_with_portfolio(
        self,
        stocks: list[dict[str, Any]],
        strategy_names: list[str],
        weights: list[float] | None = None,
        min_score: float = 0.5,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        portfolio_result = self.evaluate_strategy_portfolio(stocks, strategy_names, weights)

        if "error" in portfolio_result:
            return []

        filtered = [r for r in portfolio_result.get("results", []) if r.get("combined_score", 0) >= min_score]

        return filtered[:limit]
