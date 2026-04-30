"""
Unified Data Fetcher using Provider Registry.
统一数据获取入口 - 使用 Provider Registry
"""

from typing import Any, Optional

from .providers import DataType, ProviderRegistry
from .providers.akshare_provider import AkshareProvider
from .providers.alpha_vantage_provider import AlphaVantageProvider


class UnifiedDataFetcher:
    """
    统一数据获取入口

    使用 Provider Registry 自动选择最佳数据源
    """

    _instance: Optional["UnifiedDataFetcher"] = None
    _initialized: bool = False

    def __new__(cls) -> "UnifiedDataFetcher":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._registry = ProviderRegistry()
        self._register_default_providers()
        self._initialized = True

    def _register_default_providers(self) -> None:
        """注册默认数据源"""
        akshare = AkshareProvider(priority=10)
        self._registry.register(akshare)

        alpha_vantage = AlphaVantageProvider(priority=20)
        self._registry.register(alpha_vantage)

    def fetch_stock_cn(self, symbol: str, **kwargs) -> dict[str, Any] | None:
        """获取 A 股行情"""
        return self._registry.fetch(DataType.STOCK_CN, symbol, **kwargs)

    def fetch_stock_us(self, symbol: str, **kwargs) -> dict[str, Any] | None:
        """获取美股行情"""
        return self._registry.fetch(DataType.STOCK_US, symbol, **kwargs)

    def fetch_fund_cn(self, symbol: str, **kwargs) -> dict[str, Any] | None:
        """获取基金净值"""
        return self._registry.fetch(DataType.FUND_CN, symbol, **kwargs)

    def fetch_index(self, symbol: str, **kwargs) -> dict[str, Any] | None:
        """获取指数行情"""
        return self._registry.fetch(DataType.INDEX, symbol, **kwargs)

    def fetch(
        self,
        data_type: DataType,
        symbol: str,
        **kwargs,
    ) -> dict[str, Any] | None:
        """
        通用数据获取方法

        Args:
            data_type: 数据类型
            symbol: 代码
            **kwargs: 其他参数

        Returns:
            数据字典
        """
        return self._registry.fetch(data_type, symbol, **kwargs)

    def get_available_providers(self, data_type: DataType) -> list[str]:
        """获取指定数据类型的可用数据源"""
        providers = self._registry.get_all_providers(data_type)
        return [p.name for p in providers if p.is_available()]

    def get_provider_info(self) -> dict[str, list[str]]:
        """获取所有数据源信息"""
        info: dict[str, list[str]] = {}
        for data_type in DataType:
            providers = self.get_available_providers(data_type)
            if providers:
                info[data_type.value] = providers
        return info


unified_data_fetcher = UnifiedDataFetcher()
