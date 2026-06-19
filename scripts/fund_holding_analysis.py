#!/usr/bin/env python3
"""
基金持仓分析脚本 - 分析你投资的基金持有的股票
从投资产品CSV中读取基金代码，从东方财富API获取基金持仓数据
"""

import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.table import Table

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


def load_investment_products() -> list[dict[str, Any]]:
    """从投资产品CSV中加载所有产品"""
    # 首先尝试从 ts-demo/data/latest_money_csv 目录加载
    ts_demo_data_path = "../ts-demo/data"
    
    # 查找最新的 money_csv 目录
    money_csv_dirs = []
    if os.path.exists(ts_demo_data_path):
        for item in os.listdir(ts_demo_data_path):
            if item.startswith("money_csv_") and os.path.isdir(os.path.join(ts_demo_data_path, item)):
                money_csv_dirs.append(item)
    
    if money_csv_dirs:
        # 按日期排序，取最新的
        money_csv_dirs.sort(reverse=True)
        latest_dir = money_csv_dirs[0]
        csv_path = os.path.join(ts_demo_data_path, latest_dir, "投资产品-表格 1.csv")
        
        if os.path.exists(csv_path):
            logger.info("从 ts-demo 加载投资产品数据: %s", csv_path)
        else:
            logger.warning("ts-demo 中未找到投资产品文件，尝试其他路径")
            csv_path = None
    
    # 如果 ts-demo 中没有找到，回退到原来的逻辑
    if not csv_path or not os.path.exists(csv_path):
        data_mode = os.getenv('DATA_MODE', 'sample')
        
        if data_mode == 'real':
            csv_path = "data/real/投资产品.csv"
        else:
            csv_path = "data/sample_data/投资产品-脱敏.csv"

    if not os.path.exists(csv_path):
        logger.error("文件不存在: %s", csv_path)
        return []

    products = []
    with open(csv_path, encoding='utf-8') as f:
        lines = f.readlines()

        header = lines[0].strip().split(',')

        for line in lines[1:]:
            values = line.strip().split(',')
            product = dict(zip(header, values, strict=True))
            
            # 适配ts-demo的CSV格式：基金代码在各个平台列中
            # 平台列：微信,中金,支付宝,富途,招商,港招,交通,浦发,建设,中信,民生,工商,中银
            platform_columns = ['微信', '中金', '支付宝', '富途', '招商', '港招', '交通', '浦发', '建设', '中信', '民生', '工商', '中银']
            
            # 提取基金代码和平台
            fund_code = ''
            platform = ''
            for plat_col in platform_columns:
                if plat_col in header:
                    code = product.get(plat_col, '').strip()
                    if code and code != ',' and code != ' ':
                        fund_code = code
                        platform = plat_col
                        break
            
            # 如果找到了基金代码，添加到产品信息中
            if fund_code:
                product['代码'] = fund_code
                product['平台A'] = platform
            else:
                # 如果没有找到基金代码，跳过这个产品
                continue
            
            products.append(product)

    return products


def get_fund_products() -> list[dict[str, Any]]:
    """筛选基金类型产品"""
    products = load_investment_products()

    fund_products = []
    for p in products:
        product_type = p.get('类型', '')
        name = p.get('名称', '')
        code = p.get('代码', '')

        # 筛选基金类型
        if product_type in ['基金', '混合', '股票', '指数', '债券', 'ETF']:
            fund_products.append({
                'type': product_type,
                'name': name,
                'code': code,
                'amount': p.get('初始金额', ''),
                'platform': p.get('平台A', '') or p.get('平台B', '')
            })

    return fund_products


STOCK_INDUSTRY_CACHE: dict[str, str] = {}


def fetch_stock_industry(stock_code: str) -> str:
    """获取股票所属行业"""
    if stock_code in STOCK_INDUSTRY_CACHE:
        return STOCK_INDUSTRY_CACHE[stock_code]

    try:
        market = "1" if stock_code.startswith("6") else "0"
        url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={market}.{stock_code}&fields=f127"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

            if data and 'data' in data and data['data']:
                industry = str(data['data'].get('f127', ''))
                if industry:
                    STOCK_INDUSTRY_CACHE[stock_code] = industry
                    return industry

        STOCK_INDUSTRY_CACHE[stock_code] = "其他"
        return "其他"

    except Exception:
        STOCK_INDUSTRY_CACHE[stock_code] = "其他"
        return "其他"


def fetch_stock_realtime_price(stock_codes: list[str]) -> dict[str, dict[str, Any]]:
    """批量获取股票实时价格 - 使用腾讯财经API"""
    if not stock_codes:
        return {}

    result = {}

    try:
        codes_param = []
        for code in stock_codes:
            code = normalize_stock_code(code)
            if code.startswith("6"):
                codes_param.append(f"sh{code}")
            elif code.startswith(("0", "3")):
                codes_param.append(f"sz{code}")
            else:
                codes_param.append(f"sh{code}")

        batch_size = 100
        for i in range(0, len(codes_param), batch_size):
            batch = codes_param[i:i+batch_size]
            url = f"https://qt.gtimg.cn/q={','.join(batch)}"

            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })

                no_proxy_handler = urllib.request.ProxyHandler({})
                opener = urllib.request.build_opener(no_proxy_handler)

                with opener.open(req, timeout=15) as response:
                    text = response.read().decode('gbk')

                    for line in text.strip().split('\n'):
                        if not line or '~' not in line:
                            continue

                        parts = line.split('~')
                        if len(parts) < 35:
                            continue

                        code_part = parts[0]
                        if '=' in code_part:
                            code_part = code_part.split('=')[0]
                        code_part = code_part.replace('v_', '').replace('"', '')

                        code = code_part[2:] if code_part.startswith(('sh', 'sz')) else code_part

                        try:
                            price = float(parts[3]) if parts[3] else 0
                            prev_close = float(parts[5]) if parts[5] else 0
                            change = (price - prev_close) / prev_close * 100 if prev_close > 0 else 0
                        except (ValueError, IndexError):
                            price = 0
                            change = 0

                        name = parts[1] if len(parts) > 1 else ''

                        if code and len(code) == 6:
                            result[code] = {
                                'price': price,
                                'change': change,
                                'name': name
                            }
            except Exception as e:
                logger.error("获取价格失败: %s", e)
                continue

        return result

    except Exception as e:
        logger.error("获取价格异常: %s", e)
        return {}


def fetch_stock_industry_batch(stock_codes: list[str]) -> dict[str, str]:
    """批量获取股票行业信息"""
    if not stock_codes:
        return {}

    result = {}

    for code in stock_codes:
        if code in STOCK_INDUSTRY_CACHE:
            result[code] = STOCK_INDUSTRY_CACHE[code]
            continue

        try:
            market = "SH" if code.startswith("6") else "SZ"
            url = f"http://emweb.eastmoney.com/PC_HSF10/CompanySurvey/CompanySurveyAjax?code={market}{code}"

            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })

            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))

                if data and 'jbzl' in data:
                    industry = data['jbzl'].get('sshy', '其他')
                    if industry:
                        result[code] = industry
                        STOCK_INDUSTRY_CACHE[code] = industry
                        continue

            result[code] = '其他'

        except Exception:
            result[code] = '其他'

        time.sleep(0.1)

    return result


def normalize_stock_code(code: str) -> str:
    """标准化股票代码 - 统一为6位数字格式"""
    if not code:
        return ""

    code = str(code).strip()

    if '.' in code:
        parts = code.split('.')
        if len(parts) == 2:
            return parts[1] if len(parts[1]) == 6 else code

    if code.isdigit() and len(code) == 6:
        return code

    if code.startswith(('0.', '1.')):
        return code[2:]

    return code


def fetch_fund_holdings_eastmoney(fund_code: str) -> dict[str, Any] | None:
    """从东方财富API获取基金持仓数据

    支持的基金类型:
    - 普通股票/混合基金
    - QDII基金（投资海外股票）
    - ETF联接基金
    - 指数基金
    """
    url = f'http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={fund_code}&topline=10&rt=0.123456'

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')

            if '暂无数据' in html or len(html) < 100:
                return None

            seen_stocks: dict[str, dict[str, Any]] = {}

            pattern1 = r"<td><a href='//quote\.eastmoney\.com/unify/r/[01]\.(\d{6})'>(\d{6})</a></td><td class='tol'><a[^>]*>([^<]+)</a></td>.*?<td class='tor'>([\d.]+)%</td>"
            matches1 = re.findall(pattern1, html, re.DOTALL)

            for match in matches1:
                stock_code = normalize_stock_code(match[1])
                stock_name = match[2].strip()
                ratio = float(match[3])

                if stock_code and stock_code not in seen_stocks:
                    seen_stocks[stock_code] = {
                        'code': stock_code,
                        'name': stock_name,
                        'ratio': ratio
                    }

            pattern3 = r"<td[^>]*>(\d{6})</td>\s*<td[^>]*>([^<]+)</td>.*?<td[^>]*>([\d.]+)%</td>"
            matches3 = re.findall(pattern3, html, re.DOTALL)

            for match in matches3:
                stock_code = normalize_stock_code(match[0])
                stock_name = match[1].strip()
                ratio = float(match[2])

                if stock_code and stock_code not in seen_stocks and stock_code.isdigit():
                    seen_stocks[stock_code] = {
                        'code': stock_code,
                        'name': stock_name,
                        'ratio': ratio
                    }

            pattern4 = r"<td[^>]*>(\d{5})\.(\w+)</td>\s*<td[^>]*>([^<]+)</td>.*?<td[^>]*>([\d.]+)%</td>"
            matches4 = re.findall(pattern4, html, re.DOTALL)

            for match in matches4:
                market = match[0]
                stock_code = match[1]
                stock_name = match[2].strip()
                ratio = float(match[3])
                full_code = f"{market}.{stock_code}"

                if full_code not in seen_stocks:
                    seen_stocks[full_code] = {
                        'code': full_code,
                        'name': stock_name,
                        'ratio': ratio,
                        'market': '港股' if market == '01' else '美股' if market == '02' else '其他'
                    }

            pattern7 = r"<span data-texch='[^']*'>(\d+)</span></td><td[^>]*><span>([^<]+)</span></td>.*?<td[^>]*>([\d.]+)%</td>"
            matches7 = re.findall(pattern7, html, re.DOTALL)

            for match in matches7:
                stock_code = normalize_stock_code(match[0])
                stock_name = match[1].strip()
                ratio = float(match[2])

                if stock_code and stock_code not in seen_stocks:
                    seen_stocks[stock_code] = {
                        'code': stock_code,
                        'name': stock_name,
                        'ratio': ratio,
                        'market': '海外'
                    }

            holdings = list(seen_stocks.values())
            total_stock_ratio = sum(h['ratio'] for h in holdings)

            if holdings:
                return {
                    'code': fund_code,
                    'holdings': holdings,
                    'stock_count': len(holdings),
                    'total_stock_ratio': total_stock_ratio
                }

            return None

    except Exception:
        return None


def fetch_etf_connect_holdings(fund_code: str, fund_name: str) -> dict[str, Any] | None:
    """获取 ETF 联接基金的持仓数据

    ETF 联接基金主要投资 ETF，所以需要获取其投资的 ETF 的持仓数据

    Args:
        fund_code: 基金代码
        fund_name: 基金名称

    Returns:
        持仓数据
    """

    try:
        url = f'http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={fund_code}&topline=10&rt=0.123456'

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')

            if '暂无数据' in html or len(html) < 100:
                return None

            seen_stocks: dict[str, dict[str, Any]] = {}

            etf_pattern = r"<td[^>]*>(\d{6})</td>\s*<td[^>]*>([^<]+)</td>.*?<td[^>]*>([\d.]+)%</td>"
            etf_matches = re.findall(etf_pattern, html, re.DOTALL)

            for match in etf_matches:
                etf_code = match[0]
                etf_name = match[1].strip()
                ratio = float(match[2])

                if etf_code not in seen_stocks:
                    seen_stocks[etf_code] = {
                        'code': etf_code,
                        'name': etf_name,
                        'ratio': ratio,
                        'market': 'ETF'
                    }

            if seen_stocks:
                holdings = list(seen_stocks.values())
                total_stock_ratio = sum(h['ratio'] for h in holdings)

                return {
                    'code': fund_code,
                    'holdings': holdings,
                    'stock_count': len(holdings),
                    'total_stock_ratio': total_stock_ratio,
                    'is_etf_connect': True
                }

            return None

    except Exception:
        return None


def get_fund_type_description(fund_code: str, fund_name: str) -> str:
    """根据基金代码和名称判断基金类型"""
    fund_name_lower = fund_name.lower()

    if 'qdii' in fund_name_lower or '纳斯达克' in fund_name or '标普' in fund_name or '恒生' in fund_name or '港股' in fund_name or '亚洲' in fund_name or '全球' in fund_name or '环球' in fund_name:
        return 'QDII基金(投资海外)'

    if 'etf' in fund_name_lower and '联接' in fund_name:
        return 'ETF联接基金(主要投资ETF)'

    if 'etf' in fund_name_lower:
        return 'ETF基金'

    if '黄金' in fund_name or '油气' in fund_name or '原油' in fund_name or '商品' in fund_name:
        return '商品基金(投资商品而非股票)'

    if 'lof' in fund_name_lower:
        return 'LOF基金'

    if '债券' in fund_name or '债' in fund_name:
        return '债券基金'

    if '货币' in fund_name:
        return '货币基金'

    if '指数' in fund_name:
        return '指数基金'

    return '混合/股票基金(数据可能未更新)'


def analyze_my_fund_holdings(min_stock_ratio: float = 20.0, exclude_bond: bool = True):
    """分析你投资的基金持有的股票

    Args:
        min_stock_ratio: 最小股票仓位比例筛选，默认20%
        exclude_bond: 是否排除债券类型基金，默认True
    """
    console = Console()

    fund_products = get_fund_products()

    if not fund_products:
        console.print("[red]❌ 没有找到基金产品[/red]")
        return

    console.print("\n[bold cyan]📊 我的基金持仓分析[/bold cyan]")
    console.print(f"找到 {len(fund_products)} 个基金产品")
    filter_desc = []
    if min_stock_ratio > 0:
        filter_desc.append(f"股票仓位 >= {min_stock_ratio}%")
    if exclude_bond:
        filter_desc.append("排除债券类型基金")
    if filter_desc:
        console.print(f"[yellow]筛选条件: {', '.join(filter_desc)}[/yellow]\n")
    else:
        console.print("")

    console.print("[cyan]正在获取基金持仓数据...[/cyan]")

    all_fund_holdings = []
    stock_summary: dict[str, dict] = {}
    fund_stock_ratios: list[dict[str, Any]] = []
    high_ratio_funds: list[dict[str, Any]] = []

    commodity_funds = []

    for fund in fund_products:
        fund_code = fund.get('code', '')
        fund_name = fund.get('name', '')
        fund_type = fund.get('type', '')

        if not fund_code:
            continue

        if exclude_bond and fund_type == '债券':
            console.print(f"  [dim]⏭️ {fund_name} ({fund_code}) - 债券类型，跳过[/dim]")
            continue

        fund_name.lower()
        is_commodity = any(k in fund_name for k in ["黄金", "油气", "原油", "商品"])

        if is_commodity:
            commodity_funds.append({'code': fund_code, 'name': fund_name})
            console.print(f"  [dim]⏭️ {fund_name} ({fund_code}) - 商品基金(投资商品而非股票)，跳过[/dim]")
            continue

        console.print(f"  [cyan]获取 {fund_name} ({fund_code})...[/cyan]")

        holdings_data = fetch_fund_holdings_eastmoney(fund_code)

        if holdings_data and holdings_data.get('holdings'):
            all_fund_holdings.append(holdings_data)
            total_stock_ratio = holdings_data.get('total_stock_ratio', 0)
            fund_stock_ratios.append({
                'name': fund_name,
                'code': fund_code,
                'stock_ratio': total_stock_ratio,
                'stock_count': len(holdings_data['holdings']),
                'type': fund_type
            })

            if total_stock_ratio >= min_stock_ratio:
                high_ratio_funds.append({
                    'name': fund_name,
                    'code': fund_code,
                    'stock_ratio': total_stock_ratio,
                    'stock_count': len(holdings_data['holdings']),
                    'type': fund.get('type', ''),
                    'holdings': holdings_data['holdings']
                })
                console.print(f"    [green]✅ 获取到 {len(holdings_data['holdings'])} 只持仓股票，股票仓位: {total_stock_ratio:.2f}%[/green]")
            else:
                console.print(f"    [dim]⏭️ 股票仓位 {total_stock_ratio:.2f}% < {min_stock_ratio}%，跳过[/dim]")

            if total_stock_ratio >= min_stock_ratio:
                for stock in holdings_data['holdings']:
                    stock_code = normalize_stock_code(stock['code'])
                    stock_name = stock['name']
                    ratio = stock['ratio']

                    if stock_code not in stock_summary:
                        stock_summary[stock_code] = {
                            'name': stock_name,
                            'total_ratio': ratio,
                            'fund_ratios': [(fund_name, ratio)]
                        }
                    else:
                        stock_summary[stock_code]['total_ratio'] += ratio
                        stock_summary[stock_code]['fund_ratios'].append((fund_name, ratio))
        else:
            pass

    if not high_ratio_funds:
        console.print(f"[red]❌ 没有找到股票仓位 >= {min_stock_ratio}% 的基金[/red]")
        console.print("[yellow]💡 提示: 使用 --all 参数查看所有基金，或使用 --min-ratio 调整筛选条件[/yellow]")
        return

    console.print(f"\n[green]✅ 找到 {len(high_ratio_funds)} 只高仓位基金（股票仓位 >= {min_stock_ratio}%）[/green]")

    high_ratio_funds.sort(key=lambda x: x['stock_ratio'], reverse=True)

    table = Table(title=f"📊 高仓位基金汇总（股票仓位 >= {min_stock_ratio}%）", show_lines=False)
    table.add_column("序号", style="cyan", width=6)
    table.add_column("代码", style="cyan", width=10)
    table.add_column("名称", style="white", width=25)
    table.add_column("股票仓位", justify="right", style="yellow", width=10)
    table.add_column("持股数", justify="center", style="green", width=8)
    table.add_column("类型", style="magenta", width=8)

    for i, fund in enumerate(high_ratio_funds, 1):
        stock_ratio = fund['stock_ratio']
        if stock_ratio > 80:
            ratio_style = "[red]"
        elif stock_ratio > 50:
            ratio_style = "[yellow]"
        else:
            ratio_style = "[green]"

        table.add_row(
            str(i),
            fund['code'],
            fund['name'][:22],
            f"{ratio_style}{stock_ratio:.2f}%[/]",
            str(fund['stock_count']),
            fund.get('type', '')
        )

    console.print(table)

    sorted_stocks = sorted(
        stock_summary.items(),
        key=lambda x: x[1]['total_ratio'],
        reverse=True
    )

    console.print("\n[cyan]正在获取股票实时价格和行业信息...[/cyan]")

    top_stock_codes = [code for code, _ in sorted_stocks[:50]]
    price_data = fetch_stock_realtime_price(top_stock_codes)

    console.print("[cyan]正在获取行业信息（可能需要一些时间）...[/cyan]")
    industry_data = fetch_stock_industry_batch(top_stock_codes[:30])

    industry_summary: dict[str, float] = {}
    for stock_code, stock_data in sorted_stocks[:50]:
        industry = industry_data.get(stock_code, '其他')
        stock_data['industry'] = industry
        if industry not in industry_summary:
            industry_summary[industry] = 0.0
        industry_summary[industry] += stock_data['total_ratio']

    sorted_industries = sorted(industry_summary.items(), key=lambda x: x[1], reverse=True)

    table = Table(title="📈 我的基金重仓股票汇总 (持仓比例=各基金持仓比例之和)", show_lines=False)
    table.add_column("排名", style="cyan", width=6)
    table.add_column("代码", style="cyan", width=10)
    table.add_column("名称", style="white", width=10)
    table.add_column("现价", justify="right", style="yellow", width=10)
    table.add_column("涨跌", justify="right", width=10)
    table.add_column("持仓比例", justify="right", style="green", width=10)
    table.add_column("基金数", justify="center", style="blue", width=8)
    table.add_column("行业", style="magenta", width=10)

    for i, (stock_code, stock_data) in enumerate(sorted_stocks[:30], 1):
        price_info = price_data.get(stock_code, {})
        price = price_info.get('price', '-')
        change = price_info.get('change', '-')

        price_str = f"{price:.2f}" if isinstance(price, (int, float)) and price > 0 else "-"

        if isinstance(change, (int, float)):
            if change > 0:
                change_str = f"[red]+{change:.2f}%[/red]"
            elif change < 0:
                change_str = f"[green]{change:.2f}%[/green]"
            else:
                change_str = f"{change:.2f}%"
        else:
            change_str = "-"

        industry = stock_data.get('industry', '其他')
        fund_count = len(stock_data.get('fund_ratios', []))

        table.add_row(
            str(i),
            stock_code,
            stock_data['name'][:8],
            price_str,
            change_str,
            f"{stock_data['total_ratio']:.2f}%",
            str(fund_count),
            industry[:8] if len(industry) > 8 else industry
        )

    console.print(table)

    if sorted_industries:
        table = Table(title="🏭 行业分布统计", show_lines=False)
        table.add_column("排名", style="cyan", width=6)
        table.add_column("行业", style="white", width=20)
        table.add_column("持仓比例", justify="right", style="yellow", width=12)
        table.add_column("占比", justify="right", style="green", width=10)

        total_ratio = sum(industry_summary.values())
        for i, (industry, ratio) in enumerate(sorted_industries[:15], 1):
            percent = (ratio / total_ratio * 100) if total_ratio > 0 else 0
            table.add_row(
                str(i),
                industry,
                f"{ratio:.2f}%",
                f"{percent:.1f}%"
            )

        console.print(table)

    output_dir = "output/fund_analysis"
    os.makedirs(output_dir, exist_ok=True)

    result = {
        'analyze_time': datetime.now().isoformat(),
        'fund_count': len(all_fund_holdings),
        'stock_count': len(stock_summary),
        'industry_distribution': dict(sorted_industries),
        'top_stocks': [
            {
                'code': k,
                'name': v['name'],
                'total_ratio': v['total_ratio'],
                'industry': v.get('industry', '其他'),
                'fund_ratios': v.get('fund_ratios', []),
                'price': price_data.get(k, {}).get('price', 0),
                'change': price_data.get(k, {}).get('change', 0)
            }
            for k, v in sorted_stocks[:50]
        ],
        'fund_holdings': all_fund_holdings,
        'fund_stock_ratios': fund_stock_ratios
    }

    with open(f"{output_dir}/my_fund_holding_analysis.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    console.print(f"\n[green]✅ 分析结果已保存到 {output_dir}/my_fund_holding_analysis.json[/green]")

    with open(f"{output_dir}/my_stock_watchlist.txt", 'w', encoding='utf-8') as f:
        f.write("# 我的基金重仓股票观察列表\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for i, (code, data) in enumerate(sorted_stocks[:50], 1):
            industry = data.get('industry', '其他')
            price_info = price_data.get(code, {})
            price = price_info.get('price', 0)
            change = price_info.get('change', 0)
            f.write(f"{i:2d}. {data['name']}({code}): 持仓比例 {data['total_ratio']:.2f}%, 行业: {industry}, 现价: {price}, 涨跌: {change}%\n")

    console.print(f"[green]✅ 股票观察列表已保存到 {output_dir}/my_stock_watchlist.txt[/green]")


def show_fund_detail(fund_code: str):
    """显示单只基金的持仓明细"""
    console = Console()

    fund_products = get_fund_products()
    fund_name = ""
    for fund in fund_products:
        if fund.get('code', '') == fund_code:
            fund_name = fund.get('name', '')
            break

    if not fund_name:
        console.print(f"[red]❌ 未找到基金代码: {fund_code}[/red]")
        return

    console.print(f"\n[bold cyan]📊 基金持仓明细: {fund_name} ({fund_code})[/bold cyan]\n")

    holdings_data = fetch_fund_holdings_eastmoney(fund_code)

    if not holdings_data or not holdings_data.get('holdings'):
        console.print("[yellow]⚠️ 未获取到持仓数据（可能是债券基金或货币基金）[/yellow]")
        return

    holdings = holdings_data['holdings']
    stock_codes = [h['code'] for h in holdings]
    price_data = fetch_stock_realtime_price(stock_codes)

    console.print("[cyan]正在获取行业信息...[/cyan]")

    table = Table(title=f"📋 {fund_name} 持仓明细", show_lines=False)
    table.add_column("排名", style="cyan", width=6)
    table.add_column("代码", style="cyan", width=10)
    table.add_column("名称", style="white", width=12)
    table.add_column("现价", justify="right", style="yellow", width=10)
    table.add_column("涨跌", justify="right", width=10)
    table.add_column("持仓比例", justify="right", style="green", width=10)
    table.add_column("行业", style="magenta", width=12)

    for i, stock in enumerate(holdings, 1):
        stock_code = stock['code']
        stock_name = stock['name']
        ratio = stock['ratio']

        price_info = price_data.get(stock_code, {})
        price = price_info.get('price', '-')
        change = price_info.get('change', '-')

        price_str = f"{price:.2f}" if isinstance(price, (int, float)) and price > 0 else "-"

        if isinstance(change, (int, float)):
            if change > 0:
                change_str = f"[red]+{change:.2f}%[/red]"
            elif change < 0:
                change_str = f"[green]{change:.2f}%[/green]"
            else:
                change_str = f"{change:.2f}%"
        else:
            change_str = "-"

        industry = fetch_stock_industry(stock_code)
        time.sleep(0.05)

        table.add_row(
            str(i),
            stock_code,
            stock_name[:8],
            price_str,
            change_str,
            f"{ratio:.2f}%",
            industry[:10] if len(industry) > 10 else industry
        )

    console.print(table)


def list_funds():
    """列出所有基金"""
    console = Console()

    fund_products = get_fund_products()

    if not fund_products:
        console.print("[red]❌ 没有找到基金产品[/red]")
        return

    console.print("\n[bold cyan]📋 我投资的基金列表[/bold cyan]")
    console.print(f"共 {len(fund_products)} 个基金产品\n")

    table = Table(show_lines=False)
    table.add_column("序号", style="cyan", width=6)
    table.add_column("代码", style="cyan", width=10)
    table.add_column("名称", style="white", width=30)
    table.add_column("类型", style="yellow", width=8)
    table.add_column("平台", style="green", width=10)

    for i, fund in enumerate(fund_products, 1):
        table.add_row(
            str(i),
            fund.get('code', ''),
            fund.get('name', ''),
            fund.get('type', ''),
            fund.get('platform', '')
        )

    console.print(table)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='基金持仓分析工具')
    parser.add_argument('--detail', '-d', type=str, help='查看单只基金持仓明细，指定基金代码')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有基金')
    parser.add_argument('--analyze', '-a', action='store_true', help='分析基金持仓汇总')
    parser.add_argument('--min-ratio', '-m', type=float, default=20.0, help='最小股票仓位比例筛选（默认20%%）')
    parser.add_argument('--include-bond', action='store_true', help='包含债券类型基金（默认排除）')
    parser.add_argument('--all', action='store_true', help='分析所有基金（包括低仓位和债券基金）')

    args = parser.parse_args()

    if args.detail:
        show_fund_detail(args.detail)
    elif args.list:
        list_funds()
    elif args.analyze:
        analyze_my_fund_holdings(
            min_stock_ratio=args.min_ratio if not args.all else 0,
            exclude_bond=not args.include_bond and not args.all
        )
    else:
        analyze_my_fund_holdings(
            min_stock_ratio=args.min_ratio if not args.all else 0,
            exclude_bond=not args.include_bond and not args.all
        )
