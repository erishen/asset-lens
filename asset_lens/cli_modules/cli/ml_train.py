"""
ML Training and Backtest CLI.
ML 训练和回测命令行工具

功能:
1. 模型训练 (含超参数优化)
2. 模型融合
3. 历史回测
4. 信号验证
5. 报告生成
"""

import json
import logging
from pathlib import Path
from typing import Any

import click
import pandas as pd

from ...db.database import db_manager
from ...ml.advanced_trainer import advanced_trainer
from ...ml.backtest import BacktestConfig, BacktestEngine, SignalValidator, generate_backtest_report
from ...ml.features import FeatureEngineer
from ...ml.trainer import ModelTrainer

logger = logging.getLogger(__name__)


@click.group()
def ml_cli() -> None:
    """ML 训练和回测命令"""
    pass


@ml_cli.command()
@click.option("--model", "-m", default="lightgbm", help="模型类型 (lightgbm/xgboost/ensemble)")
@click.option("--days", "-d", default=500, help="训练数据天数")
@click.option("--codes", "-c", multiple=True, help="股票代码 (可多个)")
@click.option("--optimize", "-o", is_flag=True, help="是否进行超参数优化")
@click.option("--trials", "-t", default=50, help="Optuna 优化次数")
@click.option("--output", "-out", default="models", help="输出目录")
def train(
    model: str,
    days: int,
    codes: tuple[str, ...],
    optimize: bool,
    trials: int,
    output: str,
) -> None:
    """训练 ML 模型"""
    click.echo(f"🚀 开始训练 {model} 模型...")

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    trainer = ModelTrainer(model_type=model)

    codes_list = list(codes) if codes else None

    if optimize:
        click.echo(f"📊 进行超参数优化 ({trials} 次)...")

        klines_data = db_manager.get_klines_for_ml(codes=codes_list, days=days)
        if not klines_data:
            click.echo("❌ 没有足够的训练数据")
            return

        stocks_data = _prepare_stocks_data(klines_data)
        X, y = trainer.prepare_multi_stock_data(stocks_data)

        opt_result = advanced_trainer.optimize_hyperparameters(
            X,
            y,
            model_type=model,
            n_trials=trials,
            cv_splits=5,
        )

        click.echo(f"✅ 优化完成: 最佳 AUC = {opt_result.best_value:.4f}")
        click.echo(f"   最佳参数: {opt_result.best_params}")

        advanced_trainer.save_results(opt_result, f"{model}_optimization")

        result: Any = advanced_trainer.train_with_cv(X, y, model_type=model, params=opt_result.best_params)
    else:
        result = trainer.train_from_database(codes=codes_list, days=days)

    click.echo("\n📈 训练结果:")
    click.echo(f"   准确率:   {result.accuracy:.2%}")
    click.echo(f"   精确率:   {result.precision:.2%}")
    click.echo(f"   召回率:   {result.recall:.2%}")
    click.echo(f"   F1 分数:  {result.f1_score:.2%}")
    auc_value = getattr(result, "auc", None) or getattr(result, "auc_roc", 0)
    click.echo(f"   AUC:      {auc_value:.4f}")

    if hasattr(result, "cv_scores") and result.cv_scores:
        if hasattr(result, "cv_mean"):
            click.echo(f"   交叉验证: {result.cv_mean:.4f} ± {result.cv_std:.4f}")
        else:
            import numpy as np

            cv_mean = np.mean(result.cv_scores)
            cv_std = np.std(result.cv_scores)
            click.echo(f"   交叉验证: {cv_mean:.4f} ± {cv_std:.4f}")

    model_path = output_dir / f"{model}_model.joblib"
    trainer.save_model(model_path)
    click.echo(f"\n💾 模型已保存: {model_path}")

    result_path = output_dir / f"{model}_result.json"
    trainer.save_training_result(result, result_path)
    click.echo(f"📄 结果已保存: {result_path}")


@ml_cli.command()
@click.option("--model", "-m", default="lightgbm", help="模型类型")
@click.option("--days", "-d", default=500, help="训练数据天数")
@click.option("--backtest-days", "-bd", default=250, help="回测天数")
@click.option("--capital", "-c", default=100000, help="初始资金")
@click.option("--position-size", "-ps", default=0.1, help="仓位比例")
@click.option("--output", "-out", default="reports", help="输出目录")
def backtest(
    model: str,
    days: int,
    backtest_days: int,
    capital: float,
    position_size: float,
    output: str,
) -> None:
    """运行回测"""
    click.echo("📊 开始回测...")

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    trainer = ModelTrainer(model_type=model)
    trainer.train_from_database(days=days)

    click.echo("📈 生成预测信号...")

    klines_data = db_manager.get_klines_for_ml(days=backtest_days)

    if not klines_data:
        click.echo("❌ 没有回测数据")
        return

    predictions_list = []
    price_data = {}

    feature_engineer = FeatureEngineer()

    for code, klines in klines_data.items():
        if len(klines) < 60:
            continue

        df = pd.DataFrame(klines)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df_features = feature_engineer.calculate_all_features(df)

        feature_cols = feature_engineer.feature_names
        X = df_features[feature_cols].fillna(0).replace([float("inf"), float("-inf")], 0)

        predictions = trainer.predictor.predict(X)
        probas = trainer.predictor.predict_proba(X)[:, 1]

        for _i, (date, pred, prob) in enumerate(zip(df["date"], predictions, probas, strict=False)):
            predictions_list.append(
                {
                    "code": code,
                    "date": str(date.date()),
                    "prediction": int(pred),
                    "up_prob": float(prob),
                }
            )

        price_data[code] = df

    if not predictions_list:
        click.echo("❌ 没有生成预测信号")
        return

    predictions_df = pd.DataFrame(predictions_list)

    click.echo("📊 运行回测引擎...")

    config = BacktestConfig(
        initial_capital=capital,
        position_size=position_size,
    )

    engine = BacktestEngine(config)
    result = engine.run_backtest(predictions_df, price_data)

    click.echo("\n" + "=" * 50)
    click.echo("                  回测结果")
    click.echo("=" * 50)
    click.echo(f"  总收益率:   {result.total_return:.2f}%")
    click.echo(f"  年化收益:   {result.annual_return:.2f}%")
    click.echo(f"  最大回撤:   {result.max_drawdown:.2f}%")
    click.echo(f"  夏普比率:   {result.sharpe_ratio:.2f}")
    click.echo(f"  胜率:       {result.win_rate:.2f}%")
    click.echo(f"  盈亏比:     {result.profit_factor:.2f}")
    click.echo(f"  总交易:     {result.total_trades} 次")
    click.echo("=" * 50)

    validator = SignalValidator()
    signal_result = validator.validate_signals(predictions_df, price_data)

    click.echo("\n📊 信号验证:")
    click.echo(f"   总信号数:   {signal_result['total_signals']}")
    click.echo(f"   准确率:     {signal_result['accuracy']:.2f}%")
    click.echo(f"   平均收益:   {signal_result['avg_return']:.2f}%")

    report_path = output_dir / f"backtest_report_{model}.txt"
    generate_backtest_report(result, signal_result, report_path)

    click.echo(f"\n📄 报告已保存: {report_path}")

    result_json_path = output_dir / f"backtest_result_{model}.json"
    with open(result_json_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
    click.echo(f"📄 结果已保存: {result_json_path}")


@ml_cli.command()
@click.option("--days", "-d", default=500, help="训练数据天数")
@click.option("--trials", "-t", default=100, help="Optuna 优化次数")
@click.option("--output", "-out", default="models", help="输出目录")
def optimize(
    days: int,
    trials: int,
    output: str,
) -> None:
    """超参数优化"""
    click.echo("🔧 开始超参数优化...")

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    klines_data = db_manager.get_klines_for_ml(days=days)

    if not klines_data:
        click.echo("❌ 没有训练数据")
        return

    stocks_data = _prepare_stocks_data(klines_data)

    trainer = ModelTrainer()
    X, y = trainer.prepare_multi_stock_data(stocks_data)

    click.echo(f"📊 数据准备完成: {len(X)} 样本, {X.shape[1]} 特征")

    results = {}

    for model_type in ["lightgbm", "xgboost"]:
        click.echo(f"\n🔧 优化 {model_type}...")

        opt_result = advanced_trainer.optimize_hyperparameters(
            X,
            y,
            model_type=model_type,
            n_trials=trials,
            cv_splits=5,
        )

        click.echo(f"✅ {model_type} 优化完成:")
        click.echo(f"   最佳 AUC: {opt_result.best_value:.4f}")
        click.echo(f"   最佳参数: {json.dumps(opt_result.best_params, indent=4)}")

        advanced_trainer.save_results(opt_result, f"{model_type}_opt_result")

        train_result = advanced_trainer.train_with_cv(
            X,
            y,
            model_type=model_type,
            params=opt_result.best_params,
        )

        results[model_type] = {
            "optimization": opt_result.to_dict(),
            "training": train_result.to_dict(),
        }

        click.echo(f"   训练准确率: {train_result.accuracy:.2%}")

    click.echo("\n📊 模型对比:")
    for model_type, result in results.items():
        click.echo(
            f"   {model_type}: AUC={result['optimization']['best_value']:.4f}, ACC={result['training']['accuracy']:.2%}"
        )

    best_model = max(results.keys(), key=lambda k: results[k]["optimization"]["best_value"])
    click.echo(f"\n🏆 最佳模型: {best_model}")

    all_results_path = output_dir / "optimization_results.json"
    with open(all_results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    click.echo(f"📄 所有结果已保存: {all_results_path}")


@ml_cli.command()
@click.option("--days", "-d", default=500, help="训练数据天数")
@click.option("--output", "-out", default="models", help="输出目录")
def ensemble(
    days: int,
    output: str,
) -> None:
    """训练集成模型"""
    click.echo("🔀 开始训练集成模型...")

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    klines_data = db_manager.get_klines_for_ml(days=days)

    if not klines_data:
        click.echo("❌ 没有训练数据")
        return

    stocks_data = _prepare_stocks_data(klines_data)

    trainer = ModelTrainer()
    X, y = trainer.prepare_multi_stock_data(stocks_data)

    click.echo(f"📊 数据准备完成: {len(X)} 样本")

    result = advanced_trainer.train_ensemble(X, y, models=["lightgbm", "xgboost"])

    click.echo("\n📈 集成模型训练完成:")
    click.echo(f"   特征数量: {result.n_features}")
    click.echo(f"   训练样本: {result.n_samples}")
    click.echo(f"   训练时间: {result.training_time:.2f}s")

    advanced_trainer.save_results(result, "ensemble_result")

    click.echo(f"\n📄 结果已保存: {output_dir}/ensemble_result.json")


@ml_cli.command()
@click.option("--model", "-m", default="lightgbm", help="模型类型")
@click.option("--days", "-d", default=250, help="验证天数")
def validate(
    model: str,
    days: int,
) -> None:
    """验证信号有效性"""
    click.echo("📊 开始信号验证...")

    trainer = ModelTrainer(model_type=model)
    trainer.train_from_database(days=500)

    klines_data = db_manager.get_klines_for_ml(days=days)

    if not klines_data:
        click.echo("❌ 没有验证数据")
        return

    predictions_list = []
    price_data = {}

    feature_engineer = FeatureEngineer()

    for code, klines in klines_data.items():
        if len(klines) < 60:
            continue

        df = pd.DataFrame(klines)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df_features = feature_engineer.calculate_all_features(df)

        feature_cols = feature_engineer.feature_names
        X = df_features[feature_cols].fillna(0).replace([float("inf"), float("-inf")], 0)

        predictions = trainer.predictor.predict(X)
        probas = trainer.predictor.predict_proba(X)[:, 1]

        for _i, (date, pred, prob) in enumerate(zip(df["date"], predictions, probas, strict=False)):
            predictions_list.append(
                {
                    "code": code,
                    "date": str(date.date()),
                    "prediction": int(pred),
                    "up_prob": float(prob),
                }
            )

        price_data[code] = df

    predictions_df = pd.DataFrame(predictions_list)

    validator = SignalValidator(prediction_days=5)
    result = validator.validate_signals(predictions_df, price_data)

    click.echo("\n" + "=" * 50)
    click.echo("              信号验证结果")
    click.echo("=" * 50)
    click.echo(f"  总信号数:   {result['total_signals']}")
    click.echo(f"  正确信号:   {result['correct_signals']}")
    click.echo(f"  准确率:     {result['accuracy']:.2f}%")
    click.echo(f"  平均收益:   {result['avg_return']:.2f}%")
    click.echo(f"  信号胜率:   {result['win_rate']:.2f}%")

    if result.get("by_confidence"):
        click.echo("\n  【按置信度分布】")
        for bucket, data in sorted(result["by_confidence"].items()):
            click.echo(
                f"    {bucket}: {data['count']}次, 准确率{data['accuracy']:.1f}%, 平均收益{data['avg_return']:.2f}%"
            )

    click.echo("=" * 50)


def _prepare_stocks_data(klines_data: dict[str, list]) -> dict[str, pd.DataFrame]:
    """准备股票数据"""
    stocks_data = {}

    for code, klines in klines_data.items():
        if len(klines) < 30:
            continue

        df = pd.DataFrame(klines)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        stocks_data[code] = df

    return stocks_data
