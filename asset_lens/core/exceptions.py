"""
Custom exceptions for asset-lens.
自定义异常类
"""

from typing import Any


class AssetLensError(Exception):
    """asset-lens 基础异常类"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - 详情: {self.details}"
        return self.message


class ConfigurationError(AssetLensError):
    """配置错误"""

    def __init__(self, message: str, config_key: str | None = None):
        details: dict[str, Any] | None = {"config_key": config_key} if config_key else None
        super().__init__(message, details)


class DataLoadError(AssetLensError):
    """数据加载错误"""

    def __init__(self, message: str, file_path: str | None = None):
        details: dict[str, Any] | None = {"file_path": file_path} if file_path else None
        super().__init__(message, details)


class DataParseError(AssetLensError):
    """数据解析错误"""

    def __init__(
        self, message: str, row_number: int | None = None, raw_data: str | None = None
    ):
        details: dict[str, Any] = {}
        if row_number is not None:
            details["row_number"] = row_number
        if raw_data:
            details["raw_data"] = raw_data[:100] if len(raw_data) > 100 else raw_data
        super().__init__(message, details if details else None)


class ValidationError(AssetLensError):
    """数据验证错误"""

    def __init__(self, message: str, field: str | None = None, value: Any | None = None):
        details: dict[str, Any] = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)[:50]
        super().__init__(message, details if details else None)


class APIError(AssetLensError):
    """API 调用错误"""

    def __init__(
        self, message: str, api_name: str | None = None, status_code: int | None = None
    ):
        details: dict[str, Any] = {}
        if api_name:
            details["api_name"] = api_name
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details if details else None)


class RateLimitError(APIError):
    """API 速率限制错误"""

    def __init__(
        self, message: str, api_name: str | None = None, retry_after: int | None = None
    ):
        super().__init__(message, api_name, 429)
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class CacheError(AssetLensError):
    """缓存错误"""

    def __init__(self, message: str, cache_key: str | None = None):
        details: dict[str, Any] | None = {"cache_key": cache_key} if cache_key else None
        super().__init__(message, details)


class CalculationError(AssetLensError):
    """计算错误"""

    def __init__(
        self,
        message: str,
        calculation_type: str | None = None,
        inputs: dict[str, Any] | None = None,
    ):
        details: dict[str, Any] = {}
        if calculation_type:
            details["calculation_type"] = calculation_type
        if inputs:
            details["inputs"] = {k: str(v)[:50] for k, v in inputs.items()}
        super().__init__(message, details if details else None)


class InsufficientDataError(CalculationError):
    """数据不足错误"""

    def __init__(self, message: str, required: int, actual: int):
        super().__init__(message, "insufficient_data", {"required": required, "actual": actual})
        self.details["required"] = required
        self.details["actual"] = actual


class FileFormatError(DataParseError):
    """文件格式错误"""

    def __init__(
        self,
        message: str,
        expected_format: str | None = None,
        actual_format: str | None = None,
    ):
        self.expected_format = expected_format
        self.actual_format = actual_format
        super().__init__(message)
