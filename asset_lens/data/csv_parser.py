"""
CSV data parser for asset-lens.
CSV 数据读取和解析模块
"""

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import config
from ..data.models import Currency, InvestmentProduct, InvestmentType, RiskLevel
from .parser_utils import parse_date as _parse_date
from .parser_utils import parse_decimal as _parse_decimal


def days360(start_date: date, end_date: date, european: bool = False) -> int:
    """
    计算360天日历法的天数（金融计算方法）
    Args:
        start_date: 开始日期
        end_date: 结束日期
        european: 是否使用欧洲方法（31日改为30日）
    Returns:
        天数
    """
    start_year = start_date.year
    start_month = start_date.month
    start_day = start_date.day

    end_year = end_date.year
    end_month = end_date.month
    end_day = end_date.day

    if european:
        if start_day == 31:
            start_day = 30
        if end_day == 31:
            end_day = 30
    else:
        if start_day == 31:
            start_day = 30
        if end_day == 31 and start_day == 30:
            end_day = 30

    return (end_year - start_year) * 360 + (end_month - start_month) * 30 + (end_day - start_day)


class CSVParser:
    """CSV 数据解析器"""

    # CSV 列名映射
    COLUMN_MAPPING = {
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
        """解析 Decimal 值"""
        return _parse_decimal(value)

    @staticmethod
    def get_exchange_rates(data_dir: Path) -> tuple[float, float]:
        """
        从数据文件中读取美元和港元汇率
        优先从投资产品表格中读取，其次从工作表2中读取
        Args:
            data_dir: 数据目录路径
        Returns:
            (美元汇率, 港元汇率)
        """
        default_usd = float(config.default_usd_rate)
        default_hkd = float(config.default_hkd_rate)

        try:
            # 首先尝试从投资产品表格中读取汇率
            csv_files = list(data_dir.glob("投资产品*.csv"))
            if csv_files:
                csv_path = csv_files[0]
                with open(csv_path, "r", encoding="utf-8-sig") as f:
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
                        usd_rate = default_usd
                        hkd_rate = default_hkd

                        for i in range(1, len(lines)):
                            cells = lines[i].strip().split(",")
                            if len(cells) <= max(usd_idx, hkd_idx):
                                continue

                            if usd_idx != -1 and usd_rate == default_usd:
                                try:
                                    rate = float(cells[usd_idx])
                                    if 5 < rate < 10:
                                        usd_rate = rate
                                except (ValueError, IndexError):
                                    pass

                            if hkd_idx != -1 and hkd_rate == default_hkd:
                                try:
                                    rate = float(cells[hkd_idx])
                                    if 0.8 < rate < 1.2:
                                        hkd_rate = rate
                                except (ValueError, IndexError):
                                    pass

                            if usd_rate != default_usd and hkd_rate != default_hkd:
                                break

                        if usd_rate != default_usd or hkd_rate != default_hkd:
                            return usd_rate, hkd_rate

            # 其次尝试从工作表2文件读取
            ws2_files = list(data_dir.glob("*工作表 2*.csv"))
            if not ws2_files:
                ws2_files = list(data_dir.glob("*工作表*2*.csv"))

            if not ws2_files:
                return default_usd, default_hkd

            ws2_path = ws2_files[0]

            with open(ws2_path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()

            if len(lines) < 2:
                return default_usd, default_hkd

            # 解析表头
            header = lines[0].strip().split(",")
            usd_idx = -1
            hkd_idx = -1

            for i, col in enumerate(header):
                col_clean = col.replace(" ", "")
                if "美元汇率" in col_clean:
                    usd_idx = i
                if "港元汇率" in col_clean:
                    hkd_idx = i

            if usd_idx == -1 and hkd_idx == -1:
                return default_usd, default_hkd

            # 从最后一行往上找有数据的汇率
            usd_rate = default_usd
            hkd_rate = default_hkd

            for i in range(len(lines) - 1, 0, -1):
                cells = lines[i].strip().split(",")
                if len(cells) <= max(usd_idx, hkd_idx):
                    continue

                if usd_idx != -1 and usd_rate == default_usd:
                    try:
                        rate = float(cells[usd_idx])
                        if 5 < rate < 10:
                            usd_rate = rate
                    except (ValueError, IndexError):
                        pass

                if hkd_idx != -1 and hkd_rate == default_hkd:
                    try:
                        rate = float(cells[hkd_idx])
                        if 0.8 < rate < 1.2:
                            hkd_rate = rate
                    except (ValueError, IndexError):
                        pass

                if usd_rate != default_usd and hkd_rate != default_hkd:
                    break

            return usd_rate, hkd_rate

        except Exception:
            return default_usd, default_hkd

    @staticmethod
    def parse_date(value: str) -> datetime | None:
        """解析日期值"""
        return _parse_date(value)

    @staticmethod
    def parse_boolean(value: str) -> bool:
        """解析布尔值"""
        if not value:
            return False
        return value.strip().lower() in ["是", "yes", "true", "1", "可赎"]

    @staticmethod
    def parse_investment_type(value: str) -> InvestmentType:
        """解析投资类型"""
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
            "美元基金（美元）": InvestmentType.USD_FUND,
        }

        return type_mapping.get(value.strip(), InvestmentType.OTHER)

    @staticmethod
    def parse_risk_level(value: str) -> RiskLevel:
        """解析风险等级"""
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
        """解析投资天数，支持 '328天' 或 '328' 格式"""
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
        """解析单行数据
        Args:
            row: CSV 行数据
            reference_date: 参考日期（用于计算投资天数），默认为当前日期
        """
        if reference_date is None:
            reference_date = datetime.now().date()

        try:
            # 获取基础字段
            investment_type = cls.parse_investment_type(row.get("类型", ""))
            name = row.get("名称", "").strip()
            risk_level = cls.parse_risk_level(row.get("风险", ""))

            if not name:  # 名称不能为空
                return None

            # 过滤汇总行
            if name in ["小计", "合计", "总计", "汇总", "平均"]:
                return None

            # 解析平台金额（使用动态配置）
            platform_amounts = {}
            from asset_lens.core.platform_loader import PlatformLoader

            from ..config import config

            # 确保加载了平台配置
            if not PlatformLoader._loaded:
                PlatformLoader.load(data_mode=config.data_mode)

            for platform in PlatformLoader.get_all_platforms(data_mode=config.data_mode):
                amount = cls.parse_decimal(row.get(platform.name, ""))
                if amount:
                    platform_amounts[platform.id] = amount

            # 解析日期字段
            maturity_date = cls.parse_date(row.get("到期时间", ""))
            start_date = cls.parse_date(row.get("开始日期", ""))

            # 解析布尔值
            is_rolling = cls.parse_boolean(row.get("滚动", ""))

            # 解析数值字段
            initial_amount = cls.parse_decimal(row.get("初始金额", ""))
            secondary_buy = cls.parse_decimal(row.get("二次买入", ""))
            secondary_amount = cls.parse_decimal(row.get("二次金额", ""))
            profit_amount = cls.parse_decimal(row.get("收益金额", ""))

            # 解析投资天数（优先使用 days360 计算）
            investment_days = cls.parse_investment_days(row.get("投资天数", ""))

            # 如果有开始日期，使用 days360 重新计算投资天数
            if start_date:
                calculated_days = days360(start_date.date(), reference_date)
                if calculated_days > 0:
                    investment_days = calculated_days

            # 解析百分比字段
            return_rate = cls.parse_decimal(row.get("收益率", ""))
            annual_return = cls.parse_decimal(row.get("年化收益", ""))
            compound_return = cls.parse_decimal(row.get("复利年化", ""))

            # 解析利息发放
            interest_payment = cls.parse_decimal(row.get("利息发放", ""))

            # 解析交易记录
            transaction_records = row.get("交易记录", "").strip()

            # 解析默认顺序
            default_order = None
            if row.get("默认顺序", "").strip():
                try:
                    default_order = int(row.get("默认顺序", "").strip())
                except ValueError:
                    pass

            # 解析汇率
            usd_rate = cls.parse_decimal(row.get("美元汇率", ""))
            hkd_rate = cls.parse_decimal(row.get("港元汇率", ""))

            # 创建投资产品对象
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

            # 计算当前金额（所有平台金额之和）
            total_amount = sum(platform_amounts.values(), Decimal("0"))

            if total_amount > 0:
                product.current_amount = total_amount
            elif initial_amount is not None and profit_amount is not None:
                product.current_amount = initial_amount + profit_amount
            elif initial_amount is not None:
                product.current_amount = initial_amount

            return product

        except Exception as e:
            print(f"解析行数据时出错: {e}, 行数据: {row}")
            return None

    @classmethod
    def _calculate_irr_for_products(
        cls, products: List[InvestmentProduct], reference_date: Optional[datetime] = None
    ) -> List[InvestmentProduct]:
        """
        对有交易记录的产品使用 IRR 计算年化收益率（与 ts-demo 保持一致）
        Args:
            products: 投资产品列表
            reference_date: 参考日期（数据目录日期）
        Returns:
            更新后的投资产品列表
        """
        from ..core.dca_parser import DCAParser
        from ..core.irr_calculator import IRRCalculator

        irr_calculator = IRRCalculator()
        dca_parser = DCAParser()

        for product in products:
            transactions = []
            if product.transaction_records:
                is_dca = cls._is_dca_product(product)
                if is_dca:
                    transactions = cls._parse_dca_transactions(
                        product.transaction_records,
                        product.investment_type,
                        reference_date,
                        product.name,
                    )
                else:
                    transactions = cls._parse_transaction_records(product.transaction_records)

            total_buy = (
                sum(t["amount"] for t in transactions if t["type"] == "buy") if transactions else 0
            )
            total_sell = (
                sum(t["amount"] for t in transactions if t["type"] == "sell") if transactions else 0
            )

            is_dca_product = cls._is_dca_product(product)
            if is_dca_product and product.initial_amount and product.initial_amount > 0:
                # 检查交易记录计算的净投入与 CSV 初始金额是否一致
                net_invest = total_buy - total_sell
                if net_invest > 0 and abs(net_invest - float(product.initial_amount)) > 1:
                    diff = net_invest - float(product.initial_amount)
                    diff_days = abs(diff) / 100 if abs(diff) >= 100 else abs(diff) / 50
                    print(f"⚠️  定投产品数据不一致: {product.name}")
                    print(f"    CSV 初始金额: {product.initial_amount}")
                    print(f"    交易记录净投入: {net_invest:.2f}")
                    print(f"    差异: {diff:.2f} (约 {diff_days:.0f} 个交易日)")
                    print(f"    将使用 CSV 初始金额计算收益率")
                    print()

                current_value = float(product.current_amount or 0)
                initial_value = float(product.initial_amount)
                simple_return = (current_value - initial_value) / initial_value
                product.return_rate = Decimal(str(round(simple_return * 100, 2)))
            elif total_buy > 0:
                current_value = float(product.current_amount or 0)
                net_gain = current_value + total_sell - total_buy
                simple_return = net_gain / total_buy
                product.return_rate = Decimal(str(round(simple_return * 100, 2)))
            elif product.initial_amount and product.initial_amount > 0:
                current_value = float(product.current_amount or 0)
                initial_value = float(product.initial_amount)
                simple_return = (current_value - initial_value) / initial_value
                product.return_rate = Decimal(str(round(simple_return * 100, 2)))

            total_days = product.investment_days or 0
            if total_days > 0:
                is_bond_product = (
                    product.investment_type.value and "债" in product.investment_type.value
                ) or (product.name and "分红" in product.name)

                if is_bond_product:
                    # 对于债券类产品，使用简化计算方法（与 ts-demo 保持一致）
                    # 净收益 = 当前金额 + 利息 - 初始金额
                    if product.initial_amount and product.initial_amount > 0:
                        current_value = float(product.current_amount or 0)
                        interest = float(product.interest_payment or 0)
                        initial_value = float(product.initial_amount)
                        net_gain = current_value + interest - initial_value
                        simple_return = net_gain / initial_value
                        product.return_rate = Decimal(str(round(simple_return * 100, 2)))
                        simple_annualized = (1 + simple_return) ** (360 / total_days) - 1
                        product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
                elif is_dca_product and product.initial_amount and product.initial_amount > 0:
                    if product.start_date and product.current_amount:
                        cashflows = cls._calculate_cashflows_with_days_for_dca(
                            transactions,
                            product.start_date,
                            product.current_amount,
                            total_days,
                            product.initial_amount,
                        )
                    else:
                        cashflows = []

                    if cashflows and len(cashflows) > 1:
                        irr = irr_calculator.calculate_irr_with_days(cashflows)
                        if irr is not None and -1 < irr < 10:
                            product.annual_return = Decimal(str(round(irr * 100, 2)))
                        else:
                            if product.return_rate is not None:
                                simple_annualized = (1 + float(product.return_rate) / 100) ** (
                                    360 / total_days
                                ) - 1
                                product.annual_return = Decimal(
                                    str(round(simple_annualized * 100, 2))
                                )
                    else:
                        if product.return_rate is not None:
                            simple_annualized = (1 + float(product.return_rate) / 100) ** (
                                360 / total_days
                            ) - 1
                            product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
                elif total_days < 180:
                    if product.return_rate is not None:
                        simple_annualized = (1 + float(product.return_rate) / 100) ** (
                            360 / total_days
                        ) - 1
                        product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
                elif transactions and len(transactions) > 1 and total_buy > 0:
                    cashflows = cls._calculate_cashflows_with_days(
                        transactions,
                        product.start_date,
                        product.current_amount,
                        total_days,
                    )

                    if cashflows and len(cashflows) > 1:
                        irr = irr_calculator.calculate_irr_with_days(cashflows)
                        if irr is not None and -1 < irr < 10:
                            if product.return_rate is not None:
                                simple_annualized = (1 + float(product.return_rate) / 100) ** (
                                    360 / total_days
                                ) - 1
                                diff = abs(irr - simple_annualized)
                                if diff > 1:
                                    product.annual_return = Decimal(
                                        str(round(simple_annualized * 100, 2))
                                    )
                                else:
                                    product.annual_return = Decimal(str(round(irr * 100, 2)))
                            else:
                                product.annual_return = Decimal(str(round(irr * 100, 2)))
                        else:
                            if product.return_rate is not None:
                                simple_annualized = (1 + float(product.return_rate) / 100) ** (
                                    360 / total_days
                                ) - 1
                                product.annual_return = Decimal(
                                    str(round(simple_annualized * 100, 2))
                                )
                elif product.return_rate is not None:
                    simple_annualized = (1 + float(product.return_rate) / 100) ** (
                        360 / total_days
                    ) - 1
                    product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))

        return products

    @classmethod
    def _is_dca_product(cls, product: InvestmentProduct) -> bool:
        """判断是否为定投产品"""
        if product.investment_type and product.investment_type.value == "定投基金":
            return True
        if product.transaction_records:
            records = product.transaction_records.strip()
            if "-now:" in records or "-" in records.split(":")[0] if ":" in records else False:
                buy_count = records.count(":buy:")
                sell_count = records.count(":sell:")
                return buy_count >= 1 and sell_count == 0
        return False

    @classmethod
    def _parse_dca_transactions(
        cls,
        records_str: str,
        investment_type,
        reference_date: Optional[datetime] = None,
        product_name: Optional[str] = None,
    ) -> List[dict]:
        """解析定投交易记录"""
        from datetime import datetime

        from ..core.dca_parser import DCAParser

        dca_parser = DCAParser()
        transactions = dca_parser.parse_transaction_record(
            records_str,
            reference_date=reference_date or datetime.now(),
            investment_type=investment_type,
            product_name=product_name,
        )

        result = []
        for t in transactions:
            result.append(
                {
                    "date": t.transaction_date.strftime("%Y/%m/%d"),
                    "type": t.action,
                    "amount": float(t.amount),
                }
            )

        return result

    @classmethod
    def _calculate_cashflows_with_days(
        cls, transactions: List[dict], start_date, current_amount, total_days: int
    ) -> List[dict]:
        """
        计算现金流（使用 days360 计算天数，与 ts-demo 一致）
        Args:
            transactions: 交易记录列表
            start_date: 开始日期
            current_amount: 当前金额
            total_days: 总投资天数
        Returns:
            现金流列表，格式为 [{"amount": float, "days": int}, ...]
        """
        from datetime import date

        cashflows: List[dict] = []

        if not start_date:
            return cashflows

        for trans in transactions:
            # 解析交易日期 - 支持多种格式
            date_str = trans["date"]
            try:
                # 尝试 YYYY/MM/DD-MM/DD 范围格式
                if "/" in date_str and "-" in date_str:
                    # 格式: 2025/12/29-2025/12/31，取第一个日期
                    date_parts = date_str.split("-")[0].split("/")
                    trans_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                elif "/" in date_str:
                    date_parts = date_str.split("/")
                    trans_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                elif "-" in date_str and date_str.count("-") == 2:
                    date_parts = date_str.split("-")
                    trans_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                else:
                    continue
            except (ValueError, IndexError) as e:
                print(f"⚠️  日期解析失败: {date_str}, 错误: {e}")
                continue

            trans_days = days360(start_date, trans_date)

            if trans["type"] == "buy":
                cashflows.append({"amount": -trans["amount"], "days": trans_days})
            elif trans["type"] == "sell":
                cashflows.append({"amount": trans["amount"], "days": trans_days})

        # 添加当前金额作为最终现金流
        if current_amount:
            cashflows.append({"amount": float(current_amount), "days": total_days})

        return cashflows

    @classmethod
    def _calculate_cashflows_with_days_for_dca(
        cls,
        transactions: List[dict],
        start_date: date,
        current_amount: Decimal,
        total_days: int,
        initial_amount: Decimal,
    ) -> List[dict]:
        """
        计算定投产品的现金流（使用初始金额作为净投入）
        Args:
            transactions: 交易记录列表
            start_date: 开始日期
            current_amount: 当前金额
            total_days: 总投资天数
            initial_amount: 初始金额（净投入）
        Returns:
            现金流列表，格式为 [{"amount": float, "days": int}, ...]
        """
        cashflows: List[dict] = []

        if not start_date:
            return cashflows

        # 定投产品：第一笔投入为初始金额（负数表示流出）
        cashflows.append({"amount": -float(initial_amount), "days": 0})

        # 添加当前金额作为最终现金流
        if current_amount:
            cashflows.append({"amount": float(current_amount), "days": total_days})

        return cashflows

    @classmethod
    def _parse_transaction_records(cls, records_str: str) -> List[dict]:
        """
        解析交易记录字符串
        Args:
            records_str: 交易记录字符串，格式如 "2025/8/8:buy:15703; 2025/9/18:sell:11581"
        Returns:
            交易记录列表
        """
        transactions: List[Dict[str, Any]] = []
        if not records_str:
            return transactions

        for record in records_str.split(";"):
            record = record.strip()
            if not record:
                continue

            parts = record.split(":")
            if len(parts) >= 3:
                try:
                    date_str = parts[0]
                    trans_type = parts[1]
                    amount = float(parts[2])
                    transactions.append({"date": date_str, "type": trans_type, "amount": amount})
                except (ValueError, IndexError):
                    continue

        return transactions

    @classmethod
    def _calculate_cashflows(cls, transactions: List[dict], current_amount: Decimal) -> List[float]:
        """
        计算现金流
        Args:
            transactions: 交易记录列表
            current_amount: 当前金额
        Returns:
            现金流列表
        """
        cashflows = []

        for trans in transactions:
            if trans["type"] == "buy":
                # 买入是负现金流（投入）
                cashflows.append(-trans["amount"])
            elif trans["type"] == "sell":
                # 卖出是正现金流（收回）
                cashflows.append(trans["amount"])

        # 最后添加当前金额作为最终现金流
        if current_amount:
            cashflows.append(float(current_amount))

        return cashflows

    @classmethod
    def parse_csv_file(
        cls, csv_path: Path, reference_date: date | None = None
    ) -> List[InvestmentProduct]:
        """
        解析 CSV 文件
        Args:
            csv_path: CSV 文件路径
            reference_date: 参考日期（用于计算投资天数），默认为当前日期
        Returns:
            投资产品列表
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV 文件不存在: {csv_path}")

        if reference_date is None:
            reference_date = datetime.now().date()

        products = []

        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                # 使用 csv.DictReader 读取
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):  # 从第2行开始计数
                    product = cls.parse_row(row, reference_date)
                    if product:
                        products.append(product)
                    # 不再打印警告，因为空行和小计行是正常情况

        except Exception as e:
            from ..core.exceptions import DataLoadError

            raise DataLoadError(f"读取 CSV 文件失败: {e}", file_path=str(csv_path))

        return products

    @classmethod
    def load_data(cls, data_path: Path | None = None) -> List[InvestmentProduct]:
        """
        加载投资数据
        Args:
            data_path: 数据目录路径，如果为 None 则使用配置中的数据路径
        Returns:
            投资产品列表
        """
        if data_path is None:
            data_path = config.data_path

        if config.is_real_mode:
            data_dir = config.project_root / "data" / "real"
            if data_dir.exists():
                dirs = [
                    d
                    for d in data_dir.iterdir()
                    if d.is_dir()
                    and (d.name.startswith("money_csv_") or d.name.startswith("money_"))
                ]

                if dirs:
                    import re
                    from datetime import datetime

                    def extract_date(d: Path) -> int:
                        match = re.search(r"(\d{8})", d.name)
                        return int(match.group(1)) if match else 0

                    dirs.sort(key=extract_date, reverse=True)

                    today_suffix = int(datetime.now().strftime("%Y%m%d"))
                    target_dir = None

                    for d in dirs:
                        dir_date = extract_date(d)
                        if dir_date <= today_suffix:
                            target_dir = d
                            break

                    if target_dir is None:
                        target_dir = dirs[0]

                    print(f"使用数据目录: {target_dir.name}")

                    usd_rate, hkd_rate = cls.get_exchange_rates(target_dir)
                    if usd_rate != float(config.default_usd_rate):
                        config.default_usd_rate = usd_rate
                    if hkd_rate != float(config.default_hkd_rate):
                        config.default_hkd_rate = hkd_rate

                    csv_files = list(target_dir.glob("投资产品-表格 1.csv"))
                    if not csv_files:
                        csv_files = list(target_dir.glob("投资产品.csv"))
                    if not csv_files:
                        csv_files = list(target_dir.glob("*工作表 1*.csv"))
                    if not csv_files:
                        csv_files = list(target_dir.glob("*工作表*1*.csv"))
                    if not csv_files:
                        csv_files = list(target_dir.glob("*.csv"))

                    if csv_files:
                        csv_path = csv_files[0]
                        try:
                            products = cls.parse_csv_file(csv_path)
                            # 提取数据目录日期作为参考日期
                            dir_date_str = target_dir.name.split("_")[-1]
                            reference_date = datetime.strptime(dir_date_str, "%Y%m%d")
                            # 对有交易记录的产品使用简单年化收益率计算
                            products = cls._calculate_irr_for_products(products, reference_date)
                            print(f"✅ 成功加载 {len(products)} 个投资产品")
                            print(f"    美元汇率: {usd_rate}, 港元汇率: {hkd_rate}")
                            return products
                        except Exception as e:
                            print(f"❌ 加载数据失败: {e}")
                            raise

                    print(f"❌ 未找到 CSV 文件")
                    return []

        # 如果传入的是目录，查找投资产品的 CSV 文件
        if data_path.is_dir():
            # 尝试多种 glob 模式，优先匹配新文件名
            patterns = [
                "投资产品-表格 1.csv",
                "投资产品.csv",
                "*工作表 1*.csv",
                "*工作表*1*.csv",
                "*Sheet1*.csv",
                "*.csv",
            ]

            csv_files = []
            for pattern in patterns:
                csv_files = list(data_path.glob(pattern))
                if csv_files:
                    break

            if not csv_files:
                raise FileNotFoundError(f"数据目录中没有找到 CSV 文件: {data_path}")

            # 使用第一个找到的 CSV 文件
            csv_path = csv_files[0]
            print(f"使用数据文件: {csv_path.name}")
        else:
            csv_path = data_path

        return cls.parse_csv_file(csv_path)

    @classmethod
    def load_data_from_dir(cls, data_dir: Path) -> List[InvestmentProduct]:
        """
        从指定目录加载投资数据

        Args:
            data_dir: 数据目录路径

        Returns:
            投资产品列表
        """
        if not data_dir.exists():
            raise FileNotFoundError(f"数据目录不存在: {data_dir}")

        # 获取汇率
        usd_rate, hkd_rate = cls.get_exchange_rates(data_dir)

        # 查找 CSV 文件
        patterns = [
            "投资产品-表格 1.csv",
            "投资产品.csv",
            "*工作表 1*.csv",
            "*工作表*1*.csv",
            "*Sheet1*.csv",
            "*.csv",
        ]

        csv_files = []
        for pattern in patterns:
            csv_files = list(data_dir.glob(pattern))
            if csv_files:
                break

        if not csv_files:
            raise FileNotFoundError(f"数据目录中没有找到 CSV 文件: {data_dir}")

        # 使用第一个找到的 CSV 文件
        csv_path = csv_files[0]

        # 解析 CSV 文件
        products = cls.parse_csv_file(csv_path)

        # 提取数据目录日期作为参考日期
        dir_date_str = data_dir.name.split("_")[-1]
        try:
            from datetime import datetime

            reference_date = datetime.strptime(dir_date_str, "%Y%m%d")
            products = cls._calculate_irr_for_products(products, reference_date)
        except ValueError:
            pass

        return products
