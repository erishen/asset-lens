"""
Market stock list fetcher for asset-lens.
市场股票列表获取模块 - 获取A股、港股、美股市场股票列表

数据源: AkShare (开源免费，无需注册)
- GitHub: https://github.com/akfamily/akshare
- 文档: https://akshare.akfamily.xyz
"""

import json
import os
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import config
from ..utils.http_client import get_session_without_proxy


@contextmanager
def _disable_proxy() -> Generator[None, None, None]:
    """临时禁用代理的上下文管理器"""
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
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


class MarketStockFetcher:
    """市场股票列表获取器 - 使用 AkShare 开源库"""

    def __init__(self, cache_path: Path | None = None):
        """
        初始化市场股票获取器

        Args:
            cache_path: 缓存路径
        """
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.market_stock_cache_file = self.cache_path / "market_stocks.json"
        self._akshare = None

    @property
    def akshare(self):
        """延迟加载 AkShare"""
        if self._akshare is None:
            try:
                import akshare as ak

                self._akshare = ak
            except ImportError:
                raise ImportError(
                    "请先安装 AkShare: pip install akshare\n"
                    "AkShare 是一个开源免费的金融数据接口，无需注册\n"
                    "GitHub: https://github.com/akfamily/akshare"
                )
        return self._akshare

    def fetch_cn_stock_list(self, page: int = 1, page_size: int = 100) -> list[dict[str, Any]]:
        """
        获取A股股票列表（AkShare）

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            股票列表
        """
        try:
            stocks = []

            # 使用 AkShare 获取A股实时行情
            df = self.akshare.stock_zh_a_spot_em()

            if df is None or df.empty:
                print("获取A股数据失败")
                return []

            # 分页处理
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            df_page = df.iloc[start_idx:end_idx]

            for _, row in df_page.iterrows():
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))

                if not code or not name:
                    continue

                # 判断市场
                market = "A股"
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
                    import math

                    def safe_float(val, default=0):
                        """安全转换为浮点数，处理 NaN"""
                        try:
                            if val is None or (isinstance(val, float) and math.isnan(val)):
                                return default
                            return float(val)
                        except (ValueError, TypeError):
                            return default

                    price = safe_float(row.get("最新价", 0))
                    change_percent = safe_float(row.get("涨跌幅", 0))
                    volume = safe_float(row.get("成交量", 0))
                    amount = safe_float(row.get("成交额", 0))
                    turnover_rate = safe_float(row.get("换手率", 0))
                    pe_ratio = safe_float(row.get("市盈率-动态", 0))
                    market_cap = safe_float(row.get("总市值", 0)) / 100000000
                except (ValueError, TypeError):
                    continue

                stocks.append(
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
                        "market": market,
                        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

            return stocks

        except Exception as e:
            print(f"获取A股股票列表失败: {e}")
            return []

    def fetch_all_cn_stocks(self, max_pages: int = 10) -> list[dict[str, Any]]:
        """
        获取所有A股股票（多数据源备选）

        优先级：
        1. 腾讯财经（最稳定，速度快）
        2. AkShare（数据全，但东方财富API不稳定）
        3. Efinance（同上）
        4. Baostock（稳定但需要补充价格数据）

        Args:
            max_pages: 最大页数（AkShare一次性获取，此参数忽略）

        Returns:
            股票列表
        """
        all_stocks = []

        # 优先使用腾讯财经（最稳定）
        try:
            all_stocks = self._fetch_stocks_tencent()
            if all_stocks:
                return all_stocks
        except Exception as e:
            print(f"腾讯财经获取失败: {e}")

        print("腾讯财经获取失败，尝试 AkShare...")
        try:
            all_stocks = self._fetch_stocks_akshare()
            if all_stocks:
                return all_stocks
        except Exception as e:
            print(f"AkShare 获取失败: {e}")

        print("AkShare 获取失败，尝试 Efinance...")
        try:
            all_stocks = self._fetch_stocks_efinance()
            if all_stocks:
                return all_stocks
        except Exception as e:
            print(f"Efinance 获取失败: {e}")

        print("Efinance 获取失败，尝试 Baostock...")
        try:
            all_stocks = self._fetch_stocks_baostock()
            if all_stocks:
                return all_stocks
        except Exception as e:
            print(f"Baostock 获取失败: {e}")

        print("所有数据源获取失败")
        return []

    def _fetch_stocks_tencent(self) -> list[dict[str, Any]]:
        """使用腾讯财经获取A股列表（最稳定的数据源）

        策略：先用Baostock获取股票列表，再用腾讯财经补充实时价格
        """
        try:
            print("正在获取A股股票列表(腾讯财经+Baostock)...")

            # 第一步：用Baostock获取股票列表（稳定可靠）
            import baostock as bs

            lg = bs.login()
            if lg.error_code != '0':
                print(f"❌ Baostock 登录失败: {lg.error_msg}")
                return []

            rs = bs.query_stock_basic()
            if rs.error_code != '0':
                print(f"❌ Baostock 查询失败: {rs.error_msg}")
                bs.logout()
                return []

            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())
            bs.logout()

            if not data_list:
                print("❌ Baostock: 获取数据为空")
                return []

            # 解析股票列表
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

                stocks.append({
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
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })

            print(f"Baostock: 获取 {len(stocks)} 只股票列表")

            # 第二步：用腾讯财经补充实时价格
            print("🌐 API请求: https://qt.gtimg.cn/q= (补充实时价格)")
            stocks = self._enrich_prices_tencent(stocks)

            # 过滤掉没有价格数据的股票（可能是退市或停牌）
            valid_stocks: list[dict[str, Any]] = []
            for s in stocks:
                price = s.get("current_price")
                if isinstance(price, (int, float)) and price > 0:
                    valid_stocks.append(s)

            if valid_stocks:
                print(f"✅ 腾讯财经+Baostock: 共获取 {len(valid_stocks)} 只A股股票（有效价格）")
                return valid_stocks

            print(f"⚠️ 腾讯财经价格补充失败，返回 {len(stocks)} 只股票（无价格）")
            return stocks

        except ImportError:
            print("⚠️ Baostock 未安装，跳过此数据源")
            return []
        except Exception as e:
            error_msg = str(e).split('\n')[0][:50]
            print(f"❌ 腾讯财经获取失败: {error_msg}")
            return []

    def _fetch_stocks_akshare(self) -> list[dict[str, Any]]:
        """使用 AkShare 获取A股列表"""
        try:
            print("正在获取A股股票列表(AkShare)...")
            print("🌐 API请求: https://push2.eastmoney.com/api/qt/clist/get (通过AkShare)")

            with _disable_proxy():
                df = self.akshare.stock_zh_a_spot_em()

            if df is None or df.empty:
                print("❌ AkShare: 获取数据为空")
                return []

            print(f"✅ AkShare: 共获取 {len(df)} 只A股股票")
            return self._parse_stock_df(df, "akshare")

        except Exception as e:
            error_msg = str(e).split('\n')[0][:50]
            print(f"❌ AkShare 获取失败: {error_msg}")
            return []

    def _fetch_stocks_efinance(self) -> list[dict[str, Any]]:
        """使用 efinance 获取A股列表（备选数据源）"""
        try:
            import efinance as ef

            print("正在获取A股股票列表(Efinance)...")
            print("🌐 API请求: http://push2.eastmoney.com/api/qt/clist/get (通过Efinance)")

            with _disable_proxy():
                df = ef.stock.get_realtime_quotes()

            if df is None or df.empty:
                print("❌ Efinance: 获取数据为空")
                return []

            print(f"✅ Efinance: 共获取 {len(df)} 只A股股票")
            return self._parse_stock_df_efinance(df)

        except ImportError:
            print("⚠️ Efinance 未安装，跳过此数据源")
            return []
        except Exception as e:
            error_msg = str(e).split('\n')[0][:50]
            print(f"❌ Efinance 获取失败: {error_msg}")
            return []

    def _fetch_stocks_baostock(self) -> list[dict[str, Any]]:
        """使用 Baostock 获取A股列表（备选数据源）"""
        try:
            import baostock as bs

            print("正在获取A股股票列表(Baostock)...")
            print("🌐 API请求: http://www.baostock.com (Baostock)")

            lg = bs.login()
            if lg.error_code != '0':
                print(f"❌ Baostock 登录失败: {lg.error_msg}")
                return []

            rs = bs.query_stock_basic()

            if rs.error_code != '0':
                print(f"Baostock 查询失败: {rs.error_msg}")
                bs.logout()
                return []

            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            bs.logout()

            if not data_list:
                print("Baostock: 获取数据为空")
                return []

            print(f"Baostock: 共获取 {len(data_list)} 只股票")
            stocks = self._parse_stock_list_baostock(data_list)

            stocks = self._enrich_stock_prices(stocks)

            return stocks

        except ImportError:
            print("Baostock 未安装，跳过此数据源")
            return []
        except Exception as e:
            print(f"Baostock 获取失败: {e}")
            return []

    def _enrich_stock_prices(self, stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """补充股票实时价格数据（多数据源备选）"""
        if not stocks:
            return stocks

        result = self._enrich_prices_tencent(stocks)
        if result and any(s.get("current_price", 0) > 0 for s in result):
            return result

        result = self._enrich_prices_efinance(stocks)
        if result and any(s.get("current_price", 0) > 0 for s in result):
            return result

        print("所有价格数据源获取失败")
        return stocks

    def _enrich_prices_tencent(self, stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """使用腾讯财经补充价格数据"""
        try:
            print("正在获取实时价格数据(腾讯财经)...")

            codes = []
            for stock in stocks:
                code = stock.get("code", "")
                if code.startswith("sh"):
                    codes.append(code)
                elif code.startswith("sz"):
                    codes.append(code)

            all_prices = {}
            batch_size = 100  # 减小批量大小，避免超时

            session = get_session_without_proxy()

            for i in range(0, len(codes), batch_size):
                batch = codes[i:i+batch_size]
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
                except Exception as e:
                    print(f"  批次 {i//batch_size + 1} 获取失败: {str(e)[:50]}")
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
                    stock["market_cap"] = price_data["market_cap"] if price_data["market_cap"] > 0 else stock.get("market_cap", 0)
                    enriched += 1

            print(f"腾讯财经: 已补充 {enriched} 只股票的实时价格")
            return stocks

        except Exception as e:
            print(f"腾讯财经获取失败: {e}")
            return stocks

    def _enrich_prices_efinance(self, stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """使用 Efinance 补充价格数据"""
        try:
            import efinance as ef

            print("正在获取实时价格数据(Efinance)...")
            df = ef.stock.get_realtime_quotes()

            if df is None or df.empty:
                print("Efinance: 获取数据为空")
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

            print(f"Efinance: 已补充 {enriched} 只股票的实时价格")
            return stocks

        except ImportError:
            print("Efinance 未安装")
            return stocks
        except Exception as e:
            print(f"Efinance 获取失败: {e}")
            return stocks

    def _parse_stock_df(self, df, source: str = "akshare") -> list[dict[str, Any]]:
        """解析 AkShare 数据格式"""
        import math

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
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return all_stocks

    def _parse_stock_df_efinance(self, df) -> list[dict[str, Any]]:
        """解析 Efinance 数据格式"""
        import math

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
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return all_stocks

    def _parse_stock_list_baostock(self, data_list: list) -> list[dict[str, Any]]:
        """解析 Baostock 数据格式

        字段: ['code', 'code_name', 'ipoDate', 'outDate', 'type', 'status']
        type: 1=股票, 2=指数, 3=其他
        status: 1=上市, 0=退市
        """
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
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        print(f"Baostock 解析完成: {len(all_stocks)} 只A股")
        return all_stocks

    def save_market_stocks(self, stocks: list[dict[str, Any]]) -> None:
        """保存市场股票数据"""
        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(stocks),
            "data": stocks,
        }

        with open(self.market_stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 市场股票数据已保存到: {self.market_stock_cache_file}")

    def get_cached_market_stocks(self, max_age_hours: int = 24) -> list[dict[str, Any]]:
        """获取缓存的市场股票数据

        Args:
            max_age_hours: 缓存有效期（小时），默认24小时
        """
        if self.market_stock_cache_file.exists():
            try:
                with open(self.market_stock_cache_file, encoding="utf-8") as f:
                    data = json.load(f)

                update_time_str = data.get("update_time", "")
                if update_time_str:
                    update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                    age_hours = (datetime.now() - update_time).total_seconds() / 3600

                    if age_hours < 1:
                        age_str = f"{age_hours * 60:.0f}分钟"
                    elif age_hours < 24:
                        age_str = f"{age_hours:.1f}小时"
                    else:
                        age_str = f"{age_hours / 24:.1f}天"

                    remaining_hours = max_age_hours - age_hours
                    if remaining_hours < 0:
                        remaining_str = "已过期"
                    elif remaining_hours < 1:
                        remaining_str = f"剩余 {remaining_hours * 60:.0f} 分钟"
                    else:
                        remaining_str = f"剩余 {remaining_hours:.1f} 小时"

                    print(f"📦 使用缓存数据: {len(data.get('data', []))} 只股票 (缓存时间: {age_str}前)")
                    print(f"   缓存文件: {self.market_stock_cache_file}")
                    print(f"   更新时间: {update_time_str}")
                    print(f"   有效期: {max_age_hours}小时 ({remaining_str})")
                else:
                    print(f"📦 使用缓存数据: {len(data.get('data', []))} 只股票")

                return list(data.get("data", []))  # type: ignore
            except Exception as e:
                print(f"❌ 读取缓存失败: {e}")
                return []
        else:
            print(f"📦 缓存文件不存在: {self.market_stock_cache_file}")
            return []

    def is_cache_expired(self, max_age_hours: int = 24) -> bool:
        """检查缓存是否过期"""
        if not self.market_stock_cache_file.exists():
            print("📦 缓存不存在，需要重新获取")
            return True

        try:
            with open(self.market_stock_cache_file, encoding="utf-8") as f:
                data = json.load(f)
                update_time_str = data.get("update_time", "")
                if not update_time_str:
                    print("📦 缓存无时间戳，需要重新获取")
                    return True

                update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                age_hours = (datetime.now() - update_time).total_seconds() / 3600

                if age_hours > max_age_hours:
                    if age_hours < 48:
                        age_str = f"{age_hours:.1f}小时"
                    else:
                        age_str = f"{age_hours / 24:.1f}天"
                    print(f"⚠️ 缓存已过期: 缓存时间 {age_str}，有效期 {max_age_hours}小时")
                    return True
                else:
                    remaining = max_age_hours - age_hours
                    if remaining < 1:
                        remaining_str = f"{remaining * 60:.0f}分钟"
                    else:
                        remaining_str = f"{remaining:.1f}小时"
                    print(f"✅ 缓存有效: 剩余有效期 {remaining_str}")
                    return False
        except Exception as e:
            print(f"❌ 检查缓存失败: {e}")
            return True

    def get_cache_age_hours(self) -> float:
        """获取缓存年龄（小时）"""
        if not self.market_stock_cache_file.exists():
            return -1

        try:
            with open(self.market_stock_cache_file, encoding="utf-8") as f:
                data = json.load(f)
                update_time_str = data.get("update_time", "")
                if not update_time_str:
                    return -1

                update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                return (datetime.now() - update_time).total_seconds() / 3600
        except Exception:
            return -1


market_stock_fetcher = MarketStockFetcher()
