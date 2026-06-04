import contextlib
import csv
import logging
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

from ..config import config
from ..data.models import InvestmentProduct, InvestmentType, RiskLevel
from .csv_data_loader import CSVDataLoaderMixin
from .csv_irr import CSVIrrMixin
from .parser_utils import parse_date as _parse_date
from .parser_utils import parse_decimal as _parse_decimal
from .parsers.exchange_rate_cache import ExchangeRateCache, exchange_rate_cache
from .parsers.investment_calculator import days360

logger = logging.getLogger(__name__)

__all__ = ["CSVParser", "ExchangeRateCache", "days360", "exchange_rate_cache"]


class CSVParser(CSVDataLoaderMixin, CSVIrrMixin):
    COLUMN_MAPPING: ClassVar[dict[str, str]] = {
        "类型": "investment_type",
        "名称": "name",
        "风险": "risk_level",
        "平台A": "wechat_amount",
        "平台B": "alipay_amount",
        "到期时间": "maturity_date",
        "滚动": "is_rolling",
        "开始日期": "start_date",
        "初始金额": "initial_amount",
        "二次买入": "secondary_buy",
        "二次金额": "secondary_amount",
        "收益金额": "profit_amount",
        "投资天数": "investment_days",
        "收益率": "return_rate",
        "年化收益": "annual_return",
        "复利年化": "compound_return",
        "利息发放": "interest_payment",
        "交易记录": "transaction_records",
        "默认顺序": "default_order",
        "美元汇率": "usd_rate",
        "港元汇率": "hkd_rate",
    }

    @staticmethod
    def parse_decimal(value: str) -> Decimal | None:
        return _parse_decimal(value)

    @staticmethod
    def get_exchange_rates(data_dir: Path) -> tuple[float, float]:
        cache_key = str(data_dir)

        cached = exchange_rate_cache.get(cache_key)
        if cached:
            return cached

        default_usd = float(config.default_usd_rate)
        default_hkd = float(config.default_hkd_rate)

        try:
            summary_files = list(data_dir.glob("资产汇总*.csv"))
            if summary_files:
                summary_path = summary_files[0]
                with open(summary_path, encoding="utf-8-sig") as f:
                    lines = f.readlines()

                if len(lines) >= 2:
                    header = lines[0].strip().split(",")
                    usd_idx = -1
                    hkd_idx = -1

                    for i, col in enumerate(header):
                        col_clean = col.replace(" ", "")
                        if "美元汇率" in col_clean:
                            usd_idx = i
                        if "港元汇率" in col_clean:
                            hkd_idx = i

                    if usd_idx != -1 or hkd_idx != -1:
                        usd_rate = None
                        hkd_rate = None

                        for i in range(len(lines) - 1, 0, -1):
                            cells = lines[i].strip().split(",")
                            if len(cells) <= max(usd_idx, hkd_idx):
                                continue

                            if usd_idx != -1 and usd_rate is None:
                                try:
                                    rate = float(cells[usd_idx])
                                    if 5 < rate < 10:
                                        usd_rate = rate
                                except (ValueError, IndexError):
                                    pass

                            if hkd_idx != -1 and hkd_rate is None:
                                try:
                                    rate = float(cells[hkd_idx])
                                    if 0.8 < rate < 1.2:
                                        hkd_rate = rate
                                except (ValueError, IndexError):
                                    pass

                            if usd_rate is not None and hkd_rate is not None:
                                break

                        if usd_rate is not None or hkd_rate is not None:
                            rates = (usd_rate or default_usd, hkd_rate or default_hkd)
                            exchange_rate_cache.set(cache_key, rates)
                            logger.info(f"从资产汇总加载汇率: USD={rates[0]}, HKD={rates[1]}")
                            return rates

            csv_files = list(data_dir.glob("投资产品*.csv"))
            if csv_files:
                csv_path = csv_files[0]
                with open(csv_path, encoding="utf-8-sig") as f:
                    lines = f.readlines()

                if len(lines) >= 2:
                    header = lines[0].strip().split(",")
                    usd_idx = -1
                    hkd_idx = -1

                    for i, col in enumerate(header):
                        col_clean = col.replace(" ", "")
                        if "美元汇率" in col_clean:
                            usd_idx = i
                        if "港元汇率" in col_clean:
                            hkd_idx = i

                    if usd_idx != -1 or hkd_idx != -1:
                        usd_rate = None
                        hkd_rate = None

                        for i in range(1, len(lines)):
                            cells = lines[i].strip().split(",")
                            if len(cells) <= max(usd_idx, hkd_idx):
                                continue

                            if usd_idx != -1 and usd_rate is None:
                                try:
                                    rate = float(cells[usd_idx])
                                    if 5 < rate < 10:
                                        usd_rate = rate
                                except (ValueError, IndexError):
                                    pass

                            if hkd_idx != -1 and hkd_rate is None:
                                try:
                                    rate = float(cells[hkd_idx])
                                    if 0.8 < rate < 1.2:
                                        hkd_rate = rate
                                except (ValueError, IndexError):
                                    pass

                            if usd_rate is not None and hkd_rate is not None:
                                break

                        if usd_rate is not None or hkd_rate is not None:
                            rates = (usd_rate or default_usd, hkd_rate or default_hkd)
                            exchange_rate_cache.set(cache_key, rates)
                            logger.info(f"从投资产品加载汇率: USD={rates[0]}, HKD={rates[1]}")
                            return rates

            return default_usd, default_hkd

        except (OSError, ValueError, csv.Error) as e:
            logger.error(f"加载汇率失败: {data_dir}", exc_info=True, extra={"error": str(e)})
            return default_usd, default_hkd

    @staticmethod
    def parse_date(value: str) -> datetime | None:
        return _parse_date(value)

    @staticmethod
    def parse_boolean(value: str) -> bool:
        if not value:
            return False
        return value.strip().lower() in ["是", "yes", "true", "1", "可赎"]

    @staticmethod
    def parse_investment_type(value: str) -> InvestmentType:
        if not value:
            return InvestmentType.OTHER

        type_mapping = {
            "货币": InvestmentType.MONETARY,
            "现金": InvestmentType.CASH,
            "现金（港元）": InvestmentType.HK_CASH,
            "指数基金": InvestmentType.INDEX_FUND,
            "债券基金": InvestmentType.BOND_FUND,
            "混合基金": InvestmentType.MIXED_FUND,
            "股票": InvestmentType.STOCK,
            "美股": InvestmentType.US_STOCK,
            "美股（美元）": InvestmentType.US_STOCK,
            "港股": InvestmentType.HK_STOCK,
            "港股（港元）": InvestmentType.HK_STOCK,
            "QDII": InvestmentType.QDII,
            "理财": InvestmentType.WEALTH,
            "高端理财": InvestmentType.HIGH_END_WEALTH,
            "券商理财": InvestmentType.BROKER_WEALTH,
            "公募固收": InvestmentType.PUBLIC_FIXED_INCOME,
            "定期存款": InvestmentType.FIXED_DEPOSIT,
            "债券": InvestmentType.BOND,
            "特别国债": InvestmentType.SPECIAL_TREASURY_BOND,
            "REITs": InvestmentType.REITS,
            "黄金": InvestmentType.GOLD,
            "基金": InvestmentType.FUND,
            "定投基金": InvestmentType.DCA_FUND,
            "股息基金（港元）": InvestmentType.HK_DIVIDEND_FUND,
            "个人养老金": InvestmentType.PENSION,
            "ETF": InvestmentType.ETF,
            "美元基金": InvestmentType.USD_FUND,
            "美元基金（美元）": InvestmentType.USD_FUND,
        }

        return type_mapping.get(value.strip(), InvestmentType.OTHER)

    @staticmethod
    def parse_risk_level(value: str) -> RiskLevel:
        if not value:
            return RiskLevel.MEDIUM

        risk_mapping = {
            "低": RiskLevel.LOW,
            "中低": RiskLevel.MEDIUM_LOW,
            "中": RiskLevel.MEDIUM,
            "中高": RiskLevel.MEDIUM_HIGH,
            "高": RiskLevel.HIGH,
        }

        return risk_mapping.get(value.strip(), RiskLevel.MEDIUM)

    @staticmethod
    def parse_investment_days(value: str) -> int | None:
        if not value or not value.strip():
            return None

        value = value.strip()
        if value.endswith("天"):
            value = value[:-1]

        try:
            return int(value)
        except ValueError:
            return None

    @classmethod
    def parse_row(cls, row: dict, reference_date: date | None = None) -> InvestmentProduct | None:
        if reference_date is None:
            reference_date = datetime.now().date()

        try:
            investment_type = cls.parse_investment_type(row.get("类型", ""))
            name = row.get("名称", "").strip()
            risk_level = cls.parse_risk_level(row.get("风险", ""))

            if not name:
                return None

            if name in ["小计", "合计", "总计", "汇总", "平均"]:
                return None

            platform_amounts = {}
            from asset_lens.core.platform_loader import PlatformLoader

            from ..config import config

            if not PlatformLoader._loaded:
                PlatformLoader.load(data_mode=config.data_mode)

            for platform in PlatformLoader.get_all_platforms(data_mode=config.data_mode):
                amount = cls.parse_decimal(row.get(platform.name, ""))
                if amount:
                    platform_amounts[platform.id] = amount

            maturity_date = cls.parse_date(row.get("到期时间", ""))
            start_date = cls.parse_date(row.get("开始日期", ""))

            is_rolling = cls.parse_boolean(row.get("滚动", ""))

            initial_amount = cls.parse_decimal(row.get("初始金额", ""))
            secondary_buy = cls.parse_decimal(row.get("二次买入", ""))
            secondary_amount = cls.parse_decimal(row.get("二次金额", ""))
            profit_amount = cls.parse_decimal(row.get("收益金额", ""))

            investment_days = cls.parse_investment_days(row.get("投资天数", ""))

            if start_date:
                calculated_days = days360(start_date.date(), reference_date)
                if calculated_days > 0:
                    investment_days = calculated_days

            return_rate = cls.parse_decimal(row.get("收益率", ""))
            annual_return = cls.parse_decimal(row.get("年化收益", ""))
            compound_return = cls.parse_decimal(row.get("复利年化", ""))

            interest_payment = cls.parse_decimal(row.get("利息发放", ""))

            transaction_records = row.get("交易记录", "").strip()

            default_order = None
            if row.get("默认顺序", "").strip():
                with contextlib.suppress(ValueError):
                    default_order = int(row.get("默认顺序", "").strip())

            usd_rate = cls.parse_decimal(row.get("美元汇率", ""))
            hkd_rate = cls.parse_decimal(row.get("港元汇率", ""))

            product = InvestmentProduct(
                investment_type=investment_type,
                name=name,
                risk_level=risk_level,
                platform_amounts=platform_amounts,
                maturity_date=maturity_date.date() if maturity_date else None,
                is_rolling=is_rolling,
                start_date=start_date.date() if start_date else None,
                initial_amount=initial_amount,
                secondary_buy=secondary_buy,
                secondary_amount=secondary_amount,
                profit_amount=profit_amount,
                investment_days=investment_days,
                return_rate=return_rate,
                annual_return=annual_return,
                compound_return=compound_return,
                interest_payment=interest_payment,
                transaction_records=transaction_records if transaction_records else None,
                default_order=default_order,
                usd_rate=usd_rate,
                hkd_rate=hkd_rate,
            )

            total_amount = sum(platform_amounts.values(), Decimal("0"))

            if total_amount > 0:
                product.current_amount = total_amount
            elif initial_amount is not None and profit_amount is not None:
                product.current_amount = initial_amount + profit_amount
            elif initial_amount is not None:
                product.current_amount = initial_amount

            return product

        except (ValueError, KeyError, IndexError, TypeError) as e:
            logger.error(f"解析行数据时出错: {e}, 行数据: {row}")
            return None
