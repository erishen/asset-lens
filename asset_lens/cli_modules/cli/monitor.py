"""
Monitor CLI commands for asset-lens.
监控命令模块 - 包含 run-daily-tasks, task-status, market-environment, personal-data
"""


import click


def register_monitor_commands(cli: click.Group) -> None:
    """注册监控命令到 CLI 组"""

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--skip-report", is_flag=True, help="跳过报告生成")
    def run_daily_tasks(data_mode: str | None, skip_report: bool):
        """运行每日任务（更新数据 + 生成报告）"""
        from datetime import datetime

        from asset_lens.cli_modules.cli.helpers import setup_data_mode

        setup_data_mode(data_mode)

        start_time = datetime.now()
        click.echo("\n📊 运行每日任务")
        click.echo("=" * 60)
        click.echo(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        results = {"success": 0, "failed": 0, "skipped": 0}

        click.echo("\n1️⃣ 更新市场指数数据...")
        try:
            from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher

            domestic = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
            foreign = enhanced_market_data_fetcher.fetch_all_foreign_indexes()
            domestic_data = (domestic or {}).get("指数数据", {})
            foreign_data = (foreign or {}).get("指数数据", {})
            domestic_ok = bool(domestic_data)
            foreign_ok = bool(foreign_data)
            if domestic_ok or foreign_ok:
                click.echo(f"   ✅ 市场指数数据更新成功 (国内: {len(domestic_data)}个, 海外: {len(foreign_data)}个)")
                results["success"] += 1
            else:
                click.echo("   ⚠️ 市场指数数据更新失败")
                results["failed"] += 1
        except Exception as e:
            click.echo(f"   ❌ 市场指数数据更新失败: {e}")
            results["failed"] += 1

        click.echo("\n2️⃣ 更新基金净值数据...")
        try:
            from asset_lens.data.fund_fetcher import fetch_portfolio_fund_quotes

            result = fetch_portfolio_fund_quotes()
            if result and result.get("data"):
                click.echo(f"   ✅ 成功更新 {len(result['data'])} 只基金净值")
                results["success"] += 1
            else:
                click.echo("   ⚠️ 未获取到基金净值数据")
                results["skipped"] += 1
        except Exception as e:
            click.echo(f"   ❌ 基金净值更新失败: {e}")
            results["failed"] += 1

        click.echo("\n3️⃣ 更新股票行情数据...")
        try:
            from asset_lens.data.stock_fetcher import stock_fetcher

            stock_codes_map = stock_fetcher._load_stock_codes_config()
            stock_codes = list(set(stock_codes_map.values()))
            if stock_codes:
                result = stock_fetcher.fetch_multiple_stocks(stock_codes)
                if result and result.get("data"):
                    click.echo(f"   ✅ 成功更新 {len(result['data'])} 只股票行情")
                    results["success"] += 1
                else:
                    click.echo("   ⚠️ 未获取到股票行情数据")
                    results["skipped"] += 1
            else:
                click.echo("   ℹ️ 没有配置股票代码，跳过")
                results["skipped"] += 1
        except Exception as e:
            click.echo(f"   ❌ 股票行情更新失败: {e}")
            results["failed"] += 1

        if not skip_report:
            click.echo("\n4️⃣ 生成投资报告...")
            try:
                from asset_lens.cli_modules.cli.helpers import get_hkd_rate, get_usd_rate, load_products
                from asset_lens.config import config
                from asset_lens.data.models import Portfolio
                from asset_lens.report.analyzer import report_generator

                products = load_products()
                usd_rate = get_usd_rate()
                hkd_rate = get_hkd_rate()
                portfolio = Portfolio(products=products, usd_rate=usd_rate, hkd_rate=hkd_rate)
                report = report_generator.generate_analysis_report(portfolio)
                report_generator.print_console_report(report)
                report_generator.save_json_report(report, config.output_path)
                click.echo("   ✅ 投资报告生成成功")
                results["success"] += 1
            except Exception as e:
                click.echo(f"   ❌ 报告生成失败: {e}")
                results["failed"] += 1
        else:
            click.echo("\n4️⃣ 生成投资报告... (已跳过)")
            results["skipped"] += 1

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        click.echo("\n" + "=" * 60)
        click.echo("📊 任务执行汇总:")
        click.echo(f"   ✅ 成功: {results['success']}")
        click.echo(f"   ❌ 失败: {results['failed']}")
        click.echo(f"   ⏭️ 跳过: {results['skipped']}")
        click.echo(f"   ⏱️ 耗时: {duration:.1f} 秒")
        click.echo(f"   🕐 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if results["failed"] == 0:
            click.echo("\n✅ 每日任务完成！")
        else:
            click.echo("\n⚠️ 部分任务失败，请检查日志")

    @cli.command()
    def task_status():
        """显示任务状态（缓存数据时效性）"""
        from datetime import datetime

        from asset_lens.config import config

        click.echo("\n📊 任务状态（数据时效性）")
        click.echo("=" * 60)

        cache_dir = config.cache_path

        cache_files = [
            ("国内指数", "market_index_domestic.json"),
            ("海外指数", "market_index_foreign.json"),
            ("基金净值", "fund_quotes.json"),
            ("股票行情", "stock_quotes.json"),
            ("市场股票", "market_stocks.json"),
        ]

        click.echo("\n📁 缓存文件状态:")
        all_fresh = True

        for name, filename in cache_files:
            filepath = cache_dir / filename
            if filepath.exists():
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                age_hours = (datetime.now() - mtime).total_seconds() / 3600
                age_str = f"{age_hours:.1f}小时前" if age_hours < 24 else f"{age_hours/24:.1f}天前"

                if age_hours < 1:
                    status = "✅ 新鲜"
                elif age_hours < 24:
                    status = "⚠️ 较旧"
                    all_fresh = False
                else:
                    status = "❌ 过期"
                    all_fresh = False

                click.echo(f"  {name}: {status} (更新于 {age_str})")
            else:
                click.echo(f"  {name}: ❌ 不存在")
                all_fresh = False

        click.echo("\n📈 建议操作:")
        if all_fresh:
            click.echo("  ✅ 数据状态良好，无需更新")
        else:
            click.echo("  💡 运行 'asset-lens run-daily-tasks' 更新数据")
            click.echo("  💡 或运行 'make update-all-data' 一键更新")

    @cli.command()
    @click.option("--report-type", type=click.Choice(["daily", "weekly"]), default="daily", help="报告类型")
    def market_environment(report_type: str):
        """显示市场环境"""
        from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher

        click.echo("\n📊 市场环境分析")
        click.echo("=" * 60)
        click.echo(f"报告类型: {report_type}")

        try:
            domestic = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
            foreign = enhanced_market_data_fetcher.fetch_all_foreign_indexes()

            click.echo("\n📈 国内指数:")
            domestic_data = (domestic or {}).get("指数数据", {})
            if domestic_data:
                for name, data in list(domestic_data.items())[:10]:
                    change = data.get("涨跌幅", 0)
                    if isinstance(change, str):
                        change = float(change.replace("%", ""))
                    change_str = f"{change:+.2f}%"
                    if change > 0:
                        click.echo(f"  📈 {name}: {change_str}")
                    elif change < 0:
                        click.echo(f"  📉 {name}: {change_str}")
                    else:
                        click.echo(f"  ➡️ {name}: {change_str}")
            else:
                click.echo("  ⚠️ 无国内指数数据")

            click.echo("\n🌍 海外指数:")
            foreign_data = (foreign or {}).get("指数数据", {})
            if foreign_data:
                for name, data in list(foreign_data.items())[:5]:
                    change = data.get("涨跌幅", 0)
                    if isinstance(change, str):
                        change = float(change.replace("%", ""))
                    change_str = f"{change:+.2f}%"
                    click.echo(f"  {name}: {change_str}")
            else:
                click.echo("  ⚠️ 无海外指数数据")

            click.echo("\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def personal_data(data_mode: str | None):
        """管理个人数据"""
        from asset_lens.cli_modules.cli.helpers import setup_data_mode
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser

        setup_data_mode(data_mode)

        click.echo("\n📊 个人数据管理")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()

            click.echo("\n📈 数据概览:")
            click.echo(f"  数据目录: {config.data_path}")
            click.echo(f"  产品数量: {len(products)}")
            click.echo(f"  缓存路径: {config.cache_path}")

            if products:
                total_value = sum(p.current_amount or 0 for p in products)
                click.echo(f"  总资产: ¥{total_value:,.2f}")

                platforms = {}
                for p in products:
                    platform = p.platform or "未知"
                    platforms[platform] = platforms.get(platform, 0) + 1

                click.echo("\n📊 平台分布:")
                for platform, count in sorted(platforms.items(), key=lambda x: -x[1]):
                    click.echo(f"  {platform}: {count} 个产品")

            click.echo("\n✅ 数据状态正常！")

        except Exception as e:
            click.echo(f"❌ 获取数据失败: {e}", err=True)
