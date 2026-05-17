"""
Tests for Advanced ML Trainer.
高级机器学习训练器测试
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

try:
    import lightgbm  # noqa: F401

    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False


class TestTrainingResult:
    """训练结果测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.ml.advanced_trainer import TrainingResult

        assert TrainingResult is not None

    def test_training_result_creation(self):
        """测试训练结果创建"""
        from asset_lens.ml.advanced_trainer import TrainingResult

        result = TrainingResult(
            model_type="lightgbm",
            accuracy=0.85,
            precision=0.83,
            recall=0.87,
            f1_score=0.85,
            auc_roc=0.90,
            n_features=50,
            n_samples=1000,
        )

        assert result.model_type == "lightgbm"
        assert result.accuracy == 0.85
        assert result.auc_roc == 0.90

    def test_training_result_to_dict(self):
        """测试训练结果转换为字典"""
        from asset_lens.ml.advanced_trainer import TrainingResult

        result = TrainingResult(
            model_type="lightgbm",
            accuracy=0.85,
            precision=0.83,
            recall=0.87,
            f1_score=0.85,
            auc_roc=0.90,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["model_type"] == "lightgbm"
        assert result_dict["accuracy"] == 0.85


class TestOptimizationResult:
    """优化结果测试"""

    def test_optimization_result_creation(self):
        """测试优化结果创建"""
        from asset_lens.ml.advanced_trainer import OptimizationResult

        result = OptimizationResult(
            best_params={"n_estimators": 200, "max_depth": 8},
            best_value=0.85,
            n_trials=50,
            study_name="test_study",
            optimization_time=120.5,
        )

        assert result.best_params["n_estimators"] == 200
        assert result.best_value == 0.85
        assert result.n_trials == 50

    def test_optimization_result_to_dict(self):
        """测试优化结果转换为字典"""
        from asset_lens.ml.advanced_trainer import OptimizationResult

        result = OptimizationResult(
            best_params={"n_estimators": 200},
            best_value=0.85,
            n_trials=50,
            study_name="test_study",
            optimization_time=120.5,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["best_value"] == 0.85


class TestAdvancedMLTrainer:
    """高级机器学习训练器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.ml.advanced_trainer import AdvancedMLTrainer

        assert AdvancedMLTrainer is not None

    def test_trainer_init(self):
        """测试训练器初始化"""
        from asset_lens.ml.advanced_trainer import AdvancedMLTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = AdvancedMLTrainer(output_dir=Path(tmpdir))
            assert trainer is not None
            assert trainer.output_dir == Path(tmpdir)

    def test_select_features(self):
        """测试特征选择"""
        from asset_lens.ml.advanced_trainer import AdvancedMLTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = AdvancedMLTrainer(output_dir=Path(tmpdir))

            np.random.seed(42)
            X = pd.DataFrame(np.random.randn(100, 20))
            y = pd.Series(np.random.randint(0, 2, 100))

            X_selected = trainer.select_features(X, y, k=10)

            assert X_selected.shape[1] == 10
            assert len(trainer._selected_features) == 10

    @pytest.mark.skipif(not HAS_LIGHTGBM, reason="lightgbm not installed")
    def test_train_with_cv(self):
        """测试交叉验证训练"""
        from asset_lens.ml.advanced_trainer import AdvancedMLTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = AdvancedMLTrainer(output_dir=Path(tmpdir))

            np.random.seed(42)
            X = pd.DataFrame(np.random.randn(200, 10))
            y = pd.Series(np.random.randint(0, 2, 200))

            result = trainer.train_with_cv(X, y, model_type="lightgbm", cv_splits=3)

            assert result.model_type == "lightgbm"
            assert result.n_features == 10
            assert result.n_samples == 200
            assert len(result.cv_scores) == 3
            assert 0 <= result.auc_roc <= 1

    @pytest.mark.skipif(not HAS_LIGHTGBM, reason="lightgbm not installed")
    def test_get_model(self):
        """测试获取模型"""
        from asset_lens.ml.advanced_trainer import AdvancedMLTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = AdvancedMLTrainer(output_dir=Path(tmpdir))

            np.random.seed(42)
            X = pd.DataFrame(np.random.randn(100, 5))
            y = pd.Series(np.random.randint(0, 2, 100))

            trainer.train_with_cv(X, y, model_type="lightgbm", cv_splits=2)

            model = trainer.get_model()

            assert model is not None

    def test_save_results(self):
        """测试保存结果"""
        from asset_lens.ml.advanced_trainer import AdvancedMLTrainer, TrainingResult

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = AdvancedMLTrainer(output_dir=Path(tmpdir))

            result = TrainingResult(
                model_type="lightgbm",
                accuracy=0.85,
                precision=0.83,
                recall=0.87,
                f1_score=0.85,
                auc_roc=0.90,
            )

            trainer.save_results(result, "test_result")

            saved_file = Path(tmpdir) / "test_result.json"
            assert saved_file.exists()

    @pytest.mark.skipif(not HAS_LIGHTGBM, reason="lightgbm not installed")
    def test_benchmark_query(self):
        """测试基准查询"""
        from asset_lens.ml.advanced_trainer import AdvancedMLTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = AdvancedMLTrainer(output_dir=Path(tmpdir))

            np.random.seed(42)
            X = pd.DataFrame(np.random.randn(100, 5))
            y = pd.Series(np.random.randint(0, 2, 100))

            trainer.train_with_cv(X, y, model_type="lightgbm", cv_splits=2)

            model = trainer.get_model()

            assert model is not None


class TestFeatureImportance:
    """特征重要性测试"""

    @pytest.mark.skipif(not HAS_LIGHTGBM, reason="lightgbm not installed")
    def test_feature_importance_extraction(self):
        """测试特征重要性提取"""
        from asset_lens.ml.advanced_trainer import AdvancedMLTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = AdvancedMLTrainer(output_dir=Path(tmpdir))

            np.random.seed(42)
            X = pd.DataFrame(
                np.random.randn(100, 5), columns=["feature_1", "feature_2", "feature_3", "feature_4", "feature_5"]
            )
            y = pd.Series(np.random.randint(0, 2, 100))

            result = trainer.train_with_cv(X, y, model_type="lightgbm", cv_splits=2)

            assert isinstance(result.feature_importance, dict)
            assert len(result.feature_importance) == 5


class TestCrossValidation:
    """交叉验证测试"""

    @pytest.mark.skipif(not HAS_LIGHTGBM, reason="lightgbm not installed")
    def test_cv_scores(self):
        """测试交叉验证分数"""
        from asset_lens.ml.advanced_trainer import AdvancedMLTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = AdvancedMLTrainer(output_dir=Path(tmpdir))

            np.random.seed(42)
            X = pd.DataFrame(np.random.randn(150, 8))
            y = pd.Series(np.random.randint(0, 2, 150))

            result = trainer.train_with_cv(X, y, model_type="lightgbm", cv_splits=5)

            assert len(result.cv_scores) == 5
            assert all(0 <= score <= 1 for score in result.cv_scores)
            assert 0 <= result.cv_mean <= 1
            assert result.cv_std >= 0


class TestModelMetrics:
    """模型指标测试"""

    @pytest.mark.skipif(not HAS_LIGHTGBM, reason="lightgbm not installed")
    def test_all_metrics_calculated(self):
        """测试所有指标计算"""
        from asset_lens.ml.advanced_trainer import AdvancedMLTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = AdvancedMLTrainer(output_dir=Path(tmpdir))

            np.random.seed(42)
            X = pd.DataFrame(np.random.randn(100, 5))
            y = pd.Series(np.random.randint(0, 2, 100))

            result = trainer.train_with_cv(X, y, model_type="lightgbm", cv_splits=2)

            assert 0 <= result.accuracy <= 1
            assert 0 <= result.precision <= 1
            assert 0 <= result.recall <= 1
            assert 0 <= result.f1_score <= 1
            assert 0 <= result.auc_roc <= 1
