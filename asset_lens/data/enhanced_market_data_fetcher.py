import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from ..config import config
from ..utils.http_client import HTTPClient
from .domestic_index_fetcher import DomesticIndexFetcherMixin
from .foreign_index_fetcher import ForeignIndexFetcherMixin

logger = logging.getLogger(__name__)


@dataclass
class DataSource:
    name: str
    enabled: bool = True
    last_success: float = 0
    last_failure: float = 0
    failure_count: int = 0

    def mark_success(self):
        self.last_success = time.time()
        self.failure_count = 0

    def mark_failure(self):
        self.last_failure = time.time()
        self.failure_count += 1
        if self.failure_count >= 3:
            self.enabled = False


class EnhancedMarketDataFetcher(
    DomesticIndexFetcherMixin,
    ForeignIndexFetcherMixin,
):
    DOMESTIC_INDEXES: ClassVar[dict[str, str]] = {
        "sh000001": "上证指数",
        "sh000300": "沪深300",
        "sh000905": "中证500",
        "sz399006": "创业板指",
        "sh000688": "科创50",
        "sh518880": "黄金ETF",
    }

    FOREIGN_INDEXES: ClassVar[dict[str, str]] = {
        "^DJI": "道琼斯",
        "^GSPC": "标普500",
        "^IXIC": "纳斯达克",
        "^N225": "日经225",
        "^HSI": "恒生指数",
    }

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self._http_client = HTTPClient()
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl = 300
        self.max_workers = 3
        self._sources: dict[str, list[DataSource]] = {}
        self._init_sources()

    @property
    def akshare(self):
        try:
            import akshare

            return akshare
        except ImportError:
            return None

    def _init_sources(self):
        for code in self.DOMESTIC_INDEXES:
            self._sources[code] = [
                DataSource(name="tencent"),
                DataSource(name="sina"),
                DataSource(name="akshare_spot"),
                DataSource(name="akshare_hist"),
            ]

        for symbol in self.FOREIGN_INDEXES:
            self._sources[symbol] = [
                DataSource(name="sina_global"),
                DataSource(name="akshare"),
                DataSource(name="eastmoney"),
                DataSource(name="alpha_vantage"),
                DataSource(name="finnhub"),
                DataSource(name="yahoo"),
            ]

    def _get_from_cache(self, key: str) -> Any | None:
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any):
        self._cache[key] = (time.time(), data)

    @property
    def domestic_cache_file(self) -> Path:
        return self.cache_path / "domestic_indexes.json"

    @property
    def foreign_cache_file(self) -> Path:
        return self.cache_path / "foreign_indexes.json"

    def fetch_all_indexes(self) -> dict[str, Any]:
        domestic = self.fetch_all_domestic_indexes()
        foreign = self.fetch_all_foreign_indexes()

        return {
            "国内指数": domestic.get("指数数据", {}),
            "国外指数": foreign.get("指数数据", {}),
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


enhanced_market_data_fetcher = EnhancedMarketDataFetcher()
