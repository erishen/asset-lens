"""
AkShare Data Provider implementation.
AkShare 数据源实现
"""

from typing import Any, Dict, List, Optional

from . import DataType, ProviderType
from .base import BaseProvider


class AkshareProvider(BaseProvider):
    """
    AkShare 数据源
    
    使用 AkShare 获取 A 股、基金、期货等数据
    """
    
    def __init__(self, priority: int = 10) -> None:
        super().__init__(
            name="akshare",
            provider_type=ProviderType.AKSHARE,
            priority=priority,
            supported_data_types=[
                DataType.STOCK_CN,
                DataType.FUND_CN,
                DataType.FUND_ETF,
                DataType.FUTURES_CN,
                DataType.INDEX,
            ],
        )
        self._akshare = None
    
    @property
    def akshare(self):
        """延迟加载 AkShare"""
        if self._akshare is None:
            try:
                import akshare as ak
                self._akshare = ak
            except ImportError:
                pass
        return self._akshare
    
    def _check_availability(self) -> bool:
        """检查 AkShare 是否可用"""
        return self.akshare is not None
    
    def fetch(
        self,
        data_type: DataType,
        symbol: str,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """获取数据"""
        if not self.is_available():
            return None
        
        try:
            if data_type == DataType.STOCK_CN:
                return self._fetch_stock_quote(symbol)
            elif data_type == DataType.FUND_CN:
                return self._fetch_fund_quote(symbol)
            elif data_type == DataType.FUTURES_CN:
                return self._fetch_futures_quote(symbol)
            elif data_type == DataType.INDEX:
                return self._fetch_index_quote(symbol)
            else:
                return None
        except Exception:
            return None
    
    def _fetch_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取 A 股行情"""
        try:
            df = self.akshare.stock_zh_a_spot_em()
            row = df[df["代码"] == symbol]
            if row.empty:
                return None
            
            row = row.iloc[0]
            return {
                "symbol": symbol,
                "name": row.get("名称", ""),
                "current_price": float(row.get("最新价", 0)),
                "change": float(row.get("涨跌额", 0)),
                "change_percent": float(row.get("涨跌幅", 0)),
                "volume": int(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "open": float(row.get("今开", 0)),
                "prev_close": float(row.get("昨收", 0)),
                "source": "akshare",
            }
        except Exception:
            return None
    
    def _fetch_fund_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取基金净值"""
        try:
            df = self.akshare.fund_open_fund_info_em(fund=symbol, indicator="单位净值走势")
            if df is None or df.empty:
                return None
            
            latest = df.iloc[-1]
            return {
                "symbol": symbol,
                "nav": float(latest.get("单位净值", 0)),
                "date": str(latest.get("净值日期", "")),
                "source": "akshare",
            }
        except Exception:
            return None
    
    def _fetch_futures_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取期货行情"""
        try:
            df = self.akshare.futures_main_sina()
            if df is None or df.empty:
                return None
            
            row = df[df["symbol"] == symbol]
            if row.empty:
                return None
            
            row = row.iloc[0]
            return {
                "symbol": symbol,
                "current_price": float(row.get("最新价", 0)),
                "change": float(row.get("涨跌额", 0)),
                "change_percent": float(row.get("涨跌幅", 0)),
                "volume": int(row.get("成交量", 0)),
                "source": "akshare",
            }
        except Exception:
            return None
    
    def _fetch_index_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取指数行情"""
        try:
            df = self.akshare.stock_zh_index_spot_em()
            if df is None or df.empty:
                return None
            
            row = df[df["代码"] == symbol]
            if row.empty:
                return None
            
            row = row.iloc[0]
            return {
                "symbol": symbol,
                "name": row.get("名称", ""),
                "current_price": float(row.get("最新价", 0)),
                "change": float(row.get("涨跌额", 0)),
                "change_percent": float(row.get("涨跌幅", 0)),
                "source": "akshare",
            }
        except Exception:
            return None


akshare_provider = AkshareProvider()
