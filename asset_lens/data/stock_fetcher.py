"""
Stock data fetcher for asset-lens.
股票数据获取模块 - 获取A股、港股、美股实时行情

数据源: AkShare (开源免费，无需注册)
- GitHub: https://github.com/akfamily/akshare
- 文档: https://akshare.akfamily.xyz
"""

import json
import logging
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from ..config import config
from ..utils.http_client import get_session_without_proxy

logger = logging.getLogger(__name__)

from ..utils.http_client import with_retry


class StockDataFetcher:
    """股票数据获取器 - 使用 AkShare 开源库"""

    def __init__(self, cache_path: Path | None = None):
        """
        初始化股票数据获取器

        Args:
            cache_path: 缓存路径
        """
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.stock_cache_file = self.cache_path / "stock_quotes.json"
        self._stock_codes_map: dict[str, str] | None = None
        self._akshare = None

    @property
    def akshare(self):
        """延迟加载 AkShare"""
        if self._akshare is None:
            try:
                import akshare as ak

                self._akshare = ak
            except ImportError:
                raise ImportError(
                    "请先安装 AkShare: pip install akshare\n"
                    "AkShare 是一个开源免费的金融数据接口，无需注册\n"
                    "GitHub: https://github.com/akfamily/akshare"
                )
        return self._akshare

    def _load_stock_codes_config(self) -> dict[str, str]:
        """
        加载股票代码配置

        Returns:
            股票名称到代码的映射
        """
        if self._stock_codes_map is not None:
            return self._stock_codes_map

        config_file = config.project_root / "config" / "fund_stock_codes.json"
        result = {}

        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    data = json.load(f)

                for stock in data.get("stocks", []):
                    name = stock.get("name", "")
                    code = stock.get("code", "")
                    if name and code:
                        result[name] = code

                    for keyword in stock.get("keywords", []):
                        if keyword and code:
                            result[keyword] = code

                self._stock_codes_map = result
                return result
            except Exception as e:
                logger.error(f"加载股票代码配置失败: {e}", exc_info=True)

        self._stock_codes_map = {}
        return {}

    def fetch_stock_quote_akshare(self, stock_code: str) -> dict[str, Any] | None:
        """
        获取股票实时行情（AkShare）- 支持多数据源故障切换

        Args:
            stock_code: 股票代码（如 sh600519, sz000001, hk00700）

        Returns:
            股票行情数据
        """
        if stock_code.startswith(("sh", "sz")):
            result = self._fetch_cn_stock_with_fallback(stock_code)
            return result if isinstance(result, dict) else None
        elif stock_code.startswith("hk"):
            result = self._fetch_hk_stock_quote(stock_code)
            return result if isinstance(result, dict) else None
        else:
            return None

    def _fetch_cn_stock_with_fallback(self, stock_code: str) -> dict[str, Any] | None:
        """
        获取A股实时行情 - 支持多数据源故障切换

        数据源优先级说明：
        1. eastmoney - 免费，实时性好，数据全面（优先）
        2. sina - 免费，实时行情
        3. baostock - 免费，稳定可靠

        Args:
            stock_code: 股票代码（如 sh600519, sz000001）

        Returns:
            股票行情数据
        """
        sources = [
            ("eastmoney", self._fetch_cn_stock_quote),
            ("sina", self._fetch_cn_stock_quote_sina),
            ("baostock", self._fetch_cn_stock_quote_baostock),
        ]

        for source_name, fetch_func in sources:
            try:
                logger.info(f"尝试从 {source_name} 获取 {stock_code} 行情...")
                result = fetch_func(stock_code)
                if result and isinstance(result, dict):
                    result["source"] = f"AkShare-{source_name}"
                    return dict(result)
            except Exception as e:
                logger.warning(f"{source_name} 获取失败: {e}，尝试下一个数据源...")
                continue

        logger.error(f"所有数据源都失败: {stock_code}")
        return None

    @with_retry(max_retries=3, retry_delay=2.0, )
    def _fetch_cn_stock_quote_sina(self, stock_code: str) -> dict[str, Any] | None:
        """
        获取A股实时行情（新浪数据源）

        Args:
            stock_code: 股票代码（如 sh600519, sz000001）

        Returns:
            股票行情数据
        """
        try:
            logger.info(f"正在从新浪获取 {stock_code} 行情...")

            df = self.akshare.stock_zh_a_spot()

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

            logger.info(f"新浪成功获取 {stock_code} 行情: {row.get('名称', '')} {change_percent:+.2f}%")

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
                "amplitude": 0,
                "market_cap": 0,
                "turnover_rate": 0,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "AkShare-sina",
            }

        except Exception as e:
            logger.error(f"新浪获取A股行情失败 {stock_code}: {e}")
            raise

    @with_retry(max_retries=2, retry_delay=1.0, )
    def _fetch_cn_stock_quote_baostock(self, stock_code: str) -> dict[str, Any] | None:
        """
        获取A股实时行情（Baostock数据源）

        Args:
            stock_code: 股票代码（如 sh600519, sz000001）

        Returns:
            股票行情数据
        """
        try:
            from datetime import datetime, timedelta

            import baostock as bs
            import pandas as pd

            logger.info(f"正在从Baostock获取 {stock_code} 行情...")

            lg = bs.login()
            if lg.error_code != "0":
                logger.warning(f"Baostock登录失败: {lg.error_msg}")
                return None

            try:
                stock_code_num = stock_code[2:]
                baostock_code = f"{stock_code[:2]}.{stock_code_num}"
                rs = bs.query_history_k_data_plus(
                    baostock_code,
                    "date,code,open,high,low,close,volume,amount,turn",
                    start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                    frequency="d",
                    adjustflag="2",
                )

                if rs.error_code != "0":
                    logger.warning(f"Baostock查询失败: {rs.error_msg}")
                    return None

                data_list = []
                while (rs.error_code == "0") & rs.next():
                    data_list.append(rs.get_row_data())

                if not data_list:
                    logger.warning(f"Baostock数据为空: {stock_code}")
                    return None

                df = pd.DataFrame(data_list, columns=rs.fields)
                row = df.iloc[-1]

                current_price = float(row.get("close", 0)) if row.get("close") else 0
                prev_close = float(df.iloc[-2].get("close", 0)) if len(df) > 1 else current_price
                change_amount = current_price - prev_close if prev_close > 0 else 0
                change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

                logger.info(f"Baostock成功获取 {stock_code} 行情: {change_percent:+.2f}%")

                return {
                    "code": stock_code,
                    "name": "",
                    "current_price": current_price,
                    "open": float(row.get("open", 0)) if row.get("open") else 0,
                    "prev_close": prev_close,
                    "high": float(row.get("high", 0)) if row.get("high") else 0,
                    "low": float(row.get("low", 0)) if row.get("low") else 0,
                    "volume": int(float(row.get("volume", 0))) if row.get("volume") else 0,
                    "amount": float(row.get("amount", 0)) if row.get("amount") else 0,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                    "amplitude": 0,
                    "market_cap": 0,
                    "turnover_rate": float(row.get("turn", 0)) if row.get("turn") else 0,
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "Baostock",
                }

            finally:
                bs.logout()

        except Exception as e:
            logger.error(f"Baostock获取A股行情失败 {stock_code}: {e}")
            raise

    @with_retry(max_retries=2, retry_delay=1.0, )
    def _fetch_cn_stock_quote_joinquant(self, stock_code: str) -> dict[str, Any] | None:
        """
        获取A股实时行情（聚宽数据源）

        Args:
            stock_code: 股票代码（如 sh600519, sz000001）

        Returns:
            股票行情数据
        """
        try:
            from datetime import datetime, timedelta

            import jqdatasdk as jq
            import pandas as pd

            logger.info(f"正在从聚宽获取 {stock_code} 行情...")

            if not config.joinquant_username or not config.joinquant_password:
                logger.warning("聚宽账号密码未配置，请设置环境变量 JOINQUANT_USERNAME 和 JOINQUANT_PASSWORD")
                return None

            jq.auth(config.joinquant_username, config.joinquant_password)

            jq_code = self._convert_to_jq_code(stock_code)

            try:
                df = jq.get_price(
                    jq_code,
                    count=2,
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                    frequency="daily",
                    fields=["open", "close", "high", "low", "volume", "money"],
                )

                if df is None or df.empty or len(df) == 0:
                    logger.warning(f"聚宽数据为空: {stock_code}")
                    return None

                current_row = df.iloc[-1]
                prev_close = df.iloc[-2]["close"] if len(df) > 1 else current_row["close"]

                current_price = float(current_row["close"])
                change_amount = current_price - prev_close
                change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

                logger.info(f"聚宽成功获取 {stock_code} 行情: {change_percent:+.2f}%")

                return {
                    "code": stock_code,
                    "name": "",
                    "current_price": current_price,
                    "open": float(current_row["open"]),
                    "prev_close": float(prev_close),
                    "high": float(current_row["high"]),
                    "low": float(current_row["low"]),
                    "volume": int(current_row["volume"]),
                    "amount": float(current_row["money"]),
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                    "amplitude": 0,
                    "market_cap": 0,
                    "turnover_rate": 0,
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "JoinQuant",
                }

            except Exception as e:
                logger.error(f"聚宽查询失败: {e}")
                raise

        except ImportError:
            logger.warning("jqdatasdk 未安装，请运行: pip install jqdatasdk")
            raise
        except Exception as e:
            logger.error(f"聚宽获取A股行情失败 {stock_code}: {e}")
            raise

    def _convert_to_jq_code(self, stock_code: str) -> str:
        """
        将股票代码转换为聚宽格式

        Args:
            stock_code: 股票代码（如 sh600519, sz000001）

        Returns:
            聚宽格式股票代码（如 600519.XSHG, 000001.XSHE）
        """
        code = stock_code[2:]
        if stock_code.startswith("sh"):
            return f"{code}.XSHG"
        elif stock_code.startswith("sz"):
            return f"{code}.XSHE"
        else:
            return stock_code

    @with_retry(max_retries=3, retry_delay=2.0, )
    def _fetch_cn_stock_quote(self, stock_code: str) -> dict[str, Any] | None:
        """
        获取A股实时行情（AkShare）

        Args:
            stock_code: 股票代码（如 sh600519, sz000001）

        Returns:
            股票行情数据
        """
        try:
            logger.info(f"正在获取 {stock_code} 行情...")

            df = self.akshare.stock_zh_a_spot_em()

            if df is None or df.empty:
                logger.warning(f"获取A股数据为空: {stock_code}")
                return None

            code = stock_code[2:]

            row = df[df["代码"] == code]

            if row.empty:
                logger.warning(f"未找到股票: {stock_code}")
                return None

            row = row.iloc[0]

            current_price = float(row.get("最新价", 0))
            prev_close = float(row.get("昨收", 0))
            open_price = float(row.get("今开", 0))
            high = float(row.get("最高", 0))
            low = float(row.get("最低", 0))
            volume = float(row.get("成交量", 0))
            amount = float(row.get("成交额", 0))
            amplitude = float(row.get("振幅", 0))
            change_percent = float(row.get("涨跌幅", 0))
            change_amount = float(row.get("涨跌额", 0))
            turnover_rate = float(row.get("换手率", 0))
            market_cap = float(row.get("总市值", 0)) / 100000000 if row.get("总市值") else 0

            logger.info(f"成功获取 {stock_code} 行情: {row.get('名称', '')} {change_percent:+.2f}%")

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
                "amplitude": amplitude,
                "market_cap": market_cap,
                "turnover_rate": turnover_rate,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "AkShare",
            }

        except Exception as e:
            logger.error(f"获取A股行情失败 {stock_code}: {e}")
            raise

    @with_retry(max_retries=3, retry_delay=2.0, )
    def _fetch_hk_stock_quote(self, stock_code: str) -> dict[str, Any] | None:
        """
        获取港股实时行情（AkShare）

        Args:
            stock_code: 股票代码（如 hk00700）

        Returns:
            股票行情数据
        """
        try:
            logger.info(f"正在获取 {stock_code} 行情...")

            df = self.akshare.stock_hk_spot_em()

            if df is None or df.empty:
                logger.warning(f"获取港股数据为空: {stock_code}")
                return None

            code = stock_code[2:]

            row = df[df["代码"] == code]

            if row.empty:
                logger.warning(f"未找到股票: {stock_code}")
                return None

            row = row.iloc[0]

            current_price = float(row.get("最新价", 0))
            prev_close = float(row.get("昨收", 0))
            open_price = float(row.get("今开", 0))
            high = float(row.get("最高", 0))
            low = float(row.get("最低", 0))
            volume = float(row.get("成交量", 0)) if row.get("成交量") else 0
            amount = float(row.get("成交额", 0)) if row.get("成交额") else 0

            change_amount = current_price - prev_close if prev_close > 0 else 0
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            logger.info(f"成功获取 {stock_code} 行情: {row.get('名称', '')} {change_percent:+.2f}%")

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
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "AkShare",
            }

        except Exception as e:
            logger.error(f"获取港股行情失败 {stock_code}: {e}")
            raise

    def fetch_us_stock_quote(self, symbol: str) -> dict[str, Any] | None:
        """
        获取美股实时行情（Finnhub 正规 API）

        Args:
            symbol: 股票代码（如 AAPL, TSLA）

        Returns:
            股票行情数据

        Raises:
            ConfigurationError: 如果 API 密钥未配置
        """

        try:
            if not config.finnhub_api_key:
                logger.warning("FINNHUB_API_KEY 未配置，无法获取美股行情")
                return None

            if len(config.finnhub_api_key) < 10:
                logger.warning("FINNHUB_API_KEY 格式不正确，密钥长度应该至少 10 个字符")
                return None

            headers = {
                "Authorization": f"Bearer {config.finnhub_api_key}",
                "User-Agent": "asset-lens/1.0",
                "Accept": "application/json",
            }

            url = "https://api.finnhub.io/api/v1/quote"
            params = {"symbol": symbol}

            session = get_session_without_proxy()
            response = session.get(url, params=params, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.warning(f"获取美股行情失败: {symbol}, HTTP {response.status_code}")
                return None

            data = response.json()

            if data is None:
                return None

            current_price = float(data.get("c", 0))
            prev_close = float(data.get("pc", 0))
            high = float(data.get("h", 0))
            low = float(data.get("l", 0))
            open_price = float(data.get("o", 0))

            if current_price == 0 or prev_close == 0:
                return None

            change_amount = current_price - prev_close
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            logger.debug(f"成功获取美股行情: {symbol}")

            return {
                "code": symbol,
                "name": symbol,
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": 0,
                "amount": 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Finnhub",
            }

        except Exception as e:
            logger.error(f"获取美股行情失败 {symbol}: {e}", exc_info=True)
            return None

    def fetch_multiple_stocks(self, stock_codes: list[str]) -> dict[str, Any]:
        """
        批量获取股票行情

        Args:
            stock_codes: 股票代码列表

        Returns:
            股票行情数据字典
        """
        results = {}

        for code in stock_codes:
            logger.info(f"正在获取 {code} 行情...")

            if code.startswith(("sh", "sz", "hk")):
                data = self.fetch_stock_quote_akshare(code)
            else:
                data = self.fetch_us_stock_quote(code)

            if data:
                results[code] = data
                logger.info(f"✅ {data['name']}: {data['change_percent']:+.2f}%")
            else:
                logger.warning(f"❌ {code}: 获取失败")

            time.sleep(0.1)

        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": results,
        }

        with open(self.stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        return cache_data

    def get_cached_stocks(self) -> dict[str, Any]:
        """获取缓存的股票数据"""
        if self.stock_cache_file.exists():
            with open(self.stock_cache_file, encoding="utf-8") as f:
                return json.load(f)  # type: ignore
        return {}

    def fetch_multiple_stocks_concurrent(
        self, stock_codes: list[str], max_concurrent: int = 10, use_cache: bool = True
    ) -> dict[str, Any]:
        """
        并发获取股票行情（性能优化版本）

        Args:
            stock_codes: 股票代码列表
            max_concurrent: 最大并发数
            use_cache: 是否使用缓存

        Returns:
            股票行情数据字典
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        from ..core.intelligent_cache import intelligent_cache

        results = {}
        cached_count = 0
        fetch_count = 0

        if use_cache:
            for code in stock_codes:
                cache_key = f"stock_quote_{code}"
                cached_data = intelligent_cache.get(cache_key)

                if cached_data is not None:
                    results[code] = cached_data
                    cached_count += 1
                    logger.info(f"✅ {code}: 使用缓存数据")

        uncached_codes = [code for code in stock_codes if code not in results]

        if uncached_codes:
            logger.info(f"开始并发获取 {len(uncached_codes)} 只股票数据...")

            def fetch_single(code: str) -> tuple[str, dict | None]:
                if code.startswith(("sh", "sz", "bj")):
                    data = self.fetch_stock_quote_akshare(code)
                else:
                    data = self.fetch_us_stock_quote(code)
                return code, data

            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = {executor.submit(fetch_single, code): code for code in uncached_codes}
                for future in as_completed(futures):
                    code, data = future.result()
                    if data:
                        results[code] = data
                        fetch_count += 1
                        if use_cache:
                            cache_key = f"stock_quote_{code}"
                            intelligent_cache.set(cache_key, data, ttl=60)
                        logger.info(f"✅ {code}: {data.get('name', 'N/A')} - 获取成功")
                    else:
                        logger.error(f"❌ {code}: 获取失败")

        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": results,
            "stats": {
                "total": len(stock_codes),
                "cached": cached_count,
                "fetched": fetch_count,
                "failed": len(stock_codes) - cached_count - fetch_count,
            },
        }

        with open(self.stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        logger.info(f"批量获取完成: 总计 {len(stock_codes)} 只, 缓存 {cached_count} 只, 新获取 {fetch_count} 只")

        return cache_data


stock_fetcher = StockDataFetcher()
