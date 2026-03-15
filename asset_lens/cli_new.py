"""
CLI (Command Line Interface) for asset-lens.
命令行接口模块 - 向后兼容入口
"""

import click

# 导入新的模块化 CLI
from .cli import cli as new_cli

# 创建向后兼容的 CLI
cli = new_cli

__all__ = ['cli']
