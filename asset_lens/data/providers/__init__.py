"""
Data Provider Registry for asset-lens.
数据源注册中心 - 统一管理数据源选择策略
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class ProviderType(Enum):
    """数据源类型"""
    AKSHARE = "akshare"
    EASTMONEY = "eastmoney"
    TUSHARE = "tushare"
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    CCXT = "ccxt"
    LOCAL = "local"


class DataType(Enum):
    """数据类型"""
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


@runtime_checkable
class DataProvider(Protocol):
    """数据源协议"""
    
    @property
    def name(self) -> str:
        """数据源名称"""
        ...
    
    @property
    def provider_type(self) -> ProviderType:
        """数据源类型"""
        ...
    
    @property
    def priority(self) -> int:
        """优先级（数字越小优先级越高）"""
        ...
    
    @property
    def supported_data_types(self) -> List[DataType]:
        """支持的数据类型列表"""
        ...
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        ...
    
    def fetch(self, data_type: DataType, symbol: str, **kwargs) -> Optional[Dict[str, Any]]:
        """获取数据"""
        ...


@dataclass
class ProviderInfo:
    """数据源信息"""
    provider: DataProvider
    data_type: DataType
    priority: int
    is_available: bool
    error_count: int = 0
    success_count: int = 0
    total_response_time: float = 0.0
    last_success_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    last_error_message: Optional[str] = None


@dataclass
class ProviderHealth:
    """数据源健康状态"""
    name: str
    provider_type: str
    is_available: bool
    total_requests: int
    success_count: int
    error_count: int
    success_rate: float
    avg_response_time: float
    last_success_time: Optional[datetime]
    last_error_time: Optional[datetime]
    last_error_message: Optional[str]
    supported_data_types: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "is_available": self.is_available,
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(self.success_rate * 100, 2),
            "avg_response_time_ms": round(self.avg_response_time * 1000, 2),
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "last_error_message": self.last_error_message,
            "supported_data_types": self.supported_data_types,
        }


class ProviderRegistry:
    """
    数据源注册中心
    
    集中管理数据源选择策略，按优先级返回可用的数据源
    """
    
    _instance: Optional["ProviderRegistry"] = None
    _initialized: bool
    
    def __new__(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self._providers: Dict[DataType, List[ProviderInfo]] = {}
        self._all_providers: Dict[str, DataProvider] = {}
        self._initialized = True
    
    def register(
        self,
        provider: DataProvider,
        data_type: Optional[DataType] = None,
        priority: Optional[int] = None,
    ) -> None:
        """
        注册数据源
        
        Args:
            provider: 数据源实例
            data_type: 数据类型（如果不指定，使用 provider 支持的所有类型）
            priority: 优先级（如果不指定，使用 provider 的默认优先级）
        """
        provider_name = provider.name
        self._all_providers[provider_name] = provider
        
        if data_type is not None:
            data_types = [data_type]
        else:
            data_types = provider.supported_data_types
        
        actual_priority = priority if priority is not None else provider.priority
        
        for dt in data_types:
            if dt not in self._providers:
                self._providers[dt] = []
            
            self._providers[dt].append(
                ProviderInfo(
                    provider=provider,
                    data_type=dt,
                    priority=actual_priority,
                    is_available=provider.is_available(),
                )
            )
            self._providers[dt].sort(key=lambda x: x.priority)
    
    def unregister(self, provider_name: str) -> bool:
        """
        注销数据源
        
        Args:
            provider_name: 数据源名称
            
        Returns:
            是否成功注销
        """
        if provider_name not in self._all_providers:
            return False
        
        del self._all_providers[provider_name]
        
        for data_type in self._providers:
            self._providers[data_type] = [
                info for info in self._providers[data_type]
                if info.provider.name != provider_name
            ]
        
        return True
    
    def get_provider(
        self,
        data_type: DataType,
        check_availability: bool = True,
    ) -> Optional[DataProvider]:
        """
        获取数据源
        
        按优先级返回可用的数据源
        
        Args:
            data_type: 数据类型
            check_availability: 是否检查可用性
            
        Returns:
            数据源实例
            
        Raises:
            NoProviderAvailableError: 没有可用的数据源
        """
        if data_type not in self._providers:
            return None
        
        for info in self._providers[data_type]:
            if check_availability and not info.provider.is_available():
                continue
            return info.provider
        
        return None
    
    def get_all_providers(self, data_type: DataType) -> List[DataProvider]:
        """
        获取指定数据类型的所有数据源
        
        Args:
            data_type: 数据类型
            
        Returns:
            数据源列表（按优先级排序）
        """
        if data_type not in self._providers:
            return []
        
        return [info.provider for info in self._providers[data_type]]
    
    def get_available_providers(self, data_type: DataType) -> List[DataProvider]:
        """
        获取指定数据类型的可用数据源
        
        Args:
            data_type: 数据类型
            
        Returns:
            可用的数据源列表（按优先级排序）
        """
        if data_type not in self._providers:
            return []
        
        return [
            info.provider for info in self._providers[data_type]
            if info.provider.is_available()
        ]
    
    def fetch(
        self,
        data_type: DataType,
        symbol: str,
        fallback: bool = True,
        use_cache: bool = True,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        获取数据
        
        按优先级尝试获取数据，支持自动降级和缓存
        
        Args:
            data_type: 数据类型
            symbol: 代码/符号
            fallback: 是否自动降级到下一个数据源
            use_cache: 是否使用缓存
            **kwargs: 其他参数
            
        Returns:
            数据字典
        """
        from .cache import provider_cache
        
        providers = self._providers.get(data_type, [])
        
        for info in providers:
            if not info.provider.is_available():
                continue
            
            provider_name = info.provider.name
            
            if use_cache:
                cached = provider_cache.get(data_type.value, provider_name, symbol, **kwargs)
                if cached is not None:
                    result: Optional[Dict[str, Any]] = cached
                    return result
            
            start_time = time.time()
            try:
                result = info.provider.fetch(data_type, symbol, **kwargs)
                response_time = time.time() - start_time
                
                if result is not None:
                    info.success_count += 1
                    info.total_response_time += response_time
                    info.last_success_time = datetime.now()
                    
                    if use_cache:
                        provider_cache.set(data_type.value, provider_name, symbol, result, **kwargs)
                    
                    return result
            except Exception as e:
                info.error_count += 1
                info.last_error_time = datetime.now()
                info.last_error_message = str(e)
                if not fallback:
                    raise
                continue
        
        return None
    
    def list_providers(self) -> Dict[str, List[str]]:
        """
        列出所有注册的数据源
        
        Returns:
            按数据类型分组的数据源名称列表
        """
        result: Dict[str, List[str]] = {}
        
        for data_type, providers in self._providers.items():
            result[data_type.value] = [
                info.provider.name for info in providers
            ]
        
        return result
    
    def check_availability(self) -> Dict[str, Dict[str, bool]]:
        """
        检查所有数据源的可用性
        
        Returns:
            按数据类型分组的可用性状态
        """
        result: Dict[str, Dict[str, bool]] = {}
        
        for data_type, providers in self._providers.items():
            result[data_type.value] = {
                info.provider.name: info.provider.is_available()
                for info in providers
            }
        
        return result
    
    def get_health(self, provider_name: Optional[str] = None) -> Dict[str, ProviderHealth]:
        """
        获取数据源健康状态
        
        Args:
            provider_name: 指定数据源名称（可选，默认返回所有）
            
        Returns:
            数据源健康状态字典
        """
        result: Dict[str, ProviderHealth] = {}
        
        provider_infos: Dict[str, List[ProviderInfo]] = {}
        for data_type, providers in self._providers.items():
            for info in providers:
                name = info.provider.name
                if name not in provider_infos:
                    provider_infos[name] = []
                provider_infos[name].append(info)
        
        for name, infos in provider_infos.items():
            if provider_name is not None and name != provider_name:
                continue
            
            total_requests = sum(i.success_count + i.error_count for i in infos)
            success_count = sum(i.success_count for i in infos)
            error_count = sum(i.error_count for i in infos)
            total_response_time = sum(i.total_response_time for i in infos)
            
            success_rate = success_count / total_requests if total_requests > 0 else 0.0
            avg_response_time = total_response_time / success_count if success_count > 0 else 0.0
            
            last_success = max(
                (i.last_success_time for i in infos if i.last_success_time),
                default=None,
            )
            last_error = max(
                (i.last_error_time for i in infos if i.last_error_time),
                default=None,
            )
            last_error_message = next(
                (i.last_error_message for i in infos if i.last_error_message),
                None,
            )
            
            provider = infos[0].provider
            result[name] = ProviderHealth(
                name=name,
                provider_type=provider.provider_type.value,
                is_available=provider.is_available(),
                total_requests=total_requests,
                success_count=success_count,
                error_count=error_count,
                success_rate=success_rate,
                avg_response_time=avg_response_time,
                last_success_time=last_success,
                last_error_time=last_error,
                last_error_message=last_error_message,
                supported_data_types=[i.data_type.value for i in infos],
            )
        
        return result
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        获取数据源健康摘要
        
        Returns:
            健康摘要字典
        """
        health_data = self.get_health()
        
        if not health_data:
            return {
                "total_providers": 0,
                "available_providers": 0,
                "overall_success_rate": 0.0,
                "providers": [],
            }
        
        available_count = sum(1 for h in health_data.values() if h.is_available)
        total_requests = sum(h.total_requests for h in health_data.values())
        total_success = sum(h.success_count for h in health_data.values())
        
        return {
            "total_providers": len(health_data),
            "available_providers": available_count,
            "overall_success_rate": round(total_success / total_requests * 100, 2) if total_requests > 0 else 0.0,
            "providers": [h.to_dict() for h in health_data.values()],
        }
    
    def clear(self) -> None:
        """清空所有注册的数据源"""
        self._providers.clear()
        self._all_providers.clear()


provider_registry = ProviderRegistry()


def register_default_providers() -> None:
    """注册默认数据源"""
    from .akshare_provider import akshare_provider
    from .alpha_vantage_provider import alpha_vantage_provider
    from .ccxt_provider import ccxt_provider
    
    provider_registry.register(akshare_provider)
    provider_registry.register(alpha_vantage_provider)
    provider_registry.register(ccxt_provider)


from .cache import provider_cache  # noqa: E402


__all__ = [
    "ProviderType",
    "DataType",
    "DataProvider",
    "ProviderInfo",
    "ProviderHealth",
    "ProviderRegistry",
    "provider_registry",
    "register_default_providers",
    "provider_cache",
]
