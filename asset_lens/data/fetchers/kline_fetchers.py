"""
K-line data fetchers for different sources.
K线数据获取器 - 不同数据源的K线获取方法
"""

from ...utils.warnings_config import suppress_common_warnings

suppress_common_warnings()

import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class BaostockKlineFetcher:
    """Baostock K线数据获取器"""

    def __init__(self):
        self._logged_in = False

    def login(self) -> bool:
        """登录 Baostock"""
        try:
            import baostock as bs

            lg = bs.login()
            if lg.error_code != "0":
                logger.warning(f"Baostock login failed: {lg.error_msg}")
                return False
            self._logged_in = True
            return True
        except (ImportError, ConnectionError) as e:
            logger.error(f"Baostock connection error: {e}")
            return False
        except (ValueError, RuntimeError) as e:
            logger.error(f"Baostock login error: {e}")
            return False

    def logout(self) -> None:
        """登出 Baostock"""
        try:
            import baostock as bs

            if self._logged_in:
                bs.logout()
                self._logged_in = False
        except (ImportError, ConnectionError) as e:
            logger.warning(f"Baostock logout connection error: {e}")
        except (ValueError, RuntimeError) as e:
            logger.warning(f"Baostock logout error: {e}")

    def fetch_kline(self, code: str, days: int = 60) -> dict[str, Any] | None:
        """获取K线数据"""
        try:
            import baostock as bs

            if not self._logged_in and not self.login():
                return None

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")

            bs_code = code.replace("sh", "sh.").replace("sz", "sz.")
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,code,open,high,low,close,volume,amount",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3",
            )

            if rs.error_code != "0":
                logger.warning(f"Baostock query failed: {rs.error_msg}")
                return None

            data_list = []
            while rs.error_code == "0" and rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return None

            df = pd.DataFrame(data_list, columns=rs.fields)
            df = df.tail(days)

            return {
                "code": code,
                "data": df.to_dict("records"),
                "source": "baostock",
            }
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Baostock data parsing error: {e}")
            return None
        except (ConnectionError, RuntimeError, OSError) as e:
            logger.error(f"Baostock fetch error: {e}")
            return None


class AkshareKlineFetcher:
    """AkShare K线数据获取器"""

    def __init__(self, akshare):
        self.akshare = akshare

    def fetch_kline(self, code: str, days: int = 60) -> dict[str, Any] | None:
        """获取K线数据"""
        try:
            pure_code = code[2:]

            df = self.akshare.stock_zh_a_hist(
                symbol=pure_code,
                period="daily",
                adjust="qfq",
            )

            if df is None or df.empty:
                return None

            df = df.tail(days)

            return {
                "code": code,
                "data": df.to_dict("records"),
                "source": "akshare",
            }
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"AkShare data parsing error: {e}")
            return None
        except (ConnectionError, RuntimeError, OSError) as e:
            logger.error(f"AkShare fetch error: {e}")
            return None


class TushareKlineFetcher:
    """Tushare K线数据获取器"""

    def __init__(self, token: str | None = None):
        self.token = token
        self._pro = None

    @property
    def pro(self):
        if self._pro is None and self.token:
            import tushare as ts  # pylint: disable=import-error

            ts.set_token(self.token)
            self._pro = ts.pro_api()
        return self._pro

    def fetch_kline(self, code: str, days: int = 60) -> dict[str, Any] | None:
        """获取K线数据"""
        try:
            if not self.pro:
                return None

            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")

            ts_code = code.replace("sh", ".SH").replace("sz", ".SZ")

            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                return None

            df = df.tail(days)

            return {
                "code": code,
                "data": df.to_dict("records"),
                "source": "tushare",
            }
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Tushare data parsing error: {e}")
            return None
        except (ConnectionError, RuntimeError, OSError) as e:
            logger.error(f"Tushare fetch error: {e}")
            return None
