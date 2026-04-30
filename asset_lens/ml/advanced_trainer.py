"""
Advanced ML Trainer with Hyperparameter Optimization.
高级机器学习训练器 - 支持超参数优化、交叉验证、模型解释

功能:
1. Optuna 超参数自动优化
2. 时间序列交叉验证
3. SHAP 模型解释
4. 特征选择
5. 集成学习
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import optuna
    from optuna.samplers import TPESampler

    HAS_OPTUNA = True
    optuna.logging.set_verbosity(optuna.logging.WARNING)
except ImportError:
    HAS_OPTUNA = False

try:
    import shap

    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

try:
    from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

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


@dataclass
class TrainingResult:
    """训练结果"""

    model_type: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    cv_scores: list[float] = field(default_factory=list)
    cv_mean: float = 0.0
    cv_std: float = 0.0
    feature_importance: dict[str, float] = field(default_factory=dict)
    shap_values: dict[str, float] = field(default_factory=dict)
    best_params: dict[str, Any] = field(default_factory=dict)
    training_time: float = 0.0
    n_features: int = 0
    n_samples: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_type": self.model_type,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "auc_roc": self.auc_roc,
            "cv_scores": self.cv_scores,
            "cv_mean": self.cv_mean,
            "cv_std": self.cv_std,
            "feature_importance": self.feature_importance,
            "shap_values": self.shap_values,
            "best_params": self.best_params,
            "training_time": self.training_time,
            "n_features": self.n_features,
            "n_samples": self.n_samples,
            "timestamp": self.timestamp,
        }


@dataclass
class OptimizationResult:
    """优化结果"""

    best_params: dict[str, Any]
    best_value: float
    n_trials: int
    study_name: str
    optimization_time: float
    param_importance: dict[str, float] = field(default_factory=dict)
    trials_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "best_params": self.best_params,
            "best_value": self.best_value,
            "n_trials": self.n_trials,
            "study_name": self.study_name,
            "optimization_time": self.optimization_time,
            "param_importance": self.param_importance,
            "trials_history": self.trials_history[:10],
        }


class AdvancedMLTrainer:
    """高级机器学习训练器"""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path("models")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._study: Any = None
        self._best_model: Any = None
        self._feature_selector: Any = None
        self._selected_features: list[str] = []

    def select_features(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        k: int = 50,
        method: str = "mutual_info",
    ) -> pd.DataFrame:
        """
        特征选择

        Args:
            X: 特征数据
            y: 标签数据
            k: 选择的特征数量
            method: 选择方法 (mutual_info / f_classif)

        Returns:
            选择后的特征数据
        """
        if not HAS_SKLEARN:
            logger.warning("sklearn 未安装，跳过特征选择")
            return X

        if method == "mutual_info":
            score_func = mutual_info_classif
        else:
            score_func = f_classif

        self._feature_selector = SelectKBest(score_func=score_func, k=min(k, X.shape[1]))
        X_selected = self._feature_selector.fit_transform(X.fillna(0), y)

        selected_indices = self._feature_selector.get_support(indices=True)
        self._selected_features = [X.columns[i] for i in selected_indices]

        logger.info(f"特征选择完成: {X.shape[1]} -> {len(self._selected_features)}")

        return pd.DataFrame(X_selected, columns=self._selected_features, index=X.index)

    def optimize_hyperparameters(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_type: str = "lightgbm",
        n_trials: int = 50,
        cv_splits: int = 5,
        timeout: int | None = None,
    ) -> OptimizationResult:
        """
        使用 Optuna 优化超参数

        Args:
            X: 特征数据
            y: 标签数据
            model_type: 模型类型
            n_trials: 优化次数
            cv_splits: 交叉验证折数
            timeout: 超时时间（秒）

        Returns:
            优化结果
        """
        if not HAS_OPTUNA:
            raise ImportError("Optuna 未安装，使用 pip install optuna 安装")

        import time

        start_time = time.time()

        X = X.fillna(0).replace([np.inf, -np.inf], 0)

        def objective(trial: optuna.Trial) -> float:
            if model_type == "lightgbm" and HAS_LIGHTGBM:
                params: dict[str, Any] = {
                    "n_estimators": trial.suggest_int("n_estimators", 100, 500),
                    "max_depth": trial.suggest_int("max_depth", 3, 12),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                    "num_leaves": trial.suggest_int("num_leaves", 20, 300),
                    "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                    "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 1.0, log=True),
                    "reg_lambda": trial.suggest_float("reg_lambda", 1e-4, 1.0, log=True),
                    "min_split_gain": trial.suggest_float("min_split_gain", 0, 0.1),
                    "random_state": 42,
                    "verbose": -1,
                    "n_jobs": -1,
                }
                model = lgb.LGBMClassifier(**params)

            elif model_type == "xgboost" and HAS_XGBOOST:
                params_xgb: dict[str, Any] = {
                    "n_estimators": trial.suggest_int("n_estimators", 100, 500),
                    "max_depth": trial.suggest_int("max_depth", 3, 12),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                    "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 1.0, log=True),
                    "reg_lambda": trial.suggest_float("reg_lambda", 1e-4, 1.0, log=True),
                    "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                    "gamma": trial.suggest_float("gamma", 0, 0.5),
                    "random_state": 42,
                    "eval_metric": "logloss",
                    "n_jobs": -1,
                }
                model = xgb.XGBClassifier(**params_xgb)

            else:
                raise ValueError(f"不支持的模型类型: {model_type}")

            tscv = TimeSeriesSplit(n_splits=cv_splits)
            scores = cross_val_score(model, X, y, cv=tscv, scoring="roc_auc", n_jobs=-1)

            return float(scores.mean())

        study = optuna.create_study(
            direction="maximize",
            sampler=TPESampler(seed=42),
            study_name=f"{model_type}_optimization",
        )

        study.optimize(objective, n_trials=n_trials, timeout=timeout, show_progress_bar=False)

        self._study = study

        param_importance = {}
        try:
            importance = optuna.importance.get_param_importances(study)
            param_importance = dict(importance)
        except Exception:
            pass

        trials_history = [
            {
                "trial": t.number,
                "value": t.value,
                "params": t.params,
            }
            for t in study.trials
            if t.value is not None
        ]

        optimization_time = time.time() - start_time

        return OptimizationResult(
            best_params=study.best_params,
            best_value=study.best_value,
            n_trials=len(study.trials),
            study_name=study.study_name,
            optimization_time=optimization_time,
            param_importance=param_importance,
            trials_history=trials_history,
        )

    def train_with_cv(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_type: str = "lightgbm",
        params: dict[str, Any] | None = None,
        cv_splits: int = 5,
    ) -> TrainingResult:
        """
        使用时间序列交叉验证训练模型

        Args:
            X: 特征数据
            y: 标签数据
            model_type: 模型类型
            params: 模型参数
            cv_splits: 交叉验证折数

        Returns:
            训练结果
        """
        import time

        start_time = time.time()

        if not HAS_SKLEARN:
            raise ImportError("sklearn 未安装")

        X = X.fillna(0).replace([np.inf, -np.inf], 0)

        default_params: dict[str, Any] = {
            "random_state": 42,
            "n_jobs": -1,
        }

        if model_type == "lightgbm" and HAS_LIGHTGBM:
            default_params.update(
                {
                    "n_estimators": 300,
                    "max_depth": 8,
                    "learning_rate": 0.05,
                    "num_leaves": 127,
                    "verbose": -1,
                }
            )
            model = lgb.LGBMClassifier(**{**default_params, **(params or {})})

        elif model_type == "xgboost" and HAS_XGBOOST:
            default_params.update(
                {
                    "n_estimators": 300,
                    "max_depth": 8,
                    "learning_rate": 0.05,
                    "eval_metric": "logloss",
                }
            )
            model = xgb.XGBClassifier(**{**default_params, **(params or {})})

        else:
            raise ValueError(f"不支持的模型类型: {model_type}")

        tscv = TimeSeriesSplit(n_splits=cv_splits)

        cv_scores = []
        all_predictions: list[Any] = []
        all_true_values: list[Any] = []
        all_probabilities: list[Any] = []

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            y_proba = model.predict_proba(X_val)[:, 1]

            score = roc_auc_score(y_val, y_proba)
            cv_scores.append(score)

            all_predictions.extend(y_pred)
            all_true_values.extend(y_val)
            all_probabilities.extend(y_proba)

            logger.info(f"Fold {fold + 1}: AUC = {score:.4f}")

        self._best_model = model
        model.fit(X, y)

        predictions_array = np.array(all_predictions)
        true_values_array = np.array(all_true_values)
        probabilities_array = np.array(all_probabilities)

        training_time = time.time() - start_time

        feature_importance: dict[str, float] = {}
        if hasattr(model, "feature_importances_"):
            for name, importance in zip(X.columns, model.feature_importances_, strict=False):
                feature_importance[name] = float(importance)

        shap_values = {}
        if HAS_SHAP and len(X) > 0:
            try:
                shap_values = self._compute_shap_values(model, X.sample(min(100, len(X))))
            except Exception as e:
                logger.warning(f"SHAP 计算失败: {e}")

        return TrainingResult(
            model_type=model_type,
            accuracy=accuracy_score(true_values_array, predictions_array),
            precision=precision_score(true_values_array, predictions_array, zero_division=0),
            recall=recall_score(true_values_array, predictions_array, zero_division=0),
            f1_score=f1_score(true_values_array, predictions_array, zero_division=0),
            auc_roc=roc_auc_score(true_values_array, probabilities_array),
            cv_scores=cv_scores,
            cv_mean=np.mean(cv_scores),
            cv_std=np.std(cv_scores),
            feature_importance=feature_importance,
            shap_values=shap_values,
            best_params=params or {},
            training_time=training_time,
            n_features=X.shape[1],
            n_samples=len(X),
        )

    def _compute_shap_values(self, model: Any, X: pd.DataFrame) -> dict[str, float]:
        """计算 SHAP 值"""
        if not HAS_SHAP:
            return {}

        try:
            if hasattr(model, "predict_proba"):
                explainer = shap.TreeExplainer(model)
            else:
                explainer = shap.Explainer(model, X)

            shap_vals = explainer.shap_values(X)

            if isinstance(shap_vals, list):
                shap_vals = shap_vals[1] if len(shap_vals) > 1 else shap_vals[0]

            mean_shap = np.abs(shap_vals).mean(axis=0)

            return {name: float(val) for name, val in zip(X.columns, mean_shap, strict=False)}

        except Exception as e:
            logger.warning(f"SHAP 计算失败: {e}")
            return {}

    def get_shap_explanation(self, X: pd.DataFrame, sample_size: int = 100) -> dict[str, Any]:
        """
        获取 SHAP 解释

        Args:
            X: 特征数据
            sample_size: 样本大小

        Returns:
            SHAP 解释结果
        """
        if not HAS_SHAP or self._best_model is None:
            return {}

        X_sample = X.sample(min(sample_size, len(X))).fillna(0).replace([np.inf, -np.inf], 0)

        return self._compute_shap_values(self._best_model, X_sample)

    def train_ensemble(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        models: list[str] | None = None,
        weights: list[float] | None = None,
    ) -> TrainingResult:
        """
        训练集成模型

        Args:
            X: 特征数据
            y: 标签数据
            models: 基模型列表
            weights: 模型权重

        Returns:
            训练结果
        """
        import time

        start_time = time.time()

        if models is None:
            models = ["lightgbm", "xgboost"]

        if weights is None:
            weights = [1.0] * len(models)

        X = X.fillna(0).replace([np.inf, -np.inf], 0)

        trained_models = []
        feature_importances = []

        for model_type in models:
            result = self.train_with_cv(X, y, model_type=model_type)
            trained_models.append(self._best_model)
            feature_importances.append(result.feature_importance)

        self._best_model = {"models": trained_models, "weights": weights, "types": models}

        avg_feature_importance: dict[str, float] = {}
        all_features: set[str] = set()
        for fi in feature_importances:
            all_features.update(fi.keys())

        for feature in all_features:
            values = [fi.get(feature, 0) for fi in feature_importances]
            avg_feature_importance[feature] = float(np.mean(values))

        training_time = time.time() - start_time

        return TrainingResult(
            model_type="ensemble",
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            auc_roc=0.0,
            cv_scores=[],
            cv_mean=0.0,
            cv_std=0.0,
            feature_importance=avg_feature_importance,
            best_params={"models": models, "weights": weights},
            training_time=training_time,
            n_features=X.shape[1],
            n_samples=len(X),
        )

    def save_results(self, result: TrainingResult | OptimizationResult, filename: str) -> None:
        """保存结果"""
        path = self.output_dir / f"{filename}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"结果已保存: {path}")

    def get_model(self) -> Any:
        """获取训练好的模型"""
        return self._best_model


advanced_trainer = AdvancedMLTrainer()
