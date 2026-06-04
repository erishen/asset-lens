import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, cast

from ..config import config
from .fetchers.base import FetcherCacheMixin
from .market_stock_prices import MarketStockPricesMixin
from .market_stock_sources import MarketStockSourcesMixin

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


class MarketStockFetcher(
    FetcherCacheMixin,
    MarketStockSourcesMixin,
    MarketStockPricesMixin,
):
    INDUSTRY_KEYWORDS: ClassVar[dict[str, list[str]]] = {
        "AI算力": [
            "AI", "人工智能", "算力", "芯片", "GPU", "深度学习", "机器学习", "智能",
            "中科曙光", "浪潮信息", "寒武纪", "海光信息", "景嘉微",
        ],
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
        self._init_cache(
            cache_path or config.cache_path,
            default_ttl=86400,
        )

    @property
    def market_stock_cache_file(self) -> Path:
        return self.cache_path / "market_stocks.json"

    def infer_industry(self, name: str, code: str = "") -> str:
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
        try:
            stocks = []

            df = self.akshare.stock_zh_a_spot_em()

            if df is None or df.empty:
                logger.error("获取A股数据失败")
                return []

            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            df_page = df.iloc[start_idx:end_idx]

            for _, row in df_page.iterrows():
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))

                if not code or not name:
                    continue

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

        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"获取A股股票列表数据解析失败: {e}")
            return []
        except (RuntimeError, ConnectionError) as e:
            logger.error(f"获取A股股票列表失败: {e}")
            return []

    def fetch_all_cn_stocks(self, max_pages: int = 10) -> list[dict[str, Any]]:
        all_stocks = []

        try:
            all_stocks = self._fetch_stocks_tushare()
            if all_stocks:
                self.save_market_stocks(all_stocks)
                return all_stocks
        except (ImportError, ConnectionError) as e:
            logger.warning(f"Tushare 连接/导入失败: {e}")
        except RuntimeError as e:
            logger.warning(f"Tushare 获取失败: {e}")

        logger.info("Tushare 获取失败，尝试腾讯财经...")
        try:
            all_stocks = self._fetch_stocks_tencent()
            if all_stocks:
                self.save_market_stocks(all_stocks)
                return all_stocks
        except (ImportError, ConnectionError) as e:
            logger.warning(f"腾讯财经连接/导入失败: {e}")
        except (RuntimeError, ValueError) as e:
            logger.warning(f"腾讯财经获取失败: {e}")

        logger.info("腾讯财经获取失败，尝试 AkShare...")
        try:
            all_stocks = self._fetch_stocks_akshare()
            if all_stocks:
                self.save_market_stocks(all_stocks)
                return all_stocks
        except (ValueError, KeyError) as e:
            logger.warning(f"AkShare 数据解析失败: {e}")
        except (RuntimeError, ConnectionError) as e:
            logger.warning(f"AkShare 获取失败: {e}")

        logger.info("AkShare 获取失败，尝试 Efinance...")
        try:
            all_stocks = self._fetch_stocks_efinance()
            if all_stocks:
                self.save_market_stocks(all_stocks)
                return all_stocks
        except (ImportError, ValueError) as e:
            logger.warning(f"Efinance 导入/数据解析失败: {e}")
        except (RuntimeError, ConnectionError) as e:
            logger.warning(f"Efinance 获取失败: {e}")

        logger.info("Efinance 获取失败，尝试 Baostock...")
        try:
            all_stocks = self._fetch_stocks_baostock()
            if all_stocks:
                self.save_market_stocks(all_stocks)
                return all_stocks
        except (ImportError, ConnectionError) as e:
            logger.warning(f"Baostock 连接/导入失败: {e}")
        except RuntimeError as e:
            logger.warning(f"Baostock 获取失败: {e}")

        logger.error("所有数据源获取失败")
        logger.warning("网络获取失败，尝试使用旧缓存")
        return self.get_cached_market_stocks(max_age_hours=99999)

    def save_market_stocks(self, stocks: list[dict[str, Any]]) -> None:
        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(stocks),
            "data": stocks,
        }

        self._cache.save_file("market_stocks.json", cache_data, ttl=0)

        logger.info(f"市场股票数据已保存到: {self.market_stock_cache_file}")

    def get_cached_market_stocks(self, max_age_hours: int = 24) -> list[dict[str, Any]]:
        data = self._cache.load_file("market_stocks.json", max_age=max_age_hours * 3600)
        if data is not None:
            update_time_str = data.get("update_time", "")
            stocks = data.get("data", [])
            if update_time_str:
                try:
                    update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                    age_hours = (datetime.now() - update_time).total_seconds() / 3600

                    if age_hours < 1:
                        age_str = f"{age_hours * 60:.0f}分钟"
                    elif age_hours < 24:
                        age_str = f"{age_hours:.1f}小时"
                    else:
                        age_str = f"{age_hours / 24:.1f}天"

                    logger.info(f"使用缓存数据: {len(stocks)} 只股票 (缓存时间: {age_str}前)")
                    logger.debug(f"缓存文件: {self.market_stock_cache_file}")
                    logger.debug(f"更新时间: {update_time_str}")
                except (ValueError, TypeError):
                    logger.info(f"使用缓存数据: {len(stocks)} 只股票")
            else:
                logger.info(f"使用缓存数据: {len(stocks)} 只股票")

            return cast(list[dict[str, Any]], stocks)

        logger.info(f"缓存文件不存在或已过期: {self.market_stock_cache_file}")
        return []

    def is_cache_expired(self, max_age_hours: int = 24) -> bool:
        return not self._cache.is_file_valid("market_stocks.json", max_age=max_age_hours * 3600)

    def get_cache_age_hours(self) -> float:
        data = self._cache.load_file("market_stocks.json")
        if data is None:
            return -1

        update_time_str = data.get("update_time", "")
        if not update_time_str:
            return -1

        try:
            update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
            return (datetime.now() - update_time).total_seconds() / 3600
        except (ValueError, TypeError):
            return -1


market_stock_fetcher = MarketStockFetcher()
