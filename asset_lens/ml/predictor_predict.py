import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class PredictorPredictMixin:
    def predict_stock(
        self,
        stock_data: dict[str, float],
        code: str = "",
        name: str = "",
    ) -> Any:
        from .predictor import PredictionResult

        if not self._is_fitted:
            raise ValueError("模型未训练，请先调用 fit() 方法")

        features = pd.DataFrame([stock_data])

        missing_features = set(self._feature_names) - set(features.columns)
        for feat in missing_features:
            features[feat] = 0

        features = features[self._feature_names]

        prediction = self.predict(features)[0]
        probabilities = self.predict_proba(features)[0]

        up_prob = float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0])
        down_prob = 1 - up_prob

        confidence = abs(up_prob - 0.5) * 2

        bullish_threshold = self._bullish_threshold if hasattr(self, "_bullish_threshold") else 0.55

        expected_return = (up_prob - 0.5) * 10 if up_prob > bullish_threshold else -(0.5 - up_prob) * 10

        return PredictionResult(
            code=code,
            name=name,
            prediction="up" if prediction == 1 else "down",
            up_prob=up_prob,
            down_prob=down_prob,
            confidence=confidence,
            expected_return=expected_return,
        )

    def predict_single(
        self,
        code: str,
        name: str = "",
        history_data: list[dict[str, float]] | None = None,
    ) -> Any:
        from .predictor import PredictionResult

        if not self._is_fitted:
            logger.warning("模型未训练，返回中性预测")
            return PredictionResult(
                code=code,
                name=name,
                prediction="neutral",
                up_prob=0.5,
                down_prob=0.5,
                confidence=0.0,
                expected_return=0.0,
            )

        try:
            if history_data and len(history_data) >= 10:
                from .features import FeatureEngineer

                feature_engineer = FeatureEngineer()

                df = pd.DataFrame(history_data)
                feature_df = feature_engineer.calculate_all_features(df)

                if not feature_df.empty:
                    latest_features = feature_df.iloc[-1][feature_engineer.feature_names].to_dict()

                    stock_data = {}
                    for key, value in latest_features.items():
                        try:
                            stock_data[key] = float(value)
                        except (ValueError, TypeError):
                            stock_data[key] = 0.0

                    return self.predict_stock(stock_data, code, name)

            logger.warning(f"历史数据不足，使用默认特征: {code}")

            default_features = {name: 0.0 for name in self._feature_names}
            return self.predict_stock(default_features, code, name)

        except (ValueError, KeyError, TypeError, RuntimeError) as e:
            logger.error(f"预测 {code} 失败: {e}")
            from .predictor import PredictionResult

            return PredictionResult(
                code=code,
                name=name,
                prediction="neutral",
                up_prob=0.5,
                down_prob=0.5,
                confidence=0.0,
                expected_return=0.0,
            )

    def predict_batch(
        self,
        stocks_data: list[dict[str, Any]],
    ) -> list[Any]:
        if not self._is_fitted:
            raise ValueError("模型未训练")

        results = []
        for stock in stocks_data:
            code = stock.get("code", "")
            name = stock.get("name", "")
            history_data = stock.get("history_data")

            try:
                result = self.predict_single(code, name, history_data)
                if result:
                    results.append(result)
            except (ValueError, KeyError, RuntimeError) as e:
                logger.debug(f"预测 {code} 失败: {e}")

        return results
