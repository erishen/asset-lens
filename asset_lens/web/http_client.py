"""
Async HTTP Client for Web Routes.
异步 HTTP 客户端 - 基于 aiohttp 的单例 session 管理

提供：
- 单例 aiohttp.ClientSession，避免重复创建/销毁
- async_get / async_post 便捷方法
- 与 FastAPI 生命周期集成的 session 管理
- 批量并发请求支持 (gather)
"""

import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

_session: aiohttp.ClientSession | None = None


def get_session() -> aiohttp.ClientSession:
    """获取或创建全局 aiohttp.ClientSession 单例"""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=10),
        )
    return _session


async def close_session():
    """关闭全局 session（应用关闭时调用）"""
    global _session
    if _session is not None and not _session.closed:
        await _session.close()
        _session = None


async def async_get(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> aiohttp.ClientResponse:
    """异步 GET 请求

    Args:
        url: 请求 URL
        params: 查询参数
        headers: 请求头
        timeout: 超时秒数（覆盖默认值）

    Returns:
        aiohttp.ClientResponse
    """
    session = get_session()
    kwargs: dict[str, Any] = {}
    if params:
        kwargs["params"] = params
    if headers:
        kwargs["headers"] = headers
    if timeout is not None:
        kwargs["timeout"] = aiohttp.ClientTimeout(total=timeout)
    return await session.get(url, **kwargs)


async def async_post(
    url: str,
    json: dict[str, Any] | None = None,
    data: Any = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> aiohttp.ClientResponse:
    """异步 POST 请求

    Args:
        url: 请求 URL
        json: JSON 请求体
        data: 表单数据
        headers: 请求头
        timeout: 超时秒数（覆盖默认值）

    Returns:
        aiohttp.ClientResponse
    """
    session = get_session()
    kwargs: dict[str, Any] = {}
    if json is not None:
        kwargs["json"] = json
    if data is not None:
        kwargs["data"] = data
    if headers:
        kwargs["headers"] = headers
    if timeout is not None:
        kwargs["timeout"] = aiohttp.ClientTimeout(total=timeout)
    return await session.post(url, **kwargs)


async def async_gather_get(
    requests_list: list[dict[str, Any]],
) -> list[aiohttp.ClientResponse | BaseException]:
    """批量并发 GET 请求

    Args:
        requests_list: 请求参数列表，每项包含 url, params, headers, timeout 等

    Returns:
        响应列表，失败项为 BaseException 实例
    """
    import asyncio

    async def _single(req: dict[str, Any]) -> aiohttp.ClientResponse:
        return await async_get(
            url=req["url"],
            params=req.get("params"),
            headers=req.get("headers"),
            timeout=req.get("timeout"),
        )

    tasks = [_single(r) for r in requests_list]
    return await asyncio.gather(*tasks, return_exceptions=True)
