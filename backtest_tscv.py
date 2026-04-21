"""
使用时间序列交叉验证优化后的模型进行回测
"""
import json
from pathlib import Path

import pandas as pd

from asset_lens.db.database import db_manager
from asset_lens.ml.backtest import BacktestEngine, BacktestConfig, SignalValidator, generate_backtest_report
from asset_lens.ml.features import FeatureEngineer
from asset_lens.ml.predictor import StockPredictor

def main():
    print("📊 开始回测时间序列交叉验证优化后的模型...")
    
    model_path = Path("models/lightgbm_tscv_model.joblib")
    predictor = StockPredictor(model_type="lightgbm", model_path=model_path)
    
    print("📈 获取回测数据...")
    klines_data = db_manager.get_klines_for_ml(days=250)
    
    predictions_list = []
    price_data = {}
    
    feature_engineer = FeatureEngineer()
    
    for code, klines in klines_data.items():
        if len(klines) < 60:
            continue
        
        df = pd.DataFrame(klines)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        for col in ['open', 'close', 'high', 'low', 'volume', 'amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df_features = feature_engineer.calculate_all_features(df)
        
        feature_cols = feature_engineer.feature_names
        X = df_features[feature_cols].fillna(0).replace([float('inf'), float('-inf')], 0)
        
        predictions = predictor.predict(X)
        probas = predictor.predict_proba(X)[:, 1]
        
        for i, (date, pred, prob) in enumerate(zip(df['date'], predictions, probas)):
            predictions_list.append({
                'code': code,
                'date': str(date.date()),
                'prediction': int(pred),
                'up_prob': float(prob),
            })
        
        price_data[code] = df
    
    if not predictions_list:
        print("❌ 没有生成预测信号")
        return
    
    predictions_df = pd.DataFrame(predictions_list)
    
    print(f"📊 运行回测引擎...")
    
    config = BacktestConfig(initial_capital=100000, position_size=0.1)
    
    engine = BacktestEngine(config)
    result = engine.run_backtest(predictions_df, price_data)
    
    print("\n" + "=" * 50)
    print("         回测结果 (TSCV 优化后)")
    print("=" * 50)
    print(f"  总收益率:   {result.total_return:.2f}%")
    print(f"  年化收益:   {result.annual_return:.2f}%")
    print(f"  最大回撤:   {result.max_drawdown:.2f}%")
    print(f"  夏普比率:   {result.sharpe_ratio:.2f}")
    print(f"  胜率:       {result.win_rate:.2f}%")
    print(f"  盈亏比:     {result.profit_factor:.2f}")
    print(f"  总交易:     {result.total_trades} 次")
    print("=" * 50)
    
    validator = SignalValidator()
    signal_result = validator.validate_signals(predictions_df, price_data)
    
    print(f"\n📊 信号验证:")
    print(f"   总信号数:   {signal_result['total_signals']}")
    print(f"   准确率:     {signal_result['accuracy']:.2f}%")
    print(f"   平均收益:   {signal_result['avg_return']:.2f}%")
    
    report_path = Path("reports/backtest_report_tscv.txt")
    report = generate_backtest_report(result, signal_result, report_path)
    
    print(f"\n📄 报告已保存: {report_path}")
    
    result_json_path = Path("reports/backtest_result_tscv.json")
    with open(result_json_path, 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"📄 结果已保存: {result_json_path}")

if __name__ == "__main__":
    main()
