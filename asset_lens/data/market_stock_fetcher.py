"""
Market stock list fetcher for asset-lens.
市场股票列表获取模块 - 获取A股、港股、美股市场股票列表

数据源: AkShare (开源免费，无需注册)
- GitHub: https://github.com/akfamily/akshare
- 文档: https://akshare.akfamily.xyz
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import config


class MarketStockFetcher:
    """市场股票列表获取器 - 使用 AkShare 开源库"""

    def __init__(self, cache_path: Optional[Path] = None):
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

    def fetch_cn_stock_list(self, page: int = 1, page_size: int = 100) -> List[Dict[str, Any]]:
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
                elif code.startswith(("68")):
                    full_code = f"sh{code}"
                else:
                    continue

                try:
                    price = float(row.get("最新价", 0)) if row.get("最新价") else 0
                    change_percent = float(row.get("涨跌幅", 0)) if row.get("涨跌幅") else 0
                    volume = float(row.get("成交量", 0)) if row.get("成交量") else 0
                    amount = float(row.get("成交额", 0)) if row.get("成交额") else 0
                    turnover_rate = float(row.get("换手率", 0)) if row.get("换手率") else 0
                    pe_ratio = float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else 0
                    market_cap = float(row.get("总市值", 0)) / 100000000 if row.get("总市值") else 0
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

    def fetch_all_cn_stocks(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """
        获取所有A股股票

        Args:
            max_pages: 最大页数（AkShare一次性获取，此参数忽略）

        Returns:
            股票列表
        """
        try:
            all_stocks = []

            # 使用 AkShare 一次性获取所有A股数据
            print("正在获取A股股票列表...")
            df = self.akshare.stock_zh_a_spot_em()

            if df is None or df.empty:
                print("获取A股数据失败")
                return []

            print(f"共获取 {len(df)} 只A股股票")

            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))

                if not code or not name:
                    continue

                # 判断市场
                full_code = ""
                if code.startswith("6"):
                    full_code = f"sh{code}"
                elif code.startswith(("0", "3")):
                    full_code = f"sz{code}"
                elif code.startswith(("68")):
                    full_code = f"sh{code}"
                else:
                    continue

                try:
                    price = float(row.get("最新价", 0)) if row.get("最新价") else 0
                    change_percent = float(row.get("涨跌幅", 0)) if row.get("涨跌幅") else 0
                    volume = float(row.get("成交量", 0)) if row.get("成交量") else 0
                    amount = float(row.get("成交额", 0)) if row.get("成交额") else 0
                    turnover_rate = float(row.get("换手率", 0)) if row.get("换手率") else 0
                    pe_ratio = float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else 0
                    market_cap = float(row.get("总市值", 0)) / 100000000 if row.get("总市值") else 0
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

        except Exception as e:
            print(f"获取所有A股股票失败: {e}")
            return []

    def save_market_stocks(self, stocks: List[Dict[str, Any]]) -> None:
        """保存市场股票数据"""
        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(stocks),
            "data": stocks,
        }

        with open(self.market_stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 市场股票数据已保存到: {self.market_stock_cache_file}")

    def get_cached_market_stocks(self) -> List[Dict[str, Any]]:
        """获取缓存的市场股票数据"""
        if self.market_stock_cache_file.exists():
            with open(self.market_stock_cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("data", [])  # type: ignore
        return []


market_stock_fetcher = MarketStockFetcher()
