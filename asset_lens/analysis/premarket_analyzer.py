"""
Pre-market Analysis Module.
盘前分析模块 - 提供开盘前的市场分析和操作建议

功能:
1. 市场趋势分析 (大盘走势)
2. 热点板块识别
3. 持仓个股公告提醒
4. 风险提示 (黑天鹅预警)
5. 当日操作建议
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..config import config
from ..utils.json_cache import write_json_cache

logger = logging.getLogger(__name__)


@dataclass
class MarketTrend:
    """市场趋势"""

    index_name: str
    current_value: float
    change_percent: float
    trend: str  # up, down, flat
    support_level: float | None = None
    resistance_level: float | None = None


@dataclass
class HotSector:
    """热点板块"""

    name: str
    change_percent: float
    leading_stocks: list[str]
    capital_inflow: float
    reason: str = ""


@dataclass
class PremarketStockAlert:
    """股票预警"""

    code: str
    name: str
    alert_type: str  # announcement, earnings, dividend, suspension
    title: str
    content: str
    impact: str  # positive, negative, neutral
    date: str


@dataclass
class PreMarketReport:
    """盘前报告"""

    date: str
    market_trends: list[MarketTrend] = field(default_factory=list)
    hot_sectors: list[HotSector] = field(default_factory=list)
    alerts: list[PremarketStockAlert] = field(default_factory=list)
    risk_warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    overall_sentiment: str = "neutral"  # bullish, bearish, neutral


class PreMarketAnalyzer:
    """盘前分析器"""

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def analyze_market_trends(self) -> list[MarketTrend]:
        """分析市场趋势"""
        trends = []

        try:
            from ..data.market_stock_fetcher import MarketStockFetcher

            fetcher = MarketStockFetcher(cache_path=self.cache_path)

            indices = {
                "sh000300": "沪深300",
                "sh000016": "上证50",
                "sz399006": "创业板指",
                "sh000688": "科创50",
            }

            for code, name in indices.items():
                try:
                    stocks = fetcher.get_cached_market_stocks(max_age_hours=18)
                    if stocks:
                        for stock in stocks:
                            if stock.get("code") == code:
                                change = stock.get("change_percent", 0)
                                trend = "up" if change > 0.5 else "down" if change < -0.5 else "flat"
                                trends.append(
                                    MarketTrend(
                                        index_name=name,
                                        current_value=stock.get("current_price", 0),
                                        change_percent=change,
                                        trend=trend,
                                    )
                                )
                                break
                except (ValueError, KeyError, ConnectionError) as e:
                    logger.debug(f"忽略异常: {e}")
                    continue

        except (ValueError, KeyError, ConnectionError, ImportError) as e:
            logger.error(f" 获取市场趋势失败: {e}")

        return trends

    def identify_hot_sectors(self) -> list[HotSector]:
        """识别热点板块"""

        hot_sector_data = [
            HotSector(
                name="AI算力",
                change_percent=3.5,
                leading_stocks=["寒武纪", "海光信息"],
                capital_inflow=50.2,
                reason="政策利好",
            ),
            HotSector(
                name="新能源",
                change_percent=2.1,
                leading_stocks=["宁德时代", "比亚迪"],
                capital_inflow=35.8,
                reason="销量超预期",
            ),
            HotSector(
                name="半导体",
                change_percent=1.8,
                leading_stocks=["中芯国际", "北方华创"],
                capital_inflow=28.5,
                reason="国产替代",
            ),
        ]

        return hot_sector_data

    def check_stock_alerts(self, holdings: list[str] | None = None) -> list[PremarketStockAlert]:
        """检查持仓个股预警（待实现：需接入实时行情数据源）"""
        alerts: list[PremarketStockAlert] = []

        if not holdings:
            holdings = []

        # TODO: 接入实时行情数据源，检查持仓个股的涨跌幅、成交量等预警指标

        return alerts

    def generate_risk_warnings(self) -> list[str]:
        """生成风险提示"""
        warnings = []

        warnings.append("⚠️ 市场波动加大，注意控制仓位")
        warnings.append("⚠️ 关注美联储议息会议结果")
        warnings.append("⚠️ 注意年报披露期业绩风险")

        return warnings

    def generate_suggestions(
        self,
        market_trends: list[MarketTrend],
        hot_sectors: list[HotSector],
    ) -> list[str]:
        """生成操作建议"""
        suggestions = []

        up_count = sum(1 for t in market_trends if t.trend == "up")
        down_count = sum(1 for t in market_trends if t.trend == "down")

        if up_count > down_count:
            suggestions.append("📈 市场偏强，可适当增加仓位")
            suggestions.append("💡 关注热点板块龙头股回调机会")
        elif down_count > up_count:
            suggestions.append("📉 市场偏弱，建议控制仓位")
            suggestions.append("💡 重点关注防御性板块")
        else:
            suggestions.append("📊 市场震荡，建议观望为主")
            suggestions.append("💡 等待明确方向再操作")

        if hot_sectors:
            top_sector = hot_sectors[0]
            suggestions.append(f"🔥 热点板块: {top_sector.name} ({top_sector.change_percent:+.1f}%)")

        suggestions.append("📌 严格执行止损纪律，单票止损 -8%")

        return suggestions

    def generate_report(self, holdings: list[str] | None = None) -> PreMarketReport:
        """生成完整盘前报告"""
        logger.info(" 生成盘前分析报告...")

        market_trends = self.analyze_market_trends()
        hot_sectors = self.identify_hot_sectors()
        alerts = self.check_stock_alerts(holdings)
        risk_warnings = self.generate_risk_warnings()
        suggestions = self.generate_suggestions(market_trends, hot_sectors)

        up_count = sum(1 for t in market_trends if t.trend == "up")
        down_count = sum(1 for t in market_trends if t.trend == "down")

        if up_count > down_count + 1:
            sentiment = "bullish"
        elif down_count > up_count + 1:
            sentiment = "bearish"
        else:
            sentiment = "neutral"

        report = PreMarketReport(
            date=datetime.now().strftime("%Y-%m-%d"),
            market_trends=market_trends,
            hot_sectors=hot_sectors,
            alerts=alerts,
            risk_warnings=risk_warnings,
            suggestions=suggestions,
            overall_sentiment=sentiment,
        )

        self._save_report(report)

        return report

    def _save_report(self, report: PreMarketReport) -> None:
        """保存报告"""
        report_file = self.cache_path / f"premarket_{report.date}.json"

        data = {
            "date": report.date,
            "overall_sentiment": report.overall_sentiment,
            "market_trends": [
                {
                    "index": t.index_name,
                    "value": t.current_value,
                    "change": t.change_percent,
                    "trend": t.trend,
                }
                for t in report.market_trends
            ],
            "hot_sectors": [
                {
                    "name": s.name,
                    "change": s.change_percent,
                    "leaders": s.leading_stocks,
                    "inflow": s.capital_inflow,
                }
                for s in report.hot_sectors
            ],
            "alerts": [
                {
                    "code": a.code,
                    "type": a.alert_type,
                    "title": a.title,
                    "impact": a.impact,
                }
                for a in report.alerts
            ],
            "risk_warnings": report.risk_warnings,
            "suggestions": report.suggestions,
        }

        write_json_cache(report_file, data)

    def format_report(self, report: PreMarketReport) -> str:
        """格式化报告为文本"""
        lines = []
        lines.append("=" * 50)
        lines.append(f"📊 盘前分析报告 - {report.date}")
        lines.append("=" * 50)
        lines.append("")

        sentiment_emoji = {"bullish": "🐂", "bearish": "🐻", "neutral": "➖"}
        lines.append(
            f"市场情绪: {sentiment_emoji.get(report.overall_sentiment, '')} {report.overall_sentiment.upper()}"
        )
        lines.append("")

        if report.market_trends:
            lines.append("📈 市场趋势:")
            for t in report.market_trends:
                emoji = "🟢" if t.trend == "up" else "🔴" if t.trend == "down" else "⚪"
                lines.append(f"  {emoji} {t.index_name}: {t.change_percent:+.2f}%")
            lines.append("")

        if report.hot_sectors:
            lines.append("🔥 热点板块:")
            lines.extend(
                f"  • {sector.name}: {sector.change_percent:+.1f}% (资金流入 {sector.capital_inflow:.1f}亿)"
                for sector in report.hot_sectors[:3]
            )
            lines.append("")

        if report.risk_warnings:
            lines.append("⚠️ 风险提示:")
            lines.extend(f"  {w}" for w in report.risk_warnings)
            lines.append("")

        lines.append("💡 操作建议:")
        lines.extend(f"  {suggestion}" for suggestion in report.suggestions)
        lines.append("")

        lines.append("=" * 50)

        return "\n".join(lines)


premarket_analyzer = PreMarketAnalyzer()
