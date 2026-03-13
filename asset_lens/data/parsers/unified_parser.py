"""
Unified Data Parser - 统一数据解析类

将分散在多个模块的数据解析函数统一到一个类中。
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """解析结果"""
    success: bool
    value: Any = None
    error: Optional[str] = None


class DateParser:
    """日期解析器"""
    
    DATE_FORMATS = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y年%m月%d日",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y%m%d",
    ]
    
    @classmethod
    def parse(cls, date_str: Optional[str]) -> ParseResult:
        """解析日期字符串"""
        if not date_str:
            return ParseResult(success=False, error="Empty date string")
        
        date_str = str(date_str).strip()
        
        for fmt in cls.DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return ParseResult(success=True, value=parsed.date())
            except ValueError:
                continue
        
        return ParseResult(success=False, error=f"Unknown date format: {date_str}")
    
    @classmethod
    def parse_range(cls, start_str: str, end_str: str) -> ParseResult:
        """解析日期范围"""
        start_result = cls.parse(start_str)
        end_result = cls.parse(end_str)
        
        if not start_result.success:
            return start_result
        if not end_result.success:
            return end_result
        
        return ParseResult(
            success=True,
            value=(start_result.value, end_result.value)
        )
    
    @classmethod
    def format_date(cls, dt: Union[datetime, date], fmt: str = "%Y-%m-%d") -> str:
        """格式化日期"""
        if isinstance(dt, datetime):
            return dt.strftime(fmt)
        elif isinstance(dt, date):
            return dt.strftime(fmt)
        return str(dt)


class InvestmentTypeParser:
    """投资类型解析器"""
    
    TYPE_MAPPING = {
        "股票": "stock",
        "基金": "fund",
        "债券": "bond",
        "货币": "monetary",
        "理财": "wealth",
        "黄金": "gold",
        "加密货币": "crypto",
        "期货": "futures",
        "期权": "option",
        "ETF": "etf",
        "公募固收": "public_fixed_income",
        "高端理财": "high_end_wealth",
        "特别国债": "special_treasury_bond",
        "私募": "private_equity",
        "信托": "trust",
        "其他": "other",
    }
    
    @classmethod
    def parse(cls, type_str: Optional[str]) -> ParseResult:
        """解析投资类型"""
        if not type_str:
            return ParseResult(success=False, error="Empty type string")
        
        type_str = str(type_str).strip()
        
        # 直接匹配
        if type_str in cls.TYPE_MAPPING:
            return ParseResult(success=True, value=cls.TYPE_MAPPING[type_str])
        
        # 模糊匹配
        for cn_type, en_type in cls.TYPE_MAPPING.items():
            if cn_type in type_str or type_str in cn_type:
                return ParseResult(success=True, value=en_type)
        
        return ParseResult(success=True, value="other")
    
    @classmethod
    def get_display_name(cls, type_code: str) -> str:
        """获取显示名称"""
        reverse_mapping = {v: k for k, v in cls.TYPE_MAPPING.items()}
        return reverse_mapping.get(type_code, type_code)


class DataParser:
    """统一数据解析器"""
    
    def __init__(self):
        self.date_parser = DateParser()
        self.type_parser = InvestmentTypeParser()
    
    def parse_csv_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """解析 CSV 行数据"""
        result = {}
        
        # 解析日期
        if "date" in row or "日期" in row:
            date_str = row.get("date") or row.get("日期")
            parse_result = self.date_parser.parse(date_str)
            if parse_result.success:
                result["date"] = parse_result.value
        
        # 解析投资类型
        if "type" in row or "类型" in row or "investment_type" in row:
            type_str = row.get("type") or row.get("类型") or row.get("investment_type")
            parse_result = self.type_parser.parse(type_str)
            if parse_result.success:
                result["investment_type"] = parse_result.value
        
        # 解析金额
        for field in ["amount", "金额", "current_amount", "initial_amount"]:
            if field in row:
                try:
                    value = row[field]
                    if isinstance(value, str):
                        value = value.replace(",", "").replace("¥", "").replace("$", "").replace("¥", "")
                    result[field] = float(value) if value else 0.0
                except (ValueError, TypeError):
                    result[field] = 0.0
        
        # 复制其他字段
        for key, value in row.items():
            if key not in result:
                result[key] = value
        
        return result
    
    def parse_transaction(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """解析交易记录"""
        return self.parse_csv_row(row)
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """安全转换为浮点数"""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                value = value.replace(",", "").replace("¥", "").replace("$", "").replace("¥", "")
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """安全转换为整数"""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                value = value.replace(",", "")
            return int(float(value))
        except (ValueError, TypeError):
            return default


data_parser = DataParser()
