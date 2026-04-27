"""
ML Prediction History Module.
ML 预测历史记录模块 - 追踪模型效果

功能:
1. 记录每次预测结果
2. 追踪预测准确性
3. 分析模型表现
4. 生成效果报告
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from enum import Enum

from ..config import config


class PredictionOutcome(Enum):
    """预测结果"""
    CORRECT = "correct"          # 预测正确
    WRONG = "wrong"              # 预测错误
    PENDING = "pending"          # 待验证


@dataclass
class PredictionRecord:
    """预测记录"""
    id: str
    code: str
    name: str
    prediction_type: str
    predicted_direction: str
    predicted_prob: float
    actual_change: float | None
    outcome: PredictionOutcome
    features: dict[str, float]
    model_version: str
    created_at: str
    verified_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "prediction_type": self.prediction_type,
            "predicted_direction": self.predicted_direction,
            "predicted_prob": self.predicted_prob,
            "actual_change": self.actual_change,
            "outcome": self.outcome.value,
            "features": self.features,
            "model_version": self.model_version,
            "created_at": self.created_at,
            "verified_at": self.verified_at,
        }


@dataclass
class ModelPerformance:
    """模型表现"""
    total_predictions: int
    correct_predictions: int
    wrong_predictions: int
    pending_predictions: int
    accuracy: float
    precision: float
    recall: float
    avg_confidence: float
    profit_predictions: int
    loss_predictions: int
    period_start: str
    period_end: str


@dataclass
class PredictionAnalysis:
    """预测分析"""
    by_direction: dict[str, dict[str, int]]
    by_confidence: dict[str, dict[str, int]]
    by_stock: dict[str, dict[str, int]]
    recent_accuracy: float
    trend: str


class MLPredictionTracker:
    """ML 预测追踪器"""

    VERIFICATION_DAYS = 5

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.predictions_file = self.cache_path / "ml_predictions.json"
        self.performance_file = self.cache_path / "ml_performance.json"

    def record_prediction(
        self,
        code: str,
        name: str,
        prediction_type: str,
        predicted_direction: str,
        predicted_prob: float,
        features: dict[str, float],
        model_version: str = "v1.0",
    ) -> PredictionRecord:
        """记录预测"""
        record_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{code}"

        record = PredictionRecord(
            id=record_id,
            code=code,
            name=name,
            prediction_type=prediction_type,
            predicted_direction=predicted_direction,
            predicted_prob=predicted_prob,
            actual_change=None,
            outcome=PredictionOutcome.PENDING,
            features=features,
            model_version=model_version,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        self._save_prediction(record)

        return record

    def verify_predictions(
        self,
        price_data: dict[str, dict[str, Any]],
    ) -> list[PredictionRecord]:
        """验证预测结果"""
        predictions = self._load_predictions()
        verified: list[PredictionRecord] = []

        for pred in predictions:
            if pred.outcome != PredictionOutcome.PENDING:
                continue

            created_date = datetime.strptime(pred.created_at[:10], "%Y-%m-%d")
            days_passed = (datetime.now() - created_date).days

            if days_passed < self.VERIFICATION_DAYS:
                continue

            stock_data = price_data.get(pred.code)
            if not stock_data:
                continue

            actual_change = stock_data.get("change_percent", 0)
            pred.actual_change = actual_change

            if pred.predicted_direction == "up" and actual_change > 0:
                pred.outcome = PredictionOutcome.CORRECT
            elif pred.predicted_direction == "down" and actual_change < 0:
                pred.outcome = PredictionOutcome.CORRECT
            elif actual_change == 0:
                pred.outcome = PredictionOutcome.PENDING
            else:
                pred.outcome = PredictionOutcome.WRONG

            pred.verified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            verified.append(pred)

        self._save_all_predictions(predictions)

        return verified

    def get_performance(self, days: int = 30) -> ModelPerformance:
        """获取模型表现"""
        predictions = self._load_predictions()

        cutoff_date = datetime.now()
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        recent_predictions = [
            p for p in predictions
            if p.created_at >= cutoff_str
        ]

        total = len(recent_predictions)
        correct = sum(1 for p in recent_predictions if p.outcome == PredictionOutcome.CORRECT)
        wrong = sum(1 for p in recent_predictions if p.outcome == PredictionOutcome.WRONG)
        pending = sum(1 for p in recent_predictions if p.outcome == PredictionOutcome.PENDING)

        verified = [p for p in recent_predictions if p.outcome != PredictionOutcome.PENDING]
        accuracy = correct / len(verified) if verified else 0

        up_predictions = [p for p in verified if p.predicted_direction == "up"]
        correct_up = sum(1 for p in up_predictions if p.outcome == PredictionOutcome.CORRECT)

        precision = correct_up / len(up_predictions) if up_predictions else 0

        actual_up = sum(1 for p in verified if p.actual_change and p.actual_change > 0)
        recall = correct_up / actual_up if actual_up > 0 else 0

        avg_confidence = sum(p.predicted_prob for p in recent_predictions) / total if total > 0 else 0

        profit_preds = sum(1 for p in recent_predictions if p.predicted_direction == "up")
        loss_preds = sum(1 for p in recent_predictions if p.predicted_direction == "down")

        period_start = min(p.created_at for p in recent_predictions) if recent_predictions else cutoff_str
        period_end = max(p.created_at for p in recent_predictions) if recent_predictions else datetime.now().strftime("%Y-%m-%d")

        return ModelPerformance(
            total_predictions=total,
            correct_predictions=correct,
            wrong_predictions=wrong,
            pending_predictions=pending,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            avg_confidence=avg_confidence,
            profit_predictions=profit_preds,
            loss_predictions=loss_preds,
            period_start=period_start[:10],
            period_end=period_end[:10],
        )

    def analyze_predictions(self, days: int = 30) -> PredictionAnalysis:
        """分析预测"""
        predictions = self._load_predictions()

        cutoff_date = datetime.now()
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        recent = [p for p in predictions if p.created_at >= cutoff_str]

        by_direction: dict[str, dict[str, int]] = {
            "up": {"correct": 0, "wrong": 0, "pending": 0},
            "down": {"correct": 0, "wrong": 0, "pending": 0},
        }

        for p in recent:
            direction = p.predicted_direction
            if p.outcome == PredictionOutcome.CORRECT:
                by_direction[direction]["correct"] += 1
            elif p.outcome == PredictionOutcome.WRONG:
                by_direction[direction]["wrong"] += 1
            else:
                by_direction[direction]["pending"] += 1

        by_confidence: dict[str, dict[str, int]] = {
            "high": {"correct": 0, "wrong": 0},
            "medium": {"correct": 0, "wrong": 0},
            "low": {"correct": 0, "wrong": 0},
        }

        for p in recent:
            if p.outcome == PredictionOutcome.PENDING:
                continue
            if p.predicted_prob >= 0.7:
                level = "high"
            elif p.predicted_prob >= 0.5:
                level = "medium"
            else:
                level = "low"

            if p.outcome == PredictionOutcome.CORRECT:
                by_confidence[level]["correct"] += 1
            else:
                by_confidence[level]["wrong"] += 1

        by_stock: dict[str, dict[str, int]] = {}
        for p in recent:
            if p.code not in by_stock:
                by_stock[p.code] = {"total": 0, "correct": 0}
            by_stock[p.code]["total"] += 1
            if p.outcome == PredictionOutcome.CORRECT:
                by_stock[p.code]["correct"] += 1

        verified = [p for p in recent if p.outcome != PredictionOutcome.PENDING]
        recent_accuracy = sum(1 for p in verified if p.outcome == PredictionOutcome.CORRECT) / len(verified) if verified else 0

        older_predictions = [p for p in predictions if p.created_at < cutoff_str and p.outcome != PredictionOutcome.PENDING]
        older_correct = sum(1 for p in older_predictions if p.outcome == PredictionOutcome.CORRECT)
        older_accuracy = older_correct / len(older_predictions) if older_predictions else 0

        if recent_accuracy > older_accuracy + 0.05:
            trend = "improving"
        elif recent_accuracy < older_accuracy - 0.05:
            trend = "declining"
        else:
            trend = "stable"

        return PredictionAnalysis(
            by_direction=by_direction,
            by_confidence=by_confidence,
            by_stock=by_stock,
            recent_accuracy=recent_accuracy,
            trend=trend,
        )

    def get_recent_predictions(self, limit: int = 50) -> list[PredictionRecord]:
        """获取最近预测"""
        predictions = self._load_predictions()
        return predictions[-limit:]

    def _save_prediction(self, record: PredictionRecord) -> None:
        """保存预测记录"""
        predictions = self._load_predictions()
        predictions.append(record)
        self._save_all_predictions(predictions)

    def _save_all_predictions(self, predictions: list[PredictionRecord]) -> None:
        """保存所有预测"""
        data = [p.to_dict() for p in predictions]
        with open(self.predictions_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_predictions(self) -> list[PredictionRecord]:
        """加载预测记录"""
        if not self.predictions_file.exists():
            return []
        try:
            with open(self.predictions_file, encoding="utf-8") as f:
                data: list[dict[str, Any]] = json.load(f)
                return [
                    PredictionRecord(
                        id=p["id"],
                        code=p["code"],
                        name=p["name"],
                        prediction_type=p["prediction_type"],
                        predicted_direction=p["predicted_direction"],
                        predicted_prob=p["predicted_prob"],
                        actual_change=p.get("actual_change"),
                        outcome=PredictionOutcome(p["outcome"]),
                        features=p.get("features", {}),
                        model_version=p.get("model_version", "v1.0"),
                        created_at=p["created_at"],
                        verified_at=p.get("verified_at"),
                    )
                    for p in data
                ]
        except Exception:
            return []

    def format_performance_report(self, performance: ModelPerformance) -> str:
        """格式化表现报告"""
        lines = [
            "\n📊 ML 模型表现报告",
            "=" * 60,
            f"统计周期: {performance.period_start} ~ {performance.period_end}",
            "",
            "📈 预测统计:",
            f"  总预测数: {performance.total_predictions}",
            f"  正确: {performance.correct_predictions}",
            f"  错误: {performance.wrong_predictions}",
            f"  待验证: {performance.pending_predictions}",
            "",
            "📊 准确性指标:",
            f"  准确率: {performance.accuracy:.1%}",
            f"  精确率: {performance.precision:.1%}",
            f"  召回率: {performance.recall:.1%}",
            f"  平均置信度: {performance.avg_confidence:.1%}",
            "",
            "📋 预测分布:",
            f"  看涨预测: {performance.profit_predictions}",
            f"  看跌预测: {performance.loss_predictions}",
        ]

        return "\n".join(lines)


ml_prediction_tracker = MLPredictionTracker()
