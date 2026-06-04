"""Smoke tests for asset_lens.ml untested modules."""

import numpy as np
import pandas as pd

from asset_lens.ml.features import FeatureConfig, FeatureEngineer
from asset_lens.ml.predictor import PredictionResult
from asset_lens.ml.sector_ml import SectorMLPredictor, SectorPrediction


class TestFeatureEngineer:
    def test_feature_config_defaults(self):
        config = FeatureConfig()
        assert config.rsi_period == 14
        assert config.macd_fast == 12
        assert config.macd_slow == 26
        assert config.boll_std == 2.0

    def test_feature_engineer_creation(self):
        fe = FeatureEngineer()
        assert fe.config is not None
        assert isinstance(fe.feature_names, list)

    def test_feature_engineer_with_custom_config(self):
        config = FeatureConfig(rsi_period=7, macd_fast=8)
        fe = FeatureEngineer(config=config)
        assert fe.config.rsi_period == 7
        assert fe.config.macd_fast == 8

    def test_calculate_all_features_basic(self):
        fe = FeatureEngineer()
        n = 100
        df = pd.DataFrame(
            {
                "close": np.random.randn(n).cumsum() + 100,
                "high": np.random.randn(n).cumsum() + 101,
                "low": np.random.randn(n).cumsum() + 99,
                "open": np.random.randn(n).cumsum() + 100,
                "volume": np.random.randint(100000, 1000000, n),
            }
        )
        result = fe.calculate_all_features(df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == n


class TestPredictionResult:
    def test_prediction_result_creation(self):
        result = PredictionResult(
            code="000001",
            name="平安银行",
            up_prob=0.65,
            down_prob=0.35,
            prediction="up",
            confidence=0.7,
            expected_return=0.05,
        )
        assert result.code == "000001"
        assert result.up_prob == 0.65


class TestSectorMLPredictor:
    def test_sector_ml_predictor_creation(self):
        predictor = SectorMLPredictor()
        assert predictor.model is None
        assert isinstance(predictor.feature_names, list)

    def test_sector_etf_mapping(self):
        assert "科技" in SectorMLPredictor.SECTOR_ETF_MAPPING
        assert "医药" in SectorMLPredictor.SECTOR_ETF_MAPPING

    def test_sector_prediction_creation(self):
        pred = SectorPrediction(
            sector_name="科技",
            current_strength=0.8,
            predicted_direction=1,
            predicted_change=2.5,
            confidence=0.7,
            recommendation="加仓",
            factors={"momentum": 0.5},
        )
        assert pred.sector_name == "科技"
        assert pred.predicted_direction == 1
        assert pred.confidence == 0.7
