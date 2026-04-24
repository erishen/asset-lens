"""
ML准确率优化脚本 v2
目标: 72% → 80%

优化策略:
1. 特征工程增强 - 添加基本面因子、市场因子、时序特征
2. 模型优化 - CatBoost集成、Stacking、深度学习
3. 数据优化 - 样本平衡、数据增强
4. 标签优化 - 三分类、回归辅助
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import StackingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, TimeSeriesSplit, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

from asset_lens.db.database import db_manager
from asset_lens.ml.backtest import BacktestConfig, BacktestEngine, generate_backtest_report
from asset_lens.ml.features import FeatureEngineer

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


class AdvancedFeatureEngineer(FeatureEngineer):
    """高级特征工程 - 添加更多预测性特征"""

    def calculate_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = super().calculate_all_features(df)
        df = self._add_price_patterns(df)
        df = self._add_time_features(df)
        df = self._add_statistical_moments(df)
        df = self._add_cross_sectional(df)
        df = self._add_lag_features(df)
        return df

    def _add_price_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """价格形态特征"""
        df['body_size'] = abs(df['close'] - df['open']) / df['close']
        df['upper_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
        df['lower_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']
        
        df['is_bullish'] = (df['close'] > df['open']).astype(int)
        df['is_doji'] = (df['body_size'] < 0.01).astype(int)
        df['is_hammer'] = ((df['lower_wick'] > 2 * df['body_size']) & 
                          (df['upper_wick'] < df['body_size'])).astype(int)
        df['is_shooting_star'] = ((df['upper_wick'] > 2 * df['body_size']) & 
                                  (df['lower_wick'] < df['body_size'])).astype(int)
        
        df['consecutive_up'] = (df['is_bullish'] * (df['is_bullish'].groupby(
            (df['is_bullish'] != df['is_bullish'].shift()).cumsum()).cumsum() + 1))
        df['consecutive_down'] = ((1 - df['is_bullish']) * ((1 - df['is_bullish']).groupby(
            ((1 - df['is_bullish']) != (1 - df['is_bullish']).shift()).cumsum()).cumsum() + 1))
        
        return df

    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """时间特征"""
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_of_month'] = df['date'].dt.day
            df['month'] = df['date'].dt.month
            df['quarter'] = df['date'].dt.quarter
            df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
            df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
            df['is_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)
        return df

    def _add_statistical_moments(self, df: pd.DataFrame) -> pd.DataFrame:
        """统计矩特征"""
        for period in [10, 20, 60]:
            returns = df['close'].pct_change()
            df[f'skewness_{period}'] = returns.rolling(window=period).skew()
            df[f'kurtosis_{period}'] = returns.rolling(window=period).kurt()
            df[f'median_{period}'] = df['close'].rolling(window=period).median()
            df[f'mad_{period}'] = (df['close'] - df[f'median_{period}']).abs().rolling(window=period).mean()
        
        return df

    def _add_cross_sectional(self, df: pd.DataFrame) -> pd.DataFrame:
        """横截面特征"""
        for period in [5, 10, 20]:
            df[f'rank_close_{period}'] = df['close'].rolling(window=period).rank(pct=True)
            df[f'rank_volume_{period}'] = df['volume'].rolling(window=period).rank(pct=True)
            df[f'zscore_close_{period}'] = (df['close'] - df['close'].rolling(window=period).mean()) / \
                                            df['close'].rolling(window=period).std()
        
        return df

    def _add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """滞后特征"""
        important_features = ['rsi', 'macd', 'kdj_k', 'williams_r', 'cci']
        
        for feat in important_features:
            if feat in df.columns:
                for lag in [1, 2, 3, 5]:
                    df[f'{feat}_lag{lag}'] = df[feat].shift(lag)
                df[f'{feat}_diff'] = df[feat].diff()
                df[f'{feat}_diff3'] = df[feat].diff(3)
        
        return df


class OptimizedEnsembleModel:
    """优化集成模型 - Stacking + 多模型"""

    def __init__(self, use_stacking: bool = True):
        self.model = None
        self.feature_names = []
        self.use_stacking = use_stacking
        self.scaler = StandardScaler()

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """训练优化集成模型"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.feature_names = list(X.columns)
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        estimators = []

        if HAS_LIGHTGBM:
            lgb_model = lgb.LGBMClassifier(
                n_estimators=300,
                max_depth=8,
                learning_rate=0.05,
                num_leaves=63,
                min_child_samples=20,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.01,
                reg_lambda=0.01,
                random_state=42,
                verbose=-1,
                n_jobs=1,
            )
            estimators.append(('lgb', lgb_model))

        if HAS_XGBOOST:
            xgb_model = xgb.XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.01,
                reg_lambda=0.01,
                min_child_weight=5,
                gamma=0.1,
                random_state=42,
                eval_metric='logloss',
                n_jobs=1,
            )
            estimators.append(('xgb', xgb_model))

        if HAS_CATBOOST:
            cat_model = CatBoostClassifier(
                iterations=500,
                depth=8,
                learning_rate=0.05,
                l2_leaf_reg=3,
                random_state=42,
                verbose=0,
            )
            estimators.append(('cat', cat_model))

        if len(estimators) == 0:
            raise ImportError("需要安装 LightGBM, XGBoost 或 CatBoost")

        if self.use_stacking and len(estimators) >= 2:
            print("🚀 训练 Stacking 集成模型...")
            
            final_estimator = LogisticRegression(
                C=1.0,
                max_iter=1000,
                random_state=42,
            )
            
            self.model = StackingClassifier(
                estimators=estimators,
                final_estimator=final_estimator,
                cv=3,
                stack_method='predict_proba',
                n_jobs=1,
            )
            
            self.model.fit(X_train_scaled, y_train)
        else:
            print("🚀 训练 Voting 集成模型...")
            
            self.model = VotingClassifier(
                estimators=estimators,
                voting='soft',
            )
            
            self.model.fit(X_train_scaled, y_train)

        y_pred = self.model.predict(X_test_scaled)
        y_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
            'auc': roc_auc_score(y_test, y_proba) if len(y_test.unique()) > 1 else 0.5,
        }

        print(f"\n📈 优化模型训练结果:")
        print(f"   准确率:   {metrics['accuracy']:.2%}")
        print(f"   精确率:   {metrics['precision']:.2%}")
        print(f"   召回率:   {metrics['recall']:.2%}")
        print(f"   F1 分数:  {metrics['f1_score']:.2%}")
        print(f"   AUC:      {metrics['auc']:.4f}")

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)


class ThreeClassLabeler:
    """三分类标签生成器"""

    def __init__(
        self,
        strong_up_threshold: float = 0.05,
        up_threshold: float = 0.02,
        down_threshold: float = -0.02,
        strong_down_threshold: float = -0.05,
        prediction_days: int = 5,
    ):
        self.strong_up_threshold = strong_up_threshold
        self.up_threshold = up_threshold
        self.down_threshold = down_threshold
        self.strong_down_threshold = strong_down_threshold
        self.prediction_days = prediction_days

    def label(self, df: pd.DataFrame) -> pd.Series:
        """生成三分类标签"""
        future_return = df['close'].shift(-self.prediction_days) / df['close'] - 1

        def get_label(r):
            if pd.isna(r):
                return -1
            if r >= self.strong_up_threshold:
                return 2  # 强涨
            elif r >= self.up_threshold:
                return 1  # 涨
            elif r <= self.strong_down_threshold:
                return 0  # 强跌
            elif r <= self.down_threshold:
                return 0  # 跌
            else:
                return -1  # 忽略中间态

        return future_return.apply(get_label)


def balance_samples(X: pd.DataFrame, y: pd.Series, method: str = 'oversample') -> tuple:
    """样本平衡"""
    from collections import Counter
    
    print(f"📊 原始样本分布: {Counter(y)}")
    
    if method == 'oversample':
        max_count = y.value_counts().max()
        
        balanced_X = []
        balanced_y = []
        
        for label in y.unique():
            mask = y == label
            X_label = X[mask]
            y_label = y[mask]
            
            if len(X_label) < max_count:
                n_repeats = max_count // len(X_label) + 1
                X_label = pd.concat([X_label] * n_repeats, ignore_index=True)[:max_count]
                y_label = pd.concat([y_label] * n_repeats, ignore_index=True)[:max_count]
            
            balanced_X.append(X_label)
            balanced_y.append(y_label)
        
        X_balanced = pd.concat(balanced_X, ignore_index=True)
        y_balanced = pd.concat(balanced_y, ignore_index=True)
        
        print(f"📊 平衡后样本分布: {Counter(y_balanced)}")
        
        return X_balanced, y_balanced
    
    return X, y


def prepare_enhanced_data(days: int = 500, balance: bool = True):
    """准备增强训练数据"""
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
    
    feature_engineer = AdvancedFeatureEngineer()
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
        
        feature_cols = [col for col in df_features.columns 
                       if col not in ['open', 'high', 'low', 'close', 'volume', 'amount', 'date', 'code']]
        X = X[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
        
        all_X.append(X)
        all_y.append(y_valid)
    
    X_all = pd.concat(all_X, ignore_index=True)
    y_all = pd.concat(all_y, ignore_index=True)
    
    print(f"📊 总样本数: {len(X_all)}, 特征数: {X_all.shape[1]}")
    
    if balance:
        X_all, y_all = balance_samples(X_all, y_all)
    
    return X_all, y_all, stocks_data


def cross_validate_model(X: pd.DataFrame, y: pd.Series, n_splits: int = 3) -> dict:
    """时间序列交叉验证"""
    print(f"\n📊 进行 {n_splits} 折时间序列交叉验证...")
    
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    scores = {
        'accuracy': [],
        'precision': [],
        'recall': [],
        'f1': [],
        'auc': [],
    }
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        if len(y_val.unique()) < 2:
            print(f"   Fold {fold + 1}: 跳过 (只有一个类别)")
            continue
        
        model = OptimizedEnsembleModel(use_stacking=False)
        model.train(X_train, y_train)
        
        y_pred = model.predict(X_val)
        y_proba = model.predict_proba(X_val)[:, 1]
        
        scores['accuracy'].append(accuracy_score(y_val, y_pred))
        scores['precision'].append(precision_score(y_val, y_pred, zero_division=0))
        scores['recall'].append(recall_score(y_val, y_pred, zero_division=0))
        scores['f1'].append(f1_score(y_val, y_pred, zero_division=0))
        scores['auc'].append(roc_auc_score(y_val, y_proba))
        
        print(f"   Fold {fold + 1}: Acc={scores['accuracy'][-1]:.2%}, AUC={scores['auc'][-1]:.4f}")
    
    return {
        'accuracy_mean': np.mean(scores['accuracy']) if scores['accuracy'] else 0,
        'accuracy_std': np.std(scores['accuracy']) if scores['accuracy'] else 0,
        'auc_mean': np.mean(scores['auc']) if scores['auc'] else 0,
        'auc_std': np.std(scores['auc']) if scores['auc'] else 0,
        'f1_mean': np.mean(scores['f1']) if scores['f1'] else 0,
    }


def main():
    """主函数"""
    print("=" * 60)
    print("      ML 准确率优化 v2 (目标: 72% → 80%)")
    print("=" * 60)
    
    start_time = time.time()
    
    X, y, stocks_data = prepare_enhanced_data(days=500, balance=True)
    
    cv_results = cross_validate_model(X, y, n_splits=3)
    print(f"\n📊 交叉验证结果:")
    print(f"   准确率: {cv_results['accuracy_mean']:.2%} ± {cv_results['accuracy_std']:.2%}")
    print(f"   AUC:    {cv_results['auc_mean']:.4f} ± {cv_results['auc_std']:.4f}")
    print(f"   F1:     {cv_results['f1_mean']:.2%}")
    
    print("\n🚀 训练最终模型...")
    model = OptimizedEnsembleModel(use_stacking=True)
    metrics = model.train(X, y)
    
    total_time = time.time() - start_time
    print(f"\n⏱️ 总耗时: {total_time:.1f} 秒")
    
    improvement = (metrics['accuracy'] - 0.72) / 0.72 * 100
    print(f"\n📈 准确率提升: {metrics['accuracy']:.2%} (相比基准 72% {'↑' if improvement > 0 else '↓'}{abs(improvement):.1f}%)")
    
    output_path = Path("models/optimization_v2_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'model_metrics': metrics,
            'cv_results': cv_results,
            'total_time': total_time,
            'improvement_pct': improvement,
        }, f, indent=2, default=str)
    print(f"📄 结果已保存: {output_path}")
    
    return metrics


if __name__ == "__main__":
    main()
