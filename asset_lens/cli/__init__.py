"""
Asset-Lens CLI - 命令行接口
模块化的命令行工具
"""

import click

from .data_commands import data_commands
from .analysis_commands import analysis_commands
from .strategy_commands import strategy_commands
from .report_commands import report_commands
from .monitor_commands import monitor_commands
from .system_commands import system_commands
from .interactive_commands import interactive_commands


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Asset-Lens: Personal Asset Operating System"""
    pass


cli.add_command(data_commands, name='data')
cli.add_command(analysis_commands, name='analyze')
cli.add_command(strategy_commands, name='strategy')
cli.add_command(report_commands, name='report')
cli.add_command(monitor_commands, name='monitor')
cli.add_command(system_commands, name='system')
cli.add_command(interactive_commands, name='interactive')


def _get_data_dir(data_mode: str):
    """获取数据目录"""
    from ..config import config
    if data_mode == "real":
        return config.get_latest_data_dir()
    else:
        return config.project_root / "data" / "sample_data"


from ..data.csv_parser import CSVParser
from ..utils.currency_converter import currency_converter


__all__ = ['cli', 'CSVParser', 'currency_converter', '_get_data_dir']
