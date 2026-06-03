import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..utils.json_cache import read_json_cache, write_json_cache
from .technical_indicators import TechnicalIndicatorsMixin, safe_divide

warnings.filterwarnings("ignore", category=RuntimeWarning)

logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    ma_periods: list[int] = field(default_factory=lambda: [5, 10, 20, 60])
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    boll_period: int = 20
    boll_std: float = 2.0
    volume_ma_periods: list[int] = field(default_factory=lambda: [5, 10, 20])


class FeatureEngineer(TechnicalIndicatorsMixin):
    def __init__(self, config: FeatureConfig | None = None):
        self.config = config or FeatureConfig()
        self.feature_names: list[str] = []

    def calculate_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        all_features = []

        all_features.append(self._calc_price_features(df))
        all_features.append(self._calc_ma_features(df))
        all_features.append(self._calc_macd_features(df))
        all_features.append(self._calc_rsi_features(df))
        all_features.append(self._calc_boll_features(df))
        all_features.append(self._calc_kdj_features(df))
        all_features.append(self._calc_volume_features(df))
        all_features.append(self._calc_momentum_features(df))
        all_features.append(self._calc_volatility_features(df))
        all_features.append(self._calc_trend_features(df))
        all_features.append(self._calc_pattern_features(df))
        all_features.append(self._calc_statistical_features(df))
        all_features.append(self._calc_williams_r(df))
        all_features.append(self._calc_cci(df))
        all_features.append(self._calc_obv(df))
        all_features.append(self._calc_adx(df))
        all_features.append(self._calc_mfi(df))

        feature_df = pd.concat(all_features, axis=1)

        feature_df = feature_df.ffill().bfill().fillna(0)

        feature_df = feature_df.replace([np.inf, -np.inf], 0)

        df = pd.concat([df, feature_df], axis=1)

        self.feature_names = [
            col
            for col in df.columns
            if col
            not in [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "amount",
                "date",
                "code",
                "amplitude",
                "change_amount",
                "change_percent",
                "turnover_rate",
            ]
        ]

        return df

    def _calc_fundamental_features(self, stock_info: dict[str, Any] | None = None) -> pd.DataFrame:
        features = {}

        if stock_info:
            pe = stock_info.get("pe_ratio", 0)
            pb = stock_info.get("pb_ratio", 0)
            features["pe_ratio"] = max(0, min(pe, 1000)) if pe > 0 else 0
            features["pb_ratio"] = max(0, min(pb, 100)) if pb > 0 else 0
            features["pe_normalized"] = min(pe / 30, 3) if pe > 0 else 0

            roe = stock_info.get("roe", 0)
            features["roe"] = max(0, min(roe, 100)) if roe else 0
            features["roe_category"] = 1 if roe and roe >= 15 else (0.5 if roe and roe >= 10 else 0)

            revenue_growth = stock_info.get("revenue_growth", 0)
            profit_growth = stock_info.get("profit_growth", 0)
            features["revenue_growth"] = revenue_growth if revenue_growth else 0
            features["profit_growth"] = profit_growth if profit_growth else 0

            market_cap = stock_info.get("market_cap", 0)
            features["market_cap_log"] = np.log1p(market_cap) if market_cap > 0 else 0

            industry = stock_info.get("industry", "")
            features["is_finance"] = 1 if "银行" in industry or "保险" in industry or "证券" in industry else 0
            features["is_tech"] = 1 if "科技" in industry or "电子" in industry or "计算机" in industry else 0
            features["is_consumer"] = 1 if "消费" in industry or "食品" in industry or "医药" in industry else 0
        else:
            features["pe_ratio"] = 0
            features["pb_ratio"] = 0
            features["pe_normalized"] = 0
            features["roe"] = 0
            features["roe_category"] = 0
            features["revenue_growth"] = 0
            features["profit_growth"] = 0
            features["market_cap_log"] = 0
            features["is_finance"] = 0
            features["is_tech"] = 0
            features["is_consumer"] = 0

        return pd.DataFrame(features, index=[0])

    def calculate_all_features_with_fundamentals(
        self, df: pd.DataFrame, stock_info: dict[str, Any] | None = None
    ) -> pd.DataFrame:
        df = self.calculate_all_features(df)

        if stock_info:
            fundamental_df = self._calc_fundamental_features(stock_info)
            for col in fundamental_df.columns:
                df[col] = fundamental_df[col].iloc[0]

        return df

    def prepare_features_for_prediction(
        self, stock_data: dict[str, Any], market_data: dict[str, Any] | None = None
    ) -> pd.DataFrame:
        df = pd.DataFrame([stock_data])

        if market_data:
            for key, value in market_data.items():
                df[f"market_{key}"] = value

        return df

    def get_feature_importance_names(self) -> list[str]:
        return self.feature_names

    def save_feature_config(self, path: Path) -> None:
        config_dict = {
            "ma_periods": self.config.ma_periods,
            "rsi_period": self.config.rsi_period,
            "macd_fast": self.config.macd_fast,
            "macd_slow": self.config.macd_slow,
            "macd_signal": self.config.macd_signal,
            "boll_period": self.config.boll_period,
            "boll_std": self.config.boll_std,
            "volume_ma_periods": self.config.volume_ma_periods,
            "feature_names": self.feature_names,
        }

        write_json_cache(path, config_dict)

        logger.info(f"特征配置已保存到: {path}")

    def load_feature_config(self, path: Path) -> None:
        config_dict = read_json_cache(path)
        if config_dict is None:
            return

        self.config.ma_periods = config_dict.get("ma_periods", self.config.ma_periods)
        self.config.rsi_period = config_dict.get("rsi_period", self.config.rsi_period)
        self.config.macd_fast = config_dict.get("macd_fast", self.config.macd_fast)
        self.config.macd_slow = config_dict.get("macd_slow", self.config.macd_slow)
        self.config.macd_signal = config_dict.get("macd_signal", self.config.macd_signal)
        self.config.boll_period = config_dict.get("boll_period", self.config.boll_period)
        self.config.boll_std = config_dict.get("boll_std", self.config.boll_std)
        self.config.volume_ma_periods = config_dict.get("volume_ma_periods", self.config.volume_ma_periods)
        self.feature_names = config_dict.get("feature_names", [])

        logger.info(f"特征配置已加载: {path}")
