import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from asset_lens.analysis.ml_tracker import (
    MLPredictionTracker,
    ModelPerformance,
    PredictionAnalysis,
    PredictionOutcome,
    PredictionRecord,
)


@pytest.fixture
def tracker(tmp_path):
    return MLPredictionTracker(cache_path=tmp_path)


class TestPredictionOutcome:
    def test_values(self):
        assert PredictionOutcome.CORRECT.value == "correct"
        assert PredictionOutcome.WRONG.value == "wrong"
        assert PredictionOutcome.PENDING.value == "pending"


class TestPredictionRecord:
    def test_creation(self):
        record = PredictionRecord(
            id="test_001",
            code="600519",
            name="贵州茅台",
            prediction_type="direction",
            predicted_direction="up",
            predicted_prob=0.75,
            actual_change=None,
            outcome=PredictionOutcome.PENDING,
            features={"rsi": 55.0},
            model_version="v1.0",
            created_at="2025-01-01 10:00:00",
        )
        assert record.code == "600519"
        assert record.outcome == PredictionOutcome.PENDING

    def test_to_dict(self):
        record = PredictionRecord(
            id="test_001",
            code="600519",
            name="贵州茅台",
            prediction_type="direction",
            predicted_direction="up",
            predicted_prob=0.75,
            actual_change=2.5,
            outcome=PredictionOutcome.CORRECT,
            features={"rsi": 55.0},
            model_version="v1.0",
            created_at="2025-01-01 10:00:00",
            verified_at="2025-01-06 10:00:00",
        )
        d = record.to_dict()
        assert d["outcome"] == "correct"
        assert d["actual_change"] == 2.5


class TestMLPredictionTracker:
    def test_init(self, tracker, tmp_path):
        assert tracker.cache_path == tmp_path
        assert tmp_path.exists()

    def test_record_prediction(self, tracker):
        record = tracker.record_prediction(
            code="600519",
            name="贵州茅台",
            prediction_type="direction",
            predicted_direction="up",
            predicted_prob=0.75,
            features={"rsi": 55.0},
        )
        assert record.code == "600519"
        assert record.outcome == PredictionOutcome.PENDING
        assert record.actual_change is None

    def test_record_prediction_custom_version(self, tracker):
        record = tracker.record_prediction(
            code="600519",
            name="贵州茅台",
            prediction_type="direction",
            predicted_direction="up",
            predicted_prob=0.75,
            features={},
            model_version="v2.0",
        )
        assert record.model_version == "v2.0"

    def test_verify_predictions(self, tracker):
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        record = PredictionRecord(
            id="test_001",
            code="600519",
            name="贵州茅台",
            prediction_type="direction",
            predicted_direction="up",
            predicted_prob=0.75,
            actual_change=None,
            outcome=PredictionOutcome.PENDING,
            features={},
            model_version="v1.0",
            created_at=old_date,
        )
        tracker._save_prediction(record)

        price_data = {"600519": {"change_percent": 2.5}}
        verified = tracker.verify_predictions(price_data)
        assert len(verified) == 1
        assert verified[0].outcome == PredictionOutcome.CORRECT
        assert verified[0].actual_change == 2.5

    def test_verify_predictions_wrong(self, tracker):
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        record = PredictionRecord(
            id="test_002",
            code="600519",
            name="贵州茅台",
            prediction_type="direction",
            predicted_direction="up",
            predicted_prob=0.75,
            actual_change=None,
            outcome=PredictionOutcome.PENDING,
            features={},
            model_version="v1.0",
            created_at=old_date,
        )
        tracker._save_prediction(record)

        price_data = {"600519": {"change_percent": -3.0}}
        verified = tracker.verify_predictions(price_data)
        assert len(verified) == 1
        assert verified[0].outcome == PredictionOutcome.WRONG

    def test_verify_predictions_too_recent(self, tracker):
        recent_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = PredictionRecord(
            id="test_003",
            code="600519",
            name="贵州茅台",
            prediction_type="direction",
            predicted_direction="up",
            predicted_prob=0.75,
            actual_change=None,
            outcome=PredictionOutcome.PENDING,
            features={},
            model_version="v1.0",
            created_at=recent_date,
        )
        tracker._save_prediction(record)

        price_data = {"600519": {"change_percent": 2.0}}
        verified = tracker.verify_predictions(price_data)
        assert len(verified) == 0

    def test_verify_predictions_no_price_data(self, tracker):
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        record = PredictionRecord(
            id="test_004",
            code="600519",
            name="贵州茅台",
            prediction_type="direction",
            predicted_direction="up",
            predicted_prob=0.75,
            actual_change=None,
            outcome=PredictionOutcome.PENDING,
            features={},
            model_version="v1.0",
            created_at=old_date,
        )
        tracker._save_prediction(record)

        verified = tracker.verify_predictions({})
        assert len(verified) == 0

    def test_get_performance(self, tracker):
        tracker.record_prediction(
            code="600519", name="贵州茅台", prediction_type="direction",
            predicted_direction="up", predicted_prob=0.75, features={},
        )
        perf = tracker.get_performance(days=30)
        assert isinstance(perf, ModelPerformance)
        assert perf.total_predictions == 1
        assert perf.pending_predictions == 1

    def test_get_performance_empty(self, tracker):
        perf = tracker.get_performance()
        assert perf.total_predictions == 0
        assert perf.accuracy == 0

    def test_analyze_predictions(self, tracker):
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        record = PredictionRecord(
            id="test_001", code="600519", name="贵州茅台",
            prediction_type="direction", predicted_direction="up",
            predicted_prob=0.75, actual_change=2.0,
            outcome=PredictionOutcome.CORRECT, features={},
            model_version="v1.0", created_at=old_date,
        )
        tracker._save_prediction(record)

        analysis = tracker.analyze_predictions(days=30)
        assert isinstance(analysis, PredictionAnalysis)
        assert "up" in analysis.by_direction
        assert analysis.by_direction["up"]["correct"] == 1

    def test_get_recent_predictions(self, tracker):
        for i in range(5):
            tracker.record_prediction(
                code=f"code_{i}", name=f"Stock {i}", prediction_type="direction",
                predicted_direction="up", predicted_prob=0.7, features={},
            )
        recent = tracker.get_recent_predictions(limit=3)
        assert len(recent) == 3

    def test_load_predictions_empty(self, tracker):
        result = tracker._load_predictions()
        assert result == []

    def test_load_predictions_invalid_json(self, tracker):
        tracker.predictions_file.write_text("bad json", encoding="utf-8")
        result = tracker._load_predictions()
        assert result == []

    def test_format_performance_report(self, tracker):
        perf = ModelPerformance(
            total_predictions=10, correct_predictions=7, wrong_predictions=2,
            pending_predictions=1, accuracy=0.778, precision=0.8, recall=0.7,
            avg_confidence=0.72, profit_predictions=6, loss_predictions=4,
            period_start="2025-01-01", period_end="2025-01-31",
        )
        report = tracker.format_performance_report(perf)
        assert "ML 模型表现报告" in report
        assert "77.8%" in report
