"""
Strategy Evaluator - 策略评估与解释层
解释策略表现，分析因子贡献

功能:
1. 因子贡献分析 - 哪些因子贡献最大
2. 失效分析 - 什么时候失效
3. 风格敏感度 - 对市场风格的敏感度
4. 过拟合检测 - 是否过拟合

输出:
- 策略可用性判定
- 风险提示
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class MarketStyle(Enum):
    """市场风格"""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"


class StrategyUsability(Enum):
    """策略可用性"""
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    UNUSABLE = "unusable"


@dataclass
class FactorContribution:
    """因子贡献"""
    factor_name: str
    category: str
    contribution_pct: float
    win_rate: float
    avg_return: float
    correlation: float
    importance_rank: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_name": self.factor_name,
            "category": self.category,
            "contribution_pct": round(self.contribution_pct, 2),
            "win_rate": round(self.win_rate, 2),
            "avg_return": round(self.avg_return, 2),
            "correlation": round(self.correlation, 3),
            "importance_rank": self.importance_rank,
        }


@dataclass
class StyleSensitivity:
    """风格敏感度"""
    style: MarketStyle
    return_rate: float
    win_rate: float
    trade_count: int
    avg_holding_days: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "style": self.style.value,
            "return_rate": round(self.return_rate, 2),
            "win_rate": round(self.win_rate, 2),
            "trade_count": self.trade_count,
            "avg_holding_days": round(self.avg_holding_days, 1),
        }


@dataclass
class FailureAnalysis:
    """失效分析"""
    period: str
    market_style: MarketStyle
    return_rate: float
    failure_reasons: List[str]
    affected_factors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "market_style": self.market_style.value,
            "return_rate": round(self.return_rate, 2),
            "failure_reasons": self.failure_reasons,
            "affected_factors": self.affected_factors,
        }


@dataclass
class OverfittingCheck:
    """过拟合检测"""
    is_overfitted: bool
    confidence: float
    in_sample_return: float
    out_sample_return: float
    return_gap: float
    sharpe_gap: float
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_overfitted": self.is_overfitted,
            "confidence": round(self.confidence, 2),
            "in_sample_return": round(self.in_sample_return, 2),
            "out_sample_return": round(self.out_sample_return, 2),
            "return_gap": round(self.return_gap, 2),
            "sharpe_gap": round(self.sharpe_gap, 2),
            "warnings": self.warnings,
        }


@dataclass
class EvaluationResult:
    """评估结果"""
    strategy_name: str
    usability: StrategyUsability
    total_score: float
    factor_contributions: List[FactorContribution]
    style_sensitivities: List[StyleSensitivity]
    failure_periods: List[FailureAnalysis]
    overfitting_check: OverfittingCheck
    risk_warnings: List[str]
    recommendations: List[str]
    evaluation_date: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "usability": self.usability.value,
            "total_score": round(self.total_score, 2),
            "factor_contributions": [f.to_dict() for f in self.factor_contributions],
            "style_sensitivities": [s.to_dict() for s in self.style_sensitivities],
            "failure_periods": [f.to_dict() for f in self.failure_periods],
            "overfitting_check": self.overfitting_check.to_dict(),
            "risk_warnings": self.risk_warnings,
            "recommendations": self.recommendations,
            "evaluation_date": self.evaluation_date,
        }


class StrategyEvaluator:
    """策略评估器"""
    
    def __init__(self):
        self.min_sample_trades = 30
        self.overfitting_threshold = 0.3
    
    def analyze_factor_contributions(
        self,
        trades: List[Dict[str, Any]],
        factor_data: Dict[str, List[Dict[str, Any]]],
    ) -> List[FactorContribution]:
        """分析因子贡献"""
        contributions: List[FactorContribution] = []
        
        for factor_name, factor_values in factor_data.items():
            factor_trades = []
            for trade in trades:
                code = trade.get("code", "")
                for fv in factor_values:
                    if fv.get("code") == code and fv.get("factor") == factor_name:
                        factor_trades.append({
                            **trade,
                            "factor_value": fv.get("value"),
                        })
                        break
            
            if not factor_trades:
                continue
            
            win_trades = [t for t in factor_trades if t.get("profit", 0) > 0]
            total_profit = sum(t.get("profit", 0) for t in factor_trades)
            avg_return = sum(t.get("profit_rate", 0) for t in factor_trades) / len(factor_trades)
            
            contributions.append(FactorContribution(
                factor_name=factor_name,
                category=factor_values[0].get("category", "unknown") if factor_values else "unknown",
                contribution_pct=total_profit,
                win_rate=len(win_trades) / len(factor_trades) * 100 if factor_trades else 0,
                avg_return=avg_return * 100,
                correlation=0.0,
                importance_rank=0,
            ))
        
        contributions.sort(key=lambda x: x.contribution_pct, reverse=True)
        for i, c in enumerate(contributions):
            c.importance_rank = i + 1
        
        return contributions
    
    def analyze_style_sensitivity(
        self,
        trades: List[Dict[str, Any]],
        market_styles: List[Dict[str, Any]],
    ) -> List[StyleSensitivity]:
        """分析风格敏感度"""
        sensitivities: List[StyleSensitivity] = []
        
        style_trades: Dict[MarketStyle, List[Dict[str, Any]]] = {
            MarketStyle.BULL: [],
            MarketStyle.BEAR: [],
            MarketStyle.SIDEWAYS: [],
            MarketStyle.VOLATILE: [],
        }
        
        for trade in trades:
            trade_date = trade.get("date", "")
            for ms in market_styles:
                if ms.get("date") == trade_date:
                    style = MarketStyle(ms.get("style", "sideways"))
                    style_trades[style].append(trade)
                    break
        
        for style, style_trade_list in style_trades.items():
            if not style_trade_list:
                continue
            
            win_trades = [t for t in style_trade_list if t.get("profit", 0) > 0]
            total_return = sum(t.get("profit_rate", 0) for t in style_trade_list)
            avg_holding = sum(
                (datetime.strptime(t.get("sell_date", t.get("date")), "%Y-%m-%d") - 
                 datetime.strptime(t.get("entry_date", t.get("date")), "%Y-%m-%d")).days
                for t in style_trade_list
                if t.get("sell_date") or t.get("entry_date")
            ) / len(style_trade_list) if style_trade_list else 0
            
            sensitivities.append(StyleSensitivity(
                style=style,
                return_rate=total_return / len(style_trade_list) * 100 if style_trade_list else 0,
                win_rate=len(win_trades) / len(style_trade_list) * 100 if style_trade_list else 0,
                trade_count=len(style_trade_list),
                avg_holding_days=avg_holding,
            ))
        
        return sensitivities
    
    def analyze_failures(
        self,
        daily_values: List[Dict[str, Any]],
        market_styles: List[Dict[str, Any]],
        threshold: float = -5.0,
    ) -> List[FailureAnalysis]:
        """分析失效期"""
        failures: List[FailureAnalysis] = []
        
        for dv in daily_values:
            if dv.get("daily_return", 0) < threshold:
                date = dv.get("date", "")
                style = MarketStyle.SIDEWAYS
                for ms in market_styles:
                    if ms.get("date") == date:
                        style = MarketStyle(ms.get("style", "sideways"))
                        break
                
                failures.append(FailureAnalysis(
                    period=date,
                    market_style=style,
                    return_rate=dv.get("daily_return", 0) * 100,
                    failure_reasons=["市场下跌", "策略不适应"],
                    affected_factors=["技术面", "情绪面"],
                ))
        
        return failures
    
    def check_overfitting(
        self,
        in_sample_result: Dict[str, Any],
        out_sample_result: Dict[str, Any],
    ) -> OverfittingCheck:
        """检测过拟合"""
        in_return = in_sample_result.get("total_return", 0)
        out_return = out_sample_result.get("total_return", 0)
        in_sharpe = in_sample_result.get("sharpe_ratio", 0)
        out_sharpe = out_sample_result.get("sharpe_ratio", 0)
        
        return_gap = abs(in_return - out_return)
        sharpe_gap = abs(in_sharpe - out_sharpe)
        
        is_overfitted = return_gap > self.overfitting_threshold * abs(in_return)
        
        warnings: List[str] = []
        if is_overfitted:
            warnings.append("样本外表现显著低于样本内，可能存在过拟合")
        if return_gap > 10:
            warnings.append(f"收益差距过大 ({return_gap:.1f}%)")
        if sharpe_gap > 0.5:
            warnings.append(f"夏普比率差距过大 ({sharpe_gap:.2f})")
        
        confidence = 1.0 - (return_gap / 100) if in_return != 0 else 0.5
        
        return OverfittingCheck(
            is_overfitted=is_overfitted,
            confidence=max(0, min(1, confidence)),
            in_sample_return=in_return,
            out_sample_return=out_return,
            return_gap=return_gap,
            sharpe_gap=sharpe_gap,
            warnings=warnings,
        )
    
    def determine_usability(
        self,
        total_return: float,
        sharpe_ratio: float,
        max_drawdown: float,
        win_rate: float,
        overfitting: OverfittingCheck,
    ) -> StrategyUsability:
        """判定策略可用性"""
        score = 0
        
        if total_return > 20:
            score += 30
        elif total_return > 10:
            score += 20
        elif total_return > 5:
            score += 10
        
        if sharpe_ratio > 1.5:
            score += 25
        elif sharpe_ratio > 1.0:
            score += 15
        elif sharpe_ratio > 0.5:
            score += 5
        
        if max_drawdown < 10:
            score += 20
        elif max_drawdown < 20:
            score += 10
        elif max_drawdown < 30:
            score += 5
        
        if win_rate > 60:
            score += 15
        elif win_rate > 50:
            score += 10
        elif win_rate > 40:
            score += 5
        
        if overfitting.is_overfitted:
            score -= 20
        
        if score >= 80:
            return StrategyUsability.EXCELLENT
        elif score >= 60:
            return StrategyUsability.GOOD
        elif score >= 40:
            return StrategyUsability.MODERATE
        elif score >= 20:
            return StrategyUsability.POOR
        else:
            return StrategyUsability.UNUSABLE
    
    def generate_risk_warnings(
        self,
        result: Dict[str, Any],
        overfitting: OverfittingCheck,
        failures: List[FailureAnalysis],
    ) -> List[str]:
        """生成风险提示"""
        warnings: List[str] = []
        
        if result.get("max_drawdown", 0) > 20:
            warnings.append(f"最大回撤较大 ({result['max_drawdown']:.1f}%)，需注意风险控制")
        
        if result.get("turnover_rate", 0) > 500:
            warnings.append(f"换手率过高 ({result['turnover_rate']:.1f}%)，交易成本影响大")
        
        if overfitting.is_overfitted:
            warnings.append("策略可能过拟合，实盘表现可能低于预期")
        
        if len(failures) > 10:
            warnings.append(f"失效期较多 ({len(failures)} 次)，策略稳定性不足")
        
        if result.get("win_rate", 0) < 40:
            warnings.append(f"胜率较低 ({result['win_rate']:.1f}%)，需优化选股条件")
        
        return warnings
    
    def generate_recommendations(
        self,
        usability: StrategyUsability,
        factor_contributions: List[FactorContribution],
        style_sensitivities: List[StyleSensitivity],
    ) -> List[str]:
        """生成优化建议"""
        recommendations: List[str] = []
        
        if usability == StrategyUsability.EXCELLENT:
            recommendations.append("策略表现优秀，可用于实盘交易")
        elif usability == StrategyUsability.GOOD:
            recommendations.append("策略表现良好，建议小仓位试运行")
        elif usability == StrategyUsability.MODERATE:
            recommendations.append("策略表现一般，建议优化后再使用")
        elif usability == StrategyUsability.POOR:
            recommendations.append("策略表现较差，需要重新设计")
        else:
            recommendations.append("策略不可用，建议重新开发")
        
        if factor_contributions:
            top_factor = factor_contributions[0]
            recommendations.append(f"主要贡献因子: {top_factor.factor_name}，可适当提高权重")
            
            low_factors = [f for f in factor_contributions if f.contribution_pct < 0]
            if low_factors:
                recommendations.append(f"负贡献因子: {', '.join(f.factor_name for f in low_factors[:3])}，建议移除")
        
        weak_styles = [s for s in style_sensitivities if s.return_rate < 0]
        if weak_styles:
            recommendations.append(f"在 {', '.join(s.style.value for s in weak_styles)} 市场表现较弱，建议添加风格过滤")
        
        return recommendations
    
    def evaluate(
        self,
        strategy_name: str,
        simulation_result: Dict[str, Any],
        factor_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        market_styles: Optional[List[Dict[str, Any]]] = None,
        out_sample_result: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """
        评估策略
        
        Args:
            strategy_name: 策略名称
            simulation_result: 模拟结果
            factor_data: 因子数据
            market_styles: 市场风格数据
            out_sample_result: 样本外结果
            
        Returns:
            评估结果
        """
        trades = simulation_result.get("trades", [])
        daily_values = simulation_result.get("daily_values", [])
        
        factor_contributions = []
        if factor_data:
            factor_contributions = self.analyze_factor_contributions(trades, factor_data)
        
        style_sensitivities = []
        if market_styles:
            style_sensitivities = self.analyze_style_sensitivity(trades, market_styles)
        
        failures = []
        if market_styles:
            failures = self.analyze_failures(daily_values, market_styles)
        
        overfitting = OverfittingCheck(
            is_overfitted=False,
            confidence=1.0,
            in_sample_return=simulation_result.get("total_return", 0),
            out_sample_return=0,
            return_gap=0,
            sharpe_gap=0,
            warnings=[],
        )
        if out_sample_result:
            overfitting = self.check_overfitting(simulation_result, out_sample_result)
        
        usability = self.determine_usability(
            simulation_result.get("total_return", 0),
            simulation_result.get("sharpe_ratio", 0),
            simulation_result.get("max_drawdown", 0),
            simulation_result.get("win_rate", 0),
            overfitting,
        )
        
        risk_warnings = self.generate_risk_warnings(simulation_result, overfitting, failures)
        recommendations = self.generate_recommendations(usability, factor_contributions, style_sensitivities)
        
        total_score = (
            simulation_result.get("total_return", 0) * 0.3 +
            simulation_result.get("sharpe_ratio", 0) * 20 +
            (100 - simulation_result.get("max_drawdown", 0)) * 0.3 +
            simulation_result.get("win_rate", 0) * 0.2
        )
        
        return EvaluationResult(
            strategy_name=strategy_name,
            usability=usability,
            total_score=total_score,
            factor_contributions=factor_contributions,
            style_sensitivities=style_sensitivities,
            failure_periods=failures,
            overfitting_check=overfitting,
            risk_warnings=risk_warnings,
            recommendations=recommendations,
            evaluation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )


strategy_evaluator = StrategyEvaluator()


__all__ = [
    "MarketStyle",
    "StrategyUsability",
    "FactorContribution",
    "StyleSensitivity",
    "FailureAnalysis",
    "OverfittingCheck",
    "EvaluationResult",
    "StrategyEvaluator",
    "strategy_evaluator",
]
