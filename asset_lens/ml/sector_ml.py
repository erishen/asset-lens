"""
Sector ML prediction module.
板块ML预测模块 - 使用机器学习预测板块走势
"""

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class SectorPrediction:
    """板块预测结果"""

    sector_name: str
    current_strength: float
    predicted_direction: int  # 1=上涨, 0=下跌
    predicted_change: float
    confidence: float
    recommendation: str
    factors: dict[str, float]


class SectorMLPredictor:
    """板块ML预测器"""

    SECTOR_ETF_MAPPING = {
        "科技": ["科技ETF", "芯片ETF", "半导体ETF", "5GETF", "人工智能ETF"],
        "医药": ["医药ETF", "医疗ETF", "生物科技ETF"],
        "消费": ["消费ETF", "食品ETF", "白酒ETF"],
        "金融": ["金融ETF", "银行ETF", "证券ETF"],
        "新能源": ["新能源ETF", "光伏ETF", "锂电ETF"],
        "军工": ["军工ETF", "国防ETF"],
        "有色": ["有色ETF", "黄金ETF"],
        "化工": ["化工ETF"],
        "基建": ["基建ETF", "建材ETF"],
        "电力": ["电力ETF"],
        "煤炭": ["煤炭ETF"],
        "石油": ["油气ETF", "能源ETF"],
        "钢铁": ["钢铁ETF"],
        "汽车": ["汽车ETF", "新能源车ETF"],
        "传媒": ["传媒ETF"],
        "环保": ["环保ETF"],
    }

    def __init__(self):
        self.model = None
        self.feature_names = []
        self.sector_history: dict[str, pd.DataFrame] = {}

    def prepare_sector_features(self, sector_stats: dict) -> pd.DataFrame:
        """
        准备板块特征

        Args:
            sector_stats: 板块统计数据

        Returns:
            特征DataFrame
        """
        features = []

        for sector_name, stats in sector_stats.items():
            feature_row = {
                "sector": sector_name,
                "avg_change": stats.get("avg_change", 0),
                "avg_turnover": stats.get("avg_turnover", 0),
                "up_ratio": stats.get("up_ratio", 0),
                "strength_score": stats.get("strength_score", 0),
                "count": stats.get("count", 0),
                "volatility": abs(stats.get("avg_change", 0)),
            }

            feature_row["momentum_1d"] = stats.get("avg_change", 0)
            feature_row["breadth"] = stats.get("up_ratio", 0) - 0.5
            feature_row["activity"] = stats.get("avg_turnover", 0) / 5.0

            feature_row["strength_rank"] = 0
            sorted_sectors = sorted(sector_stats.items(), key=lambda x: x[1].get("strength_score", 0), reverse=True)
            for rank, (name, _) in enumerate(sorted_sectors):
                if name == sector_name:
                    feature_row["strength_rank"] = rank + 1
                    break

            feature_row["relative_strength"] = feature_row["strength_score"] - np.mean(
                [s.get("strength_score", 0) for s in sector_stats.values()]
            )

            features.append(feature_row)

        return pd.DataFrame(features)

    def predict_sector(
        self,
        sector_name: str,
        sector_stats: dict,
        market_condition: str = "sideways",
    ) -> SectorPrediction:
        """
        预测板块走势

        Args:
            sector_name: 板块名称
            sector_stats: 板块统计数据
            market_condition: 市场状态

        Returns:
            板块预测结果
        """
        stats = sector_stats.get(sector_name, {})

        current_strength = stats.get("strength_score", 0)
        avg_change = stats.get("avg_change", 0)
        up_ratio = stats.get("up_ratio", 0.5)
        turnover = stats.get("avg_turnover", 0)

        prediction_score = 0.0
        confidence = 0.5

        if current_strength > 20:
            prediction_score += 2.0
            confidence += 0.1
        elif current_strength > 0:
            prediction_score += 1.0
        elif current_strength < -20:
            prediction_score -= 2.0
            confidence += 0.1
        elif current_strength < 0:
            prediction_score -= 1.0

        if up_ratio > 0.6:
            prediction_score += 1.0
            confidence += 0.05
        elif up_ratio < 0.4:
            prediction_score -= 1.0
            confidence += 0.05

        if turnover > 5:
            prediction_score += 0.5
        elif turnover < 1:
            prediction_score -= 0.5

        if market_condition == "bull":
            if current_strength > 0:
                prediction_score += 1.0
        elif market_condition == "bear":
            if current_strength < 0:
                prediction_score -= 1.0

        predicted_direction = 1 if prediction_score > 0 else 0
        predicted_change = avg_change * (1 + prediction_score * 0.1)
        confidence = min(0.9, max(0.4, confidence + abs(prediction_score) * 0.05))

        if predicted_direction == 1 and confidence > 0.6:
            recommendation = "建议关注，可能走强"
        elif predicted_direction == 0 and confidence > 0.6:
            recommendation = "建议回避，可能走弱"
        else:
            recommendation = "观望为主，趋势不明"

        return SectorPrediction(
            sector_name=sector_name,
            current_strength=current_strength,
            predicted_direction=predicted_direction,
            predicted_change=predicted_change,
            confidence=confidence,
            recommendation=recommendation,
            factors={
                "strength_score": current_strength,
                "up_ratio": up_ratio,
                "turnover": turnover,
                "prediction_score": prediction_score,
            },
        )

    def predict_all_sectors(
        self,
        sector_stats: dict,
        market_condition: str = "sideways",
    ) -> list[SectorPrediction]:
        """
        预测所有板块

        Args:
            sector_stats: 板块统计数据
            market_condition: 市场状态

        Returns:
            所有板块预测结果
        """
        predictions = []

        for sector_name in sector_stats.keys():
            pred = self.predict_sector(sector_name, sector_stats, market_condition)
            predictions.append(pred)

        predictions.sort(key=lambda x: x.confidence * x.predicted_direction, reverse=True)

        return predictions

    def get_sector_rotation_suggestion(
        self,
        predictions: list[SectorPrediction],
    ) -> dict[str, Any]:
        """
        获取板块轮动建议

        Args:
            predictions: 板块预测列表

        Returns:
            轮动建议
        """
        strong_sectors = [p for p in predictions if p.predicted_direction == 1 and p.confidence > 0.55]

        weak_sectors = [p for p in predictions if p.predicted_direction == 0 and p.confidence > 0.55]

        rotation_from = [s.sector_name for s in weak_sectors[:3]]
        rotation_to = [s.sector_name for s in strong_sectors[:3]]

        if rotation_from and rotation_to:
            suggestion = f"建议从 {', '.join(rotation_from)} 轮动至 {', '.join(rotation_to)}"
        elif rotation_to:
            suggestion = f"建议关注 {', '.join(rotation_to)}"
        elif rotation_from:
            suggestion = f"建议回避 {', '.join(rotation_from)}"
        else:
            suggestion = "当前市场趋势不明，建议观望"

        return {
            "strong_sectors": [s.sector_name for s in strong_sectors[:5]],
            "weak_sectors": [s.sector_name for s in weak_sectors[:5]],
            "rotation_from": rotation_from,
            "rotation_to": rotation_to,
            "suggestion": suggestion,
        }


sector_ml_predictor = SectorMLPredictor()
