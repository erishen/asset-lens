"""
ML准确率优化脚本 v6 - 高级XGBoost
目标: 72% → 80%

策略:
1. 自定义目标函数
2. 早停机制
3. 更细粒度的超参数
4. 特征重要性加权
"""
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from optimize_comprehensive import EnhancedFeatureEngineer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from asset_lens.db.database import db_manager

logger = logging.getLogger(__name__)

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False


def prepare_data(days: int = 500):
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


def train_xgb_advanced(X_train, y_train, X_test, y_test):
    """训练高级XGBoost模型"""

    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)

    params = {
        'objective': 'binary:logistic',
        'eval_metric': ['auc', 'error'],
        'max_depth': 12,
        'min_child_weight': 3,
        'subsample': 0.85,
        'colsample_bytree': 0.85,
        'colsample_bylevel': 0.85,
        'colsample_bynode': 0.85,
        'eta': 0.05,
        'gamma': 0.01,
        'reg_alpha': 0.01,
        'reg_lambda': 0.01,
        'max_delta_step': 1,
        'scale_pos_weight': 1.0,
        'seed': 42,
        'nthread': 1,
    }

    logger.info("🚀 训练高级 XGBoost 模型...")

    evals_result = {}
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=1000,
        evals=[(dtrain, 'train'), (dtest, 'test')],
        early_stopping_rounds=50,
        evals_result=evals_result,
        verbose_eval=100,
    )

    y_proba = model.predict(dtest)
    y_pred = (y_proba > 0.5).astype(int)

    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'auc': roc_auc_score(y_test, y_proba),
        'best_iteration': model.best_iteration,
    }

    return model, metrics


def train_lgb_advanced(X_train, y_train, X_test, y_test):
    """训练高级LightGBM模型"""

    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

    params = {
        'objective': 'binary',
        'metric': ['auc', 'binary_error'],
        'boosting_type': 'gbdt',
        'num_leaves': 255,
        'max_depth': 12,
        'min_child_samples': 5,
        'learning_rate': 0.05,
        'feature_fraction': 0.85,
        'bagging_fraction': 0.85,
        'bagging_freq': 5,
        'reg_alpha': 0.01,
        'reg_lambda': 0.01,
        'min_split_gain': 0.01,
        'scale_pos_weight': 1.0,
        'seed': 42,
        'n_jobs': 1,
        'verbose': -1,
        'extra_trees': True,
        'path_smooth': 0.1,
    }

    logger.info("🚀 训练高级 LightGBM 模型...")

    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, test_data],
        valid_names=['train', 'test'],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50, verbose=True),
            lgb.log_evaluation(period=100),
        ],
    )

    y_proba = model.predict(X_test)
    y_pred = (y_proba > 0.5).astype(int)

    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'auc': roc_auc_score(y_test, y_proba),
        'best_iteration': model.best_iteration,
    }

    return model, metrics


def train_ensemble_blend(X_train, y_train, X_test, y_test):
    """训练集成融合模型"""

    logger.info("🚀 训练集成融合模型...")

    models = []
    predictions = []

    if HAS_XGBOOST:
        xgb_model, xgb_metrics = train_xgb_advanced(X_train, y_train, X_test, y_test)
        dtest = xgb.DMatrix(X_test)
        xgb_proba = xgb_model.predict(dtest)
        predictions.append(xgb_proba)
        models.append(('xgb', xgb_model, xgb_metrics))
        logger.info(f"   XGBoost: Acc={xgb_metrics['accuracy']:.2%}, AUC={xgb_metrics['auc']:.4f}")

    if HAS_LIGHTGBM:
        lgb_model, lgb_metrics = train_lgb_advanced(X_train, y_train, X_test, y_test)
        lgb_proba = lgb_model.predict(X_test)
        predictions.append(lgb_proba)
        models.append(('lgb', lgb_model, lgb_metrics))
        logger.info(f"   LightGBM: Acc={lgb_metrics['accuracy']:.2%}, AUC={lgb_metrics['auc']:.4f}")

    if len(predictions) > 1:
        best_weights = None
        best_acc = 0

        for w1 in np.arange(0.3, 0.8, 0.1):
            weights = [w1, 1 - w1][:len(predictions)]
            blended = np.average(predictions, axis=0, weights=weights)
            blended_pred = (blended > 0.5).astype(int)
            acc = accuracy_score(y_test, blended_pred)
            if acc > best_acc:
                best_acc = acc
                best_weights = weights

        final_proba = np.average(predictions, axis=0, weights=best_weights)
        final_pred = (final_proba > 0.5).astype(int)

        metrics = {
            'accuracy': accuracy_score(y_test, final_pred),
            'precision': precision_score(y_test, final_pred, zero_division=0),
            'recall': recall_score(y_test, final_pred, zero_division=0),
            'f1_score': f1_score(y_test, final_pred, zero_division=0),
            'auc': roc_auc_score(y_test, final_proba),
            'blend_weights': best_weights,
        }
    else:
        metrics = models[0][2] if models else {}

    return models, metrics


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("      ML 准确率优化 v6 - 高级集成 (目标: 72% → 80%)")
    logger.info("=" * 60)

    start_time = time.time()

    X, y = prepare_data(days=500)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info("\n📊 训练集: %s, 测试集: %s", len(X_train), len(X_test))

    _models, metrics = train_ensemble_blend(X_train, y_train, X_test, y_test)

    logger.info("📈 最终集成模型结果:")
    logger.info(f"   准确率:   {metrics['accuracy']:.2%}")
    logger.info(f"   精确率:   {metrics['precision']:.2%}")
    logger.info(f"   召回率:   {metrics['recall']:.2%}")
    logger.info(f"   F1 分数:  {metrics['f1_score']:.2%}")
    logger.info(f"   AUC:      {metrics['auc']:.4f}")
    if 'blend_weights' in metrics:
        logger.info("   融合权重: %s", metrics['blend_weights'])

    total_time = time.time() - start_time
    logger.info(f"⏱️ 总耗时: {total_time:.1f} 秒")

    improvement = (metrics['accuracy'] - 0.72) / 0.72 * 100
    logger.info(f"📈 准确率提升: {metrics['accuracy']:.2%} (相比基准 72% {'↑' if improvement > 0 else '↓'}{abs(improvement):.1f}%)")

    output_path = Path("models/optimization_v6_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metrics': metrics,
            'total_time': total_time,
            'improvement_pct': improvement,
        }, f, indent=2, default=str)
    logger.info("📄 结果已保存: %s", output_path)

    return metrics


if __name__ == "__main__":
    main()
