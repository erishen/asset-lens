"""
CCXT Crypto Provider implementation.
CCXT 加密货币数据源实现
"""

from datetime import datetime
from typing import Any

from . import DataType, ProviderType
from .base import BaseProvider


class CCXTProvider(BaseProvider):
    """
    CCXT 加密货币数据源

    使用 CCXT 获取加密货币数据
    """

    DEFAULT_EXCHANGE = "binance"

    def __init__(
        self,
        exchange: str | None = None,
        priority: int = 20,
    ) -> None:
        super().__init__(
            name="ccxt",
            provider_type=ProviderType.CCXT,
            priority=priority,
            supported_data_types=[
                DataType.CRYPTO,
            ],
        )
        self._exchange_name = exchange or self.DEFAULT_EXCHANGE
        self._exchange = None

    @property
    def exchange(self):
        """延迟加载交易所实例"""
        if self._exchange is None:
            try:
                import ccxt

                exchange_class = getattr(ccxt, self._exchange_name, None)
                if exchange_class is not None:
                    self._exchange = exchange_class(
                        {"enableRateLimit": True, "timeout": 30000}
                    )
            except ImportError:
                pass
        return self._exchange

    def _check_availability(self) -> bool:
        """检查 CCXT 是否可用"""
        return self.exchange is not None

    def fetch(
        self,
        data_type: DataType,
        symbol: str,
        **kwargs,
    ) -> dict[str, Any] | None:
        """获取数据"""
        if not self.is_available():
            return None

        if data_type != DataType.CRYPTO:
            return None

        try:
            return self._fetch_ticker(symbol)
        except Exception:
            return None

    def _fetch_ticker(self, symbol: str) -> dict[str, Any] | None:
        """获取加密货币行情"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)

            return {
                "symbol": symbol,
                "exchange": self._exchange_name,
                "last": float(ticker.get("last", 0)),
                "bid": float(ticker.get("bid", 0)),
                "ask": float(ticker.get("ask", 0)),
                "high": float(ticker.get("high", 0)),
                "low": float(ticker.get("low", 0)),
                "volume": float(ticker.get("baseVolume", 0)),
                "quote_volume": float(ticker.get("quoteVolume", 0)),
                "change": float(ticker.get("change", 0)),
                "percentage": float(ticker.get("percentage", 0)),
                "timestamp": ticker.get("timestamp", 0),
                "datetime": datetime.fromtimestamp(
                    ticker.get("timestamp", 0) / 1000
                ).isoformat(),
                "source": "ccxt",
            }
        except Exception:
            return None

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
        since: int | None = None,
    ) -> list[dict[str, Any]]:
        """获取 K 线数据"""
        if not self.is_available():
            return []

        try:
            ohlcvs = self.exchange.fetch_ohlcv(
                symbol, timeframe, since=since, limit=limit
            )

            result = []
            for ohlcv in ohlcvs:
                result.append({
                    "timestamp": ohlcv[0],
                    "datetime": datetime.fromtimestamp(ohlcv[0] / 1000).isoformat(),
                    "open": float(ohlcv[1]),
                    "high": float(ohlcv[2]),
                    "low": float(ohlcv[3]),
                    "close": float(ohlcv[4]),
                    "volume": float(ohlcv[5]),
                    "source": "ccxt",
                })

            return result
        except Exception:
            return []


ccxt_provider = CCXTProvider()
