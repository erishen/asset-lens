"""
System Commands - 系统相关命令
"""

import click
from pathlib import Path
from typing import Optional

from ..config import config


@click.group(name='system')
def system_commands():
    """系统命令"""
    pass


@system_commands.command('init')
@click.option('--force/--no-force', default=False, help='强制重新初始化')
def init_system(force: bool):
    """初始化系统
    
    示例:
        asset-lens system init
    """
    try:
        config.ensure_directories()
        click.echo("✅ 系统初始化完成")
    except Exception as e:
        click.echo(f"❌ 初始化失败: {e}")


@system_commands.command('show-config')
def show_config():
    """显示配置
    
    示例:
        asset-lens system show-config
    """
    try:
        click.echo("📋 当前配置:")
        click.echo(f"  项目根目录: {config.project_root}")
        click.echo(f"  数据模式: {config.data_mode}")
        click.echo(f"  缓存目录: {config.cache_path}")
        click.echo(f"  日志级别: INFO")
    except Exception as e:
        click.echo(f"❌ 获取失败: {e}")


@system_commands.command('check')
def check_system():
    """检查系统状态
    
    示例:
        asset-lens system check
    """
    try:
        click.echo("🔍 系统检查:")
        
        # 检查目录
        if config.project_root.exists():
            click.echo("  ✅ 项目目录存在")
        else:
            click.echo("  ❌ 项目目录不存在")
        
        # 检查缓存目录
        cache_path = config.project_root / "cache"
        if cache_path.exists():
            click.echo("  ✅ 缓存目录存在")
        else:
            click.echo("  ⚠️  缓存目录不存在")
        
        # 检查数据目录
        data_path = config.project_root / "data"
        if data_path.exists():
            click.echo("  ✅ 数据目录存在")
        else:
            click.echo("  ⚠️  数据目录不存在")
        
        click.echo("\n✅ 系统检查完成")
    except Exception as e:
        click.echo(f"❌ 检查失败: {e}")


@system_commands.command('completion')
def generate_completion():
    """生成 shell 自动补全脚本
    
    示例:
        asset-lens system completion
    """
    try:
        # 生成 Bash 自动补全脚本
        script = """
# Asset-Lens 自动补全脚本
_asset_lens_completion() {
    local cur prev words cword
    _init_completion || return
    
    if [[ ${cword} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "data analyze strategy report monitor system" -- "${cur}"))
    fi
}

complete -F _asset_lens_completion asset-lens
"""
        click.echo(script)
        click.echo("\n# 使用方法:")
        click.echo("# source <(asset-lens system completion)")
    except Exception as e:
        click.echo(f"❌ 生成失败: {e}")


@system_commands.command('version')
def show_version():
    """显示版本信息
    
    示例:
        asset-lens system version
    """
    click.echo("Asset-Lens v1.0.0")
    click.echo("Personal Asset Operating System")


@system_commands.command('switch-mode')
@click.option('--data-mode', type=click.Choice(['sample', 'real']), help='当前数据模式')
@click.option('--target-mode', type=click.Choice(['sample', 'real']), required=True, help='目标数据模式')
def switch_mode(data_mode: Optional[str], target_mode: str):
    """切换数据模式
    
    示例:
        asset-lens system switch-mode --target-mode real
    """
    env_file = config.project_root / ".env"
    
    if env_file.exists():
        with open(env_file, "r") as f:
            lines = f.readlines()
        
        with open(env_file, "w") as f:
            for line in lines:
                if line.startswith("DATA_MODE="):
                    f.write(f"DATA_MODE={target_mode}\n")
                else:
                    f.write(line)
        
        click.echo(f"✅ 数据模式已切换为: {target_mode}")
    else:
        with open(env_file, "w") as f:
            f.write(f"DATA_MODE={target_mode}\n")
        
        click.echo(f"✅ 创建 .env 文件并设置数据模式为: {target_mode}")


@system_commands.command('set-rate')
@click.option('--currency', type=click.Choice(['USD', 'HKD']), required=True, help='货币类型')
@click.option('--rate', type=float, required=True, help='汇率（1外币 = X CNY）')
def set_rate(currency: str, rate: float):
    """设置货币汇率
    
    示例:
        asset-lens system set-rate --currency USD --rate 7.2
    """
    from decimal import Decimal
    from ..data.models import Currency
    from ..utils.currency_converter import currency_converter
    
    currency_enum = Currency[currency.upper()]
    currency_converter.set_rate(currency_enum, Decimal(str(rate)))
    currency_converter.save_cached_rates()
    
    click.echo(f"✅ 已更新 {currency} 汇率: {rate}")
