import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class StockHistorySourcesMixin:
    def fetch_history_baostock(self, code: str, days: int = 60) -> dict[str, Any] | None:
        try:
            import baostock as bs

            if not self._baostock_login_with_retry():
                return None

            bs_code = self._convert_to_bs_code(code)
            if not bs_code:
                return None

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
            from datetime import timedelta

            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2",
            )

            if rs.error_code != "0":
                logger.debug(f"Baostock 查询失败 {code}: {rs.error_msg}")
                return None

            klines = []
            while rs.error_code == "0" and rs.next():
                row = rs.get_row_data()
                if len(row) >= 10:
                    klines.append(
                        {
                            "date": row[0],
                            "code": row[1],
                            "open": float(row[2]) if row[2] else 0,
                            "high": float(row[3]) if row[3] else 0,
                            "low": float(row[4]) if row[4] else 0,
                            "close": float(row[5]) if row[5] else 0,
                            "volume": float(row[6]) if row[6] else 0,
                            "amount": float(row[7]) if row[7] else 0,
                            "turnover_rate": float(row[8]) if row[8] else 0,
                            "change_percent": float(row[9]) if row[9] else 0,
                        }
                    )

            if not klines:
                return None

            latest = klines[-1]
            return {
                "code": code,
                "name": "",
                "klines": klines,
                "latest_price": latest["close"],
                "latest_change": latest["change_percent"],
                "source": "baostock",
            }

        except ImportError:
            logger.debug("Baostock 未安装")
            return None
        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.debug(f"Baostock 获取失败 {code}: {e}")
            return None

    def fetch_history_tushare(self, code: str, days: int = 60) -> dict[str, Any] | None:
        try:
            import os
            import tempfile

            os.environ["HOME"] = tempfile.gettempdir()
            import tushare as ts

            token = os.environ.get("TUSHARE_TOKEN", "")
            if not token:
                return None

            ts.set_token(token)
            pro = ts.pro_api()

            ts_code = self._convert_to_ts_code(code)
            if not ts_code:
                return None

            end_date = datetime.now().strftime("%Y%m%d")
            from datetime import timedelta

            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

            df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

            if df is None or df.empty:
                return None

            df = df.sort_values("trade_date")

            klines = []
            for _, row in df.iterrows():
                klines.append(
                    {
                        "date": str(row["trade_date"]),
                        "code": code,
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["vol"]),
                        "amount": float(row["amount"]),
                        "turnover_rate": 0,
                        "change_percent": float(row.get("pct_chg", 0)),
                    }
                )

            if not klines:
                return None

            latest = klines[-1]
            return {
                "code": code,
                "name": "",
                "klines": klines,
                "latest_price": latest["close"],
                "latest_change": latest["change_percent"],
                "source": "tushare",
            }

        except ImportError:
            return None
        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.debug(f"Tushare 获取失败 {code}: {e}")
            return None

    def fetch_history_akshare(self, code: str, days: int = 60) -> dict[str, Any] | None:
        try:
            pure_code = code.replace("sh", "").replace("sz", "")

            df = self.akshare.stock_zh_a_hist(
                symbol=pure_code,
                period="daily",
                start_date=(datetime.now() - __import__("datetime").timedelta(days=days)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq",
            )

            if df is None or df.empty:
                return None

            klines = []
            for _, row in df.iterrows():
                klines.append(
                    {
                        "date": str(row.get("日期", "")),
                        "code": code,
                        "open": float(row.get("开盘", 0)),
                        "high": float(row.get("最高", 0)),
                        "low": float(row.get("最低", 0)),
                        "close": float(row.get("收盘", 0)),
                        "volume": float(row.get("成交量", 0)),
                        "amount": float(row.get("成交额", 0)),
                        "turnover_rate": float(row.get("换手率", 0)),
                        "change_percent": float(row.get("涨跌幅", 0)),
                    }
                )

            if not klines:
                return None

            latest = klines[-1]
            return {
                "code": code,
                "name": "",
                "klines": klines,
                "latest_price": latest["close"],
                "latest_change": latest["change_percent"],
                "source": "akshare",
            }

        except (ValueError, KeyError) as e:
            logger.debug(f"AkShare 数据解析失败 {code}: {e}")
            return None
        except (ConnectionError, RuntimeError, OSError) as e:
            logger.debug(f"AkShare 获取失败 {code}: {e}")
            return None

    def fetch_history_akshare_daily(self, code: str, days: int = 60) -> dict[str, Any] | None:
        try:
            pure_code = code.replace("sh", "").replace("sz", "")

            df = self.akshare.stock_zh_a_hist_163(
                symbol=pure_code,
                start_date=(datetime.now() - __import__("datetime").timedelta(days=days)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
            )

            if df is None or df.empty:
                return None

            klines = []
            for _, row in df.iterrows():
                klines.append(
                    {
                        "date": str(row.get("日期", "")),
                        "code": code,
                        "open": float(row.get("开盘价", 0) or 0),
                        "high": float(row.get("最高价", 0) or 0),
                        "low": float(row.get("最低价", 0) or 0),
                        "close": float(row.get("收盘价", 0) or 0),
                        "volume": float(row.get("成交量", 0) or 0),
                        "amount": 0,
                        "turnover_rate": 0,
                        "change_percent": 0,
                    }
                )

            if not klines:
                return None

            latest = klines[-1]
            return {
                "code": code,
                "name": "",
                "klines": klines,
                "latest_price": latest["close"],
                "latest_change": 0,
                "source": "akshare_daily",
            }

        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.debug(f"AkShare daily 获取失败 {code}: {e}")
            return None

    def _convert_to_bs_code(self, code: str) -> str:
        if code.startswith("sh"):
            return f"sh.{code[2:]}"
        elif code.startswith("sz"):
            return f"sz.{code[2:]}"
        elif code.startswith("6"):
            return f"sh.{code}"
        elif code.startswith(("0", "3")):
            return f"sz.{code}"
        return ""

    def _convert_to_ts_code(self, code: str) -> str:
        pure = code.replace("sh", "").replace("sz", "")
        if code.startswith("sh") or code.startswith("6"):
            return f"{pure}.SH"
        elif code.startswith("sz") or code.startswith(("0", "3")):
            return f"{pure}.SZ"
        return ""
