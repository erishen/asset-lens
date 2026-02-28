"""
汇率历史数据解析器
解析工作表 2-表格 1.csv 文件
"""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List

from ..data.models import ExchangeRateHistory


class ExchangeRateParser:
    """汇率历史数据解析器"""
    
    @staticmethod
    def parse_decimal(value: str) -> Decimal | None:
        """解析 Decimal 值"""
        if not value or value.strip() == "":
            return None
        try:
            cleaned = value.replace(",", "").strip()
            return Decimal(cleaned)
        except:
            return None
    
    @staticmethod
    def parse_date(value: str) -> datetime | None:
        """解析日期值"""
        if not value or value.strip() == "":
            return None
        
        date_formats = [
            "%Y.%m.%d",
            "%Y.%m.%d %H:%M:%S",
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    @classmethod
    def parse_row(cls, row: dict) -> ExchangeRateHistory | None:
        """解析单行数据"""
        try:
            rate_date = cls.parse_date(row.get("日期", ""))
            if not rate_date:
                return None
            
            return ExchangeRateHistory(
                rate_date=rate_date,
                usd_rate=cls.parse_decimal(row.get("美元汇率", "")),
                hkd_rate=cls.parse_decimal(row.get("港元汇率", "")),
            )
        except Exception as e:
            print(f"解析汇率历史行数据时出错: {e}, 行数据: {row}")
            return None
    
    @classmethod
    def parse_csv_file(cls, csv_path: Path) -> List[ExchangeRateHistory]:
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
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    rate = cls.parse_row(row)
                    if rate:
                        rates.append(rate)
                    else:
                        print(f"警告: 第 {row_num} 行汇率历史数据解析失败")
        
        except Exception as e:
            raise Exception(f"读取汇率历史 CSV 文件失败: {e}")
        
        return rates
