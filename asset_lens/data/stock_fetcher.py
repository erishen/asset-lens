"""
Stock data fetcher for asset-lens.
股票数据获取模块 - 获取A股、港股、美股实时行情

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


class StockDataFetcher:
    """股票数据获取器 - 使用 AkShare 开源库"""

    def __init__(self, cache_path: Optional[Path] = None):
        """
        初始化股票数据获取器

        Args:
            cache_path: 缓存路径
        """
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.stock_cache_file = self.cache_path / "stock_quotes.json"
        self._stock_codes_map: Optional[Dict[str, str]] = None
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

    def _load_stock_codes_config(self) -> Dict[str, str]:
        """
        加载股票代码配置

        Returns:
            股票名称到代码的映射
        """
        if self._stock_codes_map is not None:
            return self._stock_codes_map

        config_file = config.project_root / "config" / "fund_stock_codes.json"
        result = {}

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for stock in data.get("stocks", []):
                    name = stock.get("name", "")
                    code = stock.get("code", "")
                    if name and code:
                        result[name] = code

                    for keyword in stock.get("keywords", []):
                        if keyword and code:
                            result[keyword] = code

                self._stock_codes_map = result
                return result
            except Exception as e:
                print(f"加载股票代码配置失败: {e}")

        self._stock_codes_map = {}
        return {}

    def fetch_stock_quote_akshare(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票实时行情（AkShare）

        Args:
            stock_code: 股票代码（如 sh600519, sz000001, hk00700）

        Returns:
            股票行情数据
        """
        try:
            # A股股票
            if stock_code.startswith(("sh", "sz")):
                return self._fetch_cn_stock_quote(stock_code)
            # 港股
            elif stock_code.startswith("hk"):
                return self._fetch_hk_stock_quote(stock_code)
            else:
                return None

        except Exception as e:
            print(f"获取股票行情失败 {stock_code}: {e}")
            return None

    def _fetch_cn_stock_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取A股实时行情（AkShare）

        Args:
            stock_code: 股票代码（如 sh600519, sz000001）

        Returns:
            股票行情数据
        """
        try:
            # 获取A股实时行情
            df = self.akshare.stock_zh_a_spot_em()

            if df is None or df.empty:
                return None

            # 提取股票代码（去掉前缀）
            code = stock_code[2:]

            # 查找对应股票
            row = df[df["代码"] == code]

            if row.empty:
                return None

            row = row.iloc[0]

            current_price = float(row.get("最新价", 0))
            prev_close = float(row.get("昨收", 0))
            open_price = float(row.get("今开", 0))
            high = float(row.get("最高", 0))
            low = float(row.get("最低", 0))
            volume = float(row.get("成交量", 0))
            amount = float(row.get("成交额", 0))
            amplitude = float(row.get("振幅", 0))
            change_percent = float(row.get("涨跌幅", 0))
            change_amount = float(row.get("涨跌额", 0))
            turnover_rate = float(row.get("换手率", 0))
            market_cap = float(row.get("总市值", 0)) / 100000000 if row.get("总市值") else 0

            return {
                "code": stock_code,
                "name": row.get("名称", ""),
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": int(volume),
                "amount": amount,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "amplitude": amplitude,
                "market_cap": market_cap,
                "turnover_rate": turnover_rate,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "AkShare",
            }

        except Exception as e:
            print(f"获取A股行情失败 {stock_code}: {e}")
            return None

    def _fetch_hk_stock_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取港股实时行情（AkShare）

        Args:
            stock_code: 股票代码（如 hk00700）

        Returns:
            股票行情数据
        """
        try:
            # 获取港股实时行情
            df = self.akshare.stock_hk_spot_em()

            if df is None or df.empty:
                return None

            # 提取股票代码（去掉前缀）
            code = stock_code[2:]

            # 查找对应股票
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
                "code": stock_code,
                "name": row.get("名称", ""),
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": int(volume),
                "amount": amount,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "AkShare",
            }

        except Exception as e:
            print(f"获取港股行情失败 {stock_code}: {e}")
            return None

    def fetch_us_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取美股实时行情（Finnhub 正规 API）

        Args:
            symbol: 股票代码（如 AAPL, TSLA）

        Returns:
            股票行情数据
        """
        import requests  # type: ignore

        try:
            from ..utils.http_client import get_json
            
            api_key = config.finnhub_api_key or "demo"
            url = f"https://api.finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

            data = get_json(url, timeout=10)

            if data is None:
                return None

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
                "code": symbol,
                "name": symbol,
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": 0,
                "amount": 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Finnhub",
            }

        except Exception as e:
            print(f"获取美股行情失败 {symbol}: {e}")
            return None

    def fetch_multiple_stocks(self, stock_codes: List[str]) -> Dict[str, Any]:
        """
        批量获取股票行情

        Args:
            stock_codes: 股票代码列表

        Returns:
            股票行情数据字典
        """
        results = {}

        for code in stock_codes:
            print(f"正在获取 {code} 行情...")

            if code.startswith(("sh", "sz", "hk")):
                data = self.fetch_stock_quote_akshare(code)
            else:
                data = self.fetch_us_stock_quote(code)

            if data:
                results[code] = data
                print(f"  ✅ {data['name']}: {data['change_percent']:+.2f}%")
            else:
                print(f"  ❌ {code}: 获取失败")

            time.sleep(0.1)

        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": results,
        }

        with open(self.stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        return cache_data

    def get_cached_stocks(self) -> Dict[str, Any]:
        """获取缓存的股票数据"""
        if self.stock_cache_file.exists():
            with open(self.stock_cache_file, "r", encoding="utf-8") as f:
                return json.load(f)  # type: ignore
        return {}


stock_fetcher = StockDataFetcher()
