#!/usr/bin/env python3
"""
创建符合asset-lens格式的正确数据文件
基于占比数据，使用平台金额系统
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

def create_platform_based_data():
    """创建基于平台金额系统的数据"""
    
    # 读取原始占比数据
    df = pd.read_csv('data/real/投资产品.csv')
    
    print(f"📊 原始数据: {len(df)} 个产品")
    
    # 假设总投资额
    total_investment = 10000.0
    
    # 计算每个产品的金额
    df['金额'] = df['占比(%)'] / 100 * total_investment
    
    # 定义平台（模拟）
    platforms = {
        '支付宝': 'alipay',
        '微信理财': 'wechat',
        '银行理财': 'bank', 
        '券商': 'broker',
        '基金平台': 'fund',
        '其他': 'other'
    }
    
    # 为每个产品分配平台
    platform_list = list(platforms.keys())
    df['平台'] = [random.choice(platform_list) for _ in range(len(df))]
    
    # 创建符合asset-lens格式的数据
    # asset-lens期望的列: 类型, 名称, 风险, 平台1, 平台2, ..., 收益率, 投资天数等
    
    result_data = []
    
    for _, row in df.iterrows():
        # 基础字段
        product = {
            '类型': row['类型'],
            '名称': row['名称'],
            '风险': row['风险'],
            '代码': row['代码'],
            '占比(%)': row['占比(%)'],
        }
        
        # 平台金额（只设置一个平台，金额为该产品的全部金额）
        platform_name = row['平台']
        product[platform_name] = round(row['金额'], 2)
        
        # 其他字段
        # 购买日期（随机）
        buy_date = datetime.now() - timedelta(days=random.randint(30, 365))
        product['开始日期'] = buy_date.strftime('%Y-%m-%d')
        
        # 投资天数
        product['投资天数'] = random.randint(30, 365)
        
        # 收益率（随机，基于风险）
        risk_multiplier = {
            '低': (0.5, 3.0),
            '中低': (0.0, 5.0),
            '中': (-2.0, 8.0),
            '中高': (-5.0, 12.0),
            '高': (-10.0, 20.0),
            '-': (1.0, 4.0)
        }
        
        risk = row['风险'] if row['风险'] in risk_multiplier else '-'
        min_rate, max_rate = risk_multiplier.get(risk, (0.0, 5.0))
        product['收益率'] = round(random.uniform(min_rate, max_rate), 2)
        
        # 年化收益
        product['年化收益'] = round(product['收益率'] * 365 / product['投资天数'], 2)
        
        result_data.append(product)
    
    # 创建DataFrame
    result_df = pd.DataFrame(result_data)
    
    # 确保所有平台列都存在（即使为空）
    for platform in platform_list:
        if platform not in result_df.columns:
            result_df[platform] = ''
    
    # 重新排列列：基础字段在前，平台列在后
    base_columns = ['类型', '名称', '风险', '代码', '占比(%)', '开始日期', '投资天数', '收益率', '年化收益']
    platform_columns = [col for col in result_df.columns if col in platform_list]
    
    final_columns = base_columns + platform_columns
    result_df = result_df[final_columns]
    
    # 保存文件
    output_file = 'data/real/money_csv_20260312/投资产品_正确格式.csv'
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # 也保存为默认文件名
    default_file = 'data/real/money_csv_20260312/投资产品.csv'
    result_df.to_csv(default_file, index=False, encoding='utf-8-sig')
    
    # 打印统计
    print(f"\n📈 生成的数据统计:")
    print(f"  产品数量: {len(result_df)}")
    
    # 计算总金额（从平台列）
    total_amount = 0
    for platform in platform_list:
        if platform in result_df.columns:
            platform_sum = result_df[platform].apply(lambda x: float(x) if str(x).strip() else 0).sum()
            total_amount += platform_sum
            print(f"  {platform}: {platform_sum:.2f}元")
    
    print(f"  总金额: {total_amount:.2f}元")
    
    # 按类型统计
    print(f"\n📊 按类型统计:")
    for type_name, group in result_df.groupby('类型'):
        type_amount = 0
        for platform in platform_list:
            if platform in group.columns:
                type_amount += group[platform].apply(lambda x: float(x) if str(x).strip() else 0).sum()
        print(f"  {type_name}: {type_amount:.2f}元")
    
    print(f"\n✅ 正确格式数据已保存: {output_file}")
    print(f"✅ 已覆盖默认文件: {default_file}")
    
    return output_file

def create_simple_test_data():
    """创建简单的测试数据（更容易调试）"""
    
    # 创建极简测试数据
    test_data = [
        {
            '类型': '基金',
            '名称': '测试基金A',
            '风险': '中',
            '支付宝': '1000.00',
            '开始日期': '2025-01-01',
            '投资天数': '365',
            '收益率': '5.00',
            '年化收益': '5.00'
        },
        {
            '类型': '债券',
            '名称': '测试债券B',
            '风险': '低',
            '银行理财': '2000.00',
            '开始日期': '2025-06-01',
            '投资天数': '180',
            '收益率': '3.00',
            '年化收益': '6.00'
        },
        {
            '类型': '其他',
            '名称': '测试理财C',
            '风险': '-',
            '微信理财': '3000.00',
            '开始日期': '2025-03-01',
            '投资天数': '270',
            '收益率': '4.00',
            '年化收益': '5.33'
        }
    ]
    
    test_df = pd.DataFrame(test_data)
    
    # 保存测试文件
    test_file = 'data/real/money_csv_20260312/投资产品_测试.csv'
    test_df.to_csv(test_file, index=False, encoding='utf-8-sig')
    
    # 也保存为默认文件
    default_file = 'data/real/money_csv_20260312/投资产品.csv'
    test_df.to_csv(default_file, index=False, encoding='utf-8-sig')
    
    print(f"\n🧪 简单测试数据:")
    print(f"  产品数量: {len(test_df)}")
    
    total_amount = 0
    for _, row in test_df.iterrows():
        # 查找金额列
        amount_columns = ['支付宝', '银行理财', '微信理财', '券商', '基金平台', '其他']
        for col in amount_columns:
            if col in row and str(row[col]).strip():
                amount = float(row[col])
                total_amount += amount
                print(f"  {row['名称']}: {amount:.2f}元 ({col})")
    
    print(f"  总金额: {total_amount:.2f}元")
    print(f"✅ 测试数据已保存: {test_file}")
    print(f"✅ 已覆盖默认文件: {default_file}")
    
    return test_file

def test_asset_lens_loading():
    """测试asset-lens数据加载"""
    
    print("\n🔍 测试asset-lens数据加载")
    print("=" * 60)
    
    try:
        from asset_lens.data.csv_parser import CSVParser
        
        # 测试文件
        test_file = 'data/real/money_csv_20260312/投资产品.csv'
        
        print(f"测试文件: {test_file}")
        
        # 尝试解析
        products = CSVParser.parse_csv_file(test_file)
        
        print(f"解析产品数: {len(products)}")
        
        if products:
            print(f"\n📋 解析的产品:")
            for i, product in enumerate(products[:3], 1):  # 只显示前3个
                print(f"  {i}. {product.name}")
                print(f"     类型: {product.investment_type}")
                print(f"     风险: {product.risk_level}")
                print(f"     平台金额: {product.platform_amounts}")
                print(f"     收益率: {product.return_rate}")
        else:
            print("❌ 没有解析到产品")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 创建符合asset-lens格式的数据")
    print("=" * 60)
    print("💡 使用平台金额系统，符合asset-lens解析逻辑")
    print()
    
    # 1. 创建平台金额数据
    print("📝 创建平台金额数据...")
    platform_file = create_platform_based_data()
    
    # 2. 创建简单测试数据
    print("\n🧪 创建简单测试数据...")
    test_file = create_simple_test_data()
    
    # 3. 测试asset-lens加载
    test_asset_lens_loading()
    
    print("\n" + "=" * 60)
    print("✅ 数据创建完成")
    print()
    print("🎯 关键点:")
    print("  1. asset-lens使用平台金额系统")
    print("  2. 每个平台对应一列，金额在该列中")
    print("  3. 必需列: '类型', '名称', '风险'")
    print("  4. 可选列: '开始日期', '投资天数', '收益率', '年化收益'")
    print()
    print("🚀 下一步:")
    print("  1. 运行: python3 -m asset_lens.cli analyze --data-mode real")
    print("  2. 检查是否显示正确金额")
    print("  3. 验证数据准确性")
    print("=" * 60)

if __name__ == "__main__":
    main()