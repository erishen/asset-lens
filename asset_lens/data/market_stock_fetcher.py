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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar

from ..config import config


@contextmanager
def _disable_proxy() -> Generator[None, None, None]:
    """临时禁用代理的上下文管理器"""
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


class MarketStockFetcher:
    """市场股票列表获取器 - 使用 AkShare 开源库"""

    INDUSTRY_KEYWORDS: ClassVar[dict[str, list[str]]] = {
        "AI算力": ["AI", "人工智能", "算力", "芯片", "GPU", "深度学习", "机器学习", "智能", "中科曙光", "浪潮信息", "寒武纪", "海光信息", "景嘉微"],
        "新能源": ["新能源", "锂电", "光伏", "风电", "储能", "宁德", "比亚迪", "亿纬", "隆基", "通威", "天齐", "赣锋"],
        "半导体": ["半导体", "芯片", "集成电路", "中芯", "华虹", "北方华创", "韦尔", "兆易", "紫光", "长电", "通富"],
        "医药": ["医药", "生物", "医疗", "制药", "药明", "恒瑞", "片仔癀", "云南白药", "长春高新", "智飞", "沃森"],
        "消费": ["消费", "食品", "饮料", "家电", "零售", "茅台", "五粮液", "伊利", "海天", "美的", "格力", "海尔"],
        "军工": ["军工", "航天", "兵器", "中航", "航发", "沈飞", "成飞", "西飞", "中兵"],
        "金融": ["银行", "证券", "保险", "招商银行", "平安", "中信", "兴业", "浦发", "民生", "工商", "建设"],
        "科技": ["科技", "软件", "互联网", "腾讯", "阿里", "百度", "美团", "京东", "小米", "华为"],
        "地产": ["地产", "房地产", "万科", "保利", "恒大", "碧桂园", "融创"],
        "汽车": ["汽车", "整车", "比亚迪", "长城", "吉利", "上汽", "广汽", "长安", "一汽"],
        "有色金属": ["有色", "金属", "铜", "铝", "锌", "紫金", "洛阳钼业", "中国铝业"],
        "煤炭": ["煤炭", "煤业", "中国神华", "陕西煤业", "兖矿"],
        "电力": ["电力", "水电", "火电", "风电", "长江电力", "华能", "国电"],
        "化工": ["化工", "化学", "万华", "恒力", "荣盛", "桐昆"],
        "通信": ["通信", "5G", "中兴", "烽火", "亨通", "新易盛", "光通信", "光纤"],
        "白酒": ["白酒", "茅台", "五粮液", "泸州老窖", "洋河", "汾酒", "酒鬼酒"],
        "银行": ["银行", "招商银行", "平安银行", "兴业银行", "浦发银行", "民生银行"],
        "电子": ["电子", "精密", "电路", "PCB", "东山精密", "鹏鼎", "深南电路"],
    }

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
                ) from None
        return self._akshare

    def infer_industry(self, name: str, code: str = "") -> str:
        """
        根据股票名称和代码推断行业

        Args:
            name: 股票名称
            code: 股票代码

        Returns:
            行业名称
        """
        name_lower = name.lower()

        for industry, keywords in self.INDUSTRY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in name_lower:
                    return industry

        if code.startswith("601318") or "平安" in name:
            return "金融"
        if code.startswith("601899") or "紫金" in name:
            return "有色金属"
        if code.startswith("600519"):
            return "白酒"
        if code.startswith("300750"):
            return "新能源"
        if code.startswith("300502"):
            return "通信"

        return "其他"

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
                        "industry": self.infer_industry(name, full_code),
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
        1. Tushare（需要Token，数据最完整）
        2. 腾讯财经（最稳定，速度快）
        3. AkShare（数据全，但东方财富API不稳定）
        4. Efinance（同上）
        5. Baostock（稳定但需要补充价格数据）

        Args:
            max_pages: 最大页数（AkShare一次性获取，此参数忽略）

        Returns:
            股票列表
        """
        all_stocks = []

        # 优先使用 Tushare（数据最完整）
        try:
            all_stocks = self._fetch_stocks_tushare()
            if all_stocks:
                self.save_market_stocks(all_stocks)
                return all_stocks
        except Exception as e:
            print(f"Tushare 获取失败: {e}")

        print("Tushare 获取失败，尝试腾讯财经...")
        try:
            all_stocks = self._fetch_stocks_tencent()
            if all_stocks:
                self.save_market_stocks(all_stocks)
                return all_stocks
        except Exception as e:
            print(f"腾讯财经获取失败: {e}")

        print("腾讯财经获取失败，尝试 AkShare...")
        try:
            all_stocks = self._fetch_stocks_akshare()
            if all_stocks:
                self.save_market_stocks(all_stocks)
                return all_stocks
        except Exception as e:
            print(f"AkShare 获取失败: {e}")

        print("AkShare 获取失败，尝试 Efinance...")
        try:
            all_stocks = self._fetch_stocks_efinance()
            if all_stocks:
                self.save_market_stocks(all_stocks)
                return all_stocks
        except Exception as e:
            print(f"Efinance 获取失败: {e}")

        print("Efinance 获取失败，尝试 Baostock...")
        try:
            all_stocks = self._fetch_stocks_baostock()
            if all_stocks:
                self.save_market_stocks(all_stocks)
                return all_stocks
        except Exception as e:
            print(f"Baostock 获取失败: {e}")

        print("所有数据源获取失败")
        print("⚠️ 网络获取失败，尝试使用旧缓存")
        return self.get_cached_market_stocks(max_age_hours=99999)  # 忽略缓存过期时间

    def _fetch_stocks_tushare(self) -> list[dict[str, Any]]:
        """使用 Tushare 获取A股列表（需要Token，数据最完整）"""
        import os
        import tempfile

        try:
            os.environ["HOME"] = tempfile.gettempdir()
            import tushare as ts

            token = os.environ.get("TUSHARE_TOKEN", "")
            if not token:
                print("⚠️ Tushare Token 未配置，跳过")
                return []

            print("正在获取A股股票列表(Tushare)...")
            print("🌐 API请求: https://tushare.pro (Tushare)")

            ts.set_token(token)
            pro = ts.pro_api()

            df = pro.stock_basic(exchange="", list_status="L", fields="ts_code,symbol,name,area,industry,list_date")

            if df is None or df.empty:
                print("❌ Tushare: 获取数据为空")
                return []

            stocks = []
            for _, row in df.iterrows():
                ts_code = str(row.get("ts_code", ""))
                symbol = str(row.get("symbol", ""))
                name = str(row.get("name", ""))
                industry = str(row.get("industry", ""))

                if not symbol or not name:
                    continue

                # 转换代码格式
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
                        else self.infer_industry(name, full_code),
                        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

            print(f"✅ Tushare: 获取 {len(stocks)} 只股票")

            # 用腾讯财经补充实时价格
            stocks = self._enrich_prices_tencent(stocks)

            return stocks

        except ImportError:
            print("⚠️ Tushare 未安装: pip install tushare")
            return []
        except Exception as e:
            print(f"❌ Tushare 获取失败: {e}")
            return []

    def _fetch_stocks_tencent(self) -> list[dict[str, Any]]:
        """使用腾讯财经获取A股列表（最稳定的数据源）

        策略：直接使用腾讯财经API获取股票列表和实时价格
        """
        try:
            import requests

            print("正在获取A股股票列表(腾讯财经)...")

            # 国内 API 不需要代理
            with _disable_proxy():
                session = requests.Session()

                # 获取沪市股票列表
                sh_url = "https://qt.gtimg.cn/q=s_sh"
                r = session.get(sh_url, timeout=10)

                if r.status_code != 200:
                    print(f"❌ 腾讯财经: HTTP {r.status_code}")
                    return []

                # 解析股票列表 - 腾讯财经不提供完整列表，使用缓存或Baostock
                print("腾讯财经不提供完整股票列表，尝试 Baostock...")

                import baostock as bs

                lg = bs.login()
                if lg.error_code != "0":
                    print(f"❌ Baostock 登录失败: {lg.error_msg}")
                    return []

                rs = bs.query_stock_basic()
                if rs.error_code != "0":
                    print(f"❌ Baostock 查询失败: {rs.error_msg}")
                    bs.logout()
                    return []

                data_list = []
                while rs.error_code == "0" and rs.next():
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
                            "industry": self.infer_industry(name, full_code),
                            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

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
            error_msg = str(e).split("\n")[0][:50]
            print(f"❌ 腾讯财经获取失败: {error_msg}")
            return []

    def _fetch_stocks_akshare(self) -> list[dict[str, Any]]:
        """使用 AkShare 获取A股列表"""
        try:
            print("正在获取A股股票列表(AkShare)...")
            print("🌐 API请求: https://push2.eastmoney.com/api/qt/clist/get (通过AkShare)")

            # 国内 API 不需要代理
            with _disable_proxy():
                df = self.akshare.stock_zh_a_spot_em()

            if df is None or df.empty:
                print("❌ AkShare: 获取数据为空")
                return []

            print(f"✅ AkShare: 共获取 {len(df)} 只A股股票")
            return self._parse_stock_df(df, "akshare")

        except Exception as e:
            error_msg = str(e).split("\n")[0][:50]
            print(f"❌ AkShare 获取失败: {error_msg}")
            return []

    def _fetch_stocks_efinance(self) -> list[dict[str, Any]]:
        """使用 efinance 获取A股列表（备选数据源）"""
        try:
            import efinance as ef

            print("正在获取A股股票列表(Efinance)...")
            print("🌐 API请求: http://push2.eastmoney.com/api/qt/clist/get (通过Efinance)")

            # 国内 API 不需要代理
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
            error_msg = str(e).split("\n")[0][:50]
            print(f"❌ Efinance 获取失败: {error_msg}")
            return []

    def _fetch_stocks_baostock(self) -> list[dict[str, Any]]:
        """使用 Baostock 获取A股列表（备选数据源）"""
        try:
            import baostock as bs

            print("正在获取A股股票列表(Baostock)...")
            print("🌐 API请求: http://www.baostock.com (Baostock)")

            # 国内 API 不需要代理
            with _disable_proxy():
                lg = bs.login()
                if lg.error_code != "0":
                    print(f"❌ Baostock 登录失败: {lg.error_msg}")
                    return []

                rs = bs.query_stock_basic()

                if rs.error_code != "0":
                    print(f"Baostock 查询失败: {rs.error_msg}")
                    bs.logout()
                    return []

                data_list = []
                while rs.error_code == "0" and rs.next():
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
            import requests

            print("正在获取实时价格数据(腾讯财经)...")

            codes = []
            for stock in stocks:
                code = stock.get("code", "")
                if code.startswith("sh") or code.startswith("sz"):
                    codes.append(code)

            all_prices = {}
            batch_size = 100  # 减小批量大小，避免超时

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
                except Exception as e:
                    print(f"  批次 {i // batch_size + 1} 获取失败: {str(e)[:50]}")
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
                    "industry": self.infer_industry(name, full_code),
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
                    "industry": self.infer_industry(name, full_code),
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
                    "industry": self.infer_industry(name, full_code),
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

                now = datetime.now()
                weekday = now.weekday()

                if weekday >= 5:
                    if weekday == 5:
                        friday = now - timedelta(days=1)
                        friday_15pm = friday.replace(hour=15, minute=0, second=0, microsecond=0)
                        cache_from_friday = update_time >= friday_15pm - timedelta(hours=2)
                        if cache_from_friday and age_hours < 72:
                            print(f"📅 周六使用周五缓存数据 (缓存时间: {age_hours:.1f}小时)")
                            return False
                    elif weekday == 6:
                        friday = now - timedelta(days=2)
                        friday_15pm = friday.replace(hour=15, minute=0, second=0, microsecond=0)
                        cache_from_friday = update_time >= friday_15pm - timedelta(hours=2)
                        if cache_from_friday and age_hours < 96:
                            print(f"📅 周日使用周五缓存数据 (缓存时间: {age_hours:.1f}小时)")
                            return False

                if age_hours > max_age_hours:
                    age_str = f"{age_hours:.1f}小时" if age_hours < 48 else f"{age_hours / 24:.1f}天"
                    print(f"⚠️ 缓存已过期: 缓存时间 {age_str}，有效期 {max_age_hours}小时")
                    return True
                else:
                    remaining = max_age_hours - age_hours
                    remaining_str = f"{remaining * 60:.0f}分钟" if remaining < 1 else f"{remaining:.1f}小时"
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
