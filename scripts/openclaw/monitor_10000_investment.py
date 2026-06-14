#!/usr/bin/env python3
"""
监控1万元投资组合
基于投资产品-脱敏.csv
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_investments():
    """加载投资数据"""
    data_file = Path('data/sample_data/投资产品-脱敏.csv')
    df = pd.read_csv(data_file)

    total_amount = df['初始金额'].sum()

    investments = []
    for _, row in df.iterrows():
        initial_amount = float(row.get('初始金额', 0) or 0)
        percentage = (initial_amount / total_amount * 100) if total_amount > 0 else 0

        investments.append({
            '类型': row['类型'],
            '名称': row['名称'],
            '风险': str(row.get('风险', '未知')),
            '初始金额': initial_amount,
            '当前金额': float(row.get('平台A', 0) or 0) + float(row.get('平台B', 0) or 0),
            '占比(%)': round(percentage, 2),
            '收益率': float(row.get('收益率', 0) or 0),
            '年化收益': float(row.get('年化收益', 0) or 0),
        })

    return investments, total_amount

def analyze_investments(investments, total_amount):
    """分析投资组合"""
    analysis = {
        'total_products': len(investments),
        'total_amount': total_amount,
        'total_current': sum(i['当前金额'] for i in investments),
        'total_profit': 0,
        'total_profit_rate': 0,
        'by_type': {},
        'by_risk': {},
    }

    analysis['total_profit'] = analysis['total_current'] - analysis['total_amount']
    analysis['total_profit_rate'] = (analysis['total_profit'] / analysis['total_amount'] * 100) if analysis['total_amount'] > 0 else 0

    for inv in investments:
        type_name = inv['类型']
        if type_name not in analysis['by_type']:
            analysis['by_type'][type_name] = {'count': 0, 'amount': 0, 'current': 0, 'percentage': 0}
        analysis['by_type'][type_name]['count'] += 1
        analysis['by_type'][type_name]['amount'] += inv['初始金额']
        analysis['by_type'][type_name]['current'] += inv['当前金额']
        analysis['by_type'][type_name]['percentage'] += inv['占比(%)']

        risk = inv['风险']
        if risk not in analysis['by_risk']:
            analysis['by_risk'][risk] = {'count': 0, 'amount': 0, 'percentage': 0}
        analysis['by_risk'][risk]['count'] += 1
        analysis['by_risk'][risk]['amount'] += inv['初始金额']
        analysis['by_risk'][risk]['percentage'] += inv['占比(%)']

    return analysis

def generate_report(investments, analysis):
    """生成投资报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("📊 1万元投资组合监控报告")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)

    lines.append("\n💰 投资概览:")
    lines.append(f"  产品数量: {analysis['total_products']} 个")
    lines.append(f"  初始投入: ¥{analysis['total_amount']:,.2f}")
    lines.append(f"  当前市值: ¥{analysis['total_current']:,.2f}")
    lines.append(f"  累计收益: ¥{analysis['total_profit']:,.2f}")
    lines.append(f"  收益率: {analysis['total_profit_rate']:+.2f}%")

    lines.append("\n📈 按类型分布:")
    for type_name, stats in sorted(analysis['by_type'].items(), key=lambda x: -x[1]['amount']):
        lines.append(f"  {type_name}: {stats['count']}个, ¥{stats['amount']:,.0f} ({stats['percentage']:.1f}%)")

    lines.append("\n⚠️ 按风险分布:")
    for risk, stats in sorted(analysis['by_risk'].items(), key=lambda x: -x[1]['amount']):
        lines.append(f"  {risk}风险: {stats['count']}个, ¥{stats['amount']:,.0f} ({stats['percentage']:.1f}%)")

    lines.append("\n🏆 收益前5:")
    sorted_by_return = sorted(investments, key=lambda x: x['收益率'], reverse=True)
    for i, inv in enumerate(sorted_by_return[:5], 1):
        lines.append(f"  {i}. {inv['名称'][:25]}: {inv['收益率']:+.2f}%")

    lines.append("\n📉 收益后5:")
    for i, inv in enumerate(sorted_by_return[-5:], 1):
        lines.append(f"  {i}. {inv['名称'][:25]}: {inv['收益率']:+.2f}%")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)

def main():
    """主函数"""
    logger.info("📊 加载投资数据...")
    investments, total_amount = load_investments()

    logger.info("✅ 加载了 %s 个投资产品", len(investments))
    logger.info(f"   总金额: ¥{total_amount:,.2f}")

    analysis = analyze_investments(investments, total_amount)
    report = generate_report(investments, analysis)
    logger.info(report)

    output_dir = Path('output/investment_monitoring')
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = output_dir / f'investment_report_{timestamp}.txt'
    report_file.write_text(report, encoding='utf-8')
    logger.info("\n✅ 报告已保存: %s", report_file)

if __name__ == '__main__':
    main()
