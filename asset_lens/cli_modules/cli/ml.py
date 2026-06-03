import click

logger = __import__("logging").getLogger(__name__)


@click.group()
def ml():
    pass


@ml.command()
@click.option("--model-type", default="lightgbm", help="模型类型 (lightgbm/xgboost/randomforest/stacking)")
@click.option("--prediction-days", default=5, help="预测天数")
@click.option("--output", default="cache/ml/model.pkl", help="模型输出路径")
def train(model_type: str, prediction_days: int, output: str):
    import numpy as np
    import pandas as pd
    from rich.console import Console
    from rich.table import Table

    from asset_lens.data.market_stock_fetcher import MarketStockFetcher
    from asset_lens.ml.trainer import ModelTrainer, TrainingConfig

    console = Console()
    console.print("\n🤖 训练机器学习模型")
    console.print(f"   模型类型: {model_type}")
    console.print(f"   预测天数: {prediction_days}")
    console.print("=" * 60)

    try:
        fetcher = MarketStockFetcher()
        stocks_data = fetcher.get_cached_market_stocks()

        if not stocks_data:
            console.print("[yellow]⚠️ 无缓存数据，正在自动获取市场股票数据...[/yellow]")
            try:
                stocks_data = fetcher.fetch_all_cn_stocks(max_pages=3)
                if stocks_data:
                    fetcher.save_market_stocks(stocks_data)
                    console.print(f"[green]✅ 已获取 {len(stocks_data)} 只股票数据[/green]")
                else:
                    console.print("[red]❌ 获取市场数据失败[/red]")
                    return
            except (ConnectionError, OSError, RuntimeError) as e:
                console.print(f"[red]❌ 获取市场数据失败: {e}[/red]")
                return

        console.print(f"✅ 加载 {len(stocks_data)} 只股票数据")

        config = TrainingConfig(prediction_days=prediction_days)
        trainer = ModelTrainer(model_type=model_type, config=config)

        console.print("\n📊 准备训练数据...")

        np.random.seed(42)
        stocks_price_data = {}

        for stock in stocks_data[:200]:
            code = stock.get("code", "")
            stock.get("name", "")
            current_price = stock.get("current_price", 10)

            if not code or current_price <= 0:
                continue

            n_days = 100
            returns = np.random.randn(n_days) * 0.02
            prices = current_price * np.exp(np.cumsum(returns))

            df = pd.DataFrame(
                {
                    "open": prices * (1 + np.random.randn(n_days) * 0.01),
                    "high": prices * (1 + np.abs(np.random.randn(n_days) * 0.02)),
                    "low": prices * (1 - np.abs(np.random.randn(n_days) * 0.02)),
                    "close": prices,
                    "volume": np.random.randint(100000, 1000000, n_days),
                    "amount": prices * np.random.randint(100000, 1000000, n_days),
                }
            )

            stocks_price_data[code] = df

        if not stocks_price_data:
            console.print("[red]❌ 无法准备训练数据[/red]")
            return

        console.print(f"✅ 准备 {len(stocks_price_data)} 只股票模拟历史数据")

        console.print("\n📊 数据集统计")
        console.print("=" * 60)
        total_records = sum(len(df) for df in stocks_price_data.values())
        console.print(f"  股票数量: {len(stocks_price_data)}")
        console.print(f"  总记录数: {total_records:,}")
        console.print(f"  平均每只股票: {total_records // len(stocks_price_data) if stocks_price_data else 0} 条")

        console.print("\n🚀 开始训练...")
        result = trainer.train_with_market_data(stocks_price_data)

        output_path = __import__("pathlib").Path(output)
        trainer.save_model(output_path)
        console.print(f"✅ 模型已保存: {output_path}")

        result_path = output_path.with_suffix(".json")
        trainer.save_training_result(result, result_path)

        console.print("\n📈 训练结果:")
        result_table = Table(show_header=False)
        result_table.add_column("指标", style="cyan")
        result_table.add_column("值", justify="right")

        result_table.add_row("模型类型", result.model_type)
        result_table.add_row("准确率", f"{result.accuracy:.2%}")
        result_table.add_row("精确率", f"{result.precision:.2%}")
        result_table.add_row("召回率", f"{result.recall:.2%}")
        result_table.add_row("F1分数", f"{result.f1_score:.2%}")
        result_table.add_row("AUC", f"{result.auc:.2%}")
        result_table.add_row("训练样本", f"{result.training_samples}")
        result_table.add_row("测试样本", f"{result.test_samples}")
        result_table.add_row("训练时间", f"{result.training_time:.2f}秒")

        console.print(result_table)

        console.print("\n📊 Top 10 重要特征:")
        feature_table = Table()
        feature_table.add_column("特征", style="cyan")
        feature_table.add_column("重要性", justify="right")
        feature_table.add_column("占比", justify="right")

        for _, row in result.feature_importance.head(10).iterrows():
            feature_table.add_row(row["feature"], f"{row['importance']:.4f}", f"{row['importance_pct']:.2f}%")

        console.print(feature_table)

        console.print("\n✅ 训练完成！")

    except Exception as e:
        console.print(f"[red]❌ 训练失败: {e}[/red]")
        import traceback

        traceback.print_exc()


from .ml_db_commands import register_ml_db_commands
from .ml_info_commands import register_ml_info_commands
from .ml_predict_commands import register_ml_predict_commands
from .ml_sector_commands import register_ml_sector_commands
from .ml_trade_commands import register_ml_trade_commands

register_ml_db_commands(ml)
register_ml_info_commands(ml)
register_ml_predict_commands(ml)
register_ml_sector_commands(ml)
register_ml_trade_commands(ml)


def register_ml_commands(cli_group):
    cli_group.add_command(ml)


def get_ml_command():
    return ml


if __name__ == "__main__":
    ml()
