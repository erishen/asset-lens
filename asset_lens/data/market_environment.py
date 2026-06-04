"""
Market environment analyzer for asset-lens.
市场环境分析模块 - 判断当前市场环境，动态调整策略

功能:
1. 市场环境判断 - 牛市/熊市/震荡市
2. 行业热度分析 - 热门/冷门行业
3. 策略适配建议 - 根据环境推荐策略
4. 参数动态调整 - 根据环境调整策略参数
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..config import config
from .providers.cache import UnifiedCache

logger = logging.getLogger(__name__)


@dataclass
class MarketEnvironment:
    """市场环境"""

    date: str
    market_type: str  # bull, bear, oscillation
    index_change_5d: float
    index_change_20d: float
    index_change_60d: float
    volatility: float
    volume_trend: str  # increasing, decreasing, stable
    sentiment: str  # optimistic, pessimistic, neutral
    hot_sectors: list[str]
    cold_sectors: list[str]
    recommended_strategies: list[str]
    risk_level: str  # low, medium, high


@dataclass
class StrategyAdaptation:
    """策略适配"""

    strategy_name: str
    original_params: dict[str, Any]
    adapted_params: dict[str, Any]
    reason: str
    expected_performance: str  # good, medium, poor


class MarketEnvironmentAnalyzer:
    """市场环境分析器"""

    def __init__(self):
        self.cache_path = config.cache_path
        self._cache = UnifiedCache(cache_dir=self.cache_path)
        self.history: list[MarketEnvironment] = []
        self._load_history()

    def _load_history(self) -> None:
        data = self._cache.load_file("market_environment.json")
        if data is None:
            return
        try:
            self.history = [
                MarketEnvironment(
                    date=e.get("date", ""),
                    market_type=e.get("market_type", "oscillation"),
                    index_change_5d=e.get("index_change_5d", 0),
                    index_change_20d=e.get("index_change_20d", 0),
                    index_change_60d=e.get("index_change_60d", 0),
                    volatility=e.get("volatility", 0),
                    volume_trend=e.get("volume_trend", "stable"),
                    sentiment=e.get("sentiment", "neutral"),
                    hot_sectors=e.get("hot_sectors", []),
                    cold_sectors=e.get("cold_sectors", []),
                    recommended_strategies=e.get("recommended_strategies", []),
                    risk_level=e.get("risk_level", "medium"),
                )
                for e in data.get("history", [])
            ]
        except (json.JSONDecodeError, OSError, ValueError, KeyError) as e:
            logger.warning(f"加载市场环境历史失败: {e}")

    def _save_history(self) -> None:
        data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "history": [
                {
                    "date": e.date,
                    "market_type": e.market_type,
                    "index_change_5d": e.index_change_5d,
                    "index_change_20d": e.index_change_20d,
                    "index_change_60d": e.index_change_60d,
                    "volatility": e.volatility,
                    "volume_trend": e.volume_trend,
                    "sentiment": e.sentiment,
                    "hot_sectors": e.hot_sectors,
                    "cold_sectors": e.cold_sectors,
                    "recommended_strategies": e.recommended_strategies,
                    "risk_level": e.risk_level,
                }
                for e in self.history[-30:]
            ],
        }
        self._cache.save_file("market_environment.json", data, ttl=0)

    def analyze_environment(
        self,
        index_data: dict[str, Any] | None = None,
        stocks_data: list[dict[str, Any]] | None = None,
    ) -> MarketEnvironment:
        """
        分析当前市场环境

        Args:
            index_data: 指数数据
            stocks_data: 股票数据

        Returns:
            市场环境
        """
        today = datetime.now().strftime("%Y-%m-%d")

        change_5d = 0
        change_20d = 0
        change_60d = 0
        volatility = 0

        if index_data:
            change_5d = index_data.get("change_5d", 0)
            change_20d = index_data.get("change_20d", 0)
            change_60d = index_data.get("change_60d", 0)
            volatility = index_data.get("volatility", 0)

        market_type = self._determine_market_type(change_5d, change_20d, change_60d, volatility)

        volume_trend = self._analyze_volume_trend(stocks_data)

        sentiment = self._analyze_sentiment(change_5d, change_20d, market_type)

        hot_sectors, cold_sectors = self._analyze_sectors(stocks_data)

        recommended_strategies = self._recommend_strategies(market_type, volatility, sentiment)

        risk_level = self._assess_risk(market_type, volatility, sentiment)

        environment = MarketEnvironment(
            date=today,
            market_type=market_type,
            index_change_5d=change_5d,
            index_change_20d=change_20d,
            index_change_60d=change_60d,
            volatility=volatility,
            volume_trend=volume_trend,
            sentiment=sentiment,
            hot_sectors=hot_sectors,
            cold_sectors=cold_sectors,
            recommended_strategies=recommended_strategies,
            risk_level=risk_level,
        )

        self.history.append(environment)
        self._save_history()

        return environment

    def _determine_market_type(self, change_5d: float, change_20d: float, change_60d: float, volatility: float) -> str:
        """判断市场类型"""
        if change_20d > 10 and change_60d > 20:
            return "bull"
        elif change_20d < -10 and change_60d < -20:
            return "bear"
        elif volatility > 3:
            return "oscillation"
        elif change_20d > 5:
            return "bull"
        elif change_20d < -5:
            return "bear"
        else:
            return "oscillation"

    def _analyze_volume_trend(self, stocks_data: list[dict[str, Any]] | None) -> str:
        """分析成交量趋势"""
        if not stocks_data:
            return "stable"

        up_count = sum(1 for s in stocks_data if s.get("change_percent", 0) > 0)
        total = len(stocks_data)

        if total == 0:
            return "stable"

        up_ratio = up_count / total

        if up_ratio > 0.6:
            return "increasing"
        elif up_ratio < 0.4:
            return "decreasing"
        else:
            return "stable"

    def _analyze_sentiment(self, change_5d: float, change_20d: float, market_type: str) -> str:
        """分析市场情绪"""
        if market_type == "bull" and change_5d > 3:
            return "optimistic"
        elif market_type == "bear" and change_5d < -3:
            return "pessimistic"
        elif change_5d > 2:
            return "optimistic"
        elif change_5d < -2:
            return "pessimistic"
        else:
            return "neutral"

    def _analyze_sectors(self, stocks_data: list[dict[str, Any]] | None) -> tuple[list[str], list[str]]:
        """分析热门和冷门行业"""
        if not stocks_data:
            return [], []

        sector_changes: dict[str, list[float]] = {}
        for stock in stocks_data:
            sector = stock.get("industry", "其他")
            change = stock.get("change_percent", 0)
            if sector not in sector_changes:
                sector_changes[sector] = []
            sector_changes[sector].append(change)

        sector_avg = {
            sector: sum(changes) / len(changes) for sector, changes in sector_changes.items() if len(changes) >= 3
        }

        sorted_sectors = sorted(sector_avg.items(), key=lambda x: x[1], reverse=True)

        hot_sectors = [s[0] for s in sorted_sectors[:5] if s[1] > 1]
        cold_sectors = [s[0] for s in sorted_sectors[-5:] if s[1] < -1]

        return hot_sectors, cold_sectors

    def _recommend_strategies(self, market_type: str, volatility: float, sentiment: str) -> list[str]:
        """推荐策略"""
        recommendations = []

        if market_type == "bull":
            recommendations.append("momentum")
            if sentiment == "optimistic":
                recommendations.append("value")

        elif market_type == "bear":
            recommendations.append("dividend")
            if volatility > 2:
                recommendations.append("reversal")

        else:  # oscillation
            recommendations.append("value")
            recommendations.append("dividend")

        if volatility > 3 and "reversal" not in recommendations:
            recommendations.append("reversal")

        if sentiment == "pessimistic" and "dividend" not in recommendations:
            recommendations.insert(0, "dividend")

        return recommendations[:3]

    def _assess_risk(self, market_type: str, volatility: float, sentiment: str) -> str:
        """评估风险水平"""
        risk_score = 0

        if market_type == "bear":
            risk_score += 2
        elif market_type == "oscillation":
            risk_score += 1

        if volatility > 3:
            risk_score += 2
        elif volatility > 2:
            risk_score += 1

        if sentiment == "pessimistic":
            risk_score += 1

        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"

    def adapt_strategy(self, strategy_name: str, environment: MarketEnvironment) -> StrategyAdaptation:
        """
        根据市场环境适配策略参数

        Args:
            strategy_name: 策略名称
            environment: 市场环境

        Returns:
            策略适配结果
        """
        original_params = self._get_original_params(strategy_name)
        adapted_params = original_params.copy()
        reason_parts = []

        if environment.market_type == "bull":
            if strategy_name == "momentum":
                adapted_params["change_percent_min"] = original_params.get("change_percent_min", 3) * 0.8
                adapted_params["turnover_min"] = original_params.get("turnover_min", 5) * 0.9
                reason_parts.append("牛市环境，放宽动量条件")

            elif strategy_name == "value":
                adapted_params["pe_max"] = original_params.get("pe_max", 20) * 1.2
                reason_parts.append("牛市环境，适度放宽估值要求")

        elif environment.market_type == "bear":
            if strategy_name == "momentum":
                adapted_params["change_percent_min"] = original_params.get("change_percent_min", 3) * 1.5
                adapted_params["turnover_min"] = original_params.get("turnover_min", 5) * 1.2
                reason_parts.append("熊市环境，提高动量要求")

            elif strategy_name == "value":
                adapted_params["pe_max"] = original_params.get("pe_max", 20) * 0.8
                adapted_params["market_cap_min"] = original_params.get("market_cap_min", 50) * 1.5
                reason_parts.append("熊市环境，提高安全边际")

            elif strategy_name == "reversal":
                adapted_params["change_percent_5d_min"] = original_params.get("change_percent_5d_min", -15) * 0.8
                reason_parts.append("熊市环境，适度放宽抄底条件")

        if environment.volatility > 3:
            adapted_params["stop_loss"] = original_params.get("stop_loss", -0.1) * 0.8
            reason_parts.append("高波动环境，收紧止损")

        if environment.sentiment == "pessimistic":
            adapted_params["position_size"] = original_params.get("position_size", 0.1) * 0.7
            reason_parts.append("悲观情绪，降低仓位")

        elif environment.sentiment == "optimistic":
            adapted_params["position_size"] = original_params.get("position_size", 0.1) * 1.2
            reason_parts.append("乐观情绪，适度提高仓位")

        if strategy_name in environment.recommended_strategies:
            expected = "good"
        elif environment.risk_level == "high" and strategy_name in ["momentum", "reversal"]:
            expected = "poor"
        else:
            expected = "medium"

        return StrategyAdaptation(
            strategy_name=strategy_name,
            original_params=original_params,
            adapted_params=adapted_params,
            reason="; ".join(reason_parts) if reason_parts else "当前环境适合该策略，无需调整",
            expected_performance=expected,
        )

    def _get_original_params(self, strategy_name: str) -> dict[str, Any]:
        """获取策略原始参数"""
        default_params = {
            "value": {
                "pe_max": 20,
                "pe_min": 0,
                "market_cap_min": 50,
                "market_cap_max": 500,
                "turnover_min": 1,
                "turnover_max": 5,
                "stop_loss": -0.1,
                "take_profit": 0.3,
                "position_size": 0.1,
            },
            "momentum": {
                "change_percent_min": 3,
                "change_percent_max": 9,
                "turnover_min": 5,
                "turnover_max": 15,
                "volume_ratio_min": 2,
                "stop_loss": -0.08,
                "take_profit": 0.15,
                "position_size": 0.08,
            },
            "reversal": {
                "change_percent_5d_min": -15,
                "pb_max": 1.5,
                "volume_ratio_min": 1.5,
                "stop_loss": -0.05,
                "take_profit": 0.2,
                "position_size": 0.05,
            },
            "dividend": {
                "pe_max": 15,
                "market_cap_min": 200,
                "turnover_max": 3,
                "stop_loss": -0.08,
                "take_profit": 0.15,
                "position_size": 0.15,
            },
        }
        return default_params.get(strategy_name, {})

    def get_environment_report(self) -> str:
        """生成市场环境报告"""
        if not self.history:
            return "暂无市场环境数据"

        latest = self.history[-1]
        report = []
        report.append("=" * 60)
        report.append("📊 市场环境分析报告")
        report.append("=" * 60)
        report.append(f"日期: {latest.date}")

        market_type_cn = {"bull": "牛市", "bear": "熊市", "oscillation": "震荡市"}
        report.append(f"\n市场类型: {market_type_cn.get(latest.market_type, latest.market_type)}")

        report.append("\n指数表现:")
        report.append(f"  5日涨跌: {latest.index_change_5d:+.2f}%")
        report.append(f"  20日涨跌: {latest.index_change_20d:+.2f}%")
        report.append(f"  60日涨跌: {latest.index_change_60d:+.2f}%")
        report.append(f"  波动率: {latest.volatility:.2f}%")

        volume_cn = {"increasing": "放量", "decreasing": "缩量", "stable": "平稳"}
        report.append(f"\n成交量趋势: {volume_cn.get(latest.volume_trend, latest.volume_trend)}")

        sentiment_cn = {"optimistic": "乐观", "pessimistic": "悲观", "neutral": "中性"}
        report.append(f"市场情绪: {sentiment_cn.get(latest.sentiment, latest.sentiment)}")

        risk_cn = {"low": "低", "medium": "中", "high": "高"}
        report.append(f"风险水平: {risk_cn.get(latest.risk_level, latest.risk_level)}")

        if latest.hot_sectors:
            report.append(f"\n🔥 热门行业: {', '.join(latest.hot_sectors)}")

        if latest.cold_sectors:
            report.append(f"❄️ 冷门行业: {', '.join(latest.cold_sectors)}")

        report.append(f"\n📈 推荐策略: {', '.join(latest.recommended_strategies)}")

        report.append("\n" + "=" * 60)
        report.append("⚠️ 提示: 市场环境会变化，请定期更新分析")

        return "\n".join(report)


market_environment_analyzer = MarketEnvironmentAnalyzer()
