"""
API Response Models.
API 响应模型 - 统一响应格式

响应格式:
    成功响应:
    {
        "success": true,
        "data": {...},
        "error": null,
        "timestamp": "2024-01-01 12:00:00"
    }

    错误响应:
    {
        "success": false,
        "data": null,
        "error": {
            "code": "ERROR_CODE",
            "message": "错误描述"
        },
        "timestamp": "2024-01-01 12:00:00"
    }

错误码说明:
    HTTP 4xx 客户端错误:
    - BAD_REQUEST (400): 请求参数错误
    - UNAUTHORIZED (401): 未授权访问，缺少或无效的 API Key
    - FORBIDDEN (403): 禁止访问，权限不足
    - NOT_FOUND (404): 资源不存在
    - VALIDATION_ERROR (422): 数据验证失败
    - RATE_LIMIT_EXCEEDED (429): 请求频率超限

    HTTP 5xx 服务端错误:
    - INTERNAL_ERROR (500): 内部服务器错误
    - DATA_SOURCE_ERROR (502): 数据源获取失败
    - SERVICE_UNAVAILABLE (503): 服务暂不可用

    业务错误:
    - STOCK_NOT_FOUND (404): 股票代码不存在
    - FUND_NOT_FOUND (404): 基金代码不存在
    - ANALYSIS_ERROR (500): 分析计算失败
"""

from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel


class APIResponse(BaseModel):
    """统一 API 响应格式"""

    success: bool
    data: Any | None = None
    error: dict[str, Any] | None = None
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {"success": True, "data": {"key": "value"}, "error": None, "timestamp": "2024-01-01 12:00:00"}
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""

    success: bool = False
    data: None = None
    error: dict[str, Any]
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def from_exception(cls, exc: Exception, error_code: str = "INTERNAL_ERROR") -> "ErrorResponse":
        return cls(
            error={
                "code": error_code,
                "message": str(exc),
                "type": type(exc).__name__,
            }
        )


class SuccessResponse(BaseModel):
    """成功响应模型"""

    success: bool = True
    data: Any
    error: None = None
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def create(cls, data: Any) -> "SuccessResponse":
        return cls(data=data)


ERROR_CODES = {
    "INTERNAL_ERROR": {"code": "INTERNAL_ERROR", "message": "内部服务器错误", "status_code": 500},
    "NOT_FOUND": {"code": "NOT_FOUND", "message": "资源不存在", "status_code": 404},
    "BAD_REQUEST": {"code": "BAD_REQUEST", "message": "请求参数错误", "status_code": 400},
    "UNAUTHORIZED": {"code": "UNAUTHORIZED", "message": "未授权访问", "status_code": 401},
    "FORBIDDEN": {"code": "FORBIDDEN", "message": "禁止访问", "status_code": 403},
    "VALIDATION_ERROR": {"code": "VALIDATION_ERROR", "message": "数据验证失败", "status_code": 422},
    "RATE_LIMIT_EXCEEDED": {"code": "RATE_LIMIT_EXCEEDED", "message": "请求频率超限", "status_code": 429},
    "SERVICE_UNAVAILABLE": {"code": "SERVICE_UNAVAILABLE", "message": "服务暂不可用", "status_code": 503},
    "STOCK_NOT_FOUND": {"code": "STOCK_NOT_FOUND", "message": "股票代码不存在", "status_code": 404},
    "FUND_NOT_FOUND": {"code": "FUND_NOT_FOUND", "message": "基金代码不存在", "status_code": 404},
    "DATA_SOURCE_ERROR": {"code": "DATA_SOURCE_ERROR", "message": "数据源获取失败", "status_code": 502},
    "ANALYSIS_ERROR": {"code": "ANALYSIS_ERROR", "message": "分析计算失败", "status_code": 500},
}


def create_error_response(error_code: str, detail: str | None = None) -> dict:
    """创建错误响应"""
    error_info = ERROR_CODES.get(error_code, ERROR_CODES["INTERNAL_ERROR"])
    return {
        "success": False,
        "data": None,
        "error": {
            "code": error_info["code"],
            "message": detail or error_info["message"],
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def create_success_response(data: Any) -> dict:
    """创建成功响应"""
    return {
        "success": True,
        "data": data,
        "error": None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
