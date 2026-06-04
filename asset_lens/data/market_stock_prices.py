import logging
import math
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MarketStockPricesMixin:
    def _enrich_stock_prices(self, stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not stocks:
            return stocks

        result = self._enrich_prices_tencent(stocks)
        if result and any(s.get("current_price", 0) > 0 for s in result):
            return result

        result = self._enrich_prices_efinance(stocks)
        if result and any(s.get("current_price", 0) > 0 for s in result):
            return result

        logger.error("所有价格数据源获取失败")
        return stocks

    def _enrich_prices_tencent(self, stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        try:
            import requests

            logger.info("正在获取实时价格数据(腾讯财经)...")

            codes = []
            for stock in stocks:
                code = stock.get("code", "")
                if code.startswith("sh") or code.startswith("sz"):
                    codes.append(code)

            all_prices = {}
            batch_size = 100

            session = requests.Session()

            for i in range(0, len(codes), batch_size):
                batch = codes[i : i + batch_size]
                url = "https://qt.gtimg.cn/q=" + ",".join(batch)

                try:
                    resp = session.get(url, timeout=30)
                    resp.encoding = "gbk"

                    for line in resp.text.strip().split("\n"):
                        if not line or "~" not in line:
                            continue
                        try:
                            if "=" not in line:
                                continue
                            key_part, value_part = line.split("=", 1)
                            code_raw = key_part.replace("v_", "").replace("_", "").lower()

                            parts = value_part.strip('"').split("~")
                            if len(parts) < 35:
                                continue

                            price = float(parts[3]) if parts[3] else 0
                            change_percent = float(parts[32]) if parts[32] else 0
                            volume = float(parts[6]) if parts[6] else 0
                            amount = float(parts[37]) if len(parts) > 37 and parts[37] else 0
                            turnover_rate = float(parts[38]) if len(parts) > 38 and parts[38] else 0
                            market_cap = float(parts[45]) if len(parts) > 45 and parts[45] else 0

                            all_prices[code_raw] = {
                                "price": price,
                                "change_percent": change_percent,
                                "volume": int(volume),
                                "amount": amount,
                                "turnover_rate": turnover_rate,
                                "market_cap": market_cap / 100000000 if market_cap > 0 else 0,
                            }
                        except (ValueError, IndexError):
                            continue
                except (ConnectionError, TimeoutError) as e:
                    logger.warning(f"批次 {i // batch_size + 1} 网络错误: {str(e)[:50]}")
                    continue
                except (ValueError, RuntimeError) as e:
                    logger.warning(f"批次 {i // batch_size + 1} 获取失败: {str(e)[:50]}")
                    continue

            enriched = 0
            for stock in stocks:
                code = stock.get("code", "").lower()
                if code in all_prices:
                    price_data = all_prices[code]
                    stock["current_price"] = price_data["price"]
                    stock["change_percent"] = price_data["change_percent"]
                    stock["volume"] = price_data["volume"]
                    stock["amount"] = price_data["amount"]
                    stock["turnover_rate"] = price_data["turnover_rate"]
                    stock["market_cap"] = (
                        price_data["market_cap"] if price_data["market_cap"] > 0 else stock.get("market_cap", 0)
                    )
                    enriched += 1

            logger.info(f"腾讯财经: 已补充 {enriched} 只股票的实时价格")
            return stocks

        except (ImportError, ConnectionError) as e:
            logger.warning(f"腾讯财经导入/网络错误: {e}")
            return stocks
        except (ValueError, KeyError, RuntimeError) as e:
            logger.error(f"腾讯财经获取失败: {e}")
            return stocks

    def _enrich_prices_efinance(self, stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        try:
            import efinance as ef

            logger.info("正在获取实时价格数据(Efinance)...")
            df = ef.stock.get_realtime_quotes()

            if df is None or df.empty:
                logger.warning("Efinance: 获取数据为空")
                return stocks

            price_map = {}
            for _, row in df.iterrows():
                code = str(row.get("股票代码", ""))
                if code:
                    price_map[code] = {
                        "price": row.get("最新价", 0),
                        "change_percent": row.get("涨跌幅", 0),
                        "volume": row.get("成交量", 0),
                        "amount": row.get("成交额", 0),
                    }

            enriched = 0
            for stock in stocks:
                code = stock.get("code", "")
                pure_code = code.replace("sh", "").replace("sz", "")

                if pure_code in price_map:
                    price_data = price_map[pure_code]
                    stock["current_price"] = price_data["price"]
                    stock["change_percent"] = price_data["change_percent"]
                    stock["volume"] = price_data["volume"]
                    stock["amount"] = price_data["amount"]
                    enriched += 1

            logger.info(f"Efinance: 已补充 {enriched} 只股票的实时价格")
            return stocks

        except ImportError:
            logger.warning("Efinance 未安装")
            return stocks
        except (ValueError, KeyError) as e:
            logger.error(f"Efinance 数据解析失败: {e}")
            return stocks
        except (RuntimeError, ConnectionError) as e:
            logger.error(f"Efinance 获取失败: {e}")
            return stocks

    def _parse_stock_df(self, df, source: str = "akshare") -> list[dict[str, Any]]:
        all_stocks = []

        def safe_float(val, default=0):
            try:
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    return default
                return float(val)
            except (ValueError, TypeError):
                return default

        for _, row in df.iterrows():
            code = str(row.get("代码", ""))
            name = str(row.get("名称", ""))

            if not code or not name:
                continue

            full_code = ""
            if code.startswith("6"):
                full_code = f"sh{code}"
            elif code.startswith(("0", "3")):
                full_code = f"sz{code}"
            elif code.startswith("68"):
                full_code = f"sh{code}"
            else:
                continue

            try:
                price = safe_float(row.get("最新价", 0))
                change_percent = safe_float(row.get("涨跌幅", 0))
                volume = safe_float(row.get("成交量", 0))
                amount = safe_float(row.get("成交额", 0))
                turnover_rate = safe_float(row.get("换手率", 0))
                pe_ratio = safe_float(row.get("市盈率-动态", 0))
                market_cap = safe_float(row.get("总市值", 0)) / 100000000
            except (ValueError, TypeError):
                continue

            all_stocks.append(
                {
                    "code": full_code,
                    "name": name,
                    "current_price": price,
                    "change_percent": change_percent,
                    "volume": int(volume),
                    "amount": amount,
                    "turnover_rate": turnover_rate,
                    "pe_ratio": pe_ratio,
                    "market_cap": market_cap,
                    "market": "A股",
                    "industry": self.infer_industry(name, full_code),  # type: ignore[attr-defined]
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return all_stocks

    def _parse_stock_df_efinance(self, df) -> list[dict[str, Any]]:
        all_stocks = []

        def safe_float(val, default=0):
            try:
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    return default
                return float(val)
            except (ValueError, TypeError):
                return default

        for _, row in df.iterrows():
            code = str(row.get("股票代码", ""))
            name = str(row.get("股票名称", ""))

            if not code or not name:
                continue

            full_code = ""
            if code.startswith("6"):
                full_code = f"sh{code}"
            elif code.startswith(("0", "3")):
                full_code = f"sz{code}"
            elif code.startswith("68"):
                full_code = f"sh{code}"
            else:
                continue

            try:
                price = safe_float(row.get("最新价", 0))
                change_percent = safe_float(row.get("涨跌幅", 0))
                volume = safe_float(row.get("成交量", 0))
                amount = safe_float(row.get("成交额", 0))
                turnover_rate = 0
                pe_ratio = 0
                market_cap = 0
            except (ValueError, TypeError):
                continue

            all_stocks.append(
                {
                    "code": full_code,
                    "name": name,
                    "current_price": price,
                    "change_percent": change_percent,
                    "volume": int(volume),
                    "amount": amount,
                    "turnover_rate": turnover_rate,
                    "pe_ratio": pe_ratio,
                    "market_cap": market_cap,
                    "market": "A股",
                    "industry": self.infer_industry(name, full_code),  # type: ignore[attr-defined]
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return all_stocks

    def _parse_stock_list_baostock(self, data_list: list) -> list[dict[str, Any]]:
        all_stocks = []

        for row in data_list:
            if len(row) < 6:
                continue

            code = str(row[0]) if row[0] else ""
            name = str(row[1]) if row[1] else ""
            stock_type = str(row[4]) if len(row) > 4 else ""
            status = str(row[5]) if len(row) > 5 else ""

            if not code or not name:
                continue

            if stock_type != "1":
                continue

            if status != "1":
                continue

            full_code = code.replace(".", "")

            if not (full_code.startswith("sh") or full_code.startswith("sz")):
                continue

            all_stocks.append(
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

        logger.info(f"Baostock 解析完成: {len(all_stocks)} 只A股")
        return all_stocks
