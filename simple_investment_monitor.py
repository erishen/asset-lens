#!/usr/bin/env python3
"""
简单投资监控脚本
定时检查投资组合状态
"""

import json
import pandas as pd
import os
from datetime import datetime
import sys

def load_investment_data():
    """加载投资数据"""
    config_path = 'investment_monitor_config.json'
    data_path = 'data/sample_data/投资产品-脱敏.csv'
    
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'config_loaded': False,
        'data_loaded': False,
        'monitoring_products': 0,
        'investment_summary': {},
        'status': 'pending'
    }
    
    # 加载监控配置
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        results['config_loaded'] = True
        results['monitoring_products'] = config['monitoring_plan']['total_products']
        results['categories'] = config['monitoring_plan']['categories']
    else:
        print(f"❌ 配置文件不存在: {config_path}")
        results['status'] = 'config_missing'
        return results
    
    # 加载投资数据
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        results['data_loaded'] = True
        
        # 分析投资组合
        total_weight = df['占比(%)'].sum()
        results['total_weight'] = total_weight
        
        # 按类型分组
        type_groups = df.groupby('类型')['占比(%)'].sum().sort_values(ascending=False)
        results['type_distribution'] = type_groups.to_dict()
        
        # 重点产品（占比>0.5%）
        important = df[df['占比(%)'] > 0.5]
        results['important_products'] = len(important)
        results['important_list'] = []
        
        for idx, row in important.iterrows():
            if row['名称'] != '其他（理财/国债/现金等）':
                results['important_list'].append({
                    'name': row['名称'],
                    'code': row['代码'],
                    'weight': row['占比(%)'],
                    'risk': row['风险']
                })
        
        results['status'] = 'success'
    else:
        print(f"❌ 数据文件不存在: {data_path}")
        results['status'] = 'data_missing'
    
    return results

def generate_report(results):
    """生成监控报告"""
    if results['status'] != 'success':
        return f"❌ 监控失败: {results['status']}"
    
    report = []
    report.append("📊 Asset-Lens 投资监控报告")
    report.append("=" * 50)
    report.append(f"📅 报告时间: {results['timestamp']}")
    report.append(f"📈 监控产品数: {results['monitoring_products']}个")
    report.append(f"💰 总投资占比: {results['total_weight']:.2f}%")
    report.append("")
    report.append("🏷️ 投资类型分布:")
    for type_name, weight in results['type_distribution'].items():
        report.append(f"   - {type_name}: {weight:.2f}%")
    report.append("")
    report.append("🎯 重点监控产品 (占比>0.5%):")
    for product in results['important_list']:
        report.append(f"   - {product['name']} ({product['code']}): {product['weight']:.2f}% [{product['risk']}]")
    report.append("")
    report.append("💡 建议:")
    report.append("   1. 定期检查重点产品的表现")
    report.append("   2. 关注债券类产品的稳定性")
    report.append("   3. 考虑分散投资降低风险")
    report.append("=" * 50)
    
    return "\n".join(report)

def save_report(report_text):
    """保存报告到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = 'output/monitoring_reports'
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = f"{report_dir}/investment_monitor_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return report_file

def main():
    """主函数"""
    print("🚀 开始投资监控...")
    
    # 加载数据
    results = load_investment_data()
    
    # 生成报告
    report = generate_report(results)
    
    # 输出报告
    print(report)
    
    # 保存报告
    if results['status'] == 'success':
        report_file = save_report(report)
        print(f"📁 报告已保存: {report_file}")
    
    return results['status']

if __name__ == "__main__":
    status = main()
    sys.exit(0 if status == 'success' else 1)