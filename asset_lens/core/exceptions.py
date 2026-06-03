"""
Custom exceptions for asset-lens.

asset-lens specific exceptions that extend investkit_utils base exceptions.
"""

from typing import Any

from investkit_utils.exceptions.base import (
    CacheError as _CacheError,
)
from investkit_utils.exceptions.base import (
    ConfigurationError as _ConfigurationError,
)
from investkit_utils.exceptions.base import (
    InvestKitError,
)
from investkit_utils.exceptions.base import (
    RateLimitError as _RateLimitError,
)
from investkit_utils.exceptions.base import (
    ValidationError as _ValidationError,
)


class AssetLensError(InvestKitError):
    """asset-lens 基础异常类"""

    default_message = "An error occurred in asset-lens"
    default_code = "ASSET_LENS_ERROR"
    default_status_code = 500

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        status_code: int | None = None,
        field: str | None = None,
        value: Any | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            field=field,
            value=value,
            details=details,
        )


class ConfigurationError(_ConfigurationError):
    """配置错误（扩展 investkit_utils 版本，增加 config_key）"""

    def __init__(self, message: str, config_key: str | None = None, **kwargs: Any):
        super().__init__(message=message, **kwargs)
        if config_key:
            self.details: dict[str, Any] = self.details or {}
            self.details["config_key"] = config_key
        self.config_key = config_key


class DataLoadError(AssetLensError):
    """数据加载错误"""

    default_message = "Data load error"
    default_code = "DATA_LOAD_ERROR"
    default_status_code = 422

    def __init__(self, message: str | None = None, file_path: str | None = None, **kwargs: Any):
        super().__init__(message=message, **kwargs)
        if file_path:
            self.details: dict[str, Any] = self.details or {}
            self.details["file_path"] = file_path
        self.file_path = file_path


class DataParseError(AssetLensError):
    """数据解析错误"""

    default_message = "Data parse error"
    default_code = "DATA_PARSE_ERROR"
    default_status_code = 422

    def __init__(
        self,
        message: str | None = None,
        row_number: int | None = None,
        raw_data: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(message=message, **kwargs)
        self.details: dict[str, Any] = self.details or {}
        if row_number is not None:
            self.details["row_number"] = row_number
        if raw_data:
            self.details["raw_data"] = raw_data[:100] if len(raw_data) > 100 else raw_data


class ValidationError(_ValidationError):
    """数据验证错误（扩展 investkit_utils 版本）"""

    def __init__(self, message: str | None = None, field: str | None = None, value: Any | None = None, **kwargs: Any):
        super().__init__(message=message, field=field, value=value, **kwargs)


class APIError(AssetLensError):
    """API 调用错误"""

    default_message = "API error"
    default_code = "API_ERROR"
    default_status_code = 502

    def __init__(
        self,
        message: str | None = None,
        api_name: str | None = None,
        status_code: int | None = None,
        **kwargs: Any,
    ):
        super().__init__(message=message, status_code=status_code, **kwargs)
        self.details: dict[str, Any] = self.details or {}
        if api_name:
            self.details["api_name"] = api_name
        self.api_name = api_name


class RateLimitError(_RateLimitError):
    """API 速率限制错误（扩展 investkit_utils 版本，增加 retry_after）"""

    def __init__(
        self, message: str | None = None, api_name: str | None = None, retry_after: int | None = None, **kwargs: Any
    ):
        super().__init__(message=message, **kwargs)
        self.details: dict[str, Any] = self.details or {}
        if api_name:
            self.details["api_name"] = api_name
        if retry_after:
            self.details["retry_after"] = retry_after
        self.retry_after = retry_after
        self.api_name = api_name


class CacheError(_CacheError):
    """缓存错误（扩展 investkit_utils 版本，增加 cache_key）"""

    def __init__(self, message: str | None = None, cache_key: str | None = None, **kwargs: Any):
        super().__init__(message=message, **kwargs)
        if cache_key:
            self.details: dict[str, Any] = self.details or {}
            self.details["cache_key"] = cache_key
        self.cache_key = cache_key


class CalculationError(AssetLensError):
    """计算错误"""

    default_message = "Calculation error"
    default_code = "CALCULATION_ERROR"
    default_status_code = 422

    def __init__(
        self,
        message: str | None = None,
        calculation_type: str | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        super().__init__(message=message, **kwargs)
        self.details: dict[str, Any] = self.details or {}
        if calculation_type:
            self.details["calculation_type"] = calculation_type
        if inputs:
            self.details["inputs"] = {k: str(v)[:50] for k, v in inputs.items()}


class InsufficientDataError(CalculationError):
    """数据不足错误"""

    default_message = "Insufficient data"
    default_code = "INSUFFICIENT_DATA"

    def __init__(self, message: str | None = None, required: int = 0, actual: int = 0, **kwargs: Any):
        super().__init__(message=message, calculation_type="insufficient_data", **kwargs)
        self.details["required"] = required
        self.details["actual"] = actual


class FileFormatError(DataParseError):
    """文件格式错误"""

    default_message = "File format error"
    default_code = "FILE_FORMAT_ERROR"

    def __init__(
        self,
        message: str | None = None,
        expected_format: str | None = None,
        actual_format: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(message=message, **kwargs)
        self.expected_format = expected_format
        self.actual_format = actual_format
