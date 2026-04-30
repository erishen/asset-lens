"""
Portfolio Analysis Module.
持仓分析模块 - 个股诊断、健康度评估

功能:
1. 个股诊断报告 (技术面+基本面)
2. 持仓健康度评估
3. 行业配置分析
4. 风险敞口分析
5. 调仓建议
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import config


class HealthLevel(Enum):
    """健康度等级"""

    EXCELLENT = "excellent"  # 优秀 (>80)
    GOOD = "good"  # 良好 (60-80)
    FAIR = "fair"  # 一般 (40-60)
    POOR = "poor"  # 较差 (20-40)
    CRITICAL = "critical"  # 危险 (<20)


class TrendDirection(Enum):
    """趋势方向"""

    STRONG_UP = "strong_up"  # 强势上涨
    UP = "up"  # 上涨
    SIDEWAYS = "sideways"  # 横盘
    DOWN = "down"  # 下跌
    STRONG_DOWN = "strong_down"  # 强势下跌


@dataclass
class Position:
    """持仓"""

    code: str
    name: str
    shares: float
    cost_price: float
    current_price: float
    market_value: float
    profit_loss: float
    profit_loss_percent: float
    weight: float  # 占比
    industry: str = ""
    sector: str = ""


@dataclass
class StockDiagnosis:
    """个股诊断"""

    code: str
    name: str
    current_price: float
    trend: TrendDirection
    health_score: float
    health_level: HealthLevel

    technical_score: float = 0.0
    fundamental_score: float = 0.0
    sentiment_score: float = 0.0

    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    support_levels: list[float] = field(default_factory=list)
    resistance_levels: list[float] = field(default_factory=list)

    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class PortfolioHealth:
    """持仓健康度"""

    total_value: float
    total_profit_loss: float
    total_profit_loss_percent: float

    health_score: float
    health_level: HealthLevel

    diversification_score: float  # 分散度
    concentration_risk: float  # 集中度风险
    sector_balance: float  # 行业平衡度

    top_positions: list[Position]
    risk_positions: list[Position]

    suggestions: list[str] = field(default_factory=list)


@dataclass
class SectorAllocation:
    """行业配置"""

    sector: str
    weight: float
    profit_loss: float
    profit_loss_percent: float
    positions: list[Position]


class PortfolioAnalyzer:
    """持仓分析器"""

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def diagnose_stock(
        self,
        position: Position,
        technical_data: dict[str, Any] | None = None,
        fundamental_data: dict[str, Any] | None = None,
    ) -> StockDiagnosis:
        """诊断个股"""
        technical_score = self._calculate_technical_score(position, technical_data)
        fundamental_score = self._calculate_fundamental_score(position, fundamental_data)
        sentiment_score = self._calculate_sentiment_score(position)

        health_score = technical_score * 0.4 + fundamental_score * 0.35 + sentiment_score * 0.25

        trend = self._determine_trend(position, technical_data)

        strengths = self._identify_strengths(position, technical_data, fundamental_data)
        weaknesses = self._identify_weaknesses(position, technical_data, fundamental_data)
        suggestions = self._generate_suggestions(position, health_score, trend)

        support_levels = self._calculate_support_levels(position, technical_data)
        resistance_levels = self._calculate_resistance_levels(position, technical_data)

        return StockDiagnosis(
            code=position.code,
            name=position.name,
            current_price=position.current_price,
            trend=trend,
            health_score=health_score,
            health_level=self._get_health_level(health_score),
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            sentiment_score=sentiment_score,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
        )

    def analyze_portfolio_health(self, positions: list[Position]) -> PortfolioHealth:
        """分析持仓健康度"""
        if not positions:
            return PortfolioHealth(
                total_value=0,
                total_profit_loss=0,
                total_profit_loss_percent=0,
                health_score=0,
                health_level=HealthLevel.CRITICAL,
                diversification_score=0,
                concentration_risk=0,
                sector_balance=0,
                top_positions=[],
                risk_positions=[],
            )

        total_value = sum(p.market_value for p in positions)
        total_profit_loss = sum(p.profit_loss for p in positions)
        total_cost = total_value - total_profit_loss
        total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0

        diversification_score = self._calculate_diversification(positions)
        concentration_risk = self._calculate_concentration_risk(positions)
        sector_balance = self._calculate_sector_balance(positions)

        health_score = (
            diversification_score * 0.3
            + (100 - concentration_risk) * 0.3
            + sector_balance * 0.2
            + max(0, 50 + total_profit_loss_percent) * 0.2
        )

        sorted_positions = sorted(positions, key=lambda p: p.market_value, reverse=True)
        top_positions = sorted_positions[:5]

        risk_positions = [p for p in positions if p.profit_loss_percent < -10 or p.weight > 20]

        suggestions = self._generate_portfolio_suggestions(
            positions,
            health_score,
            concentration_risk,
            sector_balance,
        )

        return PortfolioHealth(
            total_value=total_value,
            total_profit_loss=total_profit_loss,
            total_profit_loss_percent=total_profit_loss_percent,
            health_score=health_score,
            health_level=self._get_health_level(health_score),
            diversification_score=diversification_score,
            concentration_risk=concentration_risk,
            sector_balance=sector_balance,
            top_positions=top_positions,
            risk_positions=risk_positions,
            suggestions=suggestions,
        )

    def analyze_sector_allocation(self, positions: list[Position]) -> list[SectorAllocation]:
        """分析行业配置"""
        sector_map: dict[str, list[Position]] = {}

        for p in positions:
            sector = p.sector or p.industry or "未知"
            if sector not in sector_map:
                sector_map[sector] = []
            sector_map[sector].append(p)

        allocations = []
        total_value = sum(p.market_value for p in positions)

        for sector, sector_positions in sector_map.items():
            sector_value = sum(p.market_value for p in sector_positions)
            sector_profit = sum(p.profit_loss for p in sector_positions)
            sector_cost = sector_value - sector_profit

            weight = (sector_value / total_value * 100) if total_value > 0 else 0
            profit_percent = (sector_profit / sector_cost * 100) if sector_cost > 0 else 0

            allocations.append(
                SectorAllocation(
                    sector=sector,
                    weight=weight,
                    profit_loss=sector_profit,
                    profit_loss_percent=profit_percent,
                    positions=sector_positions,
                )
            )

        return sorted(allocations, key=lambda a: a.weight, reverse=True)

    def _calculate_technical_score(
        self,
        position: Position,
        technical_data: dict[str, Any] | None,
    ) -> float:
        """计算技术面得分"""
        score = 50.0

        if position.profit_loss_percent > 0:
            score += min(20, position.profit_loss_percent)
        else:
            score += max(-30, position.profit_loss_percent)

        if technical_data:
            if technical_data.get("rsi", 50) < 30:
                score += 10
            elif technical_data.get("rsi", 50) > 70:
                score -= 10

            if technical_data.get("macd_signal") == "bullish":
                score += 10
            elif technical_data.get("macd_signal") == "bearish":
                score -= 10

        return max(0, min(100, score))

    def _calculate_fundamental_score(
        self,
        position: Position,
        fundamental_data: dict[str, Any] | None,
    ) -> float:
        """计算基本面得分"""
        score = 50.0

        if fundamental_data:
            pe = fundamental_data.get("pe_ratio", 0)
            if 0 < pe < 20:
                score += 15
            elif 20 <= pe < 40:
                score += 5
            elif pe >= 100:
                score -= 10

            roe = fundamental_data.get("roe", 0)
            if roe > 15:
                score += 15
            elif roe > 10:
                score += 10
            elif roe < 5:
                score -= 10

            revenue_growth = fundamental_data.get("revenue_growth", 0)
            if revenue_growth > 20:
                score += 10
            elif revenue_growth < 0:
                score -= 10

        return max(0, min(100, score))

    def _calculate_sentiment_score(self, position: Position) -> float:
        """计算情绪面得分"""
        score = 50.0

        if position.profit_loss_percent > 10:
            score += 20
        elif position.profit_loss_percent > 5:
            score += 10
        elif position.profit_loss_percent < -10:
            score -= 20
        elif position.profit_loss_percent < -5:
            score -= 10

        return max(0, min(100, score))

    def _determine_trend(
        self,
        position: Position,
        technical_data: dict[str, Any] | None,
    ) -> TrendDirection:
        """判断趋势"""
        change = position.profit_loss_percent

        if technical_data:
            ma_trend = technical_data.get("ma_trend", "neutral")
            if ma_trend == "strong_up":
                return TrendDirection.STRONG_UP
            elif ma_trend == "up":
                return TrendDirection.UP
            elif ma_trend == "down":
                return TrendDirection.DOWN
            elif ma_trend == "strong_down":
                return TrendDirection.STRONG_DOWN

        if change > 20:
            return TrendDirection.STRONG_UP
        elif change > 5:
            return TrendDirection.UP
        elif change < -20:
            return TrendDirection.STRONG_DOWN
        elif change < -5:
            return TrendDirection.DOWN
        else:
            return TrendDirection.SIDEWAYS

    def _get_health_level(self, score: float) -> HealthLevel:
        """获取健康度等级"""
        if score >= 80:
            return HealthLevel.EXCELLENT
        elif score >= 60:
            return HealthLevel.GOOD
        elif score >= 40:
            return HealthLevel.FAIR
        elif score >= 20:
            return HealthLevel.POOR
        else:
            return HealthLevel.CRITICAL

    def _identify_strengths(
        self,
        position: Position,
        technical_data: dict[str, Any] | None,
        fundamental_data: dict[str, Any] | None,
    ) -> list[str]:
        """识别优势"""
        strengths = []

        if position.profit_loss_percent > 10:
            strengths.append(f"盈利 {position.profit_loss_percent:.1f}%")

        if fundamental_data:
            if fundamental_data.get("roe", 0) > 15:
                strengths.append(f"ROE {fundamental_data['roe']:.1f}%")
            if fundamental_data.get("revenue_growth", 0) > 20:
                strengths.append(f"营收增长 {fundamental_data['revenue_growth']:.1f}%")

        if technical_data:
            if technical_data.get("rsi", 50) < 30:
                strengths.append("RSI 超卖区域")
            if technical_data.get("macd_signal") == "bullish":
                strengths.append("MACD 金叉")

        return strengths

    def _identify_weaknesses(
        self,
        position: Position,
        technical_data: dict[str, Any] | None,
        fundamental_data: dict[str, Any] | None,
    ) -> list[str]:
        """识别劣势"""
        weaknesses = []

        if position.profit_loss_percent < -10:
            weaknesses.append(f"亏损 {abs(position.profit_loss_percent):.1f}%")

        if position.weight > 20:
            weaknesses.append(f"仓位过重 ({position.weight:.1f}%)")

        if fundamental_data:
            if fundamental_data.get("pe_ratio", 0) > 50:
                weaknesses.append(f"PE 偏高 ({fundamental_data['pe_ratio']:.1f})")
            if fundamental_data.get("roe", 0) < 5:
                weaknesses.append(f"ROE 偏低 ({fundamental_data['roe']:.1f}%)")

        if technical_data:
            if technical_data.get("rsi", 50) > 70:
                weaknesses.append("RSI 超买区域")
            if technical_data.get("macd_signal") == "bearish":
                weaknesses.append("MACD 死叉")

        return weaknesses

    def _generate_suggestions(
        self,
        position: Position,
        health_score: float,
        trend: TrendDirection,
    ) -> list[str]:
        """生成建议"""
        suggestions = []

        if health_score < 40:
            suggestions.append("建议减仓或止损")

        if trend in [TrendDirection.STRONG_DOWN, TrendDirection.DOWN]:
            suggestions.append("趋势向下，注意风险控制")

        if position.weight > 20:
            suggestions.append("仓位过重，建议降至 15% 以内")

        if position.profit_loss_percent > 20:
            suggestions.append("盈利较多，考虑部分止盈")

        if position.profit_loss_percent < -15:
            suggestions.append("亏损较大，评估是否继续持有")

        if not suggestions:
            suggestions.append("持仓健康，继续持有观察")

        return suggestions

    def _calculate_support_levels(
        self,
        position: Position,
        technical_data: dict[str, Any] | None,
    ) -> list[float]:
        """计算支撑位"""
        levels = []

        if technical_data and "support_levels" in technical_data:
            levels = technical_data["support_levels"]
        else:
            price = position.current_price
            levels = [
                price * 0.95,
                price * 0.90,
                price * 0.85,
            ]

        return levels

    def _calculate_resistance_levels(
        self,
        position: Position,
        technical_data: dict[str, Any] | None,
    ) -> list[float]:
        """计算阻力位"""
        levels = []

        if technical_data and "resistance_levels" in technical_data:
            levels = technical_data["resistance_levels"]
        else:
            price = position.current_price
            levels = [
                price * 1.05,
                price * 1.10,
                price * 1.15,
            ]

        return levels

    def _calculate_diversification(self, positions: list[Position]) -> float:
        """计算分散度"""
        if not positions:
            return 0

        n = len(positions)
        if n == 1:
            return 20

        if n <= 3:
            return 40 + n * 10
        elif n <= 5:
            return 70 + (n - 3) * 5
        elif n <= 10:
            return 85 + (n - 5) * 2
        else:
            return min(100, 95 + (n - 10))

    def _calculate_concentration_risk(self, positions: list[Position]) -> float:
        """计算集中度风险"""
        if not positions:
            return 0

        total_value = sum(p.market_value for p in positions)
        if total_value == 0:
            return 0

        weights = [p.market_value / total_value for p in positions]
        hhi = sum(w**2 for w in weights)

        return hhi * 100

    def _calculate_sector_balance(self, positions: list[Position]) -> float:
        """计算行业平衡度"""
        if not positions:
            return 0

        sector_weights: dict[str, float] = {}
        total_value = sum(p.market_value for p in positions)

        for p in positions:
            sector = p.sector or p.industry or "未知"
            if sector not in sector_weights:
                sector_weights[sector] = 0
            sector_weights[sector] += p.market_value / total_value

        n_sectors = len(sector_weights)

        if n_sectors == 1:
            return 30
        elif n_sectors == 2:
            return 50
        elif n_sectors <= 5:
            return 70 + n_sectors * 4
        else:
            return min(100, 90 + n_sectors)

    def _generate_portfolio_suggestions(
        self,
        positions: list[Position],
        health_score: float,
        concentration_risk: float,
        sector_balance: float,
    ) -> list[str]:
        """生成持仓建议"""
        suggestions = []

        if health_score < 50:
            suggestions.append("持仓健康度较低，建议优化配置")

        if concentration_risk > 30:
            suggestions.append(f"集中度风险较高 ({concentration_risk:.1f})，建议分散投资")

        if sector_balance < 60:
            suggestions.append("行业配置不均衡，建议增加行业分散度")

        risk_positions = [p for p in positions if p.profit_loss_percent < -10]
        if risk_positions:
            suggestions.append(f"有 {len(risk_positions)} 只股票亏损超过 10%，建议评估")

        large_positions = [p for p in positions if p.weight > 20]
        if large_positions:
            suggestions.append(f"有 {len(large_positions)} 只股票仓位超过 20%，建议减仓")

        if not suggestions:
            suggestions.append("持仓配置健康，继续保持")

        return suggestions


portfolio_analyzer = PortfolioAnalyzer()
