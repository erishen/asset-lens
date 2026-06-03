"""
Fundamental Data Fetcher.
基本面数据获取模块

数据源: AkShare (开源免费)
- PE/PB/ROE等基本面指标
"""

from ..utils.warnings_config import suppress_common_warnings

suppress_common_warnings()

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .fetchers.base import FetcherCacheMixin

logger = logging.getLogger(__name__)


@dataclass
class FundamentalData:
    """基本面数据"""

    code: str
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    roe: float = 0.0
    revenue_growth: float = 0.0
    profit_growth: float = 0.0
    debt_ratio: float = 0.0
    gross_margin: float = 0.0
    net_margin: float = 0.0
    total_market_value: float = 0.0
    circulating_market_value: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "roe": self.roe,
            "revenue_growth": self.revenue_growth,
            "profit_growth": self.profit_growth,
            "debt_ratio": self.debt_ratio,
            "gross_margin": self.gross_margin,
            "net_margin": self.net_margin,
            "total_market_value": self.total_market_value,
            "circulating_market_value": self.circulating_market_value,
        }


class FundamentalFetcher(FetcherCacheMixin):
    _akshare_raise_on_missing = False

    def __init__(self, cache_path: Path | None = None):
        self._init_cache(
            cache_path or Path(__file__).parent / "cache",
            default_ttl=86400,
        )
        self._fundamental_cache: dict[str, FundamentalData] = {}
        self._load_cache()

    @property
    def cache_file(self) -> Path:
        return self.cache_path / "fundamental_cache.json"

    def _load_cache(self):
        data = self._cache.load_file("fundamental_cache.json")
        if data is None:
            return
        try:
            for code, info in data.get("fundamentals", {}).items():
                self._fundamental_cache[code] = FundamentalData(
                    code=code,
                    pe_ratio=info.get("pe_ratio", 0),
                    pb_ratio=info.get("pb_ratio", 0),
                    roe=info.get("roe", 0),
                    revenue_growth=info.get("revenue_growth", 0),
                    profit_growth=info.get("profit_growth", 0),
                    debt_ratio=info.get("debt_ratio", 0),
                    gross_margin=info.get("gross_margin", 0),
                    net_margin=info.get("net_margin", 0),
                    total_market_value=info.get("total_market_value", 0),
                    circulating_market_value=info.get("circulating_market_value", 0),
                )
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"加载基本面缓存数据解析失败: {e}")
        except (OSError, RuntimeError) as e:
            logger.warning(f"加载基本面缓存失败: {e}")

    def _save_cache(self):
        data = {
            "updated_at": datetime.now().isoformat(),
            "fundamentals": {code: info.to_dict() for code, info in self._fundamental_cache.items()},
        }
        self._cache.save_file("fundamental_cache.json", data, ttl=0)

    def get_fundamental(self, code: str) -> FundamentalData:
        """获取单只股票基本面数据"""
        if code in self._fundamental_cache:
            return self._fundamental_cache[code]

        data = FundamentalData(code=code)

        if self.akshare:
            try:
                df = self.akshare.stock_a_lg_indicator(symbol=code)  # pylint: disable=no-member
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    data.pe_ratio = float(latest.get("pe", 0) or 0)
                    data.pb_ratio = float(latest.get("pb", 0) or 0)
                    data.total_market_value = float(latest.get("total_mv", 0) or 0)
                    data.circulating_market_value = float(latest.get("circ_mv", 0) or 0)
            except (ValueError, KeyError, TypeError) as e:
                logger.debug(f"获取 {code} 基本面数据解析失败: {e}")
            except (ConnectionError, RuntimeError, OSError) as e:
                logger.debug(f"获取 {code} 基本面数据失败: {e}")

        self._fundamental_cache[code] = data
        return data

    def get_realtime_pe_pb(self, code: str) -> tuple[float, float]:
        """获取实时PE/PB"""
        if self.akshare:
            try:
                df = self.akshare.stock_a_lg_indicator(symbol=code)  # pylint: disable=no-member
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    pe = float(latest.get("pe", 0) or 0)
                    pb = float(latest.get("pb", 0) or 0)
                    return pe, pb
            except (ValueError, TypeError) as e:
                logger.debug("基本面数据解析失败: %s", e)
        return 0.0, 0.0

    def batch_get_fundamentals(self, codes: list[str]) -> dict[str, FundamentalData]:
        """批量获取基本面数据"""
        result = {}
        for i, code in enumerate(codes):
            result[code] = self.get_fundamental(code)
            if (i + 1) % 50 == 0:
                logger.info(f"已获取 {i + 1}/{len(codes)} 只股票基本面数据")
        self._save_cache()
        return result


from .feature_builder import EnhancedFeatureBuilder
from .money_flow_fetcher import MoneyFlowFetcher

fundamental_fetcher = FundamentalFetcher()
money_flow_fetcher = MoneyFlowFetcher()
enhanced_feature_builder = EnhancedFeatureBuilder()
