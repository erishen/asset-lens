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
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..config import config


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
    buy_conditions: List[StrategyCondition] = field(default_factory=list)
    sell_conditions: List[StrategyCondition] = field(default_factory=list)
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
        self.strategies: Dict[str, StrategyConfig] = {}
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
            description="成长动量策略 - 追踪强势股",
            buy_conditions=[
                StrategyCondition("放量突破", "volume_ratio", ">", 2, 0.25, "成交量放大2倍以上"),
                StrategyCondition("上涨动能", "change_percent", "between", [3, 9], 0.25, "涨幅3-9%"),
                StrategyCondition("活跃换手", "turnover_rate", "between", [5, 15], 0.2, "换手率5-15%"),
                StrategyCondition("中等市值", "market_cap", "between", [30, 300], 0.15, "市值30-300亿"),
                StrategyCondition("均线多头", "ma_trend", "==", True, 0.15, "均线多头排列"),
            ],
            sell_conditions=[
                StrategyCondition("放量滞涨", "volume_ratio", ">", 3, 0.2, "放量但涨幅小"),
                StrategyCondition("止损", "profit_rate", "<", -0.08, 0.3, "亏损超过8%"),
                StrategyCondition("止盈", "profit_rate", ">", 0.15, 0.3, "盈利超过15%"),
                StrategyCondition("趋势破坏", "ma_trend", "==", False, 0.2, "均线死叉"),
            ],
            position_size=0.08,
            max_positions=15,
            stop_loss=-0.08,
            take_profit=0.15,
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
        buy_conditions: List[Dict[str, Any]],
        sell_conditions: List[Dict[str, Any]],
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

    def evaluate_stock(
        self, stock: Dict[str, Any], strategy_name: str = "value"
    ) -> Dict[str, Any]:
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
        details: List[Dict[str, Any]] = []

        for condition in strategy.buy_conditions:
            total_weight += float(condition.weight)
            value = self._get_field_value(stock, condition.field)
            matched = self._evaluate_condition(value, condition.operator, condition.value)

            if matched:
                matched_weight += float(condition.weight)

            details.append({
                "condition": condition.name,
                "field": condition.field,
                "expected": f"{condition.operator} {condition.value}",
                "actual": value,
                "matched": matched,
                "weight": condition.weight,
            })

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

    def _get_field_value(self, stock: Dict[str, Any], field: str) -> Any:
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
        stocks: List[Dict[str, Any]],
        strategy_name: str = "value",
        min_score: float = 60.0,
    ) -> List[Dict[str, Any]]:
        """
        使用策略筛选股票

        Args:
            stocks: 股票列表
            strategy_name: 策略名称
            min_score: 最低得分

        Returns:
            符合条件的股票列表
        """
        results = []

        for stock in stocks:
            evaluation = self.evaluate_stock(stock, strategy_name)

            if evaluation["match"] and evaluation["score"] >= min_score:
                results.append({
                    **stock,
                    "strategy_score": evaluation["score"],
                    "strategy_details": evaluation["details"],
                })

        results.sort(key=lambda x: x.get("strategy_score", 0), reverse=True)
        return results

    def get_strategy(self, name: str) -> Optional[StrategyConfig]:
        """获取策略"""
        return self.strategies.get(name)

    def list_strategies(self) -> List[Dict[str, Any]]:
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


strategy_engine = StrategyEngine()
