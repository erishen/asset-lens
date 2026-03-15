"""
Risk Management System - 风险管理系统
计算风险指标、生成风险预警、提供风险控制建议
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """风险指标"""
    volatility: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    beta: float = 0.0
    var_95: float = 0.0
    concentration_risk: float = 0.0


@dataclass
class RiskAlert:
    """风险预警"""
    level: str
    type: str
    message: str
    value: float
    threshold: float
    timestamp: str
    suggestion: str


class RiskManager:
    """风险管理系统"""
    
    def __init__(self):
        self._cache_path = Path("cache")
        self._cache_path.mkdir(parents=True, exist_ok=True)
        self.risk_history: List[Dict[str, Any]] = []
        
    def calculate_volatility(self, returns: List[float]) -> float:
        """计算波动率"""
        if not returns or len(returns) < 2:
            return 0.0
        
        try:
            returns_array = np.array(returns)
            volatility = np.std(returns_array) * np.sqrt(252)
            return float(volatility)
        except Exception as e:
            logger.error(f"计算波动率失败: {e}")
            return 0.0
    
    def calculate_max_drawdown(self, values: List[float]) -> float:
        """计算最大回撤"""
        if not values or len(values) < 2:
            return 0.0
        
        try:
            values_array = np.array(values)
            peak = values_array[0]
            max_dd = 0.0
            
            for value in values_array:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak if peak > 0 else 0
                if dd > max_dd:
                    max_dd = dd
            
            return float(max_dd * 100)
        except Exception as e:
            logger.error(f"计算最大回撤失败: {e}")
            return 0.0
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.03) -> float:
        """计算夏普比率"""
        if not returns or len(returns) < 2:
            return 0.0
        
        try:
            returns_array = np.array(returns)
            excess_returns = returns_array - risk_free_rate / 252
            
            if np.std(excess_returns) == 0:
                return 0.0
            
            sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
            return float(sharpe)
        except Exception as e:
            logger.error(f"计算夏普比率失败: {e}")
            return 0.0
    
    def calculate_beta(self, stock_returns: List[float], market_returns: List[float]) -> float:
        """计算贝塔系数"""
        if not stock_returns or not market_returns or len(stock_returns) < 2:
            return 0.0
        
        try:
            stock_array = np.array(stock_returns)
            market_array = np.array(market_returns)
            
            covariance = np.cov(stock_array, market_array)[0][1]
            market_variance = np.var(market_array)
            
            if market_variance == 0:
                return 0.0
            
            beta = covariance / market_variance
            return float(beta)
        except Exception as e:
            logger.error(f"计算贝塔系数失败: {e}")
            return 0.0
    
    def calculate_var_95(self, returns: List[float]) -> float:
        """计算VaR (95%置信度)"""
        if not returns or len(returns) < 2:
            return 0.0
        
        try:
            returns_array = np.array(returns)
            var_95 = np.percentile(returns_array, 5)
            return float(abs(var_95))
        except Exception as e:
            logger.error(f"计算VaR失败: {e}")
            return 0.0
    
    def calculate_concentration_risk(self, holdings: Dict[str, float]) -> float:
        """计算集中度风险"""
        if not holdings:
            return 0.0
        
        try:
            total_value = sum(holdings.values())
            if total_value == 0:
                return 0.0
            
            weights = [value / total_value for value in holdings.values()]
            herfindahl_index = sum(w ** 2 for w in weights)
            
            return float(herfindahl_index * 100)
        except Exception as e:
            logger.error(f"计算集中度风险失败: {e}")
            return 0.0
    
    def calculate_all_metrics(self, returns: List[float], values: Optional[List[float]] = None) -> RiskMetrics:
        """计算所有风险指标"""
        metrics = RiskMetrics()
        
        metrics.volatility = self.calculate_volatility(returns)
        
        if values:
            metrics.max_drawdown = self.calculate_max_drawdown(values)
        
        metrics.sharpe_ratio = self.calculate_sharpe_ratio(returns)
        
        metrics.var_95 = self.calculate_var_95(returns)
        
        return metrics
    
    def check_risk_thresholds(self, metrics: RiskMetrics, thresholds: Optional[Dict[str, float]] = None) -> List[RiskAlert]:
        """检查风险阈值"""
        if thresholds is None:
            thresholds = {
                'volatility': 25.0,
                'max_drawdown': 15.0,
                'sharpe_ratio': 0.5,
                'concentration_risk': 30.0
            }
        
        alerts = []
        
        if metrics.volatility > thresholds['volatility']:
            alerts.append(RiskAlert(
                level='high',
                type='volatility',
                message=f"波动率过高: {metrics.volatility:.2f}%",
                value=metrics.volatility,
                threshold=thresholds['volatility'],
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                suggestion="考虑降低仓位或增加对冲"
            ))
        
        if metrics.max_drawdown > thresholds['max_drawdown']:
            alerts.append(RiskAlert(
                level='high',
                type='max_drawdown',
                message=f"最大回撤过大: {metrics.max_drawdown:.2f}%",
                value=metrics.max_drawdown,
                threshold=thresholds['max_drawdown'],
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                suggestion="检查止损策略，考虑减仓"
            ))
        
        if metrics.sharpe_ratio < thresholds['sharpe_ratio']:
            alerts.append(RiskAlert(
                level='medium',
                type='sharpe_ratio',
                message=f"夏普比率过低: {metrics.sharpe_ratio:.2f}",
                value=metrics.sharpe_ratio,
                threshold=thresholds['sharpe_ratio'],
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                suggestion="优化资产配置，提高风险调整后收益"
            ))
        
        if metrics.concentration_risk > thresholds['concentration_risk']:
            alerts.append(RiskAlert(
                level='medium',
                type='concentration_risk',
                message=f"集中度风险过高: {metrics.concentration_risk:.2f}%",
                value=metrics.concentration_risk,
                threshold=thresholds['concentration_risk'],
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                suggestion="分散投资，降低单一资产权重"
            ))
        
        return alerts
    
    def generate_risk_report(self, metrics: RiskMetrics, alerts: List[RiskAlert]) -> str:
        """生成风险报告"""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("⚠️ 风险管理报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        report_lines.append("📊 风险指标:")
        report_lines.append(f"  • 波动率: {metrics.volatility:.2f}%")
        report_lines.append(f"  • 最大回撤: {metrics.max_drawdown:.2f}%")
        report_lines.append(f"  • 夏普比率: {metrics.sharpe_ratio:.2f}")
        report_lines.append(f"  • VaR(95%): {metrics.var_95:.2f}%")
        report_lines.append(f"  • 集中度风险: {metrics.concentration_risk:.2f}%")
        report_lines.append("")
        
        if alerts:
            report_lines.append("🚨 风险预警:")
            for alert in alerts:
                level_emoji = "🔴" if alert.level == 'high' else "🟡"
                report_lines.append(f"  {level_emoji} [{alert.type}] {alert.message}")
                report_lines.append(f"     建议: {alert.suggestion}")
            report_lines.append("")
        
        report_lines.append("💡 风险控制建议:")
        report_lines.append("  • 定期监控风险指标")
        report_lines.append("  • 设置合理的止损止盈点")
        report_lines.append("  • 保持资产配置多元化")
        report_lines.append("  • 避免过度集中投资")
        report_lines.append("")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def save_risk_metrics(self, metrics: RiskMetrics):
        """保存风险指标历史"""
        metrics_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'volatility': metrics.volatility,
            'max_drawdown': metrics.max_drawdown,
            'sharpe_ratio': metrics.sharpe_ratio,
            'beta': metrics.beta,
            'var_95': metrics.var_95,
            'concentration_risk': metrics.concentration_risk
        }
        
        self.risk_history.append(metrics_data)
        
        history_file = self._cache_path / "risk_history.json"
        history_data = []
        
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
            except:
                history_data = []
        
        history_data.append(metrics_data)
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)


def create_risk_manager() -> RiskManager:
    """创建风险管理实例"""
    return RiskManager()
