"""
Unified data source interface for asset-lens.
数据源统一接口 - 提供统一的数据获取 API

支持的数据源:
- 股票: A股、港股、美股
- 基金: 场内基金、场外基金
- 期货: 国内期货、国际期货
- 加密货币: BTC、ETH 等
- 宏观经济: GDP、CPI、利率等
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class DataSourceType(Enum):
    """数据源类型"""

    STOCK_CN = "stock_cn"  # A股
    STOCK_HK = "stock_hk"  # 港股
    STOCK_US = "stock_us"  # 美股
    FUND_CN = "fund_cn"  # 场内基金
    FUND_ETF = "fund_etf"  # ETF基金
    FUTURES_CN = "futures_cn"  # 国内期货
    FUTURES_INTL = "futures_intl"  # 国际期货
    CRYPTO = "crypto"  # 加密货币
    MACRO = "macro"  # 宏观经济
    INDEX = "index"  # 市场指数


class AssetType(Enum):
    """资产类型"""

    EQUITY = "equity"  # 股票
    FUND = "fund"  # 基金
    FUTURES = "futures"  # 期货
    CRYPTO = "crypto"  # 加密货币
    BOND = "bond"  # 债券
    CASH = "cash"  # 现金
    INDEX = "index"  # 指数


@runtime_checkable
class DataSource(Protocol):
    """数据源协议"""

    @property
    def source_type(self) -> DataSourceType:
        """数据源类型"""
        ...

    @property
    def asset_type(self) -> AssetType:
        """资产类型"""
        ...

    def fetch_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情"""
        ...

    def fetch_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取历史数据"""
        ...


class UnifiedDataFetcher:
    """统一数据获取器"""

    def __init__(self):
        self._fetchers: Dict[DataSourceType, Any] = {}
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化"""
        if self._initialized:
            return

        self._fetchers = {
            DataSourceType.STOCK_CN: self._get_stock_fetcher(),
            DataSourceType.STOCK_HK: self._get_international_fetcher(),
            DataSourceType.STOCK_US: self._get_international_fetcher(),
            DataSourceType.FUND_CN: self._get_fund_fetcher(),
            DataSourceType.FUTURES_CN: self._get_futures_fetcher(),
            DataSourceType.CRYPTO: self._get_crypto_fetcher(),
            DataSourceType.MACRO: self._get_macro_fetcher(),
            DataSourceType.INDEX: self._get_market_fetcher(),
        }
        self._initialized = True

    def _get_stock_fetcher(self):
        """获取股票数据获取器"""
        from .stock_history_fetcher import StockHistoryFetcher

        return StockHistoryFetcher()

    def _get_international_fetcher(self):
        """获取国际股票数据获取器"""
        from .international_stock_fetcher import InternationalStockFetcher

        return InternationalStockFetcher()

    def _get_fund_fetcher(self):
        """获取基金数据获取器"""
        from .fund_fetcher import FundFetcher

        return FundFetcher()

    def _get_futures_fetcher(self):
        """获取期货数据获取器"""
        from .futures_fetcher import get_futures_fetcher

        return get_futures_fetcher()

    def _get_crypto_fetcher(self):
        """获取加密货币数据获取器"""
        from .crypto_fetcher import get_crypto_fetcher

        return get_crypto_fetcher()

    def _get_macro_fetcher(self):
        """获取宏观经济数据获取器"""
        from .macro_economic_fetcher import get_macro_fetcher

        return get_macro_fetcher()

    def _get_market_fetcher(self):
        """获取市场指数数据获取器"""
        from .market_data_fetcher import MarketDataFetcher

        return MarketDataFetcher()

    def fetch(
        self,
        symbol: str,
        source_type: DataSourceType,
        data_type: str = "quote",
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        统一数据获取接口

        Args:
            symbol: 代码/符号
            source_type: 数据源类型
            data_type: 数据类型 (quote/history/order_book)
            **kwargs: 其他参数

        Returns:
            数据字典
        """
        self._lazy_init()

        fetcher = self._fetchers.get(source_type)
        if not fetcher:
            print(f"不支持的数据源类型: {source_type}")
            return None

        try:
            if data_type == "quote":
                return self._fetch_quote(fetcher, symbol, source_type)
            elif data_type == "history":
                return self._fetch_history(fetcher, symbol, source_type, **kwargs)
            elif data_type == "order_book":
                return self._fetch_order_book(fetcher, symbol, source_type)
            else:
                print(f"不支持的数据类型: {data_type}")
                return None

        except Exception as e:
            print(f"获取数据失败: {e}")
            return None

    def _fetch_quote(
        self, fetcher: Any, symbol: str, source_type: DataSourceType
    ) -> Optional[Dict[str, Any]]:
        """获取行情"""
        if source_type == DataSourceType.STOCK_CN:
            return fetcher.get_stock_realtime_quote(symbol)
        elif source_type in (DataSourceType.STOCK_HK, DataSourceType.STOCK_US):
            if source_type == DataSourceType.STOCK_HK:
                return fetcher.fetch_hk_stock_quote(symbol)
            else:
                return fetcher.fetch_us_stock_quote(symbol)
        elif source_type == DataSourceType.FUND_CN:
            return fetcher.fetch_fund_quote(symbol)
        elif source_type == DataSourceType.FUTURES_CN:
            return fetcher.fetch_domestic_quote(symbol)
        elif source_type == DataSourceType.CRYPTO:
            return fetcher.get_ticker(symbol)
        elif source_type == DataSourceType.MACRO:
            return fetcher.get_economic_summary()
        elif source_type == DataSourceType.INDEX:
            return fetcher.fetch_domestic_index(symbol)
        return None

    def _fetch_history(
        self,
        fetcher: Any,
        symbol: str,
        source_type: DataSourceType,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """获取历史数据"""
        if source_type == DataSourceType.STOCK_CN:
            history = fetcher.fetch_history(symbol, start_date=start_date, end_date=end_date)
            return {"symbol": symbol, "history": history}
        elif source_type in (DataSourceType.STOCK_HK, DataSourceType.STOCK_US):
            if source_type == DataSourceType.STOCK_HK:
                history = fetcher.fetch_hk_stock_history(symbol)
            else:
                history = fetcher.fetch_us_stock_history(symbol)
            return {"symbol": symbol, "history": history}
        elif source_type == DataSourceType.FUTURES_CN:
            history = fetcher.fetch_domestic_history(symbol, start_date, end_date)
            return {"symbol": symbol, "history": history}
        elif source_type == DataSourceType.CRYPTO:
            ohlcvs = fetcher.get_ohlcvs(symbol, **kwargs)
            return {"symbol": symbol, "history": ohlcvs}
        return None

    def _fetch_order_book(
        self, fetcher: Any, symbol: str, source_type: DataSourceType
    ) -> Optional[Dict[str, Any]]:
        """获取订单簿"""
        if source_type == DataSourceType.CRYPTO:
            return fetcher.get_order_book(symbol)
        return None

    def get_supported_sources(self) -> List[DataSourceType]:
        """获取支持的数据源列表"""
        self._lazy_init()
        return list(self._fetchers.keys())

    def get_source_info(self, source_type: DataSourceType) -> Dict[str, Any]:
        """获取数据源信息"""
        info = {
            DataSourceType.STOCK_CN: {
                "name": "A股",
                "description": "中国A股市场数据",
                "sources": ["AkShare", "Tushare", "Baostock"],
            },
            DataSourceType.STOCK_HK: {
                "name": "港股",
                "description": "香港股票市场数据",
                "sources": ["AkShare"],
            },
            DataSourceType.STOCK_US: {
                "name": "美股",
                "description": "美国股票市场数据",
                "sources": ["AkShare"],
            },
            DataSourceType.FUND_CN: {
                "name": "基金",
                "description": "中国基金数据",
                "sources": ["AkShare", "EastMoney"],
            },
            DataSourceType.FUTURES_CN: {
                "name": "期货",
                "description": "中国期货市场数据",
                "sources": ["AkShare", "Sina"],
            },
            DataSourceType.CRYPTO: {
                "name": "加密货币",
                "description": "加密货币市场数据",
                "sources": ["CCXT (Binance, OKX, etc.)"],
            },
            DataSourceType.MACRO: {
                "name": "宏观经济",
                "description": "宏观经济指标数据",
                "sources": ["FRED", "World Bank"],
            },
            DataSourceType.INDEX: {
                "name": "市场指数",
                "description": "国内外市场指数",
                "sources": ["AkShare"],
            },
        }
        return info.get(source_type, {})


_unified_fetcher: Optional[UnifiedDataFetcher] = None


def get_unified_fetcher() -> UnifiedDataFetcher:
    """获取统一数据获取器单例"""
    global _unified_fetcher
    if _unified_fetcher is None:
        _unified_fetcher = UnifiedDataFetcher()
    return _unified_fetcher


def fetch_data(
    symbol: str,
    source_type: str,
    data_type: str = "quote",
    **kwargs,
) -> Optional[Dict[str, Any]]:
    """
    便捷函数：获取数据

    Args:
        symbol: 代码/符号
        source_type: 数据源类型字符串 (stock_cn, stock_hk, crypto, etc.)
        data_type: 数据类型 (quote/history)
        **kwargs: 其他参数

    Returns:
        数据字典

    Example:
        >>> fetch_data("000001", "stock_cn", "quote")
        >>> fetch_data("BTC/USDT", "crypto", "quote")
        >>> fetch_data("AU0", "futures_cn", "quote")
    """
    try:
        st = DataSourceType(source_type)
    except ValueError:
        print(f"无效的数据源类型: {source_type}")
        return None

    return get_unified_fetcher().fetch(symbol, st, data_type, **kwargs)
