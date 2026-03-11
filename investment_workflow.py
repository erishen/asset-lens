#!/usr/bin/env python3
"""
个人投资监控工作流
基于实际投资数据，定期获取行情并给出建议
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 投资产品数据
INVESTMENT_DATA = {
    "重点基金": [
        {"code": "006227", "name": "南方中债7-10年期国开行债券指数A", "weight": 1.34},
        {"code": "003376", "name": "广发中债7-10年国开债指数A", "weight": 0.97},
        {"code": "013552", "name": "季季享-招商稳乐中短债90天持有期C", "weight": 0.90},
        {"code": "000633", "name": "国泰融丰外延增长灵活配置混合A", "weight": 0.53},
    ],
    "美股投资": [
        {"code": "QQQ", "name": "纳指100ETF", "weight": 0.58},
        {"code": "KO", "name": "可口可乐", "weight": 0.28},
        {"code": "XLE", "name": "能源指数ETF", "weight": 0.14},
    ],
    "指数ETF": [
        {"code": "510500", "name": "中证500ETF嘉实", "weight": 0.09},
        {"code": "510300", "name": "沪深300ETF中金", "weight": 0.02},
    ]
}

def generate_monitoring_plan():
    """生成监控计划"""
    print("🎯 个人投资监控计划")
    print("=" * 50)
    
    total_products = sum(len(products) for products in INVESTMENT_DATA.values())
    print(f"📊 总监控产品数: {total_products}")
    print(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # 按类别显示
    for category, products in INVESTMENT_DATA.items():
        print(f"📈 {category} ({len(products)}个):")
        for product in products:
            print(f"   • {product['code']} - {product['name']} ({product['weight']}%)")
        print()
    
    return total_products

def generate_asset_lens_commands():
    """生成Asset-Lens监控命令"""
    print("🔧 Asset-Lens监控命令")
    print("=" * 50)
    
    # 基金查询命令
    fund_codes = " ".join([p["code"] for p in INVESTMENT_DATA["重点基金"]])
    print(f"1. 基金净值查询:")
    print(f"   make fetch-fund CODES=\"{fund_codes}\"")
    print()
    
    # 美股查询命令（需要转换格式）
    us_stocks = [p["code"] for p in INVESTMENT_DATA["美股投资"]]
    print(f"2. 美股行情查询:")
    print(f"   # 需要美股数据源或使用agent-browser")
    print(f"   监控: {', '.join(us_stocks)}")
    print()
    
    # A股ETF查询
    etf_codes = [f"sh{p['code']}" for p in INVESTMENT_DATA["指数ETF"]]
    print(f"3. A股ETF查询:")
    print(f"   make fetch-stock CODES=\"{' '.join(etf_codes)}\"")
    print()
    
    # 策略筛选
    print(f"4. 投资策略筛选:")
    print(f"   make screen-stocks STRATEGY=momentum LIMIT=10")
    print(f"   make screen-stocks STRATEGY=value LIMIT=10")
    print()
    
    # 市场分析
    print(f"5. 市场环境分析:")
    print(f"   make market-environment")
    print(f"   make predict-etf")
    print()

def generate_daily_schedule():
    """生成每日监控计划"""
    print("⏰ 每日监控时间表")
    print("=" * 50)
    
    schedule = [
        ("09:00", "📊 开盘前准备", "查看隔夜美股、重要新闻"),
        ("09:30", "🔍 A股开盘监控", "监控ETF、重点基金"),
        ("12:00", "📈 午间分析", "上午表现总结、调整建议"),
        ("15:00", "📋 收盘总结", "全日表现、明日展望"),
        ("22:30", "🇺🇸 美股开盘", "监控美股持仓"),
        ("23:59", "📊 日报生成", "生成投资日报"),
    ]
    
    for time, task, desc in schedule:
        print(f"{time} - {task}")
        print(f"     {desc}")
    
    print()

def generate_investment_advice():
    """生成投资建议框架"""
    print("💡 投资建议框架")
    print("=" * 50)
    
    advice_template = """
📊 本周投资分析报告
────────────────────
📅 报告周期: {start_date} 至 {end_date}
📈 市场环境: {market_env}
💰 投资表现: {performance}

🎯 核心建议:
{core_advice}

📋 具体操作:
├── 增持: {buy_list}
├── 减持: {sell_list}
└── 持有: {hold_list}

🔍 关注机会:
├── 行业: {sectors}
└── 策略: {strategies}

⚠️ 风险提示:
{risk_warnings}

📞 后续计划:
{next_steps}
"""
    
    # 填充示例数据
    example_data = {
        "start_date": "2026-03-11",
        "end_date": "2026-03-15",
        "market_env": "震荡市，科技股表现强势",
        "performance": "整体+1.2%，跑赢基准+0.5%",
        "core_advice": "保持债券配置，适度增加科技股 exposure",
        "buy_list": "科技ETF、优质成长股",
        "sell_list": "高估值消费股",
        "hold_list": "核心债券基金、指数ETF",
        "sectors": "人工智能、新能源、医药",
        "strategies": "动量策略、价值挖掘",
        "risk_warnings": "美联储政策变化、地缘政治风险",
        "next_steps": "下周关注一季度财报、政策动向"
    }
    
    print(advice_template.format(**example_data))

def main():
    """主函数"""
    print("\n" + "="*60)
    print("       个人投资组合智能监控系统")
    print("="*60 + "\n")
    
    # 生成各部分内容
    generate_monitoring_plan()
    generate_asset_lens_commands()
    generate_daily_schedule()
    generate_investment_advice()
    
    # 保存配置
    config = {
        "investment_data": INVESTMENT_DATA,
        "monitoring_plan": {
            "total_products": sum(len(products) for products in INVESTMENT_DATA.values()),
            "generated_at": datetime.now().isoformat(),
            "categories": list(INVESTMENT_DATA.keys())
        }
    }
    
    config_file = "investment_monitor_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 配置已保存: {config_file}")
    print(f"📁 项目路径: {os.getcwd()}")
    print(f"🚀 下一步: 运行测试脚本或配置定时任务")

if __name__ == "__main__":
    main()
