"""
Strategy engine for asset-lens.
策略引擎 - 定义和执行投资策略

功能:
1. 策略定义 - 定义买卖条件
2. 策略执行 - 自动筛选股票
3. 策略回测 - 历史数据回测
4. 策略优化 - 参数优化
"""

import json
from dataclasses import dataclass, field
from typing import Any

from ..config import config
<<<<<<< HEAD
=======
from .portfolio_evaluator import StrategyPortfolioEvaluator
>>>>>>> dc6f1577dc16b06a31034a9bddf68e7a7ca679b5


@dataclass
class StrategyCondition:
    """策略条件"""

    name: str
    field: str
    operator: str  # >, <, >=, <=, ==, !=, between
    value: Any
    weight: float = 1.0
    description: str = ""


@dataclass
class StrategyConfig:
    """策略配置"""

    name: str
    description: str = ""
    buy_conditions: list[StrategyCondition] = field(default_factory=list)
    sell_conditions: list[StrategyCondition] = field(default_factory=list)
    position_size: float = 0.1  # 单只股票仓位比例
    max_positions: int = 10  # 最大持仓数
    stop_loss: float = -0.1  # 止损比例
    take_profit: float = 0.2  # 止盈比例
    holding_period_min: int = 0  # 最小持有天数
    holding_period_max: int = 365  # 最大持有天数


class StrategyEngine:
    """策略引擎"""

    def __init__(self):
        self.strategies_path = config.cache_path / "strategies"
        self.strategies_path.mkdir(parents=True, exist_ok=True)
        self.strategies: dict[str, StrategyConfig] = {}
<<<<<<< HEAD
=======
        self.portfolio_evaluator = StrategyPortfolioEvaluator(self)
>>>>>>> dc6f1577dc16b06a31034a9bddf68e7a7ca679b5
        self._load_default_strategies()

    def _load_default_strategies(self) -> None:
        """加载默认策略"""
        # 策略1: 价值投资策略
        self.strategies["value"] = StrategyConfig(
            name="value",
            description="价值投资策略 - 低估值、稳健增长",
            buy_conditions=[
                StrategyCondition("低PE", "pe_ratio", "<", 20, 0.3, "市盈率低于20"),
                StrategyCondition("合理市值", "market_cap", "between", [50, 500], 0.2, "市值50-500亿"),
                StrategyCondition("稳定换手", "turnover_rate", "between", [1, 5], 0.2, "换手率1-5%"),
                StrategyCondition("上涨趋势", "change_percent", ">", 0, 0.15, "当日上涨"),
                StrategyCondition("非ST", "name", "!=", "ST", 0.15, "排除ST股"),
            ],
            sell_conditions=[
                StrategyCondition("PE过高", "pe_ratio", ">", 40, 0.3, "市盈率超过40"),
                StrategyCondition("止损", "profit_rate", "<", -0.1, 0.3, "亏损超过10%"),
                StrategyCondition("止盈", "profit_rate", ">", 0.3, 0.4, "盈利超过30%"),
            ],
            position_size=0.1,
            max_positions=10,
            stop_loss=-0.1,
            take_profit=0.3,
        )

        # 策略2: 成长动量策略
        self.strategies["momentum"] = StrategyConfig(
            name="momentum",
            description="成长动量策略 - 追踪强势股（优化版）",
            buy_conditions=[
                StrategyCondition("上涨动能", "change_percent", "between", [3, 7], 0.3, "涨幅3-7%"),
                StrategyCondition("活跃换手", "turnover_rate", "between", [5, 12], 0.25, "换手率5-12%"),
                StrategyCondition("适度市值", "market_cap", "between", [50, 500], 0.2, "市值50-500亿"),
                StrategyCondition("放量确认", "volume", ">", 200000, 0.15, "成交量>20万手"),
                StrategyCondition("成交额", "amount", ">", 1, 0.1, "成交额>1亿"),
            ],
            sell_conditions=[
                StrategyCondition("止损", "profit_rate", "<", -0.05, 0.4, "亏损超过5%"),
                StrategyCondition("止盈", "profit_rate", ">", 0.10, 0.3, "盈利超过10%"),
                StrategyCondition("趋势破坏", "change_percent", "<", -5, 0.3, "单日跌幅超5%"),
            ],
            position_size=0.1,
            max_positions=20,
            stop_loss=-0.05,
            take_profit=0.10,
        )

        # 策略3: 困境反转策略
        self.strategies["reversal"] = StrategyConfig(
            name="reversal",
            description="困境反转策略 - 抄底超跌股",
            buy_conditions=[
                StrategyCondition("超跌", "change_percent_5d", "<", -15, 0.3, "5日跌幅超15%"),
                StrategyCondition("低估值", "pb_ratio", "<", 1.5, 0.25, "市净率低于1.5"),
                StrategyCondition("底部放量", "volume_ratio", ">", 1.5, 0.2, "底部放量"),
                StrategyCondition("小市值", "market_cap", "<", 100, 0.15, "市值100亿以下"),
                StrategyCondition("非ST", "name", "!=", "ST", 0.1, "排除ST股"),
            ],
            sell_conditions=[
                StrategyCondition("反弹到位", "profit_rate", ">", 0.2, 0.3, "盈利超过20%"),
                StrategyCondition("止损", "profit_rate", "<", -0.05, 0.3, "亏损超过5%"),
                StrategyCondition("放量滞涨", "volume_ratio", ">", 3, 0.2, "放量滞涨"),
            ],
            position_size=0.05,
            max_positions=20,
            stop_loss=-0.05,
            take_profit=0.2,
        )

        # 策略4: 稳健红利策略
        self.strategies["dividend"] = StrategyConfig(
            name="dividend",
            description="稳健红利策略 - 高股息、低波动",
            buy_conditions=[
                StrategyCondition("低PE", "pe_ratio", "<", 15, 0.25, "市盈率低于15"),
                StrategyCondition("大市值", "market_cap", ">", 200, 0.25, "市值200亿以上"),
                StrategyCondition("低换手", "turnover_rate", "<", 3, 0.2, "换手率低于3%"),
                StrategyCondition("稳定波动", "amplitude_20d", "<", 5, 0.15, "20日振幅小于5%"),
                StrategyCondition("小幅下跌", "change_percent", "between", [-3, 0], 0.15, "小幅回调"),
            ],
            sell_conditions=[
                StrategyCondition("估值过高", "pe_ratio", ">", 25, 0.3, "市盈率超过25"),
                StrategyCondition("止损", "profit_rate", "<", -0.08, 0.3, "亏损超过8%"),
                StrategyCondition("止盈", "profit_rate", ">", 0.15, 0.2, "盈利超过15%"),
            ],
            position_size=0.15,
            max_positions=8,
            stop_loss=-0.08,
            take_profit=0.15,
        )

    def create_custom_strategy(
        self,
        name: str,
        description: str,
        buy_conditions: list[dict[str, Any]],
        sell_conditions: list[dict[str, Any]],
        **kwargs,
    ) -> StrategyConfig:
        """
        创建自定义策略

        Args:
            name: 策略名称
            description: 策略描述
            buy_conditions: 买入条件列表
            sell_conditions: 卖出条件列表
            **kwargs: 其他参数

        Returns:
            策略配置
        """
        buy_conds = [
            StrategyCondition(
                name=c.get("name", ""),
                field=c.get("field", ""),
                operator=c.get("operator", ">"),
                value=c.get("value", 0),
                weight=c.get("weight", 1.0),
                description=c.get("description", ""),
            )
            for c in buy_conditions
        ]

        sell_conds = [
            StrategyCondition(
                name=c.get("name", ""),
                field=c.get("field", ""),
                operator=c.get("operator", ">"),
                value=c.get("value", 0),
                weight=c.get("weight", 1.0),
                description=c.get("description", ""),
            )
            for c in sell_conditions
        ]

        strategy = StrategyConfig(
            name=name,
            description=description,
            buy_conditions=buy_conds,
            sell_conditions=sell_conds,
            position_size=kwargs.get("position_size", 0.1),
            max_positions=kwargs.get("max_positions", 10),
            stop_loss=kwargs.get("stop_loss", -0.1),
            take_profit=kwargs.get("take_profit", 0.2),
        )

        self.strategies[name] = strategy
        self._save_strategy(strategy)

        return strategy

    def _save_strategy(self, strategy: StrategyConfig) -> None:
        """保存策略到文件"""
        strategy_file = self.strategies_path / f"{strategy.name}.json"

        data = {
            "name": strategy.name,
            "description": strategy.description,
            "buy_conditions": [
                {
                    "name": c.name,
                    "field": c.field,
                    "operator": c.operator,
                    "value": c.value,
                    "weight": c.weight,
                    "description": c.description,
                }
                for c in strategy.buy_conditions
            ],
            "sell_conditions": [
                {
                    "name": c.name,
                    "field": c.field,
                    "operator": c.operator,
                    "value": c.value,
                    "weight": c.weight,
                    "description": c.description,
                }
                for c in strategy.sell_conditions
            ],
            "position_size": strategy.position_size,
            "max_positions": strategy.max_positions,
            "stop_loss": strategy.stop_loss,
            "take_profit": strategy.take_profit,
        }

        with open(strategy_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def evaluate_stock(self, stock: dict[str, Any], strategy_name: str = "value") -> dict[str, Any]:
        """
        评估股票是否符合策略

        Args:
            stock: 股票数据
            strategy_name: 策略名称

        Returns:
            评估结果
        """
        if strategy_name not in self.strategies:
            return {"match": False, "score": 0, "reason": f"策略 {strategy_name} 不存在"}

        strategy = self.strategies[strategy_name]
        total_weight: float = 0
        matched_weight: float = 0
        details: list[dict[str, Any]] = []

        for condition in strategy.buy_conditions:
            total_weight += float(condition.weight)
            value = self._get_field_value(stock, condition.field)
            matched = self._evaluate_condition(value, condition.operator, condition.value)

            if matched:
                matched_weight += float(condition.weight)

            details.append(
                {
                    "condition": condition.name,
                    "field": condition.field,
                    "expected": f"{condition.operator} {condition.value}",
                    "actual": value,
                    "matched": matched,
                    "weight": condition.weight,
                }
            )

        score = (matched_weight / total_weight * 100) if total_weight > 0 else 0
        match = score >= 60  # 60分以上认为匹配

        return {
            "match": match,
            "score": round(score, 1),
            "matched_conditions": int(matched_weight),
            "total_conditions": len(strategy.buy_conditions),
            "details": details,
            "strategy": strategy_name,
        }

    def _get_field_value(self, stock: dict[str, Any], field: str) -> Any:
        """获取股票字段值"""
        if field in stock:
            return stock[field]

        if field == "volume_ratio":
            avg_volume = stock.get("avg_volume_60d", 0)
            volume = stock.get("volume", 0)
            return (volume / avg_volume) if avg_volume > 0 else 0

        if field == "ma_trend":
            return stock.get("ma_trend", False)

        if field == "change_percent_5d":
            return stock.get("change_percent_5d", 0)

        if field == "amplitude_20d":
            return stock.get("amplitude_20d", 0)

        if field == "profit_rate":
            return stock.get("profit_rate", 0)

        return 0

    def _evaluate_condition(self, value: Any, operator: str, target: Any) -> bool:
        """评估条件"""
        try:
            if operator == ">":
                return float(value) > float(target)
            elif operator == "<":
                return float(value) < float(target)
            elif operator == ">=":
                return float(value) >= float(target)
            elif operator == "<=":
                return float(value) <= float(target)
            elif operator == "==":
                if isinstance(target, bool):
                    return bool(value) == target
                return str(value) == str(target)
            elif operator == "!=":
                if isinstance(target, str):
                    return target not in str(value)
                return str(value) != str(target)
            elif operator == "between":
                if isinstance(target, list) and len(target) == 2:
                    return float(target[0]) <= float(value) <= float(target[1])
        except (ValueError, TypeError):
            return False

        return False

    def screen_stocks(
        self,
        stocks: list[dict[str, Any]],
        strategy_name: str = "value",
        min_score: float = 60.0,
        exclude_st: bool = True,
        exclude_bj: bool = True,
    ) -> list[dict[str, Any]]:
        """
        使用策略筛选股票

        Args:
            stocks: 股票列表
            strategy_name: 策略名称
            min_score: 最低得分
            exclude_st: 是否排除ST股票
            exclude_bj: 是否排除北交所股票

        Returns:
            符合条件的股票列表
        """
        results = []

        for stock in stocks:
            code = stock.get("code", "")
            name = stock.get("name", "")

            # 排除ST股票
            if exclude_st:
                if "ST" in name or "*ST" in name or "st" in name:
                    continue

            # 排除北交所股票（代码以 bj 或 8 开头）
            if exclude_bj:
                if code.startswith("bj") or code.startswith("8"):
                    continue

            evaluation = self.evaluate_stock(stock, strategy_name)

            if evaluation["match"] and evaluation["score"] >= min_score:
                results.append(
                    {
                        **stock,
                        "strategy_score": evaluation["score"],
                        "strategy_details": evaluation["details"],
                    }
                )

        results.sort(key=lambda x: x.get("strategy_score", 0), reverse=True)
        return results

    def get_strategy(self, name: str) -> StrategyConfig | None:
        """获取策略"""
        return self.strategies.get(name)

    def list_strategies(self) -> list[dict[str, Any]]:
        """列出所有策略"""
        return [
            {
                "name": s.name,
                "description": s.description,
                "buy_conditions": len(s.buy_conditions),
                "sell_conditions": len(s.sell_conditions),
                "position_size": s.position_size,
                "max_positions": s.max_positions,
                "stop_loss": s.stop_loss,
                "take_profit": s.take_profit,
            }
            for s in self.strategies.values()
        ]

    def validate_strategy(
        self,
        strategy_name: str,
        historical_data: dict[str, list[dict[str, Any]]],
        initial_capital: float = 100000,
        min_trades: int = 5,
        min_win_rate: float = 0.4,
        min_total_return: float = 0.0,
    ) -> dict[str, Any]:
        """
        验证策略有效性

        Args:
            strategy_name: 策略名称
            historical_data: 历史数据
            initial_capital: 初始资金
            min_trades: 最小交易次数
            min_win_rate: 最小胜率
            min_total_return: 最小总收益率

        Returns:
            验证结果
        """
        from .backtester import Backtester

        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return {
                "valid": False,
                "reason": f"策略 {strategy_name} 不存在",
            }

        try:
            backtester = Backtester()
            result = backtester.run_backtest(
                strategy_name=strategy_name,
                historical_data=historical_data,
                initial_capital=initial_capital,
            )

            issues = []

            if result.total_trades < min_trades:
                issues.append(f"交易次数不足 ({result.total_trades} < {min_trades})")

            if result.win_rate < min_win_rate:
                issues.append(f"胜率过低 ({result.win_rate:.1%} < {min_win_rate:.1%})")

            if result.total_return < min_total_return:
                issues.append(f"收益率不达标 ({result.total_return:.1%} < {min_total_return:.1%})")

            if result.max_drawdown < -0.3:
                issues.append(f"最大回撤过大 ({result.max_drawdown:.1%})")

            return {
                "valid": len(issues) == 0,
                "strategy_name": strategy_name,
                "total_trades": result.total_trades,
                "win_rate": result.win_rate,
                "total_return": result.total_return,
                "annual_return": result.annual_return,
                "max_drawdown": result.max_drawdown,
                "sharpe_ratio": result.sharpe_ratio,
                "profit_factor": result.profit_factor,
                "issues": issues,
                "recommendation": "策略验证通过" if not issues else "需要优化: " + "; ".join(issues),
            }

        except Exception as e:
            return {
                "valid": False,
                "reason": f"回测失败: {e}",
            }

    def optimize_strategy_params(
        self,
        strategy_name: str,
        historical_data: dict[str, list[dict[str, Any]]],
        param_ranges: dict[str, list[Any]] | None = None,
        optimization_metric: str = "sharpe_ratio",
    ) -> dict[str, Any]:
        """
        优化策略参数

        Args:
            strategy_name: 策略名称
            historical_data: 历史数据
            param_ranges: 参数范围 {"param_name": [value1, value2, ...]}
            optimization_metric: 优化指标 (sharpe_ratio, total_return, win_rate)

        Returns:
            优化结果
        """
        from .backtester import Backtester

        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return {
                "success": False,
                "reason": f"策略 {strategy_name} 不存在",
            }

        if param_ranges is None:
            param_ranges = {
                "stop_loss": [-0.05, -0.08, -0.10, -0.12],
                "take_profit": [0.10, 0.15, 0.20, 0.25],
                "holding_period_max": [10, 20, 30, 60],
            }

        original_params = {
            "stop_loss": strategy.stop_loss,
            "take_profit": strategy.take_profit,
            "holding_period_max": strategy.holding_period_max,
        }

        best_result = None
        best_params = original_params.copy()
        best_metric = float("-inf")

        results = []

        for stop_loss in param_ranges.get("stop_loss", [original_params["stop_loss"]]):
            for take_profit in param_ranges.get("take_profit", [original_params["take_profit"]]):
                for holding_period in param_ranges.get(
                    "holding_period_max", [original_params["holding_period_max"]]
                ):
                    strategy.stop_loss = stop_loss
                    strategy.take_profit = take_profit
                    strategy.holding_period_max = holding_period

                    try:
                        backtester = Backtester()
                        result = backtester.run_backtest(
                            strategy_name=strategy_name,
                            historical_data=historical_data,
                        )

                        metric_value = float(getattr(result, optimization_metric, 0))

                        result_data = {
                            "params": {
                                "stop_loss": stop_loss,
                                "take_profit": take_profit,
                                "holding_period_max": holding_period,
                            },
                            "metric_value": metric_value,
                            "total_return": result.total_return,
                            "win_rate": result.win_rate,
                            "max_drawdown": result.max_drawdown,
                            "total_trades": result.total_trades,
                        }

                        results.append(result_data)

                        if metric_value > best_metric:
                            best_metric = metric_value
                            best_params = {
                                "stop_loss": stop_loss,
                                "take_profit": take_profit,
                                "holding_period_max": holding_period,
                            }
                            best_result = result

                    except Exception:
                        continue

        strategy.stop_loss = float(original_params["stop_loss"])
        strategy.take_profit = float(original_params["take_profit"])
        strategy.holding_period_max = int(original_params["holding_period_max"])

        return {
            "success": best_result is not None,
            "strategy_name": strategy_name,
            "optimization_metric": optimization_metric,
            "best_params": best_params,
            "best_metric": best_metric,
            "original_params": original_params,
            "improvement": best_metric
            - getattr(
                Backtester().run_backtest(strategy_name, historical_data),
                optimization_metric,
                0,
            ),
            "all_results": sorted(
                results,
                key=lambda x: float(x["metric_value"])
                if isinstance(x["metric_value"], (int, float))
                else 0.0,
                reverse=True,
            )[:10],
        }

    def combine_strategies(
        self,
        strategy_names: list[str],
        combination_method: str = "intersection",
        weights: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        组合多个策略

        Args:
            strategy_names: 策略名称列表
            combination_method: 组合方法 (intersection, union, weighted)
            weights: 权重列表（仅用于 weighted 方法）

        Returns:
            组合结果
        """
        strategies_to_combine = []
        for name in strategy_names:
            strategy = self.get_strategy(name)
            if not strategy:
                return {
                    "success": False,
                    "reason": f"策略 {name} 不存在",
                }
            strategies_to_combine.append(strategy)

        if weights and len(weights) != len(strategy_names):
            return {
                "success": False,
                "reason": "权重数量与策略数量不匹配",
            }

        if weights is None:
            weights = [1.0 / len(strategy_names)] * len(strategy_names)

        combined_name = f"Combined_{'_'.join(strategy_names[:3])}"
        combined_description = f"组合策略: {', '.join(strategy_names)}"

        combined_buy_conditions = []
        combined_sell_conditions = []

        for strategy in strategies_to_combine:
            combined_buy_conditions.extend(strategy.buy_conditions)
            combined_sell_conditions.extend(strategy.sell_conditions)

        avg_position_size = sum(s.position_size for s in strategies_to_combine) / len(
            strategies_to_combine
        )
        avg_max_positions = int(
            sum(s.max_positions for s in strategies_to_combine) / len(strategies_to_combine)
        )
        avg_stop_loss = sum(s.stop_loss for s in strategies_to_combine) / len(strategies_to_combine)
        avg_take_profit = sum(s.take_profit for s in strategies_to_combine) / len(
            strategies_to_combine
        )

        strategy = self.create_custom_strategy(
            name=combined_name,
            description=combined_description,
            buy_conditions=[
                {
                    "name": c.name,
                    "field": c.field,
                    "operator": c.operator,
                    "value": c.value,
                    "weight": c.weight,
                    "description": c.description,
                }
                for c in combined_buy_conditions
            ],
            sell_conditions=[
                {
                    "name": c.name,
                    "field": c.field,
                    "operator": c.operator,
                    "value": c.value,
                    "weight": c.weight,
                    "description": c.description,
                }
                for c in combined_sell_conditions
            ],
            position_size=avg_position_size,
            max_positions=avg_max_positions,
            stop_loss=avg_stop_loss,
            take_profit=avg_take_profit,
        )

        return {
            "success": True,
            "strategy_name": strategy.name,
            "combination_method": combination_method,
            "weights": weights,
            "source_strategies": strategy_names,
            "message": f"策略组合 {combined_name} 创建成功",
        }

    def evaluate_strategy_portfolio(
        self,
        stock: dict[str, Any],
        strategy_weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
<<<<<<< HEAD
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
            if strategy_name not in self.strategies:
                continue

            evaluation = self.evaluate_stock(stock, strategy_name)
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

        best_strategy = sorted_strategies[0] if sorted_strategies else (None, {})

        return {
            "combined_score": round(weighted_score, 2),
            "best_strategy": best_strategy[0],
            "best_score": best_strategy[1].get("score", 0),
            "strategies": strategy_scores,
            "recommendation": self._get_portfolio_recommendation(weighted_score, best_strategy[0]),
        }

    def _get_portfolio_recommendation(self, combined_score: float, best_strategy: str | None) -> str:
        """获取组合推荐"""
        if combined_score >= 80:
            return f"强烈推荐 - 综合得分 {combined_score:.1f}，最佳策略: {best_strategy}"
        elif combined_score >= 60:
            return f"推荐 - 综合得分 {combined_score:.1f}，最佳策略: {best_strategy}"
        elif combined_score >= 40:
            return f"观望 - 综合得分 {combined_score:.1f}，建议等待更好时机"
        else:
            return f"不推荐 - 综合得分 {combined_score:.1f}，不符合多数策略条件"
=======
        """使用策略组合评估股票"""
        return self.portfolio_evaluator.evaluate_strategy_portfolio(stock, strategy_weights)

    def _get_portfolio_recommendation(self, combined_score: float, best_strategy: str | None) -> str:
        """获取组合建议"""
        return self.portfolio_evaluator._get_portfolio_recommendation(combined_score, best_strategy)
>>>>>>> dc6f1577dc16b06a31034a9bddf68e7a7ca679b5

    def screen_with_portfolio(
        self,
        stocks: list[dict[str, Any]],
        strategy_weights: dict[str, float] | None = None,
<<<<<<< HEAD
        min_combined_score: float = 50.0,
    ) -> list[dict[str, Any]]:
        """
        使用策略组合筛选股票

        Args:
            stocks: 股票列表
            strategy_weights: 策略权重
            min_combined_score: 最低综合得分

        Returns:
            筛选后的股票列表
        """
        results = []

        for stock in stocks:
            portfolio_result = self.evaluate_strategy_portfolio(stock, strategy_weights)

            if portfolio_result["combined_score"] >= min_combined_score:
                results.append({
                    **stock,
                    "portfolio_score": portfolio_result["combined_score"],
                    "best_strategy": portfolio_result["best_strategy"],
                    "strategy_scores": portfolio_result["strategies"],
                    "recommendation": portfolio_result["recommendation"],
                })

        results.sort(key=lambda x: x.get("portfolio_score", 0), reverse=True)
        return results
=======
        min_combined_score: float = 0.5,
    ) -> list[dict[str, Any]]:
        """使用策略组合筛选股票"""
        return self.portfolio_evaluator.screen_with_portfolio(stocks, strategy_weights, min_combined_score)
>>>>>>> dc6f1577dc16b06a31034a9bddf68e7a7ca679b5


strategy_engine = StrategyEngine()
