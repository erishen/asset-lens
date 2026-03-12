#!/usr/bin/env python3
"""
中高风险以上基金监控脚本
专门监控风险等级 >= 3 的基金产品
"""

import json
import pandas as pd
import os
from datetime import datetime
import sys

def load_high_risk_funds():
    """加载中高风险以上基金数据"""
    data_path = 'data/sample_data/投资产品-脱敏.csv'
    config_path = 'config/fund_monitor_config.json'
    
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'focus': '中高风险以上基金监控',
        'data_loaded': False,
        'high_risk_count': 0,
        'risk_distribution': {},
        'funds_by_risk': {},
        'status': 'pending'
    }
    
    # 加载投资数据
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        
        # 风险等级映射
        risk_levels = {'低': 1, '中低': 2, '中': 3, '中高': 4, '高': 5}
        df['风险等级'] = df['风险'].map(risk_levels)
        
        # 筛选中高风险以上（风险等级 >= 3）
        high_risk_funds = df[df['风险等级'] >= 3].copy()
        high_risk_funds = high_risk_funds.sort_values(['风险等级', '占比(%)'], ascending=[False, False])
        
        results['data_loaded'] = True
        results['high_risk_count'] = len(high_risk_funds)
        results['total_funds'] = len(df)
        
        # 风险等级分布
        risk_counts = high_risk_funds['风险'].value_counts()
        results['risk_distribution'] = risk_counts.to_dict()
        
        # 按风险等级分组
        results['funds_by_risk'] = {
            '高风险': high_risk_funds[high_risk_funds['风险等级'] == 5].to_dict('records'),
            '中高风险': high_risk_funds[high_risk_funds['风险等级'] == 4].to_dict('records'),
            '中等风险': high_risk_funds[high_risk_funds['风险等级'] == 3].to_dict('records')
        }
        
        # 计算总占比
        results['total_weight'] = high_risk_funds['占比(%)'].sum()
        
        # 按类型分组
        type_groups = high_risk_funds.groupby('类型')['占比(%)'].sum().sort_values(ascending=False)
        results['type_distribution'] = type_groups.to_dict()
        
        results['status'] = 'success'
    else:
        print(f"❌ 数据文件不存在: {data_path}")
        results['status'] = 'data_missing'
    
    return results

def generate_high_risk_report(results):
    """生成中高风险基金监控报告"""
    if results['status'] != 'success':
        return f"❌ 监控失败: {results['status']}"
    
    report = []
    report.append("🔥 中高风险以上基金监控报告")
    report.append("=" * 60)
    report.append(f"📅 报告时间: {results['timestamp']}")
    report.append(f"📊 监控范围: {results['focus']}")
    report.append(f"📈 总基金数: {results['total_funds']}")
    report.append(f"🎯 中高风险以上: {results['high_risk_count']}个")
    report.append(f"💰 总占比: {results['total_weight']:.2f}%")
    report.append("")
    
    # 风险等级分布
    report.append("📊 风险等级分布:")
    for risk, count in results['risk_distribution'].items():
        report.append(f"   {risk}: {count}个基金")
    report.append("")
    
    # 基金类型分布
    report.append("🏷️ 基金类型分布:")
    for type_name, weight in results['type_distribution'].items():
        report.append(f"   {type_name}: {weight:.2f}%")
    report.append("")
    
    # 高风险基金详情
    high_risk_funds = results['funds_by_risk']['高风险']
    if high_risk_funds:
        report.append("⚠️ 高风险基金 (需要密切监控):")
        for fund in high_risk_funds:
            report.append(f"   • {fund['名称']} ({fund['代码']})")
            report.append(f"     类型: {fund['类型']}, 占比: {fund['占比(%)']:.2f}%")
        report.append("")
    
    # 中高风险基金详情
    medium_high_funds = results['funds_by_risk']['中高风险']
    if medium_high_funds:
        report.append("🔸 中高风险基金 (需要定期检查):")
        # 只显示前5个
        for fund in medium_high_funds[:5]:
            report.append(f"   • {fund['名称']} ({fund['代码']}) - {fund['占比(%)']:.2f}%")
        if len(medium_high_funds) > 5:
            report.append(f"   等{len(medium_high_funds)-5}个中高风险基金...")
        report.append("")
    
    # 中等风险基金详情
    medium_funds = results['funds_by_risk']['中等风险']
    if medium_funds:
        report.append("🔹 中等风险基金 (保持关注):")
        # 只显示占比高的
        for fund in medium_funds:
            if fund['占比(%)'] > 0.5:
                report.append(f"   • {fund['名称']} ({fund['代码']}) - {fund['占比(%)']:.2f}%")
        report.append("")
    
    # 监控建议
    report.append("🎯 监控建议:")
    report.append("   1. ⚠️ 高风险基金: 每日检查，设置价格预警")
    report.append("   2. 🔸 中高风险基金: 每周检查，关注市场动态")
    report.append("   3. 🔹 中等风险基金: 每月回顾，评估表现")
    report.append("   4. 📊 重点关注: 美股、科技、指数类基金")
    report.append("")
    
    # 预警规则
    report.append("🚨 预警规则建议:")
    report.append("   1. 单日跌幅 > 5% → 立即检查")
    report.append("   2. 连续3日下跌 → 分析原因")
    report.append("   3. 月度跌幅 > 10% → 考虑调整")
    report.append("   4. 高风险基金波动 > 3% → 关注")
    report.append("")
    
    report.append("💡 投资纪律:")
    report.append("   • 高风险基金占比不宜过高")
    report.append("   • 定期再平衡投资组合")
    report.append("   • 设置止损和止盈点")
    report.append("   • 保持长期投资视角")
    report.append("=" * 60)
    
    return "\n".join(report)

def save_high_risk_report(report_text):
    """保存报告到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = 'output/high_risk_monitoring'
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = f"{report_dir}/high_risk_funds_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return report_file

def main():
    """主函数"""
    print("🔥 开始中高风险基金监控...")
    
    # 加载数据
    results = load_high_risk_funds()
    
    # 生成报告
    report = generate_high_risk_report(results)
    
    # 输出报告
    print(report)
    
    # 保存报告
    if results['status'] == 'success':
        report_file = save_high_risk_report(report)
        print(f"📁 报告已保存: {report_file}")
    
    return results['status']

if __name__ == "__main__":
    status = main()
    sys.exit(0 if status == 'success' else 1)