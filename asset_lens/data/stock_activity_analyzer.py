"""
Stock activity analyzer for asset-lens.
股票活跃度分析模块 - 分析市场活跃度并预测ETF表现
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class ActivityMetrics:
    """活跃度指标"""

    avg_turnover_rate: float = 0.0
    avg_change_percent: float = 0.0
    avg_volume: float = 0.0
    avg_amount: float = 0.0
    up_count: int = 0
    down_count: int = 0
    flat_count: int = 0
    total_count: int = 0
    activity_score: float = 0.0


@dataclass
class ETFPrediction:
    """ETF预测结果"""

    etf_name: str
    etf_code: str
    current_price: float = 0.0
    predicted_price: float = 0.0
    predicted_change: float = 0.0
    confidence: float = 0.0
    trend: str = "neutral"
    activity_score: float = 0.0
    up_ratio: float = 0.0
    down_ratio: float = 0.0
    related_stocks: list[dict[str, Any]] = field(default_factory=list)
    top_gainers: list[dict[str, Any]] = field(default_factory=list)
    top_losers: list[dict[str, Any]] = field(default_factory=list)


StockFilterCallable = Callable[[dict[str, Any]], bool]


class StockActivityAnalyzer:
    """股票活跃度分析器"""

    INDEX_FUND_MAPPING: dict[str, dict[str, Any]] = {
        "沪深300": {
            "codes": ["sh510300", "sz159919"],
            "index_keys": ["SHComp", "CSI300"],
            "description": "沪深300指数基金",
        },
        "中证500": {
            "codes": ["sh510500", "sz159922"],
            "index_keys": ["CSI500"],
            "description": "中证500指数基金",
        },
        "创业板": {
            "codes": ["sz159915", "sz159948"],
            "index_keys": ["ChiNext"],
            "description": "创业板指数基金",
        },
        "科创50": {
            "codes": ["sh588000", "sh588080"],
            "index_keys": ["STAR50"],
            "description": "科创50指数基金",
        },
        "上证50": {
            "codes": ["sh510050", "sh510100"],
            "index_keys": ["SSE50"],
            "description": "上证50指数基金",
        },
    }

    ETF_MAPPING: dict[str, dict[str, Any]] = {
        "新能源": {
            "codes": ["sz516160", "sh515790"],
            "description": "新能源ETF",
            "stocks_filter": lambda s: any(k in s.get("name", "") for k in ["新能源", "锂电", "光伏", "风电", "储能"]),
            "weight": "equal",
            "type": "industry",
        },
        "半导体": {
            "codes": ["sz512480", "sh512760"],
            "description": "半导体ETF",
            "stocks_filter": lambda s: any(k in s.get("name", "") for k in ["半导体", "芯片", "集成电路"]),
            "weight": "equal",
            "type": "industry",
        },
        "医药": {
            "codes": ["sz159929", "sh512010"],
            "description": "医药ETF",
            "stocks_filter": lambda s: any(k in s.get("name", "") for k in ["医药", "生物", "医疗", "制药"]),
            "weight": "equal",
            "type": "industry",
        },
        "消费": {
            "codes": ["sz159928", "sh510150"],
            "description": "消费ETF",
            "stocks_filter": lambda s: any(k in s.get("name", "") for k in ["消费", "食品", "饮料", "家电", "零售"]),
            "weight": "equal",
            "type": "industry",
        },
        "军工": {
            "codes": ["sz512660", "sh512680"],
            "description": "军工ETF",
            "stocks_filter": lambda s: (
                any(
                    k in s.get("name", "")
                    for k in ["军工", "航天", "兵器", "中航", "航发", "航空动力", "航空工业", "沈飞", "成飞", "西飞"]
                )
                and not any(
                    k in s.get("name", "")
                    for k in [
                        "南方航空",
                        "东方航空",
                        "中国国航",
                        "海南航空",
                        "吉祥航空",
                        "春秋航空",
                        "厦门航空",
                        "航空股份",
                    ]
                )
            ),
            "weight": "equal",
            "type": "industry",
        },
    }

    def __init__(self, cache_path: Path | None = None):
        """
        初始化股票活跃度分析器

        Args:
            cache_path: 缓存路径
        """
        self.cache_path = cache_path or config.cache_path
        self.market_stock_cache_file = self.cache_path / "market_stocks.json"

    def load_market_stocks(self) -> list[dict[str, Any]]:
        """加载市场股票数据"""
        if self.market_stock_cache_file.exists():
            with open(self.market_stock_cache_file, encoding="utf-8") as f:
                data = json.load(f)
                return cast(list[dict[str, Any]], data.get("data", []))
        return []

    def analyze_activity(self, stocks: list[dict[str, Any]]) -> ActivityMetrics:
        """
        分析股票活跃度

        Args:
            stocks: 股票列表

        Returns:
            活跃度指标
        """
        if not stocks:
            return ActivityMetrics()

        total_turnover = 0.0
        total_change = 0.0
        total_volume = 0.0
        total_amount = 0.0
        up_count = 0
        down_count = 0
        flat_count = 0

        for stock in stocks:
            change = stock.get("change_percent", 0)
            turnover = stock.get("turnover_rate", 0)
            volume = stock.get("volume", 0)
            amount = stock.get("amount", 0)

            total_turnover += turnover
            total_change += change
            total_volume += volume
            total_amount += amount

            if change > 0.5:
                up_count += 1
            elif change < -0.5:
                down_count += 1
            else:
                flat_count += 1

        count = len(stocks)
        avg_turnover = total_turnover / count if count > 0 else 0
        avg_change = total_change / count if count > 0 else 0

        activity_score = self._calculate_activity_score(avg_turnover, avg_change, up_count, down_count, count)

        return ActivityMetrics(
            avg_turnover_rate=avg_turnover,
            avg_change_percent=avg_change,
            avg_volume=total_volume / count if count > 0 else 0,
            avg_amount=total_amount / count if count > 0 else 0,
            up_count=up_count,
            down_count=down_count,
            flat_count=flat_count,
            total_count=count,
            activity_score=activity_score,
        )

    def _calculate_activity_score(
        self,
        avg_turnover: float,
        avg_change: float,
        up_count: int,
        down_count: int,
        total: int,
    ) -> float:
        """
        计算活跃度评分

        Args:
            avg_turnover: 平均换手率
            avg_change: 平均涨跌幅
            up_count: 上涨股票数
            down_count: 下跌股票数
            total: 总股票数

        Returns:
            活跃度评分 (0-100)
        """
        turnover_score = min(avg_turnover * 5, 30)

        change_score = min(abs(avg_change) * 3, 20)

        direction_score = abs(up_count - down_count) / total * 30 if total > 0 else 0

        participation_score = min((up_count + down_count) / total * 20 if total > 0 else 0, 20)

        return min(turnover_score + change_score + direction_score + participation_score, 100)

    def predict_etf(
        self,
        etf_name: str,
        stocks: list[dict[str, Any]],
    ) -> ETFPrediction | None:
        """
        预测ETF表现

        Args:
            etf_name: ETF名称
            stocks: 相关股票列表

        Returns:
            ETF预测结果
        """
        # 检查是否是指数基金
        if etf_name in self.INDEX_FUND_MAPPING:
            return self.predict_index_fund(etf_name)

        # 行业ETF使用股票活跃度分析
        if etf_name not in self.ETF_MAPPING:
            return None

        etf_info = self.ETF_MAPPING[etf_name]
        related_stocks = [s for s in stocks if etf_info["stocks_filter"](s)]

        if not related_stocks:
            return None

        metrics = self.analyze_activity(related_stocks)

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

        confidence = self._calculate_confidence(metrics, len(related_stocks))

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
        """
        预测指数基金表现（使用指数市场数据）

        Args:
            index_name: 指数名称

        Returns:
            ETF预测结果
        """
        if index_name not in self.INDEX_FUND_MAPPING:
            return None

        index_info = self.INDEX_FUND_MAPPING[index_name]

        # 加载指数市场数据
        domestic_cache_file = self.cache_path / "market_index_domestic.json"
        if not domestic_cache_file.exists():
            return None

        try:
            with open(domestic_cache_file, encoding="utf-8") as f:
                data = json.load(f)

            index_data = data.get("指数数据", {})

            # 查找匹配的指数
            index_change = None

            for key in index_info["index_keys"]:
                for index_name_in_data, idx_data in index_data.items():
                    if key in index_name_in_data or index_name_in_data in key:
                        index_change = idx_data.get("涨跌幅", 0)
                        break
                if index_change is not None:
                    break

            # 如果没找到，尝试直接匹配
            if index_change is None:
                for index_name_in_data, idx_data in index_data.items():
                    if index_name in index_name_in_data:
                        index_change = idx_data.get("涨跌幅", 0)
                        break

            if index_change is None:
                return None

            # 检查数据更新时间
            update_time_str = data.get("更新时间", "")
            confidence = 99.0  # 默认置信度

            if update_time_str:
                try:
                    from datetime import datetime, timedelta

                    update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    age = now - update_time

                    # 根据数据新鲜度调整置信度
                    if age > timedelta(hours=24):
                        confidence = 85.0  # 数据较旧
                    elif age > timedelta(hours=4):
                        confidence = 90.0  # 数据一般
                    else:
                        confidence = 99.0  # 数据新鲜
                except Exception as e:
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

        except Exception as e:
            print(f"预测指数基金失败: {e}")
            return None

    def _calculate_confidence(self, metrics: ActivityMetrics, stock_count: int) -> float:
        """
        计算预测置信度

        Args:
            metrics: 活跃度指标
            stock_count: 股票数量

        Returns:
            置信度 (0-100)
        """
        count_score = min(stock_count / 50 * 30, 30)

        activity_score = min(metrics.activity_score / 100 * 40, 40)

        direction_score = 30 - abs(metrics.up_count - metrics.down_count) / max(metrics.total_count, 1) * 30

        return min(count_score + activity_score + direction_score, 100)

    def predict_all_etfs(self) -> list[ETFPrediction]:
        """
        预测所有ETF表现

        Returns:
            ETF预测结果列表
        """
        stocks = self.load_market_stocks()

        if not stocks:
            print("❌ 没有市场股票数据，请先运行 'make filter-market-stocks' 获取数据")
            return []

        predictions = []

        for etf_name in self.ETF_MAPPING:
            prediction = self.predict_etf(etf_name, stocks)
            if prediction:
                predictions.append(prediction)

        predictions.sort(key=lambda x: x.predicted_change, reverse=True)

        return predictions

    def get_market_overview(self) -> dict[str, Any]:
        """
        获取市场概览

        Returns:
            市场概览数据
        """
        stocks = self.load_market_stocks()

        if not stocks:
            return {}

        metrics = self.analyze_activity(stocks)

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
        """
        分析所有行业ETF的表现

        Returns:
            行业分析结果列表
        """
        stocks = self.load_market_stocks()

        if not stocks:
            return []

        results = []

        for etf_name, etf_info in self.ETF_MAPPING.items():
            related_stocks = [s for s in stocks if etf_info["stocks_filter"](s)]

            if not related_stocks:
                continue

            metrics = self.analyze_activity(related_stocks)

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

        # 按预测涨跌幅排序
        results.sort(key=lambda x: x["predicted_change"], reverse=True)

        return results

    def get_investment_suggestions(
        self,
        invested_etfs: list[str],
    ) -> dict[str, Any]:
        """
        获取投资建议

        Args:
            invested_etfs: 已投资的ETF列表

        Returns:
            投资建议
        """
        all_industries = self.analyze_all_industries()

        if not all_industries:
            return {}

        # 已投资的行业
        invested = [i for i in all_industries if i["name"] in invested_etfs]

        # 未投资的行业
        not_invested = [i for i in all_industries if i["name"] not in invested_etfs]

        # 热门行业判断：综合评分
        # 条件：预测涨跌 > 0.5% 且 (上涨比例 > 40% 或 活跃度 > 50)
        hot_industries = [
            i for i in not_invested if i["predicted_change"] > 0.5 and (i["up_ratio"] > 0.4 or i["activity_score"] > 50)
        ]

        # 表现差的已投资行业
        weak_industries = [i for i in invested if i["predicted_change"] < -2]

        return {
            "invested": invested,
            "not_invested": not_invested,
            "hot_industries": hot_industries[:5],
            "weak_industries": weak_industries,
            "suggestions": self._generate_suggestions(invested, not_invested),
        }

    def _generate_suggestions(
        self,
        invested: list[dict],
        not_invested: list[dict],
    ) -> list[str]:
        """生成投资建议"""
        suggestions = []

        # 热门行业建议
        hot = [i for i in not_invested if i["predicted_change"] > 1]
        if hot:
            hot_names = [i["name"] for i in hot[:3]]
            suggestions.append(f"💡 热门行业关注: {', '.join(hot_names)} 表现较好，可考虑关注")

        # 弱势行业预警
        weak = [i for i in invested if i["predicted_change"] < -2]
        if weak:
            weak_names = [i["name"] for i in weak]
            suggestions.append(f"⚠️ 持仓预警: {', '.join(weak_names)} 表现较弱，注意风险")

        # 活跃度高的行业
        active = [i for i in not_invested if i["activity_score"] > 60]
        if active:
            active_names = [i["name"] for i in active[:3]]
            suggestions.append(f"🔥 活跃行业: {', '.join(active_names)} 市场活跃度高")

        # 换手率高的行业
        high_turnover = [i for i in not_invested if i["avg_turnover"] > 5]
        if high_turnover:
            suggestions.append(f"📊 高换手行业: {', '.join([i['name'] for i in high_turnover[:3]])} 资金关注度高")

        return suggestions


stock_activity_analyzer = StockActivityAnalyzer()
