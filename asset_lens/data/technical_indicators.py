"""
Technical Indicators Calculator.
技术指标计算器

支持的技术指标:
1. RSI - 相对强弱指数
2. BOLL - 布林带
3. OBV - 能量潮
4. WR - 威廉指标
5. ATR - 平均真实波幅
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import math


@dataclass
class IndicatorResult:
    """指标结果"""
    name: str
    value: float
    signal: str  # buy, sell, hold
    description: str


class TechnicalIndicators:
    """技术指标计算器"""

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        计算 RSI (相对强弱指数)
        
        Args:
            prices: 价格列表
            period: 周期，默认14
            
        Returns:
            RSI 值 (0-100)
        """
        if len(prices) < period + 1:
            return None
        
        gains: list[float] = []
        losses: list[float] = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)

    @staticmethod
    def calculate_boll(
        prices: List[float], 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Optional[Tuple[float, float, float]]:
        """
        计算布林带
        
        Args:
            prices: 价格列表
            period: 周期，默认20
            std_dev: 标准差倍数，默认2
            
        Returns:
            (上轨, 中轨, 下轨)
        """
        if len(prices) < period:
            return None
        
        recent_prices = prices[-period:]
        middle = sum(recent_prices) / period
        
        variance = sum((p - middle) ** 2 for p in recent_prices) / period
        std = math.sqrt(variance)
        
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        
        return (round(upper, 2), round(middle, 2), round(lower, 2))

    @staticmethod
    def calculate_obv(
        prices: List[float], 
        volumes: List[float]
    ) -> Optional[float]:
        """
        计算 OBV (能量潮)
        
        Args:
            prices: 价格列表
            volumes: 成交量列表
            
        Returns:
            OBV 值
        """
        if len(prices) != len(volumes) or len(prices) < 2:
            return None
        
        obv = 0.0
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:
                obv += volumes[i]
            elif prices[i] < prices[i - 1]:
                obv -= volumes[i]
        
        return round(obv, 2)

    @staticmethod
    def calculate_wr(
        high_prices: List[float],
        low_prices: List[float],
        close_prices: List[float],
        period: int = 14
    ) -> Optional[float]:
        """
        计算 WR (威廉指标)
        
        Args:
            high_prices: 最高价列表
            low_prices: 最低价列表
            close_prices: 收盘价列表
            period: 周期，默认14
            
        Returns:
            WR 值 (-100 to 0)
        """
        if len(high_prices) < period:
            return None
        
        recent_high = max(high_prices[-period:])
        recent_low = min(low_prices[-period:])
        current_close = close_prices[-1]
        
        if recent_high == recent_low:
            return None
        
        wr = (recent_high - current_close) / (recent_high - recent_low) * -100
        
        return round(wr, 2)

    @staticmethod
    def calculate_atr(
        high_prices: List[float],
        low_prices: List[float],
        close_prices: List[float],
        period: int = 14
    ) -> Optional[float]:
        """
        计算 ATR (平均真实波幅)
        
        Args:
            high_prices: 最高价列表
            low_prices: 最低价列表
            close_prices: 收盘价列表
            period: 周期，默认14
            
        Returns:
            ATR 值
        """
        if len(high_prices) < period + 1:
            return None
        
        true_ranges = []
        for i in range(1, len(high_prices)):
            tr1 = high_prices[i] - low_prices[i]
            tr2 = abs(high_prices[i] - close_prices[i - 1])
            tr3 = abs(low_prices[i] - close_prices[i - 1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        atr = sum(true_ranges[-period:]) / period
        
        return round(atr, 4)

    @staticmethod
    def get_rsi_signal(rsi: float) -> str:
        """获取 RSI 信号"""
        if rsi >= 70:
            return "sell"
        elif rsi <= 30:
            return "buy"
        else:
            return "hold"

    @staticmethod
    def get_boll_signal(price: float, upper: float, lower: float) -> str:
        """获取布林带信号"""
        if price >= upper:
            return "sell"
        elif price <= lower:
            return "buy"
        else:
            return "hold"

    @staticmethod
    def get_wr_signal(wr: float) -> str:
        """获取威廉指标信号"""
        if wr >= -20:
            return "sell"
        elif wr <= -80:
            return "buy"
        else:
            return "hold"


technical_indicators = TechnicalIndicators()
