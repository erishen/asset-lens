#!/usr/bin/env python3
"""
专门监控中高风险产品（风险 ≥ 中高）
基于投资产品-脱敏.csv
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_and_filter_high_risk():
    """加载并筛选中高风险产品"""
    data_file = Path('data/sample_data/投资产品-脱敏.csv')
    df = pd.read_csv(data_file)

    # 计算总金额
    total_amount = df['初始金额'].sum()

    # 风险等级映射
    risk_levels = {'低': 1, '中低': 2, '中': 3, '中高': 4, '高': 5}

    high_risk_products = []
    for _, row in df.iterrows():
        risk = str(row.get('风险', '未知'))

        # 只保留中高风险产品
        if risk in ['中高', '高']:
            initial_amount = float(row.get('初始金额', 0) or 0)
            percentage = (initial_amount / total_amount * 100) if total_amount > 0 else 0

            high_risk_products.append({
                '类型': row['类型'],
                '名称': row['名称'],
                '风险': risk,
                '风险等级': risk_levels.get(risk, 0),
                '占比(%)': round(percentage, 2),
                '初始金额': initial_amount,
                '当前金额': float(row.get('平台A', 0) or 0) + float(row.get('平台B', 0) or 0),
                '收益率': float(row.get('收益率', 0) or 0),
                '监控频率': '每日' if risk == '高' else '每周'
            })

    # 按风险等级和金额排序
    high_risk_products.sort(key=lambda x: (-x['风险等级'], -x['初始金额']))

    return high_risk_products, total_amount

def analyze_high_risk_products(products, total_amount):
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
        analysis['by_type'][type_name]['amount'] += product['初始金额']
        analysis['by_type'][type_name]['percentage'] += product['占比(%)']

        # 汇总
        analysis['total_amount'] += product['初始金额']
        analysis['total_percentage'] += product['占比(%)']

    # 监控计划
    analysis['monitoring_plan'] = {
        'daily': {
            'products': [p for p in products if p['监控频率'] == '每日'],
            'count': len([p for p in products if p['监控频率'] == '每日'])
        },
        'weekly': {
            'products': [p for p in products if p['监控频率'] == '每周'],
            'count': len([p for p in products if p['监控频率'] == '每周'])
        }
    }

    return analysis

def generate_report(products, analysis, total_amount):
    """生成监控报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("🔴 中高风险产品监控报告")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    # 概览
    lines.append("\n📊 概览:")
    lines.append(f"  中高风险产品数量: {analysis['total_products']} 个")
    lines.append(f"  总金额: ¥{analysis['total_amount']:,.2f}")
    lines.append(f"  占总投资比例: {analysis['total_percentage']:.2f}%")

    # 按风险等级
    lines.append("\n⚠️ 按风险等级:")
    for risk in ['高', '中高']:
        if risk in analysis['by_risk'] and analysis['by_risk'][risk]:
            products_list = analysis['by_risk'][risk]
            total = sum(p['初始金额'] for p in products_list)
            lines.append(f"  {risk}风险: {len(products_list)} 个, ¥{total:,.2f}")

    # 按类型
    lines.append("\n📈 按类型:")
    for type_name, stats in sorted(analysis['by_type'].items(), key=lambda x: -x[1]['amount']):
        lines.append(f"  {type_name}: {stats['count']} 个, ¥{stats['amount']:,.2f} ({stats['percentage']:.2f}%)")

    # 详细列表
    lines.append("\n📋 详细列表:")
    lines.append(f"{'名称':35} {'类型':15} {'风险':6} {'初始金额':>12} {'收益率':>8}")
    lines.append("-" * 80)

    lines.extend(
        f"{product['名称'][:33]:35} {product['类型'][:13]:15} {product['风险']:<6} "
        f"¥{product['初始金额']:>10,.2f} {product['收益率']:>7.2f}%"
        for product in products
    )

    # 监控计划
    lines.append("\n📅 监控计划:")
    lines.append(f"  每日监控: {analysis['monitoring_plan']['daily']['count']} 个高风险产品")
    lines.append(f"  每周监控: {analysis['monitoring_plan']['weekly']['count']} 个中高风险产品")

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)

def main():
    """主函数"""
    logger.info("📊 加载中高风险产品数据...")
    products, total_amount = load_and_filter_high_risk()

    if not products:
        logger.error("❌ 未找到中高风险产品")
        return

    logger.info("✅ 找到 %s 个中高风险产品", len(products))

    # 分析
    analysis = analyze_high_risk_products(products, total_amount)

    # 生成报告
    report = generate_report(products, analysis, total_amount)
    logger.info(report)

    # 保存报告
    output_dir = Path('output/high_risk_monitoring')
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = output_dir / f'high_risk_report_{timestamp}.txt'
    report_file.write_text(report, encoding='utf-8')
    logger.info("\n✅ 报告已保存: %s", report_file)

    # 保存JSON数据
    json_file = output_dir / f'high_risk_data_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'products': products,
            'analysis': analysis,
            'generated_at': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    logger.info("✅ 数据已保存: %s", json_file)

if __name__ == '__main__':
    main()
