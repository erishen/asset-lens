import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import config
from .fetchers.base import FetcherCacheMixin
from .stock_history_cache import StockHistoryCacheMixin
from .stock_history_sources import StockHistorySourcesMixin

logger = logging.getLogger(__name__)


class StockHistoryFetcher(
    FetcherCacheMixin,
    StockHistorySourcesMixin,
    StockHistoryCacheMixin,
):
    def __init__(self, cache_path: Path | None = None):
        self._init_cache(
            cache_path or config.cache_path,
            default_ttl=86400,
        )
        self._baostock_logged_in = False

    @property
    def tushare(self):
        try:
            import os
            import tempfile

            os.environ["HOME"] = tempfile.gettempdir()
            import tushare as ts

            token = os.environ.get("TUSHARE_TOKEN", "")
            if not token:
                return None

            ts.set_token(token)
            return ts
        except ImportError:
            return None

    @property
    def baostock(self):
        try:
            import baostock as bs

            return bs
        except ImportError:
            return None

    def _baostock_login_with_retry(self) -> bool:
        if self._baostock_logged_in:
            return True

        try:
            import baostock as bs

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    lg = bs.login()
                    if lg.error_code == "0":
                        self._baostock_logged_in = True
                        return True

                    logger.debug(f"Baostock 登录失败 (尝试 {attempt + 1}/{max_retries}): {lg.error_msg}")

                    if "already" in lg.error_msg.lower():
                        self._baostock_logged_in = True
                        return True

                    time.sleep(1)
                except (ConnectionError, RuntimeError, ValueError) as e:
                    logger.debug(f"Baostock 登录异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(1)

            return False
        except ImportError:
            return False

    def baostock_logout(self) -> None:
        try:
            import baostock as bs

            bs.logout()
            self._baostock_logged_in = False
        except (ImportError, RuntimeError):
            pass

    def fetch_history(self, code: str, days: int = 60) -> dict[str, Any] | None:
        cache = self.load_history_cache()
        if code in cache:
            cached_data = cache[code]
            update_time_str = cached_data.get("update_time", "")
            if update_time_str:
                try:
                    update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                    age_hours = (datetime.now() - update_time).total_seconds() / 3600
                    if age_hours < 4:
                        logger.debug(f"使用缓存数据: {code} (缓存时间: {age_hours:.1f}小时前)")
                        return cached_data
                except ValueError as e:
                    logger.debug("股票历史数据解析失败: %s", e)

        sources = [
            ("akshare", self.fetch_history_akshare),
            ("baostock", self.fetch_history_baostock),
            ("tushare", self.fetch_history_tushare),
        ]

        for source_name, fetcher in sources:
            try:
                result = fetcher(code, days)
                if result:
                    result["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logger.debug(f"成功从 {source_name} 获取 {code} 历史数据")
                    return result
            except (ValueError, KeyError, ConnectionError) as e:
                logger.debug(f"{source_name} 获取 {code} 失败: {e}")
                continue

        logger.warning(f"所有数据源获取 {code} 历史数据失败")
        return None

    def fetch_batch_history(
        self,
        codes: list[str],
        days: int = 60,
        batch_size: int = 5,
        delay: float = 0.5,
    ) -> dict[str, dict[str, Any]]:
        results = {}

        for i, code in enumerate(codes):
            if i > 0 and i % batch_size == 0:
                logger.info(f"批量获取进度: {i}/{len(codes)}")
                time.sleep(delay)

            try:
                history = self.fetch_history(code, days)
                if history:
                    results[code] = history
            except (ValueError, KeyError, ConnectionError) as e:
                logger.debug(f"获取 {code} 失败: {e}")

        if results:
            self.save_history_cache(results)

        return results

    def calculate_avg_metrics(self, history: dict[str, Any], days: int = 60) -> dict[str, float]:
        klines = history.get("klines", [])
        if not klines:
            return {"avg_volume": 0, "avg_amount": 0, "avg_turnover_rate": 0, "avg_change_percent": 0}

        recent = klines[-days:] if len(klines) > days else klines

        volumes = [k.get("volume", 0) for k in recent if k.get("volume")]
        amounts = [k.get("amount", 0) for k in recent if k.get("amount")]
        turnovers = [k.get("turnover_rate", 0) for k in recent if k.get("turnover_rate")]
        changes = [k.get("change_percent", 0) for k in recent if k.get("change_percent")]

        return {
            "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
            "avg_amount": sum(amounts) / len(amounts) if amounts else 0,
            "avg_turnover_rate": sum(turnovers) / len(turnovers) if turnovers else 0,
            "avg_change_percent": sum(changes) / len(changes) if changes else 0,
        }

    def get_stocks_with_history(
        self,
        codes: list[str] | None = None,
        max_age_hours: int = 24,
    ) -> list[dict[str, Any]]:
        cache = self.load_history_cache()
        now = datetime.now()

        stocks = []
        for code, data in cache.items():
            if codes and code not in codes:
                continue

            update_time_str = data.get("update_time", "")
            if update_time_str:
                try:
                    update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                    age_hours = (now - update_time).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        continue
                except ValueError:
                    continue

            klines = data.get("klines", [])
            if not klines:
                continue

            latest = klines[-1] if klines else {}
            metrics = self.calculate_avg_metrics(data)

            stocks.append(
                {
                    "code": code,
                    "name": data.get("name", ""),
                    "latest_price": latest.get("close", 0),
                    "change_percent": latest.get("change_percent", 0),
                    "volume": latest.get("volume", 0),
                    "amount": latest.get("amount", 0),
                    "turnover_rate": latest.get("turnover_rate", 0),
                    "avg_volume": metrics["avg_volume"],
                    "avg_amount": metrics["avg_amount"],
                    "avg_turnover_rate": metrics["avg_turnover_rate"],
                    "avg_change_percent": metrics["avg_change_percent"],
                    "source": data.get("source", ""),
                    "update_time": update_time_str,
                }
            )

        return stocks

    def get_stock_realtime_quote(self, code: str) -> dict[str, Any] | None:
        try:
            import requests

            pure_code = code.replace("sh", "").replace("sz", "")
            prefix = "sh" if code.startswith("6") or code.startswith("sh") else "sz"
            full_code = f"{prefix}{pure_code}"

            url = f"http://qt.gtimg.cn/q={full_code}"
            headers = {"Referer": "http://finance.sina.com.cn"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return None

            text = response.text
            if "~" not in text:
                return None

            parts = text.split("~")
            if len(parts) < 40:
                return None

            return {
                "code": code,
                "name": parts[1] if len(parts) > 1 else "",
                "current_price": float(parts[3]) if parts[3] else 0,
                "prev_close": float(parts[4]) if parts[4] else 0,
                "open": float(parts[5]) if parts[5] else 0,
                "volume": int(float(parts[6]) if parts[6] else 0),
                "high": float(parts[33]) if len(parts) > 33 and parts[33] else 0,
                "low": float(parts[34]) if len(parts) > 34 and parts[34] else 0,
                "change_percent": float(parts[32]) if len(parts) > 32 and parts[32] else 0,
                "amount": float(parts[37]) if len(parts) > 37 and parts[37] else 0,
                "turnover_rate": float(parts[38]) if len(parts) > 38 and parts[38] else 0,
            }

        except (ValueError, KeyError, ConnectionError) as e:
            logger.debug(f"获取实时行情失败 {code}: {e}")
            return None


stock_history_fetcher = StockHistoryFetcher()
