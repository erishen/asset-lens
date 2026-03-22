"""
Stock filter module for asset-lens.
股票筛选模块 - 支持可配置的筛选条件
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import config


@dataclass
class StockFilterConfig:
    """股票筛选配置"""

    price_min: float | None = None
    price_max: float | None = None
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    turnover_rate_min: float | None = None
    turnover_rate_max: float | None = None
    change_percent_min: float | None = None
    change_percent_max: float | None = None
    volume_min: int | None = None
    volume_max: int | None = None
    amplitude_min: float | None = None
    amplitude_max: float | None = None
    pe_ratio_min: float | None = None
    pe_ratio_max: float | None = None
    pb_ratio_min: float | None = None
    pb_ratio_max: float | None = None
    exclude_etf: bool = True
    exclude_keywords: list[str] | None = None
    sort_key: str = "turnover_rate"
    sort_direction: str = "desc"
    max_results: int = 50

    def __post_init__(self):
        if self.exclude_keywords is None:
            self.exclude_keywords = ["ETF", "基金", "指数"]


class StockFilter:
    """股票筛选器"""

    def __init__(self, config_path: Path | None = None):
        """
        初始化股票筛选器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or config.project_root / "config" / "stock_filter.json"
        self.filter_config = self._load_config()

    def _load_config(self) -> StockFilterConfig:
        """加载筛选配置"""
        if not self.config_path.exists():
            return StockFilterConfig()

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)

            filters = data.get("filters", {})
            exclude = data.get("exclude", {})
            sort = data.get("sort", {})
            limit = data.get("limit", {})

            price_filter = filters.get("price", {})
            market_cap_filter = filters.get("market_cap", {})
            turnover_rate_filter = filters.get("turnover_rate", {})
            change_percent_filter = filters.get("change_percent", {})
            volume_filter = filters.get("volume", {})
            amplitude_filter = filters.get("amplitude", {})
            pe_ratio_filter = filters.get("pe_ratio", {})
            pb_ratio_filter = filters.get("pb_ratio", {})

            return StockFilterConfig(
                price_min=price_filter.get("min") if price_filter.get("enabled") else None,
                price_max=price_filter.get("max") if price_filter.get("enabled") else None,
                market_cap_min=market_cap_filter.get("min")
                if market_cap_filter.get("enabled")
                else None,
                market_cap_max=market_cap_filter.get("max")
                if market_cap_filter.get("enabled")
                else None,
                turnover_rate_min=turnover_rate_filter.get("min")
                if turnover_rate_filter.get("enabled")
                else None,
                turnover_rate_max=turnover_rate_filter.get("max")
                if turnover_rate_filter.get("enabled")
                else None,
                change_percent_min=change_percent_filter.get("min")
                if change_percent_filter.get("enabled")
                else None,
                change_percent_max=change_percent_filter.get("max")
                if change_percent_filter.get("enabled")
                else None,
                volume_min=volume_filter.get("min") if volume_filter.get("enabled") else None,
                volume_max=volume_filter.get("max") if volume_filter.get("enabled") else None,
                amplitude_min=amplitude_filter.get("min")
                if amplitude_filter.get("enabled")
                else None,
                amplitude_max=amplitude_filter.get("max")
                if amplitude_filter.get("enabled")
                else None,
                pe_ratio_min=pe_ratio_filter.get("min") if pe_ratio_filter.get("enabled") else None,
                pe_ratio_max=pe_ratio_filter.get("max") if pe_ratio_filter.get("enabled") else None,
                pb_ratio_min=pb_ratio_filter.get("min") if pb_ratio_filter.get("enabled") else None,
                pb_ratio_max=pb_ratio_filter.get("max") if pb_ratio_filter.get("enabled") else None,
                exclude_etf=exclude.get("etf", True),
                exclude_keywords=exclude.get("keywords", ["ETF", "基金", "指数"]),
                sort_key=sort.get("key", "turnover_rate"),
                sort_direction=sort.get("direction", "desc"),
                max_results=limit.get("max_results", 50),
            )

        except Exception as e:
            print(f"加载股票筛选配置失败: {e}")
            return StockFilterConfig()

    def filter_stock(self, stock: dict[str, Any]) -> bool:
        """
        检查股票是否符合筛选条件

        Args:
            stock: 股票数据

        Returns:
            是否符合筛选条件
        """
        name = stock.get("name", "")

        if self.filter_config.exclude_etf and self.filter_config.exclude_keywords:
            for keyword in self.filter_config.exclude_keywords:
                if keyword in name:
                    return False

        price = stock.get("current_price", 0)
        if self.filter_config.price_min is not None and price < self.filter_config.price_min:
            return False
        if self.filter_config.price_max is not None and price > self.filter_config.price_max:
            return False

        market_cap = stock.get("market_cap", 0)
        if (
            self.filter_config.market_cap_min is not None
            and market_cap < self.filter_config.market_cap_min
        ):
            return False
        if (
            self.filter_config.market_cap_max is not None
            and market_cap > self.filter_config.market_cap_max
        ):
            return False

        turnover_rate = stock.get("turnover_rate", 0)
        if (
            self.filter_config.turnover_rate_min is not None
            and turnover_rate < self.filter_config.turnover_rate_min
        ):
            return False
        if (
            self.filter_config.turnover_rate_max is not None
            and turnover_rate > self.filter_config.turnover_rate_max
        ):
            return False

        change_percent = stock.get("change_percent", 0)
        if (
            self.filter_config.change_percent_min is not None
            and change_percent < self.filter_config.change_percent_min
        ):
            return False
        if (
            self.filter_config.change_percent_max is not None
            and change_percent > self.filter_config.change_percent_max
        ):
            return False

        volume = stock.get("volume", 0)
        if self.filter_config.volume_min is not None and volume < self.filter_config.volume_min:
            return False
        if self.filter_config.volume_max is not None and volume > self.filter_config.volume_max:
            return False

        amplitude = stock.get("amplitude", 0)
        if (
            self.filter_config.amplitude_min is not None
            and amplitude < self.filter_config.amplitude_min
        ):
            return False
        if (
            self.filter_config.amplitude_max is not None
            and amplitude > self.filter_config.amplitude_max
        ):
            return False

        pe_ratio = stock.get("pe_ratio")
        if pe_ratio is not None and pe_ratio > 0:
            if (
                self.filter_config.pe_ratio_min is not None
                and pe_ratio < self.filter_config.pe_ratio_min
            ):
                return False
            if (
                self.filter_config.pe_ratio_max is not None
                and pe_ratio > self.filter_config.pe_ratio_max
            ):
                return False

        pb_ratio = stock.get("pb_ratio")
        if pb_ratio is not None and pb_ratio > 0:
            if (
                self.filter_config.pb_ratio_min is not None
                and pb_ratio < self.filter_config.pb_ratio_min
            ):
                return False
            if (
                self.filter_config.pb_ratio_max is not None
                and pb_ratio > self.filter_config.pb_ratio_max
            ):
                return False

        return True

    def filter_stocks(self, stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        批量筛选股票

        Args:
            stocks: 股票列表

        Returns:
            筛选后的股票列表
        """
        filtered = [s for s in stocks if self.filter_stock(s)]

        reverse = self.filter_config.sort_direction == "desc"
        sort_key = self.filter_config.sort_key

        if sort_key in [
            "turnover_rate",
            "market_cap",
            "change_percent",
            "volume",
            "amplitude",
            "pe_ratio",
            "pb_ratio",
        ]:
            filtered.sort(key=lambda x: x.get(sort_key, 0), reverse=reverse)

        return filtered[: self.filter_config.max_results]

    def get_filter_summary(self) -> str:
        """获取筛选条件摘要"""
        lines = ["股票筛选条件:"]

        if self.filter_config.price_min is not None or self.filter_config.price_max is not None:
            price_range = f"{self.filter_config.price_min or '无下限'} - {self.filter_config.price_max or '无上限'} 元"
            lines.append(f"  - 价格范围: {price_range}")

        if (
            self.filter_config.market_cap_min is not None
            or self.filter_config.market_cap_max is not None
        ):
            cap_range = f"{self.filter_config.market_cap_min or '无下限'} - {self.filter_config.market_cap_max or '无上限'} 亿元"
            lines.append(f"  - 市值范围: {cap_range}")

        if (
            self.filter_config.turnover_rate_min is not None
            or self.filter_config.turnover_rate_max is not None
        ):
            tr_range = f"{self.filter_config.turnover_rate_min or '无下限'} - {self.filter_config.turnover_rate_max or '无上限'} %"
            lines.append(f"  - 换手率范围: {tr_range}")

        if self.filter_config.exclude_etf and self.filter_config.exclude_keywords:
            lines.append(f"  - 排除关键词: {', '.join(self.filter_config.exclude_keywords)}")

        lines.append(
            f"  - 排序方式: {self.filter_config.sort_key} ({self.filter_config.sort_direction})"
        )
        lines.append(f"  - 最大结果数: {self.filter_config.max_results}")

        return "\n".join(lines)


stock_filter = StockFilter()
