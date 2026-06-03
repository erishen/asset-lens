import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import joblib
import lightgbm as lgb
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class SectorPrediction:
    """板块预测结果"""

    sector_name: str
    current_strength: float
    predicted_direction: int  # 1=上涨, 0=下跌, -1=中性
    predicted_change: float
    confidence: float
    recommendation: str
    factors: dict[str, float]


class SectorMLPredictor:
    """板块ML预测器"""

    MODEL_PATH = Path(__file__).parent.parent.parent / "cache" / "ml" / "sector_predictor_model.joblib"

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

    _industry_cache: dict[str, str | None] = {}

    @staticmethod
    def _map_industry_to_sector(industry: str) -> str | None:
        from asset_lens.ml.sector_rotation import SECTOR_MAPPING

        if industry in SectorMLPredictor._industry_cache:
            return SectorMLPredictor._industry_cache[industry]

        for sector, keywords in SECTOR_MAPPING.items():
            if any(kw in industry for kw in keywords):
                SectorMLPredictor._industry_cache[industry] = sector
                return sector

        SectorMLPredictor._industry_cache[industry] = None
        return None

    def __init__(self):
        self.model: lgb.LGBMRegressor | None = None
        self.feature_names: list[str] = []
        if self.MODEL_PATH.exists():
            self._load_model()

    def train(self, dataset_path: str = "sector_ml_dataset.csv"):
        """训练板块预测模型"""
        logger.info(f"Loading dataset from {dataset_path}...")
        try:
            df = pd.read_csv(dataset_path)
        except FileNotFoundError:
            logger.error(f"Dataset not found at {dataset_path}. Please run SectorDataBuilder first.")
            return

        df = df.dropna()
        if df.empty:
            logger.error("Dataset is empty after dropping NaNs.")
            return

        self.feature_names = [col for col in df.columns if col not in ["date", "sector", "future_return"]]
        X = df[self.feature_names]
        y = df["future_return"]

        logger.info(f"Training model with {len(X)} samples and {len(self.feature_names)} features...")

        self.model = lgb.LGBMRegressor(random_state=42)
        self.model.fit(X, y)

        self._save_model()
        logger.info("Model training complete and saved.")

    def _save_model(self):
        """保存模型"""
        if self.model is None:
            return

        self.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        model_data = {
            "model": self.model,
            "feature_names": self.feature_names,
        }
        joblib.dump(model_data, self.MODEL_PATH)
        logger.info(f"Model saved to {self.MODEL_PATH}")

    def _load_model(self):
        """加载模型"""
        if not self.MODEL_PATH.exists():
            logger.warning("Model file not found.")
            return

        model_data = joblib.load(self.MODEL_PATH)
        self.model = model_data["model"]
        self.feature_names = model_data["feature_names"]
        logger.info(f"Model loaded from {self.MODEL_PATH}")

    def _get_daily_features(self) -> dict[str, dict[str, float]]:
        """获取当天所有板块的最新特征"""
        from asset_lens.data.money_flow_fetcher import MoneyFlowFetcher
        from asset_lens.db.database import db_manager
        from asset_lens.ml.sector_rotation import SECTOR_MAPPING

        logger.info("Getting daily features for all sectors...")

        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        market_klines = db_manager.get_klines(code="sh000300", start_date=yesterday, end_date=today, limit=2)
        market_change = market_klines[-1].get("change_percent", 0) if market_klines else 0

        north_flow_df = MoneyFlowFetcher().get_north_flow_by_industry()

        latest_date_in_db = db_manager.get_statistics().get("latest_date")
        if not latest_date_in_db:
            return {}

        klines_dict = db_manager.get_klines_for_ml(days=2)

        all_klines = [pd.DataFrame(klines).assign(code=code) for code, klines in klines_dict.items()]
        stock_klines = pd.concat(all_klines, ignore_index=True)
        stock_klines["date"] = pd.to_datetime(stock_klines["date"])

        latest_klines = stock_klines[stock_klines["date"] == stock_klines["date"].max()].copy()

        stock_info_list = [db_manager.get_stock_info(code) for code in latest_klines["code"].unique()]
        stock_to_sector = {
            info["code"]: self._map_industry_to_sector(info["industry"])
            for info in stock_info_list
            if info and info.get("industry")
        }
        latest_klines["sector"] = latest_klines["code"].map(stock_to_sector)
        latest_klines.dropna(subset=["sector"], inplace=True)

        features_by_sector = {}
        for sector in SECTOR_MAPPING:
            sector_stocks = latest_klines[latest_klines["sector"] == sector]
            if sector_stocks.empty:
                continue

            avg_change = sector_stocks["change_percent"].mean()
            avg_turnover = sector_stocks["turnover_rate"].mean()
            up_count = (sector_stocks["change_percent"] > 0).sum()
            down_count = (sector_stocks["change_percent"] < 0).sum()
            up_ratio = up_count / (up_count + down_count) if (up_count + down_count) > 0 else 0.5
            strength_score = avg_change * 10 + up_ratio * 20 + avg_turnover * 2

            sector_keywords = SECTOR_MAPPING.get(sector, [])
            if sector_keywords and not north_flow_df.empty:
                captured_keywords = list(sector_keywords)
                mask = north_flow_df["industry"].apply(lambda x, kws=captured_keywords: any(kw in str(x) for kw in kws))
                north_flow_sector = north_flow_df[mask]
                north_net_inflow = north_flow_sector["net_inflow"].sum() if not north_flow_sector.empty else 0
            else:
                north_net_inflow = 0

            features_by_sector[sector] = {
                "avg_change": avg_change,
                "avg_turnover": avg_turnover,
                "up_ratio": up_ratio,
                "strength_score": strength_score,
                "north_net_inflow": north_net_inflow,
                "market_change": market_change,
            }

        return features_by_sector

    def predict_sector(
        self,
        sector_name: str,
        sector_features: dict[str, float],
    ) -> SectorPrediction:
        """
        使用ML模型预测板块走势
        """
        if self.model is None or not self.feature_names:
            raise RuntimeError("Model is not trained or loaded. Please run the train() method first.")

        feature_vector = pd.DataFrame([sector_features], columns=self.feature_names)

        for col in self.feature_names:
            if col not in feature_vector.columns:
                feature_vector[col] = 0
        feature_vector = feature_vector[self.feature_names]

        predicted_change = self.model.predict(feature_vector)[0]

        predicted_direction = 1 if predicted_change > 0.1 else (0 if predicted_change < -0.1 else -1)

        abs_prediction = abs(predicted_change)
        if abs_prediction > 2.0:
            confidence = 0.8
        elif abs_prediction > 1.0:
            confidence = 0.7
        elif abs_prediction > 0.5:
            confidence = 0.6
        else:
            confidence = 0.5

        if predicted_direction == 1 and confidence > 0.6:
            recommendation = "建议关注，ML模型预测可能走强"
        elif predicted_direction == 0 and confidence > 0.6:
            recommendation = "建议回避，ML模型预测可能走弱"
        else:
            recommendation = "观望为主，ML模型预测趋势不明"

        current_strength = sector_features.get("strength_score", 0)

        return SectorPrediction(
            sector_name=sector_name,
            current_strength=current_strength,
            predicted_direction=predicted_direction,
            predicted_change=float(predicted_change),
            confidence=confidence,
            recommendation=recommendation,
            factors=sector_features,
        )

    def predict_all_sectors(self) -> list[SectorPrediction]:
        """
        使用ML模型预测所有板块的走势
        """
        features_by_sector = self._get_daily_features()
        if not features_by_sector:
            logger.warning("Could not generate daily features. Aborting prediction.")
            return []

        predictions = []
        for sector_name, features in features_by_sector.items():
            try:
                pred = self.predict_sector(sector_name, features)
                predictions.append(pred)
            except (ValueError, KeyError, RuntimeError) as e:
                logger.error(f"Failed to predict sector {sector_name}: {e}")

        predictions.sort(key=lambda x: x.predicted_change, reverse=True)
        return predictions

    def get_sector_rotation_suggestion(
        self,
        predictions: list[SectorPrediction],
    ) -> dict[str, Any]:
        """
        获取板块轮动建议
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
