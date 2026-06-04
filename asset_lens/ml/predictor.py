import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ..utils.json_cache import read_json_cache
from .predictor_model import PredictorModelMixin
from .predictor_predict import PredictorPredictMixin

logger = logging.getLogger(__name__)

try:
    import lightgbm as lgb  # noqa: F401

    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import xgboost as xgb  # noqa: F401

    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, StackingClassifier  # noqa: F401
    from sklearn.linear_model import LogisticRegression  # noqa: F401
    from sklearn.preprocessing import StandardScaler  # noqa: F401

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def _load_optimized_params(model_type: str) -> dict[str, Any]:
    config_path = Path(f"config/ml/{model_type}_best_params.json")
    params = read_json_cache(config_path)
    if params:
        logger.info(f"Loaded optimized parameters for {model_type} from {config_path}")
        return params
    return {}


@dataclass
class PredictionResult:
    code: str
    name: str
    up_prob: float
    down_prob: float
    prediction: str
    confidence: float
    expected_return: float
    features: dict[str, float] = field(default_factory=dict)
    confidence_level: str = "low"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "up_prob": self.up_prob,
            "down_prob": self.down_prob,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "expected_return": self.expected_return,
            "features": self.features,
            "timestamp": self.timestamp,
        }


@dataclass
class ThresholdConfig:
    bullish_threshold: float = 0.60
    bearish_threshold: float = 0.40
    high_confidence_threshold: float = 0.70
    low_confidence_threshold: float = 0.55
    bull_market_boost: float = 0.05
    bear_market_penalty: float = 0.05

    def get_bullish_threshold(self, market_condition: str = "normal") -> float:
        base = self.bullish_threshold
        if market_condition == "bull":
            return max(0.50, base - self.bull_market_boost)
        elif market_condition == "bear":
            return min(0.80, base + self.bear_market_penalty)
        return base

    def get_bearish_threshold(self, market_condition: str = "normal") -> float:
        base = self.bearish_threshold
        if market_condition == "bull":
            return max(0.20, base - self.bull_market_boost)
        elif market_condition == "bear":
            return min(0.50, base + self.bear_market_penalty)
        return base


class StockPredictor(PredictorModelMixin, PredictorPredictMixin):
    _missing_features_warned = False

    def __init__(
        self,
        model_type: str = "lightgbm",
        model_path: Path | None = None,
        threshold_config: ThresholdConfig | None = None,
    ):
        self.model_type = model_type
        self.threshold_config = threshold_config or ThresholdConfig()
        self._is_fitted = False
        self._feature_names: list[str] = []
        self._ensemble_models: dict[str, Any] = {}
        self._bullish_threshold = self.threshold_config.bullish_threshold

        if model_path and model_path.exists():
            self.load_model(model_path)
        else:
            self.model = self._create_model()

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_size: float = 0.2,
    ) -> dict[str, Any]:
        from sklearn.metrics import accuracy_score, classification_report
        from sklearn.model_selection import train_test_split

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=eval_size, random_state=42, stratify=y
        )

        self.fit(X_train, y_train)

        y_pred = self.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        try:
            report = classification_report(y_test, y_pred, output_dict=True)
        except (ValueError, RuntimeError):
            report = {}

        return {
            "accuracy": accuracy,
            "classification_report": report,
            "train_size": len(X_train),
            "test_size": len(X_test),
            "feature_count": len(self._feature_names),
        }

    def train_from_database(
        self,
        days: int = 250,
        prediction_days: int = 5,
    ) -> dict[str, Any]:
        from ..db.database import db_manager
        from .features import FeatureEngineer

        feature_engineer = FeatureEngineer()

        klines_data = db_manager.get_all_klines(days=days)

        if not klines_data:
            raise ValueError("数据库中没有K线数据，请先同步数据")

        all_features = []
        all_labels = []

        for code, klines in klines_data.items():
            if len(klines) < 30:
                continue

            df = pd.DataFrame(klines)

            try:
                feature_df = feature_engineer.calculate_all_features(df)
                if feature_df.empty:
                    continue

                for i in range(len(feature_df) - prediction_days):
                    feature_row = feature_df.iloc[i]
                    future_close = df["close"].iloc[i + prediction_days] if i + prediction_days < len(df) else None

                    if future_close is None:
                        continue

                    current_close = df["close"].iloc[i]
                    label = 1 if future_close > current_close else 0

                    features = feature_row[feature_engineer.feature_names].to_dict()
                    all_features.append(features)
                    all_labels.append(label)
            except (ValueError, KeyError, RuntimeError) as e:
                logger.debug(f"处理 {code} 失败: {e}")
                continue

        if not all_features:
            raise ValueError("无法生成训练数据")

        X = pd.DataFrame(all_features)
        y = pd.Series(all_labels)

        self._feature_names = list(X.columns)

        return self.train(X, y)
