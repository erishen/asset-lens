"""
Pytest configuration and fixtures.
"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def disable_proxy():
    """
    禁用代理设置

    测试时禁用系统代理，避免代理不可用导致测试失败
    """
    original_http_proxy = os.environ.get("HTTP_PROXY")
    original_https_proxy = os.environ.get("HTTPS_PROXY")
    original_http_proxy_lower = os.environ.get("http_proxy")
    original_https_proxy_lower = os.environ.get("https_proxy")
    original_all_proxy = os.environ.get("ALL_PROXY")
    original_all_proxy_lower = os.environ.get("all_proxy")

    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    os.environ.pop("http_proxy", None)
    os.environ.pop("https_proxy", None)
    os.environ.pop("ALL_PROXY", None)
    os.environ.pop("all_proxy", None)

    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"

    yield

    if original_http_proxy is not None:
        os.environ["HTTP_PROXY"] = original_http_proxy
    if original_https_proxy is not None:
        os.environ["HTTPS_PROXY"] = original_https_proxy
    if original_http_proxy_lower is not None:
        os.environ["http_proxy"] = original_http_proxy_lower
    if original_https_proxy_lower is not None:
        os.environ["https_proxy"] = original_https_proxy_lower
    if original_all_proxy is not None:
        os.environ["ALL_PROXY"] = original_all_proxy
    if original_all_proxy_lower is not None:
        os.environ["all_proxy"] = original_all_proxy_lower

    os.environ.pop("NO_PROXY", None)
    os.environ.pop("no_proxy", None)
