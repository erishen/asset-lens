import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..config import config
from ..data.models import InvestmentProduct, InvestmentType, RiskLevel
from .realtime_pnl_config import RealtimePnlConfigMixin

logger = logging.getLogger(__name__)


@dataclass
class ProductMapping:
    index_key: str
    direct_sensitivity: Decimal = Decimal("1.0")
    sensitivity_to_sh: Decimal = Decimal("0.7")
    equity_ratio: Decimal = Decimal("1.0")


DEFAULT_SENSITIVITIES = {
    "HS300_to_SH": Decimal("0.9"),
    "CSI500_to_SH": Decimal("0.7"),
    "GEM_to_SH": Decimal("0.8"),
    "STAR50_to_SH": Decimal("0.6"),
    "Defense_to_SH": Decimal("0.7"),
}

DEFAULT_PRODUCT_MAPPING = ProductMapping(
    index_key="Blend",
    direct_sensitivity=Decimal("1.0"),
    sensitivity_to_sh=Decimal("0.7"),
    equity_ratio=Decimal("0.7"),
)


def find_product_mapping(name: str, investment_type: InvestmentType) -> ProductMapping:
    name.lower()
    type_str = investment_type.value if investment_type else ""

    if "沪深300" in name or "沪深300" in type_str:
        return ProductMapping(
            index_key="HS300",
            direct_sensitivity=Decimal("1.0"),
            equity_ratio=Decimal("1.0"),
        )

    if "中证500" in name or "中证500" in type_str:
        return ProductMapping(
            index_key="CSI500",
            direct_sensitivity=Decimal("1.0"),
            equity_ratio=Decimal("1.0"),
        )

    if any(kw in name for kw in ["创业板", "科技创新", "成长"]):
        return ProductMapping(
            index_key="GEM",
            direct_sensitivity=Decimal("1.0"),
            equity_ratio=Decimal("0.9"),
        )

    if "科创" in name:
        return ProductMapping(
            index_key="STAR50",
            direct_sensitivity=Decimal("1.0"),
            equity_ratio=Decimal("1.0"),
        )

    if any(kw in name for kw in ["QDII", "纳斯达克", "纳指", "美股", "美国"]):
        return ProductMapping(
            index_key="Nasdaq",
            sensitivity_to_sh=Decimal("0.6"),
            equity_ratio=Decimal("1.0"),
        )

    if "黄金" in name:
        return ProductMapping(
            index_key="Gold",
            sensitivity_to_sh=Decimal("0.3"),
            equity_ratio=Decimal("1.0"),
        )

    if investment_type == InvestmentType.BOND_FUND or investment_type == InvestmentType.BOND:
        return ProductMapping(
            index_key="Bond",
            sensitivity_to_sh=Decimal("0.1"),
            equity_ratio=Decimal("0.2"),
        )

    if investment_type == InvestmentType.MONETARY:
        return ProductMapping(
            index_key="Cash",
            sensitivity_to_sh=Decimal("0.0"),
            equity_ratio=Decimal("0.0"),
        )

    if investment_type in [InvestmentType.MIXED_FUND, InvestmentType.FUND]:
        return ProductMapping(
            index_key="Blend",
            sensitivity_to_sh=Decimal("0.7"),
            equity_ratio=Decimal("0.7"),
        )

    if investment_type in [InvestmentType.STOCK, InvestmentType.US_STOCK, InvestmentType.HK_STOCK]:
        return ProductMapping(
            index_key="SHComp",
            direct_sensitivity=Decimal("1.0"),
            equity_ratio=Decimal("1.0"),
        )

    return DEFAULT_PRODUCT_MAPPING


def adjust_by_risk_level(
    name: str,
    default_equity_ratio: Decimal,
    default_sensitivity: Decimal,
    risk_level: RiskLevel | None = None,
) -> tuple[Decimal, Decimal]:
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


class RealtimePnlEstimator(RealtimePnlConfigMixin):
    def __init__(self) -> None:
        self.cache_path = config.cache_path
        self.domestic_cache_file = self.cache_path / "market_index_domestic.json"
        self.foreign_cache_file = self.cache_path / "market_index_foreign.json"
        self.fund_cache_file = self.cache_path / "fund_quotes.json"
        self.stock_cache_file = self.cache_path / "stock_quotes.json"
        self._fund_codes_map: dict[str, str] | None = None
        self._stock_codes_map: dict[str, str] | None = None

    def estimate_product_pnl(
        self,
        product: InvestmentProduct,
        moves: dict[str, Decimal],
        is_weekly: bool = False,
    ) -> dict[str, Any]:
        current_amount = product.current_amount or Decimal("0")
        inv_type = product.investment_type.value if product.investment_type else ""

        fund_moves = self._read_fund_quotes_from_cache()
        stock_moves = self._read_stock_quotes_from_cache()
        fund_codes_map = self._load_fund_codes_config()
        stock_codes_map = self._load_stock_codes_config()

        if inv_type in ["基金", "混合", "股票", "指数", "债券"]:
            fund_code = None
            if product.name in fund_codes_map:
                fund_code = fund_codes_map[product.name]
            else:
                for keyword, code in fund_codes_map.items():
                    if keyword in product.name or product.name in keyword:
                        fund_code = code
                        break

            if fund_code and fund_code in fund_moves:
                index_move = fund_moves[fund_code]
                pnl = current_amount * index_move / Decimal("100")
                return_rate = index_move

                return {
                    "name": product.name,
                    "type": inv_type,
                    "risk": product.risk_level.value if product.risk_level else "中",
                    "amount": current_amount,
                    "equity_ratio": Decimal("1"),
                    "index_key": f"基金净值({fund_code})",
                    "index_move": index_move,
                    "sensitivity": Decimal("1"),
                    "pnl": pnl,
                    "return_rate": return_rate,
                    "data_source": "基金净值",
                }

        if inv_type in ["股票", "美股", "港股", "A股"]:
            stock_code = None
            if product.name in stock_codes_map:
                stock_code = stock_codes_map[product.name]
            else:
                for keyword, code in stock_codes_map.items():
                    if keyword in product.name or product.name in keyword:
                        stock_code = code
                        break

            if stock_code and stock_code in stock_moves:
                index_move = stock_moves[stock_code]
                pnl = current_amount * index_move / Decimal("100")
                return_rate = index_move

                return {
                    "name": product.name,
                    "type": inv_type,
                    "risk": product.risk_level.value if product.risk_level else "中",
                    "amount": current_amount,
                    "equity_ratio": Decimal("1"),
                    "index_key": f"股票行情({stock_code})",
                    "index_move": index_move,
                    "sensitivity": Decimal("1"),
                    "pnl": pnl,
                    "return_rate": return_rate,
                    "data_source": "股票行情",
                }

        mapping = find_product_mapping(product.name, product.investment_type)

        equity_ratio = mapping.equity_ratio
        sensitivity = mapping.direct_sensitivity

        equity_ratio, sensitivity = adjust_by_risk_level(
            product.name,
            equity_ratio,
            sensitivity,
            product.risk_level,
        )

        amount_eq = current_amount * equity_ratio

        index_key = mapping.index_key
        index_move = Decimal("0")

        if index_key != "Blend" and index_key in moves:
            index_move = moves[index_key]
        elif index_key == "Blend":
            sensitivity = mapping.sensitivity_to_sh
            index_move = moves.get("SHComp", Decimal("0"))

        pct = (index_move / Decimal("100")) * sensitivity
        pnl = amount_eq * pct

        return_rate = (pnl / current_amount * Decimal("100")) if current_amount != 0 else Decimal("0")

        return {
            "name": product.name,
            "type": inv_type,
            "risk": product.risk_level.value if product.risk_level else "中",
            "amount": current_amount,
            "equity_ratio": equity_ratio,
            "index_key": index_key,
            "index_move": index_move,
            "sensitivity": sensitivity,
            "pnl": pnl,
            "return_rate": return_rate,
            "data_source": "指数估算",
        }

    def estimate_portfolio_pnl(
        self,
        products: list[InvestmentProduct],
        is_weekly: bool = False,
        filter_equity: bool = True,
    ) -> dict[str, Any]:
        moves = self.read_index_moves_from_cache(is_weekly)

        if not moves:
            return {
                "total": Decimal("1"),
                "details": [],
                "error": "无法读取市场指数数据，请先更新缓存",
            }

        total_amount_all = self._get_total_amount_from_summary()

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
                if p.investment_type not in exclude_types and p.current_amount and p.current_amount > 0
            ]

        details = []
        total_pnl = Decimal("0")
        total_amount = Decimal("0")

        for product in products:
            result = self.estimate_product_pnl(product, moves, is_weekly)
            details.append(result)
            total_pnl += result["pnl"]
            total_amount += result["amount"]

        total_return_rate = (total_pnl / total_amount * Decimal("100")) if total_amount != 0 else Decimal("0")

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
