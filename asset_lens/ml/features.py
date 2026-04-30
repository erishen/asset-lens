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

        df = self._add_price_features(df)
        df = self._add_ma_features(df)
        df = self._add_macd_features(df)
        df = self._add_rsi_features(df)
        df = self._add_boll_features(df)
        df = self._add_kdj_features(df)
        df = self._add_volume_features(df)
        df = self._add_momentum_features(df)
        df = self._add_volatility_features(df)
        df = self._add_trend_features(df)
        df = self._add_pattern_features(df)
        df = self._add_statistical_features(df)
        df = self._add_williams_r(df)
        df = self._add_cci(df)
        df = self._add_obv(df)
        df = self._add_adx(df)
        df = self._add_mfi(df)

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

    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """价格相关特征"""
        df["pct_change"] = df["close"].pct_change()
        df["pct_change_5d"] = df["close"].pct_change(5)
        df["pct_change_10d"] = df["close"].pct_change(10)
        df["pct_change_20d"] = df["close"].pct_change(20)

        df["high_low_ratio"] = df["high"] / df["low"]
        df["close_open_ratio"] = df["close"] / df["open"]
        df["upper_shadow"] = (df["high"] - df[["open", "close"]].max(axis=1)) / df["close"]
        df["lower_shadow"] = (df[["open", "close"]].min(axis=1) - df["low"]) / df["close"]

        return df

    def _add_ma_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """均线特征"""
        for period in self.config.ma_periods:
            df[f"ma{period}"] = df["close"].rolling(window=period).mean()
            df[f"close_ma{period}_ratio"] = df["close"] / df[f"ma{period}"]

        if "ma5" in df.columns and "ma20" in df.columns:
            df["ma5_ma20_ratio"] = df["ma5"] / df["ma20"]
            df["ma_cross_signal"] = (df["ma5"] > df["ma20"]).astype(int)

        return df

    def _add_macd_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """MACD 特征"""
        exp1 = df["close"].ewm(span=self.config.macd_fast, adjust=False).mean()
        exp2 = df["close"].ewm(span=self.config.macd_slow, adjust=False).mean()

        df["macd"] = exp1 - exp2
        df["macd_signal"] = df["macd"].ewm(span=self.config.macd_signal, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]
        df["macd_cross"] = (
            (df["macd"] > df["macd_signal"]) & (df["macd"].shift(1) <= df["macd_signal"].shift(1))
        ).astype(int)

        return df

    def _add_rsi_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """RSI 特征"""
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.rsi_period).mean()

        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        df["rsi_oversold"] = (df["rsi"] < 30).astype(int)
        df["rsi_overbought"] = (df["rsi"] > 70).astype(int)

        return df

    def _add_boll_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """布林带特征"""
        period = self.config.boll_period
        std_mult = self.config.boll_std

        df["boll_mid"] = df["close"].rolling(window=period).mean()
        df["boll_std"] = df["close"].rolling(window=period).std()
        df["boll_upper"] = df["boll_mid"] + std_mult * df["boll_std"]
        df["boll_lower"] = df["boll_mid"] - std_mult * df["boll_std"]

        df["boll_width"] = (df["boll_upper"] - df["boll_lower"]) / df["boll_mid"]
        df["boll_position"] = (df["close"] - df["boll_lower"]) / (df["boll_upper"] - df["boll_lower"])

        return df

    def _add_kdj_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """KDJ 特征"""
        low_min = df["low"].rolling(window=9).min()
        high_max = df["high"].rolling(window=9).max()

        df["kdj_rsv"] = (df["close"] - low_min) / (high_max - low_min) * 100
        df["kdj_k"] = df["kdj_rsv"].ewm(alpha=1 / 3, adjust=False).mean()
        df["kdj_d"] = df["kdj_k"].ewm(alpha=1 / 3, adjust=False).mean()
        df["kdj_j"] = 3 * df["kdj_k"] - 2 * df["kdj_d"]

        df["kdj_cross"] = ((df["kdj_k"] > df["kdj_d"]) & (df["kdj_k"].shift(1) <= df["kdj_d"].shift(1))).astype(int)

        return df

    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """成交量特征"""
        for period in self.config.volume_ma_periods:
            df[f"volume_ma{period}"] = df["volume"].rolling(window=period).mean()
            df[f"volume_ratio_{period}"] = df["volume"] / df[f"volume_ma{period}"]

        df["volume_change"] = df["volume"].pct_change()
        df["volume_price_trend"] = df["volume_change"] * df["pct_change"]

        if "amount" not in df.columns or df["amount"].isna().all():
            df["amount"] = df["volume"] * df["close"]

        df["amount"] = df["amount"].fillna(df["volume"] * df["close"])

        for period in [5, 10, 20]:
            df[f"amount_ma{period}"] = df["amount"].rolling(window=period).mean()
            df[f"amount_ratio_{period}"] = df["amount"] / df[f"amount_ma{period}"]

        return df

    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """动量特征"""
        df["momentum_5d"] = df["close"] / df["close"].shift(5) - 1
        df["momentum_10d"] = df["close"] / df["close"].shift(10) - 1
        df["momentum_20d"] = df["close"] / df["close"].shift(20) - 1

        df["roc_10"] = (df["close"] - df["close"].shift(10)) / df["close"].shift(10) * 100
        df["roc_20"] = (df["close"] - df["close"].shift(20)) / df["close"].shift(20) * 100

        return df

    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """波动率特征"""
        df["volatility_5d"] = df["pct_change"].rolling(window=5).std()
        df["volatility_10d"] = df["pct_change"].rolling(window=10).std()
        df["volatility_20d"] = df["pct_change"].rolling(window=20).std()

        df["atr"] = self._calculate_atr(df, period=14)
        df["atr_ratio"] = df["atr"] / df["close"]

        df["volatility_ratio"] = df["volatility_5d"] / df["volatility_20d"]

        return df

    def _add_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """趋势特征"""
        df["trend_strength"] = (df["close"] - df["close"].shift(20)) / df["close"].shift(20)
        df["trend_consistency"] = (df["pct_change"] > 0).rolling(window=10).mean()
        df["trend_acceleration"] = df["momentum_5d"] - df["momentum_5d"].shift(5)

        df["higher_high"] = (df["high"] > df["high"].shift(1)).astype(int)
        df["lower_low"] = (df["low"] < df["low"].shift(1)).astype(int)
        df["higher_low"] = (df["low"] > df["low"].shift(1)).astype(int)
        df["lower_high"] = (df["high"] < df["high"].shift(1)).astype(int)

        return df

    def _add_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """K线形态特征"""
        df["doji"] = (abs(df["close"] - df["open"]) / (df["high"] - df["low"]) < 0.1).astype(int)
        df["bullish_engulfing"] = (
            (df["close"] > df["open"])
            & (df["close"].shift(1) < df["open"].shift(1))
            & (df["close"] > df["open"].shift(1))
            & (df["open"] < df["close"].shift(1))
        ).astype(int)
        df["bearish_engulfing"] = (
            (df["close"] < df["open"])
            & (df["close"].shift(1) > df["open"].shift(1))
            & (df["close"] < df["open"].shift(1))
            & (df["open"] > df["close"].shift(1))
        ).astype(int)
        df["hammer"] = (
            (df["lower_shadow"] > 2 * abs(df["close"] - df["open"]))
            & (df["upper_shadow"] < 0.1 * (df["high"] - df["low"]))
        ).astype(int)

        return df

    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """统计特征"""
        for period in [10, 20]:
            df[f"return_skew_{period}"] = df["pct_change"].rolling(window=period).skew()
            df[f"return_kurt_{period}"] = df["pct_change"].rolling(window=period).kurt()
            df[f"price_range_{period}"] = (
                df["high"].rolling(window=period).max() / df["low"].rolling(window=period).min()
            )

        df["price_zscore_20"] = (df["close"] - df["close"].rolling(window=20).mean()) / df["close"].rolling(
            window=20
        ).std()
        df["volume_zscore_20"] = (df["volume"] - df["volume"].rolling(window=20).mean()) / df["volume"].rolling(
            window=20
        ).std()

        return df

    def _add_williams_r(self, df: pd.DataFrame) -> pd.DataFrame:
        """威廉指标 Williams %R"""
        period = 14
        high_max = df["high"].rolling(window=period).max()
        low_min = df["low"].rolling(window=period).min()
        df["williams_r"] = (high_max - df["close"]) / (high_max - low_min) * -100
        df["williams_oversold"] = (df["williams_r"] < -80).astype(int)
        df["williams_overbought"] = (df["williams_r"] > -20).astype(int)
        return df

    def _add_cci(self, df: pd.DataFrame) -> pd.DataFrame:
        """CCI指标"""
        period = 20
        tp = (df["high"] + df["low"] + df["close"]) / 3
        ma = tp.rolling(window=period).mean()
        md = tp.rolling(window=period).apply(lambda x: abs(x - x.mean()).mean())
        df["cci"] = (tp - ma) / (0.015 * md)
        df["cci_oversold"] = (df["cci"] < -100).astype(int)
        df["cci_overbought"] = (df["cci"] > 100).astype(int)
        return df

    def _add_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """OBV指标"""
        df["obv"] = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
        df["obv_ma10"] = df["obv"].rolling(window=10).mean()
        df["obv_ma20"] = df["obv"].rolling(window=20).mean()
        df["obv_signal"] = (df["obv"] > df["obv_ma10"]).astype(int)
        return df

    def _add_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """ADX指标"""
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
        df["adx"] = dx.rolling(window=period).mean()
        df["plus_di"] = plus_di
        df["minus_di"] = minus_di
        df["trend_strength_adx"] = (df["adx"] > 25).astype(int)

        return df

    def _add_mfi(self, df: pd.DataFrame) -> pd.DataFrame:
        """MFI指标"""
        period = 14
        tp = (df["high"] + df["low"] + df["close"]) / 3
        mf = tp * df["volume"]

        positive_mf = mf.where(tp > tp.shift(1), 0)
        negative_mf = mf.where(tp < tp.shift(1), 0)

        positive_sum = positive_mf.rolling(window=period).sum()
        negative_sum = negative_mf.rolling(window=period).sum()

        mfi_ratio = positive_sum / negative_sum.replace(0, np.inf)
        df["mfi"] = 100 - (100 / (1 + mfi_ratio))
        df["mfi_oversold"] = (df["mfi"] < 20).astype(int)
        df["mfi_overbought"] = (df["mfi"] > 80).astype(int)

        return df

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
