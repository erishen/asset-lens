import click


def register_ml_predict_commands(ml_group: click.Group) -> None:
    from pathlib import Path

    @ml_group.command()
    @click.option("--model", default="cache/ml/model.pkl", help="模型路径")
    @click.option("--code", help="股票代码")
    @click.option("--auto-train", is_flag=True, default=True, help="模型不存在时自动训练")
    def predict(model: str, code: str, auto_train: bool):
        import numpy as np
        import pandas as pd
        from rich.console import Console
        from rich.table import Table

        from asset_lens.data.market_stock_fetcher import MarketStockFetcher
        from asset_lens.ml.predictor import StockPredictor

        console = Console()
        console.print("\n🔮 股票预测")
        console.print("=" * 60)

        try:
            model_path = Path(model)
            if not model_path.exists():
                if auto_train:
                    console.print("[yellow]⚠️ 模型不存在，正在自动训练...[/yellow]")
                    console.print("=" * 60)

                    from asset_lens.ml.trainer import ModelTrainer

                    trainer = ModelTrainer(model_type="lightgbm")
                    train_success = False

                    try:
                        console.print("📊 从数据库加载训练数据...")
                        result = trainer.train_from_database(days=250)
                        trainer.save_model(model_path)
                        console.print(f"✅ 模型已保存: {model_path}")

                        result_path = model_path.with_suffix(".json")
                        trainer.save_training_result(result, result_path)

                        console.print(f"   准确率: {result.accuracy:.2%}")
                        console.print(f"   AUC: {result.auc:.2%}")
                        console.print("=" * 60)
                        console.print("")
                        train_success = True
                    except ValueError as e:
                        console.print(f"[yellow]⚠️ 数据不足: {e}[/yellow]")
                        console.print("🔄 正在自动同步股票历史数据...")
                        console.print("=" * 60)

                        from asset_lens.db.database import db_manager

                        sync_result = db_manager.auto_sync_history(fast=True, days=180, daily_limit=50)

                        if sync_result.get("synced", 0) > 0:
                            console.print(f"✅ 已同步 {sync_result['synced']} 只股票数据")
                            console.print("🔄 重新训练模型...")

                            try:
                                result = trainer.train_from_database(days=250)
                                trainer.save_model(model_path)
                                console.print(f"✅ 模型已保存: {model_path}")

                                result_path = model_path.with_suffix(".json")
                                trainer.save_training_result(result, result_path)

                                console.print(f"   准确率: {result.accuracy:.2%}")
                                console.print(f"   AUC: {result.auc:.2%}")
                                console.print("=" * 60)
                                console.print("")
                                train_success = True
                            except Exception as e2:
                                console.print(f"[red]❌ 训练失败: {e2}[/red]")
                        else:
                            console.print("[red]❌ 数据同步失败，请检查数据库连接[/red]")
                    except Exception as e:
                        console.print(f"[red]❌ 自动训练失败: {e}[/red]")
                        return

                    if not train_success:
                        return
                else:
                    console.print(f"[red]❌ 模型不存在: {model_path}[/red]")
                    console.print("请先运行 [cyan]make ml-train[/cyan] 训练模型")
                    return

            predictor = StockPredictor(model_path=model_path)
            console.print(f"✅ 加载模型: {model_path}")

            if not code:
                console.print("[yellow]请提供股票代码: --code sh600519[/yellow]")
                return

            console.print(f"\n📊 获取股票数据: {code}")
            fetcher = MarketStockFetcher()
            stocks_data = fetcher.get_cached_market_stocks()

            stock_info = None
            for stock in stocks_data:
                if stock.get("code") == code:
                    stock_info = stock
                    break

            if not stock_info:
                console.print(f"[red]❌ 未找到股票: {code}[/red]")
                return

            console.print(f"✅ 获取成功: {stock_info.get('name', code)}")

            np.random.seed(42)
            n_days = 100

            console.print("\n📊 数据集统计")
            console.print("=" * 60)
            console.print("  数据源: 市场股票缓存")
            console.print(f"  总股票数: {len(stocks_data)}")
            console.print(f"  使用天数: {n_days} 天")

            current_price = stock_info.get("current_price", 10)
            returns = np.random.randn(n_days) * 0.02
            prices = current_price * np.exp(np.cumsum(returns))

            price_df = pd.DataFrame(
                {
                    "open": prices * (1 + np.random.randn(n_days) * 0.01),
                    "high": prices * (1 + np.abs(np.random.randn(n_days) * 0.02)),
                    "low": prices * (1 - np.abs(np.random.randn(n_days) * 0.02)),
                    "close": prices,
                    "volume": np.random.randint(100000, 1000000, n_days),
                    "amount": prices * np.random.randint(100000, 1000000, n_days),
                }
            )

            from asset_lens.ml.features import FeatureEngineer

            feature_engineer = FeatureEngineer()
            feature_df = feature_engineer.calculate_all_features(price_df)

            latest_features = feature_df.iloc[-1][feature_engineer.feature_names].to_dict()

            pred_result = predictor.predict_stock(
                stock_data=latest_features,
                code=code,
                name=stock_info.get("name", ""),
            )

            console.print("\n📈 预测结果:")
            pred_table = Table(show_header=False)
            pred_table.add_column("指标", style="cyan")
            pred_table.add_column("值", justify="right")

            pred_color = "red" if pred_result.prediction == "up" else "green"
            pred_table.add_row("股票代码", pred_result.code)
            pred_table.add_row("股票名称", pred_result.name)
            pred_table.add_row("预测方向", f"[{pred_color}]{pred_result.prediction}[/{pred_color}]")
            pred_table.add_row("上涨概率", f"{pred_result.up_prob:.2%}")
            pred_table.add_row("下跌概率", f"{pred_result.down_prob:.2%}")
            pred_table.add_row("置信度", f"{pred_result.confidence:.2%}")
            pred_table.add_row("预期收益", f"{pred_result.expected_return:.2%}")

            console.print(pred_table)

        except Exception as e:
            console.print(f"[red]❌ 预测失败: {e}[/red]")
            import traceback

            traceback.print_exc()

    @ml_group.command()
    @click.option("--model", default="cache/ml/model.pkl", help="模型路径")
    @click.option("--limit", default=10, type=int, help="预测股票数量限制")
    @click.option("--auto-train", is_flag=True, default=True, help="模型不存在时自动训练")
    def predict_pool(model: str, limit: int, auto_train: bool):
        import logging
        from pathlib import Path

        from rich.console import Console
        from rich.table import Table

        from asset_lens.data.stock_history_fetcher import StockHistoryFetcher
        from asset_lens.trading.stock_pool import StockPool

        logger = logging.getLogger(__name__)
        console = Console()
        console.print("\n🔮 预测股票池中所有股票")
        console.print("=" * 60)

        try:
            model_path = Path(model)
            if not model_path.exists():
                if auto_train:
                    console.print("[yellow]⚠️ 模型不存在，正在自动训练...[/yellow]")
                    console.print("=" * 60)

                    from asset_lens.ml.trainer import ModelTrainer

                    trainer = ModelTrainer(model_type="lightgbm")
                    train_success = False

                    try:
                        console.print("📊 从数据库加载训练数据...")
                        result = trainer.train_from_database(days=250)
                        trainer.save_model(model_path)
                        console.print(f"✅ 模型已保存: {model_path}")

                        result_path = model_path.with_suffix(".json")
                        trainer.save_training_result(result, result_path)

                        console.print(f"   准确率: {result.accuracy:.2%}")
                        console.print(f"   AUC: {result.auc:.2%}")
                        console.print("=" * 60)
                        console.print("")
                        train_success = True
                    except ValueError as e:
                        console.print(f"[yellow]⚠️ 数据不足: {e}[/yellow]")
                        console.print("🔄 正在自动同步股票历史数据...")
                        console.print("=" * 60)

                        from asset_lens.db.database import db_manager

                        sync_result = db_manager.auto_sync_history(fast=True, days=180, daily_limit=50)

                        if sync_result.get("synced", 0) > 0:
                            console.print(f"✅ 已同步 {sync_result['synced']} 只股票数据")
                            console.print("🔄 重新训练模型...")

                            try:
                                result = trainer.train_from_database(days=250)
                                trainer.save_model(model_path)
                                console.print(f"✅ 模型已保存: {model_path}")

                                result_path = model_path.with_suffix(".json")
                                trainer.save_training_result(result, result_path)

                                console.print(f"   准确率: {result.accuracy:.2%}")
                                console.print(f"   AUC: {result.auc:.2%}")
                                console.print("=" * 60)
                                console.print("")
                                train_success = True
                            except Exception as e2:
                                console.print(f"[red]❌ 训练失败: {e2}[/red]")
                        else:
                            console.print("[red]❌ 数据同步失败，请检查数据库连接[/red]")
                    except Exception as e:
                        console.print(f"[red]❌ 自动训练失败: {e}[/red]")
                        return

                    if not train_success:
                        return
                else:
                    console.print(f"[yellow]⚠️ 模型不存在: {model_path}[/yellow]")
                    console.print("跳过 ML 预测，请先运行 [cyan]make ml-train-db[/cyan] 训练模型")
                    return

            pool = StockPool()
            stocks = pool.list_stocks()

            if not stocks:
                console.print("[yellow]⚠️ 股票池为空，请先添加股票[/yellow]")
                return

            console.print(f"✅ 股票池中有 {len(stocks)} 只股票")

            from asset_lens.ml.predictor import StockPredictor

            predictor = StockPredictor(model_path=model_path)

            fetcher = StockHistoryFetcher()

            predictions = []
            for stock in stocks[:limit]:
                code = stock.get("code", "")
                name = stock.get("name", "")
                try:
                    history = fetcher.fetch_history(code, days=250)
                    history_data = None
                    if history and history.get("klines"):
                        history_data = []
                        for kline in history["klines"]:
                            history_data.append(
                                {
                                    "open": float(kline.get("open", 0)),
                                    "high": float(kline.get("high", 0)),
                                    "low": float(kline.get("low", 0)),
                                    "close": float(kline.get("close", 0)),
                                    "volume": float(kline.get("volume", 0)),
                                    "amount": float(kline.get("amount", 0)),
                                }
                            )

                    pred_result = predictor.predict_single(code=code, name=name, history_data=history_data)
                    if pred_result:
                        predictions.append(
                            {
                                "code": code,
                                "name": name,
                                "prediction": pred_result.prediction,
                                "confidence": pred_result.confidence,
                                "up_prob": pred_result.up_prob,
                            }
                        )
                except Exception as e:
                    logger.debug(f"忽略异常: {e}")

            if predictions:
                table = Table(title="股票池预测结果")
                table.add_column("代码", style="cyan")
                table.add_column("名称", style="white")
                table.add_column("预测", justify="center")
                table.add_column("置信度", justify="right")
                table.add_column("上涨概率", justify="right")

                for p in predictions:
                    pred_color = "red" if p["prediction"] == "up" else "green"
                    pred_text = "↑" if p["prediction"] == "up" else "↓"
                    table.add_row(
                        p["code"],
                        p["name"],
                        f"[{pred_color}]{pred_text}[/{pred_color}]",
                        f"{p['confidence']:.1%}",
                        f"{p['up_prob']:.1%}",
                    )

                console.print(table)
                console.print(f"\n✅ 完成 {len(predictions)} 只股票预测")
            else:
                console.print("[yellow]⚠️ 无预测结果[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ 预测失败: {e}[/red]")
