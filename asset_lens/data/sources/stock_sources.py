"""
Stock data sources for asset-lens.
股票数据源模块 - 处理不同数据源的数据获取
"""

from typing import Any


def fetch_stocks_baostock() -> list[dict[str, Any]]:
    """使用 Baostock 获取A股列表"""
    try:
        import baostock as bs

        lg = bs.login()
        if lg.error_code != "0":
            logger.error(f" Baostock 登录失败: {lg.error_msg}")
            return []

        rs = bs.query_stock_basic()
        if rs.error_code != "0":
            logger.error(f" Baostock 查询失败: {rs.error_msg}")
            bs.logout()
            return []

        data_list = []
        while rs.error_code == "0" and rs.next():
            data_list.append(rs.get_row_data())
        bs.logout()

        if not data_list:
            logger.info(" Baostock: 获取数据为空")
            return []

        stocks = []
        for row in data_list:
            if len(row) < 6:
                continue
            code = str(row[0]) if row[0] else ""
            name = str(row[1]) if row[1] else ""
            stock_type = str(row[4]) if len(row) > 4 else ""
            status = str(row[5]) if len(row) > 5 else ""

            if not code or not name or stock_type != "1" or status != "1":
                continue

            full_code = code.replace(".", "")
            if not (full_code.startswith("sh") or full_code.startswith("sz")):
                continue

            stocks.append(
                {
                    "code": full_code,
                    "name": name,
                    "type": stock_type,
                    "status": status,
                }
            )

        return stocks

    except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
        logger.error(f" Baostock 获取失败: {e}")
        return []


def fetch_stocks_akshare(akshare) -> list[dict[str, Any]]:
    """使用 AkShare 获取A股列表"""
    try:
        logger.info("正在获取A股股票列表(AkShare)...")
        df = akshare.stock_zh_a_spot_em()

        if df is None or df.empty:
            return []

        stocks = []
        for _, row in df.iterrows():
            code = str(row.get("代码", ""))
            name = str(row.get("名称", ""))

            if not code or not name:
                continue

            if code.startswith("6"):
                full_code = f"sh{code}"
            elif code.startswith(("0", "3")):
                full_code = f"sz{code}"
            else:
                continue

            stocks.append(
                {
                    "code": full_code,
                    "name": name,
                    "price": float(row.get("最新价", 0)) if row.get("最新价") else 0,
                    "change_pct": float(row.get("涨跌幅", 0)) if row.get("涨跌幅") else 0,
                    "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                    "amount": float(row.get("成交额", 0)) if row.get("成交额") else 0,
                    "turnover_rate": float(row.get("换手率", 0)) if row.get("换手率") else 0,
                    "pe": float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else 0,
                    "pb": float(row.get("市净率", 0)) if row.get("市净率") else 0,
                    "market_cap": float(row.get("总市值", 0)) if row.get("总市值") else 0,
                }
            )

        return stocks

    except (ValueError, KeyError, ConnectionError) as e:
        logger.error(f" AkShare 获取失败: {e}")
        return []


def fetch_stocks_efinance() -> list[dict[str, Any]]:
    """使用 Efinance 获取A股列表"""
    try:
        logger.info("正在获取A股股票列表(Efinance)...")
        import efinance as ef

        df = ef.stock.get_quote_snapshot()

        if df is None or df.empty:
            return []

        stocks = []
        for _, row in df.iterrows():
            code = str(row.get("股票代码", ""))
            name = str(row.get("股票名称", ""))

            if not code or not name:
                continue

            if code.startswith("6"):
                full_code = f"sh{code}"
            elif code.startswith(("0", "3")):
                full_code = f"sz{code}"
            else:
                continue

            stocks.append(
                {
                    "code": full_code,
                    "name": name,
                    "price": float(row.get("最新价", 0)) if row.get("最新价") else 0,
                    "change_pct": float(row.get("涨跌幅", 0)) if row.get("涨跌幅") else 0,
                    "volume": float(row.get("成交量", 0)) if row.get("成交量") else 0,
                    "amount": float(row.get("成交额", 0)) if row.get("成交额") else 0,
                }
            )

        return stocks

    except (ValueError, KeyError, ConnectionError, ImportError) as e:
        logger.error(f" Efinance 获取失败: {e}")
        return []


def enrich_prices_tencent(stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """使用腾讯财经补充实时价格"""
    try:
        import requests

        if not stocks:
            return stocks

        codes = [s["code"] for s in stocks[:500]]
        url = f"http://qt.gtimg.cn/q={','.join(codes)}"
        headers = {"Referer": "http://gu.qq.com"}

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return stocks

        price_map = {}
        for line in response.text.strip().split("\n"):
            if "~" not in line:
                continue
            parts = line.split("~")
            if len(parts) < 35:
                continue
            code = parts[0].split("=")[0].replace("v_", "")
            try:
                price_map[code] = {
                    "price": float(parts[3]) if parts[3] else 0,
                    "change_pct": float(parts[32]) if parts[32] else 0,
                    "volume": float(parts[36]) if parts[36] else 0,
                    "amount": float(parts[37]) if parts[37] else 0,
                    "turnover_rate": float(parts[38]) if parts[38] else 0,
                    "pe": float(parts[39]) if parts[39] else 0,
                    "pb": float(parts[40]) if parts[40] else 0,
                    "market_cap": float(parts[45]) if parts[45] else 0,
                }
            except (ValueError, IndexError):
                continue

        for stock in stocks:
            code = stock.get("code", "")
            if code in price_map:
                stock.update(price_map[code])

        return stocks

    except (ConnectionError, TimeoutError, ValueError) as e:
        logger.error(f" 腾讯财经补充价格失败: {e}")
        return stocks
