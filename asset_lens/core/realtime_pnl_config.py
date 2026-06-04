import json
import logging
from decimal import Decimal

from ..config import config
from ..utils.json_cache import read_json_cache_dict

logger = logging.getLogger(__name__)


class RealtimePnlConfigMixin:
    _fund_codes_map: dict[str, str] | None
    _stock_codes_map: dict[str, str] | None

    def _load_fund_codes_config(self) -> dict[str, str]:
        if self._fund_codes_map is not None:  # type: ignore[has-type]
            return self._fund_codes_map  # type: ignore[no-any-return,has-type]

        config_file = config.project_root / "config" / "fund_stock_codes.json"
        result = {}

        if not config_file.exists():
            logger.warning(f"基金代码配置文件不存在: {config_file}", extra={"config_file": str(config_file)})
            self._fund_codes_map = {}  # type: ignore[var-annotated]
            return {}

        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.error(
                    f"基金代码配置格式错误: 期望 dict，得到 {type(data).__name__}",
                    extra={"config_file": str(config_file)},
                )
                self._fund_codes_map = {}
                return {}

            funds = data.get("funds", [])
            if not isinstance(funds, list):
                logger.warning(
                    f"基金列表格式错误: 期望 list，得到 {type(funds).__name__}", extra={"config_file": str(config_file)}
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
                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(
                        f"处理基金数据失败: {fund}", exc_info=True, extra={"fund": str(fund), "error": str(e)}
                    )
                    continue

            logger.info(f"成功加载 {len(result)} 个基金代码映射", extra={"count": len(result)})
            self._fund_codes_map = result
            return result

        except json.JSONDecodeError as e:
            logger.error(
                f"基金代码配置 JSON 解析失败: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)},
            )
            self._fund_codes_map = {}
            return {}

        except OSError as e:
            logger.error(
                f"读取基金代码配置文件失败: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)},
            )
            self._fund_codes_map = {}
            return {}

        except (ValueError, TypeError) as e:
            logger.error(
                f"加载基金代码配置时发生未知错误: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)},
            )
            self._fund_codes_map = {}
            return {}

    def _load_stock_codes_config(self) -> dict[str, str]:
        if self._stock_codes_map is not None:  # type: ignore[has-type]
            return self._stock_codes_map  # type: ignore[no-any-return,has-type]

        config_file = config.project_root / "config" / "fund_stock_codes.json"
        result = {}

        if not config_file.exists():
            logger.warning(f"股票代码配置文件不存在: {config_file}", extra={"config_file": str(config_file)})
            self._stock_codes_map = {}  # type: ignore[var-annotated]
            return {}

        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.error(
                    f"股票代码配置格式错误: 期望 dict，得到 {type(data).__name__}",
                    extra={"config_file": str(config_file)},
                )
                self._stock_codes_map = {}
                return {}

            stocks = data.get("stocks", [])
            if not isinstance(stocks, list):
                logger.warning(
                    f"股票列表格式错误: 期望 list，得到 {type(stocks).__name__}", extra={"config_file": str(config_file)}
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
                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(
                        f"处理股票数据失败: {stock}", exc_info=True, extra={"stock": str(stock), "error": str(e)}
                    )
                    continue

            logger.info(f"成功加载 {len(result)} 个股票代码映射", extra={"count": len(result)})
            self._stock_codes_map = result
            return result

        except json.JSONDecodeError as e:
            logger.error(
                f"股票代码配置 JSON 解析失败: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)},
            )
            self._stock_codes_map = {}
            return {}

        except OSError as e:
            logger.error(
                f"读取股票代码配置文件失败: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)},
            )
            self._stock_codes_map = {}
            return {}

        except (ValueError, TypeError) as e:
            logger.error(
                f"加载股票代码配置时发生未知错误: {e}",
                exc_info=True,
                extra={"config_file": str(config_file), "error": str(e)},
            )
            self._stock_codes_map = {}
            return {}

    def _read_fund_quotes_from_cache(self) -> dict[str, Decimal]:
        moves: dict[str, Decimal] = {}

        data = read_json_cache_dict(self.fund_cache_file)  # type: ignore[attr-defined]
        if data:
            for code, fund_data in data.get("data", {}).items():
                change_percent = fund_data.get("change_percent", 0)
                moves[code] = Decimal(str(change_percent))

        return moves

    def _read_stock_quotes_from_cache(self) -> dict[str, Decimal]:
        moves: dict[str, Decimal] = {}

        data = read_json_cache_dict(self.stock_cache_file)  # type: ignore[attr-defined]
        if data:
            for code, stock_data in data.get("data", {}).items():
                change_percent = stock_data.get("change_percent", 0)
                moves[code] = Decimal(str(change_percent))

        return moves

    def _get_total_amount_from_summary(self) -> Decimal:
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
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"从资产汇总获取总金额失败: {e}", exc_info=True)
        return Decimal("0")

    def read_index_moves_from_cache(self, is_weekly: bool = False) -> dict[str, Decimal]:
        moves: dict[str, Decimal] = {}

        domestic_data = read_json_cache_dict(self.domestic_cache_file) or {}  # type: ignore[attr-defined]
        if domestic_data:
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

        foreign_data = read_json_cache_dict(self.foreign_cache_file)  # type: ignore[attr-defined]
        if foreign_data:
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
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"读取国内黄金数据失败: {e}", exc_info=True)

        return moves
