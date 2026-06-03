import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PredictorModelMixin:
    def _create_model(self, task: str = "classification", **kwargs) -> Any:
        if self.model_type == "lightgbm":
            try:
                import lightgbm as lgb

                if task == "classification":
                    return lgb.LGBMClassifier(
                        n_estimators=kwargs.get("n_estimators", 200),
                        max_depth=kwargs.get("max_depth", 6),
                        learning_rate=kwargs.get("learning_rate", 0.05),
                        num_leaves=kwargs.get("num_leaves", 31),
                        min_child_samples=kwargs.get("min_child_samples", 20),
                        subsample=kwargs.get("subsample", 0.8),
                        colsample_bytree=kwargs.get("colsample_bytree", 0.8),
                        reg_alpha=kwargs.get("reg_alpha", 0.1),
                        reg_lambda=kwargs.get("reg_lambda", 0.1),
                        random_state=42,
                        verbose=-1,
                    )
                else:
                    return lgb.LGBMRegressor(
                        n_estimators=kwargs.get("n_estimators", 200),
                        max_depth=kwargs.get("max_depth", 6),
                        learning_rate=kwargs.get("learning_rate", 0.05),
                        num_leaves=kwargs.get("num_leaves", 31),
                        min_child_samples=kwargs.get("min_child_samples", 20),
                        subsample=kwargs.get("subsample", 0.8),
                        colsample_bytree=kwargs.get("colsample_bytree", 0.8),
                        reg_alpha=kwargs.get("reg_alpha", 0.1),
                        reg_lambda=kwargs.get("reg_lambda", 0.1),
                        random_state=42,
                        verbose=-1,
                    )
            except ImportError:
                logger.warning("LightGBM 未安装，使用随机森林")
                self.model_type = "random_forest"

        if self.model_type == "xgboost":
            try:
                import xgboost as xgb

                if task == "classification":
                    return xgb.XGBClassifier(
                        n_estimators=kwargs.get("n_estimators", 200),
                        max_depth=kwargs.get("max_depth", 6),
                        learning_rate=kwargs.get("learning_rate", 0.05),
                        subsample=kwargs.get("subsample", 0.8),
                        colsample_bytree=kwargs.get("colsample_bytree", 0.8),
                        random_state=42,
                        use_label_encoder=False,
                        eval_metric="logloss",
                    )
                else:
                    return xgb.XGBRegressor(
                        n_estimators=kwargs.get("n_estimators", 200),
                        max_depth=kwargs.get("max_depth", 6),
                        learning_rate=kwargs.get("learning_rate", 0.05),
                        subsample=kwargs.get("subsample", 0.8),
                        colsample_bytree=kwargs.get("colsample_bytree", 0.8),
                        random_state=42,
                    )
            except ImportError:
                logger.warning("XGBoost 未安装，使用随机森林")
                self.model_type = "random_forest"

        if self.model_type == "random_forest":
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

            if task == "classification":
                return RandomForestClassifier(
                    n_estimators=kwargs.get("n_estimators", 200),
                    max_depth=kwargs.get("max_depth", 10),
                    min_samples_split=kwargs.get("min_samples_split", 5),
                    min_samples_leaf=kwargs.get("min_samples_leaf", 2),
                    random_state=42,
                    n_jobs=-1,
                )
            else:
                return RandomForestRegressor(
                    n_estimators=kwargs.get("n_estimators", 200),
                    max_depth=kwargs.get("max_depth", 10),
                    min_samples_split=kwargs.get("min_samples_split", 5),
                    min_samples_leaf=kwargs.get("min_samples_leaf", 2),
                    random_state=42,
                    n_jobs=-1,
                )

        if self.model_type == "stacking":
            return self._create_stacking_model()

        if self.model_type == "ensemble":
            return self._create_ensemble_models(task)

        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(n_estimators=100, random_state=42)

    def _create_ensemble_models(self, task: str = "classification") -> dict[str, Any]:
        models = {}

        try:
            import lightgbm as lgb

            if task == "classification":
                models["lgb"] = lgb.LGBMClassifier(
                    n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, verbose=-1
                )
            else:
                models["lgb"] = lgb.LGBMRegressor(
                    n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, verbose=-1
                )
        except ImportError:
            pass

        try:
            import xgboost as xgb

            if task == "classification":
                models["xgb"] = xgb.XGBClassifier(
                    n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, use_label_encoder=False, eval_metric="logloss"
                )
            else:
                models["xgb"] = xgb.XGBRegressor(
                    n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42
                )
        except ImportError:
            pass

        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

        if task == "classification":
            models["rf"] = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, n_jobs=-1)
        else:
            models["rf"] = RandomForestRegressor(n_estimators=150, max_depth=8, random_state=42, n_jobs=-1)

        return models

    def _create_stacking_model(self) -> Any:
        from sklearn.ensemble import StackingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score

        estimators = []

        try:
            import lightgbm as lgb

            estimators.append(("lgb", lgb.LGBMClassifier(n_estimators=100, max_depth=5, random_state=42, verbose=-1)))
        except ImportError:
            pass

        try:
            import xgboost as xgb

            estimators.append(("xgb", xgb.XGBClassifier(n_estimators=100, max_depth=5, random_state=42, use_label_encoder=False, eval_metric="logloss")))
        except ImportError:
            pass

        from sklearn.ensemble import RandomForestClassifier

        estimators.append(("rf", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)))

        return StackingClassifier(estimators=estimators, final_estimator=LogisticRegression(), cv=3)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "StockPredictor":
        if self.model_type == "ensemble":
            self._ensemble_models = {}
            for name, model in self._create_ensemble_models("classification").items():
                try:
                    model.fit(X, y)
                    self._ensemble_models[name] = model
                    logger.info(f"训练 {name} 模型完成")
                except (ValueError, RuntimeError) as e:
                    logger.warning(f"训练 {name} 模型失败: {e}")
        else:
            self.model.fit(X, y)

        self._is_fitted = True
        self._feature_names = list(X.columns)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self._is_fitted:
            raise ValueError("模型未训练")

        if self.model_type == "ensemble" and self._ensemble_models:
            predictions = []
            for name, model in self._ensemble_models.items():
                try:
                    pred = model.predict(X)
                    predictions.append(pred)
                except (ValueError, RuntimeError) as e:
                    logger.warning(f"模型 {name} 预测失败: {e}")

            if predictions:
                stacked = np.vstack(predictions)
                return (stacked.mean(axis=0) > 0.5).astype(int)
            return np.zeros(len(X))
        else:
            return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self._is_fitted:
            raise ValueError("模型未训练")

        if self.model_type == "ensemble" and self._ensemble_models:
            probas = []
            for name, model in self._ensemble_models.items():
                try:
                    if hasattr(model, "predict_proba"):
                        proba = model.predict_proba(X)
                        probas.append(proba)
                except (ValueError, RuntimeError) as e:
                    logger.warning(f"模型 {name} 概率预测失败: {e}")

            if probas:
                return np.mean(probas, axis=0)
            return np.array([[0.5, 0.5]] * len(X))
        else:
            if hasattr(self.model, "predict_proba"):
                return self.model.predict_proba(X)
            predictions = self.model.predict(X)
            return np.column_stack([1 - predictions, predictions])

    def get_feature_importance(self) -> pd.DataFrame:
        if not self._is_fitted:
            raise ValueError("模型未训练")

        if self.model_type == "ensemble" and self._ensemble_models:
            all_importances = {}
            for name, model in self._ensemble_models.items():
                try:
                    if hasattr(model, "feature_importances_"):
                        all_importances[name] = model.feature_importances_
                except (ValueError, AttributeError) as e:
                    logger.debug("预测模型参数解析失败: %s", e)

            if all_importances:
                avg_importance = np.mean(list(all_importances.values()), axis=0)
            else:
                avg_importance = np.ones(len(self._feature_names)) / len(self._feature_names)
        else:
            if hasattr(self.model, "feature_importances_"):
                avg_importance = self.model.feature_importances_
            else:
                avg_importance = np.ones(len(self._feature_names)) / len(self._feature_names)

        total = avg_importance.sum()
        importance_pct = (avg_importance / total * 100) if total > 0 else avg_importance

        return pd.DataFrame(
            {"feature": self._feature_names, "importance": avg_importance, "importance_pct": importance_pct}
        ).sort_values("importance", ascending=False)

    def save_model(self, path: Path) -> None:
        import joblib

        model_data = {
            "model": self.model,
            "model_type": self.model_type,
            "feature_names": self._feature_names,
            "is_fitted": self._is_fitted,
        }

        if self.model_type == "ensemble" and self._ensemble_models:
            model_data["ensemble_models"] = self._ensemble_models

        joblib.dump(model_data, path)
        logger.info(f"模型已保存: {path}")

    def load_model(self, path: Path) -> None:
        import joblib

        model_data = joblib.load(path)

        self.model = model_data["model"]
        self.model_type = model_data.get("model_type", "random_forest")
        self._feature_names = model_data.get("feature_names", [])
        self._is_fitted = model_data.get("is_fitted", True)

        if self.model_type == "ensemble" and "ensemble_models" in model_data:
            self._ensemble_models = model_data["ensemble_models"]

        logger.info(f"模型已加载: {path}")
