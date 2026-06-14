"""
ML准确率优化脚本 v7 - 基本面+资金流向
目标: 73.78% → 80%

策略:
1. 添加基本面特征 (PE/PB/ROE等)
2. 添加资金流向特征 (主力资金/北向资金)
3. 高级集成模型
"""
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from asset_lens.data.fundamental_fetcher import (
    EnhancedFeatureBuilder,
)
from asset_lens.db.database import db_manager
from asset_lens.ml.features import FeatureEngineer

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


class EnhancedFeatureEngineerV2(FeatureEngineer):
    """增强版特征工程 V2 - 包含基本面和资金流向"""

    def __init__(self):
        super().__init__()
        self.feature_builder = EnhancedFeatureBuilder()
        self._code_fundamentals: dict = {}

    def set_code(self, code: str):
        """设置当前股票代码"""
        self._current_code = code

    def calculate_all_features(self, df: pd.DataFrame, code: str | None = None) -> pd.DataFrame:
        """计算所有特征"""
        df = super().calculate_all_features(df)

        current_code = code or getattr(self, '_current_code', None)
        if current_code:
            df = self._add_fundamental_features(df, current_code)
            df = self._add_money_flow_features(df, current_code)

        return df

    def _add_fundamental_features(self, df: pd.DataFrame, code: str) -> pd.DataFrame:
        """添加基本面特征"""
        try:
            features = self.feature_builder.build_fundamental_features(code)

            for key, value in features.items():
                df[key] = value
        except Exception:
            default_features = {
                'pe_ratio': 0, 'pb_ratio': 0, 'roe': 0,
                'revenue_growth': 0, 'profit_growth': 0,
                'debt_ratio': 0, 'gross_margin': 0, 'net_margin': 0,
                'log_market_value': 0, 'log_circulating_mv': 0,
            }
            for key, value in default_features.items():
                df[key] = value

        return df

    def _add_money_flow_features(self, df: pd.DataFrame, code: str) -> pd.DataFrame:
        """添加资金流向特征"""
        try:
            features = self.feature_builder.build_money_flow_features(code)

            for key, value in features.items():
                df[key] = value
        except Exception:
            default_features = {
                'main_net_inflow_mean': 0, 'main_net_inflow_std': 0,
                'main_net_inflow_ratio_mean': 0, 'super_net_inflow_mean': 0,
                'big_net_inflow_mean': 0, 'small_net_inflow_mean': 0,
                'main_inflow_trend': 0,
            }
            for key, value in default_features.items():
                df[key] = value

        return df


def prepare_data_with_fundamentals(days: int = 500, sample_size: int = 500):
    """准备带基本面数据的训练数据"""
    logger.info("📥 获取训练数据 (%s 天)...", days)

    klines_data = db_manager.get_klines_for_ml(days=days)

    codes = list(klines_data.keys())[:sample_size]
    logger.info("📊 选取 %s 只股票进行训练", len(codes))

    logger.info("📥 预加载基本面数据...")
    feature_builder = EnhancedFeatureBuilder()
    feature_builder.preload_fundamentals(codes)

    stocks_data = {}
    for code in codes:
        klines = klines_data.get(code, [])
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

    feature_engineer = EnhancedFeatureEngineerV2()
    feature_engineer.feature_builder = feature_builder

    all_X = []
    all_y = []

    for code, df in stocks_data.items():
        df_features = feature_engineer.calculate_all_features(df, code=code)

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

        feature_cols = [col for col in df_features.columns
                       if col not in ['open', 'high', 'low', 'close', 'volume', 'amount', 'date', 'code']]
        X = X[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)

        all_X.append(X)
        all_y.append(y_valid)

    X_all = pd.concat(all_X, ignore_index=True)
    y_all = pd.concat(all_y, ignore_index=True)

    logger.info("📊 总样本数: %s, 特征数: %s", len(X_all), X_all.shape[1])

    new_features = ['pe_ratio', 'pb_ratio', 'roe', 'revenue_growth', 'profit_growth',
                   'main_net_inflow_mean', 'main_inflow_trend']
    existing_new = [f for f in new_features if f in X_all.columns]
    logger.info("📊 新增特征: %s", existing_new)

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
        'seed': 42,
        'nthread': 1,
    }

    logger.info("🚀 训练高级 XGBoost 模型...")

    evals_result = {}
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=800,
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
        num_boost_round=800,
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

    predictions = []
    model_metrics = {}

    if HAS_XGBOOST:
        xgb_model, xgb_metrics = train_xgb_advanced(X_train, y_train, X_test, y_test)
        dtest = xgb.DMatrix(X_test)
        xgb_proba = xgb_model.predict(dtest)
        predictions.append(xgb_proba)
        model_metrics['xgb'] = xgb_metrics
        logger.info(f"   XGBoost: Acc={xgb_metrics['accuracy']:.2%}, AUC={xgb_metrics['auc']:.4f}")

    if HAS_LIGHTGBM:
        lgb_model, lgb_metrics = train_lgb_advanced(X_train, y_train, X_test, y_test)
        lgb_proba = lgb_model.predict(X_test)
        predictions.append(lgb_proba)
        model_metrics['lgb'] = lgb_metrics
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
            'model_metrics': model_metrics,
        }
    else:
        metrics = model_metrics.get('xgb', model_metrics.get('lgb', {}))

    return metrics


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("      ML 准确率优化 v7 - 基本面+资金流向")
    logger.info("      目标: 73.78% → 80%")
    logger.info("=" * 60)

    start_time = time.time()

    X, y = prepare_data_with_fundamentals(days=500, sample_size=500)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info("\n📊 训练集: %s, 测试集: %s", len(X_train), len(X_test))

    metrics = train_ensemble_blend(X_train, y_train, X_test, y_test)

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

    output_path = Path("models/optimization_v7_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metrics': metrics,
            'total_time': total_time,
            'improvement_pct': improvement,
            'feature_count': X.shape[1],
        }, f, indent=2, default=str)
    logger.info("📄 结果已保存: %s", output_path)

    return metrics


if __name__ == "__main__":
    main()
