"""
Risk Analyzer System - 风险分析系统
计算风险指标、生成风险预警、提供风险控制建议

职责说明:
    此模块 (monitoring/risk_analyzer.py) - RiskAnalyzer:
    - 风险指标计算 - 波动率、夏普比率、最大回撤、VaR 等
    - 风险预警生成 - 基于阈值的风险预警
    - 风险报告生成 - 生成风险分析报告
    - 市场环境判断 - 判断牛市/熊市/震荡/危机
    - 适用于: 风险分析报告、投资组合评估

    另请参阅: trading/risk_manager.py - RiskManager
    - 仓位管理建议 - 根据市场环境和风险偏好建议仓位
    - 止损止盈提醒 - 自动计算和提醒止损止盈位
    - 适用于: 交易决策、仓位控制

使用示例:
    from asset_lens.monitoring.risk_analyzer import RiskAnalyzer
    analyzer = RiskAnalyzer()
    metrics = analyzer.calculate_all_metrics(returns)
    regime = analyzer.detect_market_regime(index_returns)
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """市场环境类型"""
    BULL = "bull"          # 牛市 - 上涨趋势
    BEAR = "bear"          # 熊市 - 下跌趋势
    SIDEWAYS = "sideways"  # 震荡 - 横盘整理
    CRISIS = "crisis"      # 危机 - 极端波动


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


class RiskAnalyzer:
    """风险分析系统"""

    def __init__(self):
        self._cache_path = Path("cache")
        self._cache_path.mkdir(parents=True, exist_ok=True)
        self.risk_history: list[dict[str, Any]] = []

    def calculate_volatility(self, returns: list[float]) -> float:
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

    def calculate_max_drawdown(self, values: list[float]) -> float:
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

    def calculate_sharpe_ratio(self, returns: list[float], risk_free_rate: float = 0.03) -> float:
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

    def calculate_beta(self, stock_returns: list[float], market_returns: list[float]) -> float:
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

    def calculate_var_95(self, returns: list[float]) -> float:
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

    def calculate_concentration_risk(self, holdings: dict[str, float]) -> float:
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

    def calculate_all_metrics(self, returns: list[float], values: list[float] | None = None) -> RiskMetrics:
        """计算所有风险指标"""
        metrics = RiskMetrics()

        metrics.volatility = self.calculate_volatility(returns)

        if values:
            metrics.max_drawdown = self.calculate_max_drawdown(values)

        metrics.sharpe_ratio = self.calculate_sharpe_ratio(returns)

        metrics.var_95 = self.calculate_var_95(returns)

        return metrics

    def check_risk_thresholds(self, metrics: RiskMetrics, thresholds: dict[str, float] | None = None) -> list[RiskAlert]:
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

    def generate_risk_report(self, metrics: RiskMetrics, alerts: list[RiskAlert]) -> str:
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
                with open(history_file, encoding='utf-8') as f:
                    history_data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"加载历史数据失败: {e}")
                history_data = []

        history_data.append(metrics_data)

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)

    def detect_market_regime(
        self,
        index_returns: list[float],
        lookback_periods: int = 20,
    ) -> MarketRegime:
        """
        判断市场环境

        基于指数收益率判断当前市场环境:
        - 牛市: 收益率 > 10%, 波动率 < 25%
        - 熊市: 收益率 < -10%, 波动率 < 30%
        - 危机: 波动率 > 40% 或 最大回撤 > 20%
        - 震荡: 其他情况

        Args:
            index_returns: 指数收益率序列
            lookback_periods: 回看期数

        Returns:
            MarketRegime 市场环境类型
        """
        if not index_returns or len(index_returns) < lookback_periods:
            return MarketRegime.SIDEWAYS

        try:
            recent_returns = index_returns[-lookback_periods:]
            returns_array = np.array(recent_returns)

            cumulative_return = (1 + returns_array).prod() - 1
            volatility = np.std(returns_array) * np.sqrt(252) * 100

            values = np.cumprod(1 + returns_array) * 100
            peak = np.maximum.accumulate(values)
            drawdown = (peak - values) / peak * 100
            max_drawdown = np.max(drawdown)

            if volatility > 40 or max_drawdown > 20:
                return MarketRegime.CRISIS

            if cumulative_return > 0.10 and volatility < 25:
                return MarketRegime.BULL

            if cumulative_return < -0.10 and volatility < 30:
                return MarketRegime.BEAR

            return MarketRegime.SIDEWAYS

        except Exception as e:
            logger.error(f"判断市场环境失败: {e}")
            return MarketRegime.SIDEWAYS

    def get_regime_thresholds(self, regime: MarketRegime) -> dict[str, float]:
        """
        根据市场环境获取风险阈值

        Args:
            regime: 市场环境类型

        Returns:
            风险阈值字典
        """
        REGIME_THRESHOLDS = {
            MarketRegime.BULL: {
                'volatility': 30.0,
                'max_drawdown': 15.0,
                'sharpe_ratio': 0.5,
                'concentration_risk': 40.0,
                'stop_loss': -0.10,
                'position_limit': 0.8,
            },
            MarketRegime.BEAR: {
                'volatility': 20.0,
                'max_drawdown': 10.0,
                'sharpe_ratio': 0.3,
                'concentration_risk': 25.0,
                'stop_loss': -0.05,
                'position_limit': 0.5,
            },
            MarketRegime.SIDEWAYS: {
                'volatility': 25.0,
                'max_drawdown': 12.0,
                'sharpe_ratio': 0.4,
                'concentration_risk': 30.0,
                'stop_loss': -0.08,
                'position_limit': 0.6,
            },
            MarketRegime.CRISIS: {
                'volatility': 15.0,
                'max_drawdown': 5.0,
                'sharpe_ratio': 0.0,
                'concentration_risk': 20.0,
                'stop_loss': -0.03,
                'position_limit': 0.3,
            },
        }

        return REGIME_THRESHOLDS.get(regime, REGIME_THRESHOLDS[MarketRegime.SIDEWAYS])

    def get_regime_description(self, regime: MarketRegime) -> str:
        """获取市场环境描述"""
        descriptions = {
            MarketRegime.BULL: "🐂 牛市 - 市场上涨趋势，可适当提高仓位",
            MarketRegime.BEAR: "🐻 熊市 - 市场下跌趋势，建议降低仓位",
            MarketRegime.SIDEWAYS: "📊 震荡 - 市场横盘整理，保持中性仓位",
            MarketRegime.CRISIS: "⚠️ 危机 - 市场极端波动，建议大幅降低仓位",
        }
        return descriptions.get(regime, "未知市场环境")


def create_risk_analyzer() -> RiskAnalyzer:
    """创建风险分析实例"""
    return RiskAnalyzer()
