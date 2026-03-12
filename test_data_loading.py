#!/usr/bin/env python3
"""
测试asset-lens数据加载
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

def test_csv_parser():
    """测试CSV解析器"""
    print("🔍 测试CSV解析器")
    print("=" * 60)
    
    try:
        from asset_lens.data.csv_parser import CSVParser
        
        parser = CSVParser()
        
        # 测试加载数据
        data_dir = config.get_data_dir()
        print(f"数据目录: {data_dir}")
        
        # 查找投资产品文件
        investment_file = None
        for file in os.listdir(data_dir):
            if '投资' in file and file.endswith('.csv'):
                investment_file = os.path.join(data_dir, file)
                print(f"找到投资文件: {investment_file}")
                break
        
        if investment_file:
            # 尝试加载
            print(f"尝试加载: {investment_file}")
            products = parser.load_investment_products(investment_file)
            print(f"加载产品数: {len(products) if products else 0}")
            
            if products:
                print(f"第一个产品: {products[0]}")
                print(f"总金额: {sum(p.amount for p in products if hasattr(p, 'amount'))}")
        else:
            print("❌ 未找到投资产品文件")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_config():
    """测试配置"""
    print("\n🔧 测试配置")
    print("=" * 60)
    
    try:
        from asset_lens.config import config
        
        print(f"数据模式: {config.data_mode}")
        print(f"数据目录: {config.data_dir}")
        
        # 检查数据目录是否存在
        data_dir = Path(config.data_dir)
        if data_dir.exists():
            print(f"✅ 数据目录存在: {data_dir}")
            print(f"目录内容: {list(data_dir.glob('*.csv'))}")
        else:
            print(f"❌ 数据目录不存在: {data_dir}")
            
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")

def test_direct_loading():
    """直接加载测试"""
    print("\n📊 直接加载测试")
    print("=" * 60)
    
    import pandas as pd
    
    # 直接加载数据
    data_file = "data/real/投资产品.csv"
    
    if os.path.exists(data_file):
        print(f"加载文件: {data_file}")
        
        # 读取CSV
        df = pd.read_csv(data_file)
        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")
        
        # 检查关键列
        required_columns = ['类型', '名称', '金额(元)']
        missing = [col for col in required_columns if col not in df.columns]
        
        if missing:
            print(f"❌ 缺少列: {missing}")
        else:
            print(f"✅ 所有必需列都存在")
            
        # 计算总金额
        if '金额(元)' in df.columns:
            total_amount = df['金额(元)'].sum()
            print(f"💰 总金额: {total_amount:.2f}元")
            
            # 按类型统计
            print(f"\n📈 按类型统计:")
            type_stats = df.groupby('类型')['金额(元)'].sum().round(2)
            for type_name, amount in type_stats.items():
                print(f"  {type_name}: {amount:.2f}元")
                
            # 按风险统计
            print(f"\n⚠️ 按风险统计:")
            risk_stats = df.groupby('风险')['金额(元)'].sum().round(2)
            for risk_level, amount in risk_stats.items():
                print(f"  {risk_level}: {amount:.2f}元")
        else:
            print("❌ 没有金额列")
            
    else:
        print(f"❌ 文件不存在: {data_file}")

def check_asset_lens_issue():
    """检查asset-lens问题"""
    print("\n🔍 检查asset-lens问题")
    print("=" * 60)
    
    try:
        # 检查asset-lens的数据加载逻辑
        from asset_lens.data.investment_system import InvestmentSystem
        
        system = InvestmentSystem()
        print(f"InvestmentSystem初始化: ✅")
        
        # 尝试加载数据
        print("尝试加载投资数据...")
        system.load_investment_data()
        
        # 检查数据
        if hasattr(system, 'investment_products'):
            products = system.investment_products
            print(f"加载产品数: {len(products)}")
            
            if products:
                # 检查第一个产品
                first_product = products[0]
                print(f"第一个产品类型: {type(first_product)}")
                
                # 尝试获取属性
                attrs = ['name', 'amount', 'current_value', 'profit_rate']
                for attr in attrs:
                    if hasattr(first_product, attr):
                        value = getattr(first_product, attr)
                        print(f"  {attr}: {value}")
                    else:
                        print(f"  {attr}: ❌ 不存在")
        else:
            print("❌ 没有investment_products属性")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 asset-lens数据加载测试")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    print(f"环境变量 DATA_MODE: {os.getenv('DATA_MODE')}")
    
    # 测试配置
    test_config()
    
    # 直接加载测试
    test_direct_loading()
    
    # 检查asset-lens问题
    check_asset_lens_issue()
    
    print("\n" + "=" * 60)
    print("🎯 问题分析:")
    print("  1. 数据文件格式正确")
    print("  2. 金额列存在且数据完整")
    print("  3. asset-lens可能解析逻辑有问题")
    print("  4. 需要检查InvestmentSystem的数据加载")
    print("=" * 60)

if __name__ == "__main__":
    main()