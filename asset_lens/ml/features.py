"""
Feature Engineering for Machine Learning.
特征工程模块 - 计算股票技术指标和因子

特征类型:
- 技术指标: MA、MACD、RSI、KDJ、布林带等
- 量价因子: 成交量变化、换手率、涨跌幅
- 资金流向: 主力净流入、北向资金
- 市场情绪: VIX、涨跌家数比
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """特征配置"""

    ma_periods: list[int] = field(default_factory=lambda: [5, 10, 20, 60])
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    boll_period: int = 20
    boll_std: float = 2.0
    volume_ma_periods: list[int] = field(default_factory=lambda: [5, 10, 20])


class FeatureEngineer:
    """特征工程器 - 计算股票技术指标和因子"""

    def __init__(self, config: FeatureConfig | None = None):
        self.config = config or FeatureConfig()
        self.feature_names: list[str] = []

    def calculate_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有特征

        Args:
            df: 股票数据，需包含 close, high, low, volume 等列

        Returns:
            添加特征后的 DataFrame
        """
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

    def _calc_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """价格相关特征"""
        features = {}
        features["pct_change"] = df["close"].pct_change()
        features["pct_change_5d"] = df["close"].pct_change(5)
        features["pct_change_10d"] = df["close"].pct_change(10)
        features["pct_change_20d"] = df["close"].pct_change(20)
        features["high_low_ratio"] = df["high"] / df["low"]
        features["close_open_ratio"] = df["close"] / df["open"]
        features["upper_shadow"] = (df["high"] - df[["open", "close"]].max(axis=1)) / df["close"]
        features["lower_shadow"] = (df[["open", "close"]].min(axis=1) - df["low"]) / df["close"]
        return pd.DataFrame(features)

    def _calc_ma_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """均线特征"""
        features = {}
        for period in self.config.ma_periods:
            features[f"ma{period}"] = df["close"].rolling(window=period).mean()
            features[f"close_ma{period}_ratio"] = df["close"] / features[f"ma{period}"]

        if f"ma{self.config.ma_periods[0]}" in features and f"ma{self.config.ma_periods[2]}" in features:
            ma5 = features["ma5"]
            ma20 = features["ma20"]
            features["ma5_ma20_ratio"] = ma5 / ma20
            features["ma_cross_signal"] = (ma5 > ma20).astype(int)

        return pd.DataFrame(features)

    def _calc_macd_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """MACD 特征"""
        features = {}
        exp1 = df["close"].ewm(span=self.config.macd_fast, adjust=False).mean()
        exp2 = df["close"].ewm(span=self.config.macd_slow, adjust=False).mean()

        features["macd"] = exp1 - exp2
        features["macd_signal"] = features["macd"].ewm(span=self.config.macd_signal, adjust=False).mean()
        features["macd_hist"] = features["macd"] - features["macd_signal"]
        features["macd_cross"] = (
            (features["macd"] > features["macd_signal"]) 
            & (features["macd"].shift(1) <= features["macd_signal"].shift(1))
        ).astype(int)

        return pd.DataFrame(features)

    def _calc_rsi_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """RSI 特征"""
        features = {}
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.rsi_period).mean()

        rs = gain / loss
        features["rsi"] = 100 - (100 / (1 + rs))
        features["rsi_oversold"] = (features["rsi"] < 30).astype(int)
        features["rsi_overbought"] = (features["rsi"] > 70).astype(int)

        return pd.DataFrame(features)

    def _calc_boll_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """布林带特征"""
        features = {}
        period = self.config.boll_period
        std_mult = self.config.boll_std

        features["boll_mid"] = df["close"].rolling(window=period).mean()
        features["boll_std"] = df["close"].rolling(window=period).std()
        features["boll_upper"] = features["boll_mid"] + std_mult * features["boll_std"]
        features["boll_lower"] = features["boll_mid"] - std_mult * features["boll_std"]
        features["boll_width"] = (features["boll_upper"] - features["boll_lower"]) / features["boll_mid"]
        features["boll_position"] = (df["close"] - features["boll_lower"]) / (features["boll_upper"] - features["boll_lower"])

        return pd.DataFrame(features)

    def _calc_kdj_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """KDJ 特征"""
        features = {}
        low_min = df["low"].rolling(window=9).min()
        high_max = df["high"].rolling(window=9).max()

        features["kdj_rsv"] = (df["close"] - low_min) / (high_max - low_min) * 100
        features["kdj_k"] = features["kdj_rsv"].ewm(alpha=1 / 3, adjust=False).mean()
        features["kdj_d"] = features["kdj_k"].ewm(alpha=1 / 3, adjust=False).mean()
        features["kdj_j"] = 3 * features["kdj_k"] - 2 * features["kdj_d"]
        features["kdj_cross"] = (
            (features["kdj_k"] > features["kdj_d"]) 
            & (features["kdj_k"].shift(1) <= features["kdj_d"].shift(1))
        ).astype(int)

        return pd.DataFrame(features)

    def _calc_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """成交量特征"""
        features = {}
        for period in self.config.volume_ma_periods:
            features[f"volume_ma{period}"] = df["volume"].rolling(window=period).mean()
            features[f"volume_ratio_{period}"] = df["volume"] / features[f"volume_ma{period}"]

        features["volume_change"] = df["volume"].pct_change()
        pct_change = df["close"].pct_change()
        features["volume_price_trend"] = features["volume_change"] * pct_change

        amount = df.get("amount", df["volume"] * df["close"])
        if amount.isna().all():
            amount = df["volume"] * df["close"]

        for period in [5, 10, 20]:
            features[f"amount_ma{period}"] = amount.rolling(window=period).mean()
            features[f"amount_ratio_{period}"] = amount / features[f"amount_ma{period}"]

        return pd.DataFrame(features)

    def _calc_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """动量特征"""
        features = {}
        features["momentum_5d"] = df["close"] / df["close"].shift(5) - 1
        features["momentum_10d"] = df["close"] / df["close"].shift(10) - 1
        features["momentum_20d"] = df["close"] / df["close"].shift(20) - 1
        features["roc_10"] = (df["close"] - df["close"].shift(10)) / df["close"].shift(10) * 100
        features["roc_20"] = (df["close"] - df["close"].shift(20)) / df["close"].shift(20) * 100

        return pd.DataFrame(features)

    def _calc_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """波动率特征"""
        features = {}
        pct_change = df["close"].pct_change()
        features["volatility_5d"] = pct_change.rolling(window=5).std()
        features["volatility_10d"] = pct_change.rolling(window=10).std()
        features["volatility_20d"] = pct_change.rolling(window=20).std()

        features["atr"] = self._calculate_atr(df, period=14)
        features["atr_ratio"] = features["atr"] / df["close"]
        features["volatility_ratio"] = features["volatility_5d"] / features["volatility_20d"]

        return pd.DataFrame(features)

    def _calc_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """趋势特征"""
        features = {}
        pct_change = df["close"].pct_change()
        momentum_5d = df["close"] / df["close"].shift(5) - 1
        
        features["trend_strength"] = (df["close"] - df["close"].shift(20)) / df["close"].shift(20)
        features["trend_consistency"] = (pct_change > 0).rolling(window=10).mean()
        features["trend_acceleration"] = momentum_5d - momentum_5d.shift(5)
        features["higher_high"] = (df["high"] > df["high"].shift(1)).astype(int)
        features["lower_low"] = (df["low"] < df["low"].shift(1)).astype(int)
        features["higher_low"] = (df["low"] > df["low"].shift(1)).astype(int)
        features["lower_high"] = (df["high"] < df["high"].shift(1)).astype(int)

        return pd.DataFrame(features)

    def _calc_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """K线形态特征"""
        features = {}
        features["doji"] = (abs(df["close"] - df["open"]) / (df["high"] - df["low"]) < 0.1).astype(int)
        features["bullish_engulfing"] = (
            (df["close"] > df["open"])
            & (df["close"].shift(1) < df["open"].shift(1))
            & (df["close"] > df["open"].shift(1))
            & (df["open"] < df["close"].shift(1))
        ).astype(int)
        features["bearish_engulfing"] = (
            (df["close"] < df["open"])
            & (df["close"].shift(1) > df["open"].shift(1))
            & (df["close"] < df["open"].shift(1))
            & (df["open"] > df["close"].shift(1))
        ).astype(int)
        lower_shadow = (df[["open", "close"]].min(axis=1) - df["low"]) / df["close"]
        upper_shadow = (df["high"] - df[["open", "close"]].max(axis=1)) / df["close"]
        features["hammer"] = (
            (lower_shadow > 2 * abs(df["close"] - df["open"]))
            & (upper_shadow < 0.1 * (df["high"] - df["low"]))
        ).astype(int)

        return pd.DataFrame(features)

    def _calc_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """统计特征"""
        features = {}
        pct_change = df["close"].pct_change()
        
        for period in [10, 20]:
            features[f"return_skew_{period}"] = pct_change.rolling(window=period).skew()
            features[f"return_kurt_{period}"] = pct_change.rolling(window=period).kurt()
            features[f"price_range_{period}"] = (
                df["high"].rolling(window=period).max() / df["low"].rolling(window=period).min()
            )

        features["price_zscore_20"] = (df["close"] - df["close"].rolling(window=20).mean()) / df["close"].rolling(
            window=20
        ).std()
        features["volume_zscore_20"] = (df["volume"] - df["volume"].rolling(window=20).mean()) / df["volume"].rolling(
            window=20
        ).std()

        return pd.DataFrame(features)

    def _calc_williams_r(self, df: pd.DataFrame) -> pd.DataFrame:
        """威廉指标 Williams %R"""
        features = {}
        period = 14
        high_max = df["high"].rolling(window=period).max()
        low_min = df["low"].rolling(window=period).min()
        features["williams_r"] = (high_max - df["close"]) / (high_max - low_min) * -100
        features["williams_oversold"] = (features["williams_r"] < -80).astype(int)
        features["williams_overbought"] = (features["williams_r"] > -20).astype(int)
        return pd.DataFrame(features)

    def _calc_cci(self, df: pd.DataFrame) -> pd.DataFrame:
        """CCI指标"""
        features = {}
        period = 20
        tp = (df["high"] + df["low"] + df["close"]) / 3
        ma = tp.rolling(window=period).mean()
        md = tp.rolling(window=period).apply(lambda x: abs(x - x.mean()).mean())
        features["cci"] = (tp - ma) / (0.015 * md)
        features["cci_oversold"] = (features["cci"] < -100).astype(int)
        features["cci_overbought"] = (features["cci"] > 100).astype(int)
        return pd.DataFrame(features)

    def _calc_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """OBV指标"""
        features = {}
        features["obv"] = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
        features["obv_ma10"] = features["obv"].rolling(window=10).mean()
        features["obv_ma20"] = features["obv"].rolling(window=20).mean()
        features["obv_signal"] = (features["obv"] > features["obv_ma10"]).astype(int)
        return pd.DataFrame(features)

    def _calc_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """ADX指标"""
        features = {}
        period = 14
        high = df["high"]
        low = df["low"]
        close = df["close"]

        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0

        tr = pd.concat([high - low, abs(high - close.shift(1)), abs(low - close.shift(1))], axis=1).max(axis=1)

        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (abs(minus_dm).rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        features["adx"] = dx.rolling(window=period).mean()
        features["plus_di"] = plus_di
        features["minus_di"] = minus_di
        features["trend_strength_adx"] = (features["adx"] > 25).astype(int)

        return pd.DataFrame(features)

    def _calc_mfi(self, df: pd.DataFrame) -> pd.DataFrame:
        """MFI指标"""
        features = {}
        period = 14
        tp = (df["high"] + df["low"] + df["close"]) / 3
        mf = tp * df["volume"]

        positive_mf = mf.where(tp > tp.shift(1), 0)
        negative_mf = mf.where(tp < tp.shift(1), 0)

        positive_sum = positive_mf.rolling(window=period).sum()
        negative_sum = negative_mf.rolling(window=period).sum()

        mfi_ratio = positive_sum / negative_sum.replace(0, np.inf)
        features["mfi"] = 100 - (100 / (1 + mfi_ratio))
        features["mfi_oversold"] = (features["mfi"] < 20).astype(int)
        features["mfi_overbought"] = (features["mfi"] > 80).astype(int)

        return pd.DataFrame(features)

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算 ATR"""
        high = df["high"]
        low = df["low"]
        close = df["close"].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def prepare_features_for_prediction(
        self, stock_data: dict[str, Any], market_data: dict[str, Any] | None = None
    ) -> pd.DataFrame:
        """
        准备预测特征

        Args:
            stock_data: 股票数据字典
            market_data: 市场数据字典（可选）

        Returns:
            特征 DataFrame
        """
        df = pd.DataFrame([stock_data])

        if market_data:
            for key, value in market_data.items():
                df[f"market_{key}"] = value

        return df

    def get_feature_importance_names(self) -> list[str]:
        """获取特征名称列表"""
        return self.feature_names

    def save_feature_config(self, path: Path) -> None:
        """保存特征配置"""
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

        with open(path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"特征配置已保存到: {path}")

    def load_feature_config(self, path: Path) -> None:
        """加载特征配置"""
        with open(path, encoding="utf-8") as f:
            config_dict = json.load(f)

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
