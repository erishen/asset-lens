#!/usr/bin/env python3
"""
分析基金相关的股票投资情况
专门检查高风险基金中的股票持仓
"""

import pandas as pd
import json
from datetime import datetime
import os

def analyze_fund_stock_investments():
    """分析基金中的股票投资情况"""
    print("📊 分析基金相关的股票投资情况")
    print("=" * 60)
    
    # 加载投资数据
    data_path = 'data/sample_data/投资产品-脱敏.csv'
    df = pd.read_csv(data_path)
    
    # 风险等级映射
    risk_levels = {'低': 1, '中低': 2, '中': 3, '中高': 4, '高': 5}
    df['风险等级'] = df['风险'].map(risk_levels)
    
    # 1. 分析高风险基金（风险等级 >= 4）
    high_risk_funds = df[df['风险等级'] >= 4].copy()
    
    print(f"🎯 高风险以上基金数量: {len(high_risk_funds)}")
    print()
    
    # 2. 按基金类型分析
    print("📈 高风险基金类型分布:")
    fund_types = high_risk_funds['类型'].value_counts()
    for fund_type, count in fund_types.items():
        type_df = high_risk_funds[high_risk_funds['类型'] == fund_type]
        total_weight = type_df['占比(%)'].sum()
        print(f"   {fund_type}: {count}个基金，总占比: {total_weight:.2f}%")
    print()
    
    # 3. 分析美股投资
    print("🇺🇸 美股投资分析:")
    us_stocks = high_risk_funds[high_risk_funds['类型'] == '美股（美元）']
    if len(us_stocks) > 0:
        print(f"   美股数量: {len(us_stocks)}")
        print("   具体持仓:")
        for idx, row in us_stocks.iterrows():
            print(f"     • {row['名称']} ({row['代码']})")
            print(f"       风险: {row['风险']}, 占比: {row['占比(%)']:.2f}%")
        print()
    
    # 4. 分析ETF投资
    print("📊 ETF投资分析:")
    etf_funds = high_risk_funds[high_risk_funds['类型'] == 'ETF']
    if len(etf_funds) > 0:
        print(f"   ETF数量: {len(etf_funds)}")
        print("   具体持仓:")
        for idx, row in etf_funds.iterrows():
            print(f"     • {row['名称']} ({row['代码']})")
            print(f"       风险: {row['风险']}, 占比: {row['占比(%)']:.2f}%")
        print()
    
    # 5. 分析基金中的股票持仓（通过基金类型推断）
    print("🏦 基金中的股票持仓分析:")
    
    # 股票型基金（通常包含股票）
    stock_funds = high_risk_funds[high_risk_funds['类型'].isin(['基金', '定投基金', '个人养老金'])]
    if len(stock_funds) > 0:
        print(f"   股票型基金数量: {len(stock_funds)}")
        print("   重点关注基金:")
        for idx, row in stock_funds.iterrows():
            if row['占比(%)'] > 0.1:  # 只显示占比大于0.1%的
                print(f"     • {row['名称']} ({row['代码']})")
                print(f"       类型: {row['类型']}, 风险: {row['风险']}, 占比: {row['占比(%)']:.2f}%")
        print()
    
    # 6. 风险最高的股票投资
    print("⚠️ 风险最高的股票投资:")
    highest_risk = high_risk_funds[high_risk_funds['风险等级'] == 5]
    if len(highest_risk) > 0:
        print("   高风险股票/ETF:")
        for idx, row in highest_risk.iterrows():
            print(f"     • {row['名称']} ({row['代码']})")
            print(f"       类型: {row['类型']}, 占比: {row['占比(%)']:.2f}%")
        print()
    
    # 7. 投资建议
    print("💡 基金股票投资建议:")
    print("   1. 美股监控:")
    if len(us_stocks) > 0:
        print(f"      • 关注{len(us_stocks)}只美股，特别是纳指ETF(QQQ)")
        print("      • 美股交易时间与A股不同，注意时差影响")
    
    print("   2. ETF投资:")
    if len(etf_funds) > 0:
        print(f"      • 持有{len(etf_funds)}只ETF，分散投资")
        print("      • 关注指数ETF的跟踪误差")
    
    print("   3. 基金持仓:")
    if len(stock_funds) > 0:
        print(f"      • {len(stock_funds)}只基金可能包含股票持仓")
        print("      • 建议查看基金季报了解具体股票持仓")
    
    print("   4. 风险管理:")
    print("      • 高风险股票占比不宜过高")
    print("      • 设置止损点，控制单只股票损失")
    print("      • 定期再平衡投资组合")
    
    # 8. 生成监控配置
    print()
    print("📋 生成股票投资监控配置...")
    
    monitor_config = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'analysis_type': 'fund_stock_investment',
        'total_high_risk_funds': len(high_risk_funds),
        'us_stocks': [],
        'etfs': [],
        'stock_funds': [],
        'monitoring_recommendations': []
    }
    
    # 美股配置
    for idx, row in us_stocks.iterrows():
        monitor_config['us_stocks'].append({
            'name': row['名称'],
            'code': row['代码'],
            'risk': row['风险'],
            'weight': float(row['占比(%)']),
            'monitoring_frequency': 'daily',
            'alert_threshold': 3.0
        })
    
    # ETF配置
    for idx, row in etf_funds.iterrows():
        monitor_config['etfs'].append({
            'name': row['名称'],
            'code': row['代码'],
            'risk': row['风险'],
            'weight': float(row['占比(%)']),
            'monitoring_frequency': 'daily',
            'alert_threshold': 2.5
        })
    
    # 股票型基金配置
    for idx, row in stock_funds.iterrows():
        if row['占比(%)'] > 0.1:
            monitor_config['stock_funds'].append({
                'name': row['名称'],
                'code': row['代码'],
                'type': row['类型'],
                'risk': row['风险'],
                'weight': float(row['占比(%)']),
                'monitoring_frequency': 'weekly',
                'suggestion': '查看基金季报了解具体股票持仓'
            })
    
    # 监控建议
    monitor_config['monitoring_recommendations'] = [
        {
            'priority': 'high',
            'action': '每日监控美股和ETF价格',
            'reason': '高风险、波动大'
        },
        {
            'priority': 'medium',
            'action': '每周检查基金表现',
            'reason': '通过基金间接投资股票'
        },
        {
            'priority': 'low',
            'action': '每月查看基金持仓报告',
            'reason': '了解基金的具体股票持仓'
        }
    ]
    
    # 保存配置
    config_dir = 'config/fund_stock_analysis'
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = f"{config_dir}/fund_stock_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(monitor_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 分析配置已保存: {config_file}")
    print("=" * 60)
    
    return monitor_config

def generate_stock_investment_report(config):
    """生成股票投资报告"""
    report = []
    report.append("📊 基金股票投资分析报告")
    report.append("=" * 60)
    report.append(f"📅 报告时间: {config['timestamp']}")
    report.append(f"🎯 分析类型: {config['analysis_type']}")
    report.append(f"📈 高风险基金总数: {config['total_high_risk_funds']}")
    report.append("")
    
    # 美股分析
    if config['us_stocks']:
        report.append("🇺🇸 美股直接投资:")
        for stock in config['us_stocks']:
            report.append(f"   • {stock['name']} ({stock['code']})")
            report.append(f"     风险: {stock['risk']}, 占比: {stock['weight']:.2f}%")
            report.append(f"     监控频率: {stock['monitoring_frequency']}, 预警阈值: {stock['alert_threshold']}%")
        report.append("")
    
    # ETF分析
    if config['etfs']:
        report.append("📊 ETF投资:")
        for etf in config['etfs']:
            report.append(f"   • {etf['name']} ({etf['code']})")
            report.append(f"     风险: {etf['risk']}, 占比: {etf['weight']:.2f}%")
        report.append("")
    
    # 基金分析
    if config['stock_funds']:
        report.append("🏦 股票型基金（间接股票投资）:")
        for fund in config['stock_funds']:
            report.append(f"   • {fund['name']} ({fund['code']})")
            report.append(f"     类型: {fund['type']}, 风险: {fund['risk']}, 占比: {fund['weight']:.2f}%")
        report.append("")
    
    # 监控建议
    report.append("🎯 监控建议:")
    for rec in config['monitoring_recommendations']:
        priority_emoji = '⚠️' if rec['priority'] == 'high' else '🔸' if rec['priority'] == 'medium' else '🔹'
        report.append(f"   {priority_emoji} {rec['action']}")
        report.append(f"      原因: {rec['reason']}")
    report.append("")
    
    # 投资策略
    report.append("💡 投资策略建议:")
    report.append("   1. 直接股票投资（美股）:")
    report.append("      • 关注宏观经济和公司财报")
    report.append("      • 设置止损止盈点")
    report.append("      • 注意汇率风险")
    report.append("")
    report.append("   2. ETF投资:")
    report.append("      • 分散投资，降低个股风险")
    report.append("      • 关注指数成分股变化")
    report.append("      • 考虑定投降低择时风险")
    report.append("")
    report.append("   3. 基金投资（间接股票）:")
    report.append("      • 查看基金季报了解持仓")
    report.append("      • 关注基金经理变动")
    report.append("      • 评估基金费用和业绩")
    report.append("")
    
    report.append("🚨 风险提示:")
    report.append("   • 股票投资波动较大，需承受较高风险")
    report.append("   • 美股受美国经济政策和国际关系影响")
    report.append("   • 基金投资存在管理风险和风格漂移")
    report.append("   • 建议高风险投资不超过总资产的20%")
    report.append("=" * 60)
    
    return "\n".join(report)

def main():
    """主函数"""
    # 分析基金股票投资
    config = analyze_fund_stock_investments()
    
    # 生成报告
    report = generate_stock_investment_report(config)
    
    # 输出报告
    print(report)
    
    # 保存报告
    report_dir = 'output/fund_stock_reports'
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = f"{report_dir}/fund_stock_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📁 报告已保存: {report_file}")

if __name__ == "__main__":
    main()