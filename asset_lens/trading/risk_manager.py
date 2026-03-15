"""
Risk management module for asset-lens.
风险管理模块 - 仓位管理、风险预警、止损止盈提醒

功能:
1. 仓位管理建议 - 根据市场环境和风险偏好建议仓位
2. 风险预警系统 - 监控风险指标，触发预警
3. 止损止盈提醒 - 自动计算和提醒止损止盈位
4. 持仓集中度分析 - 分析持仓分散度
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import config


@dataclass
class RiskConfig:
    """风险配置"""

    max_single_position: float = 0.2  # 单只股票最大仓位
    max_total_position: float = 0.8  # 总仓位上限
    stop_loss_default: float = -0.08  # 默认止损
    take_profit_default: float = 0.15  # 默认止盈
    risk_tolerance: str = "medium"  # 风险偏好: low, medium, high


@dataclass
class PositionAdvice:
    """仓位建议"""

    code: str
    name: str
    current_position: float
    suggested_position: float
    action: str  # increase, decrease, hold
    reason: str


@dataclass
class RiskWarning:
    """风险预警"""

    warning_type: str
    level: str  # low, medium, high, critical
    message: str
    code: Optional[str] = None
    timestamp: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class RiskManager:
    """风险管理器"""

    RISK_TOLERANCE_POSITIONS = {
        "low": {"max_single": 0.1, "max_total": 0.5, "stop_loss": -0.05},
        "medium": {"max_single": 0.2, "max_total": 0.7, "stop_loss": -0.08},
        "high": {"max_single": 0.3, "max_total": 0.9, "stop_loss": -0.12},
    }

    def __init__(self):
        self.cache_path = config.cache_path
        self.risk_path = self.cache_path / "risk_management"
        self.risk_path.mkdir(parents=True, exist_ok=True)
        self.warnings_file = self.risk_path / "risk_warnings.json"
        self.config = RiskConfig()
        self.warnings: List[RiskWarning] = []
        self._load_warnings()

    def _load_warnings(self) -> None:
        """加载预警历史"""
        if self.warnings_file.exists():
            try:
                with open(self.warnings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.warnings = [
                        RiskWarning(
                            warning_type=w.get("warning_type", ""),
                            level=w.get("level", "low"),
                            message=w.get("message", ""),
                            code=w.get("code"),
                            timestamp=w.get("timestamp", ""),
                            details=w.get("details", {}),
                        )
                        for w in data.get("warnings", [])[-100:]  # 只保留最近100条
                    ]
            except Exception:
                pass

    def _save_warnings(self) -> None:
        """保存预警历史"""
        data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "warnings": [
                {
                    "warning_type": w.warning_type,
                    "level": w.level,
                    "message": w.message,
                    "code": w.code,
                    "timestamp": w.timestamp,
                    "details": w.details,
                }
                for w in self.warnings[-100:]
            ],
        }
        with open(self.warnings_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def set_risk_tolerance(self, tolerance: str) -> None:
        """
        设置风险偏好

        Args:
            tolerance: 风险偏好 (low, medium, high)
        """
        if tolerance not in self.RISK_TOLERANCE_POSITIONS:
            return

        self.config.risk_tolerance = tolerance
        settings = self.RISK_TOLERANCE_POSITIONS[tolerance]
        self.config.max_single_position = settings["max_single"]
        self.config.max_total_position = settings["max_total"]
        self.config.stop_loss_default = settings["stop_loss"]

    def calculate_position_advice(
        self,
        pool_name: str = "default",
        total_capital: float = 100000,
    ) -> List[PositionAdvice]:
        """
        计算仓位建议

        Args:
            pool_name: 股票池名称
            total_capital: 总资金

        Returns:
            仓位建议列表
        """
        from ..data.market_environment import market_environment_analyzer
        from .stock_pool import StockPool

        pool = StockPool(pool_name)
        environment = market_environment_analyzer.analyze_environment()

        advices: List[PositionAdvice] = []

        holding_stocks = [p for p in pool.positions.values() if p.status == "holding"]

        if not holding_stocks:
            return advices

        position_multiplier = 1.0
        if environment.risk_level == "high":
            position_multiplier = 0.6
        elif environment.risk_level == "medium":
            position_multiplier = 0.8

        total_position_value = sum(p.buy_price * p.shares for p in holding_stocks)
        current_total_ratio = total_position_value / total_capital if total_capital > 0 else 0

        for pos in holding_stocks:
            position_value = pos.buy_price * pos.shares
            current_ratio = position_value / total_capital if total_capital > 0 else 0

            suggested_ratio = self.config.max_single_position * position_multiplier

            if current_ratio > suggested_ratio * 1.2:
                action = "decrease"
                reason = f"仓位过高 ({current_ratio:.1%} > {suggested_ratio:.1%})"
            elif (
                current_ratio < suggested_ratio * 0.5
                and current_total_ratio < self.config.max_total_position
            ):
                action = "increase"
                reason = f"仓位偏低 ({current_ratio:.1%} < {suggested_ratio:.1%})"
            else:
                action = "hold"
                reason = "仓位合理"

            advices.append(
                PositionAdvice(
                    code=pos.code,
                    name=pos.name,
                    current_position=current_ratio,
                    suggested_position=suggested_ratio,
                    action=action,
                    reason=reason,
                )
            )

        return advices

    def calculate_stop_loss_take_profit(
        self,
        code: str,
        buy_price: float,
        atr: Optional[float] = None,
        strategy_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        计算止损止盈位

        Args:
            code: 股票代码
            buy_price: 买入价格
            atr: 平均真实波幅（可选）
            strategy_name: 策略名称（可选）

        Returns:
            止损止盈建议
        """
        from ..strategy.engine import strategy_engine

        result = {
            "code": code,
            "buy_price": buy_price,
            "stop_loss": 0,
            "stop_loss_price": 0,
            "take_profit": 0,
            "take_profit_price": 0,
            "risk_reward_ratio": 0,
            "method": "default",
        }

        stop_loss = self.config.stop_loss_default
        take_profit = self.config.take_profit_default

        if strategy_name:
            strategy = strategy_engine.get_strategy(strategy_name)
            if strategy:
                if strategy.stop_loss:
                    stop_loss = strategy.stop_loss
                if strategy.take_profit:
                    take_profit = strategy.take_profit

        if atr and atr > 0:
            stop_loss_price = buy_price - 2 * atr
            stop_loss_pct = (stop_loss_price - buy_price) / buy_price
            take_profit_price = buy_price + 3 * atr
            take_profit_pct = (take_profit_price - buy_price) / buy_price
            result["method"] = "atr"
        else:
            stop_loss_price = buy_price * (1 + stop_loss)
            stop_loss_pct = stop_loss
            take_profit_price = buy_price * (1 + take_profit)
            take_profit_pct = take_profit
            result["method"] = "percentage"

        result["stop_loss"] = stop_loss_pct
        result["stop_loss_price"] = stop_loss_price
        result["take_profit"] = take_profit_pct
        result["take_profit_price"] = take_profit_price

        if stop_loss_pct != 0:
            result["risk_reward_ratio"] = abs(take_profit_pct / stop_loss_pct)

        return result

    def check_position_concentration(
        self,
        pool_name: str = "default",
    ) -> Dict[str, Any]:
        """
        检查持仓集中度

        Args:
            pool_name: 股票池名称

        Returns:
            集中度分析结果
        """
        from .stock_pool import StockPool

        pool = StockPool(pool_name)

        result: Dict[str, Any] = {
            "pool_name": pool_name,
            "check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_positions": 0,
            "holding_positions": 0,
            "total_value": 0,
            "concentration": {},
            "top_positions": [],
            "warnings": [],
        }

        holding_stocks = [p for p in pool.positions.values() if p.status == "holding"]
        result["holding_positions"] = len(holding_stocks)
        result["total_positions"] = len(pool.positions)

        if not holding_stocks:
            result["warnings"].append(
                {
                    "level": "info",
                    "message": "无持仓",
                }
            )
            return result

        total_value = sum(p.buy_price * p.shares for p in holding_stocks)
        result["total_value"] = total_value

        if total_value == 0:
            return result

        position_weights: List[Dict[str, Any]] = []
        for pos in holding_stocks:
            value = pos.buy_price * pos.shares
            weight = value / total_value
            position_weights.append(
                {
                    "code": pos.code,
                    "name": pos.name,
                    "value": value,
                    "weight": weight,
                }
            )

        position_weights.sort(key=lambda x: x["weight"], reverse=True)

        result["top_positions"] = position_weights[:5]

        if position_weights:
            max_weight = position_weights[0]["weight"]
            result["concentration"]["max_single"] = max_weight

            top3_weight = sum(p["weight"] for p in position_weights[:3])
            result["concentration"]["top3"] = top3_weight

            herfindahl = sum(p["weight"] ** 2 for p in position_weights)
            result["concentration"]["herfindahl"] = herfindahl

            if max_weight > self.config.max_single_position:
                result["warnings"].append(
                    {
                        "level": "high",
                        "message": f"单一持仓占比过高: {position_weights[0]['name']} ({max_weight:.1%})",
                        "code": position_weights[0]["code"],
                    }
                )

            if top3_weight > 0.6:
                result["warnings"].append(
                    {
                        "level": "medium",
                        "message": f"前三大持仓占比过高 ({top3_weight:.1%})",
                    }
                )

        return result

    def generate_risk_warnings(
        self,
        pool_name: str = "default",
    ) -> List[RiskWarning]:
        """
        生成风险预警

        Args:
            pool_name: 股票池名称

        Returns:
            风险预警列表
        """
        from ..data.market_environment import market_environment_analyzer
        from .stock_pool import StockPool

        pool = StockPool(pool_name)
        environment = market_environment_analyzer.analyze_environment()

        new_warnings = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if environment.risk_level == "high":
            warning = RiskWarning(
                warning_type="market_risk",
                level="high",
                message=f"市场风险较高 ({environment.market_type})，建议降低仓位",
                timestamp=now,
                details={
                    "market_type": environment.market_type,
                    "risk_level": environment.risk_level,
                },
            )
            new_warnings.append(warning)

        concentration = self.check_position_concentration(pool_name)
        for w in concentration.get("warnings", []):
            warning = RiskWarning(
                warning_type="concentration",
                level=w.get("level", "low"),
                message=w.get("message", ""),
                code=w.get("code"),
                timestamp=now,
                details=concentration.get("concentration", {}),
            )
            new_warnings.append(warning)

        for pos in pool.positions.values():
            if pos.status == "holding" and pos.buy_price > 0:
                if pos.current_price > 0:
                    profit_rate = (pos.current_price - pos.buy_price) / pos.buy_price

                    if profit_rate <= self.config.stop_loss_default:
                        warning = RiskWarning(
                            warning_type="stop_loss",
                            level="critical",
                            message=f"{pos.name} 触及止损线 ({profit_rate:.2%})",
                            code=pos.code,
                            timestamp=now,
                            details={
                                "buy_price": pos.buy_price,
                                "current_price": pos.current_price,
                                "profit_rate": profit_rate,
                            },
                        )
                        new_warnings.append(warning)

        self.warnings.extend(new_warnings)
        self._save_warnings()

        return new_warnings

    def get_risk_summary(self, pool_name: str = "default") -> Dict[str, Any]:
        """
        获取风险摘要

        Args:
            pool_name: 股票池名称

        Returns:
            风险摘要
        """
        from ..data.market_environment import market_environment_analyzer
        from .stock_pool import StockPool

        pool = StockPool(pool_name)
        environment = market_environment_analyzer.analyze_environment()
        concentration = self.check_position_concentration(pool_name)

        risk_score = 0

        if environment.risk_level == "high":
            risk_score += 30
        elif environment.risk_level == "medium":
            risk_score += 15

        max_concentration = concentration.get("concentration", {}).get("max_single", 0)
        if max_concentration > 0.3:
            risk_score += 25
        elif max_concentration > 0.2:
            risk_score += 15

        status = pool.get_performance()
        win_rate = status.get("win_rate", 0)
        if win_rate < 0.4:
            risk_score += 20
        elif win_rate < 0.5:
            risk_score += 10

        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "pool_name": pool_name,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "market_risk": {
                "type": environment.market_type,
                "level": environment.risk_level,
                "sentiment": environment.sentiment,
            },
            "position_risk": {
                "holding_count": concentration.get("holding_positions", 0),
                "max_concentration": max_concentration,
                "top3_concentration": concentration.get("concentration", {}).get("top3", 0),
            },
            "performance_risk": {
                "win_rate": win_rate,
                "total_profit_rate": status.get("total_profit_rate", 0),
            },
            "recent_warnings": len([w for w in self.warnings if w.level in ["high", "critical"]]),
        }

    def print_risk_summary(self, pool_name: str = "default") -> None:
        """打印风险摘要"""
        summary = self.get_risk_summary(pool_name)

        print("\n" + "=" * 60)
        print("📊 风险管理摘要")
        print("=" * 60)
        print(f"股票池: {pool_name}")
        print(f"更新时间: {summary['update_time']}")

        print(f"\n风险评分: {summary['risk_score']}/100 ({summary['risk_level']})")

        print("\n市场风险:")
        market = summary.get("market_risk", {})
        print(f"  市场类型: {market.get('type', 'N/A')}")
        print(f"  风险等级: {market.get('level', 'N/A')}")
        print(f"  市场情绪: {market.get('sentiment', 'N/A')}")

        print("\n持仓风险:")
        position = summary.get("position_risk", {})
        print(f"  持仓数量: {position.get('holding_count', 0)}")
        print(f"  最大集中度: {position.get('max_concentration', 0):.1%}")
        print(f"  前三大集中度: {position.get('top3_concentration', 0):.1%}")

        print("\n绩效风险:")
        performance = summary.get("performance_risk", {})
        print(f"  胜率: {performance.get('win_rate', 0):.1%}")
        print(f"  总收益率: {performance.get('total_profit_rate', 0):.2%}")

        if summary.get("recent_warnings", 0) > 0:
            print(f"\n⚠️ 近期高风险预警: {summary['recent_warnings']} 条")

        print("=" * 60)


risk_manager = RiskManager()
