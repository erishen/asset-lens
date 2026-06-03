import logging

import pandas as pd

logger = logging.getLogger(__name__)


class IndustryFlowWebSourcesMixin:
    def _fetch_industry_flow_from_eastmoney(self) -> pd.DataFrame | None:
        import requests

        try:
            logger.info("尝试从东方财富API获取北向资金行业流向数据...")

            url = "https://datacenter-web.eastmoney.com/api/data/v1/get"

            params = {
                "reportName": "RPT_HSGT_BOARD_HOLDRANK",
                "columns": "BOARD_NAME,BOARD_CODE,HOLD_MARKET_VALUE,HOLD_MARKET_VALUE_CHANGE,HOLD_RATIO,CHANGE_RATIO",
                "filter": '(MARKET="北向")',
                "pageSize": "100",
                "sortColumns": "HOLD_MARKET_VALUE",
                "sortTypes": "-1",
            }

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

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

                if isinstance(holding, (int, float)):
                    holding = holding / 1e8
                if isinstance(change, (int, float)):
                    change = change / 1e8

                records.append(
                    {
                        "industry": industry,
                        "net_inflow": float(change) if isinstance(change, (int, float)) else 0,
                        "today_holding": float(holding) if isinstance(holding, (int, float)) else 0,
                        "change_rate": 0.0,
                        "data_source": "东方财富(API)",
                    }
                )

            if records:
                df = pd.DataFrame(records)
                df = df.sort_values("net_inflow", ascending=False)
                logger.info(f"✅ 成功从东方财富API获取 {len(df)} 个行业流向数据")
                return df

        except (ConnectionError, TimeoutError, ValueError, KeyError, OSError) as e:
            logger.warning(f"东方财富API获取失败: {e}")

        logger.warning("东方财富API获取失败，尝试Playwright...")

        return self._fetch_industry_flow_from_eastmoney_playwright()

    def _fetch_industry_flow_from_sina(self) -> pd.DataFrame | None:
        import json
        import re as _re

        try:
            url = "https://vip.stock.finance.sina.com.cn/q/view/newFLJK.php?param=industry"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://finance.sina.com.cn/",
            }

            import requests

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"新浪行业接口请求失败: {response.status_code}")
                return None

            text = response.text
            match = _re.search(r"=\s*(\{.*\})", text, _re.DOTALL)
            if not match:
                logger.warning("新浪行业接口返回格式异常")
                return None

            data = json.loads(match.group(1))
            if not data:
                logger.warning("新浪行业接口返回数据为空")
                return None

            records = []
            for val in data.values():
                fields = val.split(",")
                if len(fields) < 8:
                    continue

                try:
                    industry_name = fields[1]
                    stock_count = int(fields[2])
                    change_pct = float(fields[5])
                    turnover = float(fields[7])

                    turnover_yi = turnover / 1e8

                    sign = 1 if change_pct > 0 else (-1 if change_pct < 0 else 0)
                    net_inflow = turnover_yi * sign

                    records.append(
                        {
                            "industry": industry_name,
                            "net_inflow": net_inflow,
                            "today_holding": turnover_yi,
                            "change_rate": change_pct,
                            "stock_count": stock_count,
                            "data_source": "新浪行业板块",
                        }
                    )
                except (ValueError, IndexError) as e:
                    logger.debug(f"解析行业数据失败: {e}, data={val[:50]}")
                    continue

            if records:
                df = pd.DataFrame(records)
                df = df.sort_values("net_inflow", ascending=False)
                logger.info(f"✅ 新浪行业板块获取 {len(df)} 个行业数据（非交易时间可用）")
                return df

        except (ConnectionError, TimeoutError, json.JSONDecodeError, ValueError, KeyError, OSError) as e:
            logger.warning(f"新浪行业板块获取失败: {e}")

        return None

    def _fetch_industry_flow_from_push2(self) -> pd.DataFrame | None:
        import requests

        try:
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://data.eastmoney.com/",
            }

            params = {
                "pn": "1",
                "pz": "100",
                "po": "1",
                "np": "1",
                "fltt": "2",
                "invt": "2",
                "fid": "f62",
                "fs": "b:BK0824",
                "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87",
                "ut": "433fd2d0e98eaf36ad3d5001f088614d",
            }

            response = requests.get(url, params=params, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"push2接口请求失败: {response.status_code}")
                return None

            data = response.json()
            if not data.get("data") or not data["data"].get("diff"):
                logger.warning("push2接口返回数据为空")
                return None

            items = data["data"]["diff"]
            records = []

            for item in items:
                industry = item.get("f14", "")
                if not industry:
                    continue

                net_inflow = item.get("f62", 0)
                if isinstance(net_inflow, str):
                    try:
                        net_inflow = float(net_inflow)
                    except (ValueError, TypeError):
                        net_inflow = 0

                if abs(net_inflow) > 1e8:
                    net_inflow = net_inflow / 1e8
                elif abs(net_inflow) > 1e4:
                    net_inflow = net_inflow / 1e4

                records.append(
                    {
                        "industry": industry,
                        "net_inflow": float(net_inflow) if isinstance(net_inflow, (int, float)) else 0,
                        "today_holding": 0,
                        "change_rate": float(item.get("f3", 0) or 0),
                        "data_source": "东方财富(push2)",
                    }
                )

            if records:
                df = pd.DataFrame(records)
                df = df.sort_values("net_inflow", ascending=False)
                logger.info(f"✅ push2接口获取 {len(df)} 个行业资金流向数据")
                return df

        except (ConnectionError, TimeoutError, ValueError, KeyError, OSError) as e:
            logger.warning(f"push2接口获取失败: {e}")

        return None

    def _fetch_industry_flow_from_eastmoney_playwright(self) -> pd.DataFrame | None:
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
            if response.status == 200 and "datacenter" in url:
                try:
                    body = response.text()
                    if body and ("BOARD_NAME" in body or "INDUSTRY" in body) and len(body) > 100:
                        captured_data.append(body)
                        logger.info("捕获到行业流向数据响应")
                except (ValueError, OSError) as e:
                    logger.debug(f"忽略异常: {e}")

        try:
            logger.info("启动 Playwright 浏览器...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.on("response", handle_response)

                logger.info("访问东方财富北向资金行业流向页面...")
                page.goto(
                    "https://data.eastmoney.com/hsgt/hsgtDetail/industry.html",
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                page.wait_for_timeout(10000)

                if not captured_data:
                    logger.info("尝试从页面直接解析数据...")
                    try:
                        page.wait_for_timeout(3000)

                        tables = page.query_selector_all("table")
                        logger.info(f"找到 {len(tables)} 个表格")

                        records = []

                        for table in tables:
                            rows = table.query_selector_all("tbody tr")
                            if len(rows) < 5:
                                continue

                            for row in rows[:50]:
                                cells = row.query_selector_all("td")
                                if len(cells) >= 3:
                                    industry_text = cells[0].text_content()
                                    industry = industry_text.strip() if industry_text else ""

                                    if (
                                        not industry
                                        or len(industry) > 20
                                        or not any("\u4e00" <= c <= "\u9fff" for c in industry)
                                    ):
                                        continue

                                    try:
                                        holding_text = cells[1].text_content()
                                        holding_text = holding_text.strip() if holding_text else "0"
                                        holding = float(
                                            holding_text.replace(",", "").replace("亿", "").replace("%", "")
                                        )
                                    except (ValueError, AttributeError):
                                        holding = 0

                                    try:
                                        change_text = cells[2].text_content()
                                        change_text = change_text.strip() if change_text else "0"
                                        change = float(
                                            change_text.replace(",", "")
                                            .replace("亿", "")
                                            .replace("+", "")
                                            .replace("%", "")
                                        )
                                    except (ValueError, AttributeError):
                                        change = 0

                                    if industry:
                                        records.append(
                                            {
                                                "industry": industry,
                                                "net_inflow": change,
                                                "today_holding": holding,
                                                "change_rate": 0.0,
                                                "data_source": "东方财富(Playwright-页面解析)",
                                            }
                                        )

                        if records:
                            df = pd.DataFrame(records)
                            df = df.sort_values("net_inflow", ascending=False)
                            logger.info(f"✅ 成功从页面解析 {len(df)} 个行业流向数据")
                            browser.close()
                            return df
                        else:
                            logger.warning("未能从页面解析到有效的行业数据")
                    except (ValueError, AttributeError, RuntimeError) as e:
                        logger.warning(f"从页面解析数据失败: {e}")

                browser.close()
                logger.info("页面加载完成")
        except (OSError, RuntimeError, ConnectionError) as e:
            logger.warning(f"Playwright 页面加载失败: {e}")
            return None

        if not captured_data:
            logger.warning("未捕获到行业流向数据")
            return None

        for jsonp in captured_data:
            try:
                match = re.search(r"\((.+)\)", jsonp, re.DOTALL)
                if not match:
                    continue

                data = json.loads(match.group(1))

                if not (data.get("result") and data["result"].get("data")):
                    continue

                items = data["result"]["data"]
                records = []

                for item in items:
                    industry = item.get("BOARD_NAME") or item.get("INDUSTRY_NAME") or item.get("行业")
                    if not industry:
                        continue

                    holding = item.get("HOLD_MARKET_VALUE") or item.get("MARKET_VALUE") or 0
                    change = item.get("HOLD_MARKET_VALUE_CHANGE") or item.get("CHANGE_VALUE") or 0

                    if isinstance(holding, (int, float)) and abs(holding) > 1e8:
                        holding = holding / 1e8
                    if isinstance(change, (int, float)) and abs(change) > 1e8:
                        change = change / 1e8

                    records.append(
                        {
                            "industry": industry,
                            "net_inflow": float(change) if isinstance(change, (int, float)) else 0,
                            "today_holding": float(holding) if isinstance(holding, (int, float)) else 0,
                            "change_rate": 0.0,
                            "data_source": "东方财富(Playwright)",
                        }
                    )

                if records:
                    df = pd.DataFrame(records)
                    df = df.sort_values("net_inflow", ascending=False)
                    logger.info(f"✅ 成功从东方财富解析 {len(df)} 个行业流向数据")
                    return df

            except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
                logger.debug(f"解析数据失败: {e}")
                continue

        logger.warning("无法解析东方财富北向资金行业数据")
        return None
