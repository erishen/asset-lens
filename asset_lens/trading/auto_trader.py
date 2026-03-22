"""
自动交易系统

功能：
1. 自动买入/卖出
2. 交易记录（买入理由、卖出理由）
3. 真实行情对照
4. 操作评价和建议
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class TradeAction(Enum):
    BUY = "buy"
    SELL = "sell"


class TradeReason(Enum):
    STRATEGY_SIGNAL = "strategy_signal"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    MANUAL = "manual"
    REBALANCE = "rebalance"


@dataclass
class TradeRecord:
    """交易记录"""
    id: str
    timestamp: str
    action: TradeAction
    code: str
    name: str
    price: float
    shares: int
    amount: float
    reason: TradeReason
    reason_detail: str
    strategy: str
    market_data: dict
    portfolio_state: dict


@dataclass
class TradeEvaluation:
    """交易评价"""
    trade_id: str
    evaluation_date: str
    current_price: float
    price_change_pct: float
    holding_days: int
    profit_loss: float
    profit_loss_pct: float
    is_good_trade: bool
    evaluation: str
    lessons: str


class AutoTrader:
    """自动交易系统"""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path("cache/auto_trader")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.trades_file = self.data_dir / "trades.json"
        self.evaluations_file = self.data_dir / "evaluations.json"
        self.config_file = self.data_dir / "config.json"

        self.trades: list[dict] = self._load_json(self.trades_file, [])
        self.evaluations: list[dict] = self._load_json(self.evaluations_file, [])
        self.config = self._load_json(self.config_file, self._default_config())

    def _default_config(self) -> dict:
        """默认配置"""
        return {
            "strategy": "momentum",
            "stop_loss_pct": -8.0,
            "take_profit_pct": 15.0,
            "max_position_pct": 10.0,
            "max_total_investment": 100000,
            "auto_trade": False,
            "trade_reasons": {
                "momentum": {
                    "buy": [
                        "放量突破，量比>2",
                        "涨幅3-9%，动量强劲",
                        "换手率5-15%，活跃度高",
                        "均线多头排列"
                    ],
                    "sell": [
                        "放量滞涨，量比>3",
                        "跌破5日均线",
                        "触发止损线-8%",
                        "触发止盈线+15%"
                    ]
                }
            }
        }

    def _load_json(self, file_path: Path, default: Any) -> Any:
        """加载JSON文件"""
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        return default

    def _save_json(self, file_path: Path, data: Any):
        """保存JSON文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_trade_id(self) -> str:
        """生成交易ID"""
        return f"TRD{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def record_buy(
        self,
        code: str,
        name: str,
        price: float,
        shares: int,
        reason: TradeReason = TradeReason.STRATEGY_SIGNAL,
        reason_detail: str = "",
        market_data: dict | None = None,
        portfolio_state: dict | None = None
    ) -> TradeRecord:
        """记录买入"""
        trade = TradeRecord(
            id=self._generate_trade_id(),
            timestamp=datetime.now().isoformat(),
            action=TradeAction.BUY,
            code=code,
            name=name,
            price=price,
            shares=shares,
            amount=price * shares,
            reason=reason,
            reason_detail=reason_detail or self._get_default_reason("buy"),
            strategy=self.config["strategy"],
            market_data=market_data or {},
            portfolio_state=portfolio_state or {}
        )

        trade_dict = asdict(trade)
        trade_dict["action"] = trade_dict["action"].value
        trade_dict["reason"] = trade_dict["reason"].value
        self.trades.append(trade_dict)
        self._save_json(self.trades_file, self.trades)

        return trade

    def record_sell(
        self,
        code: str,
        name: str,
        price: float,
        shares: int,
        reason: TradeReason = TradeReason.STRATEGY_SIGNAL,
        reason_detail: str = "",
        market_data: dict | None = None,
        portfolio_state: dict | None = None
    ) -> TradeRecord:
        """记录卖出"""
        trade = TradeRecord(
            id=self._generate_trade_id(),
            timestamp=datetime.now().isoformat(),
            action=TradeAction.SELL,
            code=code,
            name=name,
            price=price,
            shares=shares,
            amount=price * shares,
            reason=reason,
            reason_detail=reason_detail or self._get_default_reason("sell"),
            strategy=self.config["strategy"],
            market_data=market_data or {},
            portfolio_state=portfolio_state or {}
        )

        trade_dict = asdict(trade)
        trade_dict["action"] = trade_dict["action"].value
        trade_dict["reason"] = trade_dict["reason"].value
        self.trades.append(trade_dict)
        self._save_json(self.trades_file, self.trades)

        return trade

    def _get_default_reason(self, action: str) -> str:
        """获取默认理由"""
        strategy = self.config["strategy"]
        reasons = self.config.get("trade_reasons", {}).get(strategy, {}).get(action, [])
        return "; ".join(reasons) if reasons else f"{strategy}策略信号"

    def evaluate_trade(
        self,
        trade_id: str,
        current_price: float,
        evaluation: str = "",
        lessons: str = ""
    ) -> TradeEvaluation | None:
        """评价交易"""
        trade = next((t for t in self.trades if t["id"] == trade_id), None)
        if not trade:
            return None

        trade_time = datetime.fromisoformat(trade["timestamp"])
        holding_days = (datetime.now() - trade_time).days

        price_change_pct = ((current_price - trade["price"]) / trade["price"]) * 100
        profit_loss = (current_price - trade["price"]) * trade["shares"]
        profit_loss_pct = price_change_pct

        is_good_trade = (
            (trade["action"] == "buy" and price_change_pct > 0) or
            (trade["action"] == "sell" and price_change_pct < 0)
        )

        eval_result = TradeEvaluation(
            trade_id=trade_id,
            evaluation_date=datetime.now().isoformat(),
            current_price=current_price,
            price_change_pct=round(price_change_pct, 2),
            holding_days=holding_days,
            profit_loss=round(profit_loss, 2),
            profit_loss_pct=round(profit_loss_pct, 2),
            is_good_trade=is_good_trade,
            evaluation=evaluation or self._auto_evaluate(trade, price_change_pct, holding_days),
            lessons=lessons or self._auto_lessons(trade, price_change_pct, holding_days)
        )

        self.evaluations.append(asdict(eval_result))
        self._save_json(self.evaluations_file, self.evaluations)

        return eval_result

    def _auto_evaluate(self, trade: dict, price_change_pct: float, holding_days: int) -> str:
        """自动生成评价"""
        action = trade["action"]

        if action == "buy":
            if price_change_pct > 10:
                return "优秀操作：买入后涨幅显著，时机把握准确"
            elif price_change_pct > 5:
                return "良好操作：买入后上涨，策略有效"
            elif price_change_pct > 0:
                return "一般操作：小幅上涨，可继续观察"
            elif price_change_pct > -5:
                return "需观察：小幅下跌，关注后续走势"
            else:
                return "需反思：买入后下跌较多，检查入场时机"
        else:
            if price_change_pct < -5:
                return "优秀操作：卖出后继续下跌，及时止损"
            elif price_change_pct < 0:
                return "良好操作：卖出后下跌，规避风险"
            elif price_change_pct < 5:
                return "一般操作：卖出后小幅上涨，可接受"
            else:
                return "需反思：卖出后大幅上涨，可能过早离场"

    def _auto_lessons(self, trade: dict, price_change_pct: float, holding_days: int) -> str:
        """自动生成经验教训"""
        lessons = []

        if trade["action"] == "buy":
            if price_change_pct > 10:
                lessons.append("策略信号有效，可继续使用类似入场时机")
            elif price_change_pct < -5:
                lessons.append("检查入场时机是否过于激进，考虑等待更明确的信号")

            if holding_days < 3:
                lessons.append("持仓时间较短，考虑是否过于频繁交易")
        else:
            if price_change_pct > 5:
                lessons.append("卖出过早，考虑设置更合理的止盈策略")
            elif price_change_pct < -5:
                lessons.append("及时止损正确，保护了资金安全")

        return "; ".join(lessons) if lessons else "继续观察市场，优化策略"

    def get_trade_history(self, code: str | None = None) -> list[dict]:
        """获取交易历史"""
        if code:
            return [t for t in self.trades if t["code"] == code]
        return self.trades

    def get_evaluations(self, trade_id: str | None = None) -> list[dict]:
        """获取评价记录"""
        if trade_id:
            return [e for e in self.evaluations if e["trade_id"] == trade_id]
        return self.evaluations

    def generate_report(self) -> str:
        """生成交易报告"""
        lines = []
        lines.append("=" * 70)
        lines.append("📊 自动交易系统报告")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)

        lines.append("\n📈 交易统计:")
        total_trades = len(self.trades)
        buy_trades = len([t for t in self.trades if t["action"] == "buy"])
        sell_trades = len([t for t in self.trades if t["action"] == "sell"])

        lines.append(f"  总交易次数: {total_trades}")
        lines.append(f"  买入次数: {buy_trades}")
        lines.append(f"  卖出次数: {sell_trades}")

        total_buy_amount = sum(t["amount"] for t in self.trades if t["action"] == "buy")
        total_sell_amount = sum(t["amount"] for t in self.trades if t["action"] == "sell")
        lines.append(f"  总买入金额: ¥{total_buy_amount:,.2f}")
        lines.append(f"  总卖出金额: ¥{total_sell_amount:,.2f}")

        if self.evaluations:
            lines.append("\n📊 操作评价:")
            good_trades = len([e for e in self.evaluations if e["is_good_trade"]])
            total_eval = len(self.evaluations)
            win_rate = (good_trades / total_eval * 100) if total_eval > 0 else 0
            lines.append(f"  评价次数: {total_eval}")
            lines.append(f"  成功操作: {good_trades}")
            lines.append(f"  胜率: {win_rate:.1f}%")

            total_profit = sum(e["profit_loss"] for e in self.evaluations)
            lines.append(f"  总盈亏: ¥{total_profit:,.2f}")

        if self.trades:
            lines.append("\n📋 最近交易:")
            for trade in self.trades[-5:]:
                action_emoji = "💰" if trade["action"] == "buy" else "💸"
                lines.append(f"  {action_emoji} {trade['timestamp'][:10]} {trade['action'].upper()} {trade['name']}({trade['code']})")
                lines.append(f"     价格: ¥{trade['price']:.2f} x {trade['shares']}股 = ¥{trade['amount']:,.2f}")
                lines.append(f"     理由: {trade['reason_detail'][:50]}...")

        return "\n".join(lines)

    def generate_suggestions(self) -> str:
        """生成投资建议"""
        lines = []
        lines.append("=" * 70)
        lines.append("💡 投资建议")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)

        if not self.evaluations:
            lines.append("\n暂无足够数据进行建议分析")
            return "\n".join(lines)

        good_trades = [e for e in self.evaluations if e["is_good_trade"]]
        bad_trades = [e for e in self.evaluations if not e["is_good_trade"]]

        lines.append("\n🎯 策略优化建议:")

        if len(good_trades) > len(bad_trades):
            lines.append("  ✅ 当前策略表现良好，可继续使用")
            lines.append("  💡 建议：保持现有策略，适当增加仓位")
        else:
            lines.append("  ⚠️ 当前策略需要优化")
            lines.append("  💡 建议：检查入场/出场条件，优化止损止盈设置")

        avg_holding = sum(e["holding_days"] for e in self.evaluations) / len(self.evaluations)
        lines.append(f"\n⏱️ 平均持仓天数: {avg_holding:.1f}天")

        if avg_holding < 5:
            lines.append("  💡 建议：持仓时间较短，考虑减少交易频率")
        elif avg_holding > 30:
            lines.append("  💡 建议：持仓时间较长，考虑更积极的止盈策略")

        total_profit = sum(e["profit_loss"] for e in self.evaluations)
        if total_profit > 0:
            lines.append(f"\n💰 总盈利: ¥{total_profit:,.2f}")
            lines.append("  ✅ 策略盈利，继续执行")
        else:
            lines.append(f"\n📉 总亏损: ¥{abs(total_profit):,.2f}")
            lines.append("  ⚠️ 需要调整策略或暂停交易")

        return "\n".join(lines)

auto_trader = AutoTrader()
