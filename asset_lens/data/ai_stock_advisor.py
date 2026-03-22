"""
AI-powered stock selection advisor for asset-lens.
AI 智能选股顾问 - 基于机器学习和规则的智能选股建议

功能:
1. 智能选股建议
2. 策略参数优化建议
3. 市场趋势预测
4. 风险评估建议
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..config import config


@dataclass
class StockAdvice:
    """股票建议"""

    code: str
    name: str
    action: str  # buy, sell, hold
    confidence: float
    reasons: list[str]
    risk_level: str
    target_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    holding_period: int | None = None
    position_size: float | None = None


@dataclass
class StrategyAdvice:
    """策略建议"""

    strategy_name: str
    action: str  # use, modify, avoid
    confidence: float
    reasons: list[str]
    suggested_params: dict[str, Any] = field(default_factory=dict)
    expected_return: float = 0.0
    risk_level: str = "medium"


@dataclass
class MarketPrediction:
    """市场预测"""

    market_type: str  # bull, bear, sideways
    confidence: float
    trend: str  # up, down, stable
    volatility: str  # high, medium, low
    risk_factors: list[str]
    opportunities: list[str]
    suggested_actions: list[str]


class AIStockAdvisor:
    """AI 智能选股顾问"""

    def __init__(self):
        self.cache_path = config.cache_path
        self.advice_path = self.cache_path / "ai_advices"
        self.advice_path.mkdir(parents=True, exist_ok=True)

    def generate_stock_advice(
        self,
        code: str,
        historical_data: dict[str, Any] | None = None,
        market_environment: dict[str, Any] | None = None,
    ) -> StockAdvice:
        """
        生成股票建议

        Args:
            code: 股票代码
            historical_data: 历史数据
            market_environment: 市场环境

        Returns:
            股票建议
        """
        from ..data.multi_source_fetcher import multi_source_fetcher
        from ..strategy.engine import strategy_engine

        quote = multi_source_fetcher.fetch_stock_quote(code)
        if quote is None:
            return StockAdvice(
                code=code,
                name="",
                action="hold",
                confidence=0.0,
                reasons=["无法获取股票数据"],
                risk_level="unknown",
            )

        name = quote.get("name", "")
        current_price = quote.get("current_price", 0)
        change_percent = quote.get("change_percent", 0)
        pe_ratio = quote.get("pe_ratio", 0)
        pb_ratio = quote.get("pb_ratio", 0)

        reasons = []
        buy_score = 0
        sell_score = 0
        risk_factors = []

        if pe_ratio > 0:
            if pe_ratio < 15:
                buy_score += 20
                reasons.append(f"估值较低 (PE: {pe_ratio:.1f})")
            elif pe_ratio > 50:
                sell_score += 15
                reasons.append(f"估值偏高 (PE: {pe_ratio:.1f})")
                risk_factors.append("估值风险")

        if pb_ratio > 0:
            if pb_ratio < 1.5:
                buy_score += 15
                reasons.append(f"市净率较低 (PB: {pb_ratio:.1f})")
            elif pb_ratio > 5:
                sell_score += 10
                reasons.append(f"市净率偏高 (PB: {pb_ratio:.1f})")

        if abs(change_percent) > 5:
            risk_factors.append("波动较大")

        if historical_data:
            klines = historical_data.get("klines", [])
            if len(klines) >= 20:
                closes = [k.get("close", 0) for k in klines[-20:]]
                ma20 = sum(closes) / len(closes)

                if current_price > ma20:
                    buy_score += 10
                    reasons.append("股价位于20日均线上方")
                else:
                    sell_score += 10
                    reasons.append("股价位于20日均线下方")

        if market_environment:
            market_type = market_environment.get("market_type", "震荡")
            if market_type == "牛市":
                buy_score += 10
                reasons.append("市场环境偏多")
            elif market_type == "熊市":
                sell_score += 10
                reasons.append("市场环境偏空")

        strategies = strategy_engine.list_strategies()
        strategy_matches = 0
        for s in strategies:
            evaluation = strategy_engine.evaluate_stock(quote, s.get("name", ""))
            if evaluation.get("match"):
                strategy_matches += 1
                buy_score += 5

        if strategy_matches > 0:
            reasons.append(f"匹配 {strategy_matches} 个策略")

        if buy_score > sell_score + 20:
            action = "buy"
            confidence = min((buy_score - sell_score) / 100, 1.0)
        elif sell_score > buy_score + 20:
            action = "sell"
            confidence = min((sell_score - buy_score) / 100, 1.0)
        else:
            action = "hold"
            confidence = 0.5

        risk_level = "low"
        if len(risk_factors) >= 2:
            risk_level = "high"
        elif len(risk_factors) >= 1:
            risk_level = "medium"

        target_price = None
        stop_loss = None
        take_profit = None
        holding_period = None
        position_size = None

        if action == "buy" and current_price > 0:
            target_price = current_price * 1.15
            stop_loss = current_price * 0.92
            take_profit = current_price * 1.20
            holding_period = 30
            position_size = 0.1

        return StockAdvice(
            code=code,
            name=name,
            action=action,
            confidence=confidence,
            reasons=reasons if reasons else ["无明显信号"],
            risk_level=risk_level,
            target_price=target_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            holding_period=holding_period,
            position_size=position_size,
        )

    def generate_strategy_advice(
        self,
        strategy_name: str,
        historical_data: dict[str, Any] | None = None,
        market_environment: dict[str, Any] | None = None,
    ) -> StrategyAdvice:
        """
        生成策略建议

        Args:
            strategy_name: 策略名称
            historical_data: 历史数据
            market_environment: 市场环境

        Returns:
            策略建议
        """
        from ..strategy.engine import strategy_engine

        strategy = strategy_engine.get_strategy(strategy_name)
        if strategy is None:
            return StrategyAdvice(
                strategy_name=strategy_name,
                action="avoid",
                confidence=0.0,
                reasons=["策略不存在"],
            )

        reasons = []
        use_score = 0
        avoid_score = 0
        suggested_params = {}

        if historical_data:
            try:
                validation = strategy_engine.validate_strategy(
                    strategy_name,
                    historical_data,
                )

                if validation.get("valid"):
                    use_score += 30
                    reasons.append("策略验证通过")

                    win_rate = validation.get("win_rate", 0)
                    if win_rate > 0.6:
                        use_score += 20
                        reasons.append(f"胜率较高 ({win_rate:.1%})")
                    elif win_rate < 0.4:
                        avoid_score += 15
                        reasons.append(f"胜率较低 ({win_rate:.1%})")

                    total_return = validation.get("total_return", 0)
                    if total_return > 0.1:
                        use_score += 20
                        reasons.append(f"收益良好 ({total_return:.1%})")
                    elif total_return < 0:
                        avoid_score += 20
                        reasons.append(f"收益为负 ({total_return:.1%})")

                else:
                    avoid_score += 20
                    for issue in validation.get("issues", []):
                        reasons.append(issue)

            except Exception as e:
                avoid_score += 10
                reasons.append(f"策略验证失败: {e}")

        if market_environment:
            market_type = market_environment.get("market_type", "震荡")

            strategy_lower = strategy_name.lower()
            if market_type == "牛市":
                if "momentum" in strategy_lower or "动量" in strategy_lower:
                    use_score += 20
                    reasons.append("适合牛市环境")
            elif market_type == "熊市":
                if "value" in strategy_lower or "价值" in strategy_lower:
                    use_score += 20
                    reasons.append("适合熊市环境")

        if strategy.stop_loss and strategy.stop_loss < -0.15:
            avoid_score += 10
            reasons.append("止损设置过宽")
            suggested_params["stop_loss"] = -0.08

        if strategy.take_profit and strategy.take_profit > 0.3:
            avoid_score += 10
            reasons.append("止盈设置过高")
            suggested_params["take_profit"] = 0.15

        if use_score > avoid_score + 20:
            action = "use"
            confidence = min((use_score - avoid_score) / 100, 1.0)
        elif avoid_score > use_score + 20:
            action = "avoid"
            confidence = min((avoid_score - use_score) / 100, 1.0)
        else:
            action = "modify"
            confidence = 0.5

        return StrategyAdvice(
            strategy_name=strategy_name,
            action=action,
            confidence=confidence,
            reasons=reasons if reasons else ["无明显信号"],
            suggested_params=suggested_params,
            expected_return=validation.get("total_return", 0) if historical_data else 0,
            risk_level="medium" if use_score > avoid_score else "high",
        )

    def predict_market(
        self,
        market_data: dict[str, Any] | None = None,
    ) -> MarketPrediction:
        """
        预测市场趋势

        Args:
            market_data: 市场数据

        Returns:
            市场预测
        """
        from ..data.market_environment import market_environment_analyzer

        env = market_environment_analyzer.analyze_environment()

        risk_factors = []
        opportunities = []
        suggested_actions = []

        if env.risk_level == "high":
            risk_factors.append("市场风险较高")
            suggested_actions.append("降低仓位")
            suggested_actions.append("增加防御性资产")

        if env.sentiment == "bearish":
            risk_factors.append("市场情绪悲观")
            suggested_actions.append("谨慎操作")

        if env.market_type == "牛市":
            opportunities.append("上涨趋势")
            suggested_actions.append("关注强势股")

        if env.market_type == "熊市":
            opportunities.append("估值机会")
            suggested_actions.append("关注价值股")

        if env.market_type == "震荡":
            opportunities.append("波段机会")
            suggested_actions.append("高抛低吸")

        return MarketPrediction(
            market_type=env.market_type,
            confidence=0.6,
            trend="up"
            if env.market_type == "牛市"
            else ("down" if env.market_type == "熊市" else "stable"),
            volatility="high"
            if env.risk_level == "high"
            else ("medium" if env.risk_level == "medium" else "low"),
            risk_factors=risk_factors if risk_factors else ["市场正常"],
            opportunities=opportunities if opportunities else ["观望"],
            suggested_actions=suggested_actions if suggested_actions else ["保持现状"],
        )

    def batch_generate_advice(
        self,
        codes: list[str],
        market_environment: dict[str, Any] | None = None,
    ) -> list[StockAdvice]:
        """
        批量生成股票建议

        Args:
            codes: 股票代码列表
            market_environment: 市场环境

        Returns:
            股票建议列表
        """
        advices = []

        for code in codes:
            try:
                advice = self.generate_stock_advice(
                    code,
                    market_environment=market_environment,
                )
                advices.append(advice)
            except Exception:
                continue

        advices.sort(key=lambda x: x.confidence, reverse=True)
        return advices

    def get_top_picks(
        self,
        limit: int = 10,
        min_confidence: float = 0.6,
    ) -> list[StockAdvice]:
        """
        获取热门推荐

        Args:
            limit: 最大数量
            min_confidence: 最小置信度

        Returns:
            推荐列表
        """
        from ..strategy.screener import stock_screener

        stocks = stock_screener._load_market_stocks()
        codes = [s.get("code", "") for s in stocks[:100] if s.get("code")]

        advices = self.batch_generate_advice(codes)

        buy_advices = [a for a in advices if a.action == "buy" and a.confidence >= min_confidence]

        return buy_advices[:limit]

    def save_advice(
        self,
        advice: Any,
        filename: str | None = None,
    ) -> str:
        """
        保存建议

        Args:
            advice: 建议对象
            filename: 文件名

        Returns:
            文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            advice_type = type(advice).__name__
            filename = f"{advice_type}_{timestamp}.json"

        filepath = self.advice_path / filename

        data = {
            "type": type(advice).__name__,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "advice": {k: v for k, v in advice.__dict__.items()},
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)


ai_stock_advisor = AIStockAdvisor()
