"""
卖出记录数据解析器
解析卖出记录-表格 1.csv 文件
"""

from pathlib import Path

from ..data.models import RiskLevel, SellRecord
from .parser_utils import SELL_RECORD_FIELDS, parse_date, parse_decimal


class SellRecordParser:
    """卖出记录数据解析器"""

    @staticmethod
    def parse_boolean(value: str) -> bool:
        """解析布尔值"""
        if not value or value.strip() == "":
            return False
        return value.strip() == "是" or value.strip().lower() in ["true", "yes", "1"]

    @staticmethod
    def parse_int(value: str) -> int | None:
        """解析整数值，支持 '328天' 或 '328' 格式"""
        if not value or value.strip() == "":
            return None
        try:
            value = value.strip()
            if value.endswith("天"):
                value = value[:-1]
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def parse_risk_level(value: str) -> RiskLevel:
        """解析风险等级"""
        if not value or value.strip() == "":
            return RiskLevel.MEDIUM

        value_lower = value.strip().lower()

        if "低" in value_lower and "中" not in value_lower:
            return RiskLevel.LOW
        elif "中低" in value_lower:
            return RiskLevel.MEDIUM_LOW
        elif "中高" in value_lower:
            return RiskLevel.MEDIUM_HIGH
        elif "高" in value_lower:
            return RiskLevel.HIGH
        elif "中" in value_lower:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.MEDIUM

    @classmethod
    def parse_row(cls, row: dict) -> SellRecord | None:
        """解析单行数据"""
        try:
            sell_date_str = row.get("结束日期", "")

            if not sell_date_str or not sell_date_str.strip():
                return None

            sell_date = parse_date(sell_date_str)

            if not sell_date:
                return None

            return SellRecord(
                sell_date=sell_date,
                name=row.get("名称", "").strip(),
                risk_level=cls.parse_risk_level(row.get("风险", "")),
                maturity_date=parse_date(row.get("到期时间", "")),
                is_rolling=cls.parse_boolean(row.get("滚动", "")),
                start_date=parse_date(row.get("开始日期", "")),
                initial_amount=parse_decimal(row.get("初始金额", "")),
                profit_amount=parse_decimal(row.get("收益金额", "")),
                return_rate=parse_decimal(row.get("年化收益", "")) or parse_decimal(row.get("收益率", "")),
                end_date=sell_date,
                to_account_date=parse_date(row.get("到账日期", "")),
                end_to_account_interval=cls.parse_int(row.get("结束到账间隔", "")),
                investment_days=cls.parse_int(row.get("投资天数", "")),
                annual_return=parse_decimal(row.get("年化收益", "")),
                compound_return=parse_decimal(row.get("复利年化", "")),
                interest_payment=parse_decimal(row.get("利息发放", "")),
                transaction_records=row.get("交易记录", "").strip(),
                default_order=cls.parse_int(row.get("默认顺序", "")),
            )
        except Exception as e:
            print(f"解析卖出记录行数据时出错: {e}, 行数据: {row}")
            return None

    @classmethod
    def parse_csv_file(cls, csv_path: Path) -> list[SellRecord]:
        """
        解析卖出记录 CSV 文件
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"卖出记录 CSV 文件不存在: {csv_path}")

        records: list[SellRecord] = []

        try:
            with open(csv_path, encoding="utf-8-sig") as f:
                lines = f.readlines()

                if not lines:
                    return records

                fieldnames = SELL_RECORD_FIELDS

                for line in lines[1:]:
                    values = line.strip().split(",")

                    if len(values) < 2 or not values[1].strip():
                        continue

                    if len(values) >= len(fieldnames):
                        row = dict(zip(fieldnames, values, strict=False))
                        record = cls.parse_row(row)
                        if record:
                            records.append(record)

        except Exception as e:
            from ..core.exceptions import DataLoadError

            raise DataLoadError(f"读取卖出记录 CSV 文件失败: {e}", file_path=str(csv_path)) from e

        return records

    @classmethod
    def load_sell_records(cls) -> list[SellRecord]:
        """
        加载卖出记录数据
        从配置的数据路径中查找卖出记录文件
        """
        from ..config import config

        data_path = config.data_path

        sell_record_files = list(data_path.rglob("卖出记录*.csv"))

        if not sell_record_files:
            return []

        sell_record_files.sort(reverse=True)
        latest_file = sell_record_files[0]

        return cls.parse_csv_file(latest_file)
