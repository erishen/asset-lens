"""
Custom exceptions for asset-lens.
自定义异常类
"""

from typing import Any, Dict, Optional


class AssetLensError(Exception):
    """asset-lens 基础异常类"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details: Dict[str, Any] = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - 详情: {self.details}"
        return self.message


class ConfigurationError(AssetLensError):
    """配置错误"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        details: Optional[Dict[str, Any]] = {"config_key": config_key} if config_key else None
        super().__init__(message, details)


class DataLoadError(AssetLensError):
    """数据加载错误"""

    def __init__(self, message: str, file_path: Optional[str] = None):
        details: Optional[Dict[str, Any]] = {"file_path": file_path} if file_path else None
        super().__init__(message, details)


class DataParseError(AssetLensError):
    """数据解析错误"""

    def __init__(
        self, message: str, row_number: Optional[int] = None, raw_data: Optional[str] = None
    ):
        details: Dict[str, Any] = {}
        if row_number is not None:
            details["row_number"] = row_number
        if raw_data:
            details["raw_data"] = raw_data[:100] if len(raw_data) > 100 else raw_data
        super().__init__(message, details if details else None)


class ValidationError(AssetLensError):
    """数据验证错误"""

    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details: Dict[str, Any] = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)[:50]
        super().__init__(message, details if details else None)


class APIError(AssetLensError):
    """API 调用错误"""

    def __init__(
        self, message: str, api_name: Optional[str] = None, status_code: Optional[int] = None
    ):
        details: Dict[str, Any] = {}
        if api_name:
            details["api_name"] = api_name
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details if details else None)


class RateLimitError(APIError):
    """API 速率限制错误"""

    def __init__(
        self, message: str, api_name: Optional[str] = None, retry_after: Optional[int] = None
    ):
        super().__init__(message, api_name, 429)
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class CacheError(AssetLensError):
    """缓存错误"""

    def __init__(self, message: str, cache_key: Optional[str] = None):
        details: Optional[Dict[str, Any]] = {"cache_key": cache_key} if cache_key else None
        super().__init__(message, details)


class CalculationError(AssetLensError):
    """计算错误"""

    def __init__(
        self,
        message: str,
        calculation_type: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ):
        details: Dict[str, Any] = {}
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
        expected_format: Optional[str] = None,
        actual_format: Optional[str] = None,
    ):
        self.expected_format = expected_format
        self.actual_format = actual_format
        super().__init__(message)
