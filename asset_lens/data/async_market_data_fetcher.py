"""
Async market data fetcher for asset-lens.
异步市场数据获取模块 - 使用 asyncio 并发获取市场数据

数据源: AkShare (开源免费，无需注册)
- GitHub: https://github.com/akfamily/akshare
- 文档: https://akshare.akfamily.xyz
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from ..config import config


class AsyncMarketDataFetcher:
    """异步市场数据获取器 - 使用 AkShare 开源库"""

    def __init__(self, max_concurrent: int = 5, request_delay: float = 0.1):
        """
        初始化异步数据获取器

        Args:
            max_concurrent: 最大并发数
            request_delay: 请求间隔（秒）
        """
        self.cache_path = config.cache_path
        self.domestic_cache_file = self.cache_path / "market_index_domestic.json"
        self.foreign_cache_file = self.cache_path / "market_index_foreign.json"
        self.max_concurrent = max_concurrent
        self.request_delay = request_delay
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._akshare = None
        self.cache_path.mkdir(parents=True, exist_ok=True)

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

    def fetch_domestic_index_sync(self, index_code: str) -> Optional[Dict[str, Any]]:
        """
        同步获取国内指数数据（AkShare）

        Args:
            index_code: 指数代码

        Returns:
            指数数据字典
        """
        try:
            df = self.akshare.stock_zh_index_spot_em()

            if df is None or df.empty:
                return None

            code = index_code[2:]
            row = df[df["代码"] == code]

            if row.empty:
                return None

            row = row.iloc[0]

            current_price = float(row.get("最新价", 0))
            prev_close = float(row.get("昨收", 0))
            open_price = float(row.get("今开", 0))
            high = float(row.get("最高", 0))
            low = float(row.get("最低", 0))
            volume = float(row.get("成交量", 0)) if row.get("成交量") else 0
            amount = float(row.get("成交额", 0)) if row.get("成交额") else 0

            change_amount = current_price - prev_close if prev_close > 0 else 0
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            return {
                "name": row.get("名称", ""),
                "code": index_code,
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": int(volume),
                "amount": amount,
                "change_amount": change_amount,
                "change_percent": change_percent,
            }

        except Exception as e:
            print(f"获取指数数据失败 {index_code}: {e}")
            return None

    async def fetch_domestic_index_async(
        self,
        index_code: str,
    ) -> Optional[Dict[str, Any]]:
        """
        异步获取国内指数数据

        Args:
            index_code: 指数代码

        Returns:
            指数数据字典
        """
        if self._semaphore:
            async with self._semaphore:
                await asyncio.sleep(self.request_delay)
                return self.fetch_domestic_index_sync(index_code)
        else:
            await asyncio.sleep(self.request_delay)
            return self.fetch_domestic_index_sync(index_code)

    def _load_existing_history(self) -> Dict[str, List[Dict]]:
        """加载历史数据"""
        try:
            if self.domestic_cache_file.exists():
                with open(self.domestic_cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    history_map = {}
                    for name, data in cache_data.get("指数数据", {}).items():
                        if "历史走势" in data:
                            history_map[name] = data["历史走势"]
                    return history_map
        except Exception:
            pass
        return {}

    def _update_history(self, existing_history: List[Dict], today_data: Dict) -> List[Dict]:
        """更新历史数据"""
        today_entry = {
            "日期": today_data["数据日期"],
            "开盘": today_data["今开"],
            "收盘": today_data["最新价"],
            "最高": today_data["最高"],
            "最低": today_data["最低"],
            "成交量": today_data["成交量"],
        }

        if existing_history:
            if existing_history[0]["日期"] == today_entry["日期"]:
                existing_history[0] = today_entry
            else:
                existing_history.insert(0, today_entry)
            return existing_history[:7]
        else:
            return [today_entry]

    async def fetch_all_domestic_indexes_async(self) -> Dict[str, Any]:
        """
        异步获取所有国内指数

        Returns:
            指数数据字典
        """
        index_mapping = {
            "sh000001": "上证指数",
            "sh000300": "沪深300",
            "sh000905": "中证500",
            "sz399006": "创业板指",
            "sh000688": "科创50",
        }

        gold_mapping = {
            "sh518880": "黄金ETF",
        }

        existing_history_map = self._load_existing_history()
        indexes = {}

        print("正在获取国内指数数据...")

        # AkShare 一次性获取所有指数数据
        all_indexes = {}
        try:
            df = self.akshare.stock_zh_index_spot_em()
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    code = str(row.get("代码", ""))
                    all_indexes[code] = {
                        "name": row.get("名称", ""),
                        "current_price": float(row.get("最新价", 0)),
                        "prev_close": float(row.get("昨收", 0)),
                        "open": float(row.get("今开", 0)),
                        "high": float(row.get("最高", 0)),
                        "low": float(row.get("最低", 0)),
                        "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                        "amount": float(row.get("成交额", 0)) if row.get("成交额") else 0,
                    }
        except Exception as e:
            print(f"获取指数数据失败: {e}")

        for code, name in index_mapping.items():
            index_code = code[2:]
            if index_code in all_indexes:
                data = all_indexes[index_code]
                change_amount = (
                    data["current_price"] - data["prev_close"] if data["prev_close"] > 0 else 0
                )
                change_percent = (
                    (change_amount / data["prev_close"] * 100) if data["prev_close"] > 0 else 0
                )

                today_data = {
                    "名称": name,
                    "代码": index_code,
                    "最新价": data["current_price"],
                    "涨跌额": change_amount,
                    "涨跌幅": change_percent,
                    "昨收": data["prev_close"],
                    "今开": data["open"],
                    "最高": data["high"],
                    "最低": data["low"],
                    "成交量": int(data["volume"]),
                    "成交额": data["amount"],
                    "数据日期": datetime.now().strftime("%Y-%m-%d"),
                    "数据来源": "AkShare（开源数据）",
                }

                existing_history = existing_history_map.get(name, [])
                history = self._update_history(existing_history, today_data)
                today_data["历史走势"] = history

                indexes[name] = today_data
                print(f"  ✅ {name}: {change_percent:+.2f}%")
            else:
                print(f"  ❌ {name}: 获取失败")

        for code, name in gold_mapping.items():
            index_code = code[2:]
            if index_code in all_indexes:
                data = all_indexes[index_code]
                change_amount = (
                    data["current_price"] - data["prev_close"] if data["prev_close"] > 0 else 0
                )
                change_percent = (
                    (change_amount / data["prev_close"] * 100) if data["prev_close"] > 0 else 0
                )

                today_data = {
                    "名称": name,
                    "代码": code,
                    "最新价": data["current_price"],
                    "涨跌额": change_amount,
                    "涨跌幅": change_percent,
                    "昨收": data["prev_close"],
                    "今开": data["open"],
                    "最高": data["high"],
                    "最低": data["low"],
                    "成交量": int(data["volume"]),
                    "成交额": data["amount"],
                    "数据日期": datetime.now().strftime("%Y-%m-%d"),
                    "数据来源": "AkShare（开源数据）",
                }

                indexes[name] = today_data
                print(f"  ✅ {name}: {change_percent:+.2f}%")
            else:
                print(f"  ❌ {name}: 获取失败")

        cache_data = {
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "指数数据": indexes,
        }

        with open(self.domestic_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        return cache_data

    async def fetch_foreign_index_async(
        self,
        session: Any,
        symbol: str,
        api_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        异步获取国外指数数据（Finnhub 正规 API）

        Args:
            session: aiohttp session
            symbol: 指数代码
            api_key: API key

        Returns:
            指数数据字典
        """
        if not HAS_AIOHTTP:
            print(f"获取国外指数失败 {symbol}: aiohttp 未安装")
            return None

        try:
            url = f"https://api.finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return None

                data = await response.json()

                current_price = float(data.get("c", 0))
                prev_close = float(data.get("pc", 0))
                high = float(data.get("h", 0))
                low = float(data.get("l", 0))
                open_price = float(data.get("o", 0))

                if current_price == 0 or prev_close == 0:
                    return None

                change_amount = current_price - prev_close
                change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

                return {
                    "current_price": current_price,
                    "open": open_price,
                    "prev_close": prev_close,
                    "high": high,
                    "low": low,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                }

        except Exception as e:
            print(f"获取国外指数失败 {symbol}: {e}")
            return None

    async def fetch_all_foreign_indexes_async(self) -> Dict[str, Any]:
        """
        异步获取所有国外指数

        Returns:
            指数数据字典
        """
        if not HAS_AIOHTTP:
            print("⚠️ aiohttp 未安装，跳过国外指数获取")
            return {"更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "指数数据": {}}

        import aiohttp

        api_key = config.finnhub_api_key or "demo"

        index_mapping = {
            "^DJI": "道琼斯",
            "^GSPC": "标普500",
            "^IXIC": "纳斯达克",
            "^N225": "日经225",
            "^HSI": "恒生指数",
        }

        indexes = {}

        print("正在获取国外指数数据...")

        async with aiohttp.ClientSession() as session:
            tasks = []
            for symbol in index_mapping.keys():
                tasks.append(self.fetch_foreign_index_async(session, symbol, api_key))

            results = await asyncio.gather(*tasks)

            for (symbol, name), data in zip(index_mapping.items(), results):
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
                        "数据日期": datetime.now().strftime("%Y-%m-%d"),
                        "数据来源": "Finnhub（正规API）",
                    }
                    print(f"  ✅ {name}: {data['change_percent']:+.2f}%")
                else:
                    print(f"  ❌ {name}: 获取失败")

        cache_data = {
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "指数数据": indexes,
        }

        with open(self.foreign_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        return cache_data

    async def update_all_caches_async(self) -> Tuple[bool, bool]:
        """
        异步更新所有缓存

        Returns:
            (国内指数更新成功, 国外指数更新成功)
        """
        domestic_task = self.fetch_all_domestic_indexes_async()
        foreign_task = self.fetch_all_foreign_indexes_async()

        domestic_result, foreign_result = await asyncio.gather(
            domestic_task, foreign_task, return_exceptions=True
        )

        domestic_success = domestic_result is not None and not isinstance(domestic_result, Exception)  # type: ignore
        foreign_success = foreign_result is not None and not isinstance(foreign_result, Exception)  # type: ignore
        return domestic_success, foreign_success


async_market_data_fetcher = AsyncMarketDataFetcher()
