#!/usr/bin/env python3
"""
专门监控中高风险产品（风险 ≥ 中高）
基于1万总额计算
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import os

def load_and_filter_high_risk(total_amount=10000):
    """加载并筛选中高风险产品"""
    data_file = Path('data/sample_data/投资产品.csv')
    df = pd.read_csv(data_file)
    
    # 风险等级映射
    risk_levels = {'低': 1, '中低': 2, '中': 3, '中高': 4, '高': 5}
    
    high_risk_products = []
    for _, row in df.iterrows():
        if pd.notna(row.get('占比(%)')):
            risk = row.get('风险', '未知')
            
            # 只保留中高风险产品
            if risk in ['中高', '高']:
                percentage = float(row['占比(%)'])
                amount = total_amount * percentage / 100
                
                high_risk_products.append({
                    '类型': row['类型'],
                    '名称': row['名称'],
                    '代码': row.get('代码', ''),
                    '风险': risk,
                    '风险等级': risk_levels.get(risk, 0),
                    '占比(%)': percentage,
                    '金额(元)': round(amount, 2),
                    '监控频率': '每日' if risk == '高' else '每周'
                })
    
    # 按风险等级和金额排序
    high_risk_products.sort(key=lambda x: (-x['风险等级'], -x['金额(元)']))
    
    return high_risk_products

def analyze_high_risk_products(products):
    """分析中高风险产品"""
    analysis = {
        'total_products': len(products),
        'by_risk': {'高': [], '中高': []},
        'by_type': {},
        'total_amount': 0,
        'total_percentage': 0,
        'monitoring_plan': {}
    }
    
    for product in products:
        # 按风险分组
        analysis['by_risk'][product['风险']].append(product)
        
        # 按类型统计
        type_name = product['类型']
        if type_name not in analysis['by_type']:
            analysis['by_type'][type_name] = {
                'count': 0,
                'amount': 0,
                'percentage': 0
            }
        analysis['by_type'][type_name]['count'] += 1
        analysis['by_type'][type_name]['amount'] += product['金额(元)']
        analysis['by_type'][type_name]['percentage'] += product['占比(%)']
        
        # 汇总
        analysis['total_amount'] += product['金额(元)']
        analysis['total_percentage'] += product['占比(%)']
    
    # 监控计划
    analysis['monitoring_plan'] = {
        'daily': {
            'count': len(analysis['by_risk']['高']),
            'amount': sum([p['金额(元)'] for p in analysis['by_risk']['高']]),
            'products': analysis['by_risk']['高']
        },
        'weekly': {
            'count': len(analysis['by_risk']['中高']),
            'amount': sum([p['金额(元)'] for p in analysis['by_risk']['中高']]),
            'products': analysis['by_risk']['中高']
        }
    }
    
    return analysis

def generate_high_risk_report(analysis, products):
    """生成中高风险产品报告"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_dir = Path('output/high_risk_reports')
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # 文本报告
    txt_file = report_dir / f'high_risk_report_{timestamp}.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(format_high_risk_report(analysis, products))
    
    # JSON报告
    json_file = report_dir / f'high_risk_report_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'analysis': analysis,
            'products': products,
            'report_time': datetime.now().isoformat(),
            'total_investment': 10000
        }, f, indent=2, ensure_ascii=False)
    
    return txt_file, json_file

def format_high_risk_report(analysis, products):
    """格式化中高风险报告"""
    lines = []
    
    lines.append("🚨 中高风险产品监控报告（风险 ≥ 中高）")
    lines.append("=" * 70)
    lines.append(f"📅 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"💰 基于总额: 10,000元")
    lines.append(f"⚠️ 中高风险产品: {analysis['total_products']}个")
    lines.append(f"📊 中高风险金额: {analysis['total_amount']:.2f}元")
    lines.append(f"📈 中高风险占比: {analysis['total_percentage']:.2f}%")
    lines.append("")
    
    # 每日监控产品（高风险）
    lines.append("一、🚨 每日监控产品（高风险）")
    lines.append("-" * 70)
    lines.append(f"{'名称':35} {'类型':15} {'金额':>10} {'占比':>8}")
    lines.append("-" * 70)
    
    daily_products = analysis['monitoring_plan']['daily']['products']
    if daily_products:
        for product in daily_products[:10]:  # 最多显示10个
            lines.append(
                f"{product['名称'][:34]:35} {product['类型'][:14]:15} "
                f"{product['金额(元)']:>9.2f}元 {product['占比(%)']:>7.2f}%"
            )
        
        if len(daily_products) > 10:
            lines.append(f"... 还有 {len(daily_products)-10} 个高风险产品")
        
        lines.append("-" * 70)
        lines.append(f"📊 高风险总额: {analysis['monitoring_plan']['daily']['amount']:.2f}元")
        lines.append(f"📈 高风险占比: {sum([p['占比(%)'] for p in daily_products]):.2f}%")
    else:
        lines.append("✅ 无高风险产品")
    
    lines.append("")
    
    # 每周检查产品（中高风险）
    lines.append("二、⚠️ 每周检查产品（中高风险）")
    lines.append("-" * 70)
    lines.append(f"{'名称':35} {'类型':15} {'金额':>10} {'占比':>8}")
    lines.append("-" * 70)
    
    weekly_products = analysis['monitoring_plan']['weekly']['products']
    if weekly_products:
        for product in weekly_products[:15]:  # 最多显示15个
            lines.append(
                f"{product['名称'][:34]:35} {product['类型'][:14]:15} "
                f"{product['金额(元)']:>9.2f}元 {product['占比(%)']:>7.2f}%"
            )
        
        if len(weekly_products) > 15:
            lines.append(f"... 还有 {len(weekly_products)-15} 个中高风险产品")
        
        lines.append("-" * 70)
        lines.append(f"📊 中高风险总额: {analysis['monitoring_plan']['weekly']['amount']:.2f}元")
        lines.append(f"📈 中高风险占比: {sum([p['占比(%)'] for p in weekly_products]):.2f}%")
    else:
        lines.append("✅ 无中高风险产品")
    
    lines.append("")
    
    # 按类型汇总
    lines.append("三、📊 中高风险产品类型分布")
    lines.append("-" * 70)
    lines.append(f"{'类型':20} {'数量':>5} {'金额':>12} {'占比':>8}")
    lines.append("-" * 70)
    
    for type_name, stats in sorted(
        analysis['by_type'].items(), 
        key=lambda x: x[1]['amount'], 
        reverse=True
    ):
        lines.append(
            f"{type_name:20} {stats['count']:>5}个 "
            f"{stats['amount']:>10.2f}元 {stats['percentage']:>7.2f}%"
        )
    
    lines.append("")
    
    # 监控行动计划
    lines.append("四、🎯 监控行动计划")
    lines.append("-" * 70)
    
    lines.append("📅 每日监控（高风险产品）:")
    lines.append(f"   数量: {analysis['monitoring_plan']['daily']['count']}个")
    lines.append(f"   金额: {analysis['monitoring_plan']['daily']['amount']:.2f}元")
    lines.append("   行动: 检查价格波动，设置±5%预警")
    lines.append("")
    
    lines.append("📅 每周检查（中高风险产品）:")
    lines.append(f"   数量: {analysis['monitoring_plan']['weekly']['count']}个")
    lines.append(f"   金额: {analysis['monitoring_plan']['weekly']['amount']:.2f}元")
    lines.append("   行动: 评估表现，调整仓位")
    lines.append("")
    
    # 关键产品提醒
    lines.append("五、💡 关键产品提醒")
    lines.append("-" * 70)
    
    if daily_products:
        top_high_risk = daily_products[0]
        lines.append(f"🚨 最高风险产品: {top_high_risk['名称']}")
        lines.append(f"   类型: {top_high_risk['类型']}, 金额: {top_high_risk['金额(元)']:.2f}元")
        lines.append(f"   建议: 重点关注，每日检查")
        lines.append("")
    
    if weekly_products:
        top_medium_high_risk = weekly_products[0]
        lines.append(f"⚠️ 最大中高风险产品: {top_medium_high_risk['名称']}")
        lines.append(f"   类型: {top_medium_high_risk['类型']}, 金额: {top_medium_high_risk['金额(元)']:.2f}元")
        lines.append(f"   建议: 每周评估，考虑调整")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("✅ 中高风险监控报告生成完成")
    lines.append("=" * 70)
    
    return "\n".join(lines)

def main():
    """主函数"""
    print("🚨 中高风险产品监控（风险 ≥ 中高）")
    print("=" * 70)
    
    try:
        # 1. 加载并筛选中高风险产品
        print("📁 加载投资数据...")
        products = load_and_filter_high_risk()
        print(f"   ✅ 找到 {len(products)} 个中高风险产品")
        
        # 2. 分析产品
        print("📈 分析中高风险产品...")
        analysis = analyze_high_risk_products(products)
        print(f"   ✅ 分析完成")
        print(f"      高风险产品: {analysis['monitoring_plan']['daily']['count']}个")
        print(f"      中高风险产品: {analysis['monitoring_plan']['weekly']['count']}个")
        
        # 3. 生成报告
        print("📝 生成监控报告...")
        txt_file, json_file = generate_high_risk_report(analysis, products)
        print(f"   ✅ 报告生成完成")
        print(f"      📄 文本报告: {txt_file}")
        print(f"      📊 JSON数据: {json_file}")
        
        # 4. 显示监控摘要
        print()
        print("📋 监控摘要")
        print("=" * 70)
        
        print(f"💰 基于总额: 10,000元")
        print(f"⚠️ 中高风险产品: {analysis['total_products']}个")
        print(f"📊 中高风险金额: {analysis['total_amount']:.2f}元")
        print(f"📈 中高风险占比: {analysis['total_percentage']:.2f}%")
        print()
        
        print("🚨 每日监控（高风险）:")
        daily = analysis['monitoring_plan']['daily']
        print(f"   产品数: {daily['count']}个")
        print(f"   金额: {daily['amount']:.2f}元")
        if daily['count'] > 0:
            print(f"   最高风险: {daily['products'][0]['名称'][:20]}...")
        
        print()
        
        print("⚠️ 每周检查（中高风险）:")
        weekly = analysis['monitoring_plan']['weekly']
        print(f"   产品数: {weekly['count']}个")
        print(f"   金额: {weekly['amount']:.2f}元")
        if weekly['count'] > 0:
            print(f"   最大金额: {weekly['products'][0]['名称'][:20]}...")
        
        print()
        print("💡 监控建议:")
        print("1. 高风险产品: 每日检查价格波动")
        print("2. 中高风险产品: 每周评估表现")
        print("3. 设置价格预警: ±5%波动时提醒")
        print("4. 定期重评估: 每月检查风险变化")
        
        print()
        print("=" * 70)
        print("🎯 中高风险监控系统已部署")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ 监控失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()