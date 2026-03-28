"""
CLI entry point for asset-lens.
CLI 入口文件 - 导入模块化命令
"""

from .cli_modules.cli import cli, create_cli

__all__ = ["cli", "create_cli"]
