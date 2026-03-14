"""
Futures data fetcher for asset-lens.
期货数据获取模块 - 获取国内外期货行情数据

数据源:
- AkShare (国内期货)
- 新浪财经 (国际期货)
- Investing.com (通过 akshare)
"""

import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..config import config


class FuturesFetcher:
    """期货数据获取器"""

    CACHE_DURATION = 60  # 1分钟缓存

    DOMESTIC_FUTURES = {
        "AU0": {"name": "黄金", "exchange": "SHFE", "unit": "克/人民币"},
        "AG0": {"name": "白银", "exchange": "SHFE", "unit": "千克/人民币"},
        "CU0": {"name": "铜", "exchange": "SHFE", "unit": "吨/人民币"},
        "AL0": {"name": "铝", "exchange": "SHFE", "unit": "吨/人民币"},
        "ZN0": {"name": "锌", "exchange": "SHFE", "unit": "吨/人民币"},
        "PB0": {"name": "铅", "exchange": "SHFE", "unit": "吨/人民币"},
        "NI0": {"name": "镍", "exchange": "SHFE", "unit": "吨/人民币"},
        "SN0": {"name": "锡", "exchange": "SHFE", "unit": "吨/人民币"},
        "RB0": {"name": "螺纹钢", "exchange": "SHFE", "unit": "吨/人民币"},
        "HC0": {"name": "热轧卷板", "exchange": "SHFE", "unit": "吨/人民币"},
        "I0": {"name": "铁矿石", "exchange": "DCE", "unit": "吨/人民币"},
        "J0": {"name": "焦炭", "exchange": "DCE", "unit": "吨/人民币"},
        "JM0": {"name": "焦煤", "exchange": "DCE", "unit": "吨/人民币"},
        "A0": {"name": "豆一", "exchange": "DCE", "unit": "吨/人民币"},
        "M0": {"name": "豆粕", "exchange": "DCE", "unit": "吨/人民币"},
        "Y0": {"name": "豆油", "exchange": "DCE", "unit": "吨/人民币"},
        "P0": {"name": "棕榈油", "exchange": "DCE", "unit": "吨/人民币"},
        "C0": {"name": "玉米", "exchange": "DCE", "unit": "吨/人民币"},
        "CS0": {"name": "玉米淀粉", "exchange": "DCE", "unit": "吨/人民币"},
        "SR0": {"name": "白糖", "exchange": "CZCE", "unit": "吨/人民币"},
        "CF0": {"name": "棉花", "exchange": "CZCE", "unit": "吨/人民币"},
        "TA0": {"name": "PTA", "exchange": "CZCE", "unit": "吨/人民币"},
        "MA0": {"name": "甲醇", "exchange": "CZCE", "unit": "吨/人民币"},
        "OI0": {"name": "菜籽油", "exchange": "CZCE", "unit": "吨/人民币"},
        "IC0": {"name": "中证500", "exchange": "CFFEX", "unit": "点"},
        "IF0": {"name": "沪深300", "exchange": "CFFEX", "unit": "点"},
        "IH0": {"name": "上证50", "exchange": "CFFEX", "unit": "点"},
        "IM0": {"name": "中证1000", "exchange": "CFFEX", "unit": "点"},
    }

    INTERNATIONAL_FUTURES = {
        "XAUUSD": {"name": "黄金", "exchange": "COMEX", "unit": "盎司/美元"},
        "XAGUSD": {"name": "白银", "exchange": "COMEX", "unit": "盎司/美元"},
        "CL": {"name": "原油", "exchange": "NYMEX", "unit": "桶/美元"},
        "NG": {"name": "天然气", "exchange": "NYMEX", "unit": "MMBtu/美元"},
        "GC": {"name": "黄金", "exchange": "COMEX", "unit": "盎司/美元"},
        "SI": {"name": "白银", "exchange": "COMEX", "unit": "盎司/美元"},
        "HG": {"name": "铜", "exchange": "COMEX", "unit": "磅/美元"},
    }

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_time: Dict[str, float] = {}
        self._akshare = None

    @property
    def akshare(self):
        """延迟加载 AkShare"""
        if self._akshare is None:
            try:
                import akshare as ak

                self._akshare = ak
            except ImportError:
                raise ImportError("请先安装 AkShare: pip install akshare")
        return self._akshare

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache_time:
            return False
        return time.time() - self._cache_time[cache_key] < self.CACHE_DURATION

    def _get_cached(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存数据"""
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None

    def _set_cache(self, cache_key: str, data: Dict[str, Any]):
        """设置缓存"""
        self._cache[cache_key] = data
        self._cache_time[cache_key] = time.time()

    def fetch_domestic_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取国内期货行情

        Args:
            symbol: 期货代码（如 AU0, CU0）

        Returns:
            行情数据
        """
        cache_key = f"domestic_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:

            def _fetch():
                df = self.akshare.futures_main_sina()
                if df is None or df.empty:
                    return None
                row = df[df["symbol"] == symbol]
                if row.empty:
                    return None
                row = row.iloc[0]
                return {
                    "symbol": symbol,
                    "name": self.DOMESTIC_FUTURES.get(symbol, {}).get("name", symbol),
                    "exchange": self.DOMESTIC_FUTURES.get(symbol, {}).get(
                        "exchange", ""
                    ),
                    "current_price": float(row.get("最新价", 0)),
                    "change": float(row.get("涨跌额", 0)),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "open": float(row.get("今开", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "volume": int(row.get("成交量", 0)),
                    "hold": int(row.get("持仓量", 0)),
                    "settlement": float(row.get("结算价", 0)),
                    "previous_settlement": float(row.get("昨结算", 0)),
                    "unit": self.DOMESTIC_FUTURES.get(symbol, {}).get("unit", ""),
                    "fetched_at": datetime.now().isoformat(),
                }

            result = self._fetch_with_retry(_fetch)
            if result:
                self._set_cache(cache_key, result)
            return result

        except Exception as e:
            print(f"获取期货 {symbol} 行情失败: {e}")
            return None

    def fetch_all_domestic_quotes(self) -> List[Dict[str, Any]]:
        """
        获取所有国内期货行情

        Returns:
            行情列表
        """
        cache_key = "all_domestic"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:

            def _fetch():
                df = self.akshare.futures_main_sina()
                if df is None or df.empty:
                    return []
                result = []
                for _, row in df.iterrows():
                    symbol = row.get("symbol", "")
                    result.append(
                        {
                            "symbol": symbol,
                            "name": self.DOMESTIC_FUTURES.get(symbol, {}).get(
                                "name", symbol
                            ),
                            "exchange": self.DOMESTIC_FUTURES.get(symbol, {}).get(
                                "exchange", ""
                            ),
                            "current_price": float(row.get("最新价", 0)),
                            "change": float(row.get("涨跌额", 0)),
                            "change_pct": float(row.get("涨跌幅", 0)),
                            "open": float(row.get("今开", 0)),
                            "high": float(row.get("最高", 0)),
                            "low": float(row.get("最低", 0)),
                            "volume": int(row.get("成交量", 0)),
                            "hold": int(row.get("持仓量", 0)),
                            "fetched_at": datetime.now().isoformat(),
                        }
                    )
                return result

            result = self._fetch_with_retry(_fetch)
            if result:
                self._set_cache(cache_key, result)
            return result or []

        except Exception as e:
            print(f"获取所有期货行情失败: {e}")
            return []

    def fetch_domestic_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取国内期货历史数据

        Args:
            symbol: 期货代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            历史数据列表
        """
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")

            df = self.akshare.futures_main_sina(symbol, start_date=start_date, end_date=end_date)
            if df is None or df.empty:
                return []

            result = []
            for _, row in df.iterrows():
                result.append(
                    {
                        "date": row.get("date", ""),
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                        "volume": int(row.get("volume", 0)),
                        "hold": int(row.get("hold", 0)),
                    }
                )
            return result

        except Exception as e:
            print(f"获取期货 {symbol} 历史数据失败: {e}")
            return []

    def get_commodity_index(self) -> Dict[str, Any]:
        """
        获取商品指数

        Returns:
            商品指数数据
        """
        try:
            df = self.akshare.futures_display_main_sina()
            if df is None or df.empty:
                return {}

            result = {}
            for _, row in df.iterrows():
                name = row.get("index_name", "")
                result[name] = {
                    "name": name,
                    "current": float(row.get("current", 0)),
                    "change": float(row.get("change", 0)),
                    "change_pct": float(row.get("change_pct", 0)),
                }
            return result

        except Exception as e:
            print(f"获取商品指数失败: {e}")
            return {}

    def _fetch_with_retry(self, fetch_func, max_retries: int = 3, retry_delay: float = 2.0):
        """带重试的获取"""
        last_error = None
        for attempt in range(max_retries):
            try:
                return fetch_func()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        print(f"重试 {max_retries} 次后仍失败: {last_error}")
        return None


_futures_fetcher: Optional[FuturesFetcher] = None


def get_futures_fetcher() -> FuturesFetcher:
    """获取期货数据获取器单例"""
    global _futures_fetcher
    if _futures_fetcher is None:
        _futures_fetcher = FuturesFetcher()
    return _futures_fetcher
