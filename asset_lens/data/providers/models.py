from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .protocol import DataProvider
from .types import DataType


@dataclass
class ProviderInfo:
    provider: DataProvider
    data_type: DataType
    priority: int
    is_available: bool
    error_count: int = 0
    success_count: int = 0
    total_response_time: float = 0.0
    last_success_time: datetime | None = None
    last_error_time: datetime | None = None
    last_error_message: str | None = None


@dataclass
class ProviderHealth:
    name: str
    provider_type: str
    is_available: bool
    total_requests: int
    success_count: int
    error_count: int
    success_rate: float
    avg_response_time: float
    last_success_time: datetime | None
    last_error_time: datetime | None
    last_error_message: str | None
    supported_data_types: list[str]

    def to_dict(self) -> dict[str, Any]:
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
