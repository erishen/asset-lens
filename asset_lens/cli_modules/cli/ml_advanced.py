"""
Advanced ML CLI commands for asset-lens.
高级机器学习命令 - 超参数优化、模型解释、交叉验证
"""

import logging

import click
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)

console = Console()


@click.group()
def ml_advanced():
    """高级机器学习命令"""
    pass


def _prepare_training_data():
    """准备训练数据"""
    import pandas as pd

    from asset_lens.db.database import db_manager
    from asset_lens.db.models import StockKline
    from asset_lens.ml.trainer import ModelTrainer

    session = db_manager.get_session()
    try:
        result = session.query(StockKline.code).distinct().limit(50).all()
        codes = [r[0] for r in result]

        if not codes:
            return None, None, [], []

        all_X = []
        all_y = []
        all_codes = []
        all_names = []

        trainer = ModelTrainer(model_type="lightgbm")

        for code in codes[:30]:
            try:
                klines = session.query(StockKline).filter(StockKline.code == code).order_by(StockKline.date.asc()).all()

                if len(klines) < 100:
                    continue

                df = pd.DataFrame(
                    [
                        {
                            "date": k.date,
                            "open": k.open,
                            "high": k.high,
                            "low": k.low,
                            "close": k.close,
                            "volume": k.volume,
                            "amount": k.amount,
                            "turnover_rate": k.turnover_rate,
                        }
                        for k in klines
                    ]
                )

                if df.empty or len(df) < 100:
                    continue

                X, y = trainer.prepare_training_data(df, code)

                if X is not None and len(X) > 50:
                    all_X.append(X)
                    all_y.append(y)
                    all_codes.append(code)
                    all_names.append(code)

            except Exception as e:
                logger.debug(f"忽略异常: {e}")
                continue

        if not all_X:
            return None, None, [], []

        X = pd.concat(all_X, ignore_index=True)
        y = pd.concat(all_y, ignore_index=True)

        return X, y, all_codes, all_names

    finally:
        session.close()


@ml_advanced.command()
@click.option("--model", default="lightgbm", help="模型类型 (lightgbm/xgboost)")
@click.option("--trials", default=50, help="优化次数")
@click.option("--timeout", default=None, type=int, help="超时时间（秒）")
def optimize(model, trials, timeout):
    """使用 Optuna 优化超参数

    示例:
        asset-lens ml-advanced optimize --model lightgbm --trials 100
        asset-lens ml-advanced optimize --model xgboost --timeout 300
    """
    console.print("[bold blue]🔧 超参数优化[/bold blue]")
    console.print(f"模型: {model}, 优化次数: {trials}")

    try:
        from asset_lens.ml.advanced_trainer import HAS_OPTUNA, advanced_trainer

        if not HAS_OPTUNA:
            console.print("[red]❌ Optuna 未安装，使用 pip install optuna 安装[/red]")
            return

        X, y, _codes, _names = _prepare_training_data()

        if X is None or len(X) < 100:
            console.print("[yellow]⚠️ 数据不足，无法进行优化[/yellow]")
            return

        console.print(f"数据准备完成: {len(X)} 样本, {X.shape[1]} 特征")

        with console.status("[bold green]优化中...[/bold green]"):
            result = advanced_trainer.optimize_hyperparameters(
                X,
                y,
                model_type=model,
                n_trials=trials,
                timeout=timeout,
            )

        console.print("\n[bold green]✅ 优化完成![/bold green]")
        console.print(f"最佳 AUC: {result.best_value:.4f}")
        console.print(f"优化次数: {result.n_trials}")
        console.print(f"优化时间: {result.optimization_time:.2f}s")

        params_table = Table(title="最佳参数")
        params_table.add_column("参数", style="cyan")
        params_table.add_column("值", style="green")

        for param, value in result.best_params.items():
            params_table.add_row(param, str(value))

        console.print(params_table)

        if result.param_importance:
            importance_table = Table(title="参数重要性")
            importance_table.add_column("参数", style="cyan")
            importance_table.add_column("重要性", style="yellow")

            for param, importance in list(result.param_importance.items())[:10]:
                importance_table.add_row(param, f"{importance:.4f}")

            console.print(importance_table)

        advanced_trainer.save_results(result, f"optimization_{model}")

    except Exception as e:
        console.print(f"[red]❌ 优化失败: {e}[/red]")


@ml_advanced.command()
@click.option("--model", default="lightgbm", help="模型类型")
@click.option("--cv-splits", default=5, help="交叉验证折数")
@click.option("--optimize/--no-optimize", default=False, help="是否先优化超参数")
def train(model, cv_splits, optimize):
    """使用时间序列交叉验证训练模型

    示例:
        asset-lens ml-advanced train --model lightgbm
        asset-lens ml-advanced train --model xgboost --optimize
    """
    console.print("[bold blue]🎯 模型训练（时间序列交叉验证）[/bold blue]")

    try:
        from asset_lens.ml.advanced_trainer import advanced_trainer

        X, y, _codes, _names = _prepare_training_data()

        if X is None or len(X) < 100:
            console.print("[yellow]⚠️ 数据不足，无法训练[/yellow]")
            return

        console.print(f"数据准备完成: {len(X)} 样本, {X.shape[1]} 特征")

        params = None
        if optimize:
            console.print("\n[yellow]先进行超参数优化...[/yellow]")
            from asset_lens.ml.advanced_trainer import HAS_OPTUNA

            if HAS_OPTUNA:
                opt_result = advanced_trainer.optimize_hyperparameters(X, y, model_type=model, n_trials=30)
                params = opt_result.best_params
                console.print(f"优化完成，最佳 AUC: {opt_result.best_value:.4f}")

        with console.status("[bold green]训练中...[/bold green]"):
            result = advanced_trainer.train_with_cv(
                X,
                y,
                model_type=model,
                params=params,
                cv_splits=cv_splits,
            )

        console.print("\n[bold green]✅ 训练完成![/bold green]")
        console.print(f"训练时间: {result.training_time:.2f}s")

        metrics_table = Table(title="模型指标")
        metrics_table.add_column("指标", style="cyan")
        metrics_table.add_column("值", style="green")

        metrics_table.add_row("Accuracy", f"{result.accuracy:.4f}")
        metrics_table.add_row("Precision", f"{result.precision:.4f}")
        metrics_table.add_row("Recall", f"{result.recall:.4f}")
        metrics_table.add_row("F1 Score", f"{result.f1_score:.4f}")
        metrics_table.add_row("AUC-ROC", f"{result.auc_roc:.4f}")

        console.print(metrics_table)

        cv_table = Table(title="交叉验证结果")
        cv_table.add_column("Fold", style="cyan")
        cv_table.add_column("AUC", style="green")

        for i, score in enumerate(result.cv_scores):
            cv_table.add_row(f"Fold {i + 1}", f"{score:.4f}")

        cv_table.add_row("[bold]Mean[/bold]", f"[bold]{result.cv_mean:.4f}[/bold]")
        cv_table.add_row("[bold]Std[/bold]", f"[bold]{result.cv_std:.4f}[/bold]")

        console.print(cv_table)

        if result.feature_importance:
            fi_table = Table(title="特征重要性 Top 10")
            fi_table.add_column("特征", style="cyan")
            fi_table.add_column("重要性", style="yellow")

            sorted_fi = sorted(result.feature_importance.items(), key=lambda x: x[1], reverse=True)
            for feature, importance in sorted_fi[:10]:
                fi_table.add_row(feature, f"{importance:.4f}")

            console.print(fi_table)

        advanced_trainer.save_results(result, f"training_{model}")

    except Exception as e:
        console.print(f"[red]❌ 训练失败: {e}[/red]")


@ml_advanced.command()
@click.option("--sample-size", default=100, help="样本大小")
def explain(sample_size):
    """使用 SHAP 解释模型预测

    示例:
        asset-lens ml-advanced explain
        asset-lens ml-advanced explain --sample-size 200
    """
    console.print("[bold blue]📊 模型解释（SHAP）[/bold blue]")

    try:
        from asset_lens.ml.advanced_trainer import HAS_SHAP, advanced_trainer

        if not HAS_SHAP:
            console.print("[red]❌ SHAP 未安装，使用 pip install shap 安装[/red]")
            return

        X, _y, _codes, _names = _prepare_training_data()

        if X is None:
            console.print("[yellow]⚠️ 数据不足[/yellow]")
            return

        console.print(f"计算 SHAP 值 (样本: {min(sample_size, len(X))})...")

        shap_values = advanced_trainer.get_shap_explanation(X, sample_size)

        if not shap_values:
            console.print("[yellow]⚠️ 请先训练模型[/yellow]")
            return

        shap_table = Table(title="SHAP 特征重要性 Top 15")
        shap_table.add_column("特征", style="cyan")
        shap_table.add_column("SHAP 值", style="yellow")
        shap_table.add_column("影响方向", style="green")

        sorted_shap = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
        for feature, value in sorted_shap[:15]:
            direction = "📈 正向" if value > 0 else "📉 负向"
            shap_table.add_row(feature, f"{value:.4f}", direction)

        console.print(shap_table)

        console.print("\n[dim]SHAP 值表示特征对预测结果的平均影响程度[/dim]")
        console.print("[dim]正值表示增加上涨概率，负值表示增加下跌概率[/dim]")

    except Exception as e:
        console.print(f"[red]❌ 解释失败: {e}[/red]")


@ml_advanced.command()
@click.option("--k", default=50, help="选择的特征数量")
@click.option("--method", default="mutual_info", help="选择方法 (mutual_info/f_classif)")
def select_features(k, method):
    """特征选择

    示例:
        asset-lens ml-advanced select-features --k 30
        asset-lens ml-advanced select-features --k 50 --method f_classif
    """
    console.print("[bold blue]🔍 特征选择[/bold blue]")

    try:
        from asset_lens.ml.advanced_trainer import advanced_trainer

        X, y, _codes, _names = _prepare_training_data()

        if X is None:
            console.print("[yellow]⚠️ 数据不足[/yellow]")
            return

        console.print(f"原始特征数: {X.shape[1]}")

        X_selected = advanced_trainer.select_features(X, y, k=k, method=method)

        console.print(f"选择后特征数: {X_selected.shape[1]}")

        features_table = Table(title="选择的特征")
        features_table.add_column("序号", style="dim")
        features_table.add_column("特征", style="cyan")

        for i, feature in enumerate(advanced_trainer._selected_features[:30]):
            features_table.add_row(str(i + 1), feature)

        console.print(features_table)

    except Exception as e:
        console.print(f"[red]❌ 特征选择失败: {e}[/red]")


@ml_advanced.command()
def ensemble():
    """训练集成模型

    示例:
        asset-lens ml-advanced ensemble
    """
    console.print("[bold blue]🤖 集成模型训练[/bold blue]")

    try:
        from asset_lens.ml.advanced_trainer import advanced_trainer

        X, y, _codes, _names = _prepare_training_data()

        if X is None or len(X) < 100:
            console.print("[yellow]⚠️ 数据不足，无法训练[/yellow]")
            return

        console.print(f"数据准备完成: {len(X)} 样本, {X.shape[1]} 特征")
        console.print("训练 LightGBM + XGBoost 集成模型...")

        with console.status("[bold green]训练中...[/bold green]"):
            result = advanced_trainer.train_ensemble(X, y)

        console.print("\n[bold green]✅ 集成模型训练完成![/bold green]")
        console.print(f"训练时间: {result.training_time:.2f}s")
        console.print(f"特征数: {result.n_features}")

        if result.feature_importance:
            fi_table = Table(title="集成特征重要性 Top 10")
            fi_table.add_column("特征", style="cyan")
            fi_table.add_column("重要性", style="yellow")

            sorted_fi = sorted(result.feature_importance.items(), key=lambda x: x[1], reverse=True)
            for feature, importance in sorted_fi[:10]:
                fi_table.add_row(feature, f"{importance:.4f}")

            console.print(fi_table)

    except Exception as e:
        console.print(f"[red]❌ 训练失败: {e}[/red]")


@ml_advanced.command()
def compare():
    """比较不同模型性能

    示例:
        asset-lens ml-advanced compare
    """
    console.print("[bold blue]📊 模型性能比较[/bold blue]")

    try:
        from asset_lens.ml.advanced_trainer import HAS_LIGHTGBM, HAS_XGBOOST, advanced_trainer

        X, y, _codes, _names = _prepare_training_data()

        if X is None or len(X) < 100:
            console.print("[yellow]⚠️ 数据不足[/yellow]")
            return

        results = []
        models = []

        if HAS_LIGHTGBM:
            models.append("lightgbm")
        if HAS_XGBOOST:
            models.append("xgboost")

        for model_type in models:
            console.print(f"\n训练 {model_type}...")
            result = advanced_trainer.train_with_cv(X, y, model_type=model_type)
            results.append((model_type, result))

        compare_table = Table(title="模型性能比较")
        compare_table.add_column("模型", style="cyan")
        compare_table.add_column("Accuracy", style="green")
        compare_table.add_column("Precision", style="yellow")
        compare_table.add_column("Recall", style="yellow")
        compare_table.add_column("F1", style="yellow")
        compare_table.add_column("AUC-ROC", style="green")
        compare_table.add_column("CV Mean", style="green")

        for model_type, result in results:
            compare_table.add_row(
                model_type,
                f"{result.accuracy:.4f}",
                f"{result.precision:.4f}",
                f"{result.recall:.4f}",
                f"{result.f1_score:.4f}",
                f"{result.auc_roc:.4f}",
                f"{result.cv_mean:.4f} ± {result.cv_std:.4f}",
            )

        console.print(compare_table)

        best_model = max(results, key=lambda x: x[1].auc_roc)
        console.print(f"\n[bold green]🏆 最佳模型: {best_model[0]} (AUC: {best_model[1].auc_roc:.4f})[/bold green]")

    except Exception as e:
        console.print(f"[red]❌ 比较失败: {e}[/red]")


def register_ml_advanced_commands(cli: click.Group) -> None:
    """注册高级 ML 命令到 CLI 组"""
    cli.add_command(ml_advanced, name="ml-advanced")
