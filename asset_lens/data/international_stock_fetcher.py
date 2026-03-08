"""
Hong Kong and US stock data fetcher for asset-lens.
港股和美股数据获取模块

功能:
1. 港股实时行情获取
2. 美股实时行情获取
3. 历史数据获取
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import config


class InternationalStockFetcher:
    """国际股票数据获取器"""

    def __init__(self):
        self.cache_path = config.cache_path
        self.hk_stock_cache = self.cache_path / "hk_stocks.json"
        self.us_stock_cache = self.cache_path / "us_stocks.json"

    def fetch_hk_stock_quote(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取港股实时行情

        Args:
            code: 股票代码（如 00700, 09988）

        Returns:
            行情数据
        """
        try:
            import akshare as ak

            df = ak.stock_hk_spot_em()

            if df is None or df.empty:
                return None

            row = df[df["代码"] == code]

            if row.empty:
                return None

            row = row.iloc[0]

            return {
                "code": str(row.get("代码", "")),
                "name": str(row.get("名称", "")),
                "current_price": float(row.get("最新价", 0)),
                "change_percent": float(row.get("涨跌幅", 0)),
                "change_amount": float(row.get("涨跌额", 0)),
                "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                "amount": float(row.get("成交额", 0)) if row.get("成交额") else 0,
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "open": float(row.get("今开", 0)),
                "prev_close": float(row.get("昨收", 0)),
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "market": "HK",
                "data_source": "AkShare",
            }

        except Exception as e:
            print(f"获取港股 {code} 行情失败: {e}")
            return None

    def fetch_us_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取美股实时行情

        Args:
            symbol: 股票代码（如 AAPL, GOOGL）

        Returns:
            行情数据
        """
        try:
            import akshare as ak

            df = ak.stock_us_spot_em()

            if df is None or df.empty:
                return None

            row = df[df["代码"] == symbol]

            if row.empty:
                return None

            row = row.iloc[0]

            return {
                "code": str(row.get("代码", "")),
                "name": str(row.get("名称", "")),
                "current_price": float(row.get("最新价", 0)),
                "change_percent": float(row.get("涨跌幅", 0)),
                "change_amount": float(row.get("涨跌额", 0)),
                "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                "amount": float(row.get("成交额", 0)) if row.get("成交额") else 0,
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "open": float(row.get("今开", 0)),
                "prev_close": float(row.get("昨收", 0)),
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "market": "US",
                "data_source": "AkShare",
            }

        except Exception as e:
            print(f"获取美股 {symbol} 行情失败: {e}")
            return None

    def fetch_hk_stock_history(
        self,
        code: str,
        days: int = 60,
    ) -> Optional[Dict[str, Any]]:
        """
        获取港股历史数据

        Args:
            code: 股票代码
            days: 历史天数

        Returns:
            历史数据
        """
        try:
            import akshare as ak

            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")

            df = ak.stock_hk_daily(symbol=code, adjust="qfq")

            if df is None or df.empty:
                return None

            df = df.tail(days)

            history: Dict[str, Any] = {
                "code": code,
                "name": "",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "AkShare",
                "market": "HK",
                "klines": [],
            }

            klines_list: List[Dict[str, Any]] = history["klines"]

            for _, row in df.iterrows():
                try:
                    klines_list.append(
                        {
                            "date": str(row.get("日期", "")),
                            "open": float(row.get("开盘", 0)),
                            "close": float(row.get("收盘", 0)),
                            "high": float(row.get("最高", 0)),
                            "low": float(row.get("最低", 0)),
                            "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                            "amount": 0,
                            "amplitude": 0,
                            "change_percent": 0,
                            "change_amount": 0,
                            "turnover_rate": 0,
                        }
                    )
                except (ValueError, TypeError, KeyError):
                    continue

            return history

        except Exception as e:
            print(f"获取港股 {code} 历史数据失败: {e}")
            return None

    def fetch_us_stock_history(
        self,
        symbol: str,
        days: int = 60,
    ) -> Optional[Dict[str, Any]]:
        """
        获取美股历史数据

        Args:
            symbol: 股票代码
            days: 历史天数

        Returns:
            历史数据
        """
        try:
            import akshare as ak

            df = ak.stock_us_daily(symbol=symbol, adjust="qfq")

            if df is None or df.empty:
                return None

            df = df.tail(days)

            history: Dict[str, Any] = {
                "code": symbol,
                "name": "",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "AkShare",
                "market": "US",
                "klines": [],
            }

            klines_list: List[Dict[str, Any]] = history["klines"]

            for _, row in df.iterrows():
                try:
                    klines_list.append(
                        {
                            "date": str(row.get("日期", "")),
                            "open": float(row.get("开盘", 0)),
                            "close": float(row.get("收盘", 0)),
                            "high": float(row.get("最高", 0)),
                            "low": float(row.get("最低", 0)),
                            "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                            "amount": 0,
                            "amplitude": 0,
                            "change_percent": 0,
                            "change_amount": 0,
                            "turnover_rate": 0,
                        }
                    )
                except (ValueError, TypeError, KeyError):
                    continue

            return history

        except Exception as e:
            print(f"获取美股 {symbol} 历史数据失败: {e}")
            return None

    def search_hk_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索港股

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的股票列表
        """
        try:
            import akshare as ak

            df = ak.stock_hk_spot_em()

            if df is None or df.empty:
                return []

            results = []
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))

                if keyword.upper() in code.upper() or keyword in name:
                    results.append(
                        {
                            "code": code,
                            "name": name,
                            "market": "HK",
                        }
                    )

            return results[:20]

        except Exception as e:
            print(f"搜索港股失败: {e}")
            return []

    def search_us_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索美股

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的股票列表
        """
        try:
            import akshare as ak

            df = ak.stock_us_spot_em()

            if df is None or df.empty:
                return []

            results = []
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))

                if keyword.upper() in code.upper() or keyword.upper() in name.upper():
                    results.append(
                        {
                            "code": code,
                            "name": name,
                            "market": "US",
                        }
                    )

            return results[:20]

        except Exception as e:
            print(f"搜索美股失败: {e}")
            return []

    def get_hk_stock_list(self) -> List[Dict[str, Any]]:
        """
        获取港股列表

        Returns:
            港股列表
        """
        try:
            import akshare as ak

            df = ak.stock_hk_spot_em()

            if df is None or df.empty:
                return []

            stocks = []
            for _, row in df.iterrows():
                stocks.append(
                    {
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "current_price": float(row.get("最新价", 0)),
                        "change_percent": float(row.get("涨跌幅", 0)),
                        "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                        "amount": float(row.get("成交额", 0)) if row.get("成交额") else 0,
                        "market": "HK",
                    }
                )

            return stocks

        except Exception as e:
            print(f"获取港股列表失败: {e}")
            return []

    def get_us_stock_list(self) -> List[Dict[str, Any]]:
        """
        获取美股列表

        Returns:
            美股列表
        """
        try:
            import akshare as ak

            df = ak.stock_us_spot_em()

            if df is None or df.empty:
                return []

            stocks = []
            for _, row in df.iterrows():
                stocks.append(
                    {
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "current_price": float(row.get("最新价", 0)),
                        "change_percent": float(row.get("涨跌幅", 0)),
                        "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                        "amount": float(row.get("成交额", 0)) if row.get("成交额") else 0,
                        "market": "US",
                    }
                )

            return stocks

        except Exception as e:
            print(f"获取美股列表失败: {e}")
            return []

    def save_hk_stocks_cache(self, stocks: List[Dict[str, Any]]) -> None:
        """保存港股缓存"""
        data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": stocks,
        }
        with open(self.hk_stock_cache, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_us_stocks_cache(self, stocks: List[Dict[str, Any]]) -> None:
        """保存美股缓存"""
        data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": stocks,
        }
        with open(self.us_stock_cache, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_hk_stocks_cache(self) -> List[Dict[str, Any]]:
        """加载港股缓存"""
        if self.hk_stock_cache.exists():
            with open(self.hk_stock_cache, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
                result = data.get("data", [])
                return result if isinstance(result, list) else []
        return []

    def load_us_stocks_cache(self) -> List[Dict[str, Any]]:
        """加载美股缓存"""
        if self.us_stock_cache.exists():
            with open(self.us_stock_cache, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
                result = data.get("data", [])
                return result if isinstance(result, list) else []
        return []

    def fetch_futures_quote(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取期货行情

        Args:
            code: 期货代码（如 AU0, CU0）

        Returns:
            行情数据
        """
        try:
            import akshare as ak

            df = ak.futures_sina_main_sina()

            if df is None or df.empty:
                return None

            row = df[df["symbol"] == code]

            if row.empty:
                return None

            row = row.iloc[0]

            return {
                "code": str(row.get("symbol", "")),
                "name": str(row.get("name", "")),
                "current_price": float(row.get("trade", 0)) if row.get("trade") else 0,
                "change_percent": float(row.get("changepercent", 0))
                if row.get("changepercent")
                else 0,
                "change_amount": float(row.get("change", 0)) if row.get("change") else 0,
                "volume": float(row.get("volume", 0)) if row.get("volume") else 0,
                "open": float(row.get("open", 0)) if row.get("open") else 0,
                "high": float(row.get("high", 0)) if row.get("high") else 0,
                "low": float(row.get("low", 0)) if row.get("low") else 0,
                "prev_close": float(row.get("settlement", 0)) if row.get("settlement") else 0,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "market": "Futures",
                "data_source": "AkShare",
            }

        except Exception as e:
            print(f"获取期货 {code} 行情失败: {e}")
            return None

    def fetch_futures_history(
        self,
        code: str,
        days: int = 60,
    ) -> Optional[Dict[str, Any]]:
        """
        获取期货历史数据

        Args:
            code: 期货代码
            days: 历史天数

        Returns:
            历史数据
        """
        try:
            import akshare as ak

            df = ak.futures_main_sina(symbol=code)

            if df is None or df.empty:
                return None

            df = df.tail(days)

            history: Dict[str, Any] = {
                "code": code,
                "name": "",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "AkShare",
                "market": "Futures",
                "klines": [],
            }

            klines_list: List[Dict[str, Any]] = history["klines"]

            for _, row in df.iterrows():
                try:
                    klines_list.append(
                        {
                            "date": str(row.get("date", "")),
                            "open": float(row.get("open", 0)) if row.get("open") else 0,
                            "close": float(row.get("close", 0)) if row.get("close") else 0,
                            "high": float(row.get("high", 0)) if row.get("high") else 0,
                            "low": float(row.get("low", 0)) if row.get("low") else 0,
                            "volume": float(row.get("volume", 0)) if row.get("volume") else 0,
                            "amount": 0,
                            "amplitude": 0,
                            "change_percent": 1,
                            "change_amount": 1,
                            "turnover_rate": 1,
                        }
                    )
                except (ValueError, TypeError, KeyError):
                    continue

            return history

        except Exception as e:
            print(f"获取期货 {code} 历史数据失败: {e}")
            return None

    def get_futures_list(self) -> List[Dict[str, Any]]:
        """
        获取期货列表

        Returns:
            期货列表
        """
        try:
            import akshare as ak

            df = ak.futures_sina_main_sina()

            if df is None or df.empty:
                return []

            futures = []
            for _, row in df.iterrows():
                futures.append(
                    {
                        "code": str(row.get("symbol", "")),
                        "name": str(row.get("name", "")),
                        "current_price": float(row.get("trade", 0)) if row.get("trade") else 0,
                        "change_percent": float(row.get("changepercent", 0))
                        if row.get("changepercent")
                        else 0,
                        "volume": float(row.get("volume", 0)) if row.get("volume") else 0,
                        "market": "Futures",
                    }
                )

            return futures

        except Exception as e:
            print(f"获取期货列表失败: {e}")
            return []


international_stock_fetcher = InternationalStockFetcher()
