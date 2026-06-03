"""
Common warnings suppression utility.
通用警告抑制工具 - 统一的 warnings 配置入口

避免在多个文件中重复相同的 warnings.filterwarnings 调用。
"""

import warnings


def suppress_common_warnings() -> None:
    """抑制常见的无害警告

    包括:
    - Pandas 版本警告
    - 未关闭 socket 警告
    - ResourceWarning
    - DeprecationWarning
    """
    warnings.filterwarnings("ignore", message="Pandas requires version")
    warnings.filterwarnings("ignore", message=".*unclosed.*socket.*")
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
