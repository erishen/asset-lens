"""
AI 分析模块 - 使用大模型进行股票分析和交易决策

功能：
1. 股票综合分析 - 技术面+基本面+情绪面
2. 交易决策建议 - 买入/卖出/观望
3. 风险评估 - 识别潜在风险
4. 市场环境判断 - 大盘趋势分析
"""

import json
import logging
import os
import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AIDecision(Enum):
    """AI 决策"""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    WAIT = "wait"


@dataclass
class AIAnalysisResult:
    """AI 分析结果"""

    decision: AIDecision
    confidence: float  # 0-100
    reasoning: str
    risk_level: str  # low, medium, high
    key_factors: list[str]
    market_sentiment: str
    suggested_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    holding_period: int | None = None  # 建议持仓天数
    prompt_tokens: int = 0  # 输入 token 数
    completion_tokens: int = 0  # 输出 token 数
    total_tokens: int = 0  # 总 token 数


class StockAIAnalyzer:
    """AI 股票分析器 - 基于AI的单只股票分析"""

    SYSTEM_PROMPT = '你是股票分析师，输出JSON格式: {"d":"buy/sell/hold/wait","c":0-100,"r":"理由","rl":"low/medium/high","kf":["因素"],"ms":"乐观/中性/悲观","sl":止损价,"tp":止盈价}'

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "StockAIAnalyzer 用于单只股票分析，组合分析请使用 asset_lens.core.ai_analyzer.AIAnalyzer",
            DeprecationWarning,
            stacklevel=2,
        )
        self.api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ZHIPU_API_KEY")

        if os.getenv("DEEPSEEK_API_KEY"):
            self.api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
            self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        else:
            self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            self.model = os.getenv("AI_MODEL", "gpt-4o-mini")

        self.enabled = bool(self.api_key)

        self.cache_dir = os.path.join("cache", "ai_analysis")
        os.makedirs(self.cache_dir, exist_ok=True)

        self.total_tokens_used = 0
        self.total_cost = 0.0

    def _build_analysis_prompt(
        self,
        stock_data: dict[str, Any],
        market_data: dict[str, Any] | None = None,
        strategy_signal: str | None = None,
        _additional_context: str | None = None,
    ) -> str:
        """构建分析提示词（优化版，减少 token）"""

        code = stock_data.get("code", "")
        name = stock_data.get("name", "")
        price = stock_data.get("price", 0)
        change = stock_data.get("change_percent", 0)
        stock_data.get("volume", 0)
        turnover = stock_data.get("turnover_rate", 0)
        cap = stock_data.get("market_cap", 0)
        pe = stock_data.get("pe_ratio", 0)

        parts = [f"{code}|{name}|¥{price}|{change:+.2f}%|换手{turnover:.1f}%|市值{cap}亿|PE{pe}"]

        if market_data:
            idx = market_data.get("index_change", 0)
            parts.append(f"大盘{idx:+.2f}%")

        if strategy_signal:
            parts.append(f"策略:{strategy_signal}")

        return "分析:" + " ".join(parts)

    def analyze_stock_sync(
        self,
        stock_data: dict[str, Any],
        market_data: dict[str, Any] | None = None,
        strategy_signal: str | None = None,
        additional_context: str | None = None,
    ) -> AIAnalysisResult:
        """同步分析股票"""

        if not self.enabled:
            return self._default_result("AI 分析未启用，请配置 API Key")

        try:
            prompt = self._build_analysis_prompt(stock_data, market_data, strategy_signal, additional_context)

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": '你是一位专业的股票分析师，擅长技术分析和基本面分析。请以JSON格式输出分析结果，格式：{"d":"buy/sell/hold/wait","c":0-100,"r":"理由","rl":"low/medium/high","kf":["因素"],"ms":"乐观/中性/悲观","sl":止损价,"tp":止盈价}',
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 500,
                    },
                )

                if response.status_code != 200:
                    return self._default_result(f"API 调用失败: {response.status_code}")

                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)

                self.total_tokens_used += total_tokens
                cost = (prompt_tokens * 0.001 + completion_tokens * 0.002) / 1000
                self.total_cost += cost

                return self._parse_response(content, prompt_tokens, completion_tokens, total_tokens)

        except Exception as e:
            return self._default_result(f"分析异常: {e!s}")

    def _parse_response(
        self, content: str, prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0
    ) -> AIAnalysisResult:
        """解析 AI 响应（支持简短格式和完整格式）"""
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)

                decision_map = {
                    "buy": AIDecision.BUY,
                    "sell": AIDecision.SELL,
                    "hold": AIDecision.HOLD,
                    "wait": AIDecision.WAIT,
                }

                # 支持简短格式 (d, c, r, rl, kf, ms, sl, tp) 和完整格式
                decision = decision_map.get(data.get("d", data.get("decision", "wait")).lower(), AIDecision.WAIT)

                confidence = float(data.get("c", data.get("confidence", 50)))
                reasoning = data.get("r", data.get("reasoning", ""))
                risk_level = data.get("rl", data.get("risk_level", "medium"))
                key_factors = data.get("kf", data.get("key_factors", []))
                market_sentiment = data.get("ms", data.get("market_sentiment", "中性"))
                stop_loss = data.get("sl", data.get("stop_loss"))
                take_profit = data.get("tp", data.get("take_profit"))
                holding_period = data.get("hp", data.get("holding_period"))

                return AIAnalysisResult(
                    decision=decision,
                    confidence=confidence,
                    reasoning=reasoning,
                    risk_level=risk_level,
                    key_factors=key_factors if isinstance(key_factors, list) else [],
                    market_sentiment=market_sentiment,
                    suggested_price=data.get("sp", data.get("suggested_price")),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    holding_period=holding_period,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                )
        except Exception as e:
            logger.debug(f"忽略异常: {e}")

        return self._default_result("解析 AI 响应失败")

    def _default_result(self, reason: str) -> AIAnalysisResult:
        """返回默认结果"""
        return AIAnalysisResult(
            decision=AIDecision.WAIT,
            confidence=0,
            reasoning=reason,
            risk_level="medium",
            key_factors=[],
            market_sentiment="未知",
        )

    def batch_analyze(
        self,
        stocks: list[dict[str, Any]],
        market_data: dict[str, Any] | None = None,
        strategy_signals: dict[str, str] | None = None,
    ) -> dict[str, AIAnalysisResult]:
        """批量分析股票"""
        results = {}

        for stock in stocks:
            code = stock.get("code", "")
            if not code:
                continue

            strategy_signal = None
            if strategy_signals:
                strategy_signal = strategy_signals.get(code)

            results[code] = self.analyze_stock_sync(
                stock_data=stock,
                market_data=market_data,
                strategy_signal=strategy_signal,
            )

        return results


class AITradingAdvisor:
    """AI 交易顾问"""

    def __init__(self):
        self.analyzer = StockAIAnalyzer()

    def evaluate_buy_signal(
        self,
        stock_data: dict[str, Any],
        strategy_score: float,
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """评估买入信号"""

        if not self.analyzer.enabled:
            return {
                "action": "skip",
                "reason": "AI 分析未启用",
                "strategy_only": True,
            }

        strategy_signal = f"策略得分: {strategy_score:.1f}分"
        if strategy_score >= 80:
            strategy_signal += " (强买入信号)"
        elif strategy_score >= 60:
            strategy_signal += " (买入信号)"
        else:
            strategy_signal += " (弱信号)"

        ai_result = self.analyzer.analyze_stock_sync(
            stock_data=stock_data,
            market_data=market_data,
            strategy_signal=strategy_signal,
        )

        final_decision = self._combine_decisions(
            strategy_score=strategy_score,
            ai_decision=ai_result,
        )

        return {
            "action": final_decision["action"],
            "reason": final_decision["reason"],
            "strategy_score": strategy_score,
            "ai_decision": ai_result.decision.value,
            "ai_confidence": ai_result.confidence,
            "ai_reasoning": ai_result.reasoning,
            "risk_level": ai_result.risk_level,
            "key_factors": ai_result.key_factors,
            "suggested_stop_loss": ai_result.stop_loss,
            "suggested_take_profit": ai_result.take_profit,
            "suggested_holding_period": ai_result.holding_period,
            "prompt_tokens": ai_result.prompt_tokens,
            "completion_tokens": ai_result.completion_tokens,
            "total_tokens": ai_result.total_tokens,
        }

    def evaluate_sell_signal(
        self,
        stock_data: dict[str, Any],
        holding_data: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """评估卖出信号"""

        if not self.analyzer.enabled:
            return {
                "action": "skip",
                "reason": "AI 分析未启用",
                "strategy_only": True,
            }

        profit_rate = holding_data.get("profit_rate", 0)
        holding_days = holding_data.get("holding_days", 0)

        strategy_signal = f"持仓盈亏: {profit_rate:.2f}%, 持仓天数: {holding_days}天"

        if profit_rate < -5:
            strategy_signal += " (触发止损)"
        elif profit_rate > 10:
            strategy_signal += " (触发止盈)"

        ai_result = self.analyzer.analyze_stock_sync(
            stock_data=stock_data,
            market_data=market_data,
            strategy_signal=strategy_signal,
        )

        final_decision = self._combine_sell_decisions(
            profit_rate=profit_rate,
            holding_days=holding_days,
            ai_decision=ai_result,
        )

        return {
            "action": final_decision["action"],
            "reason": final_decision["reason"],
            "profit_rate": profit_rate,
            "holding_days": holding_days,
            "ai_decision": ai_result.decision.value,
            "ai_confidence": ai_result.confidence,
            "ai_reasoning": ai_result.reasoning,
            "risk_level": ai_result.risk_level,
            "prompt_tokens": ai_result.prompt_tokens,
            "completion_tokens": ai_result.completion_tokens,
            "total_tokens": ai_result.total_tokens,
        }

    def _combine_decisions(
        self,
        strategy_score: float,
        ai_decision: AIAnalysisResult,
    ) -> dict[str, Any]:
        """组合策略和 AI 决策"""

        if ai_decision.decision == AIDecision.BUY:
            if strategy_score >= 70:
                return {
                    "action": "buy",
                    "reason": f"策略得分{strategy_score:.1f}分 + AI强烈推荐买入，信心{ai_decision.confidence}%",
                }
            elif strategy_score >= 60:
                if ai_decision.confidence >= 60:
                    return {
                        "action": "buy",
                        "reason": f"策略得分{strategy_score:.1f}分 + AI推荐买入，信心{ai_decision.confidence}%",
                    }
                else:
                    return {
                        "action": "wait",
                        "reason": f"策略得分{strategy_score:.1f}分，但AI信心不足({ai_decision.confidence}%)",
                    }
            else:
                return {"action": "wait", "reason": f"策略得分{strategy_score:.1f}分偏低，等待更好时机"}

        elif ai_decision.decision == AIDecision.WAIT:
            return {"action": "wait", "reason": f"AI建议观望: {ai_decision.reasoning[:100]}"}

        elif ai_decision.decision == AIDecision.SELL:
            return {"action": "skip", "reason": f"AI判断当前不适合买入: {ai_decision.reasoning[:100]}"}

        else:
            if strategy_score >= 75:
                return {"action": "buy", "reason": f"策略得分{strategy_score:.1f}分较高，AI中性，可考虑买入"}
            return {"action": "wait", "reason": f"策略得分{strategy_score:.1f}分，AI中性，建议观望"}

    def _combine_sell_decisions(
        self,
        profit_rate: float,
        holding_days: int,
        ai_decision: AIAnalysisResult,
    ) -> dict[str, Any]:
        """组合卖出决策"""

        if profit_rate < -5:
            return {"action": "sell", "reason": f"触发止损线，亏损{abs(profit_rate):.2f}%"}

        if profit_rate > 15:
            return {"action": "sell", "reason": f"触发止盈线，盈利{profit_rate:.2f}%"}

        if ai_decision.decision == AIDecision.SELL and ai_decision.confidence >= 60:
            return {"action": "sell", "reason": f"AI建议卖出: {ai_decision.reasoning[:100]}"}

        if ai_decision.decision == AIDecision.WAIT and profit_rate > 5 and holding_days > 10:
            return {
                "action": "sell",
                "reason": f"持仓{holding_days}天，盈利{profit_rate:.2f}%，AI建议观望，可考虑止盈",
            }

        return {"action": "hold", "reason": f"持仓{holding_days}天，盈亏{profit_rate:.2f}%，继续持有"}


ai_analyzer = StockAIAnalyzer()
ai_trading_advisor = AITradingAdvisor()
