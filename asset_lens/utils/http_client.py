"""
HTTP Client Utilities.
HTTP 客户端工具函数

提供统一的 HTTP 请求处理：
- 自动重试机制
- 超时处理
- 错误处理
- 日志记录
"""

import time
import logging
from typing import Any, Dict, Optional

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP 客户端"""

    def __init__(
        self,
        default_timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> Optional[requests.Response]:
        """
        GET 请求

        Args:
            url: 请求 URL
            params: 查询参数
            headers: 请求头
            timeout: 超时时间（秒）
            **kwargs: 其他参数

        Returns:
            Response 对象或 None
        """
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
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> Optional[requests.Response]:
        """
        POST 请求

        Args:
            url: 请求 URL
            data: 表单数据
            json: JSON 数据
            headers: 请求头
            timeout: 超时时间（秒）
            **kwargs: 其他参数

        Returns:
            Response 对象或 None
        """
        return self._request(
            "POST",
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    def _request(
        self,
        method: str,
        url: str,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> Optional[requests.Response]:
        """
        执行请求（带重试机制）

        Args:
            method: 请求方法
            url: 请求 URL
            timeout: 超时时间
            **kwargs: 其他参数

        Returns:
            Response 对象或 None
        """
        timeout = timeout or self.default_timeout

        for attempt in range(self.max_retries):
            try:
                # 递增超时时间
                current_timeout = timeout + attempt * 5

                response = requests.request(
                    method,
                    url,
                    timeout=current_timeout,
                    **kwargs,
                )

                response.raise_for_status()
                return response

            except Timeout:
                logger.warning(
                    f"请求超时 {url} (attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue

            except ConnectionError as e:
                logger.warning(f"连接错误 {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue

            except RequestException as e:
                logger.error(f"请求失败 {url}: {e}")
                break

        return None

    def get_json(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        GET 请求并返回 JSON

        Args:
            url: 请求 URL
            params: 查询参数
            headers: 请求头
            timeout: 超时时间
            **kwargs: 其他参数

        Returns:
            JSON 数据或 None
        """
        response = self.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
        if response is not None:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"JSON 解析失败: {e}")
        return None


# 全局 HTTP 客户端实例
http_client = HTTPClient()


def safe_get(
    url: str,
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 10,
    max_retries: int = 3,
) -> Optional[requests.Response]:
    """
    安全的 GET 请求

    Args:
        url: 请求 URL
        params: 查询参数
        headers: 请求头
        timeout: 超时时间
        max_retries: 最大重试次数

    Returns:
        Response 对象或 None
    """
    client = HTTPClient(default_timeout=timeout, max_retries=max_retries)
    return client.get(url, params=params, headers=headers)


def safe_post(
    url: str,
    data: Optional[Dict] = None,
    json: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 10,
    max_retries: int = 3,
) -> Optional[requests.Response]:
    """
    安全的 POST 请求

    Args:
        url: 请求 URL
        data: 表单数据
        json: JSON 数据
        headers: 请求头
        timeout: 超时时间
        max_retries: 最大重试次数

    Returns:
        Response 对象或 None
    """
    client = HTTPClient(default_timeout=timeout, max_retries=max_retries)
    return client.post(url, data=data, json=json, headers=headers)


def get_json(
    url: str,
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    GET 请求并返回 JSON

    Args:
        url: 请求 URL
        params: 查询参数
        headers: 请求头
        timeout: 超时时间

    Returns:
        JSON 数据或 None
    """
    return http_client.get_json(url, params=params, headers=headers, timeout=timeout)
