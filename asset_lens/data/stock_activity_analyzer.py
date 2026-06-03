import logging
from pathlib import Path
from typing import Any

from ..config import config
from .providers.cache import UnifiedCache
from .stock_activity_core import (
    ETF_MAPPING,
    INDEX_FUND_MAPPING,
    ActivityMetrics,
    ETFPrediction,
    _calculate_confidence,
    analyze_activity,
    load_market_stocks,
)

logger = logging.getLogger(__name__)


class StockActivityAnalyzer:
    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self._cache = UnifiedCache(cache_dir=self.cache_path)

    def load_market_stocks(self) -> list[dict[str, Any]]:
        return load_market_stocks(self.cache_path)

    def analyze_activity(self, stocks: list[dict[str, Any]]) -> ActivityMetrics:
        return analyze_activity(stocks)

    def predict_etf(self, etf_name: str, stocks: list[dict[str, Any]]) -> ETFPrediction | None:
        if etf_name in INDEX_FUND_MAPPING:
            return self.predict_index_fund(etf_name)

        if etf_name not in ETF_MAPPING:
            return None

        etf_info = ETF_MAPPING[etf_name]
        related_stocks = [s for s in stocks if etf_info["stocks_filter"](s)]

        if not related_stocks:
            return None

        metrics = analyze_activity(related_stocks)

        if etf_info["weight"] == "market_cap":
            total_cap = sum(s.get("market_cap", 0) for s in related_stocks)
            if total_cap > 0:
                weighted_change = sum(
                    s.get("change_percent", 0) * s.get("market_cap", 0) / total_cap for s in related_stocks
                )
            else:
                weighted_change = metrics.avg_change_percent
        else:
            weighted_change = metrics.avg_change_percent

        confidence = _calculate_confidence(metrics, len(related_stocks))

        sorted_stocks = sorted(related_stocks, key=lambda x: x.get("change_percent", 0), reverse=True)
        up_stocks = [s for s in sorted_stocks if s.get("change_percent", 0) > 0]
        down_stocks = [s for s in sorted_stocks if s.get("change_percent", 0) < 0]
        top_gainers = up_stocks[:5]
        top_losers = down_stocks[:5]

        up_ratio = metrics.up_count / metrics.total_count if metrics.total_count > 0 else 0
        down_ratio = metrics.down_count / metrics.total_count if metrics.total_count > 0 else 0

        return ETFPrediction(
            etf_name=etf_name,
            etf_code=etf_info["codes"][0],
            predicted_change=weighted_change,
            confidence=confidence,
            activity_score=metrics.activity_score,
            up_ratio=up_ratio,
            down_ratio=down_ratio,
            related_stocks=related_stocks,
            top_gainers=[
                {"code": s.get("code"), "name": s.get("name"), "change": s.get("change_percent")} for s in top_gainers
            ],
            top_losers=[
                {"code": s.get("code"), "name": s.get("name"), "change": s.get("change_percent")} for s in top_losers
            ],
        )

    def predict_index_fund(self, index_name: str) -> ETFPrediction | None:
        if index_name not in INDEX_FUND_MAPPING:
            return None

        index_info = INDEX_FUND_MAPPING[index_name]

        data = self._cache.load_file("market_index_domestic.json")
        if data is None:
            return None

        try:
            index_data = data.get("指数数据", {})

            index_change = None

            for key in index_info["index_keys"]:
                for index_name_in_data, idx_data in index_data.items():
                    if key in index_name_in_data or index_name_in_data in key:
                        index_change = idx_data.get("涨跌幅", 0)
                        break
                if index_change is not None:
                    break

            if index_change is None:
                for index_name_in_data, idx_data in index_data.items():
                    if index_name in index_name_in_data:
                        index_change = idx_data.get("涨跌幅", 0)
                        break

            if index_change is None:
                return None

            update_time_str = data.get("更新时间", "")
            confidence = 99.0

            if update_time_str:
                try:
                    from datetime import datetime, timedelta

                    update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    age = now - update_time

                    if age > timedelta(hours=24):
                        confidence = 85.0
                    elif age > timedelta(hours=4):
                        confidence = 90.0
                    else:
                        confidence = 99.0
                except (ValueError, OSError) as e:
                    logger.debug(f"忽略异常: {e}")

            return ETFPrediction(
                etf_name=index_name,
                etf_code=index_info["codes"][0],
                predicted_change=index_change,
                confidence=confidence,
                activity_score=0,
                up_ratio=0,
                down_ratio=0,
                related_stocks=[],
                top_gainers=[],
                top_losers=[],
            )

        except (ValueError, KeyError, ConnectionError) as e:
            logger.error(f"预测指数基金失败: {e}")
            return None

    def predict_all_etfs(self) -> list[ETFPrediction]:
        stocks = self.load_market_stocks()

        if not stocks:
            logger.error("没有市场股票数据，请先运行 'make filter-market-stocks' 获取数据")
            return []

        predictions = []

        for etf_name in ETF_MAPPING:
            prediction = self.predict_etf(etf_name, stocks)
            if prediction:
                predictions.append(prediction)

        predictions.sort(key=lambda x: x.predicted_change, reverse=True)

        return predictions

    def get_market_overview(self) -> dict[str, Any]:
        stocks = self.load_market_stocks()

        if not stocks:
            return {}

        metrics = analyze_activity(stocks)

        limit_up = [s for s in stocks if s.get("change_percent", 0) >= 9.9]
        limit_down = [s for s in stocks if s.get("change_percent", 0) <= -9.9]

        return {
            "total_stocks": metrics.total_count,
            "up_count": metrics.up_count,
            "down_count": metrics.down_count,
            "flat_count": metrics.flat_count,
            "avg_change": metrics.avg_change_percent,
            "avg_turnover": metrics.avg_turnover_rate,
            "activity_score": metrics.activity_score,
            "limit_up_count": len(limit_up),
            "limit_down_count": len(limit_down),
            "limit_up_stocks": [
                {"code": s.get("code"), "name": s.get("name"), "change": s.get("change_percent")}
                for s in sorted(limit_up, key=lambda x: x.get("change_percent", 0), reverse=True)[:10]
            ],
            "limit_down_stocks": [
                {"code": s.get("code"), "name": s.get("name"), "change": s.get("change_percent")}
                for s in sorted(limit_down, key=lambda x: x.get("change_percent", 0))[:10]
            ],
        }

    def analyze_all_industries(self) -> list[dict[str, Any]]:
        stocks = self.load_market_stocks()

        if not stocks:
            return []

        results = []

        for etf_name, etf_info in ETF_MAPPING.items():
            related_stocks = [s for s in stocks if etf_info["stocks_filter"](s)]

            if not related_stocks:
                continue

            metrics = analyze_activity(related_stocks)

            results.append(
                {
                    "name": etf_name,
                    "code": etf_info["codes"][0],
                    "predicted_change": metrics.avg_change_percent,
                    "activity_score": metrics.activity_score,
                    "up_ratio": metrics.up_count / metrics.total_count if metrics.total_count > 0 else 0,
                    "down_ratio": metrics.down_count / metrics.total_count if metrics.total_count > 0 else 0,
                    "stock_count": len(related_stocks),
                    "avg_turnover": metrics.avg_turnover_rate,
                }
            )

        results.sort(key=lambda x: x["predicted_change"], reverse=True)

        return results

    def get_investment_suggestions(self, invested_etfs: list[str]) -> dict[str, Any]:
        all_industries = self.analyze_all_industries()

        if not all_industries:
            return {}

        invested = [i for i in all_industries if i["name"] in invested_etfs]
        not_invested = [i for i in all_industries if i["name"] not in invested_etfs]

        hot_industries = [
            i for i in not_invested if i["predicted_change"] > 0.5 and (i["up_ratio"] > 0.4 or i["activity_score"] > 50)
        ]

        weak_industries = [i for i in invested if i["predicted_change"] < -2]

        return {
            "invested": invested,
            "not_invested": not_invested,
            "hot_industries": hot_industries[:5],
            "weak_industries": weak_industries,
            "suggestions": self._generate_suggestions(invested, not_invested),
        }

    def _generate_suggestions(self, invested: list[dict], not_invested: list[dict]) -> list[str]:
        suggestions = []

        hot = [i for i in not_invested if i["predicted_change"] > 1]
        if hot:
            hot_names = [i["name"] for i in hot[:3]]
            suggestions.append(f"💡 热门行业关注: {', '.join(hot_names)} 表现较好，可考虑关注")

        weak = [i for i in invested if i["predicted_change"] < -2]
        if weak:
            weak_names = [i["name"] for i in weak]
            suggestions.append(f"⚠️ 持仓预警: {', '.join(weak_names)} 表现较弱，注意风险")

        active = [i for i in not_invested if i["activity_score"] > 60]
        if active:
            active_names = [i["name"] for i in active[:3]]
            suggestions.append(f"🔥 活跃行业: {', '.join(active_names)} 市场活跃度高")

        high_turnover = [i for i in not_invested if i["avg_turnover"] > 5]
        if high_turnover:
            suggestions.append(f"📊 高换手行业: {', '.join([i['name'] for i in high_turnover[:3]])} 资金关注度高")

        return suggestions


stock_activity_analyzer = StockActivityAnalyzer()
