"""
Market data fetchers for different sources.
市场数据获取器 - 不同数据源的获取方法
"""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class DomesticIndexFetcher:
    """国内指数数据获取器"""

    def __init__(self, akshare):
        self.akshare = akshare

    def fetch_from_akshare_spot(self, index_code: str) -> dict[str, Any] | None:
        """从 AkShare 获取实时指数数据"""
        try:
            df = self.akshare.stock_zh_index_spot_em()
            if df is None or df.empty:
                return None

            code_map = {
                "sh000001": "上证指数",
                "sh000300": "沪深300",
                "sh000016": "上证50",
                "sh000905": "中证500",
                "sh000852": "中证1000",
                "sz399001": "深证成指",
                "sz399006": "创业板指",
                "sz399005": "中小板指",
            }

            target_name = code_map.get(index_code)
            if not target_name:
                return None

            row = df[df["名称"] == target_name]
            if row.empty:
                return None

            row = row.iloc[0]

            return {
                "code": index_code,
                "name": target_name,
                "price": float(row.get("最新价", 0)),
                "change": float(row.get("涨跌额", 0)),
                "change_pct": float(row.get("涨跌幅", 0)),
                "volume": float(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "source": "akshare_spot",
            }
        except Exception as e:
            logger.warning(f"AkShare spot fetch failed: {e}")
            return None

    def fetch_from_sina(self, index_code: str) -> dict[str, Any] | None:
        """从新浪财经获取指数数据"""
        try:
            sina_codes = {
                "sh000001": "s_sh000001",
                "sh000300": "s_sh000300",
                "sh000016": "s_sh000016",
                "sh000905": "s_sh000905",
                "sh000852": "s_sh000852",
                "sz399001": "s_sz399001",
                "sz399006": "s_sz399006",
            }

            sina_code = sina_codes.get(index_code)
            if not sina_code:
                return None

            url = f"http://hq.sinajs.cn/list={sina_code}"
            headers = {"Referer": "http://finance.sina.com.cn"}

            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                return None

            data = response.text
            if not data or 'var hq_str_' not in data:
                return None

            parts = data.split('"')[1].split(",")
            if len(parts) < 4:
                return None

            name = parts[0]
            price = float(parts[1])
            change = float(parts[2])
            change_pct = float(parts[3])

            return {
                "code": index_code,
                "name": name,
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "source": "sina",
            }
        except Exception as e:
            logger.warning(f"Sina fetch failed: {e}")
            return None

    def fetch_from_tencent(self, index_code: str) -> dict[str, Any] | None:
        """从腾讯财经获取指数数据"""
        try:
            tencent_codes = {
                "sh000001": "sh000001",
                "sh000300": "sh000300",
                "sh000016": "sh000016",
                "sh000905": "sh000905",
                "sh000852": "sh000852",
                "sz399001": "sz399001",
                "sz399006": "sz399006",
            }

            tencent_code = tencent_codes.get(index_code)
            if not tencent_code:
                return None

            url = f"http://qt.gtimg.cn/q={tencent_code}"
            headers = {"Referer": "http://gu.qq.com"}

            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                return None

            data = response.text
            if "~" not in data:
                return None

            parts = data.split("~")
            if len(parts) < 35:
                return None

            name = parts[1]
            price = float(parts[3])
            prev_close = float(parts[4])

            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close > 0 else 0

            return {
                "code": index_code,
                "name": name,
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "volume": float(parts[36]) if parts[36] else 0,
                "amount": float(parts[37]) if parts[37] else 0,
                "source": "tencent",
            }
        except Exception as e:
            logger.warning(f"Tencent fetch failed: {e}")
            return None


class ForeignIndexFetcher:
    """国外指数数据获取器"""

    def __init__(self, akshare):
        self.akshare = akshare

    def fetch_from_akshare_global(self, symbol: str) -> dict[str, Any] | None:
        """从 AkShare 获取全球指数数据"""
        try:
            symbol_map = {
                "DJI": "道琼斯",
                "IXIC": "纳斯达克",
                "SPX": "标普500",
                "FTSE": "富时100",
                "N225": "日经225",
                "HSI": "恒生指数",
            }

            target_name = symbol_map.get(symbol)
            if not target_name:
                return None

            df = self.akshare.index_global_em()
            if df is None or df.empty:
                return None

            row = df[df["名称"] == target_name]
            if row.empty:
                return None

            row = row.iloc[0]

            return {
                "code": symbol,
                "name": target_name,
                "price": float(row.get("最新价", 0)),
                "change": float(row.get("涨跌额", 0)),
                "change_pct": float(row.get("涨跌幅", 0)),
                "source": "akshare_global",
            }
        except Exception as e:
            logger.warning(f"AkShare global fetch failed: {e}")
            return None

    def fetch_from_eastmoney(self, symbol: str) -> dict[str, Any] | None:
        """从东方财富获取全球指数数据"""
        try:
            symbol_map = {
                "DJI": "100.DJI",
                "IXIC": "100.NDX",
                "SPX": "100.SPX",
                "FTSE": "100.FTSE",
                "N225": "100.N225",
                "HSI": "100.HSI",
            }

            em_code = symbol_map.get(symbol)
            if not em_code:
                return None

            url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={em_code}&fields=f43,f44,f45,f46,f47,f48"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                return None

            data = response.json()
            if not data or "data" not in data:
                return None

            d = data["data"]
            if not d:
                return None

            price = float(d.get("f43", 0)) / 100 if d.get("f43") else 0
            change = float(d.get("f44", 0)) / 100 if d.get("f44") else 0
            change_pct = float(d.get("f45", 0)) / 100 if d.get("f45") else 0

            return {
                "code": symbol,
                "name": symbol,
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "source": "eastmoney",
            }
        except Exception as e:
            logger.warning(f"Eastmoney fetch failed: {e}")
            return None
