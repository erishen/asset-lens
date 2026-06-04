import logging

import pandas as pd

logger = logging.getLogger(__name__)


class NorthMoneyFlowMixin:
    def get_north_money_flow(self, days: int = 30) -> pd.DataFrame:
        try:
            df = self._get_north_money_flow_eastmoney_api(days)
            if df is not None and not df.empty:
                logger.info(f"东方财富API获取北向资金成功，最新日期: {df['date'].iloc[0]}")
                return df
        except (ConnectionError, TimeoutError, ValueError, KeyError, OSError) as e:
            logger.warning(f"东方财富API获取北向资金失败: {e}")

        try:
            df = self._get_north_money_flow_playwright(days)
            if df is not None and not df.empty:
                logger.info(f"Playwright 获取北向资金成功，最新日期: {df['date'].iloc[-1]}")
                return df
        except (ValueError, KeyError, ConnectionError, OSError, RuntimeError) as e:
            logger.warning(f"Playwright 获取北向资金失败: {e}")

        logger.warning("Playwright 获取失败，尝试 AkShare 回退...")

        if not self.akshare:  # type: ignore[attr-defined]
            return pd.DataFrame()

        try:
            df = self.akshare.stock_hsgt_hist_em(symbol="北向资金")  # type: ignore[attr-defined]
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
        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.warning(f"获取北向资金历史数据失败: {e}")

        return pd.DataFrame()

    def _get_north_money_flow_eastmoney_api(self, days: int = 30) -> pd.DataFrame | None:
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
                    records.append(
                        {
                            "date": str(trade_date),
                            "north_net_inflow": float(net_buy) / 1e8
                            if isinstance(net_buy, (int, float)) and abs(net_buy) > 1e6
                            else float(net_buy or 0),
                            "north_inflow": float(sh_buy + sz_buy) / 1e8
                            if isinstance(sh_buy, (int, float)) and abs(sh_buy) > 1e6
                            else float((sh_buy or 0) + (sz_buy or 0)),
                            "data_source": "东方财富(API)",
                        }
                    )

            if records:
                df = pd.DataFrame(records)
                df = df.sort_values("date", ascending=False)
                return df.head(days)

        except (ConnectionError, TimeoutError, ValueError, KeyError, OSError) as e:
            logger.debug(f"东方财富API获取北向资金数据失败: {e}")

        return None

    def _get_north_money_flow_playwright(self, days: int = 30) -> pd.DataFrame | None:
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
                except (ValueError, OSError) as e:
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
        except (OSError, RuntimeError, ConnectionError) as e:
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

        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
            logger.warning(f"解析北向资金数据失败: {e}")
            return None
