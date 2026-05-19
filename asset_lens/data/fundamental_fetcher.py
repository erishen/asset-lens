"""
Fundamental and Money Flow Data Fetcher.
基本面数据和资金流向数据获取模块

数据源: AkShare (开源免费)
- PE/PB/ROE等基本面指标
- 北向资金/主力资金流向
"""

import warnings

warnings.filterwarnings("ignore", message="Pandas requires version")
warnings.filterwarnings("ignore", message=".*unclosed.*socket.*")
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import contextlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FundamentalData:
    """基本面数据"""

    code: str
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    roe: float = 0.0
    revenue_growth: float = 0.0
    profit_growth: float = 0.0
    debt_ratio: float = 0.0
    gross_margin: float = 0.0
    net_margin: float = 0.0
    total_market_value: float = 0.0
    circulating_market_value: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "roe": self.roe,
            "revenue_growth": self.revenue_growth,
            "profit_growth": self.profit_growth,
            "debt_ratio": self.debt_ratio,
            "gross_margin": self.gross_margin,
            "net_margin": self.net_margin,
            "total_market_value": self.total_market_value,
            "circulating_market_value": self.circulating_market_value,
        }


@dataclass
class MoneyFlowData:
    """资金流向数据"""

    code: str
    date: str = ""
    main_net_inflow: float = 0.0
    main_net_inflow_ratio: float = 0.0
    retail_net_inflow: float = 0.0
    retail_net_inflow_ratio: float = 0.0
    super_net_inflow: float = 0.0
    super_net_inflow_ratio: float = 0.0
    big_net_inflow: float = 0.0
    big_net_inflow_ratio: float = 0.0
    medium_net_inflow: float = 0.0
    medium_net_inflow_ratio: float = 0.0
    small_net_inflow: float = 0.0
    small_net_inflow_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "date": self.date,
            "main_net_inflow": self.main_net_inflow,
            "main_net_inflow_ratio": self.main_net_inflow_ratio,
            "retail_net_inflow": self.retail_net_inflow,
            "retail_net_inflow_ratio": self.retail_net_inflow_ratio,
            "super_net_inflow": self.super_net_inflow,
            "super_net_inflow_ratio": self.super_net_inflow_ratio,
            "big_net_inflow": self.big_net_inflow,
            "big_net_inflow_ratio": self.big_net_inflow_ratio,
            "medium_net_inflow": self.medium_net_inflow,
            "medium_net_inflow_ratio": self.medium_net_inflow_ratio,
            "small_net_inflow": self.small_net_inflow,
            "small_net_inflow_ratio": self.small_net_inflow_ratio,
        }


class FundamentalFetcher:
    """基本面数据获取器"""

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or Path(__file__).parent / "cache"
        self.cache_file = self.cache_path / "fundamental_cache.json"
        self._akshare = None
        self._cache: dict[str, FundamentalData] = {}
        self._load_cache()

    @property
    def akshare(self):
        if self._akshare is None:
            try:
                import akshare as ak

                self._akshare = ak
            except ImportError:
                logger.warning("AkShare 未安装")
        return self._akshare

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for code, info in data.get("fundamentals", {}).items():
                        self._cache[code] = FundamentalData(
                            code=code,
                            pe_ratio=info.get("pe_ratio", 0),
                            pb_ratio=info.get("pb_ratio", 0),
                            roe=info.get("roe", 0),
                            revenue_growth=info.get("revenue_growth", 0),
                            profit_growth=info.get("profit_growth", 0),
                            debt_ratio=info.get("debt_ratio", 0),
                            gross_margin=info.get("gross_margin", 0),
                            net_margin=info.get("net_margin", 0),
                            total_market_value=info.get("total_market_value", 0),
                            circulating_market_value=info.get("circulating_market_value", 0),
                        )
            except Exception as e:
                logger.warning(f"加载基本面缓存失败: {e}")

    def _save_cache(self):
        self.cache_path.mkdir(parents=True, exist_ok=True)
        data = {
            "updated_at": datetime.now().isoformat(),
            "fundamentals": {code: info.to_dict() for code, info in self._cache.items()},
        }
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_fundamental(self, code: str) -> FundamentalData:
        """获取单只股票基本面数据"""
        if code in self._cache:
            return self._cache[code]

        data = FundamentalData(code=code)

        if self.akshare:
            try:
                df = self.akshare.stock_a_lg_indicator(symbol=code)  # pylint: disable=no-member
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    data.pe_ratio = float(latest.get("pe", 0) or 0)
                    data.pb_ratio = float(latest.get("pb", 0) or 0)
                    data.total_market_value = float(latest.get("total_mv", 0) or 0)
                    data.circulating_market_value = float(latest.get("circ_mv", 0) or 0)
            except Exception as e:
                logger.debug(f"获取 {code} 基本面数据失败: {e}")

        self._cache[code] = data
        return data

    def get_realtime_pe_pb(self, code: str) -> tuple[float, float]:
        """获取实时PE/PB"""
        if self.akshare:
            try:
                df = self.akshare.stock_a_lg_indicator(symbol=code)  # pylint: disable=no-member
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    pe = float(latest.get("pe", 0) or 0)
                    pb = float(latest.get("pb", 0) or 0)
                    return pe, pb
            except Exception:
                pass
        return 0.0, 0.0

    def batch_get_fundamentals(self, codes: list[str]) -> dict[str, FundamentalData]:
        """批量获取基本面数据"""
        result = {}
        for i, code in enumerate(codes):
            result[code] = self.get_fundamental(code)
            if (i + 1) % 50 == 0:
                logger.info(f"已获取 {i + 1}/{len(codes)} 只股票基本面数据")
        self._save_cache()
        return result


class MoneyFlowFetcher:
    """资金流向数据获取器"""

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or Path(__file__).parent / "cache"
        self.cache_file = self.cache_path / "money_flow_cache.json"
        self._akshare = None
        self._cache: dict[str, list[MoneyFlowData]] = {}
        self._load_cache()

    @property
    def akshare(self):
        if self._akshare is None:
            try:
                import akshare as ak

                self._akshare = ak
            except ImportError:
                logger.warning("AkShare 未安装")
        return self._akshare

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for code, flows in data.get("money_flows", {}).items():
                        self._cache[code] = [MoneyFlowData(**flow) for flow in flows]
            except Exception as e:
                logger.warning(f"加载资金流向缓存失败: {e}")

    def _save_cache(self):
        self.cache_path.mkdir(parents=True, exist_ok=True)
        data = {
            "updated_at": datetime.now().isoformat(),
            "money_flows": {code: [flow.to_dict() for flow in flows] for code, flows in self._cache.items()},
        }
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_money_flow(self, code: str, days: int = 30) -> list[MoneyFlowData]:
        """获取股票资金流向数据"""
        cache_key = f"{code}_{days}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        flows = []

        if self.akshare:
            try:
                df = self.akshare.stock_individual_fund_flow(stock=code, market="sh" if code.startswith("6") else "sz")
                if df is not None and not df.empty:
                    df = df.tail(days)
                    for _, row in df.iterrows():
                        flow = MoneyFlowData(
                            code=code,
                            date=str(row.get("日期", "")),
                            main_net_inflow=float(row.get("主力净流入-净额", 0) or 0),
                            main_net_inflow_ratio=float(row.get("主力净流入-净占比", 0) or 0),
                            super_net_inflow=float(row.get("超大单净流入-净额", 0) or 0),
                            super_net_inflow_ratio=float(row.get("超大单净流入-净占比", 0) or 0),
                            big_net_inflow=float(row.get("大单净流入-净额", 0) or 0),
                            big_net_inflow_ratio=float(row.get("大单净流入-净占比", 0) or 0),
                            medium_net_inflow=float(row.get("中单净流入-净额", 0) or 0),
                            medium_net_inflow_ratio=float(row.get("中单净流入-净占比", 0) or 0),
                            small_net_inflow=float(row.get("小单净流入-净额", 0) or 0),
                            small_net_inflow_ratio=float(row.get("小单净流入-净占比", 0) or 0),
                        )
                        flows.append(flow)
            except Exception as e:
                logger.debug(f"获取 {code} 资金流向失败: {e}")

        self._cache[cache_key] = flows
        return flows

    def get_latest_money_flow(self, code: str) -> MoneyFlowData:
        """获取最新资金流向"""
        flows = self.get_money_flow(code, days=1)
        return flows[0] if flows else MoneyFlowData(code=code)

    def get_north_money_flow(self, days: int = 30) -> pd.DataFrame:
        """获取北向资金数据（优先使用东方财富API，然后Playwright，最后AkShare）"""
        try:
            df = self._get_north_money_flow_eastmoney_api(days)
            if df is not None and not df.empty:
                logger.info(f"东方财富API获取北向资金成功，最新日期: {df['date'].iloc[0]}")
                return df
        except Exception as e:
            logger.warning(f"东方财富API获取北向资金失败: {e}")

        try:
            df = self._get_north_money_flow_playwright(days)
            if df is not None and not df.empty:
                logger.info(f"Playwright 获取北向资金成功，最新日期: {df['date'].iloc[-1]}")
                return df
        except Exception as e:
            logger.warning(f"Playwright 获取北向资金失败: {e}")

        logger.warning("Playwright 获取失败，尝试 AkShare 回退...")

        if not self.akshare:
            return pd.DataFrame()

        try:
            df = self.akshare.stock_hsgt_hist_em(symbol="北向资金")
            if df is not None and not df.empty:
                df = df.rename(
                    columns={
                        "日期": "date",
                        "当日成交净买额": "north_net_inflow",
                        "当日资金流入": "north_inflow",
                    }
                )
                df = df[df["north_net_inflow"].notna()]
                if not df.empty:
                    df["data_source"] = "AkShare历史数据"
                    logger.warning(f"AkShare 回退成功，但数据可能不是最新，最新日期: {df['date'].iloc[-1]}")
                    return df[["date", "north_net_inflow", "north_inflow", "data_source"]].tail(days)
                else:
                    logger.warning("AkShare 数据中 north_net_inflow 全为 NaN，无法使用")
        except Exception as e:
            logger.warning(f"获取北向资金历史数据失败: {e}")

        return pd.DataFrame()

    def _get_north_money_flow_eastmoney_api(self, days: int = 30) -> pd.DataFrame | None:
        """使用东方财富API获取北向资金每日净流入数据"""
        import requests

        try:
            url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
            params = {
                "reportName": "RPT_HSGT_NORTHBOUNDDETAIL",
                "columns": "TRADE_DATE,NET_BUY_AMT,SH_NET_BUY_AMT,SZ_NET_BUY_AMT",
                "pageSize": str(days),
                "sortColumns": "TRADE_DATE",
                "sortTypes": "-1",
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://data.eastmoney.com/",
            }
            response = requests.get(url, params=params, headers=headers, timeout=15)

            if response.status_code != 200:
                return None

            data = response.json()
            if not data.get("result") or not data["result"].get("data"):
                return None

            items = data["result"]["data"]
            records = []
            for item in items:
                trade_date = item.get("TRADE_DATE", "")
                net_buy = item.get("NET_BUY_AMT", 0)
                sh_buy = item.get("SH_NET_BUY_AMT", 0)
                sz_buy = item.get("SZ_NET_BUY_AMT", 0)

                if trade_date:
                    if isinstance(trade_date, str) and len(trade_date) > 10:
                        trade_date = trade_date[:10]
                    records.append({
                        "date": str(trade_date),
                        "north_net_inflow": float(net_buy) / 1e8 if isinstance(net_buy, (int, float)) and abs(net_buy) > 1e6 else float(net_buy or 0),
                        "north_inflow": float(sh_buy + sz_buy) / 1e8 if isinstance(sh_buy, (int, float)) and abs(sh_buy) > 1e6 else float((sh_buy or 0) + (sz_buy or 0)),
                        "data_source": "东方财富(API)",
                    })

            if records:
                df = pd.DataFrame(records)
                df = df.sort_values("date", ascending=False)
                return df.head(days)

        except Exception as e:
            logger.debug(f"东方财富API获取北向资金数据失败: {e}")

        return None

    def _get_north_money_flow_playwright(self, days: int = 30) -> pd.DataFrame | None:
        """使用 Playwright 从东方财富获取北向资金数据"""
        import json
        import re

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright 未安装，跳过")
            return None

        captured_data = []
        response_count = [0]

        def handle_response(response):
            url = response.url
            response_count[0] += 1
            if "datacenter" in url and "NET_INFLOW" in url:
                logger.info(f"捕获到北向资金 API 响应: {url[:80]}...")
                try:
                    if response.status == 200:
                        body = response.text()
                        if body and "NET_INFLOW_BOTH" in body:
                            captured_data.append(body)
                            logger.info(f"成功捕获北向资金数据，长度: {len(body)}")
                except Exception as e:
                    logger.warning(f"处理响应失败: {e}")

        try:
            logger.info("启动 Playwright 浏览器...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.on("response", handle_response)

                logger.info("访问东方财富北向资金页面...")
                page.goto("https://data.eastmoney.com/hsgt/", wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)
                browser.close()
                logger.info(f"页面加载完成，共捕获 {response_count[0]} 个响应")
        except Exception as e:
            logger.warning(f"Playwright 页面加载失败: {e}")
            return None

        if not captured_data:
            logger.warning("未捕获到北向资金 API 响应，可能页面结构已变化")
            return None

        jsonp = captured_data[0]
        match = re.search(r"\((.+)\)", jsonp, re.DOTALL)
        if not match:
            logger.warning("无法解析 JSONP 响应")
            return None

        try:
            data = json.loads(match.group(1))
            if not (data.get("result") and data["result"].get("data")):
                logger.warning("响应数据格式不正确")
                return None

            items = data["result"]["data"]
            records = []

            for item in items:
                date = item.get("TRADE_DATE", "")[:10]
                sh = item.get("NET_INFLOW_SH", 0) / 100
                sz = item.get("NET_INFLOW_SZ", 0) / 100
                both = item.get("NET_INFLOW_BOTH", 0) / 100

                records.append(
                    {
                        "date": date,
                        "north_net_inflow": both,
                        "north_inflow": sh + sz,
                        "data_source": "东方财富(Playwright)",
                    }
                )

            df = pd.DataFrame(records)
            df = df.sort_values("date", ascending=False)
            logger.info(f"成功解析 {len(df)} 条北向资金记录")
            return df.head(days)

        except Exception as e:
            logger.warning(f"解析北向资金数据失败: {e}")
            logger.debug(f"解析北向资金数据失败: {e}")
            return None

    def get_north_flow_by_industry(self, use_cache: bool = True, force: bool = False) -> pd.DataFrame:
        """获取北向资金行业流向数据

        使用AkShare的北向资金持股数据,按行业聚合计算流向

        缓存策略:
        - 开市时间 (9:30-15:00): 缓存30分钟，且不主动获取新数据（除非force=True）
        - 非开市时间: 缓存4小时，可以获取新数据

        Args:
            use_cache: 是否使用缓存(默认True)
            force: 强制获取数据，即使在开市时间(默认False)

        Returns:
            DataFrame包含行业流向数据
        """
        cache_file = self.cache_path / "north_industry_flow_cache.json"

        # 判断是否在开市时间
        from datetime import datetime
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        is_trading_time = (9 <= current_hour < 15) or (current_hour == 9 and current_minute >= 30)
        is_weekend = now.weekday() >= 5

        if use_cache:
            cached_df = self._load_industry_cache(cache_file)
            if cached_df is not None and not cached_df.empty:
                cache_time = None
                if 'cache_time' in cached_df.columns and len(cached_df) > 0:
                    cache_time = cached_df['cache_time'].iloc[0]

                if is_weekend or not is_trading_time:
                    logger.info(f"非交易时间，使用缓存的行业流向数据(缓存时间: {cache_time or '未知'})")
                elif cache_time:
                    logger.info(f"使用缓存的行业流向数据(缓存时间: {cache_time})")
                else:
                    logger.info("使用缓存的行业流向数据")

                return cached_df.drop(columns=['cache_time'], errors='ignore')

        if (is_weekend or not is_trading_time) and not force:
            logger.warning("⚠️ 非交易时间，北向资金行业数据源不返回实时数据")
            logger.info("💡 建议：1) 等待交易时间(周一至周五 9:30-15:00)再获取")
            logger.info("💡        2) 使用 force=True 强制尝试获取")
            logger.info("💡        3) 查看历史数据: make north-industry-history")
            return pd.DataFrame()

        try:
            logger.info("使用AkShare获取北向资金持股数据...")
            df = self._fetch_industry_flow_from_akshare()

            if df is not None and not df.empty:
                if self._validate_industry_data(df):
                    self._save_industry_cache(cache_file, df)
                    logger.info(f"✅ 成功获取并缓存 {len(df)} 个行业的北向资金流向数据")
                    return df
                else:
                    logger.warning("数据验证失败")
                    return pd.DataFrame()
            else:
                logger.warning("未获取到数据")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取北向资金行业流向数据失败: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _fetch_industry_flow_from_eastmoney(self) -> pd.DataFrame | None:
        """使用东方财富API获取北向资金行业流向数据"""
        import requests

        try:
            logger.info("尝试从东方财富API获取北向资金行业流向数据...")

            # 东方财富北向资金行业流向API
            url = "https://datacenter-web.eastmoney.com/api/data/v1/get"

            params = {
                "reportName": "RPT_HSGT_BOARD_HOLDRANK",
                "columns": "BOARD_NAME,BOARD_CODE,HOLD_MARKET_VALUE,HOLD_MARKET_VALUE_CHANGE,HOLD_RATIO,CHANGE_RATIO",
                "filter": "(MARKET=\"北向\")",
                "pageSize": "100",
                "sortColumns": "HOLD_MARKET_VALUE",
                "sortTypes": "-1"
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.warning(f"东方财富API请求失败: {response.status_code}")
                return None

            data = response.json()

            if not data.get("result") or not data["result"].get("data"):
                logger.warning("东方财富API返回数据格式异常")
                return None

            items = data["result"]["data"]
            records = []

            for item in items:
                industry = item.get("BOARD_NAME") or item.get("BOARD_CODE")
                if not industry:
                    continue

                holding = item.get("HOLD_MARKET_VALUE", 0)
                change = item.get("HOLD_MARKET_VALUE_CHANGE", 0)

                # 转换为亿元（东方财富返回的是元）
                if isinstance(holding, (int, float)):
                    holding = holding / 1e8
                if isinstance(change, (int, float)):
                    change = change / 1e8

                records.append({
                    "industry": industry,
                    "net_inflow": float(change) if isinstance(change, (int, float)) else 0,
                    "today_holding": float(holding) if isinstance(holding, (int, float)) else 0,
                    "change_rate": 0.0,
                    "data_source": "东方财富(API)"
                })

            if records:
                df = pd.DataFrame(records)
                df = df.sort_values("net_inflow", ascending=False)
                logger.info(f"✅ 成功从东方财富API获取 {len(df)} 个行业流向数据")
                return df

        except Exception as e:
            logger.warning(f"东方财富API获取失败: {e}")

        logger.warning("东方财富API获取失败，尝试Playwright...")

        # 如果API失败，尝试使用Playwright
        return self._fetch_industry_flow_from_eastmoney_playwright()

    def _fetch_industry_flow_from_eastmoney_playwright(self) -> pd.DataFrame | None:
        """使用Playwright从东方财富获取北向资金行业流向数据（备用方法）"""
        import json
        import re

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright 未安装，跳过")
            return None

        captured_data = []

        def handle_response(response):
            url = response.url
            # 捕获行业流向相关的API响应
            if response.status == 200 and "datacenter" in url:
                try:
                    body = response.text()
                    # 检查是否包含行业数据
                    if body and ("BOARD_NAME" in body or "INDUSTRY" in body) and len(body) > 100:
                        captured_data.append(body)
                        logger.info("捕获到行业流向数据响应")
                except Exception:
                    pass

        try:
            logger.info("启动 Playwright 浏览器...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.on("response", handle_response)

                logger.info("访问东方财富北向资金行业流向页面...")
                # 访问北向资金行业流向页面
                page.goto("https://data.eastmoney.com/hsgt/hsgtDetail/industry.html",
                         wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(10000)  # 等待10秒让数据加载

                # 如果没有捕获到API响应，尝试从页面直接解析
                if not captured_data:
                    logger.info("尝试从页面直接解析数据...")
                    try:
                        # 等待页面完全加载
                        page.wait_for_timeout(3000)

                        # 查找所有表格
                        tables = page.query_selector_all("table")
                        logger.info(f"找到 {len(tables)} 个表格")

                        records = []

                        # 遍历所有表格，查找包含行业数据的表格
                        for table in tables:
                            rows = table.query_selector_all("tbody tr")
                            if len(rows) < 5:  # 跳过行数太少的表格
                                continue

                            for row in rows[:50]:  # 只取前50行
                                cells = row.query_selector_all("td")
                                if len(cells) >= 3:
                                    # 尝试解析第一列是否是行业名称
                                    industry_text = cells[0].text_content()
                                    industry = industry_text.strip() if industry_text else ""

                                    # 检查是否是有效的行业名称（通常是中文，长度2-10个字符）
                                    if not industry or len(industry) > 20 or not any('\u4e00' <= c <= '\u9fff' for c in industry):
                                        continue

                                    # 尝试解析数字
                                    try:
                                        holding_text = cells[1].text_content()
                                        holding_text = holding_text.strip() if holding_text else "0"
                                        holding = float(holding_text.replace(",", "").replace("亿", "").replace("%", ""))
                                    except (ValueError, AttributeError):
                                        holding = 0

                                    try:
                                        change_text = cells[2].text_content()
                                        change_text = change_text.strip() if change_text else "0"
                                        change = float(change_text.replace(",", "").replace("亿", "").replace("+", "").replace("%", ""))
                                    except (ValueError, AttributeError):
                                        change = 0

                                    if industry:
                                        records.append({
                                            "industry": industry,
                                            "net_inflow": change,
                                            "today_holding": holding,
                                            "change_rate": 0.0,
                                            "data_source": "东方财富(Playwright-页面解析)"
                                        })

                        if records:
                            df = pd.DataFrame(records)
                            df = df.sort_values("net_inflow", ascending=False)
                            logger.info(f"✅ 成功从页面解析 {len(df)} 个行业流向数据")
                            browser.close()
                            return df
                        else:
                            logger.warning("未能从页面解析到有效的行业数据")
                    except Exception as e:
                        logger.warning(f"从页面解析数据失败: {e}")

                browser.close()
                logger.info("页面加载完成")
        except Exception as e:
            logger.warning(f"Playwright 页面加载失败: {e}")
            return None

        if not captured_data:
            logger.warning("未捕获到行业流向数据")
            return None

        # 尝试解析捕获的数据
        for jsonp in captured_data:
            try:
                # 尝试解析JSONP格式
                match = re.search(r"\((.+)\)", jsonp, re.DOTALL)
                if not match:
                    continue

                data = json.loads(match.group(1))

                # 检查数据格式
                if not (data.get("result") and data["result"].get("data")):
                    continue

                items = data["result"]["data"]
                records = []

                # 尝试解析行业流向数据
                for item in items:
                    # 尝试不同的字段名
                    industry = item.get("BOARD_NAME") or item.get("INDUSTRY_NAME") or item.get("行业")
                    if not industry:
                        continue

                    # 尝试获取市值或净流入数据
                    holding = item.get("HOLD_MARKET_VALUE") or item.get("MARKET_VALUE") or 0
                    change = item.get("HOLD_MARKET_VALUE_CHANGE") or item.get("CHANGE_VALUE") or 0

                    # 转换为亿元
                    if isinstance(holding, (int, float)) and abs(holding) > 1e8:
                        holding = holding / 1e8
                    if isinstance(change, (int, float)) and abs(change) > 1e8:
                        change = change / 1e8

                    records.append({
                        "industry": industry,
                        "net_inflow": float(change) if isinstance(change, (int, float)) else 0,
                        "today_holding": float(holding) if isinstance(holding, (int, float)) else 0,
                        "change_rate": 0.0,
                        "data_source": "东方财富(Playwright)"
                    })

                if records:
                    df = pd.DataFrame(records)
                    df = df.sort_values("net_inflow", ascending=False)
                    logger.info(f"✅ 成功从东方财富解析 {len(df)} 个行业流向数据")
                    return df

            except Exception as e:
                logger.debug(f"解析数据失败: {e}")
                continue

        logger.warning("无法解析东方财富北向资金行业数据")
        return None

    def _fetch_industry_flow_from_akshare(self) -> pd.DataFrame | None:
        """从AkShare获取北向资金持股数据并按行业聚合"""
        # 先尝试使用Playwright从东方财富获取
        logger.info("尝试使用Playwright从东方财富获取北向资金行业流向数据...")
        df = self._fetch_industry_flow_from_eastmoney_playwright()
        if df is not None and not df.empty:
            logger.info(f"✅ 成功从东方财富Playwright获取 {len(df)} 个行业数据")
            return df

        logger.warning("东方财富Playwright获取失败，尝试使用AkShare...")

        if not self.akshare:
            logger.warning("AkShare 未安装")
            return None

        max_retries = 2  # 减少重试次数
        for attempt in range(max_retries):
            try:
                import signal
                import time
                from datetime import datetime

                start_time = time.time()

                if attempt > 0:
                    wait_time = attempt * 3  # 减少等待时间
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

                # 判断是否在开市时间
                now = datetime.now()
                current_hour = now.hour
                current_minute = now.minute
                is_trading_time = (9 <= current_hour < 15) or (current_hour == 9 and current_minute >= 30)

                # 设置超时时间（统一使用60秒，因为这个接口确实很慢）
                timeout = 60

                if is_trading_time:
                    logger.info(f"⏳ 正在获取北向资金持股数据(开市时间，超时{timeout}秒)...")
                else:
                    logger.info(f"⏳ 正在获取北向资金持股数据(非开市时间，超时{timeout}秒)...")

                # 使用超时机制
                def timeout_handler(signum, frame):
                    raise TimeoutError("数据获取超时")

                # 设置超时信号（仅在Unix系统上有效）
                try:
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(timeout)
                except (AttributeError, ValueError):
                    # Windows系统不支持SIGALRM，跳过
                    pass

                try:
                    df = self.akshare.stock_hsgt_hold_stock_em(market="北向")

                    # 检查返回的数据是否有效
                    if df is None:
                        logger.warning("AkShare接口返回None")
                        if attempt < max_retries - 1:
                            continue
                        return None
                except (TypeError, KeyError, AttributeError, IndexError, ValueError) as e:
                    logger.warning(f"数据解析错误: {e}")
                    logger.warning("AkShare接口返回数据格式异常，可能是数据源问题")
                    if attempt < max_retries - 1:
                        continue
                    return None
                except Exception as e:
                    import traceback
                    logger.warning(f"数据解析错误: {e}")
                    logger.warning("AkShare接口返回数据格式异常，可能是数据源问题")
                    logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
                    if attempt < max_retries - 1:
                        continue
                    return None
                finally:
                    # 取消超时
                    with contextlib.suppress(AttributeError, ValueError):
                        signal.alarm(0)

                fetch_time = time.time() - start_time
                logger.info(f"✅ 数据获取完成，耗时 {fetch_time:.2f} 秒")

                if df is None:
                    logger.warning("AkShare接口返回None")
                    logger.warning("可能原因：数据源暂时不可用、接口维护或数据格式变化")
                    if attempt < max_retries - 1:
                        continue
                    return None

                if df.empty:
                    logger.warning("未获取到北向资金持股数据（返回空数据）")
                    logger.warning("可能原因：数据源暂时不可用、接口维护或数据格式变化")
                    if attempt < max_retries - 1:
                        continue
                    return None

                logger.info(f"获取到 {len(df)} 条持股数据")

                # 安全地获取列名
                try:
                    columns = df.columns.tolist()
                    logger.debug(f"数据列名: {columns}")
                except Exception as e:
                    logger.warning(f"获取列名失败: {e}")
                    logger.warning("数据格式异常，无法获取列名")
                    if attempt < max_retries - 1:
                        continue
                    return None

                # 检查是否有"所属板块"列
                industry_col = None
                for col in df.columns:
                    if "板块" in col or "行业" in col:
                        industry_col = col
                        break

                if not industry_col:
                    logger.warning("数据中没有行业/板块相关列")
                    return None

                logger.debug(f"使用行业列: {industry_col}")

                # 查找市值相关列
                value_cols = [col for col in df.columns if "市值" in col or "增持" in col]

                if not value_cols:
                    logger.warning("数据中没有市值相关列")
                    return None

                logger.debug(f"找到市值列: {value_cols}")

                # 选择合适的列进行聚合
                # 优先使用包含"今日"的列
                today_col = None
                for col in value_cols:
                    if "今日" in col:
                        today_col = col
                        break

                if not today_col:
                    today_col = value_cols[0]

                logger.info(f"使用市值列: {today_col}")

                # 查找5日增持估计列
                five_day_col = None
                for col in df.columns:
                    if "5日" in col and "市值" in col:
                        five_day_col = col
                        break

                if five_day_col:
                    logger.info(f"找到5日增持列: {five_day_col}")

                # 按行业聚合
                logger.info("正在按行业聚合数据...")
                agg_start = time.time()

                if five_day_col:
                    # 计算5日流向变化
                    industry_flow = df.groupby(industry_col).agg({
                        today_col: "sum",
                        five_day_col: "sum"
                    }).reset_index()

                    # 计算今日持仓和5日前持仓
                    industry_flow.columns = ["industry", "today_holding", "five_day_holding"]

                    # 5日净流入 = 今日持仓 - 5日前持仓
                    industry_flow["net_inflow"] = industry_flow["today_holding"] - industry_flow["five_day_holding"]

                    # 数据单位转换
                    max_val = abs(industry_flow["today_holding"].max())
                    if max_val > 1e9:
                        logger.info("检测到数据单位为'元',正在转换为'亿'...")
                        industry_flow["today_holding"] = industry_flow["today_holding"] / 1e8
                        industry_flow["five_day_holding"] = industry_flow["five_day_holding"] / 1e8
                        industry_flow["net_inflow"] = industry_flow["net_inflow"] / 1e8
                    elif max_val > 1e6:
                        logger.info("检测到数据单位为'万元',正在转换为'亿'...")
                        industry_flow["today_holding"] = industry_flow["today_holding"] / 1e4
                        industry_flow["five_day_holding"] = industry_flow["five_day_holding"] / 1e4
                        industry_flow["net_inflow"] = industry_flow["net_inflow"] / 1e4

                    # 计算变化率（限制范围，避免异常值）
                    # 变化率 = 净流入 / 5日前持仓 * 100
                    # 但如果5日前持仓太小，变化率会异常，需要限制
                    def calc_change_rate(row):
                        if abs(row["five_day_holding"]) < 1:  # 小于1亿，不计算变化率
                            return 0.0
                        rate = row["net_inflow"] / abs(row["five_day_holding"]) * 100
                        # 限制变化率范围在 -100% 到 +1000% 之间
                        return max(-100, min(1000, rate))

                    industry_flow["change_rate"] = industry_flow.apply(calc_change_rate, axis=1)
                else:
                    # 没有5日数据，只显示当前持仓
                    industry_flow = df.groupby(industry_col).agg({
                        today_col: "sum"
                    }).reset_index()

                    industry_flow.columns = ["industry", "net_inflow"]

                    # 数据单位转换
                    max_val = abs(industry_flow["net_inflow"].max())
                    if max_val > 1e9:
                        logger.info("检测到数据单位为'元',正在转换为'亿'...")
                        industry_flow["net_inflow"] = industry_flow["net_inflow"] / 1e8
                    elif max_val > 1e6:
                        logger.info("检测到数据单位为'万元',正在转换为'亿'...")
                        industry_flow["net_inflow"] = industry_flow["net_inflow"] / 1e4

                    industry_flow["change_rate"] = 0.0

                agg_time = time.time() - agg_start
                logger.info(f"✅ 聚合完成,耗时 {agg_time:.2f} 秒")

                # 添加数据源标记
                if five_day_col:
                    industry_flow["data_source"] = "AkShare(5日流向变化)"
                else:
                    industry_flow["data_source"] = "AkShare(北向持股分布)"

                # 排序
                industry_flow = industry_flow.sort_values("net_inflow", ascending=False)

                total_time = time.time() - start_time
                logger.info(f"✅ 成功聚合 {len(industry_flow)} 个行业数据,总耗时 {total_time:.2f} 秒")

                return industry_flow

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"第{attempt + 1}次尝试失败: {error_msg}")

                # 判断错误类型
                if "Connection" in error_msg or "RemoteDisconnected" in error_msg:
                    logger.warning("网络连接问题,将重试...")
                elif "timeout" in error_msg.lower():
                    logger.warning("请求超时,将重试...")
                else:
                    logger.error(f"非网络错误,停止重试: {e}")
                    import traceback
                    traceback.print_exc()
                    return None

                if attempt == max_retries - 1:
                    logger.error(f"所有{max_retries}次尝试均失败")
                    logger.info("💡 北向资金行业数据获取失败是常见问题，建议：")
                    logger.info("   1. 使用缓存数据（如果有）")
                    logger.info("   2. 查看历史数据: make north-industry-history")
                    logger.info("   3. 稍后重试（非开市时间成功率更高）")
                    import traceback
                    traceback.print_exc()
                    return None

        return None

    def _validate_industry_data(self, df: pd.DataFrame) -> bool:
        """验证行业流向数据质量

        Args:
            df: 待验证的DataFrame

        Returns:
            数据是否有效
        """
        if df.empty:
            logger.warning("数据为空")
            return False

        if len(df) < 10:
            logger.warning(f"行业数量过少: {len(df)}")
            return False

        if df['net_inflow'].isna().any():
            logger.warning("存在缺失的净流入数据")
            return False

        if df['change_rate'].isna().any():
            logger.warning("存在缺失的变化率数据")
            return False

        total_inflow = df[df['net_inflow'] > 0]['net_inflow'].sum()
        total_outflow = df[df['net_inflow'] < 0]['net_inflow'].sum()

        # 北向资金总规模可能在几千亿到几万亿,调整验证阈值
        if abs(total_inflow) > 50000 or abs(total_outflow) > 50000:
            logger.warning(f"数据异常: 总流入{total_inflow:.2f}亿, 总流出{total_outflow:.2f}亿 (超过5万亿)")
            return False

        logger.info(f"数据验证通过: {len(df)}个行业, 总流入{total_inflow:.2f}亿, 总流出{total_outflow:.2f}亿")
        return True

    def _load_industry_cache(self, cache_file: Path) -> pd.DataFrame | None:
        """加载行业流向缓存

        Args:
            cache_file: 缓存文件路径

        Returns:
            缓存的DataFrame或None
        """
        if not cache_file.exists():
            return None

        try:
            import json
            from datetime import datetime, timedelta

            with open(cache_file, encoding='utf-8') as f:
                data = json.load(f)

            # 检查数据是否有效
            if not data or 'cache_time' not in data or 'industries' not in data:
                logger.warning("缓存数据格式无效")
                return None

            cache_time_str = data.get('cache_time')
            if not cache_time_str:
                logger.warning("缓存时间缺失")
                return None

            try:
                cache_time = datetime.fromisoformat(cache_time_str)
            except (ValueError, TypeError) as e:
                logger.warning(f"缓存时间格式错误: {e}")
                return None

            # 根据当前时间动态调整缓存有效期
            now = datetime.now()
            current_hour = now.hour

            # 开市时间 (9:30-15:00) 缓存30分钟，非开市时间缓存4小时
            if 9 <= current_hour < 15:
                cache_hours = 0.5  # 30分钟
                cache_desc = "30分钟(开市时间)"
            else:
                cache_hours = 4  # 4小时
                cache_desc = "4小时(非开市时间)"

            if now - cache_time > timedelta(hours=cache_hours):
                logger.info(f"缓存已过期(超过{cache_desc})")
                return None

            df = pd.DataFrame(data['industries'])
            df['cache_time'] = data['cache_time']
            return df

        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            return None

    def _save_industry_cache(self, cache_file: Path, df: pd.DataFrame):
        """保存行业流向缓存

        Args:
            cache_file: 缓存文件路径
            df: 待缓存的DataFrame
        """
        try:
            self.cache_path.mkdir(parents=True, exist_ok=True)

            import json
            from datetime import datetime

            data = {
                'cache_time': datetime.now().isoformat(),
                'industries': df.to_dict('records')
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"缓存已保存: {cache_file}")

        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")


class EnhancedFeatureBuilder:
    """增强特征构建器 - 整合基本面和资金流向特征"""

    def __init__(self):
        self.fundamental_fetcher = FundamentalFetcher()
        self.money_flow_fetcher = MoneyFlowFetcher()
        self._fundamental_cache: dict[str, FundamentalData] = {}
        self._money_flow_cache: dict[str, list[MoneyFlowData]] = {}

    def preload_fundamentals(self, codes: list[str]):
        """预加载基本面数据"""
        logger.info(f"预加载 {len(codes)} 只股票基本面数据...")
        self._fundamental_cache = self.fundamental_fetcher.batch_get_fundamentals(codes)
        logger.info(f"基本面数据加载完成: {len(self._fundamental_cache)} 只")

    def build_fundamental_features(self, code: str) -> dict[str, float]:
        """构建基本面特征"""
        if code not in self._fundamental_cache:
            self._fundamental_cache[code] = self.fundamental_fetcher.get_fundamental(code)

        data = self._fundamental_cache[code]

        return {
            "pe_ratio": data.pe_ratio,
            "pb_ratio": data.pb_ratio,
            "roe": data.roe,
            "revenue_growth": data.revenue_growth,
            "profit_growth": data.profit_growth,
            "debt_ratio": data.debt_ratio,
            "gross_margin": data.gross_margin,
            "net_margin": data.net_margin,
            "log_market_value": np.log1p(data.total_market_value),
            "log_circulating_mv": np.log1p(data.circulating_market_value),
        }

    def build_money_flow_features(self, code: str, lookback: int = 5) -> dict[str, float]:
        """构建资金流向特征"""
        if code not in self._money_flow_cache:
            self._money_flow_cache[code] = self.money_flow_fetcher.get_money_flow(code, days=lookback + 10)

        flows = self._money_flow_cache[code]

        if not flows:
            return {
                "main_net_inflow_mean": 0,
                "main_net_inflow_std": 0,
                "main_net_inflow_ratio_mean": 0,
                "super_net_inflow_mean": 0,
                "big_net_inflow_mean": 0,
                "small_net_inflow_mean": 0,
                "main_inflow_trend": 0,
            }

        recent_flows = flows[-lookback:] if len(flows) >= lookback else flows

        main_inflows = [f.main_net_inflow for f in recent_flows]
        main_ratios = [f.main_net_inflow_ratio for f in recent_flows]
        super_inflows = [f.super_net_inflow for f in recent_flows]
        big_inflows = [f.big_net_inflow for f in recent_flows]
        small_inflows = [f.small_net_inflow for f in recent_flows]

        trend = 0.0
        if len(main_inflows) >= 2:
            trend = float((main_inflows[-1] - main_inflows[0]) / (abs(main_inflows[0]) + 1))

        return {
            "main_net_inflow_mean": float(np.mean(main_inflows)) if main_inflows else 0.0,
            "main_net_inflow_std": float(np.std(main_inflows)) if main_inflows else 0.0,
            "main_net_inflow_ratio_mean": float(np.mean(main_ratios)) if main_ratios else 0.0,
            "super_net_inflow_mean": float(np.mean(super_inflows)) if super_inflows else 0.0,
            "big_net_inflow_mean": float(np.mean(big_inflows)) if big_inflows else 0.0,
            "small_net_inflow_mean": float(np.mean(small_inflows)) if small_inflows else 0.0,
            "main_inflow_trend": trend,
        }

    def build_all_enhanced_features(self, code: str) -> dict[str, float]:
        """构建所有增强特征"""
        features = {}
        features.update(self.build_fundamental_features(code))
        features.update(self.build_money_flow_features(code))
        return features


fundamental_fetcher = FundamentalFetcher()
money_flow_fetcher = MoneyFlowFetcher()
enhanced_feature_builder = EnhancedFeatureBuilder()
