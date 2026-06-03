import logging
from dataclasses import dataclass, field
from typing import Any

from ..config import config
from ..utils.json_cache import write_json_cache
from .engine_evaluation import StrategyEvaluationMixin
from .portfolio_evaluator import StrategyPortfolioEvaluator

logger = logging.getLogger(__name__)


@dataclass
class StrategyCondition:
    name: str
    field: str
    operator: str
    value: Any
    weight: float = 1.0
    description: str = ""


@dataclass
class StrategyConfig:
    name: str
    description: str = ""
    buy_conditions: list[StrategyCondition] = field(default_factory=list)
    sell_conditions: list[StrategyCondition] = field(default_factory=list)
    position_size: float = 0.1
    max_positions: int = 10
    stop_loss: float = -0.1
    take_profit: float = 0.2
    holding_period_min: int = 0
    holding_period_max: int = 365


class StrategyEngine(StrategyEvaluationMixin):
    def __init__(self):
        self.strategies_path = config.cache_path / "strategies"
        self.strategies_path.mkdir(parents=True, exist_ok=True)
        self.strategies: dict[str, StrategyConfig] = {}
        self.portfolio_evaluator = StrategyPortfolioEvaluator(self)
        self._load_default_strategies()

    def _load_default_strategies(self) -> None:
        defaults = [
            StrategyConfig(
                name="value",
                description="价值投资策略 - 低PE、低PB、高ROE、高股息",
                buy_conditions=[
                    StrategyCondition(name="低PE", field="pe_ratio", operator="lt", value=15, weight=2.0),
                    StrategyCondition(name="低PB", field="pb_ratio", operator="lt", value=1.5, weight=1.5),
                    StrategyCondition(name="高ROE", field="roe", operator="gt", value=15, weight=2.0),
                    StrategyCondition(name="高股息", field="dividend_yield", operator="gt", value=3, weight=1.5),
                    StrategyCondition(name="低负债", field="debt_ratio", operator="lt", value=60, weight=1.0),
                ],
                position_size=0.1,
                max_positions=10,
                stop_loss=-0.08,
                take_profit=0.3,
            ),
            StrategyConfig(
                name="growth",
                description="成长投资策略 - 高营收增长、高利润增长",
                buy_conditions=[
                    StrategyCondition(name="营收增长", field="revenue_growth", operator="gt", value=20, weight=2.0),
                    StrategyCondition(name="利润增长", field="profit_growth", operator="gt", value=25, weight=2.0),
                    StrategyCondition(name="合理PE", field="pe_ratio", operator="lt", value=40, weight=1.0),
                    StrategyCondition(name="合理PB", field="pb_ratio", operator="lt", value=5, weight=0.5),
                ],
                position_size=0.08,
                max_positions=15,
                stop_loss=-0.1,
                take_profit=0.5,
            ),
            StrategyConfig(
                name="momentum",
                description="动量策略 - 追涨杀跌",
                buy_conditions=[
                    StrategyCondition(name="涨跌幅", field="change_percent", operator="gt", value=3, weight=2.0),
                    StrategyCondition(name="高换手", field="turnover_rate", operator="gt", value=5, weight=1.5),
                    StrategyCondition(name="放量", field="volume", operator="gt", value=1000000, weight=1.0),
                ],
                position_size=0.05,
                max_positions=20,
                stop_loss=-0.05,
                take_profit=0.15,
            ),
            StrategyConfig(
                name="dividend",
                description="高股息策略 - 稳定分红",
                buy_conditions=[
                    StrategyCondition(name="高股息", field="dividend_yield", operator="gt", value=4, weight=3.0),
                    StrategyCondition(name="低PE", field="pe_ratio", operator="lt", value=20, weight=1.5),
                    StrategyCondition(name="低负债", field="debt_ratio", operator="lt", value=50, weight=1.0),
                ],
                position_size=0.15,
                max_positions=8,
                stop_loss=-0.05,
                take_profit=0.2,
            ),
            StrategyConfig(
                name="quality",
                description="质量策略 - 高ROE、稳定增长",
                buy_conditions=[
                    StrategyCondition(name="高ROE", field="roe", operator="gt", value=20, weight=2.5),
                    StrategyCondition(name="营收增长", field="revenue_growth", operator="gt", value=10, weight=1.5),
                    StrategyCondition(name="低负债", field="debt_ratio", operator="lt", value=40, weight=1.5),
                    StrategyCondition(name="合理PE", field="pe_ratio", operator="lt", value=25, weight=1.0),
                ],
                position_size=0.1,
                max_positions=12,
                stop_loss=-0.08,
                take_profit=0.25,
            ),
        ]

        for strategy in defaults:
            self.strategies[strategy.name] = strategy

    def create_custom_strategy(
        self,
        name: str,
        description: str = "",
        conditions: list[dict[str, Any]] | None = None,
        position_size: float = 0.1,
        max_positions: int = 10,
        stop_loss: float = -0.1,
        take_profit: float = 0.2,
    ) -> StrategyConfig:
        strategy_conditions = []
        if conditions:
            for cond in conditions:
                strategy_conditions.append(
                    StrategyCondition(
                        name=cond.get("name", ""),
                        field=cond.get("field", ""),
                        operator=cond.get("operator", "gt"),
                        value=cond.get("value", 0),
                        weight=cond.get("weight", 1.0),
                        description=cond.get("description", ""),
                    )
                )

        strategy = StrategyConfig(
            name=name,
            description=description,
            buy_conditions=strategy_conditions,
            position_size=position_size,
            max_positions=max_positions,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        self.strategies[name] = strategy
        self._save_strategy(strategy)

        return strategy

    def _save_strategy(self, strategy: StrategyConfig) -> None:
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

        write_json_cache(strategy_file, data)

    def get_strategy(self, name: str) -> StrategyConfig | None:
        return self.strategies.get(name)

    def list_strategies(self) -> list[dict[str, Any]]:
        return [
            {
                "name": s.name,
                "description": s.description,
                "buy_conditions": len(s.buy_conditions),
                "sell_conditions": len(s.sell_conditions),
                "position_size": s.position_size,
                "max_positions": s.max_positions,
            }
            for s in self.strategies.values()
        ]


strategy_engine = StrategyEngine()
