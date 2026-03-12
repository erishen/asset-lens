#!/usr/bin/env python3
"""
测试投资数据分析功能
"""

import os
import sys
import csv
from datetime import datetime

print("📊 投资数据分析测试")
print("=" * 50)

# 读取投资数据
data_file = "data/sample_data/投资产品-脱敏.csv"

try:
    with open(data_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    print(f"✅ 数据读取成功: {len(data)} 条记录")
    
    # 分析投资类型分布
    type_distribution = {}
    for item in data:
        invest_type = item.get('类型', '未知')
        weight = float(item.get('占比(%)', 0))
        type_distribution[invest_type] = type_distribution.get(invest_type, 0) + weight
    
    print("\n📈 投资类型分布:")
    for invest_type, weight in sorted(type_distribution.items(), key=lambda x: x[1], reverse=True):
        if weight > 0:  # 只显示有占比的类型
            print(f"  {invest_type}: {weight:.2f}%")
    
    # 提取重点监控产品
    print("\n🎯 重点监控产品 (占比 > 0.5%):")
    focus_products = []
    for item in data:
        try:
            weight = float(item.get('占比(%)', 0))
            if weight > 0.5 and item.get('代码') and item.get('代码') != '-':
                focus_products.append({
                    'name': item.get('名称', '未知'),
                    'code': item.get('代码', '未知'),
                    'type': item.get('类型', '未知'),
                    'weight': weight
                })
        except ValueError:
            continue
    
    for product in sorted(focus_products, key=lambda x: x['weight'], reverse=True):
        print(f"  • {product['code']} - {product['name']} ({product['weight']}%)")
    
    # 生成监控建议
    print("\n💡 监控建议:")
    print("  1. 每日监控重点基金净值")
    print("  2. 每周分析投资组合结构")
    print("  3. 每月评估风险收益比")
    print("  4. 每季度调整资产配置")
    
    # 保存分析结果
    output_file = f"投资分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("投资分析报告\n")
        f.write("=" * 40 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据文件: {data_file}\n")
        f.write(f"总记录数: {len(data)}\n\n")
        
        f.write("投资类型分布:\n")
        for invest_type, weight in sorted(type_distribution.items(), key=lambda x: x[1], reverse=True):
            if weight > 0:
                f.write(f"  {invest_type}: {weight:.2f}%\n")
        
        f.write("\n重点监控产品:\n")
        for product in sorted(focus_products, key=lambda x: x['weight'], reverse=True):
            f.write(f"  • {product['code']} - {product['name']} ({product['weight']}%)\n")
    
    print(f"\n✅ 分析报告已保存: {output_file}")
    
except Exception as e:
    print(f"❌ 数据分析失败: {e}")
    import traceback
    traceback.print_exc()

print("\n🔧 环境信息:")
print(f"  工作目录: {os.getcwd()}")
print(f"  Python版本: {sys.version}")
print(f"  数据模式: {os.environ.get('ASSET_LENS_DATA_MODE', '未设置')}")

print("\n🎉 测试完成！")
