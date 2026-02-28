"""
Market index data models for asset-lens.
市场指数数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class IndexPerformance:
    """指数周期表现"""
    
    weekly_change: Decimal = Decimal("0")  # 周涨跌幅
    weekly_high: Decimal = Decimal("0")  # 周最高
    weekly_low: Decimal = Decimal("0")  # 周最低
    weekly_amplitude: Decimal = Decimal("0")  # 周振幅
    monthly_change: Optional[Decimal] = None  # 月涨跌幅
    ytd_change: Optional[Decimal] = None  # 年初至今涨跌幅
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "周涨跌幅": str(self.weekly_change),
            "周最高": str(self.weekly_high),
            "周最低": str(self.weekly_low),
            "周振幅": str(self.weekly_amplitude),
        }
        if self.monthly_change is not None:
            result["月涨跌幅"] = str(self.monthly_change)
        if self.ytd_change is not None:
            result["年初至今涨跌幅"] = str(self.ytd_change)
        return result


@dataclass
class IndexHistory:
    """指数历史走势"""
    
    date: str  # 日期
    open: Decimal  # 开盘价
    close: Decimal  # 收盘价
    high: Decimal  # 最高价
    low: Decimal  # 最低价
    volume: Optional[int] = None  # 成交量
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "日期": self.date,
            "开盘": str(self.open),
            "收盘": str(self.close),
            "最高": str(self.high),
            "最低": str(self.low),
        }
        if self.volume is not None:
            result["成交量"] = self.volume
        return result


@dataclass
class MarketIndex:
    """市场指数数据"""
    
    code: str  # 代码
    name: str  # 名称
    latest_price: Decimal  # 最新价
    change_amount: Decimal = Decimal("0")  # 涨跌额
    change_percent: Decimal = Decimal("0")  # 涨跌幅
    prev_close: Decimal = Decimal("0")  # 昨收
    open: Decimal = Decimal("0")  # 今开
    high: Decimal = Decimal("0")  # 最高
    low: Decimal = Decimal("0")  # 最低
    volume: Optional[int] = None  # 成交量
    amount: Optional[Decimal] = None  # 成交额
    performance: Optional[IndexPerformance] = None  # 周期表现
    history: List[IndexHistory] = field(default_factory=list)  # 历史走势
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "代码": self.code,
            "名称": self.name,
            "最新价": str(self.latest_price),
            "涨跌额": str(self.change_amount),
            "涨跌幅": str(self.change_percent),
            "昨收": str(self.prev_close),
            "今开": str(self.open),
            "最高": str(self.high),
            "最低": str(self.low),
        }
        if self.volume is not None:
            result["成交量"] = self.volume
        if self.amount is not None:
            result["成交额"] = str(self.amount)
        if self.performance:
            result["周期表现"] = self.performance.to_dict()
        if self.history:
            result["历史走势"] = [h.to_dict() for h in self.history]
        return result


@dataclass
class MarketIndexCache:
    """市场指数缓存数据"""
    
    update_time: str  # 更新时间
    data_date: str  # 数据日期
    is_trading_time: bool = False  # 是否交易时间
    is_trading_day: bool = False  # 是否交易日
    next_trading_day: Optional[str] = None  # 下一个交易日
    indexes: Dict[str, MarketIndex] = field(default_factory=dict)  # 指数数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "更新时间": self.update_time,
            "数据日期": self.data_date,
            "是否交易时间": self.is_trading_time,
            "是否交易日": self.is_trading_day,
        }
        if self.next_trading_day:
            result["下一个交易日"] = self.next_trading_day
        if self.indexes:
            result["指数数据"] = {
                name: index.to_dict() 
                for name, index in self.indexes.items()
            }
        return result
