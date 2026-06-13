import logging
from typing import Any

logger = logging.getLogger(__name__)


class StockFetcherSourcesMixin:
    def _fetch_cn_stock_quote_sina(self, stock_code: str) -> dict[str, Any] | None:
        try:
            import requests

            pure_code = stock_code.replace("sh", "").replace("sz", "")
            prefix = "sh" if stock_code.startswith("6") or stock_code.startswith("sh") else "sz"
            full_code = f"{prefix}{pure_code}"

            url = f"http://hq.sinajs.cn/list={full_code}"
            headers = {
                "Referer": "http://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = "gbk"

            if response.status_code != 200:
                return None

            text = response.text
            pattern = f'var hq_str_{full_code}="'
            start = text.find(pattern)
            if start == -1:
                return None

            start += len(pattern)
            end = text.find('";', start)
            data_str = text[start:end]

            if not data_str:
                return None

            parts = data_str.split(",")
            if len(parts) < 32:
                return None

            name = parts[0]
            open_price = float(parts[1]) if parts[1] else 0
            prev_close = float(parts[2]) if parts[2] else 0
            current_price = float(parts[3]) if parts[3] else 0
            high = float(parts[4]) if parts[4] else 0
            low = float(parts[5]) if parts[5] else 0
            volume = int(float(parts[8]) if parts[8] else 0)
            amount = float(parts[9]) if parts[9] else 0

            if current_price == 0:
                return None

            change_amount = current_price - prev_close
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            return {
                "code": stock_code,
                "name": name,
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": volume,
                "amount": amount,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "sina",
            }

        except (ConnectionError, TimeoutError, ValueError, KeyError, OSError) as e:
            logger.debug(f"新浪财经获取失败 {stock_code}: {e}")
            return None

    def _fetch_cn_stock_quote_baostock(self, stock_code: str) -> dict[str, Any] | None:
        try:
            from asset_lens.data.baostock_session import baostock_session

            bs = baostock_session.bs
            if bs is None:
                return None

            pure_code = stock_code.replace("sh", "").replace("sz", "")
            prefix = "sh" if stock_code.startswith("6") or stock_code.startswith("sh") else "sz"
            bs_code = f"{prefix}.{pure_code}"

            from datetime import datetime, timedelta

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount,turn,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2",
            )

            if rs.error_code != "0":
                return None

            data_list = []
            while rs.error_code == "0" and rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return None

            latest = data_list[-1]
            if len(latest) < 9:
                return None

            current_price = float(latest[4]) if latest[4] else 0
            prev_close = float(data_list[-2][4]) if len(data_list) > 1 and data_list[-2][4] else current_price

            if current_price == 0:
                return None

            change_amount = current_price - prev_close
            change_percent = float(latest[8]) if latest[8] else 0

            return {
                "code": stock_code,
                "name": "",
                "current_price": current_price,
                "open": float(latest[1]) if latest[1] else 0,
                "prev_close": prev_close,
                "high": float(latest[2]) if latest[2] else 0,
                "low": float(latest[3]) if latest[3] else 0,
                "volume": int(float(latest[5]) if latest[5] else 0),
                "amount": float(latest[6]) if latest[6] else 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "baostock",
            }

        except ImportError:
            return None
        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.debug(f"Baostock 获取失败 {stock_code}: {e}")
            return None

    def _fetch_cn_stock_quote_joinquant(self, stock_code: str) -> dict[str, Any] | None:
        try:
            import jqdatasdk as jq

            jq_code = self._convert_to_jq_code(stock_code)
            if not jq_code:
                return None

            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            df = jq.get_price(
                jq_code,
                start_date=start_date,
                end_date=end_date,
                frequency="daily",
                fields=["open", "close", "high", "low", "volume", "money"],
            )

            if df is None or df.empty:
                return None

            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            current_price = float(latest["close"])
            prev_close = float(prev["close"])

            if current_price == 0:
                return None

            change_amount = current_price - prev_close
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            return {
                "code": stock_code,
                "name": "",
                "current_price": current_price,
                "open": float(latest["open"]),
                "prev_close": prev_close,
                "high": float(latest["high"]),
                "low": float(latest["low"]),
                "volume": int(latest["volume"]),
                "amount": float(latest["money"]),
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "joinquant",
            }

        except ImportError:
            return None
        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.debug(f"JoinQuant 获取失败 {stock_code}: {e}")
            return None

    def _convert_to_jq_code(self, stock_code: str) -> str:
        pure_code = stock_code.replace("sh", "").replace("sz", "")
        if stock_code.startswith("6") or stock_code.startswith("sh"):
            return f"{pure_code}.XSHG"
        elif stock_code.startswith(("0", "3")) or stock_code.startswith("sz"):
            return f"{pure_code}.XSHE"
        return ""

    def _fetch_us_stock_quote_yfinance(self, symbol: str) -> dict[str, Any] | None:
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")

            if hist is None or hist.empty:
                return None

            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest

            current_price = float(latest["Close"])
            prev_close = float(prev["Close"])

            if current_price == 0:
                return None

            change_amount = current_price - prev_close
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            return {
                "code": symbol,
                "name": symbol,
                "current_price": current_price,
                "open": float(latest["Open"]),
                "prev_close": prev_close,
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "volume": int(latest["Volume"]),
                "amount": 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "yfinance",
            }

        except ImportError:
            return None
        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.debug(f"yfinance 获取失败 {symbol}: {e}")
            return None

    def _fetch_us_stock_quote_finnhub(self, symbol: str) -> dict[str, Any] | None:
        try:
            import json
            import subprocess

            from ..config import config

            api_key = config.finnhub_api_key or "demo"
            url = f"https://api.finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

            result = subprocess.run(
                ["curl", "-s", "--max-time", "15", url],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            current_price = float(data.get("c", 0))
            prev_close = float(data.get("pc", 0))

            if current_price == 0 or prev_close == 0:
                return None

            change_amount = current_price - prev_close
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            return {
                "code": symbol,
                "name": symbol,
                "current_price": current_price,
                "open": float(data.get("o", 0)),
                "prev_close": prev_close,
                "high": float(data.get("h", 0)),
                "low": float(data.get("l", 0)),
                "volume": 0,
                "amount": 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "finnhub",
            }

        except (OSError, json.JSONDecodeError, ValueError, KeyError) as e:
            logger.debug(f"Finnhub 获取失败 {symbol}: {e}")
            return None

    def _fetch_us_stock_quote_eastmoney(self, symbol: str) -> dict[str, Any] | None:
        try:
            import json
            import subprocess

            em_codes = {
                "AAPL": "105.AAPL",
                "GOOGL": "105.GOOGL",
                "MSFT": "105.MSFT",
                "AMZN": "105.AMZN",
                "TSLA": "105.TSLA",
                "NVDA": "105.NVDA",
                "META": "105.META",
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
            name = item.get("f14", symbol)

            if current_price == 0:
                return None

            prev_close = current_price - change_amount if change_amount else current_price

            return {
                "code": symbol,
                "name": name,
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

        except (OSError, json.JSONDecodeError, ValueError, KeyError) as e:
            logger.debug(f"东方财富获取失败 {symbol}: {e}")
            return None

    def _fetch_us_stock_quote_akshare_full(self, symbol: str) -> dict[str, Any] | None:
        try:
            df = self.akshare.stock_us_spot_em()  # type: ignore[attr-defined]

            if df is None or df.empty:
                return None

            row = df[df["代码"] == symbol]
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
                "code": symbol,
                "name": str(row.get("名称", symbol)),
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

        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.debug(f"AkShare 获取失败 {symbol}: {e}")
            return None
