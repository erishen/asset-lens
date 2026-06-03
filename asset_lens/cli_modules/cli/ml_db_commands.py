import click


def register_ml_db_commands(ml_group: click.Group) -> None:
    from pathlib import Path

    @ml_group.command()
    @click.option("--model-type", default="lightgbm", help="模型类型")
    @click.option("--days", default=250, help="使用最近N天的数据")
    @click.option("--output", default="cache/ml/model.pkl", help="模型输出路径")
    def train_db(model_type: str, days: int, output: str):
        from rich.console import Console
        from rich.table import Table

        from asset_lens.ml.trainer import ModelTrainer

        console = Console()
        console.print("\n🤖 从数据库训练模型")
        console.print(f"   模型类型: {model_type}")
        console.print(f"   数据天数: {days}")
        console.print("=" * 60)

        try:
            trainer = ModelTrainer(model_type=model_type)

            console.print("\n📊 从数据库加载训练数据...")
            result = trainer.train_from_database(days=days)

            output_path = Path(output)
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

            console.print(result_table)
            console.print("\n✅ 训练完成！")

        except ValueError as e:
            console.print(f"[yellow]⚠️ {e}[/yellow]")
            console.print("🔄 正在自动同步股票历史数据...")

            from asset_lens.db.database import db_manager

            sync_result = db_manager.auto_sync_history(fast=True, days=180, daily_limit=50)

            if sync_result.get("synced", 0) > 0:
                console.print(f"✅ 已同步 {sync_result['synced']} 只股票数据")
                console.print("🔄 重新训练模型...")
                try:
                    result = trainer.train_from_database(days=days)
                    output_path = Path(output)
                    trainer.save_model(output_path)
                    console.print(f"✅ 模型已保存: {output_path}")
                    console.print("\n✅ 训练完成！")
                except Exception as retry_error:
                    console.print(f"[red]❌ 重试训练失败: {retry_error}[/red]")
            else:
                console.print("[red]❌ 同步数据失败，请检查网络连接[/red]")
        except Exception as e:
            console.print(f"[red]❌ 训练失败: {e}[/red]")
            import traceback

            traceback.print_exc()

    @ml_group.command()
    @click.argument("code")
    @click.option("--model", default="cache/ml/model.pkl", help="模型路径")
    def predict_db(code: str, model: str):
        from rich.console import Console
        from rich.table import Table

        from asset_lens.ml.trainer import ModelTrainer

        console = Console()
        console.print(f"\n🔮 从数据库预测股票: {code}")
        console.print("=" * 60)

        try:
            model_path = Path(model)
            if not model_path.exists():
                console.print(f"[red]❌ 模型不存在: {model_path}[/red]")
                return

            trainer = ModelTrainer()
            trainer.load_model(model_path)

            result = trainer.predict_and_save(code, save_to_db=True)

            if "error" in result:
                console.print(f"[red]❌ {result['error']}[/red]")
                return

            console.print("\n📈 预测结果:")
            pred_table = Table(show_header=False)
            pred_table.add_column("指标", style="cyan")
            pred_table.add_column("值", justify="right")

            pred_color = "red" if result.get("prediction") == 1 else "green"
            pred_text = "上涨" if result.get("prediction") == 1 else "下跌"
            pred_table.add_row("股票代码", code)
            pred_table.add_row("预测方向", f"[{pred_color}]{pred_text}[/{pred_color}]")
            pred_table.add_row("置信度", f"{result.get('confidence', 0):.2%}")

            console.print(pred_table)
            console.print("\n✅ 预测结果已保存到数据库")

        except Exception as e:
            console.print(f"[red]❌ 预测失败: {e}[/red]")
            import traceback

            traceback.print_exc()

    @ml_group.command()
    @click.option("--days", default=30, help="查看最近N天的预测")
    def predictions(days: int):
        from rich.console import Console
        from rich.table import Table

        from asset_lens.db.database import db_manager

        console = Console()
        console.print(f"\n📊 历史预测记录 (最近{days}天)")
        console.print("=" * 60)

        try:
            records = db_manager.get_predictions(days=days)

            if not records:
                console.print("[yellow]暂无预测记录[/yellow]")
                return

            table = Table()
            table.add_column("日期", style="cyan")
            table.add_column("代码", style="white")
            table.add_column("预测", style="yellow")
            table.add_column("置信度", justify="right")
            table.add_column("结果", style="green")

            for r in records[:50]:
                pred_text = "涨" if r["prediction"] == 1 else "跌"
                result_text = ""
                if r.get("actual_result") is not None:
                    actual = "涨" if r["actual_result"] == 1 else "跌"
                    correct = "✓" if r.get("is_correct") else "✗"
                    result_text = f"{actual} {correct}"

                table.add_row(r["predict_date"], r["code"], pred_text, f"{r['confidence']:.1%}", result_text)

            console.print(table)

        except Exception as e:
            console.print(f"[red]❌ 查询失败: {e}[/red]")
