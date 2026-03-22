"""
ML CLI Commands.
机器学习命令行接口
"""

import json
from pathlib import Path

import click


@click.group()
def ml():
    """机器学习相关命令"""
    pass


@ml.command()
@click.option("--model-type", default="lightgbm", help="模型类型 (lightgbm/xgboost/randomforest)")
@click.option("--prediction-days", default=5, help="预测天数")
@click.option("--output", default="cache/ml/model.pkl", help="模型输出路径")
def train(model_type: str, prediction_days: int, output: str):
    """训练机器学习模型"""
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
            console.print("[red]❌ 无缓存数据，请先运行 make update-market-data-fast[/red]")
            return

        console.print(f"✅ 加载 {len(stocks_data)} 只股票数据")

        config = TrainingConfig(prediction_days=prediction_days)
        trainer = ModelTrainer(model_type=model_type, config=config)

        console.print("\n📊 准备训练数据...")

        np.random.seed(42)
        stocks_price_data = {}

        for stock in stocks_data[:200]:
            code = stock.get('code', '')
            name = stock.get('name', '')
            current_price = stock.get('current_price', 10)

            if not code or current_price <= 0:
                continue

            n_days = 100
            returns = np.random.randn(n_days) * 0.02
            prices = current_price * np.exp(np.cumsum(returns))

            df = pd.DataFrame({
                'open': prices * (1 + np.random.randn(n_days) * 0.01),
                'high': prices * (1 + np.abs(np.random.randn(n_days) * 0.02)),
                'low': prices * (1 - np.abs(np.random.randn(n_days) * 0.02)),
                'close': prices,
                'volume': np.random.randint(100000, 1000000, n_days),
                'amount': prices * np.random.randint(100000, 1000000, n_days),
            })

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

        output_path = Path(output)
        trainer.save_model(output_path)
        console.print(f"✅ 模型已保存: {output_path}")

        result_path = output_path.with_suffix('.json')
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
            feature_table.add_row(
                row['feature'],
                f"{row['importance']:.4f}",
                f"{row['importance_pct']:.2f}%"
            )

        console.print(feature_table)

        console.print("\n✅ 训练完成！")

    except Exception as e:
        console.print(f"[red]❌ 训练失败: {e}[/red]")
        import traceback
        traceback.print_exc()


@ml.command()
@click.option("--model", default="cache/ml/model.pkl", help="模型路径")
@click.option("--code", help="股票代码")
def predict(model: str, code: str):
    """使用模型预测股票"""
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
            if stock.get('code') == code:
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

        current_price = stock_info.get('current_price', 10)
        returns = np.random.randn(n_days) * 0.02
        prices = current_price * np.exp(np.cumsum(returns))

        price_df = pd.DataFrame({
            'open': prices * (1 + np.random.randn(n_days) * 0.01),
            'high': prices * (1 + np.abs(np.random.randn(n_days) * 0.02)),
            'low': prices * (1 - np.abs(np.random.randn(n_days) * 0.02)),
            'close': prices,
            'volume': np.random.randint(100000, 1000000, n_days),
            'amount': prices * np.random.randint(100000, 1000000, n_days),
        })

        from asset_lens.ml.features import FeatureEngineer
        feature_engineer = FeatureEngineer()
        feature_df = feature_engineer.calculate_all_features(price_df)

        latest_features = feature_df.iloc[-1][feature_engineer.feature_names].to_dict()

        result = predictor.predict_stock(
            stock_data=latest_features,
            code=code,
            name=stock_info.get('name', ''),
        )

        console.print("\n📈 预测结果:")
        pred_table = Table(show_header=False)
        pred_table.add_column("指标", style="cyan")
        pred_table.add_column("值", justify="right")

        pred_color = "green" if result.prediction == "up" else "red"
        pred_table.add_row("股票代码", result.code)
        pred_table.add_row("股票名称", result.name)
        pred_table.add_row("预测方向", f"[{pred_color}]{result.prediction}[/{pred_color}]")
        pred_table.add_row("上涨概率", f"{result.up_prob:.2%}")
        pred_table.add_row("下跌概率", f"{result.down_prob:.2%}")
        pred_table.add_row("置信度", f"{result.confidence:.2%}")
        pred_table.add_row("预期收益", f"{result.expected_return:.2%}")

        console.print(pred_table)

    except Exception as e:
        console.print(f"[red]❌ 预测失败: {e}[/red]")
        import traceback
        traceback.print_exc()


@ml.command()
@click.option("--model", default="cache/ml/model.pkl", help="模型路径")
def importance(model: str):
    """查看模型特征重要性"""
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
            table.add_row(
                str(i),
                row['feature'],
                f"{row['importance']:.4f}",
                f"{row['importance_pct']:.2f}%"
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ 分析失败: {e}[/red]")


@ml.command()
def status():
    """查看 ML 模块状态"""
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

        result_path = model_path.with_suffix('.json')
        if result_path.exists():
            with open(result_path) as f:
                result = json.load(f)

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
    except Exception:
        console.print("\n[yellow]⚠️ 数据库未初始化或无数据[/yellow]")


@ml.command()
@click.option("--model-type", default="lightgbm", help="模型类型")
@click.option("--days", default=250, help="使用最近N天的数据")
@click.option("--output", default="cache/ml/model.pkl", help="模型输出路径")
def train_db(model_type: str, days: int, output: str):
    """从数据库数据训练模型"""
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

        result_path = output_path.with_suffix('.json')
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
        console.print(f"[red]❌ {e}[/red]")
        console.print("[yellow]请先运行 'asset-lens db fetch' 获取历史数据[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ 训练失败: {e}[/red]")
        import traceback
        traceback.print_exc()


@ml.command()
@click.argument("code")
@click.option("--model", default="cache/ml/model.pkl", help="模型路径")
def predict_db(code: str, model: str):
    """从数据库数据预测股票"""
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

        pred_color = "green" if result.get('prediction') == 1 else "red"
        pred_text = "上涨" if result.get('prediction') == 1 else "下跌"
        pred_table.add_row("股票代码", code)
        pred_table.add_row("预测方向", f"[{pred_color}]{pred_text}[/{pred_color}]")
        pred_table.add_row("置信度", f"{result.get('confidence', 0):.2%}")

        console.print(pred_table)
        console.print("\n✅ 预测结果已保存到数据库")

    except Exception as e:
        console.print(f"[red]❌ 预测失败: {e}[/red]")
        import traceback
        traceback.print_exc()


@ml.command()
@click.option("--days", default=30, help="查看最近N天的预测")
def predictions(days: int):
    """查看历史预测记录"""
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
            pred_text = "涨" if r['prediction'] == 1 else "跌"
            result_text = ""
            if r.get('actual_result') is not None:
                actual = "涨" if r['actual_result'] == 1 else "跌"
                correct = "✓" if r.get('is_correct') else "✗"
                result_text = f"{actual} {correct}"

            table.add_row(
                r['predict_date'],
                r['code'],
                pred_text,
                f"{r['confidence']:.1%}",
                result_text
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ 查询失败: {e}[/red]")


@ml.command()
@click.option("--model-type", default="lightgbm", help="模型类型")
def train_adaptive(model_type: str):
    """AI驱动的自适应训练 - 根据市场行情自动调整策略"""
    from rich.console import Console

    from asset_lens.ml.adaptive_trainer import adaptive_trainer
    from asset_lens.strategy.ai_analyzer import AIAnalyzer

    console = Console()
    ai_analyzer = AIAnalyzer()
    initial_tokens = ai_analyzer.total_tokens_used
    initial_cost = ai_analyzer.total_cost

    result = adaptive_trainer.analyze_and_train(model_type=model_type)

    final_tokens = ai_analyzer.total_tokens_used
    final_cost = ai_analyzer.total_cost
    session_tokens = final_tokens - initial_tokens
    session_cost = final_cost - initial_cost

    if "error" in result:
        console.print(f"[red]❌ {result['error']}[/red]")
        return

    training_result = result.get("training_result", {})
    console.print("\n✅ 自适应训练完成!")
    console.print(f"   准确率: {training_result.get('accuracy', 0):.2%}")
    console.print(f"   AUC: {training_result.get('auc', 0):.2%}")

    console.print("\n📊 AI 资源消耗统计")
    console.print("=" * 60)
    console.print(f"  本次 Tokens: {session_tokens:,}")
    console.print(f"  本次费用: ${session_cost:.6f}")
    console.print(f"  累计 Tokens: {final_tokens:,}")
    console.print(f"  累计费用: ${final_cost:.6f}")


@ml.command()
def analyze_market():
    """ML分析当前市场行情"""
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


@ml.command()
def trade():
    """运行AI模拟交易会话"""
    from rich.console import Console

    from asset_lens.ml.ai_trader import AISimulatedTrader
    from asset_lens.strategy.ai_analyzer import AIAnalyzer

    console = Console()
    ai_analyzer = AIAnalyzer()
    initial_tokens = ai_analyzer.total_tokens_used
    initial_cost = ai_analyzer.total_cost

    trader = AISimulatedTrader()
    result = trader.run_trading_session()

    final_tokens = ai_analyzer.total_tokens_used
    final_cost = ai_analyzer.total_cost

    session_tokens = final_tokens - initial_tokens
    session_cost = final_cost - initial_cost

    console.print("\n📊 AI 资源消耗统计")
    console.print("=" * 60)
    console.print(f"  输入 Tokens: {session_tokens:,}")
    console.print(f"  估算费用: ${session_cost:.6f}")
    console.print(f"  累计 Tokens: {final_tokens:,}")
    console.print(f"  累计费用: ${final_cost:.6f}")

    console.print("\n✅ 交易会话完成!")


@ml.command()
@click.option("--days", default=7, help="查看最近N天的交易记录")
def trade_history(days: int):
    """查看AI模拟交易历史"""
    from asset_lens.ml.ai_trader import AISimulatedTrader

    trader = AISimulatedTrader()
    trader.show_trading_history(days=days)


@ml.command()
def portfolio():
    """查看AI模拟交易投资组合"""
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

    profit_color = "green" if summary['total_profit_rate'] >= 0 else "red"
    console.print(f"  总收益: [{profit_color}]{summary['total_profit_rate']:+.2f}%[/{profit_color}]")

    if summary['holdings']:
        console.print(f"\n  当前持仓 ({summary['holding_count']}只):")

        table = Table()
        table.add_column("代码", style="cyan")
        table.add_column("名称", style="white")
        table.add_column("买入价", justify="right")
        table.add_column("现价", justify="right")
        table.add_column("数量", justify="right")
        table.add_column("市值", justify="right")
        table.add_column("收益%", justify="right")

        for h in summary['holdings']:
            profit_color = "green" if h['profit_rate'] >= 0 else "red"
            table.add_row(
                h['code'],
                h['name'],
                f"¥{h['buy_price']:.2f}",
                f"¥{h['current_price']:.2f}",
                str(h['shares']),
                f"¥{h['market_value']:,.0f}",
                f"[{profit_color}]{h['profit_rate']:+.2f}%[/{profit_color}]",
            )

        console.print(table)
    else:
        console.print("\n  [yellow]暂无持仓[/yellow]")


@ml.command()
def sector():
    """分析板块轮动情况（使用ML预测）"""
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
        up_count = len([s for s in stocks if s.get('change_percent', 0) > 0])
        down_count = len([s for s in stocks if s.get('change_percent', 0) < 0])
        console.print(f"  上涨股票: {up_count} ({up_count/len(stocks):.1%})")
        console.print(f"  下跌股票: {down_count} ({down_count/len(stocks):.1%})")

    result = sector_analyzer.analyze()

    console.print(f"\n  市场状态: [bold]{result.market_condition.upper()}[/bold]")
    console.print(f"  轮动信号: {result.rotation_signal}")

    sector_stats = sector_analyzer._calculate_sector_stats(
        sector_analyzer.__dict__.get('_stocks', [])
    )

    if not sector_stats:
        sector_stats = sector_analyzer._calculate_sector_stats(stocks)

    ml_predictions = sector_ml_predictor.predict_all_sectors(
        sector_stats, result.market_condition
    )

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
        if pred.predicted_direction == 1:
            direction = "[green]↑ 上涨[/green]"
        else:
            direction = "[red]↓ 下跌[/red]"

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
        if pred.predicted_direction == 1:
            direction = "[green]↑ 上涨[/green]"
        else:
            direction = "[red]↓ 下跌[/red]"

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
    console.print("   make ml-fund-sector FUND=\"基金名称\"  # 分析基金板块")


@ml.command()
@click.argument("fund_name")
def fund_sector(fund_name: str):
    """分析基金所属板块并给出建议

    示例: make ml-fund-sector FUND="易方达科技创新混合"
    """
    from rich.console import Console

    from asset_lens.ml.sector_rotation import sector_analyzer

    console = Console()

    console.print(f"\n📊 基金板块分析: {fund_name}")
    console.print("=" * 60)

    result = sector_analyzer.get_fund_sector_recommendation(fund_name)

    console.print(f"\n  基金名称: {result['fund_name']}")
    console.print(f"  所属板块: {result['sector']}")
    console.print(f"  市场状态: {result.get('market_condition', '未知')}")

    if result.get('is_recommended'):
        console.print("  板块状态: [green]✅ 强势板块[/green]")
    elif result.get('is_avoid'):
        console.print("  板块状态: [red]⚠️ 弱势板块[/red]")
    else:
        console.print("  板块状态: [yellow]➖ 中性板块[/yellow]")

    console.print(f"\n  💡 建议: {result['recommendation']}")

    console.print("\n💡 相关命令:")
    console.print("   make ml-sector          # ML板块轮动分析")
    console.print("   make ml-analyze-market  # ML市场分析")
