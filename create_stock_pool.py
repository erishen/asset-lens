#!/usr/bin/env python3
"""
创建模拟股票池
基于Asset-Lens策略建立可供参考的股票池
"""

import json
import pandas as pd
from datetime import datetime
import os
import random

def create_simulated_stock_pool():
    """创建模拟股票池"""
    print("📊 创建模拟股票池（供参考和模拟交易）")
    print("=" * 60)
    
    # 模拟A股股票列表（实际使用时可以从AkShare获取）
    simulated_stocks = [
        # 价值型股票（低估值、稳健）
        {"code": "sh600519", "name": "贵州茅台", "industry": "白酒", "market_cap": 20000, "pe": 25.5},
        {"code": "sh601318", "name": "中国平安", "industry": "保险", "market_cap": 8000, "pe": 8.2},
        {"code": "sh600036", "name": "招商银行", "industry": "银行", "market_cap": 9000, "pe": 6.5},
        {"code": "sz000858", "name": "五粮液", "industry": "白酒", "market_cap": 6000, "pe": 18.3},
        {"code": "sh600276", "name": "恒瑞医药", "industry": "医药", "market_cap": 3000, "pe": 35.2},
        
        # 成长型股票（高增长、动量）
        {"code": "sz300750", "name": "宁德时代", "industry": "新能源", "market_cap": 7000, "pe": 42.8},
        {"code": "sz002475", "name": "立讯精密", "industry": "消费电子", "market_cap": 2500, "pe": 28.6},
        {"code": "sh688981", "name": "中芯国际", "industry": "半导体", "market_cap": 4000, "pe": 55.3},
        {"code": "sz300124", "name": "汇川技术", "industry": "工业自动化", "market_cap": 1800, "pe": 32.7},
        {"code": "sz002594", "name": "比亚迪", "industry": "新能源汽车", "market_cap": 6500, "pe": 38.9},
        
        # 红利型股票（高股息、稳定）
        {"code": "sh601988", "name": "中国银行", "industry": "银行", "market_cap": 9500, "pe": 5.2},
        {"code": "sh601328", "name": "交通银行", "industry": "银行", "market_cap": 3800, "pe": 4.8},
        {"code": "sh600028", "name": "中国石化", "industry": "石油化工", "market_cap": 5500, "pe": 7.3},
        {"code": "sh601857", "name": "中国石油", "industry": "石油", "market_cap": 12000, "pe": 9.1},
        {"code": "sh600900", "name": "长江电力", "industry": "电力", "market_cap": 4800, "pe": 16.5},
        
        # 反转型股票（超跌、困境）
        {"code": "sz000725", "name": "京东方A", "industry": "面板", "market_cap": 1500, "pe": 12.8},
        {"code": "sz000100", "name": "TCL科技", "industry": "家电", "market_cap": 800, "pe": 9.5},
        {"code": "sh600703", "name": "三安光电", "industry": "LED", "market_cap": 900, "pe": 18.2},
        {"code": "sz002241", "name": "歌尔股份", "industry": "消费电子", "market_cap": 700, "pe": 15.7},
        {"code": "sz002456", "name": "欧菲光", "industry": "光学", "market_cap": 300, "pe": 22.4},
        
        # 科技成长股
        {"code": "sz300782", "name": "卓胜微", "industry": "射频芯片", "market_cap": 500, "pe": 45.6},
        {"code": "sh688111", "name": "金山办公", "industry": "软件", "market_cap": 1200, "pe": 52.3},
        {"code": "sz300454", "name": "深信服", "industry": "网络安全", "market_cap": 600, "pe": 38.9},
        {"code": "sz300496", "name": "中科创达", "industry": "智能汽车", "market_cap": 400, "pe": 47.2},
        {"code": "sh688012", "name": "中微公司", "industry": "半导体设备", "market_cap": 800, "pe": 58.7},
    ]
    
    # 添加模拟数据
    for stock in simulated_stocks:
        # 随机生成一些技术指标
        stock['price'] = round(random.uniform(10, 300), 2)
        stock['change_percent'] = round(random.uniform(-5, 5), 2)
        stock['volume_ratio'] = round(random.uniform(0.5, 3.0), 2)
        stock['turnover_rate'] = round(random.uniform(1, 10), 2)
        stock['amplitude_20d'] = round(random.uniform(2, 8), 2)
        stock['pb_ratio'] = round(random.uniform(1, 5), 2)
        stock['dividend_yield'] = round(random.uniform(1, 5), 2) if stock['pe'] < 15 else round(random.uniform(0, 2), 2)
        
        # 计算策略得分
        stock['value_score'] = calculate_value_score(stock)
        stock['momentum_score'] = calculate_momentum_score(stock)
        stock['dividend_score'] = calculate_dividend_score(stock)
        stock['reversal_score'] = calculate_reversal_score(stock)
        
        # 总得分
        stock['total_score'] = round((stock['value_score'] + stock['momentum_score'] + 
                                     stock['dividend_score'] + stock['reversal_score']) / 4, 2)
    
    return simulated_stocks

def calculate_value_score(stock):
    """计算价值策略得分"""
    score = 0
    
    # 低PE得分
    if stock['pe'] < 20:
        score += 30
    elif stock['pe'] < 30:
        score += 20
    elif stock['pe'] < 40:
        score += 10
    
    # 合理市值得分
    if 50 <= stock['market_cap'] <= 500:
        score += 20
    elif 500 < stock['market_cap'] <= 2000:
        score += 15
    else:
        score += 5
    
    # 稳定换手得分
    if 1 <= stock['turnover_rate'] <= 5:
        score += 20
    elif 0.5 <= stock['turnover_rate'] < 1 or 5 < stock['turnover_rate'] <= 8:
        score += 10
    
    # 上涨趋势得分
    if stock['change_percent'] > 0:
        score += 15
    elif stock['change_percent'] > -2:
        score += 10
    else:
        score += 5
    
    # 非ST得分（假设都不是ST）
    score += 15
    
    return min(score, 100)

def calculate_momentum_score(stock):
    """计算动量策略得分"""
    score = 0
    
    # 放量突破得分
    if stock['volume_ratio'] > 2:
        score += 25
    elif stock['volume_ratio'] > 1.5:
        score += 15
    else:
        score += 5
    
    # 上涨动能得分
    if 3 <= stock['change_percent'] <= 9:
        score += 25
    elif 1 <= stock['change_percent'] < 3 or 9 < stock['change_percent'] <= 12:
        score += 15
    else:
        score += 5
    
    # 活跃换手得分
    if 5 <= stock['turnover_rate'] <= 15:
        score += 20
    elif 3 <= stock['turnover_rate'] < 5 or 15 < stock['turnover_rate'] <= 20:
        score += 10
    
    # 中等市值得分
    if 30 <= stock['market_cap'] <= 300:
        score += 15
    elif 10 <= stock['market_cap'] < 30 or 300 < stock['market_cap'] <= 500:
        score += 10
    
    # 均线多头得分（模拟）
    if stock['change_percent'] > 0 and stock['volume_ratio'] > 1:
        score += 15
    else:
        score += 5
    
    return min(score, 100)

def calculate_dividend_score(stock):
    """计算红利策略得分"""
    score = 0
    
    # 低PE得分
    if stock['pe'] < 15:
        score += 25
    elif stock['pe'] < 20:
        score += 15
    elif stock['pe'] < 25:
        score += 10
    
    # 大市值得分
    if stock['market_cap'] > 200:
        score += 25
    elif stock['market_cap'] > 100:
        score += 15
    else:
        score += 5
    
    # 低换手得分
    if stock['turnover_rate'] < 3:
        score += 20
    elif stock['turnover_rate'] < 5:
        score += 10
    
    # 稳定波动得分
    if stock['amplitude_20d'] < 5:
        score += 15
    elif stock['amplitude_20d'] < 8:
        score += 10
    
    # 小幅下跌得分
    if -3 <= stock['change_percent'] <= 0:
        score += 15
    elif 0 < stock['change_percent'] <= 3:
        score += 10
    else:
        score += 5
    
    return min(score, 100)

def calculate_reversal_score(stock):
    """计算反转策略得分"""
    score = 0
    
    # 超跌得分（模拟5日涨跌幅）
    five_day_change = stock['change_percent'] * 2  # 模拟5日涨跌幅
    if five_day_change < -15:
        score += 30
    elif five_day_change < -10:
        score += 20
    elif five_day_change < -5:
        score += 10
    
    # 低估值得分
    if stock['pb_ratio'] < 1.5:
        score += 25
    elif stock['pb_ratio'] < 2:
        score += 15
    elif stock['pb_ratio'] < 3:
        score += 10
    
    # 底部放量得分
    if stock['volume_ratio'] > 1.5:
        score += 20
    elif stock['volume_ratio'] > 1.2:
        score += 10
    
    # 小市值得分
    if stock['market_cap'] < 100:
        score += 15
    elif stock['market_cap'] < 200:
        score += 10
    
    # 非ST得分
    score += 10
    
    return min(score, 100)

def generate_stock_pool_report(stocks):
    """生成股票池报告"""
    print(f"📈 股票池规模: {len(stocks)}只股票")
    print()
    
    # 按策略筛选
    value_stocks = sorted([s for s in stocks if s['value_score'] >= 70], 
                         key=lambda x: x['value_score'], reverse=True)[:10]
    momentum_stocks = sorted([s for s in stocks if s['momentum_score'] >= 70], 
                           key=lambda x: x['momentum_score'], reverse=True)[:10]
    dividend_stocks = sorted([s for s in stocks if s['dividend_score'] >= 70], 
                           key=lambda x: x['dividend_score'], reverse=True)[:10]
    reversal_stocks = sorted([s for s in stocks if s['reversal_score'] >= 70], 
                           key=lambda x: x['reversal_score'], reverse=True)[:10]
    
    # 按总得分筛选
    top_stocks = sorted(stocks, key=lambda x: x['total_score'], reverse=True)[:15]
    
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_stocks': len(stocks),
        'by_strategy': {
            'value': value_stocks,
            'momentum': momentum_stocks,
            'dividend': dividend_stocks,
            'reversal': reversal_stocks
        },
        'top_stocks': top_stocks,
        'strategy_summary': {
            'value_count': len(value_stocks),
            'momentum_count': len(momentum_stocks),
            'dividend_count': len(dividend_stocks),
            'reversal_count': len(reversal_stocks)
        }
    }
    
    return report

def print_stock_pool_report(report):
    """打印股票池报告"""
    print("📊 股票池策略分析报告")
    print("=" * 60)
    print(f"📅 生成时间: {report['timestamp']}")
    print(f"📈 总股票数: {report['total_stocks']}")
    print()
    
    # 策略统计
    print("🎯 策略筛选结果:")
    print("-" * 40)
    summary = report['strategy_summary']
    print(f"  价值策略 (value): {summary['value_count']}只 ≥70分")
    print(f"  动量策略 (momentum): {summary['momentum_count']}只 ≥70分")
    print(f"  红利策略 (dividend): {summary['dividend_count']}只 ≥70分")
    print(f"  反转策略 (reversal): {summary['reversal_count']}只 ≥70分")
    print()
    
    # 价值策略股票
    if report['by_strategy']['value']:
        print("💰 价值策略推荐 (低估值、稳健增长):")
        print("-" * 40)
        for stock in report['by_strategy']['value'][:5]:
            print(f"  • {stock['name']} ({stock['code']})")
            print(f"    行业: {stock['industry']}, 市值: {stock['market_cap']}亿")
            print(f"    PE: {stock['pe']}, 价值得分: {stock['value_score']}/100")
        print()
    
    # 动量策略股票
    if report['by_strategy']['momentum']:
        print("🚀 动量策略推荐 (成长强势股):")
        print("-" * 40)
        for stock in report['by_strategy']['momentum'][:5]:
            print(f"  • {stock['name']} ({stock['code']})")
            print(f"    行业: {stock['industry']}, 涨跌幅: {stock['change_percent']}%")
            print(f"    量比: {stock['volume_ratio']}, 动量得分: {stock['momentum_score']}/100")
        print()
    
    # 红利策略股票
    if report['by_strategy']['dividend']:
        print("💵 红利策略推荐 (高股息、稳定):")
        print("-" * 40)
        for stock in report['by_strategy']['dividend'][:5]:
            print(f"  • {stock['name']} ({stock['code']})")
            print(f"    行业: {stock['industry']}, 股息率: {stock['dividend_yield']}%")
            print(f"    PE: {stock['pe']}, 红利得分: {stock['dividend_score']}/100")
        print()
    
    # 反转策略股票
    if report['by_strategy']['reversal']:
        print("🔄 反转策略推荐 (超跌、困境反转):")
        print("-" * 40)
        for stock in report['by_strategy']['reversal'][:5]:
            print(f"  • {stock['name']} ({stock['code']})")
            print(f"    行业: {stock['industry']}, PB: {stock['pb_ratio']}")
            print(f"    涨跌幅: {stock['change_percent']}%, 反转得分: {stock['reversal_score']}/100")
        print()
    
    # 综合推荐
    print("🏆 综合推荐 (总得分最高):")
    print("-" * 40)
    for i, stock in enumerate(report['top_stocks'][:10], 1):
        print(f"  {i:2d}. {stock['name']} ({stock['code']})")
        print(f"      行业: {stock['industry']}, 市值: {stock['market_cap']}亿")
        print(f"      总得分: {stock['total_score']}/100")
        print(f"      策略得分: V{stock['value_score']} M{stock['momentum_score']} D{stock['dividend_score']} R{stock['reversal_score']}")
    print()
    
    # 投资建议
    print("💡 模拟交易建议:")
    print("-" * 40)
    print("  1. 价值策略组合:")
    print("     • 适合长期投资，注重安全边际")
    print("     • 单只仓位: 10%，最大10只")
    print("     • 止损: -10%，止盈: 30%")
    print()
    print("  2. 动量策略组合:")
    print("     • 适合中期趋势跟踪")
    print("     • 单只仓位: 8%，最大15只")
    print("     • 止损: -8%，止盈: 15%")
    print()
    print("  3. 红利策略组合:")
    print("     • 适合稳健收益，现金流投资")
    print("     • 单只仓位: 15%，最大8只")
    print("     • 止损: -8%，止盈: 15%")
    print()
    print("  4. 反转策略组合:")
    print("     • 适合短线抄底，高风险高收益")
    print("     • 单只仓位: 5%，最大20只")
    print("     • 止损: -5%，止盈: 20%")
    print()
    print("  5. 混合策略组合:")
    print("     • 价值: 40%仓位")
    print("     • 动量: 30%仓位")
    print("     • 红利: 20%仓位")
    print("     • 反转: 10%仓位")
    print("     • 分散风险，平衡收益")
    print()
    
    print("🚨 风险提示:")
    print("-" * 40)
    print("  • 模拟交易仅供参考，不构成投资建议")
    print("  • 实际投资需考虑市场环境和个人风险承受能力")
    print("  • 建议先进行模拟交易，熟悉策略后再实盘")
    print("=" * 60)

def save_stock_pool_data(report, stocks):
    """保存股票池数据"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 创建目录
    os.makedirs('data/stock_pool', exist_ok=True)
    os.makedirs('config/stock_strategy', exist_ok=True)
    os.makedirs('output/stock_reports', exist_ok=True)
    
    # 保存完整股票数据
    stock_data_file = f"data/stock_pool/stock_pool_{timestamp}.json"
    with open(stock_data_file, 'w', encoding='utf-8') as f:
        json.dump(stocks, f, indent=2, ensure_ascii=False)
    
    # 保存策略报告
    report_file = f"output/stock_reports/stock_pool_report_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 保存策略配置
    strategy_config = {
        'timestamp': report['timestamp'],
        'strategies': {
            'value': {
                'description': '价值投资策略 - 低估值、稳健增长',
                'position_size': '10%',
                'max_positions': 10,
                'stop_loss': '-10%',
                'take_profit': '30%',
                'recommended_stocks': [{'code': s['code'], 'name': s['name'], 'score': s['value_score']} 
                                      for s in report['by_strategy']['value'][:5]]
            },
            'momentum': {
                'description': '成长动量策略 - 追踪强势股',
                'position_size': '8%',
                'max_positions': 15,
                'stop_loss': '-8%',
                'take_profit': '15%',
                'recommended_stocks': [{'code': s['code'], 'name': s['name'], 'score': s['momentum_score']} 
                                      for s in report['by_strategy']['momentum'][:5]]
            },
            'dividend': {
                'description': '稳健红利策略 - 高股息、低波动',
                'position_size': '15%',
                'max_positions': 8,
                'stop_loss': '-8%',
                'take_profit': '15%',
                'recommended_stocks': [{'code': s['code'], 'name': s['name'], 'score': s['dividend_score']} 
                                      for s in report['by_strategy']['dividend'][:5]]
            },
            'reversal': {
                'description': '困境反转策略 - 抄底超跌股',
                'position_size': '5%',
                'max_positions': 20,
                'stop_loss': '-5%',
                'take_profit': '20%',
                'recommended_stocks': [{'code': s['code'], 'name': s['name'], 'score': s['reversal_score']} 
                                      for s in report['by_strategy']['reversal'][:5]]
            }
        },
        'top_recommendations': [
            {'rank': i+1, 'code': s['code'], 'name': s['name'], 'total_score': s['total_score']}
            for i, s in enumerate(report['top_stocks'][:10])
        ]
    }
    
    config_file = f"config/stock_strategy/strategy_config_{timestamp}.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(strategy_config, f, indent=2, ensure_ascii=False)
    
    # 生成文本报告
    text_report = generate_text_report(report)
    text_report_file = f"output/stock_reports/stock_pool_report_{timestamp}.txt"
    with open(text_report_file, 'w', encoding='utf-8') as f:
        f.write(text_report)
    
    print(f"📁 股票数据已保存: {stock_data_file}")
    print(f"📁 策略报告已保存: {report_file}")
    print(f"📁 策略配置已保存: {config_file}")
    print(f"📁 文本报告已保存: {text_report_file}")
    
    return stock_data_file, report_file, config_file, text_report_file

def generate_text_report(report):
    """生成文本格式报告"""
    lines = []
    lines.append("📊 Asset-Lens 股票池策略分析报告")
    lines.append("=" * 60)
    lines.append(f"📅 生成时间: {report['timestamp']}")
    lines.append(f"📈 总股票数: {report['total_stocks']}")
    lines.append("")
    
    # 策略统计
    lines.append("🎯 策略筛选结果:")
    lines.append("-" * 40)
    summary = report['strategy_summary']
    lines.append(f"  价值策略 (value): {summary['value_count']}只 ≥70分")
    lines.append(f"  动量策略 (momentum): {summary['momentum_count']}只 ≥70分")
    lines.append(f"  红利策略 (dividend): {summary['dividend_count']}只 ≥70分")
    lines.append(f"  反转策略 (reversal): {summary['reversal_count']}只 ≥70分")
    lines.append("")
    
    # 综合推荐
    lines.append("🏆 综合推荐股票 (总得分最高):")
    lines.append("-" * 40)
    for i, stock in enumerate(report['top_stocks'][:15], 1):
        lines.append(f"  {i:2d}. {stock['name']} ({stock['code']})")
        lines.append(f"      行业: {stock['industry']}, 市值: {stock['market_cap']}亿")
        lines.append(f"      价格: {stock['price']}元, 涨跌幅: {stock['change_percent']}%")
        lines.append(f"      总得分: {stock['total_score']}/100")
        lines.append(f"      策略得分: V{stock['value_score']} M{stock['momentum_score']} D{stock['dividend_score']} R{stock['reversal_score']}")
        lines.append("")
    
    # 投资建议
    lines.append("💡 模拟交易配置建议:")
    lines.append("-" * 40)
    lines.append("  1. 保守型配置 (风险厌恶):")
    lines.append("     • 价值策略: 50%仓位")
    lines.append("     • 红利策略: 40%仓位")
    lines.append("     • 动量策略: 10%仓位")
    lines.append("")
    lines.append("  2. 平衡型配置 (风险中性):")
    lines.append("     • 价值策略: 40%仓位")
    lines.append("     • 动量策略: 30%仓位")
    lines.append("     • 红利策略: 20%仓位")
    lines.append("     • 反转策略: 10%仓位")
    lines.append("")
    lines.append("  3. 进取型配置 (风险偏好):")
    lines.append("     • 动量策略: 50%仓位")
    lines.append("     • 反转策略: 30%仓位")
    lines.append("     • 价值策略: 20%仓位")
    lines.append("")
    
    lines.append("🚨 风险提示:")
    lines.append("-" * 40)
    lines.append("  • 本报告基于模拟数据，仅供参考")
    lines.append("  • 实际投资需进行充分研究和风险评估")
    lines.append("  • 建议先进行3-6个月模拟交易验证策略")
    lines.append("  • 投资有风险，入市需谨慎")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def main():
    """主函数"""
    # 创建模拟股票池
    stocks = create_simulated_stock_pool()
    
    # 生成报告
    report = generate_stock_pool_report(stocks)
    
    # 打印报告
    print_stock_pool_report(report)
    
    # 保存数据
    stock_data_file, report_file, config_file, text_report_file = save_stock_pool_data(report, stocks)
    
    print("✅ 股票池创建完成！")
    print("=" * 60)
    
    return report

if __name__ == "__main__":
    main()
