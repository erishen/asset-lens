"""
Stock quote parsers for asset-lens.
股票行情数据解析模块
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SinaQuoteParser:
    """新浪行情解析器"""

    @staticmethod
    def parse(df, stock_code: str) -> dict[str, Any] | None:
        """解析新浪A股行情数据"""
        try:
            if df is None or df.empty:
                logger.warning(f"新浪数据为空: {stock_code}")
                return None

            code = stock_code[2:]
            row = df[df["代码"] == code]

            if row.empty:
                logger.warning(f"新浪未找到股票: {stock_code}")
                return None

            row = row.iloc[0]

            current_price = float(row.get("最新价", 0))
            prev_close = float(row.get("昨收", 0))
            open_price = float(row.get("今开", 0))
            high = float(row.get("最高", 0))
            low = float(row.get("最低", 0))
            volume = float(row.get("成交量", 0))
            amount = float(row.get("成交额", 0))

            change_amount = current_price - prev_close if prev_close > 0 else 0
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            return {
                "code": stock_code,
                "name": row.get("名称", ""),
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": int(volume),
                "amount": amount,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "sina",
            }
        except Exception as e:
            logger.error(f"解析新浪数据失败: {e}")
            return None


class BaostockQuoteParser:
    """Baostock行情解析器"""

    @staticmethod
    def parse(rs, stock_code: str) -> dict[str, Any] | None:
        """解析Baostock行情数据"""
        try:
            if rs.error_code != "0":
                logger.warning(f"Baostock查询失败: {rs.error_msg}")
                return None

            data_list = []
            while rs.error_code == "0" and rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                logger.warning(f"Baostock数据为空: {stock_code}")
                return None

            row = data_list[0]
            if len(row) < 6:
                return None

            date = row[0]
            row[1]
            name = row[2]
            open_price = float(row[5]) if row[5] else 0
            high = float(row[6]) if row[6] else 0
            low = float(row[7]) if row[7] else 0
            close = float(row[8]) if row[8] else 0
            volume = float(row[9]) if row[9] else 0
            amount = float(row[10]) if row[10] else 0

            prev_close = close
            change_amount = 0
            change_percent = 0

            return {
                "code": stock_code,
                "name": name,
                "date": date,
                "current_price": close,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": int(volume),
                "amount": amount,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "baostock",
            }
        except Exception as e:
            logger.error(f"解析Baostock数据失败: {e}")
            return None


class TencentQuoteParser:
    """腾讯行情解析器"""

    @staticmethod
    def parse(data: str, stock_code: str) -> dict[str, Any] | None:
        """解析腾讯行情数据"""
        try:
            if "~" not in data:
                return None

            parts = data.split("~")
            if len(parts) < 50:
                return None

            parts[0].split("=")[0].replace("v_", "")
            name = parts[1] if len(parts) > 1 else ""
            current_price = float(parts[3]) if parts[3] else 0
            prev_close = float(parts[4]) if parts[4] else 0
            open_price = float(parts[5]) if parts[5] else 0
            volume = float(parts[36]) if parts[36] else 0
            amount = float(parts[37]) if parts[37] else 0

            change_amount = current_price - prev_close
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            high = float(parts[33]) if len(parts) > 33 and parts[33] else current_price
            low = float(parts[34]) if len(parts) > 34 and parts[34] else current_price

            return {
                "code": stock_code,
                "name": name,
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": int(volume),
                "amount": amount,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "tencent",
            }
        except Exception as e:
            logger.error(f"解析腾讯数据失败: {e}")
            return None


class JoinquantQuoteParser:
    """JoinQuant行情解析器"""

    @staticmethod
    def parse(df, stock_code: str) -> dict[str, Any] | None:
        """解析JoinQuant行情数据"""
        try:
            if df is None or df.empty:
                return None

            row = df.iloc[0]

            close = float(row.get("close", 0))
            open_price = float(row.get("open", 0))
            high = float(row.get("high", 0))
            low = float(row.get("low", 0))
            volume = float(row.get("volume", 0))
            amount = float(row.get("amount", 0)) if "amount" in row else volume * close
            prev_close = float(row.get("pre_close", close))

            change_amount = close - prev_close
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            return {
                "code": stock_code,
                "name": row.get("name", stock_code),
                "current_price": close,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": int(volume),
                "amount": amount,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "joinquant",
            }
        except Exception as e:
            logger.error(f"解析JoinQuant数据失败: {e}")
            return None
