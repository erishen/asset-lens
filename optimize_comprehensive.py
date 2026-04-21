"""
综合优化脚本
1. 添加更多特征 - 市场情绪、资金流向、板块轮动
2. 模型融合 - LightGBM + XGBoost 集成
3. 调整信号阈值 - 提高信号置信度阈值
4. 优化仓位管理 - 根据信号强度动态调整
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from asset_lens.db.database import db_manager
from asset_lens.ml.backtest import BacktestConfig, BacktestEngine, SignalValidator, generate_backtest_report
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


class EnhancedFeatureEngineer(FeatureEngineer):
    """增强版特征工程 - 添加市场情绪、资金流向特征"""

    def calculate_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有特征"""
        df = super().calculate_all_features(df)
        df = self._add_market_sentiment(df)
        df = self._add_money_flow(df)
        df = self._add_enhanced_volatility(df)
        return df

    def _add_market_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        """市场情绪特征"""
        df['up_down_ratio'] = (df['close'] > df['open']).rolling(window=20).mean()
        
        df['amplitude'] = (df['high'] - df['low']) / df['open']
        df['amplitude_ma5'] = df['amplitude'].rolling(window=5).mean()
        df['amplitude_ma20'] = df['amplitude'].rolling(window=20).mean()
        
        df['gap_up'] = (df['low'] > df['high'].shift(1)).astype(int)
        df['gap_down'] = (df['high'] < df['low'].shift(1)).astype(int)
        
        df['limit_up_prob'] = (df['close'] >= df['close'].shift(1) * 1.1 * 0.99).rolling(window=20).mean()
        df['limit_down_prob'] = (df['close'] <= df['close'].shift(1) * 0.9 * 1.01).rolling(window=20).mean()
        
        df['price_momentum_3d'] = df['close'].pct_change(3)
        df['price_momentum_5d'] = df['close'].pct_change(5)
        df['price_acceleration'] = df['price_momentum_3d'] - df['price_momentum_3d'].shift(3)
        
        return df

    def _add_money_flow(self, df: pd.DataFrame) -> pd.DataFrame:
        """资金流向特征"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        df['money_flow'] = typical_price * df['volume']
        df['money_flow_ratio'] = df['money_flow'] / df['money_flow'].rolling(window=20).mean()
        
        df['vwap'] = (df['amount'] / df['volume']).replace([np.inf, -np.inf], np.nan)
        df['vwap_ratio'] = df['close'] / df['vwap']
        
        df['volume_price_corr'] = df['volume'].rolling(window=20).corr(df['close'])
        
        df['large_volume_ratio'] = (df['volume'] > df['volume'].rolling(window=20).quantile(0.8)).astype(int)
        df['small_volume_ratio'] = (df['volume'] < df['volume'].rolling(window=20).quantile(0.2)).astype(int)
        
        df['volume_trend'] = df['volume'].rolling(window=5).mean() / df['volume'].rolling(window=20).mean()
        
        return df

    def _add_enhanced_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """增强波动率特征"""
        df['parkinson_vol'] = np.sqrt(
            (1 / (4 * np.log(2))) * 
            (np.log(df['high'] / df['low']) ** 2)
        ).rolling(window=20).mean()
        
        df['garman_klass_vol'] = np.sqrt(
            0.5 * (np.log(df['high'] / df['low']) ** 2) -
            (2 * np.log(2) - 1) * (np.log(df['close'] / df['open']) ** 2)
        ).rolling(window=20).mean()
        
        df['volatility_regime'] = (df['volatility_20d'] > df['volatility_20d'].rolling(window=60).mean()).astype(int)
        
        return df


class EnsembleModel:
    """集成模型 - LightGBM + XGBoost"""

    def __init__(self):
        self.model = None
        self.feature_names = []

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """训练集成模型"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.feature_names = list(X.columns)

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
                n_jobs=-1,
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
                n_jobs=-1,
            )
            estimators.append(('xgb', xgb_model))

        if len(estimators) == 0:
            raise ImportError("需要安装 LightGBM 或 XGBoost")

        self.model = VotingClassifier(
            estimators=estimators,
            voting='soft',
        )

        print("🚀 训练集成模型...")
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
            'auc': roc_auc_score(y_test, y_proba),
        }

        print(f"\n📈 集成模型训练结果:")
        print(f"   准确率:   {metrics['accuracy']:.2%}")
        print(f"   精确率:   {metrics['precision']:.2%}")
        print(f"   召回率:   {metrics['recall']:.2%}")
        print(f"   F1 分数:  {metrics['f1_score']:.2%}")
        print(f"   AUC:      {metrics['auc']:.4f}")

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        return self.model.predict_proba(X)


class OptimizedBacktestEngine(BacktestEngine):
    """优化回测引擎 - 支持动态仓位和更高信号阈值"""

    def __init__(self, config: BacktestConfig, signal_threshold: float = 0.7):
        super().__init__(config)
        self.signal_threshold = signal_threshold

    def _process_buy_signals(
        self,
        predictions: pd.DataFrame,
        price_data: dict[str, pd.DataFrame],
        date: str,
    ) -> None:
        """处理买入信号 - 使用更高的信号阈值"""
        for _, row in predictions.iterrows():
            code = row['code']

            if row.get('prediction', 0) != 1:
                continue

            up_prob = row.get('up_prob', 0)
            if up_prob < self.signal_threshold:
                continue

            total_position = sum(p['value'] for p in self.positions.values())
            total_position_pct = total_position / self.capital

            if total_position_pct >= self.config.max_position:
                continue

            if code in self.positions:
                current_pct = self.positions[code]['value'] / self.capital
                if current_pct >= self.config.single_stock_max:
                    continue

            df = price_data.get(code)
            if df is None or df.empty:
                continue

            day_data = df[df['date'] == date] if 'date' in df.columns else df[df.index == date]

            if day_data.empty:
                continue

            current_price = float(day_data['close'].iloc[0])

            position_multiplier = min(2.0, 1.0 + (up_prob - self.signal_threshold) * 5)
            position_size = self.config.position_size * position_multiplier
            position_size = min(position_size, self.config.single_stock_max)

            available_capital = self.capital * (self.config.max_position - total_position_pct)
            buy_amount = min(self.capital * position_size, available_capital)

            if buy_amount < 1000:
                continue

            self._execute_buy(code, current_price, date, buy_amount, up_prob)


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
        
        feature_cols = [col for col in df_features.columns 
                       if col not in ['open', 'high', 'low', 'close', 'volume', 'amount', 'date', 'code']]
        X = X[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
        
        all_X.append(X)
        all_y.append(y_valid)
    
    X_all = pd.concat(all_X, ignore_index=True)
    y_all = pd.concat(all_y, ignore_index=True)
    
    print(f"📊 总样本数: {len(X_all)}, 特征数: {X_all.shape[1]}")
    
    return X_all, y_all, stocks_data


def run_optimized_backtest(
    model: EnsembleModel,
    stocks_data: dict[str, pd.DataFrame],
    signal_threshold: float = 0.7,
    capital: float = 100000,
) -> dict:
    """运行优化回测"""
    print(f"\n📊 运行优化回测 (信号阈值: {signal_threshold})...")
    
    feature_engineer = EnhancedFeatureEngineer()
    predictions_list = []
    price_data = {}
    
    for code, df in stocks_data.items():
        df_features = feature_engineer.calculate_all_features(df)
        
        feature_cols = [col for col in df_features.columns 
                       if col not in ['open', 'high', 'low', 'close', 'volume', 'amount', 'date', 'code']]
        X = df_features[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
        
        predictions = model.predict(X)
        probas = model.predict_proba(X)[:, 1]
        
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
        return {}
    
    predictions_df = pd.DataFrame(predictions_list)
    
    config = BacktestConfig(initial_capital=capital, position_size=0.1)
    engine = OptimizedBacktestEngine(config, signal_threshold=signal_threshold)
    result = engine.run_backtest(predictions_df, price_data)
    
    validator = SignalValidator()
    signal_result = validator.validate_signals(predictions_df, price_data)
    
    print("\n" + "=" * 50)
    print(f"      回测结果 (信号阈值: {signal_threshold})")
    print("=" * 50)
    print(f"  总收益率:   {result.total_return:.2f}%")
    print(f"  年化收益:   {result.annual_return:.2f}%")
    print(f"  最大回撤:   {result.max_drawdown:.2f}%")
    print(f"  夏普比率:   {result.sharpe_ratio:.2f}")
    print(f"  胜率:       {result.win_rate:.2f}%")
    print(f"  盈亏比:     {result.profit_factor:.2f}")
    print(f"  总交易:     {result.total_trades} 次")
    print("=" * 50)
    
    print(f"\n📊 信号验证:")
    print(f"   总信号数:   {signal_result['total_signals']}")
    print(f"   准确率:     {signal_result['accuracy']:.2f}%")
    print(f"   平均收益:   {signal_result['avg_return']:.2f}%")
    
    return {
        'backtest': result.to_dict(),
        'signal': signal_result,
    }


def main():
    """主函数"""
    print("🚀 开始综合优化...")
    start_time = time.time()
    
    X, y, stocks_data = prepare_data(days=500)
    
    model = EnsembleModel()
    metrics = model.train(X, y)
    
    results = {}
    
    for threshold in [0.6, 0.65, 0.7, 0.75, 0.8]:
        result = run_optimized_backtest(model, stocks_data, signal_threshold=threshold)
        results[f'threshold_{threshold}'] = result
    
    print("\n" + "=" * 60)
    print("              不同信号阈值对比")
    print("=" * 60)
    print(f"{'阈值':<10} {'年化收益':<12} {'夏普比率':<12} {'胜率':<12} {'交易次数':<10}")
    print("-" * 60)
    
    for threshold, result in results.items():
        bt = result.get('backtest', {})
        print(f"{threshold.replace('threshold_', ''):<10} "
              f"{bt.get('annual_return', 0):<12.2f} "
              f"{bt.get('sharpe_ratio', 0):<12.2f} "
              f"{bt.get('win_rate', 0):<12.2f} "
              f"{bt.get('total_trades', 0):<10}")
    
    print("=" * 60)
    
    best_threshold = max(
        results.keys(),
        key=lambda k: results[k].get('backtest', {}).get('sharpe_ratio', 0)
    )
    print(f"\n🏆 最佳信号阈值: {best_threshold.replace('threshold_', '')}")
    
    total_time = time.time() - start_time
    print(f"\n⏱️ 总耗时: {total_time:.1f} 秒")
    
    output_path = Path("models/optimization_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'model_metrics': metrics,
            'backtest_results': {k: v.get('backtest', {}) for k, v in results.items()},
            'best_threshold': best_threshold,
            'total_time': total_time,
        }, f, indent=2, default=str)
    print(f"📄 结果已保存: {output_path}")


if __name__ == "__main__":
    main()
