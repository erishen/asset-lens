import click


def register_ml_info_commands(ml_group: click.Group) -> None:
    import logging
    from pathlib import Path

    from asset_lens.utils.json_cache import read_json_cache

    logger = logging.getLogger(__name__)

    @ml_group.command()
    @click.option("--model", default="cache/ml/model.pkl", help="模型路径")
    def importance(model: str):
        from rich.console import Console
        from rich.table import Table

        from asset_lens.ml.predictor import StockPredictor

        console = Console()
        console.print("\n📊 特征重要性分析")
        console.print("=" * 60)

        try:
            model_path = Path(model)
            if not model_path.exists():
                console.print(f"[red]❌ 模型不存在: {model_path}[/red]")
                return

            predictor = StockPredictor(model_path=model_path)

            importance_df = predictor.get_feature_importance()

            table = Table()
            table.add_column("排名", justify="right")
            table.add_column("特征", style="cyan")
            table.add_column("重要性", justify="right")
            table.add_column("占比", justify="right")

            for i, (_, row) in enumerate(importance_df.head(20).iterrows(), 1):
                table.add_row(str(i), row["feature"], f"{row['importance']:.4f}", f"{row['importance_pct']:.2f}%")

            console.print(table)

        except Exception as e:
            console.print(f"[red]❌ 分析失败: {e}[/red]")

    @ml_group.command()
    def status():
        from rich.console import Console

        console = Console()
        console.print("\n🤖 ML 模块状态")
        console.print("=" * 60)

        try:
            import lightgbm

            console.print(f"✅ LightGBM: {lightgbm.__version__}")
        except ImportError:
            console.print("[yellow]⚠️ LightGBM 未安装: pip install lightgbm[/yellow]")

        try:
            import xgboost

            console.print(f"✅ XGBoost: {xgboost.__version__}")
        except ImportError:
            console.print("[yellow]⚠️ XGBoost 未安装: pip install xgboost[/yellow]")

        try:
            import sklearn

            console.print(f"✅ scikit-learn: {sklearn.__version__}")
        except ImportError:
            console.print("[yellow]⚠️ scikit-learn 未安装: pip install scikit-learn[/yellow]")

        model_path = Path("cache/ml/model.pkl")
        if model_path.exists():
            console.print(f"\n✅ 已训练模型: {model_path}")

            result_path = model_path.with_suffix(".json")
            result = read_json_cache(result_path)
            if result:

                console.print(f"   模型类型: {result.get('model_type')}")
                console.print(f"   准确率: {result.get('accuracy', 0):.2%}")
                console.print(f"   训练时间: {result.get('timestamp', 'N/A')}")
        else:
            console.print("\n[yellow]⚠️ 未找到训练模型，请运行 make ml-train[/yellow]")

        try:
            from asset_lens.db.database import db_manager

            stats = db_manager.get_statistics()
            console.print("\n📊 数据库状态:")
            console.print(f"   K线数据: {stats['kline_count']:,} 条")
            console.print(f"   股票数量: {stats['stock_count']}")
            console.print(f"   ML模型数: {stats['model_count']}")
            console.print(f"   预测记录: {stats['prediction_count']}")

            model_info = db_manager.get_latest_model("stock_predictor")
            if model_info:
                console.print("\n✅ 数据库中的最新模型:")
                console.print(f"   ID: {model_info['id']}")
                console.print(f"   类型: {model_info['model_type']}")
                console.print(f"   准确率: {model_info['metrics'].get('accuracy', 0):.2%}")
                console.print(f"   创建时间: {model_info['created_at']}")
        except Exception as e:
            logger.debug(f"忽略异常: {e}")
            console.print("\n[yellow]⚠️ 数据库未初始化或无数据[/yellow]")
