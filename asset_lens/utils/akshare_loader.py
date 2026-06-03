"""
AkShare lazy-loading utility.
AkShare 延迟加载工具 - 统一的 AkShare 模块加载入口

避免在多个 fetcher 文件中重复实现延迟加载逻辑。
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_AKSHARE_INSTANCE: Any | None = None


def get_akshare(raise_on_missing: bool = True) -> Any:
    """延迟加载 AkShare 模块

    Args:
        raise_on_missing: 如果 AkShare 未安装，是否抛出 ImportError。
                         设为 False 时，未安装返回 None。

    Returns:
        akshare 模块对象

    Raises:
        ImportError: 当 raise_on_missing=True 且 AkShare 未安装时
    """
    global _AKSHARE_INSTANCE

    if _AKSHARE_INSTANCE is not None:
        return _AKSHARE_INSTANCE

    try:
        import akshare as ak

        _AKSHARE_INSTANCE = ak
        return ak
    except ImportError:
        if raise_on_missing:
            raise ImportError(
                "请先安装 AkShare: pip install akshare\n"
                "AkShare 是一个开源免费的金融数据接口，无需注册\n"
                "GitHub: https://github.com/akfamily/akshare"
            ) from None
        logger.warning("AkShare 未安装")
        return None


def reset_akshare() -> None:
    """重置 AkShare 实例（主要用于测试）"""
    global _AKSHARE_INSTANCE
    _AKSHARE_INSTANCE = None
