import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from asset_lens.analysis.model_retrainer import (
    ModelRetrainer,
    ModelStatus,
    ModelVersion,
    RetrainingConfig,
    RetrainingResult,
)


@pytest.fixture
def retrainer(tmp_path):
    return ModelRetrainer(cache_path=tmp_path)


class TestModelStatus:
    def test_values(self):
        assert ModelStatus.CURRENT.value == "current"
        assert ModelStatus.OUTDATED.value == "outdated"
        assert ModelStatus.TRAINING.value == "training"
        assert ModelStatus.FAILED.value == "failed"


class TestModelVersion:
    def test_creation(self):
        mv = ModelVersion(
            version="v1.0",
            model_type="lightgbm",
            accuracy=0.85,
            precision=0.82,
            recall=0.80,
            f1_score=0.81,
            training_samples=10000,
            training_date="2025-01-01",
            file_path="/tmp/model.pkl",
            status=ModelStatus.CURRENT,
        )
        assert mv.version == "v1.0"
        assert mv.accuracy == 0.85

    def test_to_dict(self):
        mv = ModelVersion(
            version="v1.0",
            model_type="lightgbm",
            accuracy=0.85,
            precision=0.82,
            recall=0.80,
            f1_score=0.81,
            training_samples=10000,
            training_date="2025-01-01",
            file_path="/tmp/model.pkl",
            status=ModelStatus.CURRENT,
            metrics={"auc": 0.9},
        )
        d = mv.to_dict()
        assert d["version"] == "v1.0"
        assert d["status"] == "current"
        assert d["metrics"]["auc"] == 0.9


class TestRetrainingConfig:
    def test_defaults(self):
        cfg = RetrainingConfig()
        assert cfg.max_age_days == 30
        assert cfg.min_accuracy_drop == 0.05
        assert cfg.min_new_samples == 1000
        assert cfg.auto_retrain is True
        assert cfg.keep_versions == 3


class TestRetrainingResult:
    def test_creation(self):
        result = RetrainingResult(
            old_version="v1.0",
            new_version="v2.0",
            old_accuracy=0.8,
            new_accuracy=0.85,
            improvement=0.05,
            training_time=120.0,
            success=True,
            message="成功",
        )
        assert result.success is True
        assert result.improvement == 0.05
        assert result.timestamp != ""


class TestModelRetrainer:
    def test_init(self, retrainer, tmp_path):
        assert retrainer.cache_path == tmp_path
        assert retrainer.models_path.exists()

    def test_check_model_status_no_model(self, retrainer):
        status = retrainer.check_model_status()
        assert status == ModelStatus.OUTDATED

    def test_check_model_status_current(self, retrainer):
        today = datetime.now().strftime("%Y-%m-%d")
        retrainer._save_version(ModelVersion(
            version="v1.0", model_type="lightgbm", accuracy=0.85,
            precision=0.8, recall=0.8, f1_score=0.8, training_samples=1000,
            training_date=today, file_path="model.pkl", status=ModelStatus.CURRENT,
        ))
        (retrainer.models_path / "model.pkl").touch()
        status = retrainer.check_model_status()
        assert status == ModelStatus.CURRENT

    def test_check_model_status_outdated(self, retrainer):
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        retrainer._save_version(ModelVersion(
            version="v1.0", model_type="lightgbm", accuracy=0.85,
            precision=0.8, recall=0.8, f1_score=0.8, training_samples=1000,
            training_date=old_date, file_path="model.pkl", status=ModelStatus.CURRENT,
        ))
        (retrainer.models_path / "model.pkl").touch()
        status = retrainer.check_model_status()
        assert status == ModelStatus.OUTDATED

    def test_should_retrain_outdated(self, retrainer):
        with patch.object(retrainer, "check_model_status", return_value=ModelStatus.OUTDATED):
            should, _reason = retrainer.should_retrain()
        assert should is True

    def test_should_retrain_accuracy_drop(self, retrainer):
        with patch.object(retrainer, "check_model_status", return_value=ModelStatus.CURRENT):
            versions = [
                {"version": "v2.0", "accuracy": 0.7, "training_date": datetime.now().strftime("%Y-%m-%d")},
                {"version": "v1.0", "accuracy": 0.85, "training_date": datetime.now().strftime("%Y-%m-%d")},
            ]
            with patch.object(retrainer, "_load_versions", return_value=versions):
                with patch.object(retrainer, "_get_prediction_count", return_value=0):
                    should, _reason = retrainer.should_retrain()
        assert should is True

    def test_should_retrain_no_need(self, retrainer):
        with patch.object(retrainer, "check_model_status", return_value=ModelStatus.CURRENT):
            with patch.object(retrainer, "_load_versions", return_value=[]):
                with patch.object(retrainer, "_get_prediction_count", return_value=0):
                    should, _reason = retrainer.should_retrain()
        assert should is False

    def test_retrain_model_not_needed(self, retrainer):
        with patch.object(retrainer, "should_retrain", return_value=(False, "no need")):
            result = retrainer.retrain_model()
        assert result.success is False

    def test_retrain_model_force(self, retrainer):
        with patch.object(retrainer, "should_retrain", return_value=(False, "no need")):
            with patch.object(retrainer, "_train_model", return_value={
                "accuracy": 0.88, "precision": 0.85, "recall": 0.83,
                "f1_score": 0.84, "training_samples": 5000, "metrics": {"auc": 0.92},
            }):
                result = retrainer.retrain_model(force=True)
        assert result.success is True
        assert result.new_accuracy == 0.88

    def test_retrain_model_failure(self, retrainer):
        with patch.object(retrainer, "should_retrain", return_value=(True, "need")):
            with patch.object(retrainer, "_train_model", side_effect=Exception("training error")):
                result = retrainer.retrain_model()
        assert result.success is False
        assert "training error" in result.message

    def test_generate_version(self, retrainer):
        v = retrainer._generate_version()
        assert v.startswith("v")

    def test_get_current_version(self, retrainer):
        assert retrainer._get_current_version() == "v1.0"

    def test_get_current_accuracy(self, retrainer):
        assert retrainer._get_current_accuracy() == 0.7

    def test_get_prediction_count_no_file(self, retrainer):
        assert retrainer._get_prediction_count() == 0

    def test_get_prediction_count_with_file(self, retrainer):
        data = [{"id": "1"}, {"id": "2"}]
        (retrainer.cache_path / "ml_predictions.json").write_text(json.dumps(data), encoding="utf-8")
        assert retrainer._get_prediction_count() == 2

    def test_save_and_load_versions(self, retrainer):
        mv = ModelVersion(
            version="v1.0", model_type="lightgbm", accuracy=0.85,
            precision=0.8, recall=0.8, f1_score=0.8, training_samples=1000,
            training_date="2025-01-01", file_path="model.pkl", status=ModelStatus.CURRENT,
        )
        retrainer._save_version(mv)
        versions = retrainer._load_versions()
        assert len(versions) == 1
        assert versions[0]["version"] == "v1.0"

    def test_keep_versions_limit(self, retrainer):
        for i in range(5):
            mv = ModelVersion(
                version=f"v{i}", model_type="lightgbm", accuracy=0.8 + i * 0.01,
                precision=0.8, recall=0.8, f1_score=0.8, training_samples=1000,
                training_date="2025-01-01", file_path="model.pkl", status=ModelStatus.CURRENT,
            )
            retrainer._save_version(mv)
        versions = retrainer._load_versions()
        assert len(versions) == 3

    def test_get_version_history(self, retrainer):
        mv = ModelVersion(
            version="v1.0", model_type="lightgbm", accuracy=0.85,
            precision=0.8, recall=0.8, f1_score=0.8, training_samples=1000,
            training_date="2025-01-01", file_path="model.pkl", status=ModelStatus.CURRENT,
        )
        retrainer._save_version(mv)
        history = retrainer.get_version_history()
        assert len(history) == 1
        assert isinstance(history[0], ModelVersion)

    def test_format_status_report(self, retrainer):
        report = retrainer.format_status_report()
        assert "ML 模型状态报告" in report

    def test_log_retraining(self, retrainer):
        result = RetrainingResult(
            old_version="v1.0", new_version="v2.0",
            old_accuracy=0.8, new_accuracy=0.85, improvement=0.05,
            training_time=120.0, success=True, message="成功",
        )
        retrainer._log_retraining(result)
        log_file = retrainer.models_path / "retrain_log.json"
        assert log_file.exists()

    def test_load_versions_invalid_json(self, retrainer):
        (retrainer.models_path / "versions.json").write_text("bad", encoding="utf-8")
        assert retrainer._load_versions() == []
