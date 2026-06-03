"""
Analyze CLI commands for asset-lens.
分析命令模块 - 聚合入口
"""

import click

from asset_lens.cli_modules.cli.analyze_annual import register_annual_return_command
from asset_lens.cli_modules.cli.analyze_core import (
    register_analyze_commands as register_core_commands,
)
from asset_lens.cli_modules.cli.analyze_time import register_analyze_time_commands


def register_analyze_commands(cli: click.Group) -> None:
    """注册分析命令到 CLI 组"""
    register_core_commands(cli)
    register_annual_return_command(cli)
    register_analyze_time_commands(cli)
