"""
Sector rotation analysis module.
板块轮动分析模块 - 分析行业板块强弱，辅助基金投资决策
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SectorInfo:
    """板块信息"""

    name: str
    code: str
    change_percent: float
    volume_ratio: float
    turnover_rate: float
    strength_score: float
    trend: str
    recommendation: str


@dataclass
class SectorRotationResult:
    """板块轮动分析结果"""

    market_condition: str
    strong_sectors: list[SectorInfo]
    weak_sectors: list[SectorInfo]
    recommended_sectors: list[str]
    avoid_sectors: list[str]
    rotation_signal: str
    timestamp: str


SECTOR_MAPPING = {
    "科技": ["科技", "芯片", "半导体", "电子", "计算机", "通信", "5G", "人工智能", "AI"],
    "医药": ["医药", "医疗", "生物", "中药", "创新药", "医疗器械"],
    "消费": ["消费", "食品", "饮料", "白酒", "家电", "零售"],
    "金融": ["银行", "证券", "保险", "金融"],
    "地产": ["地产", "房地产", "物业"],
    "新能源": ["新能源", "光伏", "锂电", "风电", "储能", "碳中和"],
    "汽车": ["汽车", "新能源车", "智能汽车"],
    "军工": ["军工", "国防", "航空航天"],
    "有色": ["有色", "黄金", "铜", "铝", "稀土"],
    "化工": ["化工", "化纤", "塑料", "橡胶"],
    "机械": ["机械", "工程机械", "机床"],
    "基建": ["基建", "建筑", "建材", "水泥"],
    "电力": ["电力", "火电", "水电", "核电"],
    "煤炭": ["煤炭", "焦炭"],
    "石油": ["石油", "油气", "石化"],
    "钢铁": ["钢铁", "钢材"],
    "农业": ["农业", "种业", "养殖", "饲料"],
    "传媒": ["传媒", "影视", "游戏", "教育"],
    "环保": ["环保", "节能", "水务"],
}


class SectorRotationAnalyzer:
    """板块轮动分析器"""

    def __init__(self):
        self.sector_data: dict[str, list[dict]] = {}

    def analyze(self) -> SectorRotationResult:
        """
        分析板块轮动情况

        Returns:
            板块轮动分析结果
        """
        from ..data.market_stock_fetcher import MarketStockFetcher

        fetcher = MarketStockFetcher()
        stocks = fetcher.get_cached_market_stocks()

        sector_stats = self._calculate_sector_stats(stocks)

        sorted_sectors = sorted(sector_stats.items(), key=lambda x: x[1]["strength_score"], reverse=True)

        strong_sectors = []
        weak_sectors = []

        for sector_name, stats in sorted_sectors[:5]:
            strong_sectors.append(
                SectorInfo(
                    name=sector_name,
                    code=stats.get("code", ""),
                    change_percent=stats.get("avg_change", 0),
                    volume_ratio=stats.get("volume_ratio", 1.0),
                    turnover_rate=stats.get("avg_turnover", 0),
                    strength_score=stats.get("strength_score", 0),
                    trend="强势" if stats.get("avg_change", 0) > 0 else "弱势",
                    recommendation=self._get_sector_recommendation(sector_name, stats, "strong"),
                )
            )

        for sector_name, stats in sorted_sectors[-5:]:
            weak_sectors.append(
                SectorInfo(
                    name=sector_name,
                    code=stats.get("code", ""),
                    change_percent=stats.get("avg_change", 0),
                    volume_ratio=stats.get("volume_ratio", 1.0),
                    turnover_rate=stats.get("avg_turnover", 0),
                    strength_score=stats.get("strength_score", 0),
                    trend="弱势",
                    recommendation=self._get_sector_recommendation(sector_name, stats, "weak"),
                )
            )

        market_condition = self._determine_market_condition(stocks)

        recommended_sectors = [s.name for s in strong_sectors[:3]]
        avoid_sectors = [s.name for s in weak_sectors[-3:]]

        rotation_signal = self._generate_rotation_signal(strong_sectors, weak_sectors, market_condition)

        return SectorRotationResult(
            market_condition=market_condition,
            strong_sectors=strong_sectors,
            weak_sectors=weak_sectors,
            recommended_sectors=recommended_sectors,
            avoid_sectors=avoid_sectors,
            rotation_signal=rotation_signal,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    def _calculate_sector_stats(self, stocks: list[dict]) -> dict[str, dict]:
        """计算各板块统计"""
        sector_stats: dict[str, dict] = {}

        for stock in stocks:
            name = stock.get("name", "")
            if not name:
                continue

            matched_sector = None
            for sector_name, keywords in SECTOR_MAPPING.items():
                for keyword in keywords:
                    if keyword in name:
                        matched_sector = sector_name
                        break
                if matched_sector:
                    break

            if not matched_sector:
                continue

            if matched_sector not in sector_stats:
                sector_stats[matched_sector] = {
                    "count": 0,
                    "total_change": 0,
                    "total_turnover": 0,
                    "total_market_cap": 0,
                    "up_count": 0,
                    "down_count": 0,
                }

            stats = sector_stats[matched_sector]
            stats["count"] += 1
            change = stock.get("change_percent", 0)
            stats["total_change"] += change
            stats["total_turnover"] += stock.get("turnover_rate", 0)
            stats["total_market_cap"] += stock.get("market_cap", 0)

            if change > 0:
                stats["up_count"] += 1
            elif change < 0:
                stats["down_count"] += 1

        for stats in sector_stats.values():
            if stats["count"] > 0:
                stats["avg_change"] = stats["total_change"] / stats["count"]
                stats["avg_turnover"] = stats["total_turnover"] / stats["count"]
                stats["up_ratio"] = stats["up_count"] / stats["count"]
                stats["strength_score"] = stats["avg_change"] * 10 + stats["up_ratio"] * 20 + stats["avg_turnover"] * 2

        return sector_stats

    def _determine_market_condition(self, stocks: list[dict]) -> str:
        """判断市场状态"""
        if not stocks:
            return "sideways"

        changes = [s.get("change_percent", 0) for s in stocks]
        avg_change = np.mean(changes) if changes else 0
        up_ratio = len([c for c in changes if c > 0]) / len(changes) if changes else 0.5

        if avg_change > 1 and up_ratio > 0.6:
            return "bull"
        elif avg_change < -1 and up_ratio < 0.4:
            return "bear"
        else:
            return "sideways"

    def _get_sector_recommendation(self, sector_name: str, stats: dict, strength: str) -> str:
        """获取板块建议"""
        avg_change = stats.get("avg_change", 0)
        stats.get("up_ratio", 0)

        if strength == "strong":
            if avg_change > 2:
                return "强势领涨，可关注相关基金"
            elif avg_change > 0:
                return "表现较好，可适度配置"
            else:
                return "相对抗跌，防御价值高"
        else:
            if avg_change < -2:
                return "跌幅较大，建议回避"
            elif avg_change < 0:
                return "表现弱势，暂不配置"
            else:
                return "表现一般，观望为主"

    def _generate_rotation_signal(
        self,
        strong_sectors: list[SectorInfo],
        weak_sectors: list[SectorInfo],
        market_condition: str,
    ) -> str:
        """生成轮动信号"""
        if market_condition == "bull":
            return f"市场偏强，建议关注 {strong_sectors[0].name if strong_sectors else '强势板块'}"
        elif market_condition == "bear":
            return "市场偏弱，建议降低仓位，防御为主"
        else:
            if strong_sectors and weak_sectors:
                return f"市场震荡，可从 {weak_sectors[0].name} 轮动至 {strong_sectors[0].name}"
            else:
                return "市场震荡，观望为主"

    def get_fund_sector_recommendation(self, fund_name: str) -> dict[str, Any]:
        """
        根据基金名称判断所属板块并给出建议

        Args:
            fund_name: 基金名称

        Returns:
            板块建议
        """
        result = self.analyze()

        matched_sector = None
        for sector_name, keywords in SECTOR_MAPPING.items():
            for keyword in keywords:
                if keyword in fund_name:
                    matched_sector = sector_name
                    break
            if matched_sector:
                break

        if not matched_sector:
            return {
                "fund_name": fund_name,
                "sector": "未知",
                "recommendation": "无法判断板块，建议参考其他指标",
            }

        is_recommended = matched_sector in result.recommended_sectors
        is_avoid = matched_sector in result.avoid_sectors

        if is_recommended:
            suggestion = "该板块当前强势，建议持有或加仓"
        elif is_avoid:
            suggestion = "该板块当前弱势，建议减仓或回避"
        else:
            suggestion = "该板块表现中性，建议观望"

        return {
            "fund_name": fund_name,
            "sector": matched_sector,
            "is_recommended": is_recommended,
            "is_avoid": is_avoid,
            "recommendation": suggestion,
            "market_condition": result.market_condition,
        }

    def analyze_portfolio_sectors(self, funds: list[str]) -> dict[str, Any]:
        """
        分析投资组合的板块分布

        Args:
            funds: 基金名称列表

        Returns:
            板块分布分析
        """
        result = self.analyze()

        sector_distribution: dict[str, list[str]] = {}
        unknown_funds = []

        for fund_name in funds:
            matched_sector = None
            for sector_name, keywords in SECTOR_MAPPING.items():
                for keyword in keywords:
                    if keyword in fund_name:
                        matched_sector = sector_name
                        break
                if matched_sector:
                    break

            if matched_sector:
                if matched_sector not in sector_distribution:
                    sector_distribution[matched_sector] = []
                sector_distribution[matched_sector].append(fund_name)
            else:
                unknown_funds.append(fund_name)

        recommendations = []
        for sector, fund_list in sector_distribution.items():
            is_recommended = sector in result.recommended_sectors
            is_avoid = sector in result.avoid_sectors

            if is_recommended:
                status = "✅ 强势板块"
            elif is_avoid:
                status = "⚠️ 弱势板块"
            else:
                status = "➖ 中性板块"

            recommendations.append(
                {
                    "sector": sector,
                    "funds": fund_list,
                    "count": len(fund_list),
                    "status": status,
                    "is_recommended": is_recommended,
                    "is_avoid": is_avoid,
                }
            )

        return {
            "market_condition": result.market_condition,
            "sector_distribution": sector_distribution,
            "recommendations": recommendations,
            "unknown_funds": unknown_funds,
            "recommended_sectors": result.recommended_sectors,
            "avoid_sectors": result.avoid_sectors,
        }


sector_analyzer = SectorRotationAnalyzer()
