"""
Cryptocurrency data fetcher for asset-lens.
加密货币数据获取模块 - 获取主流加密货币实时行情和历史数据

数据源: CCXT (支持 100+ 交易所)
- GitHub: https://github.com/ccxt/ccxt
- 文档: https://docs.ccxt.com
- 支持交易所: Binance, OKX, Coinbase, Kraken, Huobi 等
"""

import time
from datetime import datetime
from typing import Any, ClassVar


class CryptoFetcher:
    """加密货币数据获取器 - 使用 CCXT 库"""

    SUPPORTED_EXCHANGES: ClassVar[list[str]] = [
        "binance",
        "okx",
        "coinbase",
        "kraken",
        "huobi",
        "gateio",
        "bybit",
    ]

    DEFAULT_EXCHANGE: ClassVar[str] = "binance"

    CACHE_DURATION = 300  # 5分钟缓存

    def __init__(self, exchange: str | None = None) -> None:
        self._exchange_name = exchange or self.DEFAULT_EXCHANGE
        self._exchange = None
        self._cache: dict[str, Any] = {}
        self._cache_time: dict[str, float] = {}

    @property
    def exchange(self):
        """延迟加载交易所实例"""
        if self._exchange is None:
            try:
                import ccxt

                exchange_class = getattr(ccxt, self._exchange_name, None)
                if exchange_class is None:
                    raise ValueError(f"不支持的交易所: {self._exchange_name}")

                self._exchange = exchange_class({"enableRateLimit": True, "timeout": 30000})

            except ImportError:
                raise ImportError(
                    "请先安装 CCXT: pip install ccxt\n"
                    "CCXT 是一个统一的加密货币交易 API 库\n"
                    "支持 100+ 交易所: Binance, OKX, Coinbase, Kraken 等\n"
                    "GitHub: https://github.com/ccxt/ccxt"
                ) from None
        return self._exchange

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache_time:
            return False
        return time.time() - self._cache_time[cache_key] < self.CACHE_DURATION

    def _get_cached(self, cache_key: str) -> Any | None:
        """获取缓存数据"""
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None

    def _set_cache(self, cache_key: str, data: Any) -> None:
        """设置缓存"""
        self._cache[cache_key] = data
        self._cache_time[cache_key] = time.time()

    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()
        self._cache_time.clear()

    def get_ticker(self, symbol: str) -> dict[str, Any] | None:
        """
        获取加密货币实时行情

        Args:
            symbol: 交易对符号（如 BTC/USDT, ETH/USDT）

        Returns:
            行情数据字典
        """
        cache_key = f"ticker_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return dict(cached)  # type: ignore

        try:
            ticker = self.exchange.fetch_ticker(symbol)

            result = {
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
                "datetime": datetime.fromtimestamp(ticker.get("timestamp", 0) / 1000).isoformat(),
            }

            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            print(f"获取 {symbol} 行情失败: {e}")
            return None

    def get_ohlcvs(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
        since: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取 K 线数据

        Args:
            symbol: 交易对符号（如 BTC/USDT）
            timeframe: 时间周期（1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M）
            limit: 返回数据条数
            since: 起始时间戳（毫秒）

        Returns:
            K 线数据列表
        """
        cache_key = f"ohlcv_{symbol}_{timeframe}_{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            return list(cached)  # type: ignore

        try:
            ohlcvs = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)

            result = [
                {
                    "timestamp": ohlcv[0],
                    "datetime": datetime.fromtimestamp(ohlcv[0] / 1000).isoformat(),
                    "open": float(ohlcv[1]),
                    "high": float(ohlcv[2]),
                    "low": float(ohlcv[3]),
                    "close": float(ohlcv[4]),
                    "volume": float(ohlcv[5]),
                }
                for ohlcv in ohlcvs
            ]

            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            print(f"获取 {symbol} K线数据失败: {e}")
            return []

    def get_order_book(self, symbol: str, limit: int = 20) -> dict[str, Any] | None:
        """
        获取订单簿（买卖盘）

        Args:
            symbol: 交易对符号
            limit: 返回档数

        Returns:
            订单簿数据
        """
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit)

            return {
                "symbol": symbol,
                "exchange": self._exchange_name,
                "bids": [
                    {"price": float(bid[0]), "amount": float(bid[1])} for bid in order_book.get("bids", [])[:limit]
                ],
                "asks": [
                    {"price": float(ask[0]), "amount": float(ask[1])} for ask in order_book.get("asks", [])[:limit]
                ],
                "timestamp": order_book.get("timestamp", 0),
            }

        except Exception as e:
            print(f"获取 {symbol} 订单簿失败: {e}")
            return None

    def get_market_cap(self) -> dict[str, Any] | None:
        """
        获取加密货币总市值（通过 CoinGecko API）

        Returns:
            市值数据
        """
        try:
            from ..utils.http_client import safe_get

            url = "https://api.coingecko.com/api/v3/global"
            response = safe_get(url, timeout=10)

            if response is not None and response.status_code == 200:
                data = response.json()
                return {
                    "total_market_cap_usd": data["data"]["total_market_cap"]["usd"],
                    "total_volume_usd": data["data"]["total_volume"]["usd"],
                    "btc_dominance": data["data"]["market_cap_percentage"]["btc"],
                    "eth_dominance": data["data"]["market_cap_percentage"]["eth"],
                    "updated_at": datetime.fromtimestamp(data["data"]["updated_at"]).isoformat(),
                }

        except Exception as e:
            print(f"获取市值数据失败: {e}")

        return None

    def get_top_cryptos(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        获取市值排名前 N 的加密货币

        Args:
            limit: 返回数量

        Returns:
            加密货币列表
        """
        try:
            from ..utils.http_client import safe_get

            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": False,
            }

            response = safe_get(url, params=params, timeout=10)

            if response is not None and response.status_code == 200:
                data = response.json()
                result = [
                    {
                        "id": coin.get("id"),
                        "symbol": coin.get("symbol", "").upper(),
                        "name": coin.get("name"),
                        "current_price": coin.get("current_price"),
                        "market_cap": coin.get("market_cap"),
                        "market_cap_rank": coin.get("market_cap_rank"),
                        "total_volume": coin.get("total_volume"),
                        "price_change_24h": coin.get("price_change_24h"),
                        "price_change_percentage_24h": coin.get("price_change_percentage_24h"),
                        "circulating_supply": coin.get("circulating_supply"),
                        "total_supply": coin.get("total_supply"),
                        "image": coin.get("image"),
                        "last_updated": coin.get("last_updated"),
                    }
                    for coin in data
                ]
                return result

        except Exception as e:
            print(f"获取热门加密货币失败: {e}")

        return []

    def get_supported_symbols(self) -> list[str]:
        """
        获取交易所支持的所有交易对

        Returns:
            交易对列表
        """
        try:
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            print(f"获取交易对列表失败: {e}")
            return []

    def convert_symbol_to_ccxt(self, symbol: str) -> str:
        """
        将通用符号转换为 CCXT 格式

        Args:
            symbol: 通用符号（如 BTCUSDT, ETHUSDT）

        Returns:
            CCXT 格式符号（如 BTC/USDT, ETH/USDT）
        """
        stablecoins = ["USDT", "USDC", "BUSD", "USD", "EUR"]

        for stablecoin in stablecoins:
            if symbol.endswith(stablecoin):
                base = symbol[: -len(stablecoin)]
                return f"{base}/{stablecoin}"

        if symbol.endswith("BTC"):
            base = symbol[:-3]
            return f"{base}/BTC"

        if symbol.endswith("ETH"):
            base = symbol[:-3]
            return f"{base}/ETH"

        return symbol


_crypto_fetcher: CryptoFetcher | None = None


def get_crypto_fetcher(exchange: str | None = None) -> CryptoFetcher:
    """获取加密货币数据获取器单例"""
    global _crypto_fetcher
    if _crypto_fetcher is None:
        _crypto_fetcher = CryptoFetcher(exchange)
    return _crypto_fetcher
