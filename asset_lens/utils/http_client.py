"""
HTTP Client Utilities.
HTTP 客户端工具函数

提供统一的 HTTP 请求处理：
- 自适应超时机制
- 智能重试策略
- 多数据源故障转移
- 错误处理
- 日志记录
- 跳过代理支持
"""

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

logger = logging.getLogger(__name__)


def get_session_without_proxy() -> requests.Session:
    """
    创建一个跳过代理的 requests Session

    Returns:
        配置为跳过代理的 Session 对象
    """
    session = requests.Session()
    session.trust_env = False
    session.proxies = {}
    return session


def get_request_session(skip_proxy: bool = False) -> requests.Session:
    """
    获取请求 Session

    Args:
        skip_proxy: 是否跳过代理

    Returns:
        Session 对象
    """
    if skip_proxy:
        return get_session_without_proxy()
    return requests.Session()


class ErrorType(Enum):
    """错误类型枚举"""
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    HTTP_ERROR = "http_error"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


@dataclass
class RequestStats:
    """请求统计信息"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_time: float = 0.0
    avg_response_time: float = 0.0
    last_error: str | None = None
    last_error_type: ErrorType | None = None


@dataclass
class AdaptiveTimeout:
    """自适应超时配置"""
    base_timeout: int = 10
    max_timeout: int = 60
    min_timeout: int = 5
    increase_factor: float = 1.5
    decrease_factor: float = 0.9
    current_timeout: float = field(default=10.0)
    success_streak: int = 0
    failure_streak: int = 0

    def on_success(self, response_time: float):
        """成功时调整超时"""
        self.success_streak += 1
        self.failure_streak = 0

        if self.success_streak >= 3:
            self.current_timeout = max(
                self.min_timeout,
                self.current_timeout * self.decrease_factor
            )
            self.success_streak = 0

    def on_failure(self, error_type: ErrorType):
        """失败时调整超时"""
        self.failure_streak += 1
        self.success_streak = 0

        if error_type == ErrorType.TIMEOUT:
            self.current_timeout = min(
                self.max_timeout,
                self.current_timeout * self.increase_factor
            )

    def get_timeout(self) -> int:
        """获取当前超时时间"""
        return int(self.current_timeout)


class HTTPClient:
    """HTTP 客户端（增强版）"""

    def __init__(
        self,
        default_timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_adaptive_timeout: bool = True,
        enable_jitter: bool = True,
        skip_proxy: bool = True,
    ):
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_adaptive_timeout = enable_adaptive_timeout
        self.enable_jitter = enable_jitter
        self.skip_proxy = skip_proxy

        self.adaptive_timeout = AdaptiveTimeout(base_timeout=default_timeout)
        self.stats = RequestStats()

        self._session = get_request_session(skip_proxy=skip_proxy)

        self._error_handlers: dict[ErrorType, Callable] = {
            ErrorType.TIMEOUT: self._handle_timeout,
            ErrorType.CONNECTION: self._handle_connection_error,
            ErrorType.HTTP_ERROR: self._handle_http_error,
            ErrorType.RATE_LIMIT: self._handle_rate_limit,
            ErrorType.SERVER_ERROR: self._handle_server_error,
        }

    def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
        **kwargs,
    ) -> requests.Response | None:
        return self._request(
            "GET",
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    def post(
        self,
        url: str,
        data: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
        **kwargs,
    ) -> requests.Response | None:
        return self._request(
            "POST",
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    def _classify_error(self, error: Exception) -> ErrorType:
        """分类错误类型"""
        if isinstance(error, Timeout):
            return ErrorType.TIMEOUT
        elif isinstance(error, ConnectionError):
            return ErrorType.CONNECTION
        elif isinstance(error, HTTPError):
            if hasattr(error, 'response') and error.response is not None:
                status_code = error.response.status_code
                if status_code == 429:
                    return ErrorType.RATE_LIMIT
                elif 500 <= status_code < 600:
                    return ErrorType.SERVER_ERROR
            return ErrorType.HTTP_ERROR
        else:
            return ErrorType.UNKNOWN

    def _handle_timeout(self, error: Exception, attempt: int) -> bool:
        """处理超时错误"""
        logger.warning(f"请求超时 (attempt {attempt + 1}/{self.max_retries})")
        return attempt < self.max_retries - 1

    def _handle_connection_error(self, error: Exception, attempt: int) -> bool:
        """处理连接错误"""
        logger.warning(f"连接错误 (attempt {attempt + 1}/{self.max_retries}): {error}")
        return attempt < self.max_retries - 1

    def _handle_http_error(self, error: Exception, attempt: int) -> bool:
        """处理 HTTP 错误"""
        logger.error(f"HTTP 错误: {error}")
        return False

    def _handle_rate_limit(self, error: Exception, attempt: int) -> bool:
        """处理限流错误"""
        wait_time = self._calculate_backoff(attempt, base_delay=5.0)
        logger.warning(f"触发限流，等待 {wait_time:.1f} 秒后重试")
        time.sleep(wait_time)
        return attempt < self.max_retries - 1

    def _handle_server_error(self, error: Exception, attempt: int) -> bool:
        """处理服务器错误"""
        logger.warning(f"服务器错误 (attempt {attempt + 1}/{self.max_retries})")
        return attempt < self.max_retries - 1

    def _calculate_backoff(self, attempt: int, base_delay: float | None = None) -> float:
        """计算退避时间（指数退避 + 抖动）"""
        base = base_delay or self.retry_delay
        backoff = base * (2 ** attempt)

        if self.enable_jitter:
            jitter = random.uniform(0, 0.3 * backoff)
            backoff += jitter

        return float(min(backoff, 30.0))

    def _get_timeout(self, timeout: int | None, attempt: int) -> int:
        """获取超时时间"""
        if timeout is not None:
            return timeout

        if self.enable_adaptive_timeout:
            base = self.adaptive_timeout.get_timeout()
            return base + attempt * 5

        return self.default_timeout + attempt * 5

    def _request(
        self,
        method: str,
        url: str,
        timeout: int | None = None,
        **kwargs,
    ) -> requests.Response | None:
        start_time = time.time()
        self.stats.total_requests += 1

        for attempt in range(self.max_retries):
            try:
                current_timeout = self._get_timeout(timeout, attempt)

                response = self._session.request(
                    method,
                    url,
                    timeout=current_timeout,
                    **kwargs,
                )

                response.raise_for_status()

                response_time = time.time() - start_time
                self.stats.successful_requests += 1
                self.stats.total_time += response_time
                self.stats.avg_response_time = (
                    self.stats.total_time / self.stats.successful_requests
                )

                if self.enable_adaptive_timeout:
                    self.adaptive_timeout.on_success(response_time)

                return response

            except Exception as e:
                error_type = self._classify_error(e)
                self.stats.last_error = str(e)
                self.stats.last_error_type = error_type

                if self.enable_adaptive_timeout:
                    self.adaptive_timeout.on_failure(error_type)

                handler = self._error_handlers.get(error_type)
                should_retry = handler(e, attempt) if handler else False

                if should_retry:
                    backoff = self._calculate_backoff(attempt)
                    time.sleep(backoff)
                else:
                    break

        self.stats.failed_requests += 1
        return None

    def get_json(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        response = self.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
        if response is not None:
            try:
                result = response.json()
                return result if isinstance(result, dict) else None
            except ValueError as e:
                logger.error(f"JSON 解析失败: {e}")
        return None

    def get_stats(self) -> RequestStats:
        """获取请求统计信息"""
        return self.stats

    def reset_stats(self):
        """重置统计信息"""
        self.stats = RequestStats()


class MultiSourceFetcher:
    """多数据源获取器"""

    def __init__(self, client: HTTPClient | None = None):
        self.client = client or HTTPClient()
        self._sources: dict[str, list[str]] = {}

    def register_sources(self, data_type: str, urls: list[str]):
        """注册数据源"""
        self._sources[data_type] = urls

    def fetch_with_fallback(
        self,
        data_type: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any] | None:
        """带故障转移的数据获取"""
        urls = self._sources.get(data_type, [])

        for i, url in enumerate(urls):
            logger.info(f"尝试数据源 {i + 1}/{len(urls)}: {url}")

            response = self.client.get_json(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )

            if response is not None:
                return response

            logger.warning(f"数据源 {url} 失败，尝试下一个...")

        logger.error(f"所有数据源都失败: {data_type}")
        return None


def with_retry(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    on_retry: Callable | None = None,
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        retry_delay: 重试延迟
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        delay = retry_delay * (2 ** attempt)
                        if on_retry:
                            on_retry(attempt, e)
                        time.sleep(delay)

            if last_error:
                raise last_error
            return None

        return wrapper
    return decorator


http_client = HTTPClient()
multi_source_fetcher = MultiSourceFetcher(http_client)


def safe_get(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = 10,
    max_retries: int = 3,
) -> requests.Response | None:
    client = HTTPClient(default_timeout=timeout, max_retries=max_retries)
    return client.get(url, params=params, headers=headers)


def safe_post(
    url: str,
    data: dict | None = None,
    json: dict | None = None,
    headers: dict | None = None,
    timeout: int = 10,
    max_retries: int = 3,
) -> requests.Response | None:
    client = HTTPClient(default_timeout=timeout, max_retries=max_retries)
    return client.post(url, data=data, json=json, headers=headers)


def get_json(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = 10,
) -> dict[str, Any] | None:
    return http_client.get_json(url, params=params, headers=headers, timeout=timeout)
