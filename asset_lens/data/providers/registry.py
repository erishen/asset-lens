import time
from datetime import datetime
from typing import Any, Optional

from .models import ProviderHealth, ProviderInfo
from .protocol import DataProvider
from .types import DataType


class ProviderRegistry:
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

        self._providers: dict[DataType, list[ProviderInfo]] = {}
        self._all_providers: dict[str, DataProvider] = {}
        self._initialized = True

    def register(
        self,
        provider: DataProvider,
        data_type: DataType | None = None,
        priority: int | None = None,
    ) -> None:
        provider_name = provider.name
        self._all_providers[provider_name] = provider

        data_types = [data_type] if data_type is not None else provider.supported_data_types

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
        if provider_name not in self._all_providers:
            return False

        del self._all_providers[provider_name]

        for data_type in self._providers:
            self._providers[data_type] = [
                info for info in self._providers[data_type] if info.provider.name != provider_name
            ]

        return True

    def get_provider(
        self,
        data_type: DataType,
        check_availability: bool = True,
    ) -> DataProvider | None:
        if data_type not in self._providers:
            return None

        for info in self._providers[data_type]:
            if check_availability and not info.provider.is_available():
                continue
            return info.provider

        return None

    def get_all_providers(self, data_type: DataType) -> list[DataProvider]:
        if data_type not in self._providers:
            return []

        return [info.provider for info in self._providers[data_type]]

    def get_available_providers(self, data_type: DataType) -> list[DataProvider]:
        if data_type not in self._providers:
            return []

        return [info.provider for info in self._providers[data_type] if info.provider.is_available()]

    def fetch(
        self,
        data_type: DataType,
        symbol: str,
        fallback: bool = True,
        use_cache: bool = True,
        **kwargs,
    ) -> dict[str, Any] | None:
        from .cache import provider_cache as _provider_cache

        providers = self._providers.get(data_type, [])

        for info in providers:
            if not info.provider.is_available():
                continue

            provider_name = info.provider.name

            if use_cache:
                cached = _provider_cache.get(data_type.value, provider_name, symbol, **kwargs)
                if cached is not None:
                    result: dict[str, Any] | None = cached
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
                        _provider_cache.set(data_type.value, provider_name, symbol, result, **kwargs)

                    return result
            except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
                info.error_count += 1
                info.last_error_time = datetime.now()
                info.last_error_message = str(e)
                if not fallback:
                    raise
                continue

        return None

    def list_providers(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}

        for data_type, providers in self._providers.items():
            result[data_type.value] = [info.provider.name for info in providers]

        return result

    def check_availability(self) -> dict[str, dict[str, bool]]:
        result: dict[str, dict[str, bool]] = {}

        for data_type, providers in self._providers.items():
            result[data_type.value] = {info.provider.name: info.provider.is_available() for info in providers}

        return result

    def get_health(self, provider_name: str | None = None) -> dict[str, ProviderHealth]:
        result: dict[str, ProviderHealth] = {}

        provider_infos: dict[str, list[ProviderInfo]] = {}
        for providers in self._providers.values():
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

    def get_health_summary(self) -> dict[str, Any]:
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
        self._providers.clear()
        self._all_providers.clear()


provider_registry = ProviderRegistry()


def register_default_providers() -> None:
    from .akshare_provider import akshare_provider
    from .alpha_vantage_provider import alpha_vantage_provider
    from .ccxt_provider import ccxt_provider

    provider_registry.register(akshare_provider)
    provider_registry.register(alpha_vantage_provider)
    provider_registry.register(ccxt_provider)
