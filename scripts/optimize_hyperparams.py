"""Hyperparameter optimization using Optuna."""
import logging
import warnings

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)


def objective_xgboost(trial, X_train, X_test, y_train, y_test):
    """XGBoost optimization objective."""
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 500),
        'max_depth': trial.suggest_int('max_depth', 4, 12),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.001, 0.1, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.001, 0.1, log=True),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'gamma': trial.suggest_float('gamma', 0.001, 0.1, log=True),
        'random_state': 42,
        'eval_metric': 'logloss',
        'n_jobs': -1,
    }

    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return accuracy_score(y_test, y_pred)


def objective_lightgbm(trial, X_train, X_test, y_train, y_test):
    """LightGBM optimization objective."""
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 500),
        'max_depth': trial.suggest_int('max_depth', 4, 12),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'num_leaves': trial.suggest_int('num_leaves', 31, 255),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.001, 0.1, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.001, 0.1, log=True),
        'min_split_gain': trial.suggest_float('min_split_gain', 0.001, 0.1, log=True),
        'random_state': 42,
        'verbose': -1,
        'n_jobs': -1,
    }

    model = lgb.LGBMClassifier(**params)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return accuracy_score(y_test, y_pred)


def optimize_hyperparameters(X, y, model_type='xgboost', n_trials=50):
    """Run hyperparameter optimization."""
    X = X.fillna(0).replace([np.inf, -np.inf], 0)

    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    if model_type == "xgboost":

        def objective(trial):
            return objective_xgboost(trial, X_train, X_test, y_train, y_test)
    else:

        def objective(trial):
            return objective_lightgbm(trial, X_train, X_test, y_train, y_test)

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    logger.info("Best trial: %.4f", study.best_trial.value)
    logger.info("Best params:")
    for key, value in study.best_params.items():
        logger.info("  %s: %s", key, value)

    return study.best_params, study.best_trial.value

def save_best_params(params: dict, model_type: str):
    """Save best parameters to a JSON file."""
    config_dir = Path("config/ml")
    config_dir.mkdir(parents=True, exist_ok=True)
    file_path = config_dir / f"{model_type}_best_params.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=4)
    logger.info("Best parameters for %s saved to %s", model_type, file_path)

if __name__ == '__main__':
    import json
    from asset_lens.db.database import db_manager

    logger.info('Loading data from database...')
    klines_data = db_manager.get_klines_for_ml(days=250)

    all_data = []
    for code, klines in klines_data.items():
        if len(klines) < 30:
            continue
        df = pd.DataFrame(klines)
        df['code'] = code
        all_data.append(df)

    df = pd.concat(all_data, ignore_index=True)
    logger.info('Loaded %d records from %d stocks', len(df), len(klines_data))

    from asset_lens.ml.features import FeatureEngineer
    from asset_lens.ml.trainer import ModelTrainer

    feature_engineer = FeatureEngineer()
    trainer = ModelTrainer()

    X_list = []
    y_list = []

    for code in df['code'].unique()[:100]:
        stock_df = df[df['code'] == code].copy()
        stock_df = stock_df.sort_values('date').reset_index(drop=True)

        for col in ['open', 'close', 'high', 'low', 'volume', 'amount']:
            if col in stock_df.columns:
                stock_df[col] = pd.to_numeric(stock_df[col], errors='coerce').fillna(0)

        stock_df = feature_engineer.calculate_all_features(stock_df)

        future_return = stock_df['close'].pct_change(5).shift(-5)
        stock_df['label'] = (future_return > 0.02).astype(int)

        valid = stock_df.dropna(subset=['label', *feature_engineer.feature_names])
        if len(valid) > 0:
            X_list.append(valid[feature_engineer.feature_names])
            y_list.append(valid['label'])

    X = pd.concat(X_list, ignore_index=True)
    y = pd.concat(y_list, ignore_index=True)

    logger.info('Training data: %d samples, %d features', len(X), len(X.columns))

    logger.info('Optimizing XGBoost...')
    best_params_xgb, best_score_xgb = optimize_hyperparameters(X, y, 'xgboost', n_trials=30)
    save_best_params(best_params_xgb, 'xgboost')

    logger.info('Optimizing LightGBM...')
    best_params_lgb, best_score_lgb = optimize_hyperparameters(X, y, 'lightgbm', n_trials=30)
    save_best_params(best_params_lgb, 'lightgbm')

    logger.info('OPTIMIZATION RESULTS')
    logger.info('XGBoost best accuracy: %.4f', best_score_xgb)
    logger.info('LightGBM best accuracy: %.4f', best_score_lgb)
