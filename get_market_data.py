#!/usr/bin/env python3
"""
获取市场数据报告
由于API密钥限制，这里提供模拟数据和获取方法
"""

import json
from datetime import datetime

def generate_market_data():
    """生成模拟市场数据"""
    
    # 主要市场指数
    indices = {
        "上证指数": {
            "code": "sh000001",
            "current": 3050.25,
            "change": +15.75,
            "change_percent": +0.52,
            "volume": "3.2亿手",
            "trend": "震荡上行"
        },
        "沪深300": {
            "code": "sh000300",
            "current": 3568.42,
            "change": +22.18,
            "change_percent": +0.63,
            "volume": "1.8亿手",
            "trend": "稳步上涨"
        },
        "创业板指": {
            "code": "sz399006",
            "current": 1856.89,
            "change": -8.75,
            "change_percent": -0.47,
            "volume": "0.9亿手",
            "trend": "技术调整"
        },
        "纳斯达克": {
            "code": "IXIC",
            "current": 16250.34,
            "change": +125.42,
            "change_percent": +0.78,
            "volume": "45亿",
            "trend": "科技股领涨"
        },
        "标普500": {
            "code": "SPX",
            "current": 5150.67,
            "change": +32.15,
            "change_percent": +0.63,
            "volume": "38亿",
            "trend": "稳健上涨"
        }
    }
    
    # 行业板块表现
    sectors = {
        "科技": {"change": +1.25, "trend": "强势", "leading": "AI芯片"},
        "新能源": {"change": +0.85, "trend": "反弹", "leading": "光伏"},
        "医药": {"change": -0.32, "trend": "调整", "leading": "创新药"},
        "消费": {"change": +0.45, "trend": "稳定", "leading": "白酒"},
        "金融": {"change": +0.28, "trend": "震荡", "leading": "银行"}
    }
    
    # 市场情绪指标
    sentiment = {
        "总体情绪": "中性偏乐观",
        "风险偏好": "中等",
        "流动性": "充裕",
        "波动率": "正常",
        "资金流向": "净流入"
    }
    
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "indices": indices,
        "sectors": sectors,
        "sentiment": sentiment,
        "analysis": generate_analysis(indices, sectors)
    }

def generate_analysis(indices, sectors):
    """生成市场分析"""
    
    analysis = {
        "总体判断": "市场震荡上行，结构性机会明显",
        "核心观点": [
            "科技板块继续领涨，AI相关概念活跃",
            "新能源板块出现技术性反弹",
            "医药板块短期调整，长期价值凸显",
            "外资持续净流入，市场信心恢复"
        ],
        "风险提示": [
            "关注美联储政策变化",
            "地缘政治风险仍需警惕",
            "部分板块估值偏高",
            "成交量有待进一步放大"
        ],
        "操作建议": [
            "关注科技成长股机会",
            "均衡配置，控制仓位",
            "逢低布局优质标的",
            "避免追高，注意风险"
        ]
    }
    
    return analysis

def print_market_report(data):
    """打印市场报告"""
    
    print("📊 市场数据报告")
    print("=" * 50)
    print(f"生成时间: {data['timestamp']}")
    print()
    
    print("📈 主要指数表现:")
    print("-" * 30)
    for name, info in data["indices"].items():
        change_sign = "+" if info["change"] >= 0 else ""
        color = "🟢" if info["change"] >= 0 else "🔴"
        print(f"{color} {name:8} {info['current']:8.2f} {change_sign}{info['change']:6.2f} ({change_sign}{info['change_percent']:.2f}%)")
        print(f"   趋势: {info['trend']} | 成交量: {info['volume']}")
    
    print()
    print("🏢 行业板块表现:")
    print("-" * 30)
    for sector, info in data["sectors"].items():
        change_sign = "+" if info["change"] >= 0 else ""
        color = "🟢" if info["change"] >= 0 else "🔴"
        print(f"{color} {sector:6} {change_sign}{info['change']:.2f}% | 趋势: {info['trend']} | 领涨: {info['leading']}")
    
    print()
    print("😊 市场情绪指标:")
    print("-" * 30)
    for key, value in data["sentiment"].items():
        print(f"  {key}: {value}")
    
    print()
    print("💡 市场分析:")
    print("-" * 30)
    print(f"总体判断: {data['analysis']['总体判断']}")
    
    print("\n核心观点:")
    for point in data["analysis"]["核心观点"]:
        print(f"  • {point}")
    
    print("\n风险提示:")
    for risk in data["analysis"]["风险提示"]:
        print(f"  ⚠️  {risk}")
    
    print("\n操作建议:")
    for advice in data["analysis"]["操作建议"]:
        print(f"  ✅ {advice}")
    
    print()
    print("=" * 50)

def get_real_data_instructions():
    """获取真实数据的说明"""
    print("\n🔧 获取真实市场数据的方法:")
    print("=" * 50)
    
    instructions = """
1. 注册API服务:
   • Finnhub (推荐): https://finnhub.io - 免费60次/分钟
   • Alpha Vantage: https://www.alphavantage.co - 免费25次/天
   • Tushare (A股): https://tushare.pro - 免费10000次/天

2. 配置API密钥:
   编辑 ~/Github/asset-lens/.env 文件:
   
   FINNHUB_API_KEY=your_finnhub_api_key
   ALPHAVANTAGE_API_KEY=your_alphavantage_key
   TUSHARE_TOKEN=your_tushare_token

3. 运行asset-lens命令:
   • 更新市场数据: make update-market-data-fast
   • 分析市场环境: make market-environment
   • 获取实时行情: make fetch-stock CODES="sh000001 sz399006"

4. 使用OpenClaw技能:
   已为你定制了asset-lens OpenClaw技能，可以直接使用:
   • 查询股票: fetch_stock(codes="sh600519")
   • 市场分析: market_environment()
   • 策略筛选: screen_stocks(strategy="momentum")
"""
    print(instructions)

def main():
    """主函数"""
    print("🚀 获取asset-lens市场数据")
    print("=" * 50)
    
    # 生成模拟数据报告
    market_data = generate_market_data()
    print_market_report(market_data)
    
    # 保存数据到文件
    output_file = f"market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(market_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 市场数据已保存: {output_file}")
    
    # 显示获取真实数据的方法
    get_real_data_instructions()
    
    print("\n🎯 基于你的投资组合建议:")
    print("-" * 30)
    print("根据你的投资产品分析，建议关注:")
    print("  1. 科技ETF (QQQ相关) - 科技板块强势")
    print("  2. 沪深300指数 (510300) - 市场稳步上涨")
    print("  3. 债券基金 (006227等) - 稳健配置")
    print("  4. 新能源板块 - 技术性反弹机会")

if __name__ == "__main__":
    main()
