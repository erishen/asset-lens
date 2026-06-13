import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@contextmanager
def _disable_proxy() -> Generator[None, None, None]:
    proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]
    original_values = {}

    for var in proxy_vars:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]

    try:
        yield
    finally:
        for var, value in original_values.items():
            os.environ[var] = value


class MarketStockSourcesMixin:
    def _fetch_stocks_tushare(self) -> list[dict[str, Any]]:
        import tempfile

        try:
            os.environ["HOME"] = tempfile.gettempdir()
            import tushare as ts

            token = os.environ.get("TUSHARE_TOKEN", "")
            if not token:
                logger.warning("Tushare Token 未配置，跳过")
                return []

            logger.info("正在获取A股股票列表(Tushare)...")
            logger.debug("API请求: https://tushare.pro (Tushare)")

            ts.set_token(token)
            pro = ts.pro_api()

            df = pro.stock_basic(exchange="", list_status="L", fields="ts_code,symbol,name,area,industry,list_date")

            if df is None or df.empty:
                logger.info(" Tushare: 获取数据为空")
                return []

            stocks = []
            for _, row in df.iterrows():
                ts_code = str(row.get("ts_code", ""))
                symbol = str(row.get("symbol", ""))
                name = str(row.get("name", ""))
                industry = str(row.get("industry", ""))

                if not symbol or not name:
                    continue

                if ts_code.endswith(".SH"):
                    full_code = f"sh{symbol}"
                elif ts_code.endswith(".SZ"):
                    full_code = f"sz{symbol}"
                else:
                    continue

                stocks.append(
                    {
                        "code": full_code,
                        "name": name,
                        "current_price": 0,
                        "change_percent": 0,
                        "volume": 0,
                        "amount": 0,
                        "turnover_rate": 0,
                        "pe_ratio": 0,
                        "market_cap": 0,
                        "market": "A股",
                        "industry": industry
                        if industry and industry != "nan"
                        else self.infer_industry(name, full_code),  # type: ignore[attr-defined]
                        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

            logger.info(f"Tushare: 获取 {len(stocks)} 只股票")

            stocks = self._enrich_prices_tencent(stocks)  # type: ignore[attr-defined]

            return stocks  # type: ignore[no-any-return]

        except ImportError:
            logger.warning(" Tushare 未安装: pip install tushare")
            return []
        except (ValueError, KeyError) as e:
            logger.error(f"Tushare 数据解析失败: {e}")
            return []
        except Exception as e:
            logger.error(f" Tushare 获取失败: {e}")
            return []

    def _fetch_stocks_tencent(self) -> list[dict[str, Any]]:
        try:
            import requests

            logger.info("正在获取A股股票列表(腾讯财经)...")

            with _disable_proxy():
                session = requests.Session()

                sh_url = "https://qt.gtimg.cn/q=s_sh"
                r = session.get(sh_url, timeout=10)

                if r.status_code != 200:
                    logger.info(f" 腾讯财经: HTTP {r.status_code}")
                    return []

                logger.info("腾讯财经不提供完整股票列表，尝试 Baostock...")

                from asset_lens.data.baostock_session import baostock_ctx

                with baostock_ctx() as bs:
                    if bs is None:
                        return []

                    rs = bs.query_stock_basic()
                    if rs.error_code != "0":
                        logger.error(f" Baostock 查询失败: {rs.error_msg}")
                        return []

                    data_list = []
                    while rs.error_code == "0" and rs.next():
                        data_list.append(rs.get_row_data())

                if not data_list:
                    logger.info(" Baostock: 获取数据为空")
                    return []

                stocks = []
                for row in data_list:
                    if len(row) < 6:
                        continue
                    code = str(row[0]) if row[0] else ""
                    name = str(row[1]) if row[1] else ""
                    stock_type = str(row[4]) if len(row) > 4 else ""
                    status = str(row[5]) if len(row) > 5 else ""

                    if not code or not name or stock_type != "1" or status != "1":
                        continue

                    full_code = code.replace(".", "")
                    if not (full_code.startswith("sh") or full_code.startswith("sz")):
                        continue

                    stocks.append(
                        {
                            "code": full_code,
                            "name": name,
                            "current_price": 0,
                            "change_percent": 0,
                            "volume": 0,
                            "amount": 0,
                            "turnover_rate": 0,
                            "pe_ratio": 0,
                            "market_cap": 0,
                            "market": "A股",
                            "industry": self.infer_industry(name, full_code),  # type: ignore[attr-defined]
                            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                logger.info(f"Baostock: 获取 {len(stocks)} 只股票列表")

            logger.debug("API请求: https://qt.gtimg.cn/q= (补充实时价格)")
            stocks = self._enrich_prices_tencent(stocks)  # type: ignore[attr-defined]

            valid_stocks: list[dict[str, Any]] = []
            for s in stocks:
                price = s.get("current_price")
                if isinstance(price, (int, float)) and price > 0:
                    valid_stocks.append(s)

            if valid_stocks:
                logger.info(f"腾讯财经+Baostock: 共获取 {len(valid_stocks)} 只A股股票（有效价格）")
                return valid_stocks

            logger.error(f" 腾讯财经价格补充失败，返回 {len(stocks)} 只股票（无价格）")
            return stocks  # type: ignore[no-any-return]

        except ImportError:
            logger.warning(" Baostock 未安装，跳过此数据源")
            return []
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"腾讯财经网络错误: {e}")
            return []
        except (ValueError, KeyError) as e:
            error_msg = str(e).split("\n")[0][:50]
            logger.error(f" 腾讯财经数据解析失败: {error_msg}")
            return []
        except RuntimeError as e:
            error_msg = str(e).split("\n")[0][:50]
            logger.error(f" 腾讯财经获取失败: {error_msg}")
            return []

    def _fetch_stocks_akshare(self) -> list[dict[str, Any]]:
        try:
            logger.info("正在获取A股股票列表(AkShare)...")
            logger.debug("API请求: https://push2.eastmoney.com/api/qt/clist/get (通过AkShare)")

            with _disable_proxy():
                df = self.akshare.stock_zh_a_spot_em()  # type: ignore[attr-defined]

            if df is None or df.empty:
                logger.info(" AkShare: 获取数据为空")
                return []

            logger.info(f" AkShare: 共获取 {len(df)} 只A股股票")
            return self._parse_stock_df(df, "akshare")  # type: ignore[attr-defined,no-any-return]

        except (ValueError, KeyError) as e:
            error_msg = str(e).split("\n")[0][:50]
            logger.error(f"AkShare 数据解析失败: {error_msg}")
            return []
        except (RuntimeError, ConnectionError) as e:
            error_msg = str(e).split("\n")[0][:50]
            logger.error(f" AkShare 获取失败: {error_msg}")
            return []

    def _fetch_stocks_efinance(self) -> list[dict[str, Any]]:
        try:
            import efinance as ef

            logger.info("正在获取A股股票列表(Efinance)...")
            logger.info(" API请求: http://push2.eastmoney.com/api/qt/clist/get (通过Efinance)")

            with _disable_proxy():
                df = ef.stock.get_realtime_quotes()

            if df is None or df.empty:
                logger.warning("Efinance: 获取数据为空")
                return []

            logger.info(f"Efinance: 共获取 {len(df)} 只A股股票")
            return self._parse_stock_df_efinance(df)  # type: ignore[attr-defined,no-any-return]

        except ImportError:
            logger.warning(" Efinance 未安装，跳过此数据源")
            return []
        except (ValueError, KeyError) as e:
            error_msg = str(e).split("\n")[0][:50]
            logger.error(f"Efinance 数据解析失败: {error_msg}")
            return []
        except (RuntimeError, ConnectionError) as e:
            error_msg = str(e).split("\n")[0][:50]
            logger.error(f" Efinance 获取失败: {error_msg}")
            return []

    def _fetch_stocks_baostock(self) -> list[dict[str, Any]]:
        try:
            from asset_lens.data.baostock_session import baostock_ctx

            logger.info("正在获取A股股票列表(Baostock)...")
            logger.debug("API请求: http://www.baostock.com (Baostock)")

            with _disable_proxy():
                with baostock_ctx() as bs:
                    if bs is None:
                        return []

                    rs = bs.query_stock_basic()

                    if rs.error_code != "0":
                        logger.error(f"Baostock 查询失败: {rs.error_msg}")
                        return []

                    data_list = []
                    while rs.error_code == "0" and rs.next():
                        data_list.append(rs.get_row_data())

            if not data_list:
                logger.warning("Baostock: 获取数据为空")
                return []

            logger.info(f"Baostock: 共获取 {len(data_list)} 只股票")
            stocks = self._parse_stock_list_baostock(data_list)  # type: ignore[attr-defined]

            stocks = self._enrich_stock_prices(stocks)  # type: ignore[attr-defined]

            return stocks  # type: ignore[no-any-return]

        except ImportError:
            logger.warning("Baostock 未安装，跳过此数据源")
            return []
        except (ConnectionError, OSError) as e:
            logger.error(f"Baostock 网络错误: {e}")
            return []
        except (RuntimeError, ValueError) as e:
            logger.error(f"Baostock 获取失败: {e}")
            return []
