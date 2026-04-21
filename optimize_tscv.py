"""
时间序列交叉验证优化脚本
使用 TimeSeriesSplit 避免数据泄露
"""
import json
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from asset_lens.db.database import db_manager
from asset_lens.ml.features import FeatureEngineer


def prepare_data(days: int = 500):
    """准备训练数据"""
    print(f"📥 获取训练数据 ({days} 天)...")
    
    klines_data = db_manager.get_klines_for_ml(days=days)
    
    stocks_data = {}
    for code, klines in klines_data.items():
        if len(klines) < 60:
            continue
        
        df = pd.DataFrame(klines)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        for col in ['open', 'close', 'high', 'low', 'volume', 'amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        stocks_data[code] = df
    
    print(f"📊 成功加载 {len(stocks_data)} 只股票的数据")
    
    feature_engineer = FeatureEngineer()
    all_X = []
    all_y = []
    
    for code, df in stocks_data.items():
        df_features = feature_engineer.calculate_all_features(df)
        
        future_return = df_features['close'].shift(-5) / df_features['close'] - 1
        
        def label_return(r):
            if pd.isna(r):
                return -1
            if r >= 0.02:
                return 1
            elif r <= -0.02:
                return 0
            else:
                return -1
        
        y = future_return.apply(label_return)
        
        valid_mask = y != -1
        X = df_features[valid_mask].copy()
        y_valid = y[valid_mask].copy()
        
        feature_cols = feature_engineer.feature_names
        X = X[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
        
        all_X.append(X)
        all_y.append(y_valid)
    
    X_all = pd.concat(all_X, ignore_index=True)
    y_all = pd.concat(all_y, ignore_index=True)
    
    print(f"📊 总样本数: {len(X_all)}, 特征数: {X_all.shape[1]}")
    
    return X_all, y_all


def objective(trial, X, y, n_splits=5):
    """Optuna 优化目标函数"""
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 500),
        'max_depth': trial.suggest_int('max_depth', 4, 15),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
        'num_leaves': trial.suggest_int('num_leaves', 20, 300),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-4, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-4, 10.0, log=True),
        'min_split_gain': trial.suggest_float('min_split_gain', 0.0, 0.2),
        'random_state': 42,
        'verbose': -1,
        'n_jobs': -1,
    }
    
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = []
    
    for train_idx, val_idx in tscv.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        model = lgb.LGBMClassifier(**params)
        model.fit(X_train, y_train)
        
        y_proba = model.predict_proba(X_val)[:, 1]
        
        try:
            score = roc_auc_score(y_val, y_proba)
            scores.append(score)
        except ValueError:
            scores.append(0.5)
    
    return np.mean(scores)


def run_optimization(n_trials: int = 50, n_splits: int = 5):
    """运行优化"""
    print("🚀 开始时间序列交叉验证优化...")
    
    X, y = prepare_data(days=500)
    
    print(f"\n🔧 开始 Optuna 优化 ({n_trials} 次, {n_splits} 折)...")
    start_time = time.time()
    
    study = optuna.create_study(
        direction='maximize',
        study_name='lightgbm_tscv_optimization',
    )
    
    study.optimize(
        lambda trial: objective(trial, X, y, n_splits),
        n_trials=n_trials,
        show_progress_bar=True,
    )
    
    optimization_time = time.time() - start_time
    
    print(f"\n✅ 优化完成!")
    print(f"   最佳 AUC: {study.best_value:.4f}")
    print(f"   优化时间: {optimization_time:.1f} 秒")
    print(f"   最佳参数:")
    for key, value in study.best_params.items():
        print(f"     {key}: {value}")
    
    result = {
        'best_params': study.best_params,
        'best_value': study.best_value,
        'n_trials': n_trials,
        'n_splits': n_splits,
        'optimization_time': optimization_time,
        'param_importance': optuna.importance.get_param_importances(study),
    }
    
    output_path = Path("models/lightgbm_tscv_optimization.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n📄 结果已保存: {output_path}")
    
    return study.best_params, study.best_value


def train_with_best_params(params: dict):
    """使用最佳参数训练模型"""
    from asset_lens.ml.trainer import ModelTrainer
    
    print("\n🚀 使用优化参数训练模型...")
    
    trainer = ModelTrainer(model_type="lightgbm")
    
    result = trainer.train_from_database(days=500, **params)
    
    print(f"\n📈 训练结果:")
    print(f"   准确率:   {result.accuracy:.2%}")
    print(f"   精确率:   {result.precision:.2%}")
    print(f"   召回率:   {result.recall:.2%}")
    print(f"   F1 分数:  {result.f1_score:.2%}")
    print(f"   AUC:      {result.auc:.4f}")
    
    model_path = Path("models/lightgbm_tscv_model.joblib")
    trainer.save_model(model_path)
    print(f"\n💾 模型已保存: {model_path}")
    
    result_path = Path("models/lightgbm_tscv_result.json")
    trainer.save_training_result(result, result_path)
    print(f"📄 结果已保存: {result_path}")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials', type=int, default=50, help='优化试验次数')
    parser.add_argument('--splits', type=int, default=5, help='交叉验证折数')
    args = parser.parse_args()
    
    best_params, best_value = run_optimization(
        n_trials=args.trials,
        n_splits=args.splits,
    )
    
    train_with_best_params(best_params)
