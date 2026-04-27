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

from .features import FeatureEngineer

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
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, StackingClassifier
    from sklearn.linear_model import LogisticRegression
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

    _missing_features_warned = False

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
        self.feature_engineer = FeatureEngineer()

        if model_path and model_path.exists():
            self.load_model(model_path)

    def _create_model(self, task: str = "classification", **kwargs) -> Any:
        """创建模型"""
        if self.model_type == "lightgbm":
            if not HAS_LIGHTGBM:
                raise ImportError("LightGBM 未安装")

            default_params: dict[str, Any] = {
                'n_estimators': 100,
                'max_depth': 5,
                'learning_rate': 0.05,
                'num_leaves': 31,
                'min_child_samples': 20,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'reg_alpha': 0.1,
                'reg_lambda': 0.1,
                'min_split_gain': 0.01,
                'random_state': 42,
                'verbose': -1,
                'n_jobs': -1,
            }
            default_params.update(kwargs)

            if task == "classification":
                return lgb.LGBMClassifier(**default_params)
            else:
                return lgb.LGBMRegressor(**default_params)

        elif self.model_type == "xgboost":
            if not HAS_XGBOOST:
                raise ImportError("XGBoost 未安装")

            if task == "classification":
                return xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=0.1,
                    reg_lambda=0.1,
                    min_child_weight=10,
                    gamma=0.1,
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

        elif self.model_type == "stacking":
            if not HAS_SKLEARN:
                raise ImportError("sklearn 未安装")
            if task == "classification":
                return self._create_stacking_model()

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

    def _create_stacking_model(self) -> Any:
        """创建Stacking集成模型"""
        estimators = []

        if HAS_LIGHTGBM:
            estimators.append(('lgb', lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.05,
                num_leaves=31,
                min_child_samples=20,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbose=-1,
                n_jobs=1,
            )))

        if HAS_XGBOOST:
            estimators.append(('xgb', xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.05,
                reg_lambda=0.05,
                random_state=42,
                eval_metric='logloss',
                use_label_encoder=False,
                n_jobs=1,
            )))

        if HAS_SKLEARN:
            estimators.append(('rf', RandomForestClassifier(
                n_estimators=50,
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=1,
            )))

        if not estimators:
            raise ValueError("没有可用的基模型")

        stacking = StackingClassifier(
            estimators=estimators,
            final_estimator=LogisticRegression(
                C=1.0,
                max_iter=1000,
                random_state=42,
            ),
            cv=3,
            stack_method='predict_proba',
            n_jobs=-1,
        )

        return stacking

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

        missing_features = set(self.feature_names) - set(X.columns)
        if missing_features:
            if not StockPredictor._missing_features_warned:
                logger.warning(f"缺失特征: {missing_features}，将使用默认值 0")
                StockPredictor._missing_features_warned = True
            missing_df = pd.DataFrame(
                0.0, index=X.index, columns=list(missing_features)
            )
            X = pd.concat([X, missing_df], axis=1)

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

    def predict_single(
        self,
        code: str,
        name: str = "",
        current_price: float = 0,
        change_percent: float = 0,
        turnover_rate: float = 0,
        market_cap: float = 0,
        pe_ratio: float = 0,
        volume: float = 0,
        amount: float = 0,
        history_data: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> PredictionResult | None:
        """
        简化的单只股票预测接口

        Args:
            code: 股票代码
            name: 股票名称
            current_price: 当前价格
            change_percent: 涨跌幅
            turnover_rate: 换手率
            market_cap: 市值
            pe_ratio: 市盈率
            volume: 成交量
            amount: 成交额
            history_data: 历史K线数据（用于计算技术指标）
            **kwargs: 其他特征

        Returns:
            预测结果，如果模型未加载则返回 None
        """
        if self.model is None:
            return None

        stock_data: dict[str, Any] = {
            "current_price": current_price,
            "change_percent": change_percent,
            "turnover_rate": turnover_rate,
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "volume": volume,
            "amount": amount,
            **kwargs,
        }

        if history_data and len(history_data) >= 30:
            try:
                df = pd.DataFrame(history_data)
                required_cols = ['close', 'high', 'low', 'volume']
                if all(col in df.columns for col in required_cols):
                    if 'open' not in df.columns:
                        df['open'] = df['close'].shift(1).fillna(df['close'])
                    if 'amount' not in df.columns:
                        df['amount'] = df['volume'] * df['close']
                    
                    df = self.feature_engineer.calculate_all_features(df)
                    
                    if not df.empty:
                        latest = df.iloc[-1]
                        for feat in self.feature_engineer.feature_names:
                            if feat in df.columns:
                                val = latest.get(feat)
                                if pd.notna(val) and not np.isinf(val):
                                    stock_data[feat] = float(val)
            except Exception as e:
                logger.debug(f"计算特征失败 {code}: {e}")

        return self.predict_stock(stock_data, code, name)

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
        for i, (code, name) in enumerate(zip(codes, names, strict=False)):
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
        elif hasattr(self.model, 'estimators_') and self.model_type == 'stacking':
            importances = []
            for estimator_item in self.model.estimators_:
                if hasattr(estimator_item, 'estimator'):
                    estimator = estimator_item.estimator
                else:
                    estimator = estimator_item
                if hasattr(estimator, 'feature_importances_'):
                    importances.append(estimator.feature_importances_)
            if importances:
                importance = np.mean(importances, axis=0)
            else:
                importance = np.zeros(len(self.feature_names))
        else:
            importance = np.zeros(len(self.feature_names))

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
