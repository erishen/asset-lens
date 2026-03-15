"""
Volume breakout filter for asset-lens.
放量突破筛选模块 - 检测放量突破信号
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import config


@dataclass
class VolumeBreakoutConfig:
    """放量突破筛选配置"""

    turnover_ratio: float = 3.0
    amount_ratio: float = 2.0
    market_cap_max: float = 500.0
    market_cap_min: float = 20.0
    price_min: float = 5.0
    price_max: float = 100.0
    require_hot_industry: bool = True
    max_results: int = 30
    use_api_history: bool = True


class VolumeBreakoutFilter:
    """放量突破筛选器"""

    INDUSTRY_MAPPING = {
        "新能源": ["锂电", "光伏", "风电", "储能", "新能源", "电池", "硅料"],
        "半导体": ["半导体", "芯片", "集成电路", "晶圆", "封测", "光刻"],
        "医药": ["医药", "生物", "医疗", "制药", "疫苗", "中药", "CXO"],
        "消费": ["消费", "食品", "饮料", "家电", "零售", "白酒", "啤酒"],
        "军工": ["军工", "航空", "航天", "兵器", "国防", "雷达"],
        "科技": ["科技", "软件", "互联网", "人工智能", "大数据", "云计算"],
        "金融": ["银行", "证券", "保险", "信托", "期货"],
        "地产": ["地产", "房地产", "物业", "建筑"],
        "能源": ["石油", "煤炭", "天然气", "电力", "能源"],
        "材料": ["钢铁", "有色", "化工", "水泥", "材料"],
        "汽车": ["汽车", "新能源车", "零部件", "整车"],
        "通信": ["通信", "5G", "光纤", "基站"],
    }

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or config.project_root / "config" / "volume_breakout.json"
        self.filter_config = self._load_config()
        self.cache_path = config.cache_path
        self.market_stock_file = self.cache_path / "market_stocks.json"
        self.history_file = self.cache_path / "stock_history.json"

    def _load_config(self) -> VolumeBreakoutConfig:
        if not self.config_path.exists():
            return VolumeBreakoutConfig()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return VolumeBreakoutConfig(
                turnover_ratio=data.get("turnover_ratio", 3.0),
                amount_ratio=data.get("amount_ratio", 2.0),
                market_cap_max=data.get("market_cap_max", 500.0),
                market_cap_min=data.get("market_cap_min", 20.0),
                price_min=data.get("price_min", 5.0),
                price_max=data.get("price_max", 100.0),
                require_hot_industry=data.get("require_hot_industry", True),
                max_results=data.get("max_results", 30),
                use_api_history=data.get("use_api_history", True),
            )
        except Exception:
            return VolumeBreakoutConfig()

    def _get_industry(self, name: str) -> Optional[str]:
        """根据股票名称推断行业"""
        for industry, keywords in self.INDUSTRY_MAPPING.items():
            for kw in keywords:
                if kw in name:
                    return industry
        return None

    def _load_market_stocks(self) -> List[Dict[str, Any]]:
        """加载市场股票数据"""
        if self.market_stock_file.exists():
            with open(self.market_stock_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("data", [])  # type: ignore
        return []

    def _load_history(self) -> Dict[str, Any]:
        """加载历史数据"""
        if self.history_file.exists():
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)  # type: ignore
        return {}

    def _save_history(self, history: Dict[str, Any]) -> None:
        """保存历史数据"""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def update_history(self, stocks: List[Dict[str, Any]]) -> None:
        """更新历史数据（每日运行时调用）"""
        history = self._load_history()
        today = datetime.now().strftime("%Y-%m-%d")

        for stock in stocks:
            code = stock.get("code", "")
            if not code:
                continue

            if code not in history:
                history[code] = {
                    "name": stock.get("name", ""),
                    "turnover_rates": [],
                    "amounts": [],
                    "dates": [],
                }

            entry = history[code]
            entry["name"] = stock.get("name", "")
            entry["turnover_rates"].append(stock.get("turnover_rate", 0))
            entry["amounts"].append(stock.get("amount", 0))
            entry["dates"].append(today)

            if len(entry["turnover_rates"]) > 60:
                entry["turnover_rates"] = entry["turnover_rates"][-60:]
                entry["amounts"] = entry["amounts"][-60:]
                entry["dates"] = entry["dates"][-60:]

        self._save_history(history)

    def _get_avg_turnover_60d(self, code: str, history: Dict[str, Any]) -> Optional[float]:
        """获取60日平均换手率"""
        if code not in history:
            return None
        rates = history[code].get("turnover_rates", [])
        if len(rates) < 5:
            return None
        return sum(rates[:-1]) / len(rates[:-1]) if len(rates) > 1 else None

    def _get_avg_amount_60d(self, code: str, history: Dict[str, Any]) -> Optional[float]:
        """获取60日平均成交额"""
        if code not in history:
            return None
        amounts = history[code].get("amounts", [])
        if len(amounts) < 5:
            return None
        return sum(amounts[:-1]) / len(amounts[:-1]) if len(amounts) > 1 else None

    def get_hot_industries(self, stocks: List[Dict[str, Any]]) -> List[str]:
        """获取热门行业"""
        industry_stats = {}

        for stock in stocks:
            name = stock.get("name", "")
            industry = self._get_industry(name)
            if not industry:
                continue

            if industry not in industry_stats:
                industry_stats[industry] = {"up": 0, "down": 0, "total": 0}

            change = stock.get("change_percent", 0)
            industry_stats[industry]["total"] += 1
            if change > 0:
                industry_stats[industry]["up"] += 1
            elif change < 0:
                industry_stats[industry]["down"] += 1

        hot_industries = []
        for industry, stats in industry_stats.items():
            if stats["total"] >= 3:
                up_ratio = stats["up"] / stats["total"]
                if up_ratio > 0.5:
                    hot_industries.append(industry)

        return hot_industries

    def filter(self, stocks: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        筛选放量突破股票

        Args:
            stocks: 股票列表，如果为空则从缓存加载

        Returns:
            符合条件的股票列表
        """
        if stocks is None:
            stocks = self._load_market_stocks()

        if not stocks:
            return []

        history = self._load_history()
        hot_industries = self.get_hot_industries(stocks)

        results = []

        for stock in stocks:
            name = stock.get("name", "")
            code = stock.get("code", "")

            for kw in ["ST", "退", "ETF", "基金", "指数"]:
                if kw in name:
                    continue

            price = stock.get("current_price", 0)
            if price < self.filter_config.price_min or price > self.filter_config.price_max:
                continue

            market_cap = stock.get("market_cap", 0)
            if market_cap < self.filter_config.market_cap_min:
                continue
            if self.filter_config.market_cap_max and market_cap > self.filter_config.market_cap_max:
                continue

            turnover = stock.get("turnover_rate", 0)
            avg_turnover = self._get_avg_turnover_60d(code, history)

            turnover_breakout = False
            turnover_ratio = 0
            if avg_turnover and avg_turnover > 0:
                turnover_ratio = turnover / avg_turnover
                if turnover_ratio >= self.filter_config.turnover_ratio:
                    turnover_breakout = True
            elif turnover > 10:
                turnover_breakout = True
                turnover_ratio = turnover / 3

            amount = stock.get("amount", 0)
            avg_amount = self._get_avg_amount_60d(code, history)

            amount_breakout = False
            amount_ratio = 0
            if avg_amount and avg_amount > 0:
                amount_ratio = amount / avg_amount
                if amount_ratio >= self.filter_config.amount_ratio:
                    amount_breakout = True
            elif amount > 500000000:
                amount_breakout = True
                amount_ratio = amount / 250000000

            if not turnover_breakout and not amount_breakout:
                continue

            industry = self._get_industry(name)
            is_hot_industry = industry in hot_industries if industry else False

            if self.filter_config.require_hot_industry and not is_hot_industry:
                continue

            results.append(
                {
                    **stock,
                    "industry": industry,
                    "turnover_ratio": round(turnover_ratio, 2),
                    "amount_ratio": round(amount_ratio, 2),
                    "avg_turnover_60d": round(avg_turnover, 2) if avg_turnover else None,
                    "avg_amount_60d": round(avg_amount / 100000000, 2) if avg_amount else None,
                    "is_hot_industry": is_hot_industry,
                    "breakout_type": self._get_breakout_type(turnover_breakout, amount_breakout),
                }
            )

        results.sort(key=lambda x: x.get("turnover_ratio", 0), reverse=True)
        return results[: self.filter_config.max_results]

    def filter_with_api_history(
        self,
        stocks: Optional[List[Dict[str, Any]]] = None,
        days: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        使用API获取历史数据进行放量突破筛选

        Args:
            stocks: 股票列表，如果为空则从缓存加载
            days: 历史天数

        Returns:
            符合条件的股票列表
        """
        from ..data.stock_history_fetcher import stock_history_fetcher

        if stocks is None:
            stocks = self._load_market_stocks()

        if not stocks:
            return []

        # 第一步：先根据当前市场数据进行预筛选
        print(f"📊 第一步：预筛选 {len(stocks)} 只股票...")
        pre_filtered = []
        for stock in stocks:
            name = stock.get("name", "")
            code = stock.get("code", "")

            # 排除 ST、退市、ETF、北交所 等
            if any(kw in name for kw in ["ST", "退", "ETF", "基金", "指数"]):
                continue

            # 排除北交所股票（sh920xxx, sz8xxxxx）
            if code.startswith("sh92") or code.startswith("sz8"):
                continue

            price = stock.get("current_price", 0)
            if price < self.filter_config.price_min or price > self.filter_config.price_max:
                continue

            market_cap = stock.get("market_cap", 0)
            if market_cap < self.filter_config.market_cap_min:
                continue
            if self.filter_config.market_cap_max and market_cap > self.filter_config.market_cap_max:
                continue

            # 预筛选：换手率 > 3% 或成交额 > 1亿
            turnover = stock.get("turnover_rate", 0)
            amount = stock.get("amount", 0)
            if turnover > 3 or amount > 100000000:
                pre_filtered.append(stock)

        print(f"   预筛选后剩余 {len(pre_filtered)} 只股票")

        if not pre_filtered:
            return []

        # 第二步：只获取预筛选后股票的历史数据
        print(f"📡 第二步：获取 {len(pre_filtered)} 只股票的 {days} 日历史数据...")
        stocks_with_history = stock_history_fetcher.get_stocks_with_history(pre_filtered, days)

        hot_industries = self.get_hot_industries(stocks)
        results = []

        for stock in stocks_with_history:
            name = stock.get("name", "")
            code = stock.get("code", "")

            for kw in ["ST", "退", "ETF", "基金", "指数"]:
                if kw in name:
                    continue

            price = stock.get("current_price", 0)
            if price < self.filter_config.price_min or price > self.filter_config.price_max:
                continue

            market_cap = stock.get("market_cap", 0)
            if market_cap < self.filter_config.market_cap_min:
                continue
            if self.filter_config.market_cap_max and market_cap > self.filter_config.market_cap_max:
                continue

            turnover = stock.get("turnover_rate", 0)
            avg_turnover = stock.get("avg_turnover_rate_60d", 0)

            turnover_breakout = False
            turnover_ratio = 0
            if avg_turnover and avg_turnover > 0:
                turnover_ratio = turnover / avg_turnover
                if turnover_ratio >= self.filter_config.turnover_ratio:
                    turnover_breakout = True
            elif turnover > 10:
                turnover_breakout = True
                turnover_ratio = turnover / 3

            amount = stock.get("amount", 0)
            avg_amount = stock.get("avg_amount_60d", 0)

            amount_breakout = False
            amount_ratio = 0
            if avg_amount and avg_amount > 0:
                amount_ratio = amount / avg_amount
                if amount_ratio >= self.filter_config.amount_ratio:
                    amount_breakout = True
            elif amount > 500000000:
                amount_breakout = True
                amount_ratio = amount / 250000000

            if not turnover_breakout and not amount_breakout:
                continue

            industry = self._get_industry(name)
            is_hot_industry = industry in hot_industries if industry else False

            if self.filter_config.require_hot_industry and not is_hot_industry:
                continue

            results.append(
                {
                    **stock,
                    "industry": industry,
                    "turnover_ratio": round(turnover_ratio, 2),
                    "amount_ratio": round(amount_ratio, 2),
                    "avg_turnover_60d": round(avg_turnover, 2) if avg_turnover else None,
                    "avg_amount_60d": round(avg_amount / 100000000, 2) if avg_amount else None,
                    "is_hot_industry": is_hot_industry,
                    "breakout_type": self._get_breakout_type(turnover_breakout, amount_breakout),
                    "data_source": "API",
                }
            )

        results.sort(key=lambda x: x.get("turnover_ratio", 0), reverse=True)
        return results[: self.filter_config.max_results]

    def _get_breakout_type(self, turnover_breakout: bool, amount_breakout: bool) -> str:
        """获取突破类型"""
        if turnover_breakout and amount_breakout:
            return "量价齐升"
        elif turnover_breakout:
            return "换手突破"
        elif amount_breakout:
            return "成交额突破"
        return "无突破"


volume_breakout_filter = VolumeBreakoutFilter()
