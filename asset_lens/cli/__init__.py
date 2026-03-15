"""
CLI module for asset-lens.
命令行接口模块 - 拆分后的模块化实现
"""

import click


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """asset-lens: Personal Asset Operating System"""
    from asset_lens.config import config
    config.ensure_directories()


# 导入并注册命令
from .core import register_core_commands
from .data import register_data_commands
from .analyze import register_analyze_commands
from .report import register_report_commands
from .strategy import register_strategy_commands
from .stock_pool import register_stock_pool_commands
from .monitor import register_monitor_commands

# 注册所有命令
register_core_commands(cli)
register_data_commands(cli)
register_analyze_commands(cli)
register_report_commands(cli)
register_strategy_commands(cli)
register_stock_pool_commands(cli)
register_monitor_commands(cli)


def create_cli() -> click.Group:
    """创建并配置 CLI 应用"""
    return cli


__all__ = [
    "cli",
    "create_cli",
]
