"""
Stock Predictor using Machine Learning.
股票预测器 - 使用机器学习模型预测股票涨跌

支持的模型:
- LightGBM: 快速、高效
- XGBoost: 效果优秀
- RandomForest: 可解释性强
"""

# pylint: disable=unsupported-assignment-operation,unsubscriptable-object

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    logger.warning("LightGBM 未安装，使用 pip install lightgbm 安装")

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("XGBoost 未安装，使用 pip install xgboost 安装")

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("sklearn 未安装，使用 pip install scikit-learn 安装")


@dataclass
class PredictionResult:
    """预测结果"""
    code: str
    name: str
    up_prob: float
    down_prob: float
    prediction: str
    confidence: float
    expected_return: float
    features: dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            'code': self.code,
            'name': self.name,
            'up_prob': self.up_prob,
            'down_prob': self.down_prob,
            'prediction': self.prediction,
            'confidence': self.confidence,
            'expected_return': self.expected_return,
            'features': self.features,
            'timestamp': self.timestamp,
        }


class StockPredictor:
    """股票预测器"""

    def __init__(
        self,
        model_type: str = "lightgbm",
        model_path: Path | None = None,
    ):
        self.model_type = model_type
        self.model: Any = None
        self.scaler: Any = None
        self.feature_names: list[str] = []
        self.model_path = model_path

        if model_path and model_path.exists():
            self.load_model(model_path)

    def _create_model(self, task: str = "classification", **kwargs) -> Any:
        """创建模型"""
        if self.model_type == "lightgbm":
            if not HAS_LIGHTGBM:
                raise ImportError("LightGBM 未安装")

            if task == "classification":
                return lgb.LGBMClassifier(
                    n_estimators=370,
                    max_depth=8,
                    learning_rate=0.069,
                    num_leaves=214,
                    min_child_samples=13,
                    subsample=0.726,
                    colsample_bytree=0.788,
                    reg_alpha=0.03,
                    reg_lambda=0.042,
                    min_split_gain=0.052,
                    random_state=42,
                    verbose=-1,
                    n_jobs=-1,
                    **kwargs
                )
            else:
                return lgb.LGBMRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    num_leaves=31,
                    min_child_samples=20,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    verbose=-1,
                    **kwargs
                )

        elif self.model_type == "xgboost":
            if not HAS_XGBOOST:
                raise ImportError("XGBoost 未安装")

            if task == "classification":
                return xgb.XGBClassifier(
                    n_estimators=377,
                    max_depth=10,
                    learning_rate=0.039,
                    subsample=0.994,
                    colsample_bytree=0.603,
                    reg_alpha=0.0054,
                    reg_lambda=0.03,
                    min_child_weight=2,
                    gamma=0.014,
                    random_state=42,
                    eval_metric='logloss',
                    n_jobs=-1,
                    **kwargs
                )
            else:
                return xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    **kwargs
                )

        elif self.model_type == "randomforest":
            if not HAS_SKLEARN:
                raise ImportError("sklearn 未安装")

            if task == "classification":
                return RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                    **kwargs
                )
            else:
                return RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                    **kwargs
                )

        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")

    def _create_ensemble_models(self, task: str = "classification") -> dict[str, Any]:
        """创建集成模型"""
        models = {}

        if HAS_LIGHTGBM:
            if task == "classification":
                models['lightgbm'] = lgb.LGBMClassifier(
                    n_estimators=300,
                    max_depth=8,
                    learning_rate=0.03,
                    num_leaves=127,
                    min_child_samples=5,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=0.05,
                    reg_lambda=0.05,
                    min_split_gain=0.01,
                    random_state=42,
                    verbose=-1,
                )

        if HAS_XGBOOST:
            if task == "classification":
                models['xgboost'] = xgb.XGBClassifier(
                    n_estimators=300,
                    max_depth=8,
                    learning_rate=0.03,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=0.05,
                    reg_lambda=0.05,
                    min_child_weight=3,
                    gamma=0.01,
                    random_state=42,
                    eval_metric='logloss',
                )

        return models

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        feature_names: list[str] | None = None,
        task: str = "classification",
        **kwargs
    ) -> "StockPredictor":
        """
        训练模型

        Args:
            X: 特征数据
            y: 标签数据
            feature_names: 特征名称
            task: 任务类型 (classification / regression)

        Returns:
            self
        """
        self.feature_names = feature_names or list(X.columns)

        X = X[self.feature_names].fillna(0)
        X = X.replace([np.inf, -np.inf], 0)

        if HAS_SKLEARN:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            X = pd.DataFrame(X_scaled, columns=self.feature_names, index=X.index)

        if self.model_type == "ensemble":
            self.model = self._create_ensemble_models(task)
            for name, model in self.model.items():
                model.fit(X, y)
                logger.info(f"集成模型训练完成: {name}")
        else:
            self.model = self._create_model(task, **kwargs)
            self.model.fit(X, y)

        logger.info(f"模型训练完成: {self.model_type}, 特征数: {len(self.feature_names)}")

        return self

    def predict(self, X: pd.DataFrame) -> "np.ndarray":
        """
        预测

        Args:
            X: 特征数据

        Returns:
            预测结果
        """
        if self.model is None:
            raise ValueError("模型未训练，请先调用 fit() 或 load_model()")

        X = X[self.feature_names].fillna(0)
        X = X.replace([np.inf, -np.inf], 0)

        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
            X = pd.DataFrame(X_scaled, columns=self.feature_names, index=X.index)

        if self.model_type == "ensemble" and isinstance(self.model, dict):
            proba = self.predict_proba(X)
            return (proba[:, 1] >= 0.5).astype(int)
        else:
            result = self.model.predict(X)
            return np.asarray(result)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测概率

        Args:
            X: 特征数据

        Returns:
            预测概率
        """
        if self.model is None:
            raise ValueError("模型未训练，请先调用 fit() 或 load_model()")

        # 检查缺失的特征并填充默认值
        missing_features = set(self.feature_names) - set(X.columns)
        if missing_features:
            logger.warning(f"缺失特征: {missing_features}，将使用默认值 0")
            for feat in missing_features:
                X[feat] = 0.0

        X = X[self.feature_names].fillna(0)
        X = X.replace([np.inf, -np.inf], 0)

        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
            X = pd.DataFrame(X_scaled, columns=self.feature_names, index=X.index)

        if self.model_type == "ensemble" and isinstance(self.model, dict):
            probas = []
            weights_list: list[float] = []
            for name, model in self.model.items():
                proba = model.predict_proba(X)
                probas.append(proba)
                if name == 'lightgbm':
                    weights_list.append(0.5)
                elif name == 'xgboost':
                    weights_list.append(0.5)
            weights_arr = np.array(weights_list) / sum(weights_list)
            weighted_proba = np.zeros_like(probas[0])
            for i, proba in enumerate(probas):
                weighted_proba += weights_arr[i] * proba
            return np.asarray(weighted_proba)
        else:
            result = self.model.predict_proba(X)
            return np.asarray(result)

    def predict_stock(
        self,
        stock_data: dict[str, Any],
        code: str,
        name: str = "",
    ) -> PredictionResult:
        """
        预测单只股票

        Args:
            stock_data: 股票特征数据
            code: 股票代码
            name: 股票名称

        Returns:
            预测结果
        """
        X = pd.DataFrame([stock_data])

        proba = self.predict_proba(X)[0]
        up_prob = proba[1] if len(proba) > 1 else proba[0]
        down_prob = proba[0] if len(proba) > 1 else 1 - proba[0]

        prediction = "up" if up_prob > 0.5 else "down"
        confidence = max(up_prob, down_prob)
        expected_return = (up_prob - 0.5) * 0.1

        return PredictionResult(
            code=code,
            name=name,
            up_prob=round(up_prob, 4),
            down_prob=round(down_prob, 4),
            prediction=prediction,
            confidence=round(confidence, 4),
            expected_return=round(expected_return, 4),
            features=stock_data,
        )

    def predict_batch(
        self,
        stocks_data: list[dict[str, Any]],
        codes: list[str],
        names: list[str] | None = None,
    ) -> list[PredictionResult]:
        """
        批量预测股票

        Args:
            stocks_data: 股票特征数据列表
            codes: 股票代码列表
            names: 股票名称列表

        Returns:
            预测结果列表
        """
        if names is None:
            names = [""] * len(codes)

        X = pd.DataFrame(stocks_data)
        probas = self.predict_proba(X)

        results = []
        for i, (code, name) in enumerate(zip(codes, names)):
            proba = probas[i]
            up_prob = proba[1] if len(proba) > 1 else proba[0]
            down_prob = proba[0] if len(proba) > 1 else 1 - proba[0]

            prediction = "up" if up_prob > 0.5 else "down"
            confidence = max(up_prob, down_prob)
            expected_return = (up_prob - 0.5) * 0.1

            results.append(PredictionResult(
                code=code,
                name=name,
                up_prob=round(up_prob, 4),
                down_prob=round(down_prob, 4),
                prediction=prediction,
                confidence=round(confidence, 4),
                expected_return=round(expected_return, 4),
                features=stocks_data[i],
            ))

        return results

    def get_feature_importance(self) -> pd.DataFrame:
        """获取特征重要性"""
        if self.model is None:
            raise ValueError("模型未训练")

        if self.model_type == "ensemble" and isinstance(self.model, dict):
            importances = []
            for name, model in self.model.items():
                if hasattr(model, 'feature_importances_'):
                    importances.append(model.feature_importances_)
                elif hasattr(model, 'get_score'):
                    importance_dict = model.get_score(importance_type='gain')
                    imp = [importance_dict.get(f'f{i}', 0) for i in range(len(self.feature_names))]
                    importances.append(imp)
            importance = np.mean(importances, axis=0)
        elif hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
        elif hasattr(self.model, 'get_score'):
            importance_dict = self.model.get_score(importance_type='gain')
            importance = [importance_dict.get(f'f{i}', 0) for i in range(len(self.feature_names))]
        else:
            raise ValueError("模型不支持特征重要性")

        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance,
        })

        df = df.sort_values('importance', ascending=False)
        df['importance_pct'] = df['importance'] / df['importance'].sum() * 100

        return df

    def save_model(self, path: Path) -> None:
        """保存模型"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'saved_at': datetime.now().isoformat(),
        }

        joblib.dump(model_data, path)
        logger.info(f"模型已保存: {path}")

    def load_model(self, path: Path) -> None:
        """加载模型"""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"模型文件不存在: {path}")

        model_data = joblib.load(path)

        self.model = model_data['model']
        self.scaler = model_data.get('scaler')
        self.feature_names = model_data['feature_names']
        self.model_type = model_data.get('model_type', self.model_type)

        logger.info(f"模型已加载: {path}, 类型: {self.model_type}")
