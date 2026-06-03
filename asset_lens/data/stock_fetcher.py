import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from ..config import config
from ..utils.http_client import get_session_without_proxy, with_retry
from .fetchers.base import FetcherCacheMixin
from .stock_fetcher_sources import StockFetcherSourcesMixin

logger = logging.getLogger(__name__)


class StockDataFetcher(FetcherCacheMixin, StockFetcherSourcesMixin):
    def __init__(self, cache_path: Path | None = None):
        self._init_cache(
            cache_path or config.cache_path,
            default_ttl=3600,
        )
        self._stock_codes_map: dict[str, str] | None = None

    @property
    def stock_cache_file(self) -> Path:
        return self.cache_path / "stock_quotes.json"

    def _load_stock_codes_config(self) -> dict[str, str]:
        if self._stock_codes_map is not None:
            return self._stock_codes_map

        config_file = config.project_root / "config" / "fund_stock_codes.json"
        result = {}

        data = self._cache.load_file(str(config_file))
        if data is not None:
            try:
                for stock in data.get("stocks", []):
                    name = stock.get("name", "")
                    code = stock.get("code", "")
                    if name and code:
                        result[name] = code

                    for keyword in stock.get("keywords", []):
                        if keyword and code:
                            result[keyword] = code

                self._stock_codes_map = result
                return result
            except (ValueError, KeyError) as e:
                logger.error(f"加载股票代码配置数据解析失败: {e}")
            except (OSError, TypeError, RuntimeError) as e:
                logger.error(f"加载股票代码配置失败: {e}", exc_info=True)

        self._stock_codes_map = {}
        return {}

    def fetch_stock_quote_akshare(self, stock_code: str) -> dict[str, Any] | None:
        if stock_code.startswith(("sh", "sz")):
            result = self._fetch_cn_stock_with_fallback(stock_code)
            return result if isinstance(result, dict) else None
        elif stock_code.startswith("hk"):
            result = self._fetch_hk_stock_quote(stock_code)
            return result if isinstance(result, dict) else None
        else:
            return None

    def _fetch_cn_stock_with_fallback(self, stock_code: str) -> dict[str, Any] | None:
        sources = [
            ("akshare", self._fetch_cn_stock_quote),
            ("sina", self._fetch_cn_stock_quote_sina),
            ("baostock", self._fetch_cn_stock_quote_baostock),
        ]

        for source_name, fetcher in sources:
            try:
                result = fetcher(stock_code)
                if result and result.get("current_price", 0) > 0:
                    logger.debug(f"✅ {source_name} 获取 {stock_code} 成功")
                    return result
                else:
                    logger.debug(f"⚠️ {source_name} 获取 {stock_code} 返回空数据")
            except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
                logger.debug(f"❌ {source_name} 获取 {stock_code} 失败: {e}")
                continue

        logger.warning(f"所有数据源获取 {stock_code} 失败")
        return None

    def _fetch_cn_stock_quote(self, stock_code: str) -> dict[str, Any] | None:
        try:
            pure_code = stock_code.replace("sh", "").replace("sz", "")

            df = self.akshare.stock_zh_a_spot_em()

            if df is None or df.empty:
                return None

            row = df[df["代码"] == pure_code]
            if row.empty:
                return None

            row = row.iloc[0]
            current_price = float(row.get("最新价", 0))
            prev_close = float(row.get("昨收", 0))

            if current_price == 0:
                return None

            change_amount = current_price - prev_close
            change_percent = float(row.get("涨跌幅", 0))

            return {
                "code": stock_code,
                "name": str(row.get("名称", "")),
                "current_price": current_price,
                "open": float(row.get("今开", 0)),
                "prev_close": prev_close,
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "volume": int(float(row.get("成交量", 0) or 0)),
                "amount": float(row.get("成交额", 0) or 0),
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "akshare",
            }

        except (ValueError, KeyError) as e:
            logger.debug(f"AkShare 数据解析失败 {stock_code}: {e}")
            return None
        except (ConnectionError, RuntimeError, OSError) as e:
            logger.debug(f"AkShare 获取失败 {stock_code}: {e}")
            return None

    def _fetch_hk_stock_quote(self, stock_code: str) -> dict[str, Any] | None:
        try:
            pure_code = stock_code.replace("hk", "")

            df = self.akshare.stock_hk_spot_em()

            if df is None or df.empty:
                return None

            row = df[df["代码"] == pure_code]
            if row.empty:
                return None

            row = row.iloc[0]
            current_price = float(row.get("最新价", 0))
            prev_close = float(row.get("昨收", 0))

            if current_price == 0:
                return None

            change_amount = current_price - prev_close
            change_percent = float(row.get("涨跌幅", 0))

            return {
                "code": stock_code,
                "name": str(row.get("名称", "")),
                "current_price": current_price,
                "open": float(row.get("今开", 0)),
                "prev_close": prev_close,
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "volume": int(float(row.get("成交量", 0) or 0)),
                "amount": float(row.get("成交额", 0) or 0),
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "akshare_hk",
            }

        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.debug(f"AkShare 港股获取失败 {stock_code}: {e}")
            return None

    def fetch_us_stock_quote(self, symbol: str) -> dict[str, Any] | None:
        sources = [
            ("eastmoney", self._fetch_us_stock_quote_eastmoney),
            ("finnhub", self._fetch_us_stock_quote_finnhub),
            ("yfinance", self._fetch_us_stock_quote_yfinance),
            ("akshare", self._fetch_us_stock_quote_akshare_full),
        ]

        for source_name, fetcher in sources:
            try:
                result = fetcher(symbol)
                if result and result.get("current_price", 0) > 0:
                    logger.debug(f"✅ {source_name} 获取 {symbol} 成功")
                    return result
            except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
                logger.debug(f"❌ {source_name} 获取 {symbol} 失败: {e}")
                continue

        logger.warning(f"所有数据源获取 {symbol} 失败")
        return None

    def fetch_multiple_stocks(self, stock_codes: list[str]) -> dict[str, Any]:
        results = {}
        for code in stock_codes:
            try:
                if code.startswith(("sh", "sz")):
                    result = self.fetch_stock_quote_akshare(code)
                elif code.startswith("hk"):
                    result = self._fetch_hk_stock_quote(code)
                else:
                    result = self.fetch_us_stock_quote(code)

                if result:
                    results[code] = result
            except (ValueError, KeyError, RuntimeError) as e:
                logger.debug(f"获取 {code} 失败: {e}")

        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(results),
            "data": results,
        }

        self._cache.save_file("stock_quotes.json", cache_data, ttl=0)

        return cache_data

    def get_cached_stocks(self) -> dict[str, Any]:
        data = self._cache.load_file("stock_quotes.json")
        if data is not None:
            return data
        return {}

    def fetch_multiple_stocks_concurrent(
        self,
        stock_codes: list[str],
        max_workers: int = 5,
    ) -> dict[str, Any]:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}

        def fetch_single(code: str) -> tuple[str, dict | None]:
            try:
                if code.startswith(("sh", "sz")):
                    result = self.fetch_stock_quote_akshare(code)
                elif code.startswith("hk"):
                    result = self._fetch_hk_stock_quote(code)
                else:
                    result = self.fetch_us_stock_quote(code)
                return code, result
            except (ValueError, KeyError, RuntimeError, ConnectionError):
                return code, None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_single, code): code for code in stock_codes}

            for future in as_completed(futures):
                code, result = future.result()
                if result:
                    results[code] = result

        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(results),
            "data": results,
        }

        self._cache.save_file("stock_quotes.json", cache_data, ttl=0)

        return cache_data


stock_fetcher = StockDataFetcher()
