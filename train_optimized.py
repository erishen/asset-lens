"""
使用优化后的参数训练模型并回测
"""
import json
from pathlib import Path

from asset_lens.db.database import db_manager
from asset_lens.ml.trainer import ModelTrainer

def main():
    print("🚀 使用优化参数训练模型...")
    
    opt_result_path = Path("models/lightgbm_optimization.json")
    with open(opt_result_path) as f:
        opt_result = json.load(f)
    
    best_params = opt_result["best_params"]
    print(f"📊 最佳参数: {json.dumps(best_params, indent=2)}")
    
    trainer = ModelTrainer(model_type="lightgbm")
    
    print("📥 从数据库获取训练数据...")
    klines_data = db_manager.get_klines_for_ml(days=500)
    
    stocks_data = {}
    for code, klines in klines_data.items():
        if len(klines) < 30:
            continue
        
        import pandas as pd
        df = pd.DataFrame(klines)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        for col in ['open', 'close', 'high', 'low', 'volume', 'amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        stocks_data[code] = df
    
    print(f"📊 成功加载 {len(stocks_data)} 只股票的数据")
    
    X, y = trainer.prepare_multi_stock_data(stocks_data)
    
    result = trainer.train(X, y, **best_params)
    
    print(f"\n📈 训练结果:")
    print(f"   准确率:   {result.accuracy:.2%}")
    print(f"   精确率:   {result.precision:.2%}")
    print(f"   召回率:   {result.recall:.2%}")
    print(f"   F1 分数:  {result.f1_score:.2%}")
    print(f"   AUC:      {result.auc:.4f}")
    
    model_path = Path("models/lightgbm_optimized_model.joblib")
    trainer.save_model(model_path)
    print(f"\n💾 模型已保存: {model_path}")
    
    result_path = Path("models/lightgbm_optimized_result.json")
    trainer.save_training_result(result, result_path)
    print(f"📄 结果已保存: {result_path}")

if __name__ == "__main__":
    main()
