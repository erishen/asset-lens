"""
Market Sentiment Analyzer for asset-lens.
市场风向分析器 - 反推市场趋势和投资风向

功能:
1. 市场指数趋势分析
2. 板块热度分析
3. 资金流向分析
4. 风险偏好判断
5. 投资建议生成
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SentimentIndicator:
    """情绪指标"""

    name: str
    value: float
    level: str  # bullish, bearish, neutral
    description: str


@dataclass
class MarketSentiment:
    """市场风向结果"""

    overall_score: float  # 综合评分 0-100
    trend: str  # bullish, bearish, neutral
    risk_level: str  # low, medium, high
    indicators: list[SentimentIndicator] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    analysis_time: str = ""


class MarketSentimentAnalyzer:
    """市场风向分析器"""

    def __init__(self):
        self.index_weights = {
            "上证指数": 0.25,
            "深证成指": 0.20,
            "创业板指": 0.20,
            "沪深300": 0.20,
            "上证50": 0.15,
        }

    def analyze(self) -> MarketSentiment:
        """分析市场风向"""
        indicators = []

        # 1. 市场指数趋势
        index_indicator = self._analyze_index_trend()
        indicators.append(index_indicator)

        # 2. 板块热度
        sector_indicator = self._analyze_sector_heat()
        indicators.append(sector_indicator)

        # 3. 资金流向
        fund_indicator = self._analyze_fund_flow()
        indicators.append(fund_indicator)

        # 4. 股票池表现
        pool_indicator = self._analyze_stock_pool()
        indicators.append(pool_indicator)

        # 5. 成交量分析
        volume_indicator = self._analyze_volume()
        indicators.append(volume_indicator)

        # 计算综合评分
        overall_score = self._calculate_overall_score(indicators)

        # 判断趋势
        trend = self._determine_trend(overall_score)

        # 判断风险等级
        risk_level = self._determine_risk_level(overall_score, indicators)

        # 生成建议
        suggestions = self._generate_suggestions(overall_score, indicators)

        return MarketSentiment(
            overall_score=overall_score,
            trend=trend,
            risk_level=risk_level,
            indicators=indicators,
            suggestions=suggestions,
            analysis_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    def _analyze_index_trend(self) -> SentimentIndicator:
        """分析指数趋势"""
        try:
            import requests

            index_codes = {
                "上证指数": "sh000001",
                "深证成指": "sz399001",
                "创业板指": "sz399006",
                "沪深300": "sh000300",
                "上证50": "sh000016",
            }

            total_score = 0.0
            descriptions = []
            count = 0

            for name, code in index_codes.items():
                try:
                    url = f"http://hq.sinajs.cn/list={code}"
                    headers = {
                        "Referer": "http://finance.sina.com.cn",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    }
                    response = requests.get(url, headers=headers, timeout=5)

                    if response.status_code == 200:
                        content = response.text
                        pattern = f'var hq_str_{code}="'
                        start = content.find(pattern)

                        if start != -1:
                            start += len(pattern)
                            end = content.find('";', start)
                            data_str = content[start:end]
                            parts = data_str.split(",")

                            if len(parts) >= 32:
                                current_price = float(parts[3]) if parts[3] else 0
                                prev_close = float(parts[2]) if parts[2] else 0
                                change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                                weight = self.index_weights.get(name, 0.1)

                                if change_pct > 1:
                                    score = 80
                                    desc = "强势上涨"
                                elif change_pct > 0.3:
                                    score = 65
                                    desc = "小幅上涨"
                                elif change_pct > -0.3:
                                    score = 50
                                    desc = "横盘震荡"
                                elif change_pct > -1:
                                    score = 35
                                    desc = "小幅下跌"
                                else:
                                    score = 20
                                    desc = "大幅下跌"

                                total_score += score * weight
                                descriptions.append(f"{name}{desc}({change_pct:+.2f}%)")
                                count += 1
                except Exception as e:
                    logger.debug(f"忽略异常: {e}")
                    continue

            if count == 0:
                return SentimentIndicator(
                    name="指数趋势",
                    value=50,
                    level="neutral",
                    description="无法获取指数数据",
                )

            if total_score >= 65:
                level = "bullish"
            elif total_score >= 35:
                level = "neutral"
            else:
                level = "bearish"

            return SentimentIndicator(
                name="指数趋势",
                value=round(total_score, 1),
                level=level,
                description="; ".join(descriptions[:3]),
            )

        except Exception as e:
            return SentimentIndicator(
                name="指数趋势",
                value=50,
                level="neutral",
                description=f"分析失败: {e!s}",
            )

    def _analyze_sector_heat(self) -> SentimentIndicator:
        """分析板块热度"""
        try:
            from ..config import config
            from ..trading.stock_pool import StockPool

            pool_path = config.cache_path / "stock_pools"
            if not pool_path.exists():
                return SentimentIndicator(
                    name="板块热度",
                    value=50,
                    level="neutral",
                    description="无股票池数据",
                )

            pool_files = [f for f in pool_path.glob("*_pool.json") if not f.name.startswith("test_")]
            if not pool_files:
                return SentimentIndicator(
                    name="板块热度",
                    value=50,
                    level="neutral",
                    description="无股票池数据",
                )

            total_stocks = 0
            profit_stocks = 0
            total_profit_rate = 0

            for pool_file in pool_files:
                pool = StockPool(pool_file.stem.replace("_pool", ""))
                for code, position in pool.positions.items():
                    if position.status in ["watching", "holding"] and not code.startswith("sh92") and not code.startswith("bj"):
                            total_stocks += 1
                            profit_rate = position.return_rate if hasattr(position, "return_rate") else 0
                            if profit_rate > 0:
                                profit_stocks += 1
                                total_profit_rate += profit_rate

            if total_stocks == 0:
                return SentimentIndicator(
                    name="板块热度",
                    value=50,
                    level="neutral",
                    description="股票池为空",
                )

            win_rate = profit_stocks / total_stocks * 100
            avg_profit = total_profit_rate / profit_stocks if profit_stocks > 0 else 0

            if win_rate >= 60 and avg_profit > 5:
                score = 75
                level = "bullish"
                desc = f"板块活跃，胜率{win_rate:.0f}%，平均收益{avg_profit:.1f}%"
            elif win_rate >= 50:
                score = 55
                level = "neutral"
                desc = f"板块平稳，胜率{win_rate:.0f}%"
            else:
                score = 35
                level = "bearish"
                desc = f"板块低迷，胜率{win_rate:.0f}%"

            return SentimentIndicator(
                name="板块热度",
                value=score,
                level=level,
                description=desc,
            )

        except Exception as e:
            return SentimentIndicator(
                name="板块热度",
                value=50,
                level="neutral",
                description=f"分析失败: {e!s}",
            )

    def _analyze_fund_flow(self) -> SentimentIndicator:
        """分析资金流向"""
        try:
            from ..config import config
            from ..data.csv_parser import CSVParser

            data_path = config.data_path
            data_dirs = sorted([d for d in data_path.iterdir() if d.is_dir() and d.name.startswith("money_csv_")])
            if not data_dirs:
                return SentimentIndicator(
                    name="资金流向",
                    value=50,
                    level="neutral",
                    description="无投资数据",
                )

            products = CSVParser.load_data_from_dir(data_dirs[-1])
            if not products:
                return SentimentIndicator(
                    name="资金流向",
                    value=50,
                    level="neutral",
                    description="无投资数据",
                )

            total_profit = sum(float(p.profit_amount or 0) for p in products)
            total_current = sum(float(p.current_amount or 0) for p in products)

            if total_current == 0:
                return SentimentIndicator(
                    name="资金流向",
                    value=50,
                    level="neutral",
                    description="无资金数据",
                )

            profit_rate = total_profit / (total_current - total_profit) * 100 if total_current > total_profit else 0

            if profit_rate >= 10:
                score = 80
                level = "bullish"
                desc = f"资金大幅盈利，收益率{profit_rate:.1f}%"
            elif profit_rate >= 5:
                score = 65
                level = "bullish"
                desc = f"资金稳健盈利，收益率{profit_rate:.1f}%"
            elif profit_rate >= 0:
                score = 50
                level = "neutral"
                desc = f"资金小幅盈利，收益率{profit_rate:.1f}%"
            elif profit_rate >= -5:
                score = 40
                level = "neutral"
                desc = f"资金小幅亏损，收益率{profit_rate:.1f}%"
            else:
                score = 25
                level = "bearish"
                desc = f"资金大幅亏损，收益率{profit_rate:.1f}%"

            return SentimentIndicator(
                name="资金流向",
                value=score,
                level=level,
                description=desc,
            )

        except Exception as e:
            return SentimentIndicator(
                name="资金流向",
                value=50,
                level="neutral",
                description=f"分析失败: {e!s}",
            )

    def _analyze_stock_pool(self) -> SentimentIndicator:
        """分析股票池表现"""
        try:
            from ..config import config
            from ..trading.stock_pool import StockPool

            pool_path = config.cache_path / "stock_pools"
            if not pool_path.exists():
                return SentimentIndicator(
                    name="选股效果",
                    value=50,
                    level="neutral",
                    description="无股票池数据",
                )

            pool_files = [f for f in pool_path.glob("*_pool.json") if not f.name.startswith("test_")]
            if not pool_files:
                return SentimentIndicator(
                    name="选股效果",
                    value=50,
                    level="neutral",
                    description="无股票池数据",
                )

            total_selected = 0
            for pool_file in pool_files:
                pool = StockPool(pool_file.stem.replace("_pool", ""))
                total_selected += len([p for p in pool.positions.values() if p.status in ["watching", "holding"]])

            if total_selected >= 10:
                score = 70
                level = "bullish"
                desc = f"选股活跃，共{total_selected}只股票入选"
            elif total_selected >= 5:
                score = 55
                level = "neutral"
                desc = f"选股平稳，共{total_selected}只股票入选"
            elif total_selected > 0:
                score = 45
                level = "neutral"
                desc = f"选股谨慎，仅{total_selected}只股票入选"
            else:
                score = 30
                level = "bearish"
                desc = "无股票入选，市场观望"

            return SentimentIndicator(
                name="选股效果",
                value=score,
                level=level,
                description=desc,
            )

        except Exception as e:
            return SentimentIndicator(
                name="选股效果",
                value=50,
                level="neutral",
                description=f"分析失败: {e!s}",
            )

    def _analyze_volume(self) -> SentimentIndicator:
        """分析成交量"""
        return SentimentIndicator(
            name="成交量",
            value=50,
            level="neutral",
            description="成交量数据暂未接入",
        )

    def _calculate_overall_score(self, indicators: list[SentimentIndicator]) -> float:
        """计算综合评分"""
        weights = {
            "指数趋势": 0.30,
            "板块热度": 0.25,
            "资金流向": 0.25,
            "选股效果": 0.15,
            "成交量": 0.05,
        }

        total_score = 0.0
        total_weight = 0.0

        for indicator in indicators:
            weight = weights.get(indicator.name, 0.1)
            total_score += indicator.value * weight
            total_weight += weight

        return round(total_score / total_weight if total_weight > 0 else 50, 1)

    def _determine_trend(self, score: float) -> str:
        """判断趋势"""
        if score >= 65:
            return "bullish"
        elif score >= 35:
            return "neutral"
        else:
            return "bearish"

    def _determine_risk_level(self, score: float, indicators: list[SentimentIndicator]) -> str:
        """判断风险等级"""
        if score >= 70:
            return "low"
        elif score >= 40:
            return "medium"
        else:
            return "high"

    def _generate_suggestions(self, score: float, indicators: list[SentimentIndicator]) -> list[str]:
        """生成投资建议"""
        suggestions = []

        if score >= 70:
            suggestions.append("✅ 市场情绪乐观，可适当增加仓位")
            suggestions.append("✅ 关注强势板块，把握机会")
        elif score >= 50:
            suggestions.append("⚠️ 市场情绪中性，保持谨慎")
            suggestions.append("⚠️ 控制仓位，精选个股")
        else:
            suggestions.append("🔴 市场情绪悲观，建议降低仓位")
            suggestions.append("🔴 以防守为主，等待机会")

        suggestions.extend(
            f"⚠️ {indicator.name}偏弱：{indicator.description}"
            for indicator in indicators
            if indicator.level == "bearish" and indicator.value < 35
        )

        return suggestions

    def get_report(self) -> str:
        """生成风向报告"""
        sentiment = self.analyze()

        trend_emoji = {"bullish": "📈", "neutral": "➡️", "bearish": "📉"}
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}

        lines = [
            "=" * 60,
            "📊 市场风向分析报告",
            f"分析时间: {sentiment.analysis_time}",
            "=" * 60,
            "",
            f"【综合评分】{sentiment.overall_score}分",
            f"【市场趋势】{trend_emoji.get(sentiment.trend, '')} {sentiment.trend}",
            f"【风险等级】{risk_emoji.get(sentiment.risk_level, '')} {sentiment.risk_level}",
            "",
            "【分项指标】",
        ]

        for indicator in sentiment.indicators:
            level_emoji = {"bullish": "✅", "neutral": "➡️", "bearish": "❌"}
            lines.append(f"  {indicator.name}: {indicator.value}分 {level_emoji.get(indicator.level, '')}")
            lines.append(f"    └─ {indicator.description}")

        lines.extend(
            [
                "",
                "【投资建议】",
            ]
        )

        lines.extend(f"  {suggestion}" for suggestion in sentiment.suggestions)

        lines.extend(
            [
                "",
                "=" * 60,
            ]
        )

        return "\n".join(lines)


market_sentiment_analyzer = MarketSentimentAnalyzer()
