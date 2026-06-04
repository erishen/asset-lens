import json
import logging
from datetime import datetime
from typing import Any

from ..config import config

logger = logging.getLogger(__name__)


class ForeignIndexFetcherMixin:
    def _fetch_from_akshare_global(self, symbol: str) -> dict[str, Any] | None:
        try:
            ak_names = {
                "^DJI": "道琼斯",
                "^GSPC": "标普500",
                "^IXIC": "纳斯达克",
                "^N225": "日经225",
                "^HSI": "恒生指数",
            }

            ak_name = ak_names.get(symbol)
            if not ak_name:
                return None

            df = self.akshare.index_global_hist_em(symbol=ak_name)  # type: ignore[attr-defined]
            if df is None or df.empty:
                return None

            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            current_price = float(latest.get("最新价", 0))
            prev_close = float(prev.get("最新价", 0))

            if current_price == 0:
                return None

            return {
                "name": ak_name,
                "code": symbol,
                "current_price": current_price,
                "open": float(latest.get("今开", 0)),
                "prev_close": prev_close,
                "high": float(latest.get("最高", 0)),
                "low": float(latest.get("最低", 0)),
                "volume": 0,
                "amount": 0,
                "change_amount": current_price - prev_close,
                "change_percent": float(latest.get("振幅", 0)),
                "source": "akshare",
            }
        except (ValueError, KeyError, TypeError) as e:
            logger.debug(f"AkShare 数据解析失败 {symbol}: {e}")
            return None
        except (ConnectionError, RuntimeError, OSError) as e:
            logger.debug(f"AkShare 获取失败 {symbol}: {e}")
            return None

    def _fetch_from_eastmoney(self, symbol: str) -> dict[str, Any] | None:
        try:
            import subprocess

            em_codes = {
                "^DJI": "100.DJIA",
                "^GSPC": "100.SPX",
                "^IXIC": "100.NDX",
                "^N225": "100.N225",
                "^HSI": "100.HSI",
            }

            em_code = em_codes.get(symbol)
            if not em_code:
                return None

            url = f"http://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids={em_code}&fields=f2,f3,f4,f12,f14"

            result = subprocess.run(
                ["curl", "-s", "--max-time", "15", url],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            diff = data.get("data", {}).get("diff", [])
            if not diff:
                return None

            item = diff[0]
            current_price = float(item.get("f2", 0))
            change_percent = float(item.get("f3", 0))
            change_amount = float(item.get("f4", 0))
            name = item.get("f14", "")

            if current_price == 0:
                return None

            prev_close = current_price - change_amount if change_amount else current_price

            return {
                "name": name,
                "code": symbol,
                "current_price": current_price,
                "open": 0,
                "prev_close": prev_close,
                "high": 0,
                "low": 0,
                "volume": 0,
                "amount": 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "eastmoney",
            }
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            logger.debug(f"东方财富数据解析失败 {symbol}: {e}")
            return None
        except OSError as e:
            logger.debug(f"东方财富IO错误 {symbol}: {e}")
            return None
        except (subprocess.SubprocessError, RuntimeError) as e:
            logger.debug(f"东方财富获取失败 {symbol}: {e}")
            return None

    def _fetch_from_sina_global(self, symbol: str) -> dict[str, Any] | None:
        try:
            import requests

            sina_codes = {
                "^DJI": "gb_dji",
                "^GSPC": "gb_inx",
                "^IXIC": "gb_ixic",
                "^N225": "gb_n225",
                "^HSI": "hkHSI",
            }

            sina_code = sina_codes.get(symbol)
            if not sina_code:
                return None

            url = f"http://hq.sinajs.cn/list={sina_code}"
            headers = {
                "Referer": "http://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = "gbk"
            content = response.text

            pattern = f'var hq_str_{sina_code}="'
            start = content.find(pattern)

            if start == -1:
                logger.warning(f"新浪全球指数 pattern 未找到 {symbol}")
                return None

            start += len(pattern)
            end = content.find('";', start)
            data_str = content[start:end]

            if not data_str:
                return None

            parts = data_str.split(",")

            if sina_code.startswith("hk"):
                current_price = float(parts[6]) if len(parts) > 6 else 0
                prev_close = float(parts[2]) if len(parts) > 2 else 0
                open_price = float(parts[3]) if len(parts) > 3 else 0
                high = float(parts[4]) if len(parts) > 4 else 0
                low = float(parts[5]) if len(parts) > 5 else 0
                name = parts[1] if len(parts) > 1 else ""
            else:
                current_price = float(parts[1]) if len(parts) > 1 else 0
                change_percent = float(parts[2]) if len(parts) > 2 else 0
                change_amount = float(parts[4]) if len(parts) > 4 else 0
                open_price = float(parts[5]) if len(parts) > 5 else 0
                high = float(parts[6]) if len(parts) > 6 else 0
                low = float(parts[7]) if len(parts) > 7 else 0
                prev_close = current_price - change_amount if change_amount else current_price
                name = parts[0] if len(parts) > 0 else ""

            if current_price == 0:
                return None

            change_amount = current_price - prev_close if prev_close > 0 else 0
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            return {
                "name": name,
                "code": symbol,
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": 0,
                "amount": 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "sina_global",
            }
        except (ConnectionError, TimeoutError, ValueError, KeyError, OSError) as e:
            logger.debug(f"新浪全球指数获取失败 {symbol}: {e}")
            return None

    def _fetch_from_finnhub(self, symbol: str) -> dict[str, Any] | None:
        try:
            api_key = config.finnhub_api_key or "demo"
            url = f"https://api.finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

            data = self._http_client.get_json(url, timeout=15)  # type: ignore[attr-defined]
            if data is None:
                return None

            current_price = float(data.get("c", 0))
            prev_close = float(data.get("pc", 0))

            if current_price == 0 or prev_close == 0:
                return None

            return {
                "name": self.FOREIGN_INDEXES.get(symbol, symbol),  # type: ignore[attr-defined]
                "code": symbol,
                "current_price": current_price,
                "open": float(data.get("o", 0)),
                "prev_close": prev_close,
                "high": float(data.get("h", 0)),
                "low": float(data.get("l", 0)),
                "volume": 0,
                "amount": 0,
                "change_amount": current_price - prev_close,
                "change_percent": ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "source": "finnhub",
            }
        except (ConnectionError, TimeoutError, ValueError, KeyError) as e:
            logger.debug(f"Finnhub 获取失败 {symbol}: {e}")
            return None

    def _fetch_from_yahoo(self, symbol: str) -> dict[str, Any] | None:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"

            data = self._http_client.get_json(url, timeout=15)  # type: ignore[attr-defined]
            if data is None:
                return None

            result = data.get("chart", {}).get("result", [])
            if not result:
                return None

            meta = result[0].get("meta", {})
            current_price = float(meta.get("regularMarketPrice", 0))
            prev_close = float(meta.get("previousClose", 0))

            if current_price == 0 or prev_close == 0:
                return None

            return {
                "name": self.FOREIGN_INDEXES.get(symbol, symbol),  # type: ignore[attr-defined]
                "code": symbol,
                "current_price": current_price,
                "open": float(meta.get("regularMarketOpen", 0)),
                "prev_close": prev_close,
                "high": float(meta.get("regularMarketDayHigh", 0)),
                "low": float(meta.get("regularMarketDayLow", 0)),
                "volume": 0,
                "amount": 0,
                "change_amount": current_price - prev_close,
                "change_percent": ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "source": "yahoo",
            }
        except (ConnectionError, TimeoutError, ValueError, KeyError) as e:
            logger.debug(f"Yahoo Finance 获取失败 {symbol}: {e}")
            return None

    def _fetch_from_alpha_vantage(self, symbol: str) -> dict[str, Any] | None:
        try:
            import subprocess

            api_key = config.alphavantage_api_key or "demo"

            symbol_map = {
                "^GSPC": "SPY",
                "^DJI": "DIA",
                "^IXIC": "QQQ",
                "^N225": "EWJ",
                "^HSI": "EWH",
            }

            av_symbol = symbol_map.get(symbol, symbol.replace("^", ""))
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={av_symbol}&apikey={api_key}"

            result = subprocess.run(
                ["curl", "-s", "--max-time", "30", url],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            quote = data.get("Global Quote", {})
            if not quote:
                return None

            current_price = float(quote.get("05. price", 0))
            prev_close = float(quote.get("08. previous close", 0))

            if current_price == 0 or prev_close == 0:
                return None

            return {
                "name": self.FOREIGN_INDEXES.get(symbol, symbol),  # type: ignore[attr-defined]
                "code": symbol,
                "current_price": current_price,
                "open": float(quote.get("02. open", 0)),
                "prev_close": prev_close,
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "volume": int(float(quote.get("06. volume", 0) or 0)),
                "amount": 0,
                "change_amount": current_price - prev_close,
                "change_percent": ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "source": "alpha_vantage",
            }
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError, KeyError) as e:
            logger.debug(f"Alpha Vantage 获取失败 {symbol}: {e}")
            return None

    def fetch_foreign_index(self, symbol: str) -> dict[str, Any] | None:
        cache_key = f"foreign_{symbol}"
        cached = self._get_from_cache(cache_key)  # type: ignore[attr-defined]
        if cached:
            return cached  # type: ignore[no-any-return]

        fetchers = [
            ("sina_global", self._fetch_from_sina_global),
            ("akshare", self._fetch_from_akshare_global),
            ("eastmoney", self._fetch_from_eastmoney),
            ("alpha_vantage", self._fetch_from_alpha_vantage),
            ("finnhub", self._fetch_from_finnhub),
            ("yahoo", self._fetch_from_yahoo),
        ]

        for source_name, fetcher in fetchers:
            try:
                data = fetcher(symbol)
                if data:
                    self._set_cache(cache_key, data)  # type: ignore[attr-defined]
                    logger.info(f"成功从 {source_name} 获取 {symbol}")
                    return data
            except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
                logger.debug(f"{source_name} 获取失败: {e}")
                continue

        logger.error(f"所有数据源都失败: {symbol}")
        return None

    def fetch_all_foreign_indexes(self) -> dict[str, Any]:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        logger.info("正在获取国外市场指数...")

        indexes = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:  # type: ignore[attr-defined]
            future_to_symbol = {
                executor.submit(self.fetch_foreign_index, symbol): symbol for symbol in self.FOREIGN_INDEXES  # type: ignore[attr-defined]
            }

            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                name = self.FOREIGN_INDEXES[symbol]  # type: ignore[attr-defined]

                try:
                    data = future.result()
                    if data:
                        indexes[name] = {
                            "名称": name,
                            "代码": symbol,
                            "最新价": data["current_price"],
                            "涨跌额": data["change_amount"],
                            "涨跌幅": data["change_percent"],
                            "昨收": data["prev_close"],
                            "今开": data["open"],
                            "最高": data["high"],
                            "最低": data["low"],
                            "成交量": data["volume"],
                            "成交额": data["amount"],
                            "数据日期": datetime.now().strftime("%Y-%m-%d"),
                            "数据来源": data.get("source", "未知"),
                        }
                        logger.info(f"✅ {name}: {data['change_percent']:+.2f}%")
                    else:
                        logger.warning(f"❌ {name}: 获取失败")
                except (ValueError, KeyError, RuntimeError) as e:
                    logger.error(f"❌ {name}: {e}")

        from ..utils.json_cache import write_json_cache

        cache_data = {
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "指数数据": indexes,
        }

        write_json_cache(self.foreign_cache_file, cache_data)  # type: ignore[attr-defined]

        return cache_data
