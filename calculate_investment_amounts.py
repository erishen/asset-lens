#!/usr/bin/env python3
"""
投资金额计算脚本
按总投资金额和占比计算各个产品的具体投资金额
"""

import pandas as pd
import json
from datetime import datetime
import os

def calculate_investment_amounts(total_investment=10000):
    """计算投资金额"""
    print(f"💰 投资金额计算（总投资: {total_investment:,}元）")
    print("=" * 60)
    
    # 加载投资数据
    data_path = 'data/sample_data/投资产品-脱敏.csv'
    df = pd.read_csv(data_path)
    
    # 计算每个产品的投资金额
    df['投资金额(元)'] = df['占比(%)'] / 100 * total_investment
    
    # 风险等级映射
    risk_levels = {'低': 1, '中低': 2, '中': 3, '中高': 4, '高': 5}
    df['风险等级'] = df['风险'].map(risk_levels)
    
    # 按投资金额排序
    df_sorted = df.sort_values('投资金额(元)', ascending=False)
    
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_investment': total_investment,
        'total_products': len(df),
        'investment_summary': {},
        'by_type': {},
        'by_risk': {},
        'important_products': [],
        'high_risk_products': [],
        'monitoring_suggestions': []
    }
    
    # 总投资汇总
    total_amount = df['投资金额(元)'].sum()
    results['investment_summary'] = {
        'total_amount': float(total_amount),
        'average_per_product': float(total_amount / len(df)),
        'max_investment': float(df['投资金额(元)'].max()),
        'min_investment': float(df['投资金额(元)'].min())
    }
    
    # 按类型汇总
    type_summary = df.groupby('类型').agg({
        '占比(%)': 'sum',
        '投资金额(元)': 'sum',
        '名称': 'count'
    }).sort_values('投资金额(元)', ascending=False)
    
    for type_name, row in type_summary.iterrows():
        results['by_type'][type_name] = {
            'percentage': float(row['占比(%)']),
            'amount': float(row['投资金额(元)']),
            'count': int(row['名称'])
        }
    
    # 按风险等级汇总
    risk_summary = df.groupby('风险').agg({
        '占比(%)': 'sum',
        '投资金额(元)': 'sum',
        '名称': 'count'
    }).sort_values('投资金额(元)', ascending=False)
    
    for risk_level, row in risk_summary.iterrows():
        results['by_risk'][risk_level] = {
            'percentage': float(row['占比(%)']),
            'amount': float(row['投资金额(元)']),
            'count': int(row['名称'])
        }
    
    # 重点产品（投资金额 > 总投资的0.5%）
    threshold = total_investment * 0.005  # 0.5%
    important_products = df[df['投资金额(元)'] > threshold].sort_values('投资金额(元)', ascending=False)
    
    for idx, row in important_products.iterrows():
        results['important_products'].append({
            'name': row['名称'],
            'code': row['代码'],
            'type': row['类型'],
            'risk': row['风险'],
            'percentage': float(row['占比(%)']),
            'amount': float(row['投资金额(元)']),
            'monitoring_priority': 'high' if row['投资金额(元)'] > total_investment * 0.01 else 'medium'
        })
    
    # 高风险产品（风险等级 ≥ 4）
    high_risk = df[df['风险等级'] >= 4].sort_values(['风险等级', '投资金额(元)'], ascending=[False, False])
    
    for idx, row in high_risk.iterrows():
        results['high_risk_products'].append({
            'name': row['名称'],
            'code': row['代码'],
            'type': row['类型'],
            'risk': row['风险'],
            'risk_level': int(row['风险等级']),
            'percentage': float(row['占比(%)']),
            'amount': float(row['投资金额(元)']),
            'monitoring_frequency': 'daily' if row['风险等级'] == 5 else 'weekly'
        })
    
    # 监控建议
    results['monitoring_suggestions'] = [
        {
            'priority': 'high',
            'suggestion': f'重点关注投资金额 > {threshold:.0f}元的产品',
            'reason': '金额较大，对整体收益影响显著'
        },
        {
            'priority': 'high',
            'suggestion': '每日监控高风险产品（风险等级5）',
            'reason': '波动大，需要密切跟踪'
        },
        {
            'priority': 'medium',
            'suggestion': '每周检查中高风险产品（风险等级4）',
            'reason': '中等波动，需要定期评估'
        },
        {
            'priority': 'low',
            'suggestion': '每月回顾低风险产品',
            'reason': '波动小，长期持有为主'
        }
    ]
    
    return df_sorted, results

def generate_investment_report(df, results, show_details=True):
    """生成投资金额报告"""
    total_investment = results['total_investment']
    
    report = []
    report.append(f"💰 投资金额分析报告（总投资: {total_investment:,}元）")
    report.append("=" * 60)
    report.append(f"📅 报告时间: {results['timestamp']}")
    report.append(f"📊 总产品数: {results['total_products']}")
    report.append(f"💰 总投资金额: {results['investment_summary']['total_amount']:.2f}元")
    report.append(f"📈 平均每产品: {results['investment_summary']['average_per_product']:.2f}元")
    report.append("")
    
    # 按类型汇总
    report.append("🏷️ 按投资类型汇总:")
    report.append("-" * 40)
    for type_name, data in results['by_type'].items():
        report.append(f"  {type_name:20} {data['percentage']:6.2f}% → {data['amount']:8.2f}元 ({data['count']}个)")
    report.append("")
    
    # 按风险等级汇总
    report.append("⚠️ 按风险等级汇总:")
    report.append("-" * 40)
    for risk_level, data in results['by_risk'].items():
        report.append(f"  {risk_level:10} {data['percentage']:6.2f}% → {data['amount']:8.2f}元 ({data['count']}个)")
    report.append("")
    
    # 重点产品
    if results['important_products']:
        report.append("🎯 重点监控产品（投资金额较大）:")
        report.append("-" * 40)
        for product in results['important_products']:
            priority_emoji = '⚠️' if product['monitoring_priority'] == 'high' else '🔸'
            report.append(f"  {priority_emoji} {product['name']} ({product['code']})")
            report.append(f"     类型: {product['type']}, 风险: {product['risk']}")
            report.append(f"     占比: {product['percentage']:.2f}% → 金额: {product['amount']:.2f}元")
        report.append("")
    
    # 高风险产品
    if results['high_risk_products']:
        report.append("🔥 高风险产品监控（风险等级 ≥ 4）:")
        report.append("-" * 40)
        
        # 高风险（等级5）
        high_risk_5 = [p for p in results['high_risk_products'] if p['risk_level'] == 5]
        if high_risk_5:
            report.append("  ⚠️ 高风险（等级5）:")
            for product in high_risk_5:
                report.append(f"    • {product['name']} ({product['code']})")
                report.append(f"      金额: {product['amount']:.2f}元, 监控: {product['monitoring_frequency']}")
        
        # 中高风险（等级4）
        high_risk_4 = [p for p in results['high_risk_products'] if p['risk_level'] == 4]
        if high_risk_4:
            report.append("  🔸 中高风险（等级4）:")
            # 只显示金额较大的
            for product in high_risk_4[:5]:
                if product['amount'] > total_investment * 0.001:  # 大于0.1%
                    report.append(f"    • {product['name']} ({product['code']})")
                    report.append(f"      金额: {product['amount']:.2f}元, 监控: {product['monitoring_frequency']}")
            if len(high_risk_4) > 5:
                report.append(f"    等{len(high_risk_4)-5}个中高风险产品...")
        report.append("")
    
    # 监控建议
    report.append("💡 监控建议:")
    report.append("-" * 40)
    for suggestion in results['monitoring_suggestions']:
        priority_emoji = '⚠️' if suggestion['priority'] == 'high' else '🔸' if suggestion['priority'] == 'medium' else '🔹'
        report.append(f"  {priority_emoji} {suggestion['suggestion']}")
        report.append(f"      原因: {suggestion['reason']}")
    report.append("")
    
    # 详细产品列表（可选）
    if show_details:
        report.append("📋 详细产品列表（按投资金额排序）:")
        report.append("-" * 40)
        for idx, row in df.head(15).iterrows():
            amount = row['投资金额(元)']
            risk_emoji = '⚠️' if row['风险等级'] >= 4 else '🔸' if row['风险等级'] == 3 else '🔹'
            report.append(f"  {risk_emoji} {row['名称']:30} {row['占比(%)']:6.2f}% → {amount:8.2f}元")
        if len(df) > 15:
            report.append(f"  等{len(df)-15}个产品...")
        report.append("")
    
    # 投资策略建议
    report.append("🎯 投资策略建议:")
    report.append("-" * 40)
    report.append("  1. 金额分配:")
    report.append(f"     • 重点关注: 投资金额 > {total_investment*0.005:.0f}元的产品")
    report.append(f"     • 适度关注: 投资金额 {total_investment*0.001:.0f}-{total_investment*0.005:.0f}元")
    report.append(f"     • 一般关注: 投资金额 < {total_investment*0.001:.0f}元")
    report.append("")
    report.append("  2. 风险控制:")
    report.append("     • 高风险产品总投资不宜超过总投资的20%")
    report.append("     • 单只高风险产品不宜超过总投资的5%")
    report.append("     • 设置止损点：单只产品最大损失不超过投资金额的10%")
    report.append("")
    report.append("  3. 监控频率:")
    report.append("     • 每日: 高风险、大金额产品")
    report.append("     • 每周: 中高风险、中等金额产品")
    report.append("     • 每月: 低风险、小金额产品")
    report.append("")
    
    report.append("=" * 60)
    
    return "\n".join(report)

def save_results(results, report_text):
    """保存结果"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    total_investment = results['total_investment']
    
    # 保存配置
    config_dir = f'config/investment_{total_investment}'
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = f"{config_dir}/investment_{total_investment}_{timestamp}.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 保存报告
    report_dir = f'output/investment_reports/{total_investment}'
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = f"{report_dir}/investment_report_{total_investment}_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return config_file, report_file

def main(total_investment=10000):
    """主函数"""
    # 计算投资金额
    df, results = calculate_investment_amounts(total_investment)
    
    # 生成报告
    report = generate_investment_report(df, results, show_details=True)
    
    # 输出报告
    print(report)
    
    # 保存结果
    config_file, report_file = save_results(results, report)
    
    print(f"📁 配置已保存: {config_file}")
    print(f"📁 报告已保存: {report_file}")
    
    return results

if __name__ == "__main__":
    import sys
    
    # 可以指定总投资金额
    if len(sys.argv) > 1:
        try:
            total_investment = float(sys.argv[1])
            main(total_investment)
        except ValueError:
            print(f"❌ 参数错误: {sys.argv[1]}，请输入有效的数字")
            sys.exit(1)
    else:
        main()  # 默认1万元