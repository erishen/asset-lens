import click


def register_ml_sector_commands(ml_group: click.Group) -> None:
    @ml_group.command(name="predict-sectors")
    def predict_sectors():
        from rich.console import Console
        from rich.table import Table

        from asset_lens.ml.sector_ml import sector_ml_predictor

        console = Console()
        console.print("🚀 [bold green]Running ML Sector Prediction...[/bold green]")

        predictions = sector_ml_predictor.predict_all_sectors()

        if not predictions:
            console.print("⚠️ Could not generate sector predictions.", style="yellow")
            return

        table = Table(title="板块走势ML预测", show_header=True, header_style="bold magenta")
        table.add_column("板块名称", style="cyan")
        table.add_column("预测方向", style="dim")
        table.add_column("预测涨幅 (%)", justify="right")
        table.add_column("置信度", justify="right")
        table.add_column("建议")

        for pred in predictions:
            direction_str = (
                "📈 看涨" if pred.predicted_direction == 1 else ("📉 看跌" if pred.predicted_direction == 0 else "횡보")
            )
            color = "green" if pred.predicted_direction == 1 else ("red" if pred.predicted_direction == 0 else "yellow")

            table.add_row(
                pred.sector_name,
                f"[{color}]{direction_str}[/{color}]",
                f"{pred.predicted_change:.2f}",
                f"{pred.confidence:.2f}",
                pred.recommendation,
            )

        console.print(table)

        console.print("\n[bold]板块轮动建议:[/bold]")
        suggestion = sector_ml_predictor.get_sector_rotation_suggestion(predictions)
        console.print(f"  [green]建议关注: {', '.join(suggestion['strong_sectors'])}[/green]")
        console.print(f"  [red]建议回避: {', '.join(suggestion['weak_sectors'])}[/red]")
        console.print(f"  [bold cyan]轮动信号:[/bold cyan] {suggestion['suggestion']}")

    @ml_group.command()
    def sector():
        from rich.console import Console
        from rich.table import Table

        from asset_lens.data.market_stock_fetcher import MarketStockFetcher
        from asset_lens.ml.sector_ml import sector_ml_predictor
        from asset_lens.ml.sector_rotation import sector_analyzer

        console = Console()

        console.print("\n📊 板块轮动分析 (ML增强)")
        console.print("=" * 60)

        fetcher = MarketStockFetcher()
        stocks = fetcher.get_cached_market_stocks()

        console.print("\n📊 数据集统计")
        console.print("=" * 60)
        console.print("  数据源: 市场股票缓存")
        console.print(f"  总股票数: {len(stocks):,}")
        if stocks:
            up_count = len([s for s in stocks if s.get("change_percent", 0) > 0])
            down_count = len([s for s in stocks if s.get("change_percent", 0) < 0])
            console.print(f"  上涨股票: {up_count} ({up_count / len(stocks):.1%})")
            console.print(f"  下跌股票: {down_count} ({down_count / len(stocks):.1%})")

        result = sector_analyzer.analyze()

        console.print(f"\n  市场状态: [bold]{result.market_condition.upper()}[/bold]")
        console.print(f"  轮动信号: {result.rotation_signal}")

        sector_stats = sector_analyzer._calculate_sector_stats(sector_analyzer.__dict__.get("_stocks", []))

        if not sector_stats:
            sector_stats = sector_analyzer._calculate_sector_stats(stocks)

        ml_predictions = sector_ml_predictor.predict_all_sectors()

        rotation = sector_ml_predictor.get_sector_rotation_suggestion(ml_predictions)

        console.print("\n  🤖 ML预测轮动建议:")
        console.print(f"     {rotation['suggestion']}")

        console.print("\n  ✅ ML预测强势板块:")
        strong_table = Table()
        strong_table.add_column("板块", style="cyan")
        strong_table.add_column("当前强度", justify="right")
        strong_table.add_column("预测方向", justify="center")
        strong_table.add_column("置信度", justify="right")
        strong_table.add_column("建议", style="green")

        for pred in ml_predictions[:5]:
            direction = "[red]↑ 上涨[/red]" if pred.predicted_direction == 1 else "[green]↓ 下跌[/green]"

            strong_table.add_row(
                pred.sector_name,
                f"{pred.current_strength:.1f}",
                direction,
                f"{pred.confidence:.0%}",
                pred.recommendation,
            )

        console.print(strong_table)

        console.print("\n  ⚠️ ML预测弱势板块:")
        weak_table = Table()
        weak_table.add_column("板块", style="cyan")
        weak_table.add_column("当前强度", justify="right")
        weak_table.add_column("预测方向", justify="center")
        weak_table.add_column("置信度", justify="right")
        weak_table.add_column("建议", style="red")

        for pred in ml_predictions[-5:]:
            direction = "[red]↑ 上涨[/red]" if pred.predicted_direction == 1 else "[green]↓ 下跌[/green]"

            weak_table.add_row(
                pred.sector_name,
                f"{pred.current_strength:.1f}",
                direction,
                f"{pred.confidence:.0%}",
                pred.recommendation,
            )

        console.print(weak_table)

        console.print(f"\n  📋 ML建议关注: {', '.join(rotation['rotation_to'])}")
        console.print(f"  📋 ML建议回避: {', '.join(rotation['rotation_from'])}")

        console.print("\n💡 相关命令:")
        console.print("   make ml-analyze-market  # ML市场分析")
        console.print('   make ml-fund-sector FUND="基金名称"  # 分析基金板块')

    @ml_group.command()
    @click.argument("fund_name")
    def fund_sector(fund_name: str):
        from rich.console import Console

        from asset_lens.ml.sector_rotation import sector_analyzer

        console = Console()

        console.print(f"\n📊 基金板块分析: {fund_name}")
        console.print("=" * 60)

        result = sector_analyzer.get_fund_sector_recommendation(fund_name)

        console.print(f"\n  基金名称: {result['fund_name']}")
        console.print(f"  所属板块: {result['sector']}")
        console.print(f"  市场状态: {result.get('market_condition', '未知')}")

        if result.get("is_recommended"):
            console.print("  板块状态: [green]✅ 强势板块[/green]")
        elif result.get("is_avoid"):
            console.print("  板块状态: [red]⚠️ 弱势板块[/red]")
        else:
            console.print("  板块状态: [yellow]➖ 中性板块[/yellow]")

        console.print(f"\n  💡 建议: {result['recommendation']}")

        console.print("\n💡 相关命令:")
        console.print("   make ml-sector          # ML板块轮动分析")
        console.print("   make ml-analyze-market  # ML市场分析")
