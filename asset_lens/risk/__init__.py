"""
Risk Module - 统一风险入口
提供风险管理与分析的统一接口

此模块整合了两个风险相关模块的功能：
- RiskManager: 仓位管理、止损止盈、风险预警
- RiskAnalyzer: 风险指标计算、波动率、夏普比率等

使用示例:
    from asset_lens.risk import RiskService
    
    # 获取风险服务
    risk = RiskService()
    
    # 获取风险摘要（仓位、止损止盈）
    summary = risk.get_risk_summary()
    
    # 计算风险指标（波动率、夏普比率）
    metrics = risk.calculate_metrics(returns)
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class RiskSummary:
    """风险摘要"""
    risk_score: float
    risk_level: str
    total_position: float
    warnings: List[str]
    suggestions: List[str]


@dataclass
class RiskMetrics:
    """风险指标"""
    volatility: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    beta: float = 0.0
    var_95: float = 0.0


class RiskService:
    """
    风险服务 - 统一风险入口
    
    整合 RiskManager 和 RiskAnalyzer 的功能，
    提供一站式的风险管理与分析服务。
    """
    
    def __init__(self):
        self._manager = None
        self._analyzer = None
    
    @property
    def manager(self):
        """获取风险管理器（仓位、止损止盈）"""
        if self._manager is None:
            from asset_lens.trading.risk_manager import RiskManager
            self._manager = RiskManager()
        return self._manager
    
    @property
    def analyzer(self):
        """获取风险分析器（指标计算）"""
        if self._analyzer is None:
            from asset_lens.monitoring.risk_analyzer import RiskAnalyzer
            self._analyzer = RiskAnalyzer()
        return self._analyzer
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """
        获取风险摘要
        
        包含仓位、止损止盈、风险预警等信息
        
        Returns:
            风险摘要字典
        """
        result: Dict[str, Any] = self.manager.get_risk_summary()
        return result
    
    def get_position_advice(self) -> Dict[str, Any]:
        """
        获取仓位建议
        
        Returns:
            仓位建议字典
        """
        result: Dict[str, Any] = self.manager.get_position_advice()
        return result
    
    def calculate_metrics(
        self,
        returns: List[float],
        benchmark_returns: Optional[List[float]] = None,
    ) -> RiskMetrics:
        """
        计算风险指标
        
        Args:
            returns: 收益率序列
            benchmark_returns: 基准收益率序列（可选）
            
        Returns:
            RiskMetrics 对象
        """
        metrics_dict = self.analyzer.calculate_all_metrics(returns)
        
        return RiskMetrics(
            volatility=metrics_dict.get("volatility", 0.0),
            max_drawdown=metrics_dict.get("max_drawdown", 0.0),
            sharpe_ratio=metrics_dict.get("sharpe_ratio", 0.0),
            beta=metrics_dict.get("beta", 0.0),
            var_95=metrics_dict.get("var_95", 0.0),
        )
    
    def check_stop_loss(
        self,
        entry_price: float,
        current_price: float,
        stop_loss_pct: float = -0.08,
    ) -> Dict[str, Any]:
        """
        检查止损
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            stop_loss_pct: 止损比例（负数）
            
        Returns:
            止损检查结果
        """
        result: Dict[str, Any] = self.manager.check_stop_loss(entry_price, current_price, stop_loss_pct)
        return result
    
    def calculate_stop_loss_levels(
        self,
        entry_price: float,
        stop_loss_pct: float = -0.08,
        take_profit_pct: float = 0.15,
    ) -> Dict[str, float]:
        """
        计算止损止盈位
        
        Args:
            entry_price: 入场价格
            stop_loss_pct: 止损比例
            take_profit_pct: 止盈比例
            
        Returns:
            止损止盈位字典
        """
        return {
            "entry_price": entry_price,
            "stop_loss_price": entry_price * (1 + stop_loss_pct),
            "take_profit_price": entry_price * (1 + take_profit_pct),
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct,
        }


risk_service = RiskService()


__all__ = ["RiskService", "RiskSummary", "RiskMetrics", "risk_service"]
