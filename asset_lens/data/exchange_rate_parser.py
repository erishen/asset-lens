import logging
logger = logging.getLogger(__name__)

"""
汇率历史数据解析器
解析资产汇总.csv 文件（原备份-表格 1.csv）
"""

import csv
import logging
from pathlib import Path

from ..data.models import ExchangeRateHistory
from .parser_utils import parse_date, parse_decimal


class ExchangeRateParser:
    """汇率历史数据解析器"""

    @classmethod
    def parse_row(cls, row: dict) -> ExchangeRateHistory | None:
        """解析单行数据"""
        try:
            rate_date = parse_date(row.get("日期", ""))
            if not rate_date:
                return None

            usd_rate = parse_decimal(row.get("美元汇率", ""))
            hkd_rate = parse_decimal(row.get("港元汇率", ""))

            return ExchangeRateHistory(
                rate_date=rate_date,
                usd_rate=usd_rate,
                hkd_rate=hkd_rate,
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.info(f"解析汇率历史行数据时出错: {e}, 行数据: {row}")
            return None

    @classmethod
    def parse_csv_file(cls, csv_path: Path) -> list[ExchangeRateHistory]:
        """
        解析汇率历史 CSV 文件
        Args:
            csv_path: CSV 文件路径
        Returns:
            汇率历史记录列表
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"汇率历史 CSV 文件不存在: {csv_path}")

        rates = []

        try:
            with open(csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    rate = cls.parse_row(row)
                    if rate:
                        rates.append(rate)
                    else:
                        logger.error(f"警告: 第 {row_num} 行汇率历史数据解析失败")

        except (OSError, ValueError, KeyError) as e:
            raise Exception(f"读取汇率历史 CSV 文件失败: {e}") from e

        return rates
