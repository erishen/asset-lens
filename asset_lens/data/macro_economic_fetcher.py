"""
Macro economic data fetcher for asset-lens.
宏观经济数据获取模块 - 获取国内外宏观经济指标数据

数据源:
- FRED (Federal Reserve Economic Data) - 美联储经济数据
- World Bank API - 世界银行数据
- OECD API - 经合组织数据
- 中国国家统计局
"""

import time
from datetime import datetime
from typing import Any

from ..config import config


class MacroEconomicFetcher:
    """宏观经济数据获取器"""

    CACHE_DURATION = 3600  # 1小时缓存

    FRED_BASE_URL = "https://api.stlouisfed.org/fred"
    WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"

    INDICATORS = {
        "us_gdp": {
            "name": "美国GDP",
            "fred_id": "GDP",
            "unit": "十亿美元",
            "frequency": "季度",
        },
        "us_cpi": {
            "name": "美国CPI",
            "fred_id": "CPIAUCSL",
            "unit": "指数",
            "frequency": "月度",
        },
        "us_unemployment": {
            "name": "美国失业率",
            "fred_id": "UNRATE",
            "unit": "%",
            "frequency": "月度",
        },
        "us_fed_funds_rate": {
            "name": "美国联邦基金利率",
            "fred_id": "FEDFUNDS",
            "unit": "%",
            "frequency": "月度",
        },
        "us_10y_treasury": {
            "name": "美国10年期国债收益率",
            "fred_id": "GS10",
            "unit": "%",
            "frequency": "月度",
        },
        "china_gdp": {
            "name": "中国GDP",
            "world_bank_id": "NY.GDP.MKTP.CD",
            "unit": "美元",
            "frequency": "年度",
        },
        "china_cpi": {
            "name": "中国CPI",
            "world_bank_id": "FP.CPI.TOTL.ZG",
            "unit": "%",
            "frequency": "年度",
        },
        "world_gdp_growth": {
            "name": "全球GDP增长率",
            "world_bank_id": "NY.GDP.MKTP.KD.ZG",
            "unit": "%",
            "frequency": "年度",
        },
    }

    def __init__(self, fred_api_key: str | None = None):
        self._fred_api_key = fred_api_key or config.fred_api_key
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_time: dict[str, float] = {}
        self._requests = None

    @property
    def requests(self):
        """延迟加载 requests - 已弃用，使用 http_client"""
        from ..utils.http_client import http_client
        return http_client

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache_time:
            return False
        return time.time() - self._cache_time[cache_key] < self.CACHE_DURATION

    def _get_cached(self, cache_key: str) -> dict[str, Any] | None:
        """获取缓存数据"""
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None

    def _set_cache(self, cache_key: str, data: dict[str, Any]):
        """设置缓存"""
        self._cache[cache_key] = data
        self._cache_time[cache_key] = time.time()

    def fetch_fred_series(
        self,
        series_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any] | None:
        """
        获取 FRED 数据系列

        Args:
            series_id: FRED 数据系列 ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            数据系列
        """
        if not self._fred_api_key:
            print("警告: 未配置 FRED API Key，无法获取美联储数据")
            return None

        cache_key = f"fred_{series_id}_{start_date}_{end_date}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            url = f"{self.FRED_BASE_URL}/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self._fred_api_key,
                "file_type": "json",
            }
            if start_date:
                params["observation_start"] = start_date
            if end_date:
                params["observation_end"] = end_date

            from ..utils.http_client import safe_get

            response = safe_get(url, params=params, timeout=30)

            if response is not None and response.status_code == 200:
                data = response.json()
                result = {
                    "series_id": series_id,
                    "observations": [
                        {
                            "date": obs["date"],
                            "value": float(obs["value"]) if obs["value"] != "." else None,
                        }
                        for obs in data.get("observations", [])
                    ],
                    "count": len(data.get("observations", [])),
                    "fetched_at": datetime.now().isoformat(),
                }
                self._set_cache(cache_key, result)
                return result

        except Exception as e:
            print(f"获取 FRED 数据 {series_id} 失败: {e}")

        return None

    def fetch_world_bank_indicator(
        self,
        indicator_id: str,
        country: str = "all",
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> dict[str, Any] | None:
        """
        获取世界银行指标数据

        Args:
            indicator_id: 世界银行指标 ID
            country: 国家代码（如 CHN, USA, 或 all）
            start_year: 开始年份
            end_year: 结束年份

        Returns:
            指标数据
        """
        cache_key = f"wb_{indicator_id}_{country}_{start_year}_{end_year}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            url = f"{self.WORLD_BANK_BASE_URL}/country/{country}/indicator/{indicator_id}"
            params = {"format": "json", "per_page": 1000}
            if start_year:
                params["date"] = f"{start_year}"
            if end_year:
                params["date"] = f"{params.get('date', '')}:{end_year}"

            response = self.requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                observations = []
                for item in data[1] if len(data) > 1 else []:
                    if item.get("value") is not None:
                        observations.append(
                            {
                                "country": item.get("country", {}).get("value"),
                                "country_code": item.get("countryiso3code"),
                                "year": item.get("date"),
                                "value": float(item["value"]),
                            }
                        )

                result = {
                    "indicator_id": indicator_id,
                    "observations": observations,
                    "count": len(observations),
                    "fetched_at": datetime.now().isoformat(),
                }
                self._set_cache(cache_key, result)
                return result

        except Exception as e:
            print(f"获取世界银行数据 {indicator_id} 失败: {e}")

        return None

    def get_indicator(self, indicator_key: str) -> dict[str, Any] | None:
        """
        获取宏观经济指标

        Args:
            indicator_key: 指标键（如 us_gdp, china_cpi）

        Returns:
            指标数据
        """
        if indicator_key not in self.INDICATORS:
            print(f"未知指标: {indicator_key}")
            return None

        indicator = self.INDICATORS[indicator_key]

        if "fred_id" in indicator:
            return self.fetch_fred_series(indicator["fred_id"])
        elif "world_bank_id" in indicator:
            return self.fetch_world_bank_indicator(indicator["world_bank_id"])

        return None

    def get_interest_rates(self) -> dict[str, Any]:
        """
        获取主要国家利率

        Returns:
            利率数据
        """
        result: dict[str, Any] = {
            "us_fed_funds_rate": None,
            "us_10y_treasury": None,
            "fetched_at": datetime.now().isoformat(),
        }

        fed_data = self.get_indicator("us_fed_funds_rate")
        if fed_data and fed_data.get("observations"):
            latest = fed_data["observations"][-1]
            result["us_fed_funds_rate"] = {
                "value": latest["value"],
                "date": latest["date"],
            }

        treasury_data = self.get_indicator("us_10y_treasury")
        if treasury_data and treasury_data.get("observations"):
            latest = treasury_data["observations"][-1]
            result["us_10y_treasury"] = {
                "value": latest["value"],
                "date": latest["date"],
            }

        return result

    def get_inflation_data(self) -> dict[str, Any]:
        """
        获取通胀数据

        Returns:
            通胀数据
        """
        result: dict[str, Any] = {
            "us_cpi": None,
            "china_cpi": None,
            "fetched_at": datetime.now().isoformat(),
        }

        us_cpi = self.get_indicator("us_cpi")
        if us_cpi and us_cpi.get("observations"):
            latest = us_cpi["observations"][-1]
            result["us_cpi"] = {
                "value": latest["value"],
                "date": latest["date"],
            }

        china_cpi = self.get_indicator("china_cpi")
        if china_cpi and china_cpi.get("observations"):
            latest = china_cpi["observations"][-1]
            result["china_cpi"] = {
                "value": latest["value"],
                "year": latest["year"],
            }

        return result

    def get_gdp_data(self) -> dict[str, Any]:
        """
        获取 GDP 数据

        Returns:
            GDP 数据
        """
        result: dict[str, Any] = {
            "us_gdp": None,
            "china_gdp": None,
            "world_gdp_growth": None,
            "fetched_at": datetime.now().isoformat(),
        }

        us_gdp = self.get_indicator("us_gdp")
        if us_gdp and us_gdp.get("observations"):
            latest = us_gdp["observations"][-1]
            result["us_gdp"] = {
                "value": latest["value"],
                "date": latest["date"],
            }

        china_gdp = self.get_indicator("china_gdp")
        if china_gdp and china_gdp.get("observations"):
            latest = china_gdp["observations"][-1]
            result["china_gdp"] = {
                "value": latest["value"],
                "year": latest["year"],
            }

        world_gdp = self.get_indicator("world_gdp_growth")
        if world_gdp and world_gdp.get("observations"):
            latest = world_gdp["observations"][-1]
            result["world_gdp_growth"] = {
                "value": latest["value"],
                "year": latest["year"],
            }

        return result

    def get_economic_summary(self) -> dict[str, Any]:
        """
        获取经济数据摘要

        Returns:
            经济数据摘要
        """
        return {
            "interest_rates": self.get_interest_rates(),
            "inflation": self.get_inflation_data(),
            "gdp": self.get_gdp_data(),
            "fetched_at": datetime.now().isoformat(),
        }


_macro_fetcher: MacroEconomicFetcher | None = None


def get_macro_fetcher(fred_api_key: str | None = None) -> MacroEconomicFetcher:
    """获取宏观经济数据获取器单例"""
    global _macro_fetcher
    if _macro_fetcher is None:
        _macro_fetcher = MacroEconomicFetcher(fred_api_key)
    return _macro_fetcher
