"""
卖出记录数据解析器
解析卖出记录-表格 1.csv 文件
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List

from ..data.models import SellRecord, RiskLevel


class SellRecordParser:
    """卖出记录数据解析器"""
    
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
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%Y.%m.%d",
            "%Y.%m.%d %H:%M:%S",
            "%Y%m%d",
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
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
            
            sell_date = cls.parse_date(sell_date_str)
            
            if not sell_date:
                return None
            
            return SellRecord(
                sell_date=sell_date,
                name=row.get("名称", "").strip(),
                risk_level=cls.parse_risk_level(row.get("风险", "")),
                maturity_date=cls.parse_date(row.get("到期时间", "")),
                is_rolling=cls.parse_boolean(row.get("滚动", "")),
                start_date=cls.parse_date(row.get("开始日期", "")),
                initial_amount=cls.parse_decimal(row.get("初始金额", "")),
                profit_amount=cls.parse_decimal(row.get("收益金额", "")),
                return_rate=cls.parse_decimal(row.get("收益率", "")),
                end_date=sell_date,
                to_account_date=cls.parse_date(row.get("到账日期", "")),
                end_to_account_interval=cls.parse_int(row.get("结束到账间隔", "")),
                investment_days=cls.parse_int(row.get("投资天数", "")),
                annual_return=cls.parse_decimal(row.get("年化收益", "")),
                compound_return=cls.parse_decimal(row.get("复利年化", "")),
                interest_payment=cls.parse_decimal(row.get("利息发放", "")),
                transaction_records=row.get("交易记录", "").strip(),
                default_order=cls.parse_int(row.get("默认顺序", "")),
            )
        except Exception as e:
            print(f"解析卖出记录行数据时出错: {e}, 行数据: {row}")
            return None
    
    @classmethod
    def parse_csv_file(cls, csv_path: Path) -> List[SellRecord]:
        """
        解析卖出记录 CSV 文件
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"卖出记录 CSV 文件不存在: {csv_path}")
        
        records = []
        
        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
                
                if not lines:
                    return records
                
                fieldnames = [
                    "类型", "名称", "风险", "微信", "中金", "支付宝", "富途", "招商", "港招",
                    "交通", "浦发", "建设", "中信", "民生", "工商", "中银", "到期时间",
                    "滚动", "开始日期", "初始金额", "收益金额", "收益率", "结束日期",
                    "到账日期", "结束到账间隔", "投资天数", "年化收益", "复利年化",
                    "利息发放", "交易记录", "默认顺序"
                ]
                
                for line_num, line in enumerate(lines[1:], start=2):
                    values = line.strip().split(",")
                    
                    if len(values) < 2 or not values[1].strip():
                        continue
                    
                    if len(values) >= len(fieldnames):
                        row = dict(zip(fieldnames, values))
                        record = cls.parse_row(row)
                        if record:
                            records.append(record)
        
        except Exception as e:
            from ..core.exceptions import DataLoadError
            raise DataLoadError(
                f"读取卖出记录 CSV 文件失败: {e}",
                file_path=str(csv_path)
            )
        
        return records

    @classmethod
    def load_sell_records(cls) -> List[SellRecord]:
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
