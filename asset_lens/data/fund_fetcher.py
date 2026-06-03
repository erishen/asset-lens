"""
Fund data fetcher for asset-lens.
基金数据获取模块 - 获取基金净值、持仓等信息

数据源: AkShare (开源免费，无需注册)
- GitHub: https://github.com/akfamily/akshare
- 文档: https://akshare.akfamily.xyz
"""

import logging
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import config
from ..utils.http_client import get_session_without_proxy
from .fetchers.base import FetcherCacheMixin

logger = logging.getLogger(__name__)


@contextmanager
def timeout_context(seconds: int, message: str = "操作超时"):
    """
    超时上下文管理器（使用 signal.alarm，仅限 Unix/macOS）

    Args:
        seconds: 超时秒数
        message: 超时消息
    """
    import signal

    def _timeout_handler(signum, frame):
        raise TimeoutError(message)

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    except TimeoutError:
        raise
    except (ValueError, RuntimeError, OSError) as e:
        logger.debug(f"忽略异常: {e}")
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class FundDataFetcher(FetcherCacheMixin):
    def __init__(self, cache_path: Path | None = None):
        self._init_cache(
            cache_path or config.cache_path,
            default_ttl=3600,
        )
        self._fund_codes_map: dict[str, str] | None = None

    @property
    def fund_cache_file(self) -> Path:
        return self.cache_path / "fund_quotes.json"

    def _load_fund_codes_config(self) -> dict[str, str]:
        if self._fund_codes_map is not None:
            return self._fund_codes_map

        config_file = config.project_root / "config" / "fund_stock_codes.json"
        result = {}

        data = self._cache.load_file(str(config_file))
        if data is not None:
            try:
                for fund in data.get("funds", []):
                    name = fund.get("name", "")
                    code = fund.get("code", "")
                    if name and code:
                        result[name] = code

                    for keyword in fund.get("keywords", []):
                        if keyword and code:
                            result[keyword] = code

                self._fund_codes_map = result
                return result
            except (json.JSONDecodeError, OSError, ValueError) as e:
                logger.warning(f"加载基金代码配置失败: {e}")

        self._fund_codes_map = {}
        return {}

    def fetch_fund_quote_akshare(self, fund_code: str, timeout: int = 15) -> dict[str, Any] | None:
        """
        获取基金净值（AkShare + 东方财富API 双源，自动重试）

        Args:
            fund_code: 基金代码（如 000001, 110022）
            timeout: 超时秒数

        Returns:
            基金净值数据
        """
        for attempt in range(2):
            try:
                with timeout_context(timeout, f"获取基金 {fund_code} 超时"):
                    df = self.akshare.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")

                    if df is None or df.empty:
                        break

                    if not hasattr(df, "iloc"):
                        break

                    latest = df.iloc[-1]

                    if len(df) > 1:
                        prev = df.iloc[-2]
                        prev_nav = float(prev.get("单位净值", 0))
                    else:
                        prev_nav = float(latest.get("单位净值", 0))

                    current_nav = float(latest.get("单位净值", 0))
                    change_percent = ((current_nav - prev_nav) / prev_nav * 100) if prev_nav > 0 else 0

                    return {
                        "code": fund_code,
                        "name": fund_code,
                        "current_nav": current_nav,
                        "prev_nav": prev_nav,
                        "nav_date": str(latest.get("净值日期", "")),
                        "estimate_nav": current_nav,
                        "estimate_time": str(latest.get("净值日期", "")),
                        "change_percent": round(change_percent, 2),
                        "fund_type": "开放式基金",
                        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "AkShare",
                    }

            except TimeoutError as e:
                logger.warning(f"获取基金净值超时 (第{attempt + 1}次): {e}")
                if attempt == 0:
                    import time

                    time.sleep(1)
                    continue
            except (ValueError, KeyError, ConnectionError) as e:
                logger.error(f"获取基金净值失败 {fund_code}: {e}")
                if attempt == 0:
                    import time

                    time.sleep(1)
                    continue

        return self._fetch_fund_quote_eastmoney_api(fund_code)

    def _fetch_fund_quote_eastmoney_api(self, fund_code: str) -> dict[str, Any] | None:
        """使用东方财富基金详情API获取净值（AkShare超时时的备用方案）"""
        try:
            url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js"
            session = get_session_without_proxy()
            response = session.get(url, timeout=10)
            response.raise_for_status()

            text = response.text
            if not text or "jsonpgz" not in text:
                return None

            import json

            json_str = text.replace("jsonpgz(", "").rstrip(")")
            data = json.loads(json_str)

            current_nav = float(data.get("gsz", 0))
            prev_nav = float(data.get("dwjz", 0))
            change_percent = float(data.get("gszzl", 0))

            if current_nav == 0 and prev_nav == 0:
                return None

            if current_nav == 0:
                current_nav = prev_nav

            return {
                "code": fund_code,
                "name": data.get("name", fund_code),
                "current_nav": current_nav,
                "prev_nav": prev_nav,
                "nav_date": data.get("jzrq", ""),
                "estimate_nav": current_nav,
                "estimate_time": data.get("gztime", ""),
                "change_percent": change_percent,
                "fund_type": "开放式基金",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "EastMoney-API",
            }
        except (ValueError, KeyError, ConnectionError) as e:
            logger.error(f"东方财富API获取基金 {fund_code} 净值失败: {e}")
            return None

    def fetch_fund_quote_eastmoney(self, fund_code: str) -> dict[str, Any] | None:
        """
        获取基金净值（兼容旧接口名）

        Args:
            fund_code: 基金代码（如 000001, 110022）

        Returns:
            基金净值数据
        """
        return self.fetch_fund_quote_akshare(fund_code)

    def fetch_fund_info(self, fund_code: str) -> dict[str, Any] | None:
        """
        获取基金详细信息

        Args:
            fund_code: 基金代码

        Returns:
            基金详细信息
        """
        try:
            df = self.akshare.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")

            if df is None or df.empty:
                return None

            return {
                "code": fund_code,
                "name": fund_code,
                "latest_nav": float(df.iloc[-1].get("单位净值", 0)),
                "nav_date": str(df.iloc[-1].get("净值日期", "")),
                "source": "AkShare",
            }

        except (ValueError, KeyError, ConnectionError) as e:
            logger.error(f"获取基金信息失败 {fund_code}: {e}")
            return None

    def fetch_fund_historical_nav(
        self, fund_code: str, page: int = 1, page_size: int = 20
    ) -> list[dict[str, Any]] | None:
        """
        获取基金历史净值

        Args:
            fund_code: 基金代码
            page: 页码
            page_size: 每页数量

        Returns:
            历史净值列表
        """
        try:
            df = self.akshare.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")

            if df is None or df.empty:
                return None

            result = []
            for _, row in df.tail(page_size).iterrows():
                result.append(
                    {
                        "date": str(row.get("净值日期", "")),
                        "nav": float(row.get("单位净值", 0)),
                        "accumulated_nav": float(row.get("累计净值", 0)) if "累计净值" in row else 0,
                        "change_percent": None,
                    }
                )

            return result

        except (ValueError, KeyError, ConnectionError) as e:
            logger.error(f"获取基金历史净值失败 {fund_code}: {e}")
            return None

    def fetch_multiple_funds(self, fund_codes: list[str]) -> dict[str, Any]:
        """
        批量获取基金净值

        Args:
            fund_codes: 基金代码列表

        Returns:
            基金净值数据字典
        """
        results = {}

        for code in fund_codes:
            logger.info(f"正在获取基金 {code} 净值...")

            data = self.fetch_fund_quote_akshare(code)

            if data:
                results[code] = data
                logger.info(f"   {data['name']}: {data['change_percent']:+.2f}%")
            else:
                logger.error(f"   {code}: 获取失败")

            time.sleep(0.1)

        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": results,
        }

        self._cache.save_file("fund_quotes.json", cache_data, ttl=0)

        return cache_data

    def get_cached_funds(self) -> dict[str, Any]:
        """获取缓存的基金数据"""
        data = self._cache.load_file("fund_quotes.json")
        if data is not None:
            return data
        return {}

    def search_fund(self, keyword: str) -> list[dict[str, Any]]:
        """
        搜索基金

        Args:
            keyword: 搜索关键词

        Returns:
            基金列表
        """
        try:
            # 使用 AkShare 的基金搜索接口
            df = self.akshare.fund_open_fund_daily_em()

            if df is None or df.empty:
                return []

            # 搜索匹配的基金
            mask = df["基金简称"].str.contains(keyword, na=False)
            matched = df[mask]

            result = []
            for _, row in matched.head(10).iterrows():
                result.append(
                    {
                        "code": str(row.get("基金代码", "")),
                        "name": str(row.get("基金简称", "")),
                        "type": str(row.get("基金类型", "")),
                        "pinyin": "",
                        "nav": float(row.get("单位净值", 0)) if row.get("单位净值") else 0,
                        "manager": "",
                        "company": "",
                    }
                )

            return result

        except (ValueError, KeyError, ConnectionError) as e:
            logger.error(f"搜索基金失败: {e}")
            return []


fund_fetcher = FundDataFetcher()


def auto_match_fund_codes(product_names: list[str]) -> dict[str, str | None]:
    """
    自动匹配基金代码

    Args:
        product_names: 产品名称列表

    Returns:
        产品名称到基金代码的映射
    """
    result: dict[str, str | None] = {}

    config_map = fund_fetcher._load_fund_codes_config()

    for name in product_names:
        if not name or name.strip() == "":
            result[name] = None
            continue

        skip_keywords = [
            "余额宝",
            "朝朝宝",
            "活期富",
            "现金宝",
            "活期",
            "零钱通",
            "理财宝",
            "薪金煲",
            "货币",
            "现金",
            "存款",
            "理财",
            "定期",
            "通知存款",
            "白银",
            "原油",
            "期货",
            "期权",
            "外汇",
        ]

        should_skip = False
        for keyword in skip_keywords:
            if keyword in name:
                should_skip = True
                break

        if should_skip:
            result[name] = None
            continue

        if name in config_map:
            result[name] = config_map[name]
            continue

        for keyword, code in config_map.items():
            if keyword in name or name in keyword:
                result[name] = code
                break

        if name in result:
            continue

        funds = fund_fetcher.search_fund(name)

        if funds:
            for fund in funds:
                fund_name = fund.get("name", "")
                if name in fund_name or fund_name in name:
                    result[name] = str(fund.get("code", ""))
                    break

            if name not in result:
                result[name] = str(funds[0].get("code", ""))
        else:
            result[name] = None

        time.sleep(0.1)

    return result


def fetch_portfolio_fund_quotes() -> dict[str, Any]:
    """
    获取投资组合中所有基金的净值

    Returns:
        基金净值数据
    """
    from .csv_parser import CSVParser

    logger.info(" 正在加载投资产品数据...")
    products = CSVParser.load_data()

    fund_products = []
    for p in products:
        name = p.name
        inv_type = p.investment_type.value if p.investment_type else ""

        if inv_type in ["基金", "混合", "股票", "指数", "债券"]:
            fund_products.append(name)

    if not fund_products:
        logger.info(" 没有找到基金类产品")
        return {}

    logger.info(f"📋 找到 {len(fund_products)} 个基金类产品")

    logger.info(f"🔍 正在匹配基金代码...")
    fund_codes_map = auto_match_fund_codes(fund_products)

    matched_codes = []
    unmatched_names = []

    for name, code in fund_codes_map.items():
        if code:
            matched_codes.append(code)
            logger.info(f"   {name} -> {code}")
        else:
            unmatched_names.append(name)
            logger.info(f"   {name} -> 未匹配")

    if unmatched_names:
        logger.info(f"  有 {len(unmatched_names)} 个产品未能匹配基金代码:")
        for name in unmatched_names:
            logger.info(f"  - {name}")

    if not matched_codes:
        logger.info(f" 没有匹配到任何基金代码")
        return {}

    logger.info(f" 正在获取 {len(matched_codes)} 只基金的净值...")
    return fund_fetcher.fetch_multiple_funds(matched_codes)
