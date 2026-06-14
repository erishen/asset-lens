"""
ML准确率优化脚本 v4 - 激进优化
目标: 72% → 80%

策略:
1. 使用更多训练数据 (1000天)
2. 更深的模型
3. 更多迭代次数
"""
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from optimize_comprehensive import EnhancedFeatureEngineer
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from asset_lens.db.database import db_manager

logger = logging.getLogger(__name__)

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


def prepare_data(days: int = 1000):
    """准备训练数据"""
    logger.info("📥 获取训练数据 (%s 天)...", days)

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

    logger.info("📊 成功加载 %s 只股票的数据", len(stocks_data))

    feature_engineer = EnhancedFeatureEngineer()
    all_X = []
    all_y = []

    for df in stocks_data.values():
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

    logger.info("📊 总样本数: %s, 特征数: %s", len(X_all), X_all.shape[1])

    return X_all, y_all


def train_model(X_train, y_train, X_test, y_test):
    """训练模型 - 使用更激进的参数"""

    estimators = []

    if HAS_LIGHTGBM:
        lgb_model = lgb.LGBMClassifier(
            n_estimators=600,
            max_depth=12,
            learning_rate=0.05,
            num_leaves=255,
            min_child_samples=5,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.005,
            reg_lambda=0.005,
            random_state=42,
            verbose=-1,
            n_jobs=1,
        )
        estimators.append(('lgb', lgb_model))

    if HAS_XGBOOST:
        xgb_model = xgb.XGBClassifier(
            n_estimators=500,
            max_depth=10,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.005,
            reg_lambda=0.005,
            min_child_weight=3,
            gamma=0.05,
            random_state=42,
            eval_metric='logloss',
            n_jobs=1,
        )
        estimators.append(('xgb', xgb_model))

    if HAS_CATBOOST:
        cat_model = CatBoostClassifier(
            iterations=500,
            depth=10,
            learning_rate=0.05,
            l2_leaf_reg=2,
            random_state=42,
            verbose=0,
        )
        estimators.append(('cat', cat_model))

    logger.info("🚀 训练激进优化模型...")

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


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("      ML 准确率优化 v4 - 激进优化 (目标: 72% → 80%)")
    logger.info("=" * 60)

    start_time = time.time()

    X, y = prepare_data(days=1000)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info("\n📊 训练集: %s, 测试集: %s", len(X_train), len(X_test))

    _model, metrics = train_model(X_train, y_train, X_test, y_test)

    logger.info("📈 模型训练结果:")
    logger.info(f"   准确率:   {metrics['accuracy']:.2%}")
    logger.info(f"   精确率:   {metrics['precision']:.2%}")
    logger.info(f"   召回率:   {metrics['recall']:.2%}")
    logger.info(f"   F1 分数:  {metrics['f1_score']:.2%}")
    logger.info(f"   AUC:      {metrics['auc']:.4f}")

    total_time = time.time() - start_time
    logger.info(f"⏱️ 总耗时: {total_time:.1f} 秒")

    improvement = (metrics['accuracy'] - 0.72) / 0.72 * 100
    logger.info(f"📈 准确率提升: {metrics['accuracy']:.2%} (相比基准 72% {'↑' if improvement > 0 else '↓'}{abs(improvement):.1f}%)")

    output_path = Path("models/optimization_v4_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'model_metrics': metrics,
            'total_time': total_time,
            'improvement_pct': improvement,
        }, f, indent=2, default=str)
    logger.info("📄 结果已保存: %s", output_path)

    return metrics


if __name__ == "__main__":
    main()
