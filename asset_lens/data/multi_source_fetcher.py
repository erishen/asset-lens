"""
Multi-source data fetcher for asset-lens.
多数据源管理模块 - 支持多个数据源的备用和切换

功能:
1. 多数据源管理
2. 自动故障切换
3. 数据源优先级
4. 数据源健康检查

支持的数据源:
- AkShare (免费)
- Tushare (需要 Token)
- Baostock (免费)
- EastMoney (免费)
- Sina (免费)
"""

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

from ..config import config

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DataSourceStatus(Enum):
    """数据源状态"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class DataSourceConfig:
    """数据源配置"""

    name: str
    priority: int = 0
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    last_check: str | None = None
    status: DataSourceStatus = DataSourceStatus.HEALTHY
    error_count: int = 0
    success_count: int = 0


class MultiSourceDataFetcher:
    """多数据源管理器"""

    def __init__(self):
        self.cache_path = config.cache_path
        self.config_file = self.cache_path / "data_sources.json"
        self.sources: dict[str, DataSourceConfig] = self._load_configs()
        self._initialize_sources()

    def _load_configs(self) -> dict[str, DataSourceConfig]:
        """加载数据源配置"""
        default_sources = {
            "akshare": DataSourceConfig(
                name="akshare",
                priority=1,
                enabled=True,
            ),
            "eastmoney": DataSourceConfig(
                name="eastmoney",
                priority=2,
                enabled=True,
            ),
            "sina": DataSourceConfig(
                name="sina",
                priority=3,
                enabled=True,
            ),
            "tushare": DataSourceConfig(
                name="tushare",
                priority=4,
                enabled=bool(getattr(config, "tushare_token", None)),
            ),
            "baostock": DataSourceConfig(
                name="baostock",
                priority=5,
                enabled=True,
            ),
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    data = json.load(f)
                for name, cfg in data.get("sources", {}).items():
                    if name in default_sources:
                        default_sources[name].enabled = cfg.get("enabled", True)
                        default_sources[name].priority = cfg.get("priority", default_sources[name].priority)
            except (ValueError, KeyError, TypeError):
                pass

        return default_sources

    def _save_configs(self) -> None:
        """保存数据源配置"""
        data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources": {
                name: {
                    "enabled": cfg.enabled,
                    "priority": cfg.priority,
                    "status": cfg.status.value,
                    "error_count": cfg.error_count,
                    "success_count": cfg.success_count,
                }
                for name, cfg in self.sources.items()
            },
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _initialize_sources(self) -> None:
        """初始化数据源"""
        for name, cfg in self.sources.items():
            if cfg.enabled:
                self._check_source_health(name)

    def _check_source_health(self, source_name: str) -> bool:
        """检查数据源健康状态"""
        try:
            if source_name == "akshare":
                import akshare as ak

                df = ak.stock_zh_a_spot_em()
                return df is not None and not df.empty

            elif source_name == "eastmoney":
                import akshare as ak

                df = ak.stock_zh_a_hist(symbol="000001", period="daily", adjust="qfq")
                return df is not None and not df.empty

            elif source_name == "sina":
                import akshare as ak

                df = ak.stock_zh_a_spot()
                return df is not None and not df.empty

            elif source_name == "tushare":
                if not getattr(config, "tushare_token", None):
                    return False
                import tushare as ts  # pylint: disable=import-error

                ts.set_token(config.tushare_token)
                pro = ts.pro_api()
                df = pro.daily(ts_code="000001.SZ", limit=1)
                return df is not None and not df.empty

            elif source_name == "baostock":
                import baostock as bs

                lg = bs.login()
                if lg.error_code != "0":
                    return False
                bs.logout()
                return True

            return False

        except Exception as e:
            logger.debug(f"忽略异常: {e}")
            return False

    def get_available_sources(self) -> list[str]:
        """获取可用数据源列表（按优先级排序）"""
        available = [
            name for name, cfg in self.sources.items() if cfg.enabled and cfg.status != DataSourceStatus.UNAVAILABLE
        ]
        return sorted(available, key=lambda x: self.sources[x].priority)

    def fetch_with_fallback(
        self,
        fetch_func: Callable[[str], T | None],
        sources: list[str] | None = None,
    ) -> T | None:
        """
        使用故障切换机制获取数据

        Args:
            fetch_func: 获取函数，接受数据源名称作为参数
            sources: 数据源列表，默认使用所有可用数据源

        Returns:
            获取的数据
        """
        if sources is None:
            sources = self.get_available_sources()

        last_error = None

        for source_name in sources:
            cfg = self.sources.get(source_name)
            if not cfg or not cfg.enabled:
                continue

            for attempt in range(cfg.max_retries):
                try:
                    result = fetch_func(source_name)
                    if result is not None:
                        cfg.success_count += 1
                        cfg.status = DataSourceStatus.HEALTHY
                        self._save_configs()
                        return result

                except Exception as e:
                    last_error = e
                    cfg.error_count += 1

                    if cfg.error_count >= 5:
                        cfg.status = DataSourceStatus.DEGRADED
                    if cfg.error_count >= 10:
                        cfg.status = DataSourceStatus.UNAVAILABLE

                    if attempt < cfg.max_retries - 1:
                        time.sleep(cfg.retry_delay)

        if last_error:
            raise last_error

        return None

    def fetch_stock_quote(
        self,
        code: str,
        sources: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """
        获取股票行情（多数据源）

        Args:
            code: 股票代码
            sources: 数据源列表

        Returns:
            行情数据
        """

        def _fetch(source_name: str) -> dict[str, Any] | None:
            if source_name == "akshare":
                return self._fetch_quote_akshare(code)
            elif source_name == "eastmoney":
                return self._fetch_quote_eastmoney(code)
            elif source_name == "sina":
                return self._fetch_quote_sina(code)
            elif source_name == "tushare":
                return self._fetch_quote_tushare(code)
            elif source_name == "baostock":
                return self._fetch_quote_baostock(code)
            return None

        return self.fetch_with_fallback(_fetch, sources)

    def _fetch_quote_akshare(self, code: str) -> dict[str, Any] | None:
        """使用 AkShare 获取行情"""
        try:
            import akshare as ak

            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return None

            stock_code = code[2:] if code.startswith(("sh", "sz")) else code
            row = df[df["代码"] == stock_code]

            if row.empty:
                return None

            row = row.iloc[0]

            return {
                "code": code,
                "name": str(row.get("名称", "")),
                "current_price": float(row.get("最新价", 0)),
                "change_percent": float(row.get("涨跌幅", 0)),
                "change_amount": float(row.get("涨跌额", 0)),
                "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                "amount": float(row.get("成交额", 0)) if row.get("成交额") else 0,
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "open": float(row.get("今开", 0)),
                "prev_close": float(row.get("昨收", 0)),
                "data_source": "akshare",
            }

        except (ValueError, TypeError):
            return None

    def _fetch_quote_eastmoney(self, code: str) -> dict[str, Any] | None:
        """使用 EastMoney 获取行情"""
        try:
            import akshare as ak

            stock_code = code[2:] if code.startswith(("sh", "sz")) else code
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                adjust="qfq",
            )

            if df is None or df.empty:
                return None

            row = df.iloc[-1]

            return {
                "code": code,
                "name": "",
                "current_price": float(row.get("收盘", 0)),
                "change_percent": 0,
                "change_amount": 0,
                "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                "amount": 0,
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "open": float(row.get("开盘", 0)),
                "prev_close": float(df.iloc[-2].get("收盘", 0)) if len(df) > 1 else 0,
                "data_source": "eastmoney",
            }

        except (ValueError, TypeError):
            return None

    def _fetch_quote_sina(self, code: str) -> dict[str, Any] | None:
        """使用 Sina 获取行情"""
        try:
            import akshare as ak

            df = ak.stock_zh_a_spot()
            if df is None or df.empty:
                return None

            stock_code = code[2:] if code.startswith(("sh", "sz")) else code
            row = df[df["code"] == stock_code]

            if row.empty:
                return None

            row = row.iloc[0]

            return {
                "code": code,
                "name": str(row.get("name", "")),
                "current_price": float(row.get("trade", 0)),
                "change_percent": float(row.get("changepercent", 0)),
                "change_amount": float(row.get("change", 0)),
                "volume": float(row.get("volume", 0)) if row.get("volume") else 0,
                "amount": float(row.get("amount", 0)) if row.get("amount") else 0,
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "open": float(row.get("open", 0)),
                "prev_close": float(row.get("settlement", 0)),
                "data_source": "sina",
            }

        except (ValueError, TypeError):
            return None

    def _fetch_quote_tushare(self, code: str) -> dict[str, Any] | None:
        """使用 Tushare 获取行情"""
        if not getattr(config, "tushare_token", None):
            return None

        try:
            import tushare as ts  # pylint: disable=import-error

            ts.set_token(config.tushare_token)
            pro = ts.pro_api()

            ts_code = f"{code[2:]}.{code[:2].upper()}" if code.startswith(("sh", "sz")) else f"{code}.SZ"
            df = pro.daily(ts_code=ts_code, limit=1)

            if df is None or df.empty:
                return None

            row = df.iloc[0]

            return {
                "code": code,
                "name": "",
                "current_price": float(row.get("close", 0)),
                "change_percent": float(row.get("pct_chg", 0)),
                "change_amount": float(row.get("change", 0)),
                "volume": float(row.get("vol", 0)) if row.get("vol") else 0,
                "amount": float(row.get("amount", 0)) * 1000 if row.get("amount") else 0,
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "open": float(row.get("open", 0)),
                "prev_close": float(row.get("pre_close", 0)),
                "data_source": "tushare",
            }

        except (ValueError, TypeError):
            return None

    def _fetch_quote_baostock(self, code: str) -> dict[str, Any] | None:
        """使用 Baostock 获取行情"""
        try:
            import baostock as bs
            import pandas as pd

            lg = bs.login()
            if lg.error_code != "0":
                return None

            try:
                stock_code = code[2:] if code.startswith(("sh", "sz")) else code
                rs = bs.query_history_k_data_plus(
                    stock_code,
                    "date,code,open,high,low,close,volume,amount,adjustflag,turn,tradestatus,pbMRQ,peTTM",
                    start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                    frequency="d",
                    adjustflag="2",
                )

                if rs.error_code != "0":
                    return None

                data_list = []
                while (rs.error_code == "0") & rs.next():
                    data_list.append(rs.get_row_data())

                if not data_list:
                    return None

                df = pd.DataFrame(data_list, columns=rs.fields)
                row = df.iloc[-1]

                return {
                    "code": code,
                    "name": "",
                    "current_price": float(row.get("close", 0)) if row.get("close") else 0,
                    "change_percent": 0,
                    "change_amount": 0,
                    "volume": float(row.get("volume", 0)) if row.get("volume") else 0,
                    "amount": float(row.get("amount", 0)) if row.get("amount") else 0,
                    "high": float(row.get("high", 0)) if row.get("high") else 0,
                    "low": float(row.get("low", 0)) if row.get("low") else 0,
                    "open": float(row.get("open", 0)) if row.get("open") else 0,
                    "prev_close": float(df.iloc[-2].get("close", 0)) if len(df) > 1 else 0,
                    "data_source": "baostock",
                }

            finally:
                bs.logout()

        except (ValueError, TypeError):
            return None

    def get_source_status(self) -> dict[str, Any]:
        """获取数据源状态"""
        return {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources": {
                name: {
                    "enabled": cfg.enabled,
                    "priority": cfg.priority,
                    "status": cfg.status.value,
                    "error_count": cfg.error_count,
                    "success_count": cfg.success_count,
                }
                for name, cfg in self.sources.items()
            },
            "available_sources": self.get_available_sources(),
        }

    def enable_source(self, source_name: str) -> bool:
        """启用数据源"""
        if source_name in self.sources:
            self.sources[source_name].enabled = True
            self._save_configs()
            return True
        return False

    def disable_source(self, source_name: str) -> bool:
        """禁用数据源"""
        if source_name in self.sources:
            self.sources[source_name].enabled = False
            self._save_configs()
            return True
        return False

    def set_source_priority(self, source_name: str, priority: int) -> bool:
        """设置数据源优先级"""
        if source_name in self.sources:
            self.sources[source_name].priority = priority
            self._save_configs()
            return True
        return False

    def reset_source_status(self, source_name: str) -> bool:
        """重置数据源状态"""
        if source_name in self.sources:
            cfg = self.sources[source_name]
            cfg.status = DataSourceStatus.HEALTHY
            cfg.error_count = 0
            cfg.success_count = 0
            self._save_configs()
            return True
        return False


multi_source_fetcher = MultiSourceDataFetcher()
