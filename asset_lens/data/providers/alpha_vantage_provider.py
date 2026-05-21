"""
Alpha Vantage Data Provider implementation.
Alpha Vantage 数据源实现
"""

import logging
import os
from typing import TYPE_CHECKING, Any

from . import DataType, ProviderType
from .base import BaseProvider

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import requests


class AlphaVantageProvider(BaseProvider):
    """
    Alpha Vantage 数据源

    使用 Alpha Vantage API 获取美股、外汇等数据
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str | None = None, priority: int = 30) -> None:
        super().__init__(
            name="alpha_vantage",
            provider_type=ProviderType.ALPHA_VANTAGE,
            priority=priority,
            supported_data_types=[
                DataType.STOCK_US,
                DataType.INDEX,
            ],
        )
        self._api_key = api_key or os.getenv("ALPHAVANTAGE_API_KEY")
        self._session: requests.Session | None = None

    @property
    def session(self):
        """延迟加载 requests session"""
        if self._session is None:
            try:
                import requests

                self._session = requests.Session()
            except ImportError:
                pass
        return self._session

    def _check_availability(self) -> bool:
        """检查 Alpha Vantage 是否可用"""
        return self._api_key is not None and self.session is not None

    def fetch(
        self,
        data_type: DataType,
        symbol: str,
        **kwargs,
    ) -> dict[str, Any] | None:
        """获取数据"""
        if not self.is_available():
            return None

        try:
            if data_type == DataType.STOCK_US:
                return self._fetch_stock_quote(symbol)
            elif data_type == DataType.INDEX:
                return self._fetch_index_quote(symbol)
            else:
                return None
        except Exception as e:
            logger.debug(f"忽略异常: {e}")
            return None

    def _fetch_stock_quote(self, symbol: str) -> dict[str, Any] | None:
        """获取美股行情"""
        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self._api_key,
            }

            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            if response.status_code != 200:
                return None

            data = response.json()
            if "Global Quote" not in data:
                return None

            quote = data["Global Quote"]
            return {
                "symbol": symbol,
                "current_price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": float(quote.get("10. change percent", "0").replace("%", "")),
                "volume": int(quote.get("06. volume", 0)),
                "open": float(quote.get("02. open", 0)),
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "prev_close": float(quote.get("08. previous close", 0)),
                "source": "alpha_vantage",
            }
        except (ValueError, TypeError):
            return None

    def _fetch_index_quote(self, symbol: str) -> dict[str, Any] | None:
        """获取指数行情"""
        return self._fetch_stock_quote(symbol)


alpha_vantage_provider = AlphaVantageProvider()
