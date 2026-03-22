"""
Enhanced Market Data Fetcher.
增强版市场指数数据获取模块

特性：
- 多数据源冗余
- 并发获取
- 智能缓存
- 错误处理
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from ..config import config
from ..utils.http_client import HTTPClient

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    data: dict[str, Any]
    timestamp: float
    ttl: int = 3600  # 默认1小时过期

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.timestamp > self.ttl


@dataclass
class DataSource:
    """数据源配置"""
    name: str
    priority: int = 0
    enabled: bool = True
    last_success: float = 0.0
    failure_count: int = 0

    def mark_success(self):
        """标记成功"""
        self.last_success = time.time()
        self.failure_count = 0

    def mark_failure(self):
        """标记失败"""
        self.failure_count += 1
        if self.failure_count >= 3:
            self.enabled = False


class EnhancedMarketDataFetcher:
    """增强版市场数据获取器"""

    DOMESTIC_INDEXES = {
        "sh000001": "上证指数",
        "sh000300": "沪深300",
        "sh000905": "中证500",
        "sz399006": "创业板指",
        "sh000688": "科创50",
        "sh518880": "黄金ETF",
    }

    FOREIGN_INDEXES = {
        "^DJI": "道琼斯",
        "^GSPC": "标普500",
        "^IXIC": "纳斯达克",
        "^N225": "日经225",
        "^HSI": "恒生指数",
    }

    def __init__(
        self,
        max_workers: int = 5,
        cache_ttl: int = 3600,
        request_timeout: int = 15,
    ):
        self.cache_path = config.cache_path
        self.domestic_cache_file = self.cache_path / "market_index_domestic.json"
        self.foreign_cache_file = self.cache_path / "market_index_foreign.json"
        self.cache_path.mkdir(parents=True, exist_ok=True)

        self.max_workers = max_workers
        self.cache_ttl = cache_ttl
        self.request_timeout = request_timeout

        self._akshare = None
        self._http_client = HTTPClient(
            default_timeout=request_timeout,
            max_retries=3,
            enable_adaptive_timeout=True,
        )

        self._cache: dict[str, CacheEntry] = {}
        self._sources: dict[str, list[DataSource]] = {}

        self._init_sources()

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
                    "AkShare 是一个开源免费的金融数据接口，无需注册"
                )
        return self._akshare

    def _init_sources(self):
        """初始化数据源"""
        for code in self.DOMESTIC_INDEXES:
            self._sources[code] = [
                DataSource(name="akshare_spot", priority=0),
                DataSource(name="akshare_hist", priority=1),
                DataSource(name="sina", priority=2),
            ]

        for symbol in self.FOREIGN_INDEXES:
            self._sources[symbol] = [
                DataSource(name="finnhub", priority=0),
                DataSource(name="yahoo", priority=1),
                DataSource(name="alpha_vantage", priority=2),
            ]

    def _get_from_cache(self, key: str) -> dict[str, Any] | None:
        """从缓存获取数据"""
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            return entry.data
        return None

    def _set_cache(self, key: str, data: dict[str, Any], ttl: int | None = None):
        """设置缓存"""
        self._cache[key] = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl or self.cache_ttl,
        )

    def _fetch_from_akshare_spot(self, index_code: str) -> dict[str, Any] | None:
        """从 AkShare 实时行情获取"""
        try:
            df = self.akshare.stock_zh_index_spot_em()
            if df is None or df.empty:
                return None

            code = index_code[2:] if index_code.startswith(("sh", "sz")) else index_code
            row = df[df["代码"] == code]

            if row.empty:
                return None

            row = row.iloc[0]
            current_price = float(row.get("最新价", 0))
            prev_close = float(row.get("昨收", 0))

            if current_price == 0:
                return None

            return {
                "name": row.get("名称", ""),
                "code": index_code,
                "current_price": current_price,
                "open": float(row.get("今开", 0)),
                "prev_close": prev_close,
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "volume": int(float(row.get("成交量", 0) or 0)),
                "amount": float(row.get("成交额", 0) or 0),
                "change_amount": current_price - prev_close,
                "change_percent": ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "source": "akshare_spot",
            }
        except Exception as e:
            logger.debug(f"AkShare spot 获取失败 {index_code}: {e}")
            return None

    def _fetch_from_akshare_hist(self, index_code: str) -> dict[str, Any] | None:
        """从 AkShare 历史数据获取"""
        try:
            code = index_code[2:] if index_code.startswith(("sh", "sz")) else index_code
            df = self.akshare.index_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=(datetime.now() - timedelta(days=7)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
            )

            if df is None or df.empty:
                return None

            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            current_price = float(latest.get("收盘", 0))
            prev_close = float(prev.get("收盘", 0))

            if current_price == 0:
                return None

            return {
                "name": self.DOMESTIC_INDEXES.get(index_code, index_code),
                "code": index_code,
                "current_price": current_price,
                "open": float(latest.get("开盘", 0)),
                "prev_close": prev_close,
                "high": float(latest.get("最高", 0)),
                "low": float(latest.get("最低", 0)),
                "volume": int(float(latest.get("成交量", 0) or 0)),
                "amount": 0,
                "change_amount": current_price - prev_close,
                "change_percent": ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "source": "akshare_hist",
            }
        except Exception as e:
            logger.debug(f"AkShare hist 获取失败 {index_code}: {e}")
            return None

    def _fetch_from_sina(self, index_code: str) -> dict[str, Any] | None:
        """从新浪财经获取"""
        try:
            sina_codes = {
                "sh000001": "s_sh000001",
                "sh000300": "s_sh000300",
                "sh000905": "s_sh000905",
                "sz399006": "s_sz399006",
                "sh000688": "s_sh000688",
            }

            sina_code = sina_codes.get(index_code)
            if not sina_code:
                return None

            url = f"http://hq.sinajs.cn/list={sina_code}"
            headers = {'Referer': 'http://finance.sina.com.cn'}
            response = self._http_client.get(url, headers=headers, timeout=10)

            if response is None:
                return None

            text = response.text
            if not text or 'var hq_str_' not in text:
                return None

            parts = text.split('"')[1].split(',')
            if len(parts) < 4:
                return None

            name = parts[0]
            current_price = float(parts[1])
            change_amount = float(parts[2])
            change_percent = float(parts[3])
            prev_close = current_price - change_amount if change_amount else current_price

            return {
                "name": name,
                "code": index_code,
                "current_price": current_price,
                "open": 0,
                "prev_close": prev_close,
                "high": 0,
                "low": 0,
                "volume": 0,
                "amount": 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "sina",
            }
        except Exception as e:
            logger.debug(f"新浪财经获取失败 {index_code}: {e}")
            return None

    def _fetch_from_tencent(self, index_code: str) -> dict[str, Any] | None:
        """从腾讯财经获取"""
        try:
            tencent_codes = {
                "sh000001": "sh000001",
                "sh000300": "sh000300",
                "sh000905": "sh000905",
                "sz399006": "sz399006",
                "sh000688": "sh000688",
                "sh518880": "sh518880",
            }

            tencent_code = tencent_codes.get(index_code)
            if not tencent_code:
                return None

            url = f"http://qt.gtimg.cn/q={tencent_code}"
            response = self._http_client.get(url, timeout=10)

            if response is None:
                return None

            text = response.text
            if not text or 'v_' not in text:
                return None

            parts = text.split('~')
            if len(parts) < 35:
                return None

            name = parts[1]
            current_price = float(parts[3])
            prev_close = float(parts[4])
            open_price = float(parts[5])
            high = float(parts[33]) if len(parts) > 33 else 0
            low = float(parts[34]) if len(parts) > 34 else 0
            volume = int(float(parts[6]) or 0)
            amount = float(parts[37]) if len(parts) > 37 else 0

            change_amount = current_price - prev_close
            change_percent = float(parts[32]) if len(parts) > 32 else 0

            return {
                "name": name,
                "code": index_code,
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": volume,
                "amount": amount,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "tencent",
            }
        except Exception as e:
            logger.debug(f"腾讯财经获取失败 {index_code}: {e}")
            return None

    def _fetch_from_akshare_global(self, symbol: str) -> dict[str, Any] | None:
        """从 AkShare 获取全球指数（推荐，正规数据源）"""
        try:
            # AkShare 全球指数名称映射
            ak_names = {
                "^DJI": "道琼斯",
                "^GSPC": "标普500",
                "^IXIC": "纳斯达克",
                "^N225": "日经225",
                "^HSI": "恒生指数",
            }

            ak_name = ak_names.get(symbol)
            if not ak_name:
                return None

            df = self.akshare.index_global_hist_em(symbol=ak_name)
            if df is None or df.empty:
                return None

            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            # AkShare 返回的列名：日期, 代码, 名称, 今开, 最新价, 最高, 最低, 振幅
            current_price = float(latest.get("最新价", 0))
            prev_close = float(prev.get("最新价", 0))

            if current_price == 0:
                return None

            return {
                "name": ak_name,
                "code": symbol,
                "current_price": current_price,
                "open": float(latest.get("今开", 0)),
                "prev_close": prev_close,
                "high": float(latest.get("最高", 0)),
                "low": float(latest.get("最低", 0)),
                "volume": 0,
                "amount": 0,
                "change_amount": current_price - prev_close,
                "change_percent": float(latest.get("振幅", 0)),
                "source": "akshare",
            }
        except Exception as e:
            logger.debug(f"AkShare 获取失败 {symbol}: {e}")
            return None

    def _fetch_from_eastmoney(self, symbol: str) -> dict[str, Any] | None:
        """从东方财富获取全球指数
        
        注意：这是东方财富网站的内部 API，非官方开放接口。
        - 优点：免费、无需注册、响应快速
        - 缺点：可能随时变更、无官方支持、不适合商业用途
        - 建议：仅作为备用数据源，优先使用 AkShare 或官方 API
        """
        try:
            import subprocess

            # 东方财富的指数代码映射
            em_codes = {
                "^DJI": "100.DJIA",
                "^GSPC": "100.SPX",
                "^IXIC": "100.NDX",
                "^N225": "100.N225",
                "^HSI": "100.HSI",
            }

            em_code = em_codes.get(symbol)
            if not em_code:
                return None

            url = f"http://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids={em_code}&fields=f2,f3,f4,f12,f14"

            result = subprocess.run(
                ["curl", "-s", "--max-time", "15", url],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            diff = data.get("data", {}).get("diff", [])
            if not diff:
                return None

            item = diff[0]
            current_price = float(item.get("f2", 0))
            change_percent = float(item.get("f3", 0))
            change_amount = float(item.get("f4", 0))
            name = item.get("f14", "")

            if current_price == 0:
                return None

            prev_close = current_price - change_amount if change_amount else current_price

            return {
                "name": name,
                "code": symbol,
                "current_price": current_price,
                "open": 0,
                "prev_close": prev_close,
                "high": 0,
                "low": 0,
                "volume": 0,
                "amount": 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "eastmoney",
            }
        except Exception as e:
            logger.debug(f"东方财富获取失败 {symbol}: {e}")
            return None

    def _fetch_from_sina_global(self, symbol: str) -> dict[str, Any] | None:
        """从新浪财经获取全球指数（备份源）
        
        新浪财经全球指数 API:
        - 美股: gb_dji (道琼斯), gb_ixic (纳斯达克), gb_inx (标普500)
        - 港股: hkHSI (恒生指数)
        - 日本: gb_n225 (日经225)
        """
        try:
            import requests

            sina_codes = {
                "^DJI": "gb_dji",
                "^GSPC": "gb_inx",
                "^IXIC": "gb_ixic",
                "^N225": "gb_n225",
                "^HSI": "hkHSI",
            }

            sina_code = sina_codes.get(symbol)
            if not sina_code:
                return None

            url = f"http://hq.sinajs.cn/list={sina_code}"
            headers = {
                "Referer": "http://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'gbk'
            content = response.text

            pattern = f'var hq_str_{sina_code}="'
            start = content.find(pattern)

            if start == -1:
                logger.warning(f"新浪全球指数 pattern 未找到 {symbol}")
                return None

            start += len(pattern)
            end = content.find('";', start)
            data_str = content[start:end]

            if not data_str:
                return None

            parts = data_str.split(",")

            if sina_code.startswith("hk"):
                current_price = float(parts[6]) if len(parts) > 6 else 0
                prev_close = float(parts[2]) if len(parts) > 2 else 0
                open_price = float(parts[3]) if len(parts) > 3 else 0
                high = float(parts[4]) if len(parts) > 4 else 0
                low = float(parts[5]) if len(parts) > 5 else 0
                name = parts[1] if len(parts) > 1 else ""
            else:
                current_price = float(parts[1]) if len(parts) > 1 else 0
                change_percent = float(parts[2]) if len(parts) > 2 else 0
                change_amount = float(parts[4]) if len(parts) > 4 else 0
                open_price = float(parts[5]) if len(parts) > 5 else 0
                high = float(parts[6]) if len(parts) > 6 else 0
                low = float(parts[7]) if len(parts) > 7 else 0
                prev_close = current_price - change_amount if change_amount else current_price
                name = parts[0] if len(parts) > 0 else ""

            if current_price == 0:
                return None

            change_amount = current_price - prev_close if prev_close > 0 else 0
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            return {
                "name": name,
                "code": symbol,
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": 0,
                "amount": 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "sina_global",
            }
        except Exception as e:
            logger.debug(f"新浪全球指数获取失败 {symbol}: {e}")
            return None

    def _fetch_from_finnhub(self, symbol: str) -> dict[str, Any] | None:
        """从 Finnhub 获取"""
        try:
            api_key = config.finnhub_api_key or "demo"
            url = f"https://api.finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

            data = self._http_client.get_json(url, timeout=15)
            if data is None:
                return None

            current_price = float(data.get("c", 0))
            prev_close = float(data.get("pc", 0))

            if current_price == 0 or prev_close == 0:
                return None

            return {
                "name": self.FOREIGN_INDEXES.get(symbol, symbol),
                "code": symbol,
                "current_price": current_price,
                "open": float(data.get("o", 0)),
                "prev_close": prev_close,
                "high": float(data.get("h", 0)),
                "low": float(data.get("l", 0)),
                "volume": 0,
                "amount": 0,
                "change_amount": current_price - prev_close,
                "change_percent": ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "source": "finnhub",
            }
        except Exception as e:
            logger.debug(f"Finnhub 获取失败 {symbol}: {e}")
            return None

    def _fetch_from_yahoo(self, symbol: str) -> dict[str, Any] | None:
        """从 Yahoo Finance 获取"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"

            data = self._http_client.get_json(url, timeout=15)
            if data is None:
                return None

            result = data.get("chart", {}).get("result", [])
            if not result:
                return None

            meta = result[0].get("meta", {})
            current_price = float(meta.get("regularMarketPrice", 0))
            prev_close = float(meta.get("previousClose", 0))

            if current_price == 0 or prev_close == 0:
                return None

            return {
                "name": self.FOREIGN_INDEXES.get(symbol, symbol),
                "code": symbol,
                "current_price": current_price,
                "open": float(meta.get("regularMarketOpen", 0)),
                "prev_close": prev_close,
                "high": float(meta.get("regularMarketDayHigh", 0)),
                "low": float(meta.get("regularMarketDayLow", 0)),
                "volume": 0,
                "amount": 0,
                "change_amount": current_price - prev_close,
                "change_percent": ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "source": "yahoo",
            }
        except Exception as e:
            logger.debug(f"Yahoo Finance 获取失败 {symbol}: {e}")
            return None

    def _fetch_from_alpha_vantage(self, symbol: str) -> dict[str, Any] | None:
        """从 Alpha Vantage 获取"""
        try:
            import subprocess
            api_key = config.alphavantage_api_key or "demo"

            # Alpha Vantage 使用股票代码，不是指数代码
            symbol_map = {
                "^GSPC": "SPY",  # 标普500 ETF
                "^DJI": "DIA",   # 道琼斯 ETF
                "^IXIC": "QQQ",  # 纳斯达克 ETF
                "^N225": "EWJ",  # 日本 ETF
                "^HSI": "EWH",   # 香港 ETF
            }

            av_symbol = symbol_map.get(symbol, symbol.replace("^", ""))
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={av_symbol}&apikey={api_key}"

            # 使用 curl 获取数据（绕过 SSL 问题）
            result = subprocess.run(
                ["curl", "-s", "--max-time", "30", url],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            quote = data.get("Global Quote", {})
            if not quote:
                return None

            current_price = float(quote.get("05. price", 0))
            prev_close = float(quote.get("08. previous close", 0))

            if current_price == 0 or prev_close == 0:
                return None

            return {
                "name": self.FOREIGN_INDEXES.get(symbol, symbol),
                "code": symbol,
                "current_price": current_price,
                "open": float(quote.get("02. open", 0)),
                "prev_close": prev_close,
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "volume": int(float(quote.get("06. volume", 0) or 0)),
                "amount": 0,
                "change_amount": current_price - prev_close,
                "change_percent": ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "source": "alpha_vantage",
            }
        except Exception as e:
            logger.debug(f"Alpha Vantage 获取失败 {symbol}: {e}")
            return None

    def fetch_domestic_index(self, index_code: str) -> dict[str, Any] | None:
        """获取国内指数（多数据源故障转移）"""
        cache_key = f"domestic_{index_code}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        fetchers = [
            ("tencent", self._fetch_from_tencent),
            ("sina", self._fetch_from_sina),
            ("akshare_spot", self._fetch_from_akshare_spot),
            ("akshare_hist", self._fetch_from_akshare_hist),
        ]

        for source_name, fetcher in fetchers:
            try:
                data = fetcher(index_code)
                if data:
                    self._set_cache(cache_key, data)
                    logger.info(f"成功从 {source_name} 获取 {index_code}")
                    return data
            except Exception as e:
                logger.debug(f"{source_name} 获取失败: {e}")
                continue

        logger.error(f"所有数据源都失败: {index_code}")
        return None

    def fetch_foreign_index(self, symbol: str) -> dict[str, Any] | None:
        """获取国外指数（多数据源故障转移）
        
        数据源优先级：
        1. AkShare - 推荐，正规开源库
        2. 东方财富 - 备用，内部API（非官方）
        3. Alpha Vantage - 官方API，需要Key
        4. Finnhub - 官方API，需要Key
        5. Yahoo Finance - 官方API，不稳定
        """
        cache_key = f"foreign_{symbol}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        fetchers = [
            ("sina_global", self._fetch_from_sina_global),
            ("akshare", self._fetch_from_akshare_global),
            ("eastmoney", self._fetch_from_eastmoney),
            ("alpha_vantage", self._fetch_from_alpha_vantage),
            ("finnhub", self._fetch_from_finnhub),
            ("yahoo", self._fetch_from_yahoo),
        ]

        for source_name, fetcher in fetchers:
            try:
                data = fetcher(symbol)
                if data:
                    self._set_cache(cache_key, data)
                    logger.info(f"成功从 {source_name} 获取 {symbol}")
                    return data
            except Exception as e:
                logger.debug(f"{source_name} 获取失败: {e}")
                continue

        logger.error(f"所有数据源都失败: {symbol}")
        return None

    def fetch_all_domestic_indexes(self) -> dict[str, Any]:
        """并发获取所有国内指数"""
        logger.info("正在获取国内市场指数...")

        indexes = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_code = {
                executor.submit(self.fetch_domestic_index, code): code
                for code in self.DOMESTIC_INDEXES
            }

            for future in as_completed(future_to_code):
                code = future_to_code[future]
                name = self.DOMESTIC_INDEXES[code]

                try:
                    data = future.result()
                    if data:
                        indexes[name] = {
                            "名称": name,
                            "代码": code[2:] if code.startswith(("sh", "sz")) else code,
                            "最新价": data["current_price"],
                            "涨跌额": data["change_amount"],
                            "涨跌幅": data["change_percent"],
                            "昨收": data["prev_close"],
                            "今开": data["open"],
                            "最高": data["high"],
                            "最低": data["low"],
                            "成交量": data["volume"],
                            "成交额": data["amount"],
                            "数据日期": datetime.now().strftime("%Y-%m-%d"),
                            "数据来源": data.get("source", "未知"),
                        }
                        logger.info(f"✅ {name}: {data['change_percent']:+.2f}%")
                    else:
                        logger.warning(f"❌ {name}: 获取失败")
                except Exception as e:
                    logger.error(f"❌ {name}: {e}")

        cache_data = {
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "指数数据": indexes,
        }

        with open(self.domestic_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        return cache_data

    def fetch_all_foreign_indexes(self) -> dict[str, Any]:
        """并发获取所有国外指数"""
        logger.info("正在获取国外市场指数...")

        indexes = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.fetch_foreign_index, symbol): symbol
                for symbol in self.FOREIGN_INDEXES
            }

            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                name = self.FOREIGN_INDEXES[symbol]

                try:
                    data = future.result()
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
                            "成交量": data["volume"],
                            "成交额": data["amount"],
                            "数据日期": datetime.now().strftime("%Y-%m-%d"),
                            "数据来源": data.get("source", "未知"),
                        }
                        logger.info(f"✅ {name}: {data['change_percent']:+.2f}%")
                    else:
                        logger.warning(f"❌ {name}: 获取失败")
                except Exception as e:
                    logger.error(f"❌ {name}: {e}")

        cache_data = {
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "指数数据": indexes,
        }

        with open(self.foreign_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        return cache_data

    def fetch_all_indexes(self) -> dict[str, Any]:
        """获取所有指数"""
        domestic = self.fetch_all_domestic_indexes()
        foreign = self.fetch_all_foreign_indexes()

        return {
            "国内指数": domestic.get("指数数据", {}),
            "国外指数": foreign.get("指数数据", {}),
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


enhanced_market_data_fetcher = EnhancedMarketDataFetcher()
