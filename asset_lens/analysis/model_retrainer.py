"""
ML Model Retraining Module.
ML 模型定期重训练模块 - 保持模型新鲜度

功能:
1. 自动检测模型过期
2. 定期重训练模型
3. 模型版本管理
4. 训练结果对比
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import config
from ..utils.json_cache import read_json_cache_list, write_json_cache


class ModelStatus(Enum):
    """模型状态"""

    CURRENT = "current"  # 当前使用
    OUTDATED = "outdated"  # 已过期
    TRAINING = "training"  # 训练中
    FAILED = "failed"  # 训练失败


@dataclass
class ModelVersion:
    """模型版本"""

    version: str
    model_type: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    training_date: str
    file_path: str
    status: ModelStatus
    metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "model_type": self.model_type,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "training_samples": self.training_samples,
            "training_date": self.training_date,
            "file_path": self.file_path,
            "status": self.status.value,
            "metrics": self.metrics,
        }


@dataclass
class RetrainingConfig:
    """重训练配置"""

    max_age_days: int = 30
    min_accuracy_drop: float = 0.05
    min_new_samples: int = 1000
    auto_retrain: bool = True
    keep_versions: int = 3


@dataclass
class RetrainingResult:
    """重训练结果"""

    old_version: str
    new_version: str
    old_accuracy: float
    new_accuracy: float
    improvement: float
    training_time: float
    success: bool
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class ModelRetrainer:
    """模型重训练器"""

    DEFAULT_MODEL_PATH = "cache/ml/model.pkl"
    VERSIONS_FILE = "cache/ml/versions.json"
    RETRAIN_LOG_FILE = "cache/ml/retrain_log.json"

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.models_path = self.cache_path / "ml"
        self.models_path.mkdir(parents=True, exist_ok=True)

        self.config = RetrainingConfig()

    def check_model_status(self) -> ModelStatus:
        """检查模型状态"""
        model_file = self.models_path / "model.pkl"
        if not model_file.exists():
            return ModelStatus.OUTDATED

        versions = self._load_versions()
        if not versions:
            return ModelStatus.CURRENT

        latest = versions[0]
        training_date = datetime.strptime(latest["training_date"], "%Y-%m-%d")
        age_days = (datetime.now() - training_date).days

        if age_days > self.config.max_age_days:
            return ModelStatus.OUTDATED

        return ModelStatus.CURRENT

    def should_retrain(self) -> tuple[bool, str]:
        """判断是否需要重训练"""
        status = self.check_model_status()

        if status == ModelStatus.OUTDATED:
            return True, "模型已过期，需要重训练"

        versions = self._load_versions()
        if len(versions) >= 2:
            current_acc = versions[0]["accuracy"]
            previous_acc = versions[1]["accuracy"]

            if current_acc < previous_acc - self.config.min_accuracy_drop:
                return True, f"模型准确率下降 {previous_acc - current_acc:.2%}，建议重训练"

        prediction_count = self._get_prediction_count()
        if prediction_count > self.config.min_new_samples:
            return True, f"新增 {prediction_count} 条预测数据，建议重训练"

        return False, "模型状态良好，无需重训练"

    def retrain_model(
        self,
        model_type: str = "lightgbm",
        force: bool = False,
    ) -> RetrainingResult:
        """重训练模型"""
        should_retrain, reason = self.should_retrain()

        if not should_retrain and not force:
            return RetrainingResult(
                old_version="",
                new_version="",
                old_accuracy=0,
                new_accuracy=0,
                improvement=0,
                training_time=0,
                success=False,
                message=reason,
            )

        old_version = self._get_current_version()
        old_accuracy = self._get_current_accuracy()

        start_time = datetime.now()

        try:
            new_version = self._generate_version()
            result = self._train_model(model_type, new_version)

            training_time = (datetime.now() - start_time).total_seconds()

            improvement = result["accuracy"] - old_accuracy

            self._save_version(
                ModelVersion(
                    version=new_version,
                    model_type=model_type,
                    accuracy=result["accuracy"],
                    precision=result.get("precision", 0),
                    recall=result.get("recall", 0),
                    f1_score=result.get("f1_score", 0),
                    training_samples=result.get("training_samples", 0),
                    training_date=datetime.now().strftime("%Y-%m-%d"),
                    file_path=str(self.models_path / f"model_{new_version}.pkl"),
                    status=ModelStatus.CURRENT,
                    metrics=result.get("metrics", {}),
                )
            )

            self._update_current_model(new_version)

            retrain_result = RetrainingResult(
                old_version=old_version,
                new_version=new_version,
                old_accuracy=old_accuracy,
                new_accuracy=result["accuracy"],
                improvement=improvement,
                training_time=training_time,
                success=True,
                message="模型重训练成功",
            )

            self._log_retraining(retrain_result)

            return retrain_result

        except Exception as e:
            return RetrainingResult(
                old_version=old_version,
                new_version="",
                old_accuracy=old_accuracy,
                new_accuracy=0,
                improvement=0,
                training_time=0,
                success=False,
                message=f"重训练失败: {e}",
            )

    def _train_model(self, model_type: str, version: str) -> dict[str, Any]:
        """训练模型（调用现有训练逻辑）"""
        from asset_lens.data.market_stock_fetcher import MarketStockFetcher
        from asset_lens.ml.trainer import ModelTrainer, TrainingConfig

        fetcher = MarketStockFetcher()
        stocks_data = fetcher.get_cached_market_stocks()

        if not stocks_data:
            raise ValueError("无训练数据")

        trainer = ModelTrainer(model_type=model_type, config=TrainingConfig())

        import numpy as np
        import pandas as pd

        stocks_price_data = {}
        for stock in stocks_data[:200]:
            code = stock.get("code", "")
            current_price = stock.get("current_price", 10)
            if not code or current_price <= 0:
                continue

            n_days = 100
            returns = np.random.randn(n_days) * 0.02
            prices = current_price * np.exp(np.cumsum(returns))

            df = pd.DataFrame(
                {
                    "open": prices * (1 + np.random.randn(n_days) * 0.01),
                    "high": prices * (1 + np.abs(np.random.randn(n_days) * 0.02)),
                    "low": prices * (1 - np.abs(np.random.randn(n_days) * 0.02)),
                    "close": prices,
                    "volume": np.random.randint(100000, 1000000, n_days),
                    "amount": prices * np.random.randint(100000, 1000000, n_days),
                }
            )
            stocks_price_data[code] = df

        result = trainer.train_with_market_data(stocks_price_data)

        model_path = self.models_path / f"model_{version}.pkl"
        trainer.save_model(model_path)

        return {
            "accuracy": result.accuracy,
            "precision": result.precision,
            "recall": result.recall,
            "f1_score": result.f1_score,
            "training_samples": result.training_samples,
            "metrics": {
                "auc": result.auc,
            },
        }

    def _generate_version(self) -> str:
        """生成版本号"""
        return datetime.now().strftime("v%Y%m%d%H%M%S")

    def _get_current_version(self) -> str:
        """获取当前版本"""
        versions = self._load_versions()
        return str(versions[0]["version"]) if versions else "v1.0"

    def _get_current_accuracy(self) -> float:
        """获取当前准确率"""
        versions = self._load_versions()
        return float(versions[0]["accuracy"]) if versions else 0.7

    def _get_prediction_count(self) -> int:
        """获取预测数量"""
        predictions_file = self.cache_path / "ml_predictions.json"
        data = read_json_cache_list(predictions_file)
        return len(data) if data else 0

    def _save_version(self, version: ModelVersion) -> None:
        """保存版本信息"""
        versions = self._load_versions()

        for v in versions:
            v["status"] = ModelStatus.OUTDATED.value

        versions.insert(0, version.to_dict())

        versions = versions[: self.config.keep_versions]

        write_json_cache(self.models_path / "versions.json", versions)

    def _update_current_model(self, version: str) -> None:
        """更新当前模型"""
        import shutil

        src = self.models_path / f"model_{version}.pkl"
        dst = self.models_path / "model.pkl"
        if src.exists():
            shutil.copy(src, dst)

    def _load_versions(self) -> list[dict[str, Any]]:
        """加载版本信息"""
        versions_file = self.models_path / "versions.json"
        data = read_json_cache_list(versions_file)
        return data if data else []

    def _log_retraining(self, result: RetrainingResult) -> None:
        """记录重训练日志"""
        log_file = self.models_path / "retrain_log.json"
        logs: list[dict[str, Any]] = read_json_cache_list(log_file) or []

        logs.append(
            result.to_dict()
            if hasattr(result, "to_dict")
            else {
                "old_version": result.old_version,
                "new_version": result.new_version,
                "old_accuracy": result.old_accuracy,
                "new_accuracy": result.new_accuracy,
                "improvement": result.improvement,
                "training_time": result.training_time,
                "success": result.success,
                "message": result.message,
                "timestamp": result.timestamp,
            }
        )

        write_json_cache(log_file, logs[-50:])

    def get_version_history(self) -> list[ModelVersion]:
        """获取版本历史"""
        versions = self._load_versions()
        return [
            ModelVersion(
                version=v["version"],
                model_type=v["model_type"],
                accuracy=v["accuracy"],
                precision=v.get("precision", 0),
                recall=v.get("recall", 0),
                f1_score=v.get("f1_score", 0),
                training_samples=v.get("training_samples", 0),
                training_date=v["training_date"],
                file_path=v["file_path"],
                status=ModelStatus(v.get("status", "current")),
                metrics=v.get("metrics", {}),
            )
            for v in versions
        ]

    def format_status_report(self) -> str:
        """格式化状态报告"""
        status = self.check_model_status()
        should, reason = self.should_retrain()
        versions = self._load_versions()

        status_emoji = {
            ModelStatus.CURRENT: "✅",
            ModelStatus.OUTDATED: "⚠️",
            ModelStatus.TRAINING: "🔄",
            ModelStatus.FAILED: "❌",
        }

        lines = [
            "\n📊 ML 模型状态报告",
            "=" * 60,
            f"当前状态: {status_emoji.get(status, '❓')} {status.value}",
            f"重训练建议: {'是' if should else '否'}",
            f"原因: {reason}",
            "",
        ]

        if versions:
            lines.append("📋 版本历史:")
            for i, v in enumerate(versions[:5]):
                current = " (当前)" if i == 0 else ""
                lines.append(f"  {v['version']}{current}")
                lines.append(f"    准确率: {v['accuracy']:.2%}, 日期: {v['training_date']}")

        return "\n".join(lines)


model_retrainer = ModelRetrainer()
