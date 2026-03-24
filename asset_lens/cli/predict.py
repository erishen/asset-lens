"""
预测相关 CLI 命令
"""

import click
from rich.console import Console
from rich.table import Table


def register_predict_commands(cli: click.Group) -> None:
    """注册预测命令到 CLI 组"""

    @cli.command("predict-etf")
    @click.option("--code", type=str, help="ETF 代码")
    @click.option("--days", type=int, default=5, help="预测天数")
    def predict_etf(code: str | None, days: int):
        """预测 ETF 走势"""
        from asset_lens.data.stock_activity_analyzer import StockActivityAnalyzer

        click.echo("\n📊 ETF 走势预测")
        click.echo("=" * 60)

        try:
            analyzer = StockActivityAnalyzer()

            if code:
                result = analyzer.predict_etf(code, days)
                click.echo(f"\n📈 {code} 预测结果:")
                click.echo(f"  当前价格: ¥{result.current_price:.2f}")
                click.echo(f"  预测价格: ¥{result.predicted_price:.2f}")
                click.echo(f"  预测涨跌: {result.predicted_change:.2f}%")
                click.echo(f"  置信度: {result.confidence:.1f}%")
                click.echo(f"  趋势: {result.trend}")

                if result.related_stocks:
                    console = Console()
                    table = Table(title="相关股票")
                    table.add_column("代码", style="cyan")
                    table.add_column("名称", style="green")
                    table.add_column("涨跌幅", justify="right")
                    table.add_column("市值", justify="right")

                    for stock in result.related_stocks[:10]:
                        table.add_row(
                            stock.get("code", ""),
                            stock.get("name", ""),
                            f"{stock.get('change_percent', 0):.2f}%",
                            f"¥{stock.get('market_cap', 1):,.1f}",
                        )
                    console.print(table)
            else:
                click.echo("请使用 --code 参数指定 ETF 代码")
                click.echo("示例: asset-lens predict-etf --code 510050 --days 5")

            click.echo("\n✅ 预测完成！")

        except Exception as e:
            click.echo(f"❌ 预测失败: {e}", err=True)

    @cli.command("ml-analyze-market")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def ml_analyze_market(data_mode: str | None):
        """ML 市场分析"""
        from asset_lens.cli.helpers import setup_data_mode
        from asset_lens.data.market_environment import MarketEnvironmentAnalyzer

        setup_data_mode(data_mode)

        click.echo("\n📊 ML 市场分析")
        click.echo("=" * 60)

        try:
            analyzer = MarketEnvironmentAnalyzer()
            result = analyzer.analyze_environment()

            if result:
                click.echo(f"\n市场类型: {result.market_type}")
                click.echo(f"市场情绪: {result.sentiment}")
                click.echo(f"推荐策略: {result.recommended_strategies}")

            click.echo("\n✅ ML 市场分析完成！")

        except Exception as e:
            click.echo(f"❌ ML 市场分析失败: {e}", err=True)

    @cli.command("ml-sector")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def ml_sector(data_mode: str | None):
        """ML 板块轮动分析"""
        from asset_lens.cli.helpers import setup_data_mode
        from asset_lens.ml.sector_rotation import SectorRotationAnalyzer

        setup_data_mode(data_mode)

        click.echo("\n📊 ML 板块轮动分析")
        click.echo("=" * 60)

        try:
            analyzer = SectorRotationAnalyzer()
            result = analyzer.analyze()

            if result:
                console = Console()
                table = Table(title="板块轮动分析")
                table.add_column("板块", style="cyan")
                table.add_column("热度", justify="right")
                table.add_column("趋势", style="green")
                table.add_column("建议", style="yellow")

                for sector in result.strong_sectors[:10]:
                    table.add_row(
                        sector.name,
                        f"{sector.strength_score:.1f}",
                        sector.trend,
                        sector.recommendation,
                    )
                console.print(table)

            click.echo("\n✅ ML 板块轮动分析完成！")

        except Exception as e:
            click.echo(f"❌ ML 板块轮动分析失败: {e}", err=True)
