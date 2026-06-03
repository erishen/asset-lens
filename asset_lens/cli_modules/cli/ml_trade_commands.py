import click


def register_ml_trade_commands(ml_group: click.Group) -> None:
    @ml_group.command()
    @click.option("--model-type", default="lightgbm", help="模型类型")
    def train_adaptive(model_type: str):
        from rich.console import Console

        from asset_lens.ml.adaptive_trainer import adaptive_trainer

        console = Console()

        result = adaptive_trainer.analyze_and_train(model_type=model_type)

        if "error" in result:
            console.print(f"[red]❌ {result['error']}[/red]")
            return

        training_result = result.get("training_result", {})
        console.print("\n✅ 自适应训练完成!")
        console.print(f"   准确率: {training_result.get('accuracy', 0):.2%}")
        console.print(f"   AUC: {training_result.get('auc', 0):.2%}")

        ai_stats = result.get("ai_stats", {})
        if ai_stats:
            console.print("\n📊 AI 资源消耗统计")
            console.print("=" * 60)
            console.print(f"  本次 Tokens: {ai_stats.get('session_tokens', 0):,}")
            console.print(f"  本次费用: ${ai_stats.get('session_cost', 0):.6f}")
            console.print(f"  累计 Tokens: {ai_stats.get('total_tokens', 0):,}")
            console.print(f"  累计费用: ${ai_stats.get('total_cost', 0):.6f}")

    @ml_group.command()
    def analyze_market():
        from rich.console import Console

        from asset_lens.ml.adaptive_trainer import AIMarketAnalyzer

        console = Console()
        console.print("\n📊 ML市场分析")
        console.print("=" * 60)

        analyzer = AIMarketAnalyzer()
        analysis = analyzer.analyze_market()

        console.print(f"\n  市场状态: [bold]{analysis.condition.value.upper()}[/bold]")
        console.print(f"  置信度: {analysis.confidence:.1%}")
        console.print(f"  风险等级: {analysis.risk_level}")
        console.print(f"  建议策略: {analysis.suggested_strategy}")
        console.print(f"\n  投资建议: {analysis.recommendation}")

        console.print("\n  市场指标:")
        for key, value in analysis.indicators.items():
            if isinstance(value, float):
                console.print(f"    {key}: {value:.4f}")
            else:
                console.print(f"    {key}: {value}")

        console.print("\n💡 相关命令:")
        console.print("   make ml-sector          # ML板块轮动分析")
        console.print("   make ai-trade           # AI模拟交易")
        console.print("   make ai-train-adaptive  # AI自适应训练")

    @ml_group.command()
    def trade():
        from rich.console import Console

        from asset_lens.ml.ai_trader import AISimulatedTrader

        console = Console()

        trader = AISimulatedTrader()
        trader.run_trading_session()

        console.print("\n✅ 交易会话完成!")

    @ml_group.command()
    @click.option("--days", default=7, help="查看最近N天的交易记录")
    def trade_history(days: int):
        from asset_lens.ml.ai_trader import AISimulatedTrader

        trader = AISimulatedTrader()
        trader.show_trading_history(days=days)

    @ml_group.command()
    def portfolio():
        from rich.console import Console
        from rich.table import Table

        from asset_lens.ml.ai_trader import AISimulatedTrader

        console = Console()
        trader = AISimulatedTrader()
        summary = trader.get_portfolio_summary()

        console.print("\n📊 投资组合概览")
        console.print("=" * 60)

        console.print(f"\n  初始资金: ¥{summary['initial_capital']:,.2f}")
        console.print(f"  可用资金: ¥{summary['current_capital']:,.2f}")
        console.print(f"  持仓市值: ¥{summary['total_market_value']:,.2f}")
        console.print(f"  总资产: ¥{summary['total_value']:,.2f}")

        profit_color = "green" if summary["total_profit_rate"] >= 0 else "red"
        console.print(f"  总收益: [{profit_color}]{summary['total_profit_rate']:+.2f}%[/{profit_color}]")

        if summary["holdings"]:
            console.print(f"\n  当前持仓 ({summary['holding_count']}只):")

            table = Table()
            table.add_column("代码", style="cyan")
            table.add_column("名称", style="white")
            table.add_column("买入价", justify="right")
            table.add_column("现价", justify="right")
            table.add_column("数量", justify="right")
            table.add_column("市值", justify="right")
            table.add_column("收益%", justify="right")

            for h in summary["holdings"]:
                profit_color = "green" if h["profit_rate"] >= 0 else "red"
                table.add_row(
                    h["code"],
                    h["name"],
                    f"¥{h['buy_price']:.2f}",
                    f"¥{h['current_price']:.2f}",
                    str(h["shares"]),
                    f"¥{h['market_value']:,.0f}",
                    f"[{profit_color}]{h['profit_rate']:+.2f}%[/{profit_color}]",
                )

            console.print(table)
        else:
            console.print("\n  [yellow]暂无持仓[/yellow]")
