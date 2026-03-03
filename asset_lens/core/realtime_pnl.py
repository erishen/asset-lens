"""
Real-time PnL estimation for asset-lens.
实时盈亏估算模块
"""

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import config
from ..data.market_index import MarketIndex, MarketIndexCache
from ..data.models import InvestmentProduct, InvestmentType, RiskLevel


@dataclass
class ProductMapping:
    """产品到指数的映射"""

    index_key: str  # 指数代码
    direct_sensitivity: Decimal = Decimal("1.0")  # 对自身指数的敏感度
    sensitivity_to_sh: Decimal = Decimal("0.7")  # 对上证指数的敏感度
    equity_ratio: Decimal = Decimal("1.0")  # 权益占比


# 默认敏感度配置（相对于上证指数）
DEFAULT_SENSITIVITIES = {
    "HS300_to_SH": Decimal("0.9"),  # 沪深300相对于上证的敏感度
    "CSI500_to_SH": Decimal("0.7"),  # 中证500相对于上证的敏感度
    "GEM_to_SH": Decimal("0.8"),  # 创业板相对于上证的敏感度
    "STAR50_to_SH": Decimal("0.6"),  # 科创50相对于上证的敏感度
    "Defense_to_SH": Decimal("0.7"),  # 军工板块相对于上证的敏感度
}

# 默认产品映射
DEFAULT_PRODUCT_MAPPING = ProductMapping(
    index_key="Blend",
    direct_sensitivity=Decimal("1.0"),
    sensitivity_to_sh=Decimal("0.7"),
    equity_ratio=Decimal("0.7"),
)


def find_product_mapping(name: str, investment_type: InvestmentType) -> ProductMapping:
    """
    根据产品名称和类型查找指数映射

    Args:
        name: 产品名称
        investment_type: 投资类型

    Returns:
        产品映射配置
    """
    name_lower = name.lower()
    type_str = investment_type.value if investment_type else ""

    # 沪深300增强/指数
    if "沪深300" in name or "沪深300" in type_str:
        return ProductMapping(
            index_key="HS300",
            direct_sensitivity=Decimal("1.0"),
            equity_ratio=Decimal("1.0"),
        )

    # 中证500
    if "中证500" in name or "中证500" in type_str:
        return ProductMapping(
            index_key="CSI500",
            direct_sensitivity=Decimal("1.0"),
            equity_ratio=Decimal("1.0"),
        )

    # 创业板风格
    if any(kw in name for kw in ["创业板", "科技创新", "成长"]):
        return ProductMapping(
            index_key="GEM",
            direct_sensitivity=Decimal("1.0"),
            equity_ratio=Decimal("0.9"),
        )

    # 科创50
    if "科创" in name:
        return ProductMapping(
            index_key="STAR50",
            direct_sensitivity=Decimal("1.0"),
            equity_ratio=Decimal("1.0"),
        )

    # QDII基金（纳斯达克/美股等）
    if any(kw in name for kw in ["QDII", "纳斯达克", "纳指", "美股", "美国"]):
        return ProductMapping(
            index_key="Nasdaq",
            sensitivity_to_sh=Decimal("0.6"),
            equity_ratio=Decimal("1.0"),
        )

    # 黄金基金
    if "黄金" in name:
        return ProductMapping(
            index_key="Gold",
            sensitivity_to_sh=Decimal("0.3"),
            equity_ratio=Decimal("1.0"),
        )

    # 债券基金
    if investment_type == InvestmentType.BOND_FUND or investment_type == InvestmentType.BOND:
        return ProductMapping(
            index_key="Bond",
            sensitivity_to_sh=Decimal("0.1"),
            equity_ratio=Decimal("0.2"),
        )

    # 货币基金
    if investment_type == InvestmentType.MONETARY:
        return ProductMapping(
            index_key="Cash",
            sensitivity_to_sh=Decimal("0.0"),
            equity_ratio=Decimal("0.0"),
        )

    # 主动/混合基金（默认按上证敏感度）
    if investment_type in [InvestmentType.MIXED_FUND, InvestmentType.FUND]:
        return ProductMapping(
            index_key="Blend",
            sensitivity_to_sh=Decimal("0.7"),
            equity_ratio=Decimal("0.7"),
        )

    # 股票
    if investment_type in [InvestmentType.STOCK, InvestmentType.US_STOCK, InvestmentType.HK_STOCK]:
        return ProductMapping(
            index_key="SHComp",
            direct_sensitivity=Decimal("1.0"),
            equity_ratio=Decimal("1.0"),
        )

    # 默认配置
    return DEFAULT_PRODUCT_MAPPING


def adjust_by_risk_level(
    name: str,
    default_equity_ratio: Decimal,
    default_sensitivity: Decimal,
    risk_level: Optional[RiskLevel] = None,
) -> tuple[Decimal, Decimal]:
    """
    根据产品风险等级调整敏感度

    Args:
        name: 产品名称
        default_equity_ratio: 默认权益比例
        default_sensitivity: 默认敏感度
        risk_level: 风险等级

    Returns:
        (调整后的权益比例, 调整后的敏感度)
    """
    if risk_level is None:
        return default_equity_ratio, default_sensitivity

    if risk_level == RiskLevel.LOW:
        return (
            default_equity_ratio * Decimal("0.3"),
            default_sensitivity * Decimal("0.3"),
        )
    elif risk_level == RiskLevel.MEDIUM:
        return (
            default_equity_ratio * Decimal("0.7"),
            default_sensitivity * Decimal("0.7"),
        )
    elif risk_level == RiskLevel.HIGH:
        return default_equity_ratio, default_sensitivity

    return default_equity_ratio, default_sensitivity


class RealtimePnlEstimator:
    """实时盈亏估算器"""

    def __init__(self):
        self.cache_path = config.cache_path
        self.domestic_cache_file = self.cache_path / "market_index_domestic.json"
        self.foreign_cache_file = self.cache_path / "market_index_foreign.json"

    def _get_total_amount_from_summary(self) -> Decimal:
        """从资产汇总-表格 1.csv 获取最新的总金额"""
        from ..data.asset_summary_parser import AssetSummaryParser

        try:
            data_dir = config.get_latest_data_dir()
            if not data_dir:
                return Decimal("0")

            summary_file = data_dir / "资产汇总-表格 1.csv"
            if not summary_file.exists():
                summary_file = data_dir / "资产汇总.csv"
            if not summary_file.exists():
                # 兼容旧文件名
                summary_file = data_dir / "备份-表格 1.csv"
            if summary_file.exists():
                summaries = AssetSummaryParser.parse_csv_file(summary_file)
                if summaries:
                    return summaries[-1].total_amount or Decimal("0")
        except Exception:
            pass
        return Decimal("0")

    def read_index_moves_from_cache(self, is_weekly: bool = False) -> Dict[str, Decimal]:
        """
        从缓存读取指数涨跌幅数据

        Args:
            is_weekly: 是否为周预估

        Returns:
            指数涨跌幅字典
        """
        moves: Dict[str, Decimal] = {}

        # 读取国内市场数据
        if self.domestic_cache_file.exists():
            try:
                with open(self.domestic_cache_file, "r", encoding="utf-8") as f:
                    domestic_data = json.load(f)

                # 处理国内数据 - 将中文名称映射为英文代码
                index_mapping = {
                    "上证指数": "SHComp",
                    "沪深300": "HS300",
                    "中证500": "CSI500",
                    "创业板指": "GEM",
                    "科创50": "STAR50",
                    "军工指数": "Defense",
                }

                for cn_name, en_code in index_mapping.items():
                    if cn_name in domestic_data.get("指数数据", {}):
                        index_data = domestic_data["指数数据"][cn_name]
                        if is_weekly:
                            weekly_change = index_data.get("周期表现", {}).get("周涨跌幅", 0)
                            if weekly_change == 0:
                                weekly_change = index_data.get("涨跌幅", 0)
                            moves[en_code] = Decimal(str(weekly_change))
                        else:
                            moves[en_code] = Decimal(str(index_data.get("涨跌幅", 0)))
            except Exception as e:
                print(f"读取国内市场数据失败: {e}")

        if self.foreign_cache_file.exists():
            try:
                with open(self.foreign_cache_file, "r", encoding="utf-8") as f:
                    foreign_data = json.load(f)

                for key, index_data in foreign_data.get("指数数据", {}).items():
                    if "QQQ" in key or "纳斯达克" in key:
                        if is_weekly:
                            weekly_change = index_data.get("周期表现", {}).get("周涨跌幅", 0)
                            if weekly_change == 0:
                                weekly_change = index_data.get("涨跌幅", 0)
                            moves["Nasdaq"] = Decimal(str(weekly_change))
                        else:
                            moves["Nasdaq"] = Decimal(str(index_data.get("涨跌幅", 0)))
                    elif "Gold" in key or "黄金" in key:
                        if is_weekly:
                            weekly_change = index_data.get("周期表现", {}).get("周涨跌幅", 0)
                            if weekly_change == 0:
                                weekly_change = index_data.get("涨跌幅", 0)
                            moves["Gold"] = Decimal(str(weekly_change))
                        else:
                            moves["Gold"] = Decimal(str(index_data.get("涨跌幅", 0)))
            except Exception as e:
                print(f"读取海外市场数据失败: {e}")

        if "黄金ETF" in domestic_data.get("指数数据", {}):
            try:
                gold_data = domestic_data["指数数据"]["黄金ETF"]
                if is_weekly:
                    weekly_change = gold_data.get("周期表现", {}).get("周涨跌幅", 0)
                    if weekly_change == 0:
                        weekly_change = gold_data.get("涨跌幅", 0)
                    moves["Gold"] = Decimal(str(weekly_change))
                else:
                    moves["Gold"] = Decimal(str(gold_data.get("涨跌幅", 0)))
            except Exception as e:
                print(f"读取国内黄金数据失败: {e}")

        return moves

    def estimate_product_pnl(
        self,
        product: InvestmentProduct,
        moves: Dict[str, Decimal],
        is_weekly: bool = False,
    ) -> Dict[str, Any]:
        """
        估算单个产品的盈亏

        Args:
            product: 投资产品
            moves: 指数涨跌幅字典
            is_weekly: 是否为周预估

        Returns:
            盈亏估算结果
        """
        # 获取产品映射
        mapping = find_product_mapping(product.name, product.investment_type)

        # 计算权益金额
        current_amount = product.current_amount or Decimal("0")
        equity_ratio = mapping.equity_ratio
        sensitivity = mapping.direct_sensitivity

        # 根据风险等级调整
        equity_ratio, sensitivity = adjust_by_risk_level(
            product.name,
            equity_ratio,
            sensitivity,
            product.risk_level,
        )

        amount_eq = current_amount * equity_ratio

        # 获取指数涨跌幅
        index_key = mapping.index_key
        index_move = Decimal("0")

        if index_key != "Blend" and index_key in moves:
            # 使用直接指数涨跌幅
            index_move = moves[index_key]
        elif index_key == "Blend":
            # 混合基金使用上证指数
            sensitivity = mapping.sensitivity_to_sh
            index_move = moves.get("SHComp", Decimal("0"))

        # 计算盈亏
        pct = (index_move / Decimal("100")) * sensitivity
        pnl = amount_eq * pct

        # 计算收益率
        return_rate = (
            (pnl / current_amount * Decimal("100")) if current_amount != 0 else Decimal("0")
        )

        return {
            "name": product.name,
            "type": product.investment_type.value if product.investment_type else "其他",
            "risk": product.risk_level.value if product.risk_level else "中",
            "amount": current_amount,
            "equity_ratio": equity_ratio,
            "index_key": index_key,
            "index_move": index_move,
            "sensitivity": sensitivity,
            "pnl": pnl,
            "return_rate": return_rate,
        }

    def estimate_portfolio_pnl(
        self,
        products: List[InvestmentProduct],
        is_weekly: bool = False,
        filter_equity: bool = True,
    ) -> Dict[str, Any]:
        """
        估算投资组合的盈亏

        Args:
            products: 投资产品列表
            is_weekly: 是否为周预估
            filter_equity: 是否过滤非权益类产品

        Returns:
            投资组合盈亏估算结果
        """
        # 读取指数涨跌幅数据
        moves = self.read_index_moves_from_cache(is_weekly)

        if not moves:
            return {
                "total": Decimal("1"),
                "details": [],
                "error": "无法读取市场指数数据，请先更新缓存",
            }

        # 从备份-表格 1.csv 获取正确的总金额
        total_amount_all = self._get_total_amount_from_summary()

        # 过滤非权益类产品（与 ts-demo 保持一致）
        if filter_equity:
            exclude_types = [
                InvestmentType.MONETARY,
                InvestmentType.BOND,
                InvestmentType.WEALTH,
                InvestmentType.GOLD,
                InvestmentType.SPECIAL_TREASURY_BOND,
                InvestmentType.US_STOCK,
                InvestmentType.HK_DIVIDEND_FUND,
                InvestmentType.HIGH_END_WEALTH,
            ]
            products = [
                p
                for p in products
                if p.investment_type not in exclude_types
                and p.current_amount
                and p.current_amount > 0
            ]

        # 计算每个产品的盈亏
        details = []
        total_pnl = Decimal("0")
        total_amount = Decimal("0")

        for product in products:
            result = self.estimate_product_pnl(product, moves, is_weekly)
            details.append(result)
            total_pnl += result["pnl"]
            total_amount += result["amount"]

        # 计算整体收益率
        total_return_rate = (
            (total_pnl / total_amount * Decimal("100")) if total_amount != 0 else Decimal("0")
        )

        # 按盈亏排序
        details.sort(key=lambda x: x["pnl"], reverse=True)

        return {
            "total": total_pnl,
            "total_amount": total_amount,
            "total_amount_all": total_amount_all,
            "total_return_rate": total_return_rate,
            "details": details,
            "moves": moves,
            "is_weekly": is_weekly,
        }
