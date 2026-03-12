#!/usr/bin/env python3
"""
基于1万总额的投资监控
使用asset-lens项目的工具和逻辑
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import os

def load_investment_data():
    """加载投资数据"""
    data_file = Path('data/sample_data/投资产品.csv')
    df = pd.read_csv(data_file)
    return df

def calculate_amounts(df, total_amount=10000):
    """计算每个产品的金额"""
    investments = []
    
    for _, row in df.iterrows():
        if pd.notna(row.get('占比(%)')):
            percentage = float(row['占比(%)'])
            amount = total_amount * percentage / 100
            
            investments.append({
                '类型': row['类型'],
                '名称': row['名称'],
                '代码': row.get('代码', ''),
                '风险': row.get('风险', '未知'),
                '占比(%)': percentage,
                '金额(元)': round(amount, 2)
            })
    
    return investments

def analyze_investments(investments):
    """分析投资组合"""
    analysis = {
        'total_amount': 10000,
        'total_products': len(investments),
        'total_percentage': sum([i['占比(%)'] for i in investments]),
        'by_type': {},
        'by_risk': {},
        'focus_products': [],
        'high_risk_products': []
    }
    
    # 按类型分析
    for inv in investments:
        type_name = inv['类型']
        if type_name not in analysis['by_type']:
            analysis['by_type'][type_name] = {
                'count': 0, 
                'amount': 0, 
                'percentage': 0
            }
        analysis['by_type'][type_name]['count'] += 1
        analysis['by_type'][type_name]['amount'] += inv['金额(元)']
        analysis['by_type'][type_name]['percentage'] += inv['占比(%)']
    
    # 按风险分析
    risk_mapping = {'低': 1, '中低': 2, '中': 3, '中高': 4, '高': 5}
    for inv in investments:
        risk = inv['风险']
        if risk not in analysis['by_risk']:
            analysis['by_risk'][risk] = {
                'count': 0, 
                'amount': 0, 
                'percentage': 0,
                'level': risk_mapping.get(risk, 0)
            }
        analysis['by_risk'][risk]['count'] += 1
        analysis['by_risk'][risk]['amount'] += inv['金额(元)']
        analysis['by_risk'][risk]['percentage'] += inv['占比(%)']
    
    # 重点关注产品（金额 > 50元）
    analysis['focus_products'] = [
        inv for inv in investments 
        if inv['金额(元)'] >= 50
    ]
    
    # 高风险产品（风险 >= 中高）
    analysis['high_risk_products'] = [
        inv for inv in investments 
        if inv['风险'] in ['中高', '高']
    ]
    
    return analysis

def generate_report(analysis, investments):
    """生成报告"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_dir = Path('output/investment_reports/10000')
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # 文本报告
    txt_file = report_dir / f'investment_report_10000_{timestamp}.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(format_text_report(analysis, investments))
    
    # JSON报告
    json_file = report_dir / f'investment_report_10000_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'analysis': analysis,
            'investments': investments,
            'report_time': datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    return txt_file, json_file

def format_text_report(analysis, investments):
    """格式化文本报告"""
    lines = []
    
    lines.append("📊 基于1万总额的投资监控报告")
    lines.append("=" * 60)
    lines.append(f"📅 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"💰 假设总额: {analysis['total_amount']}元")
    lines.append(f"📈 产品数量: {analysis['total_products']}个")
    lines.append(f"📊 占比总和: {analysis['total_percentage']:.2f}%")
    lines.append("")
    
    # 按类型汇总
    lines.append("一、📈 按投资类型汇总")
    lines.append("-" * 60)
    lines.append(f"{'类型':20} {'数量':>5} {'金额':>12} {'占比':>8}")
    lines.append("-" * 60)
    
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
    
    # 按风险汇总
    lines.append("二、⚠️ 按风险等级汇总")
    lines.append("-" * 60)
    lines.append(f"{'风险等级':10} {'数量':>5} {'金额':>12} {'占比':>8}")
    lines.append("-" * 60)
    
    risk_order = ['高', '中高', '中', '中低', '低']
    for risk in risk_order:
        if risk in analysis['by_risk']:
            stats = analysis['by_risk'][risk]
            lines.append(
                f"{risk:10} {stats['count']:>5}个 "
                f"{stats['amount']:>10.2f}元 {stats['percentage']:>7.2f}%"
            )
    
    lines.append("")
    
    # 重点关注产品
    lines.append("三、🎯 重点关注产品（金额 ≥ 50元）")
    lines.append("-" * 60)
    lines.append(f"{'名称':30} {'类型':15} {'风险':6} {'金额':>10} {'占比':>8}")
    lines.append("-" * 60)
    
    for inv in sorted(
        analysis['focus_products'], 
        key=lambda x: x['金额(元)'], 
        reverse=True
    )[:15]:  # 只显示前15个
        lines.append(
            f"{inv['名称'][:29]:30} {inv['类型'][:14]:15} "
            f"{inv['风险']:6} {inv['金额(元)']:>9.2f}元 {inv['占比(%)']:>7.2f}%"
        )
    
    if len(analysis['focus_products']) > 15:
        lines.append(f"... 还有 {len(analysis['focus_products'])-15} 个产品")
    
    lines.append("")
    
    # 高风险产品
    if analysis['high_risk_products']:
        lines.append("四、🚨 高风险产品监控（风险 ≥ 中高）")
        lines.append("-" * 60)
        lines.append(f"{'名称':30} {'类型':15} {'风险':6} {'金额':>10}")
        lines.append("-" * 60)
        
        for inv in analysis['high_risk_products']:
            lines.append(
                f"{inv['名称'][:29]:30} {inv['类型'][:14]:15} "
                f"{inv['风险']:6} {inv['金额(元)']:>9.2f}元"
            )
        
        lines.append("")
    
    # 监控建议
    lines.append("五、💡 监控建议")
    lines.append("-" * 60)
    
    suggestions = []
    
    # 基于风险的建议
    if '高' in analysis['by_risk']:
        high_risk_amount = analysis['by_risk']['高']['amount']
        suggestions.append(f"高风险产品: {high_risk_amount:.2f}元，建议每日监控")
    
    if '中高' in analysis['by_risk']:
        medium_high_amount = analysis['by_risk']['中高']['amount']
        suggestions.append(f"中高风险产品: {medium_high_amount:.2f}元，建议每周检查")
    
    # 基于金额的建议
    focus_count = len(analysis['focus_products'])
    if focus_count > 0:
        suggestions.append(f"重点关注 {focus_count} 个产品（金额 ≥ 50元）")
    
    # 基于类型的建议
    if '美股（美元）' in analysis['by_type']:
        us_stock_amount = analysis['by_type']['美股（美元）']['amount']
        suggestions.append(f"美股投资: {us_stock_amount:.2f}元，注意汇率风险")
    
    for i, suggestion in enumerate(suggestions[:5], 1):
        lines.append(f"{i:2d}. {suggestion}")
    
    lines.append("")
    lines.append("=" * 60)
    lines.append("✅ 报告生成完成")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def main():
    """主函数"""
    print("📊 基于1万总额的投资监控")
    print("=" * 60)
    
    try:
        # 1. 加载数据
        print("📁 加载投资数据...")
        df = load_investment_data()
        print(f"   ✅ 加载 {len(df)} 个投资产品")
        
        # 2. 计算金额
        print("💰 计算投资金额（基于1万总额）...")
        investments = calculate_amounts(df)
        print(f"   ✅ 计算完成，总投资占比: {sum([i['占比(%)'] for i in investments]):.2f}%")
        
        # 3. 分析投资组合
        print("📈 分析投资组合...")
        analysis = analyze_investments(investments)
        print(f"   ✅ 分析完成")
        print(f"      产品类型: {len(analysis['by_type'])} 种")
        print(f"      风险等级: {len(analysis['by_risk'])} 级")
        print(f"      重点关注: {len(analysis['focus_products'])} 个产品")
        
        # 4. 生成报告
        print("📝 生成监控报告...")
        txt_file, json_file = generate_report(analysis, investments)
        print(f"   ✅ 报告生成完成")
        print(f"      📄 文本报告: {txt_file}")
        print(f"      📊 JSON数据: {json_file}")
        
        # 5. 显示摘要
        print()
        print("📋 投资摘要")
        print("=" * 60)
        print(f"💰 总投资: {analysis['total_amount']}元")
        print(f"📈 产品数: {analysis['total_products']}个")
        
        # 类型分布
        print("\n📊 类型分布（前3）:")
        for type_name, stats in sorted(
            analysis['by_type'].items(), 
            key=lambda x: x[1]['amount'], 
            reverse=True
        )[:3]:
            print(f"   • {type_name}: {stats['amount']:.2f}元 ({stats['percentage']:.2f}%)")
        
        # 风险分布
        print("\n⚠️ 风险分布:")
        for risk in ['高', '中高', '中', '中低', '低']:
            if risk in analysis['by_risk']:
                stats = analysis['by_risk'][risk]
                print(f"   • {risk}风险: {stats['amount']:.2f}元 ({stats['percentage']:.2f}%)")
        
        # 监控建议
        print("\n💡 监控建议:")
        if analysis['high_risk_products']:
            print(f"   • 高风险产品: {len(analysis['high_risk_products'])}个，需密切监控")
        if analysis['focus_products']:
            print(f"   • 重点关注: {len(analysis['focus_products'])}个产品（金额 ≥ 50元）")
        
        print()
        print("=" * 60)
        print("🎯 基于1万总额的监控系统已就绪")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 监控失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()