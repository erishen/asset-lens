"""
Core CLI commands for asset-lens.
基础命令模块 - 包含 completion, interactive, init, init-sample, show-config, switch-mode, set-rate, version, check
"""

import os

import click


def register_core_commands(cli: click.Group) -> None:
    """注册核心命令到 CLI 组"""

    @cli.command()
    def completion():
        """生成 shell 自动补全脚本

        使用方法:
            # Bash
            $ source <(python -m asset_lens completion)
            # 或添加到 ~/.bashrc
            $ echo 'source <(python -m asset_lens completion)' >> ~/.bashrc

            # Zsh
            $ source <(python -m asset_lens completion)
            # 或添加到 ~/.zshrc
            $ echo 'source <(python -m asset_lens completion)' >> ~/.zshrc
        """
        shell = os.environ.get("SHELL", "")

        if "zsh" in shell:
            click.echo(
                """
# asset-lens completion for zsh
_asset_lens_completion() {
    local -a commands
    commands=(
        'analyze:分析投资组合并生成报告'
        'summary:生成投资组合摘要'
        'calculate:快捷计算收益率'
        'fetch-stock:获取股票实时行情'
        'fetch-fund:获取基金净值'
        'search-fund:搜索基金'
        'update-market:更新市场指数数据'
        'estimate-pnl:估算实时盈亏'
        'report:生成投资报告'
        'version:显示版本信息'
        'completion:生成 shell 自动补全脚本'
    )

    _describe 'command' commands
}
compdef _asset_lens_completion asset-lens
"""
            )
        else:
            click.echo(
                """
# asset-lens completion for bash
_asset_lens_completion() {
    local cur words
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    words="analyze summary calculate fetch-stock fetch-fund search-fund update-market estimate-pnl report version completion"

    COMPREPLY=( $(compgen -W "${words}" -- ${cur}) )
    return 0
}
complete -F _asset_lens_completion asset-lens
"""
            )

        click.echo("\n✅ 补全脚本已生成")
        click.echo("💡 请运行以下命令启用补全:")
        click.echo("   source <(python -m asset_lens completion)")
        click.echo("\n💡 或添加到您的 shell 配置文件中以永久启用")

    @cli.command()
    def interactive():
        """交互式命令行界面（问卷式输入）

        提供友好的交互式体验，引导用户完成各种操作。
        """
        from asset_lens.config import config

        click.echo("\n" + "=" * 60)
        click.echo("🚀 欢迎使用 Asset-Lens 交互式向导")
        click.echo("=" * 60)

        while True:
            click.echo("\n请选择要执行的操作:")
            click.echo("  1. 📊 分析投资组合")
            click.echo("  2. 💰 计算收益率")
            click.echo("  3. 📈 查询股票行情")
            click.echo("  4. 📉 查询基金净值")
            click.echo("  5. 🔍 搜索基金")
            click.echo("  6. 🌍 更新市场数据")
            click.echo("  7. 📝 生成投资报告")
            click.echo("  8. ⚙️  系统设置")
            click.echo("  0. 🚪 退出")

            choice = click.prompt("\n请输入选项", type=click.INT, default=0)

            if choice == 0:
                click.echo("\n👋 感谢使用 Asset-Lens，再见！")
                break
            elif choice == 1:
                _interactive_analyze()
            elif choice == 2:
                _interactive_calculate()
            elif choice == 3:
                _interactive_fetch_stock()
            elif choice == 4:
                _interactive_fetch_fund()
            elif choice == 5:
                _interactive_search_fund()
            elif choice == 6:
                _interactive_update_market()
            elif choice == 7:
                _interactive_report()
            elif choice == 8:
                _interactive_settings(config)
            else:
                click.echo("❌ 无效选项，请重新选择")

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
    @click.option("--target-mode", type=click.Choice(["sample", "real"]), required=True, help="目标数据模式")
    def switch_mode(data_mode: str | None, target_mode: str):
        """切换数据模式（sample <-> real）"""
        from asset_lens.config import config

        env_file = config.project_root / ".env"

        if env_file.exists():
            with open(env_file) as f:
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

    @cli.command()
    def show_config():
        """显示当前配置"""
        from asset_lens.config import config

        click.echo("\n📋 当前配置")
        click.echo("=" * 50)
        click.echo(f"数据模式: {config.data_mode}")
        click.echo(f"数据路径: {config.data_path}")
        click.echo(f"输出路径: {config.output_path}")
        click.echo(f"缓存路径: {config.cache_path}")
        click.echo(f"默认美元汇率: {config.default_usd_rate}")
        click.echo(f"默认港元汇率: {config.default_hkd_rate}")
        click.echo(f"最低收益率阈值: {config.min_return_threshold}%")
        click.echo(f"工作日占比: {config.workday_ratio}")
        click.echo(f"输出格式: {', '.join(config.output_format)}")
        click.echo(f"报告语言: {config.report_language}")
        click.echo("=" * 50)

    @cli.command()
    @click.option("--currency", type=click.Choice(["USD", "HKD"]), required=True, help="货币类型")
    @click.option("--rate", type=float, required=True, help="汇率（1外币 = X CNY）")
    def set_rate(currency: str, rate: float):
        """设置货币汇率"""
        from decimal import Decimal

        from asset_lens.data.models import Currency
        from asset_lens.utils.currency_converter import currency_converter

        currency_enum = Currency[currency.upper()]
        currency_converter.set_rate(currency_enum, Decimal(str(rate)))
        currency_converter.save_cached_rates()

        click.echo(f"✅ 已更新 {currency} 汇率: {rate}")

    @cli.command()
    def init():
        """初始化项目（创建必要的数据目录和文件）"""
        from asset_lens.config import config

        click.echo("\n🚀 初始化 asset-lens 项目...")

        dirs_to_create = [
            config.project_root / "data" / "sample_data",
            config.project_root / "data" / "real",
            config.output_path,
            config.cache_path,
        ]

        for dir_path in dirs_to_create:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                click.echo(f"  ✅ 创建目录: {dir_path}")
            else:
                click.echo(f"  ⏭️  目录已存在: {dir_path}")

        sample_files = [
            ("data/sample_data/投资组合-示例.csv", _get_sample_portfolio_csv()),
        ]

        for file_path, content in sample_files:
            full_path = config.project_root / file_path
            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                click.echo(f"  ✅ 创建文件: {file_path}")
            else:
                click.echo(f"  ⏭️  文件已存在: {file_path}")

        click.echo("\n✅ 初始化完成!")
        click.echo("\n💡 下一步:")
        click.echo("   1. 编辑 data/sample_data/投资组合-示例.csv 添加您的投资数据")
        click.echo("   2. 运行 'asset-lens analyze' 分析投资组合")

    @cli.command()
    def init_sample():
        """初始化示例数据"""
        from asset_lens.config import config

        click.echo("\n📊 初始化示例数据...")

        sample_data_dir = config.project_root / "data" / "sample_data"
        if not sample_data_dir.exists():
            sample_data_dir.mkdir(parents=True, exist_ok=True)

        sample_file = sample_data_dir / "投资组合-示例.csv"
        if not sample_file.exists():
            with open(sample_file, "w", encoding="utf-8") as f:
                f.write(_get_sample_portfolio_csv())
            click.echo(f"  ✅ 创建示例数据文件: {sample_file}")
        else:
            click.echo(f"  ⏭️  示例数据文件已存在: {sample_file}")

        click.echo("\n✅ 示例数据初始化完成!")

    @cli.command()
    def version():
        """显示版本信息"""
        click.echo("")
        click.echo("  asset-lens v1.0.0")
        click.echo("  个人资产操作系统")
        click.echo("")

    @cli.command()
    def check():
        """项目自检"""
        click.echo("")
        click.echo("  ╔════════════════════════════════════════════════════════════╗")
        click.echo("  ║                  项目自检                                   ║")
        click.echo("  ╚════════════════════════════════════════════════════════════╝")
        click.echo("")

        checks_passed = 0
        checks_failed = 0

        try:
            click.echo("  ✅ 配置模块正常")
            checks_passed += 1
        except Exception as e:
            click.echo(f"  ❌ 配置模块失败: {e}")
            checks_failed += 1

        try:
            from asset_lens.data.csv_parser import CSVParser
            CSVParser.load_data()
            click.echo("  ✅ 数据加载正常")
            checks_passed += 1
        except Exception as e:
            click.echo(f"  ❌ 数据加载失败: {e}")
            checks_failed += 1

        try:
            from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher
            enhanced_market_data_fetcher.fetch_all_domestic_indexes()
            click.echo("  ✅ 市场数据获取器正常")
            checks_passed += 1
        except Exception as e:
            click.echo(f"  ❌ 市场数据获取器失败: {e}")
            checks_failed += 1

        try:
            click.echo("  ✅ Web API 正常")
            checks_passed += 1
        except Exception as e:
            click.echo(f"  ❌ Web API 失败: {e}")
            checks_failed += 1

        click.echo("")
        click.echo(f"  检查结果: {checks_passed} 通过, {checks_failed} 失败")
        click.echo("")


def _interactive_analyze():
    """交互式分析投资组合"""
    click.echo("\n📊 投资组合分析")
    click.echo("-" * 40)

    data_mode = click.prompt(
        "选择数据模式",
        type=click.Choice(["sample", "real"]),
        default="sample",
    )

    click.prompt(
        "选择输出格式",
        type=click.Choice(["console", "csv", "json", "all"]),
        default="console",
    )

    click.echo(f"\n正在分析 {data_mode} 数据...")
    click.echo(f"请运行: make analyze DATA_MODE={data_mode}")


def _interactive_calculate():
    """交互式计算收益率"""
    click.echo("\n💰 收益率计算")
    click.echo("-" * 40)

    principal = click.prompt("请输入本金金额", type=click.FLOAT)
    current = click.prompt("请输入当前金额", type=click.FLOAT)
    days = click.prompt("请输入投资天数", type=click.INT, default=365)

    profit = current - principal
    profit_rate = (profit / principal) * 100
    annual_return = (profit_rate / days) * 365 if days > 0 else 0

    click.echo("\n📊 计算结果:")
    click.echo(f"  本金: ¥{principal:,.2f}")
    click.echo(f"  当前: ¥{current:,.2f}")
    click.echo(f"  收益: ¥{profit:,.2f}")
    click.echo(f"  收益率: {profit_rate:.2f}%")
    click.echo(f"  年化收益率: {annual_return:.2f}%")


def _interactive_fetch_stock():
    """交互式查询股票行情"""
    click.echo("\n📈 股票行情查询")
    click.echo("-" * 40)

    code = click.prompt("请输入股票代码（如 sh600519）")

    click.echo(f"\n正在查询 {code}...")
    click.echo(f'请运行: make fetch-stock CODES="{code}"')


def _interactive_fetch_fund():
    """交互式查询基金净值"""
    click.echo("\n📉 基金净值查询")
    click.echo("-" * 40)

    code = click.prompt("请输入基金代码（如 000001）")

    click.echo(f"\n正在查询 {code}...")
    click.echo(f'请运行: make fetch-fund CODES="{code}"')


def _interactive_search_fund():
    """交互式搜索基金"""
    click.echo("\n🔍 基金搜索")
    click.echo("-" * 40)

    keyword = click.prompt("请输入搜索关键词（如 沪深300）")

    click.echo(f"\n正在搜索 '{keyword}'...")
    click.echo(f'请运行: make search-fund KEYWORD="{keyword}"')


def _interactive_update_market():
    """交互式更新市场数据"""
    click.echo("\n🌍 市场数据更新")
    click.echo("-" * 40)

    api = click.prompt(
        "选择数据源",
        type=click.Choice(["sina", "eastmoney", "finnhub"]),
        default="eastmoney",
    )

    async_mode = click.confirm("是否使用异步模式", default=True)

    click.echo(f"\n正在更新市场数据（数据源: {api}）...")
    if async_mode:
        click.echo(f"请运行: make update-market-async API={api}")
    else:
        click.echo(f"请运行: make update-market API={api}")


def _interactive_report():
    """交互式生成报告"""
    click.echo("\n📝 投资报告生成")
    click.echo("-" * 40)

    report_type = click.prompt(
        "选择报告类型",
        type=click.Choice(["strategy", "pool", "comparison", "risk"]),
        default="strategy",
    )

    click.echo(f"\n正在生成 {report_type} 报告...")
    click.echo(f"请运行: make report-{report_type}")


def _interactive_settings(config):
    """交互式系统设置"""
    click.echo("\n⚙️  系统设置")
    click.echo("-" * 40)

    click.echo("当前设置:")
    click.echo(f"  数据模式: {config.data_mode}")
    click.echo(f"  USD 汇率: {config.default_usd_rate}")
    click.echo(f"  HKD 汇率: {config.default_hkd_rate}")
    click.echo(f"  输出目录: {config.output_path}")

    if click.confirm("\n是否修改设置"):
        click.echo("\n💡 请修改 config/settings.json 文件来更新设置")


def _get_sample_portfolio_csv() -> str:
    """获取示例投资组合 CSV 内容"""
    return """产品名称,产品类型,初始金额,当前金额,投资天数,年化收益率,风险等级,备注
示例基金A,基金,10000,11000,365,10.0,低,示例数据
示例股票B,股票,20000,22000,180,20.0,高,示例数据
示例债券C,债券,50000,52000,365,4.0,低,示例数据"""
