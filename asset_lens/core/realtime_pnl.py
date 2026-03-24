import json
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..config import config
from ..data.models import InvestmentProduct, InvestmentType, RiskLevel

logger = logging.getLogger(__name__)


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
    risk_level: RiskLevel | None = None,
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
        self.fund_cache_file = self.cache_path / "fund_quotes.json"
        self.stock_cache_file = self.cache_path / "stock_quotes.json"
        self._fund_codes_map: dict[str, str] | None = None
        self._stock_codes_map: dict[str, str] | None = None

    def _load_fund_codes_config(self) -> dict[str, str]:
        """加载基金代码配置

        Returns:
            基金代码映射字典 {关键词: 代码}

        Note:
            如果加载失败，返回空字典并记录警告
        """
        if self._fund_codes_map is not None:
            return self._fund_codes_map

        config_file = config.project_root / "config" / "fund_stock_codes.json"
        result = {}

        if not config_file.exists():
            logger.warning(
                f"基金代码配置文件不存在: {config_file}",
                extra={"config_file": str(config_file)}
            )
            self._fund_codes_map = {}
            return {}

        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.error(
                    f"基金代码配置格式错误: 期望 dict，得到 {type(data).__name__}",
                    extra={"config_file": str(config_file)}
                )
                self._fund_codes_map = {}
                return {}

            funds = data.get("funds", [])
            if not isinstance(funds, list):
                logger.warning(
                    f"基金列表格式错误: 期望 list，得到 {type(funds).__name__}",
                    extra={"config_file": str(config_file)}
                )
                self._fund_codes_map = {}
                return {}

            for fund in funds:
                try:
                    name = fund.get("name", "")
                    code = fund.get("code", "")
                    if name and code:
                        result[name] = code

                    for keyword in fund.get("keywords", []):
                        if keyword and code:
                            result[keyword] = code
                except Exception as e:
                    logger.warning(
                        f"处理基金数据失败: {fund}",
                        exc_info=True,
                        extra={"fund": str(fund), "error": str(e)}
                    )
                    continue

            logger.info(
                f"成功加载 {len(result)} 个基金代码映射",
                extra={"count": len(result)}
            )
            self._fund_codes_map = result
            return result

        except json.JSONDecodeError as e:
            logger.error(
                f"基金代码配置 JSON 解析失败: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)}
            )
            self._fund_codes_map = {}
            return {}

        except OSError as e:
            logger.error(
                f"读取基金代码配置文件失败: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)}
            )
            self._fund_codes_map = {}
            return {}

        except Exception as e:
            logger.error(
                f"加载基金代码配置时发生未知错误: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)}
            )
            self._fund_codes_map = {}
            return {}

    def _load_stock_codes_config(self) -> dict[str, str]:
        """加载股票代码配置

        Returns:
            股票代码映射字典 {关键词: 代码}

        Note:
            如果加载失败，返回空字典并记录警告
        """
        if self._stock_codes_map is not None:
            return self._stock_codes_map

        config_file = config.project_root / "config" / "fund_stock_codes.json"
        result = {}

        if not config_file.exists():
            logger.warning(
                f"股票代码配置文件不存在: {config_file}",
                extra={"config_file": str(config_file)}
            )
            self._stock_codes_map = {}
            return {}

        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.error(
                    f"股票代码配置格式错误: 期望 dict，得到 {type(data).__name__}",
                    extra={"config_file": str(config_file)}
                )
                self._stock_codes_map = {}
                return {}

            stocks = data.get("stocks", [])
            if not isinstance(stocks, list):
                logger.warning(
                    f"股票列表格式错误: 期望 list，得到 {type(stocks).__name__}",
                    extra={"config_file": str(config_file)}
                )
                self._stock_codes_map = {}
                return {}

            for stock in stocks:
                try:
                    name = stock.get("name", "")
                    code = stock.get("code", "")
                    if name and code:
                        result[name] = code

                    for keyword in stock.get("keywords", []):
                        if keyword and code:
                            result[keyword] = code
                except Exception as e:
                    logger.warning(
                        f"处理股票数据失败: {stock}",
                        exc_info=True,
                        extra={"stock": str(stock), "error": str(e)}
                    )
                    continue

            logger.info(
                f"成功加载 {len(result)} 个股票代码映射",
                extra={"count": len(result)}
            )
            self._stock_codes_map = result
            return result

        except json.JSONDecodeError as e:
            logger.error(
                f"股票代码配置 JSON 解析失败: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)}
            )
            self._stock_codes_map = {}
            return {}

        except OSError as e:
            logger.error(
                f"读取股票代码配置文件失败: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)}
            )
            self._stock_codes_map = {}
            return {}

        except Exception as e:
            logger.error(
                f"加载股票代码配置时发生未知错误: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)}
            )
            self._stock_codes_map = {}
            return {}

    def _read_fund_quotes_from_cache(self) -> dict[str, Decimal]:
        """从缓存读取基金净值涨跌幅"""
        moves: dict[str, Decimal] = {}

        if not self.fund_cache_file.exists():
            return moves

        try:
            with open(self.fund_cache_file, encoding="utf-8") as f:
                data = json.load(f)

            for code, fund_data in data.get("data", {}).items():
                change_percent = fund_data.get("change_percent", 0)
                moves[code] = Decimal(str(change_percent))
        except Exception as e:
            logger.warning(f"读取基金净值数据失败: {e}", exc_info=True)

        return moves

    def _read_stock_quotes_from_cache(self) -> dict[str, Decimal]:
        """从缓存读取股票行情涨跌幅"""
        moves: dict[str, Decimal] = {}

        if not self.stock_cache_file.exists():
            return moves

        try:
            with open(self.stock_cache_file, encoding="utf-8") as f:
                data = json.load(f)

            for code, stock_data in data.get("data", {}).items():
                change_percent = stock_data.get("change_percent", 0)
                moves[code] = Decimal(str(change_percent))
        except Exception as e:
            logger.warning(f"读取股票行情数据失败: {e}", exc_info=True)

        return moves

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
                summary_file = data_dir / "备份-表格 1.csv"
            if summary_file.exists():
                summaries = AssetSummaryParser.parse_csv_file(summary_file)
                if summaries:
                    return summaries[-1].total_amount or Decimal("0")
        except Exception as e:
            logger.warning(f"从资产汇总获取总金额失败: {e}", exc_info=True)
        return Decimal("0")

    def read_index_moves_from_cache(self, is_weekly: bool = False) -> dict[str, Decimal]:
        """
        从缓存读取指数涨跌幅数据

        Args:
            is_weekly: 是否为周预估

        Returns:
            指数涨跌幅字典
        """
        moves: dict[str, Decimal] = {}

        # 读取国内市场数据
        if self.domestic_cache_file.exists():
            try:
                with open(self.domestic_cache_file, encoding="utf-8") as f:
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
                logger.warning(f"读取国内市场数据失败: {e}", exc_info=True)

        if self.foreign_cache_file.exists():
            try:
                with open(self.foreign_cache_file, encoding="utf-8") as f:
                    foreign_data = json.load(f)

                foreign_index_mapping = {
                    "QQQ": "Nasdaq",
                    "纳斯达克": "Nasdaq",
                    "SPY": "SP500",
                    "标普": "SP500",
                    "GLD": "Gold",
                    "黄金": "Gold",
                    "HSI": "HangSeng",
                    "恒生": "HangSeng",
                    "NKY": "Nikkei",
                    "日经": "Nikkei",
                    "UKX": "FTSE",
                    "富时": "FTSE",
                    "DAX": "DAX",
                    "CAC": "CAC",
                }

                for key, index_data in foreign_data.get("指数数据", {}).items():
                    for pattern, index_code in foreign_index_mapping.items():
                        if pattern in key:
                            if is_weekly:
                                weekly_change = index_data.get("周期表现", {}).get("周涨跌幅", 0)
                                if weekly_change == 0:
                                    weekly_change = index_data.get("涨跌幅", 0)
                                moves[index_code] = Decimal(str(weekly_change))
                            else:
                                moves[index_code] = Decimal(str(index_data.get("涨跌幅", 0)))
                            break
            except Exception as e:
                logger.warning(f"读取海外市场数据失败: {e}", exc_info=True)

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
                logger.warning(f"读取国内黄金数据失败: {e}", exc_info=True)

        return moves

    def estimate_product_pnl(
        self,
        product: InvestmentProduct,
        moves: dict[str, Decimal],
        is_weekly: bool = False,
    ) -> dict[str, Any]:
        """
        估算单个产品的盈亏

        Args:
            product: 投资产品
            moves: 指数涨跌幅字典
            is_weekly: 是否为周预估

        Returns:
            盈亏估算结果
        """
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

        return_rate = (
            (pnl / current_amount * Decimal("100")) if current_amount != 0 else Decimal("0")
        )

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
