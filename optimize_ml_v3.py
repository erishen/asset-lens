"""
ML准确率优化脚本 v3
目标: 72% → 80%

优化策略:
1. 使用Optuna优化后的最佳参数
2. 增强特征工程
3. Stacking集成
4. 特征选择
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import StackingClassifier, VotingClassifier
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from asset_lens.db.database import db_manager
from optimize_comprehensive import EnhancedFeatureEngineer

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False


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
    
    feature_engineer = EnhancedFeatureEngineer()
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


def select_features(X_train, y_train, X_test, k=80):
    """特征选择"""
    print(f"🔍 特征选择: {X_train.shape[1]} → {k}")
    
    selector = SelectKBest(score_func=mutual_info_classif, k=min(k, X_train.shape[1]))
    X_train_selected = selector.fit_transform(X_train, y_train)
    X_test_selected = selector.transform(X_test)
    
    selected_indices = selector.get_support(indices=True)
    selected_features = [X_train.columns[i] for i in selected_indices]
    
    return pd.DataFrame(X_train_selected, columns=selected_features), \
           pd.DataFrame(X_test_selected, columns=selected_features), selected_features


def train_stacking_model(X_train, y_train, X_test, y_test):
    """训练Stacking集成模型"""
    
    estimators = []
    
    if HAS_LIGHTGBM:
        lgb_model = lgb.LGBMClassifier(
            n_estimators=390,
            max_depth=11,
            learning_rate=0.0775,
            num_leaves=227,
            min_child_samples=9,
            subsample=0.97,
            colsample_bytree=0.811,
            reg_alpha=0.00109,
            reg_lambda=0.0018,
            random_state=42,
            verbose=-1,
            n_jobs=1,
        )
        estimators.append(('lgb', lgb_model))
    
    if HAS_XGBOOST:
        xgb_model = xgb.XGBClassifier(
            n_estimators=306,
            max_depth=11,
            learning_rate=0.0944,
            subsample=0.884,
            colsample_bytree=0.703,
            reg_alpha=0.0805,
            reg_lambda=0.0369,
            min_child_weight=8,
            gamma=0.0969,
            random_state=42,
            eval_metric='logloss',
            n_jobs=1,
        )
        estimators.append(('xgb', xgb_model))
    
    if HAS_CATBOOST:
        cat_model = CatBoostClassifier(
            iterations=300,
            depth=10,
            learning_rate=0.08,
            l2_leaf_reg=3,
            random_state=42,
            verbose=0,
        )
        estimators.append(('cat', cat_model))
    
    print("🚀 训练 Stacking 集成模型...")
    
    final_estimator = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    
    model = StackingClassifier(
        estimators=estimators,
        final_estimator=final_estimator,
        cv=3,
        stack_method='predict_proba',
        n_jobs=1,
    )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'auc': roc_auc_score(y_test, y_proba),
    }
    
    return model, metrics


def train_voting_model(X_train, y_train, X_test, y_test):
    """训练Voting集成模型"""
    
    estimators = []
    
    if HAS_LIGHTGBM:
        lgb_model = lgb.LGBMClassifier(
            n_estimators=390,
            max_depth=11,
            learning_rate=0.0775,
            num_leaves=227,
            min_child_samples=9,
            subsample=0.97,
            colsample_bytree=0.811,
            reg_alpha=0.00109,
            reg_lambda=0.0018,
            random_state=42,
            verbose=-1,
            n_jobs=1,
        )
        estimators.append(('lgb', lgb_model))
    
    if HAS_XGBOOST:
        xgb_model = xgb.XGBClassifier(
            n_estimators=306,
            max_depth=11,
            learning_rate=0.0944,
            subsample=0.884,
            colsample_bytree=0.703,
            reg_alpha=0.0805,
            reg_lambda=0.0369,
            min_child_weight=8,
            gamma=0.0969,
            random_state=42,
            eval_metric='logloss',
            n_jobs=1,
        )
        estimators.append(('xgb', xgb_model))
    
    if HAS_CATBOOST:
        cat_model = CatBoostClassifier(
            iterations=300,
            depth=10,
            learning_rate=0.08,
            l2_leaf_reg=3,
            random_state=42,
            verbose=0,
        )
        estimators.append(('cat', cat_model))
    
    print("🚀 训练 Voting 集成模型...")
    
    model = VotingClassifier(estimators=estimators, voting='soft')
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'auc': roc_auc_score(y_test, y_proba),
    }
    
    return model, metrics


def cross_validate(X, y, n_splits=3):
    """交叉验证"""
    print(f"\n📊 进行 {n_splits} 折交叉验证...")
    
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    scores = {'accuracy': [], 'auc': []}
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        _, metrics = train_voting_model(X_train, y_train, X_val, y_val)
        
        scores['accuracy'].append(metrics['accuracy'])
        scores['auc'].append(metrics['auc'])
        
        print(f"   Fold {fold + 1}: Acc={metrics['accuracy']:.2%}, AUC={metrics['auc']:.4f}")
    
    return {
        'accuracy_mean': np.mean(scores['accuracy']),
        'accuracy_std': np.std(scores['accuracy']),
        'auc_mean': np.mean(scores['auc']),
        'auc_std': np.std(scores['auc']),
    }


def main():
    """主函数"""
    print("=" * 60)
    print("      ML 准确率优化 v3 (目标: 72% → 80%)")
    print("=" * 60)
    
    start_time = time.time()
    
    X, y = prepare_data(days=500)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📊 训练集: {len(X_train)}, 测试集: {len(X_test)}")
    
    model, metrics = train_voting_model(X_train, y_train, X_test, y_test)
    
    print(f"\n📈 模型训练结果:")
    print(f"   准确率:   {metrics['accuracy']:.2%}")
    print(f"   精确率:   {metrics['precision']:.2%}")
    print(f"   召回率:   {metrics['recall']:.2%}")
    print(f"   F1 分数:  {metrics['f1_score']:.2%}")
    print(f"   AUC:      {metrics['auc']:.4f}")
    
    total_time = time.time() - start_time
    print(f"\n⏱️ 总耗时: {total_time:.1f} 秒")
    
    improvement = (metrics['accuracy'] - 0.72) / 0.72 * 100
    print(f"\n📈 准确率提升: {metrics['accuracy']:.2%} (相比基准 72% {'↑' if improvement > 0 else '↓'}{abs(improvement):.1f}%)")
    
    output_path = Path("models/optimization_v3_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'model_metrics': metrics,
            'total_time': total_time,
            'improvement_pct': improvement,
        }, f, indent=2, default=str)
    print(f"📄 结果已保存: {output_path}")
    
    return metrics


if __name__ == "__main__":
    main()
