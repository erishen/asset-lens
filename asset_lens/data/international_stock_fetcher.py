"""
Hong Kong and US stock data fetcher for asset-lens.
港股和美股数据获取模块

功能:
1. 港股实时行情获取
2. 美股实时行情获取
3. 历史数据获取
"""

import json
import os
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

import requests

from ..config import config


class InternationalStockFetcher:
    """国际股票数据获取器"""

    MAX_RETRIES = 3
    RETRY_DELAY = 2.0

    def __init__(self):
        self.cache_path = config.cache_path
        self.hk_stock_cache = self.cache_path / "hk_stocks.json"
        self.us_stock_cache = self.cache_path / "us_stocks.json"

    def _fetch_with_retry(
        self,
        fetch_func: Callable,
        *args,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        **kwargs,
    ) -> Any | None:
        """
        带重试的数据获取

        Args:
            fetch_func: 获取函数
            max_retries: 最大重试次数
            retry_delay: 重试间隔

        Returns:
            获取结果
        """
        max_retries = max_retries or self.MAX_RETRIES
        retry_delay = retry_delay or self.RETRY_DELAY

        last_exception = None
        for attempt in range(max_retries):
            try:
                return fetch_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"数据获取失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)

        print(f"所有重试失败: {last_exception}")
        return None

    def fetch_hk_stock_quote(self, code: str) -> dict[str, Any] | None:
        """
        获取港股实时行情 - 使用 AlphaVantage MCP 服务

        Args:
            code: 股票代码（如 00700, 09988）

        Returns:
            行情数据
        """

        def _fetch():
            try:
                # 使用 AlphaVantage MCP 服务获取港股数据
                import requests

                # 从环境变量获取 API Key
                api_key = os.getenv("ALPHAVANTAGE_API_KEY", "")

                # 构建 AlphaVantage API 请求
                url = "https://www.alphavantage.co/query"
                params = {"function": "GLOBAL_QUOTE", "symbol": code, "apikey": api_key}

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()
                quote = data.get("Global Quote", {})

                if not quote:
                    return None

                # 解析 AlphaVantage 数据格式
                current_price = float(quote.get("05. price", 0))
                prev_close = float(quote.get("08. previous close", 0))
                change = float(quote.get("09. change", 0))
                change_percent_str = quote.get("10. change percent", "0%").replace("%", "")
                change_percent = float(change_percent_str)

                return {
                    "code": code,
                    "name": quote.get("01. symbol", code),  # AlphaVantage 返回的是代码
                    "current_price": current_price,
                    "change_percent": change_percent,
                    "change_amount": change,
                    "volume": 0,  # AlphaVantage 免费版不包含成交量
                    "amount": 0,
                    "high": float(quote.get("03. high", 0)),
                    "low": float(quote.get("04. low", 0)),
                    "open": float(quote.get("02. open", 0)),
                    "prev_close": prev_close,
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "market": "HK",
                    "data_source": "AlphaVantage_API",
                }

            except Exception as e:
                print(f"AlphaVantage API 获取港股失败: {e}，回退到 AkShare")
                # 回退到原有的 AkShare 实现
                return self._fetch_hk_stock_quote_akshare(code)

        try:
            return self._fetch_with_retry(_fetch)
        except Exception as e:
            print(f"获取港股 {code} 行情失败: {e}")
            return None

    def _fetch_hk_stock_quote_akshare(self, code: str) -> dict[str, Any] | None:
        """
        使用 AkShare 获取港股实时行情（回退方案）

        Args:
            code: 股票代码（如 00700, 09988）

        Returns:
            行情数据
        """
        import akshare as ak

        try:
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
            print(f"AkShare 获取港股 {code} 行情失败: {e}")
            return None

    def fetch_us_stock_quote(self, symbol: str) -> dict[str, Any] | None:
        """
        获取美股实时行情 - 使用 AlphaVantage MCP 服务

        Args:
            symbol: 股票代码（如 AAPL, GOOGL, KO, QQQ）

        Returns:
            行情数据
        """

        def _fetch():
            try:
                # 使用 AlphaVantage API 服务获取美股数据

                # 从环境变量获取 API Key
                api_key = os.getenv("ALPHAVANTAGE_API_KEY", "")

                # 构建 AlphaVantage API 请求
                url = "https://www.alphavantage.co/query"
                params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key}

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()
                quote = data.get("Global Quote", {})

                if not quote:
                    return None

                # 解析 AlphaVantage 数据格式
                current_price = float(quote.get("05. price", 0))
                prev_close = float(quote.get("08. previous close", 0))
                change = float(quote.get("09. change", 0))
                change_percent_str = quote.get("10. change percent", "0%").replace("%", "")
                change_percent = float(change_percent_str)

                return {
                    "code": symbol,
                    "name": quote.get("01. symbol", symbol),  # AlphaVantage 返回的是代码
                    "current_price": current_price,
                    "change_percent": change_percent,
                    "change_amount": change,
                    "volume": 0,  # AlphaVantage 免费版不包含成交量
                    "amount": 0,
                    "high": float(quote.get("03. high", 0)),
                    "low": float(quote.get("04. low", 0)),
                    "open": float(quote.get("02. open", 0)),
                    "prev_close": prev_close,
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "market": "US",
                    "data_source": "AlphaVantage_API",
                }

            except Exception as e:
                print(f"AlphaVantage API 获取失败: {e}，回退到 AkShare")
                # 回退到原有的 AkShare 实现
                return self._fetch_us_stock_quote_akshare(symbol)

        try:
            return self._fetch_with_retry(_fetch)
        except Exception as e:
            print(f"获取美股 {symbol} 行情失败: {e}")
            return None

    def _fetch_us_stock_quote_akshare(self, symbol: str) -> dict[str, Any] | None:
        """
        使用 AkShare 获取美股实时行情（回退方案）

        Args:
            symbol: 股票代码（如 AAPL, GOOGL）

        Returns:
            行情数据
        """
        import akshare as ak

        try:
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
            print(f"AkShare 获取美股 {symbol} 行情失败: {e}")
            return None

    def fetch_hk_stock_history(
        self,
        code: str,
        days: int = 60,
    ) -> dict[str, Any] | None:
        """
        获取港股历史数据

        Args:
            code: 股票代码
            days: 历史天数

        Returns:
            历史数据
        """

        def _fetch():
            import akshare as ak

            df = ak.stock_hk_daily(symbol=code, adjust="qfq")

            if df is None or df.empty:
                return None

            df = df.tail(days)

            history: dict[str, Any] = {
                "code": code,
                "name": "",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "AkShare",
                "market": "HK",
                "klines": [],
            }

            klines_list: list[dict[str, Any]] = history["klines"]

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

        try:
            return self._fetch_with_retry(_fetch)
        except Exception as e:
            print(f"获取港股 {code} 历史数据失败: {e}")
            return None

    def fetch_us_stock_history(
        self,
        symbol: str,
        days: int = 60,
    ) -> dict[str, Any] | None:
        """
        获取美股历史数据

        Args:
            symbol: 股票代码
            days: 历史天数

        Returns:
            历史数据
        """

        def _fetch():
            import akshare as ak

            df = ak.stock_us_daily(symbol=symbol, adjust="qfq")

            if df is None or df.empty:
                return None

            df = df.tail(days)

            history: dict[str, Any] = {
                "code": symbol,
                "name": "",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "AkShare",
                "market": "US",
                "klines": [],
            }

            klines_list: list[dict[str, Any]] = history["klines"]

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

        try:
            return self._fetch_with_retry(_fetch)
        except Exception as e:
            print(f"获取美股 {symbol} 历史数据失败: {e}")
            return None

    def search_hk_stock(self, keyword: str) -> list[dict[str, Any]]:
        """
        搜索港股

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的股票列表
        """

        def _fetch():
            import akshare as ak

            df = ak.stock_hk_spot_em()

            if df is None or df.empty:
                return []

            mask = (df["代码"].str.contains(keyword, na=False)) | (df["名称"].str.contains(keyword, na=False))
            result = df[mask]

            return [
                {"code": str(row.get("代码", "")), "name": str(row.get("名称", ""))} for _, row in result.iterrows()
            ]

        try:
            return self._fetch_with_retry(_fetch) or []
        except Exception:
            return []

    def search_us_stock(self, keyword: str) -> list[dict[str, Any]]:
        """
        搜索美股

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的股票列表
        """

        def _fetch():
            import akshare as ak

            df = ak.stock_us_spot_em()

            if df is None or df.empty:
                return []

            mask = (df["代码"].str.contains(keyword, na=False)) | (df["名称"].str.contains(keyword, na=False))
            result = df[mask]

            return [
                {"code": str(row.get("代码", "")), "name": str(row.get("名称", ""))} for _, row in result.iterrows()
            ]

        try:
            return self._fetch_with_retry(_fetch) or []
        except Exception:
            return []

    def get_hk_stock_list(self) -> list[dict[str, Any]]:
        """
        获取港股列表

        Returns:
            港股列表
        """

        def _fetch():
            import akshare as ak

            df = ak.stock_hk_spot_em()

            if df is None or df.empty:
                return []

            return [
                {
                    "code": str(row.get("代码", "")),
                    "name": str(row.get("名称", "")),
                    "current_price": float(row.get("最新价", 0)),
                    "change_percent": float(row.get("涨跌幅", 0)),
                    "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                    "amount": float(row.get("成交额", 0)) if row.get("成交额") else 0,
                }
                for _, row in df.iterrows()
            ]

        try:
            return self._fetch_with_retry(_fetch) or []
        except Exception:
            return []

    def get_us_stock_list(self) -> list[dict[str, Any]]:
        """
        获取美股列表

        Returns:
            美股列表
        """

        def _fetch():
            import akshare as ak

            df = ak.stock_us_spot_em()

            if df is None or df.empty:
                return []

            return [
                {
                    "code": str(row.get("代码", "")),
                    "name": str(row.get("名称", "")),
                    "current_price": float(row.get("最新价", 0)),
                    "change_percent": float(row.get("涨跌幅", 0)),
                    "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                    "amount": float(row.get("成交额", 0)) if row.get("成交额") else 0,
                }
                for _, row in df.iterrows()
            ]

        try:
            return self._fetch_with_retry(_fetch) or []
        except Exception:
            return []

    def fetch_futures_quote(self, symbol: str) -> dict[str, Any] | None:
        """
        获取期货行情

        Args:
            symbol: 期货代码（如 AU0, CU0）

        Returns:
            行情数据
        """

        def _fetch():
            import akshare as ak

            df = ak.futures_main_sina()

            if df is None or df.empty:
                return None

            row = df[df["symbol"] == symbol]

            if row.empty:
                return None

            row = row.iloc[0]

            return {
                "code": str(row.get("symbol", "")),
                "name": str(row.get("name", "")),
                "current_price": float(row.get("trade", 0)),
                "change_percent": float(row.get("changepercent", 0)),
                "change_amount": float(row.get("change", 0)),
                "volume": float(row.get("volume", 0)) if row.get("volume") else 0,
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "market": "Futures",
                "data_source": "AkShare",
            }

        try:
            return self._fetch_with_retry(_fetch)
        except Exception as e:
            print(f"获取期货 {symbol} 行情失败: {e}")
            return None

    def save_hk_stocks_cache(self, stocks: list[dict[str, Any]]) -> None:
        """保存港股缓存"""
        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": stocks,
        }
        with open(self.hk_stock_cache, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def load_hk_stocks_cache(self) -> list[dict[str, Any]]:
        """加载港股缓存"""
        if not self.hk_stock_cache.exists():
            return []
        try:
            with open(self.hk_stock_cache, encoding="utf-8") as f:
                data = json.load(f)
                return list(data.get("data", []))
        except Exception:
            return []

    def save_us_stocks_cache(self, stocks: list[dict[str, Any]]) -> None:
        """保存美股缓存"""
        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": stocks,
        }
        with open(self.us_stock_cache, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def load_us_stocks_cache(self) -> list[dict[str, Any]]:
        """加载美股缓存"""
        if not self.us_stock_cache.exists():
            return []
        try:
            with open(self.us_stock_cache, encoding="utf-8") as f:
                data = json.load(f)
                return list(data.get("data", []))
        except Exception:
            return []


international_stock_fetcher = InternationalStockFetcher()
