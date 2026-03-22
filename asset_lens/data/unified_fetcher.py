"""
Unified data source interface for asset-lens.
数据源统一接口 - 提供统一的数据获取 API

⚠️ DEPRECATED: 此模块已弃用，请使用 unified_data_fetcher.py 中的 UnifiedDataFetcher。
此模块保留仅为向后兼容，将在未来版本中移除。

新版本使用 Provider Registry 架构，支持自动选择最佳数据源。

迁移指南:
    # 旧版 (已弃用)
    from asset_lens.data.unified_fetcher import UnifiedDataFetcher
    fetcher = UnifiedDataFetcher()
    
    # 新版 (推荐)
    from asset_lens.data.unified_data_fetcher import unified_data_fetcher
    result = unified_data_fetcher.fetch_stock_cn("600519")
"""

import warnings
from enum import Enum
from typing import Any


class DataSourceType(Enum):
    """数据源类型 - 保留用于向后兼容"""

    STOCK_CN = "stock_cn"
    STOCK_HK = "stock_hk"
    STOCK_US = "stock_us"
    FUND_CN = "fund_cn"
    FUND_ETF = "fund_etf"
    FUTURES_CN = "futures_cn"
    FUTURES_INTL = "futures_intl"
    CRYPTO = "crypto"
    MACRO = "macro"
    INDEX = "index"


class AssetType(Enum):
    """资产类型 - 保留用于向后兼容"""

    EQUITY = "equity"
    FUND = "fund"
    FUTURES = "futures"
    CRYPTO = "crypto"
    BOND = "bond"
    CASH = "cash"
    INDEX = "index"


class UnifiedDataFetcher:
    """
    统一数据获取器 - 薄包装
    
    ⚠️ DEPRECATED: 请使用 unified_data_fetcher.py 中的 unified_data_fetcher 实例。
    
    此类仅作为向后兼容的薄包装，内部转发到新的 Provider Registry 实现。
    """

    def __init__(self):
        warnings.warn(
            "UnifiedDataFetcher 已弃用，请使用 unified_data_fetcher.py 中的 unified_data_fetcher",
            DeprecationWarning,
            stacklevel=2,
        )
        self._new_fetcher = None

    def _get_new_fetcher(self):
        """获取新的统一数据获取器"""
        if self._new_fetcher is None:
            from .unified_data_fetcher import unified_data_fetcher
            self._new_fetcher = unified_data_fetcher
        return self._new_fetcher

    def fetch(
        self,
        symbol: str,
        source_type: DataSourceType,
        data_type: str = "quote",
        **kwargs,
    ) -> dict[str, Any] | None:
        """
        统一数据获取接口 - 转发到新实现
        
        Args:
            symbol: 代码/符号
            source_type: 数据源类型
            data_type: 数据类型 (quote/history)
            **kwargs: 其他参数
            
        Returns:
            数据字典
        """
        from .providers import DataType

        type_map = {
            DataSourceType.STOCK_CN: DataType.STOCK_CN,
            DataSourceType.STOCK_HK: DataType.STOCK_HK,
            DataSourceType.STOCK_US: DataType.STOCK_US,
            DataSourceType.FUND_CN: DataType.FUND_CN,
            DataSourceType.FUND_ETF: DataType.FUND_ETF,
            DataSourceType.FUTURES_CN: DataType.FUTURES_CN,
            DataSourceType.FUTURES_INTL: DataType.FUTURES_INTL,
            DataSourceType.CRYPTO: DataType.CRYPTO,
            DataSourceType.MACRO: DataType.MACRO,
            DataSourceType.INDEX: DataType.INDEX,
        }

        new_type = type_map.get(source_type)
        if new_type is None:
            warnings.warn(f"不支持的数据源类型: {source_type}", RuntimeWarning, stacklevel=2)
            return None

        fetcher = self._get_new_fetcher()
        result: dict[str, Any] | None = fetcher.fetch(new_type, symbol, **kwargs)
        return result


__all__ = ["UnifiedDataFetcher", "DataSourceType", "AssetType"]
