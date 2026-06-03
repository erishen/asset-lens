import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)


def safe_divide(a: pd.Series | np.ndarray, b: pd.Series | np.ndarray, fill_value: float = 0.0) -> pd.Series:
    if isinstance(a, np.ndarray):
        a = pd.Series(a)
    if isinstance(b, np.ndarray):
        b = pd.Series(b)

    with np.errstate(divide="ignore", invalid="ignore"):
        result = a / b

    result = result.replace([np.inf, -np.inf], fill_value)
    result = result.fillna(fill_value)

    return result


class TechnicalIndicatorsMixin:
    def _calc_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        features["pct_change"] = df["close"].pct_change().fillna(0)
        features["pct_change_5d"] = df["close"].pct_change(5).fillna(0)
        features["pct_change_10d"] = df["close"].pct_change(10).fillna(0)
        features["pct_change_20d"] = df["close"].pct_change(20).fillna(0)
        features["high_low_ratio"] = safe_divide(df["high"], df["low"], 1.0)
        features["close_open_ratio"] = safe_divide(df["close"], df["open"], 1.0)

        close_safe = df["close"].replace(0, np.nan)
        features["upper_shadow"] = safe_divide(df["high"] - df[["open", "close"]].max(axis=1), close_safe, 0)
        features["lower_shadow"] = safe_divide(df[["open", "close"]].min(axis=1) - df["low"], close_safe, 0)

        return pd.DataFrame(features)

    def _calc_ma_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        for period in self.config.ma_periods:
            rolling_ma = df["close"].rolling(window=period, min_periods=max(period // 2, 1)).mean()
            features[f"ma{period}"] = rolling_ma.fillna(df["close"])
            features[f"close_ma{period}_ratio"] = safe_divide(df["close"], rolling_ma, 1.0)

        if f"ma{self.config.ma_periods[0]}" in features and f"ma{self.config.ma_periods[2]}" in features:
            ma5 = features["ma5"]
            ma20 = features["ma20"]
            features["ma5_ma20_ratio"] = safe_divide(ma5, ma20, 1.0)
            features["ma_cross_signal"] = (ma5 > ma20).astype(int)

        return pd.DataFrame(features)

    def _calc_macd_features(self, df: pd.DataFrame) -> pd.DataFrame:
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
        features = {}
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config.rsi_period).mean().fillna(0)
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.rsi_period).mean().fillna(0.001)

        rs = safe_divide(gain, loss, 0)
        features["rsi"] = (100 - safe_divide(100, 1 + rs, 50)).fillna(50)
        features["rsi_oversold"] = (features["rsi"] < 30).astype(int)
        features["rsi_overbought"] = (features["rsi"] > 70).astype(int)

        return pd.DataFrame(features)

    def _calc_boll_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        period = self.config.boll_period
        std_mult = self.config.boll_std

        features["boll_mid"] = df["close"].rolling(window=period).mean().fillna(df["close"])
        features["boll_std"] = df["close"].rolling(window=period).std().fillna(0)
        features["boll_upper"] = features["boll_mid"] + std_mult * features["boll_std"]
        features["boll_lower"] = features["boll_mid"] - std_mult * features["boll_std"]
        features["boll_width"] = safe_divide(features["boll_upper"] - features["boll_lower"], features["boll_mid"], 0)

        boll_range = features["boll_upper"] - features["boll_lower"]
        features["boll_position"] = safe_divide(df["close"] - features["boll_lower"], boll_range, 0.5)

        return pd.DataFrame(features)

    def _calc_kdj_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        low_min = df["low"].rolling(window=9).min().fillna(df["low"])
        high_max = df["high"].rolling(window=9).max().fillna(df["high"])

        kdj_range = high_max - low_min
        features["kdj_rsv"] = safe_divide(df["close"] - low_min, kdj_range, 0.5) * 100
        features["kdj_k"] = features["kdj_rsv"].ewm(alpha=1 / 3, adjust=False).mean().fillna(50)
        features["kdj_d"] = features["kdj_k"].ewm(alpha=1 / 3, adjust=False).mean().fillna(50)
        features["kdj_j"] = 3 * features["kdj_k"] - 2 * features["kdj_d"]
        features["kdj_cross"] = (
            (features["kdj_k"] > features["kdj_d"]) & (features["kdj_k"].shift(1) <= features["kdj_d"].shift(1))
        ).astype(int)

        return pd.DataFrame(features)

    def _calc_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        for period in self.config.volume_ma_periods:
            vol_ma = df["volume"].rolling(window=period).mean().fillna(df["volume"])
            features[f"volume_ma{period}"] = vol_ma
            features[f"volume_ratio_{period}"] = safe_divide(df["volume"], vol_ma, 1.0)

        features["volume_change"] = df["volume"].pct_change().fillna(0)
        pct_change = df["close"].pct_change().fillna(0)
        features["volume_price_trend"] = features["volume_change"] * pct_change

        amount = df.get("amount", df["volume"] * df["close"])
        if amount.isna().all():
            amount = df["volume"] * df["close"]

        for period in [5, 10, 20]:
            amt_ma = amount.rolling(window=period).mean().fillna(amount)
            features[f"amount_ma{period}"] = amt_ma
            features[f"amount_ratio_{period}"] = safe_divide(amount, amt_ma, 1.0)

        return pd.DataFrame(features)

    def _calc_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        close_shift5 = df["close"].shift(5).replace(0, np.nan)
        close_shift10 = df["close"].shift(10).replace(0, np.nan)
        close_shift20 = df["close"].shift(20).replace(0, np.nan)

        features["momentum_5d"] = safe_divide(df["close"], close_shift5, 1.0) - 1
        features["momentum_10d"] = safe_divide(df["close"], close_shift10, 1.0) - 1
        features["momentum_20d"] = safe_divide(df["close"], close_shift20, 1.0) - 1
        features["roc_10"] = safe_divide(df["close"] - close_shift10, close_shift10, 0) * 100
        features["roc_20"] = safe_divide(df["close"] - close_shift20, close_shift20, 0) * 100

        return pd.DataFrame(features)

    def _calc_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        pct_change = df["close"].pct_change()
        features["volatility_5d"] = pct_change.rolling(window=5).std().fillna(0)
        features["volatility_10d"] = pct_change.rolling(window=10).std().fillna(0)
        features["volatility_20d"] = pct_change.rolling(window=20).std().fillna(0)

        features["atr"] = self._calculate_atr(df, period=14).fillna(0)
        features["atr_ratio"] = safe_divide(features["atr"], df["close"], 0)
        features["volatility_ratio"] = safe_divide(features["volatility_5d"], features["volatility_20d"], 1.0)

        return pd.DataFrame(features)

    def _calc_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        pct_change = df["close"].pct_change().fillna(0)
        close_shift20 = df["close"].shift(20).replace(0, np.nan)

        features["trend_strength"] = safe_divide(df["close"] - close_shift20, close_shift20, 0)
        features["trend_consistency"] = (pct_change > 0).rolling(window=10).mean().fillna(0.5)

        momentum_5d = safe_divide(df["close"], df["close"].shift(5), 1.0) - 1
        features["trend_acceleration"] = (momentum_5d - momentum_5d.shift(5)).fillna(0)
        features["higher_high"] = (df["high"] > df["high"].shift(1)).astype(int)
        features["lower_low"] = (df["low"] < df["low"].shift(1)).astype(int)
        features["higher_low"] = (df["low"] > df["low"].shift(1)).astype(int)
        features["lower_high"] = (df["high"] < df["high"].shift(1)).astype(int)

        return pd.DataFrame(features)

    def _calc_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}

        hl_range = df["high"] - df["low"]
        features["doji"] = (safe_divide(abs(df["close"] - df["open"]), hl_range, 0) < 0.1).astype(int)

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

        close_safe = df["close"].replace(0, np.nan)
        lower_shadow = safe_divide(df[["open", "close"]].min(axis=1) - df["low"], close_safe, 0)
        upper_shadow = safe_divide(df["high"] - df[["open", "close"]].max(axis=1), close_safe, 0)

        features["hammer"] = (
            (lower_shadow > 2 * abs(df["close"] - df["open"])) & (upper_shadow < 0.1 * hl_range.fillna(0))
        ).astype(int)

        return pd.DataFrame(features)

    def _calc_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        pct_change = df["close"].pct_change().fillna(0)

        for period in [10, 20]:
            features[f"return_skew_{period}"] = pct_change.rolling(window=period).skew().fillna(0)
            features[f"return_kurt_{period}"] = pct_change.rolling(window=period).kurt().fillna(0)

            low_min = df["low"].rolling(window=period).min().replace(0, np.nan)
            features[f"price_range_{period}"] = safe_divide(df["high"].rolling(window=period).max(), low_min, 1.0)

        close_mean = df["close"].rolling(window=20).mean()
        close_std = df["close"].rolling(window=20).std().replace(0, np.nan)
        features["price_zscore_20"] = safe_divide(df["close"] - close_mean, close_std, 0)

        volume_mean = df["volume"].rolling(window=20).mean()
        volume_std = df["volume"].rolling(window=20).std().replace(0, np.nan)
        features["volume_zscore_20"] = safe_divide(df["volume"] - volume_mean, volume_std, 0)

        return pd.DataFrame(features)

    def _calc_williams_r(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        period = 14
        high_max = df["high"].rolling(window=period).max().fillna(df["high"])
        low_min = df["low"].rolling(window=period).min().fillna(df["low"])

        wr_range = high_max - low_min
        features["williams_r"] = safe_divide(high_max - df["close"], wr_range, 0.5) * -100
        features["williams_oversold"] = (features["williams_r"] < -80).astype(int)
        features["williams_overbought"] = (features["williams_r"] > -20).astype(int)
        return pd.DataFrame(features)

    def _calc_cci(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        period = 20
        tp = (df["high"] + df["low"] + df["close"]) / 3
        ma = tp.rolling(window=period).mean().fillna(tp)
        md = tp.rolling(window=period).apply(lambda x: abs(x - x.mean()).mean()).fillna(0.001)

        features["cci"] = safe_divide(tp - ma, 0.015 * md, 0)
        features["cci_oversold"] = (features["cci"] < -100).astype(int)
        features["cci_overbought"] = (features["cci"] > 100).astype(int)
        return pd.DataFrame(features)

    def _calc_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        features["obv"] = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
        features["obv_ma10"] = features["obv"].rolling(window=10).mean()
        features["obv_ma20"] = features["obv"].rolling(window=20).mean()
        features["obv_signal"] = (features["obv"] > features["obv_ma10"]).astype(int)
        return pd.DataFrame(features)

    def _calc_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        period = 14
        high = df["high"]
        low = df["low"]
        close = df["close"]

        plus_dm = high.diff().fillna(0)
        minus_dm = low.diff().fillna(0)
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0

        tr = pd.concat([high - low, abs(high - close.shift(1)), abs(low - close.shift(1))], axis=1).max(axis=1)

        atr = tr.rolling(window=period).mean().replace(0, np.nan)
        plus_di = 100 * safe_divide(plus_dm.rolling(window=period).mean(), atr, 0)
        minus_di = 100 * safe_divide(abs(minus_dm).rolling(window=period).mean(), atr, 0)

        di_sum = (plus_di + minus_di).replace(0, np.nan)
        dx = 100 * safe_divide(abs(plus_di - minus_di), di_sum, 0)
        features["adx"] = dx.rolling(window=period).mean().fillna(0)
        features["plus_di"] = plus_di.fillna(0)
        features["minus_di"] = minus_di.fillna(0)
        features["trend_strength_adx"] = (features["adx"] > 25).astype(int)

        return pd.DataFrame(features)

    def _calc_mfi(self, df: pd.DataFrame) -> pd.DataFrame:
        features = {}
        period = 14
        tp = (df["high"] + df["low"] + df["close"]) / 3
        mf = tp * df["volume"]

        positive_mf = mf.where(tp > tp.shift(1), 0)
        negative_mf = mf.where(tp < tp.shift(1), 0)

        positive_sum = positive_mf.rolling(window=period).sum().fillna(0)
        negative_sum = negative_mf.rolling(window=period).sum().replace(0, np.nan)

        mfi_ratio = safe_divide(positive_sum, negative_sum, 0)
        features["mfi"] = (100 - safe_divide(100, 1 + mfi_ratio, 50)).fillna(50)
        features["mfi_oversold"] = (features["mfi"] < 20).astype(int)
        features["mfi_overbought"] = (features["mfi"] > 80).astype(int)

        return pd.DataFrame(features)

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close = df["close"].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr
