"""
Advanced Investment Strategies - 高级投资策略
包含多种量化策略：趋势跟踪、均值回归、因子投资等
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class StrategySignal:
    """策略信号"""
    code: str
    name: str
    signal: str  # buy, sell, hold
    confidence: float  # 0-1
    price: float
    timestamp: str
    metadata: Dict[str, Any]


class TrendFollowingStrategy:
    """趋势跟踪策略"""
    
    def __init__(
        self,
        short_window: int = 20,
        long_window: int = 60,
        stop_loss: float = 0.05,
        take_profit: float = 0.15
    ):
        """
        初始化趋势跟踪策略
        
        Args:
            short_window: 短期均线周期
            long_window: 长期均线周期
            stop_loss: 止损比例
            take_profit: 止盈比例
        """
        self.short_window = short_window
        self.long_window = long_window
        self.stop_loss = stop_loss
        self.take_profit = take_profit
    
    def generate_signals(
        self,
        prices: pd.DataFrame,
        volume: Optional[pd.Series] = None
    ) -> List[StrategySignal]:
        """
        生成交易信号
        
        Args:
            prices: 价格数据 (OHLCV)
            volume: 成交量数据
            
        Returns:
            交易信号列表
        """
        signals = []
        
        # 计算均线
        short_ma = prices['close'].rolling(window=self.short_window).mean()
        long_ma = prices['close'].rolling(window=self.long_window).mean()
        
        # 计算趋势强度
        trend_strength = (short_ma - long_ma) / long_ma
        
        # 生成信号
        for i in range(len(prices)):
            if i < self.long_window:
                continue
            
            current_price = prices['close'].iloc[i]
            current_short_ma = short_ma.iloc[i]
            current_long_ma = long_ma.iloc[i]
            current_strength = trend_strength.iloc[i]
            
            # 金叉买入信号
            if current_short_ma > current_long_ma and short_ma.iloc[i-1] <= long_ma.iloc[i-1]:
                signal = StrategySignal(
                    code=prices.index[i] if isinstance(prices.index[i], str) else f"stock_{i}",
                    name="趋势跟踪策略",
                    signal="buy",
                    confidence=min(abs(current_strength) * 10, 1.0),
                    price=current_price,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    metadata={
                        "short_ma": current_short_ma,
                        "long_ma": current_long_ma,
                        "trend_strength": current_strength
                    }
                )
                signals.append(signal)
            
            # 死叉卖出信号
            elif current_short_ma < current_long_ma and short_ma.iloc[i-1] >= long_ma.iloc[i-1]:
                signal = StrategySignal(
                    code=prices.index[i] if isinstance(prices.index[i], str) else f"stock_{i}",
                    name="趋势跟踪策略",
                    signal="sell",
                    confidence=min(abs(current_strength) * 10, 1.0),
                    price=current_price,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    metadata={
                        "short_ma": current_short_ma,
                        "long_ma": current_long_ma,
                        "trend_strength": current_strength
                    }
                )
                signals.append(signal)
        
        return signals


class MeanReversionStrategy:
    """均值回归策略"""
    
    def __init__(
        self,
        window: int = 20,
        std_threshold: float = 2.0,
        max_holding_period: int = 10
    ):
        """
        初始化均值回归策略
        
        Args:
            window: 均值计算窗口
            std_threshold: 标准差阈值
            max_holding_period: 最大持有期
        """
        self.window = window
        self.std_threshold = std_threshold
        self.max_holding_period = max_holding_period
    
    def generate_signals(
        self,
        prices: pd.DataFrame,
        volume: Optional[pd.Series] = None
    ) -> List[StrategySignal]:
        """
        生成交易信号
        
        Args:
            prices: 价格数据
            volume: 成交量数据
            
        Returns:
            交易信号列表
        """
        signals = []
        
        # 计算均值和标准差
        rolling_mean = prices['close'].rolling(window=self.window).mean()
        rolling_std = prices['close'].rolling(window=self.window).std()
        
        # 计算 Z-score
        z_score = (prices['close'] - rolling_mean) / rolling_std
        
        # 生成信号
        for i in range(len(prices)):
            if i < self.window:
                continue
            
            current_price = prices['close'].iloc[i]
            current_z_score = z_score.iloc[i]
            current_mean = rolling_mean.iloc[i]
            
            # 价格低于均值2个标准差，买入信号
            if current_z_score < -self.std_threshold:
                signal = StrategySignal(
                    code=prices.index[i] if isinstance(prices.index[i], str) else f"stock_{i}",
                    name="均值回归策略",
                    signal="buy",
                    confidence=min(abs(current_z_score) / 5, 1.0),
                    price=current_price,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    metadata={
                        "z_score": current_z_score,
                        "mean": current_mean,
                        "std": rolling_std.iloc[i]
                    }
                )
                signals.append(signal)
            
            # 价格高于均值2个标准差，卖出信号
            elif current_z_score > self.std_threshold:
                signal = StrategySignal(
                    code=prices.index[i] if isinstance(prices.index[i], str) else f"stock_{i}",
                    name="均值回归策略",
                    signal="sell",
                    confidence=min(abs(current_z_score) / 5, 1.0),
                    price=current_price,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    metadata={
                        "z_score": current_z_score,
                        "mean": current_mean,
                        "std": rolling_std.iloc[i]
                    }
                )
                signals.append(signal)
        
        return signals


class FactorInvestingStrategy:
    """因子投资策略"""
    
    def __init__(
        self,
        factors: Optional[List[str]] = None,
        factor_weights: Optional[Dict[str, float]] = None
    ):
        """
        初始化因子投资策略
        
        Args:
            factors: 因子列表
            factor_weights: 因子权重
        """
        self.factors = factors or ["momentum", "value", "quality", "size"]
        self.factor_weights = factor_weights or {
            "momentum": 0.3,
            "value": 0.3,
            "quality": 0.2,
            "size": 0.2
        }
    
    def calculate_momentum_factor(self, prices: pd.DataFrame) -> pd.Series:
        """计算动量因子"""
        return prices['close'].pct_change(periods=252)
    
    def calculate_value_factor(self, fundamentals: pd.DataFrame) -> pd.Series:
        """计算价值因子"""
        return 1 / fundamentals['pe_ratio']
    
    def calculate_quality_factor(self, fundamentals: pd.DataFrame) -> pd.Series:
        """计算质量因子"""
        return fundamentals['roe']
    
    def calculate_size_factor(self, fundamentals: pd.DataFrame) -> pd.Series:
        """计算规模因子"""
        return -np.log(fundamentals['market_cap'])
    
    def generate_signals(
        self,
        prices: pd.DataFrame,
        fundamentals: Optional[pd.DataFrame] = None
    ) -> List[StrategySignal]:
        """
        生成交易信号
        
        Args:
            prices: 价格数据
            fundamentals: 基本面数据
            
        Returns:
            交易信号列表
        """
        signals = []
        
        # 计算因子得分
        factor_scores = pd.DataFrame()
        
        if "momentum" in self.factors:
            factor_scores["momentum"] = self.calculate_momentum_factor(prices)
        
        if fundamentals is not None:
            if "value" in self.factors:
                factor_scores["value"] = self.calculate_value_factor(fundamentals)
            
            if "quality" in self.factors:
                factor_scores["quality"] = self.calculate_quality_factor(fundamentals)
            
            if "size" in self.factors:
                factor_scores["size"] = self.calculate_size_factor(fundamentals)
        
        # 标准化因子得分
        factor_scores = (factor_scores - factor_scores.mean()) / factor_scores.std()
        
        # 计算综合得分
        total_score = sum(
            factor_scores[factor] * self.factor_weights[factor]
            for factor in self.factors
            if factor in factor_scores.columns
        )
        
        # 生成信号
        for i in range(len(prices)):
            if i < 252:
                continue
            
            current_score = total_score.iloc[i]
            current_price = prices['close'].iloc[i]
            
            # 高得分买入信号
            if current_score > 1.5:
                signal = StrategySignal(
                    code=prices.index[i] if isinstance(prices.index[i], str) else f"stock_{i}",
                    name="因子投资策略",
                    signal="buy",
                    confidence=min(current_score / 3, 1.0),
                    price=current_price,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    metadata={
                        "total_score": current_score,
                        "factor_scores": factor_scores.iloc[i].to_dict()
                    }
                )
                signals.append(signal)
            
            # 低得分卖出信号
            elif current_score < -1.5:
                signal = StrategySignal(
                    code=prices.index[i] if isinstance(prices.index[i], str) else f"stock_{i}",
                    name="因子投资策略",
                    signal="sell",
                    confidence=min(abs(current_score) / 3, 1.0),
                    price=current_price,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    metadata={
                        "total_score": current_score,
                        "factor_scores": factor_scores.iloc[i].to_dict()
                    }
                )
                signals.append(signal)
        
        return signals


class PortfolioOptimizer:
    """投资组合优化器"""
    
    def __init__(
        self,
        risk_free_rate: float = 0.03,
        target_return: Optional[float] = None,
        max_risk: Optional[float] = None
    ):
        """
        初始化投资组合优化器
        
        Args:
            risk_free_rate: 无风险利率
            target_return: 目标收益率
            max_risk: 最大风险
        """
        self.risk_free_rate = risk_free_rate
        self.target_return = target_return
        self.max_risk = max_risk
    
    def optimize(
        self,
        returns: pd.DataFrame,
        method: str = "max_sharpe"
    ) -> Dict[str, float]:
        """
        优化投资组合权重
        
        Args:
            returns: 收益率数据
            method: 优化方法 (max_sharpe, min_risk, risk_parity)
            
        Returns:
            最优权重
        """
        # 计算期望收益率和协方差矩阵
        expected_returns = returns.mean()
        cov_matrix = returns.cov()
        
        n_assets = len(expected_returns)
        
        # 简单优化示例（实际应使用 scipy.optimize）
        if method == "max_sharpe":
            # 最大化夏普比率
            weights = self._max_sharpe_ratio(expected_returns, cov_matrix)
        elif method == "min_risk":
            # 最小化风险
            weights = self._min_risk(cov_matrix)
        elif method == "risk_parity":
            # 风险平价
            weights = self._risk_parity(cov_matrix)
        else:
            # 等权重
            weights = np.ones(n_assets) / n_assets
        
        # 转换为字典
        weight_dict = {
            asset: weight
            for asset, weight in zip(returns.columns, weights)
        }
        
        return weight_dict
    
    def _max_sharpe_ratio(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame
    ) -> np.ndarray:
        """最大化夏普比率"""
        # 简化实现：使用收益风险比
        sharpe_ratios = expected_returns / np.sqrt(np.diag(cov_matrix))
        weights = sharpe_ratios / sharpe_ratios.sum()
        return np.asarray(weights.values)
    
    def _min_risk(self, cov_matrix: pd.DataFrame) -> np.ndarray:
        """最小化风险"""
        # 简化实现：使用逆方差
        inv_var = 1 / np.diag(cov_matrix)
        weights = inv_var / inv_var.sum()
        return np.asarray(weights)
    
    def _risk_parity(self, cov_matrix: pd.DataFrame) -> np.ndarray:
        """风险平价"""
        # 简化实现：使用逆波动率
        inv_vol = 1 / np.sqrt(np.diag(cov_matrix))
        weights = inv_vol / inv_vol.sum()
        return np.asarray(weights)
