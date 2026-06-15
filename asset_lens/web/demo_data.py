"""
Demo 模式模拟数据模块
当 DEMO_MODE 启用时，为所有 API 端点提供模拟数据

使用方法:
    from .demo_data import get_demo_portfolio_summary, get_demo_market_indexes, ...
"""

from datetime import datetime

import random


# ============================================================
# 投资组合模拟数据
# ============================================================

DEMO_PORTFOLIO_SUMMARY = {
    "total_assets": 100890.00,
    "total_profit": 12890.00,
    "total_return": 14.65,
    "position_count": 15,
}

DEMO_PORTFOLIO_ITEMS = [
    # A股
    {"name": "龙腾科技", "code": "demo001", "investment_type": "A股", "risk_level": "高",
     "current_amount": 15000.00, "initial_amount": 12000.00, "profit_amount": 3000.00, "return_rate": 25.00, "annual_return": 20.00},
    {"name": "星辰能源", "code": "demo002", "investment_type": "A股", "risk_level": "高",
     "current_amount": 5400.00, "initial_amount": 6000.00, "profit_amount": -600.00, "return_rate": -10.00, "annual_return": -8.00},
    {"name": "鼎盛银行", "code": "demo003", "investment_type": "A股", "risk_level": "中",
     "current_amount": 8000.00, "initial_amount": 7000.00, "profit_amount": 1000.00, "return_rate": 14.29, "annual_return": 11.40},
    # 基金
    {"name": "远见蓝筹混合", "code": "demo004", "investment_type": "基金", "risk_level": "中高",
     "current_amount": 9600.00, "initial_amount": 9300.00, "profit_amount": 300.00, "return_rate": 3.23, "annual_return": 2.60},
    {"name": "稳健沪深300指数", "code": "demo005", "investment_type": "定投基金", "risk_level": "中",
     "current_amount": 6400.00, "initial_amount": 5600.00, "profit_amount": 800.00, "return_rate": 14.29, "annual_return": 11.40},
    {"name": "卓越制造股票", "code": "demo006", "investment_type": "基金", "risk_level": "高",
     "current_amount": 4500.00, "initial_amount": 3500.00, "profit_amount": 1000.00, "return_rate": 28.57, "annual_return": 22.80},
    {"name": "中证500指数联接", "code": "demo007", "investment_type": "基金", "risk_level": "中",
     "current_amount": 4900.00, "initial_amount": 4700.00, "profit_amount": 200.00, "return_rate": 4.26, "annual_return": 3.40},
    # 债券
    {"name": "国债A", "code": "demo008", "investment_type": "债券", "risk_level": "低",
     "current_amount": 12000.00, "initial_amount": 11600.00, "profit_amount": 400.00, "return_rate": 3.45, "annual_return": 3.40},
    {"name": "信用债A", "code": "demo009", "investment_type": "债券", "risk_level": "中低",
     "current_amount": 9100.00, "initial_amount": 8700.00, "profit_amount": 400.00, "return_rate": 4.60, "annual_return": 4.40},
    # 现金
    {"name": "货币基金A", "code": "demo010", "investment_type": "现金", "risk_level": "低",
     "current_amount": 9400.00, "initial_amount": 9300.00, "profit_amount": 100.00, "return_rate": 1.08, "annual_return": 1.80},
    {"name": "货币基金B", "code": "demo011", "investment_type": "现金", "risk_level": "低",
     "current_amount": 5800.00, "initial_amount": 5800.00, "profit_amount": 0.00, "return_rate": 0.00, "annual_return": 0.00},
    # 黄金
    {"name": "黄金ETF联接", "code": "demo012", "investment_type": "黄金", "risk_level": "中",
     "current_amount": 8500.00, "initial_amount": 7000.00, "profit_amount": 1500.00, "return_rate": 21.43, "annual_return": 18.00},
    # 个人养老金
    {"name": "积极养老Y", "code": "demo013", "investment_type": "个人养老金", "risk_level": "中高",
     "current_amount": 3700.00, "initial_amount": 3500.00, "profit_amount": 200.00, "return_rate": 5.71, "annual_return": 5.20},
    # ETF
    {"name": "中证500ETF", "code": "demo014", "investment_type": "ETF", "risk_level": "高",
     "current_amount": 3900.00, "initial_amount": 3500.00, "profit_amount": 400.00, "return_rate": 11.43, "annual_return": 9.10},
    # 股息基金
    {"name": "环球股息基金", "code": "demo015", "investment_type": "股息基金", "risk_level": "中",
     "current_amount": 5200.00, "initial_amount": 4600.00, "profit_amount": 600.00, "return_rate": 13.04, "annual_return": 10.40},
]


# ============================================================
# 市场指数模拟数据
# ============================================================

DEMO_MARKET_INDEXES = [
    {"code": "sh000001", "name": "上证指数", "price": 3356.72, "change": 12.35, "change_percent": 0.37},
    {"code": "sz399001", "name": "深证成指", "price": 10567.89, "change": 45.67, "change_percent": 0.43},
    {"code": "sz399006", "name": "创业板指", "price": 2123.45, "change": -8.90, "change_percent": -0.42},
    {"code": "sh000300", "name": "沪深300", "price": 3912.45, "change": -5.23, "change_percent": -0.13},
    {"code": "sh000016", "name": "上证50", "price": 2678.90, "change": 8.12, "change_percent": 0.30},
    {"code": "sh000905", "name": "中证500", "price": 5234.56, "change": -12.34, "change_percent": -0.24},
]


# ============================================================
# 股票行情模拟数据
# ============================================================

DEMO_STOCK_QUOTES = {
    "demo001": {"name": "龙腾科技", "base_price": 168.50},
    "demo002": {"name": "星辰能源", "base_price": 21.80},
    "demo003": {"name": "鼎盛银行", "base_price": 35.68},
    "demo004": {"name": "远见蓝筹混合", "base_price": 2.35},
}


# ============================================================
# 策略模拟数据
# ============================================================

DEMO_STRATEGIES = [
    {
        "name": "动量策略",
        "description": "基于价格动量和成交量突破的中短期交易策略，适合趋势明显的市场环境",
        "buy_conditions": 3,
        "sell_conditions": 2,
        "position_size": 0.2,
        "max_positions": 5,
        "stop_loss": -0.08,
        "take_profit": 0.15,
    },
    {
        "name": "价值投资策略",
        "description": "基于基本面分析和估值模型的长期投资策略，注重安全边际和分红收益",
        "buy_conditions": 4,
        "sell_conditions": 3,
        "position_size": 0.15,
        "max_positions": 8,
        "stop_loss": -0.12,
        "take_profit": 0.30,
    },
    {
        "name": "均线策略",
        "description": "基于多周期均线交叉的趋势跟踪策略，适合波动较大的市场",
        "buy_conditions": 2,
        "sell_conditions": 2,
        "position_size": 0.25,
        "max_positions": 4,
        "stop_loss": -0.05,
        "take_profit": 0.10,
    },
    {
        "name": "防御策略",
        "description": "低波动率、高分红的防御性投资策略，适合市场不确定性较高的时期",
        "buy_conditions": 3,
        "sell_conditions": 2,
        "position_size": 0.10,
        "max_positions": 10,
        "stop_loss": -0.06,
        "take_profit": 0.08,
    },
]


# ============================================================
# 风险模拟数据
# ============================================================

DEMO_RISK_SUMMARY = {
    "risk_score": 45,
    "risk_level": "中等",
    "total_position": 583586,
    "warnings": [
        "黄金持仓占比较高（8.5%），注意价格波动风险",
        "A股持仓集中度偏高，贵州茅台单只占比达 15%",
        "现金类资产收益率偏低，考虑适当增配固收产品",
    ],
    "suggestions": [
        "建议适当降低黄金持仓比例至5%以下",
        "可考虑增加债券配置以降低整体风险",
        "建议分散A股持仓至不同行业",
        "可考虑配置部分海外资产以分散地域风险",
    ],
}

DEMO_RISK_INDICATORS = {
    "市场风险": 60,
    "集中度风险": 55,
    "流动性风险": 30,
    "信用风险": 20,
    "操作风险": 25,
}


# ============================================================
# 获取函数
# ============================================================

def get_demo_portfolio_summary() -> dict:
    """获取模拟投资组合摘要"""
    return DEMO_PORTFOLIO_SUMMARY.copy()


def get_demo_portfolio_items(
    investment_type: str | None = None,
    sort_by: str = "return_rate",
    sort_order: str = "desc",
) -> dict:
    """获取模拟投资组合项目列表"""
    items = DEMO_PORTFOLIO_ITEMS.copy()

    if investment_type:
        items = [item for item in items if item["investment_type"] == investment_type]

    reverse = sort_order.lower() == "desc"
    items.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

    return {
        "total": len(items),
        "investment_type": investment_type,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "items": items,
    }


def get_demo_market_indexes() -> list[dict]:
    """获取模拟市场指数数据"""
    # 添加轻微随机波动，让数据看起来更真实
    result = []
    for idx in DEMO_MARKET_INDEXES:
        item = idx.copy()
        item["change"] = round(item["change"] + random.uniform(-0.5, 0.5), 2)
        item["change_percent"] = round(item["change_percent"] + random.uniform(-0.05, 0.05), 2)
        item["price"] = round(item["price"] + item["change"], 2)
        result.append(item)
    return result


def get_demo_stock_quote(code: str) -> dict:
    """获取模拟股票行情"""
    stock_info = DEMO_STOCK_QUOTES.get(code.lower())

    if stock_info:
        base_price = stock_info["base_price"]
        name = stock_info["name"]
    else:
        base_price = round(random.uniform(5, 200), 2)
        name = f"模拟股票{code}"

    change_percent = round(random.uniform(-3, 3), 2)
    prev_close = base_price
    current_price = round(prev_close * (1 + change_percent / 100), 2)
    change_amount = round(current_price - prev_close, 2)
    high = round(max(current_price, prev_close) * (1 + random.uniform(0, 0.02)), 2)
    low = round(min(current_price, prev_close) * (1 - random.uniform(0, 0.02)), 2)
    open_price = round(prev_close * (1 + random.uniform(-0.01, 0.01)), 2)

    return {
        "code": code,
        "name": name,
        "current_price": current_price,
        "change_percent": change_percent,
        "change_amount": change_amount,
        "volume": int(random.uniform(100000, 5000000)),
        "amount": round(random.uniform(1000000, 50000000), 2),
        "high": high,
        "low": low,
        "open": open_price,
        "prev_close": prev_close,
    }


def get_demo_strategies() -> list[dict]:
    """获取模拟策略列表"""
    return [s.copy() for s in DEMO_STRATEGIES]


def get_demo_strategy_detail(strategy_name: str) -> dict | None:
    """获取模拟策略详情"""
    for s in DEMO_STRATEGIES:
        if s["name"] == strategy_name:
            return s.copy()
    return None


def get_demo_risk_summary() -> dict:
    """获取模拟风险摘要"""
    return DEMO_RISK_SUMMARY.copy()


def get_demo_risk_indicators() -> dict:
    """获取模拟风险指标"""
    return DEMO_RISK_INDICATORS.copy()


def get_demo_performance() -> dict:
    """获取模拟投资组合绩效"""
    summary = get_demo_portfolio_summary()
    top_performers = sorted(DEMO_PORTFOLIO_ITEMS, key=lambda x: x["return_rate"], reverse=True)[:5]

    return {
        "summary": summary,
        "top_performers": [
            {"name": item["name"], "return_rate": item["return_rate"], "profit_amount": item["profit_amount"]}
            for item in top_performers
        ],
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
