"""
CLI module for asset-lens.
命令行接口模块 - 拆分后的模块化实现
"""

import click

from .analyze import register_analyze_commands
from .compare import register_compare_commands
from .core import register_core_commands
from .data import register_data_commands
from .db import db as db_group
from .ml import ml as ml_group
from .monitor import register_monitor_commands
from .predict import register_predict_commands
from .report import register_report_commands
from .stock_pool import register_stock_pool_commands
from .strategy import register_strategy_commands


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """asset-lens: Personal Asset Operating System"""
    from asset_lens.config import config

    config.ensure_directories()


# 注册所有命令
register_core_commands(cli)
register_data_commands(cli)
register_analyze_commands(cli)
register_report_commands(cli)
register_predict_commands(cli)
register_compare_commands(cli)
register_strategy_commands(cli)
register_stock_pool_commands(cli)
register_monitor_commands(cli)

# 注册 ML 命令组
cli.add_command(ml_group, name="ml")

# 注册 DB 命令组
cli.add_command(db_group, name="db")


def create_cli() -> click.Group:
    """创建并配置 CLI 应用"""
    return cli


__all__ = [
    "cli",
    "create_cli",
]
