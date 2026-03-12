#!/usr/bin/env python3
"""
Asset-Lens快速测试脚本
"""

import os
import sys
import akshare as ak
import pandas as pd
from datetime import datetime

def test_basic_functions():
    """测试基本功能"""
    print("🔧 Asset-Lens快速测试")
    print("=" * 60)
    
    tests = [
        ("获取A股列表", lambda: ak.stock_info_a_code_name()),
        ("获取上证指数", lambda: ak.stock_zh_index_daily(symbol="sh000001")),
        ("获取深证成指", lambda: ak.stock_zh_index_daily(symbol="sz399001")),
        ("获取创业板指", lambda: ak.stock_zh_index_daily(symbol="sz399006")),
    ]
    
    for name, func in tests:
        try:
            print(f"📊 {name}...")
            result = func()
            if isinstance(result, pd.DataFrame):
                print(f"   ✅ 成功，数据形状: {result.shape}")
                if len(result) > 0:
                    print(f"     示例数据: {result.iloc[0].to_dict() if len(result) > 0 else '无数据'}")
            else:
                print(f"   ✅ 成功，结果类型: {type(result)}")
        except Exception as e:
            print(f"   ❌ 失败: {str(e)[:100]}")

def test_stock_data():
    """测试股票数据"""
    print("\n📈 测试股票数据获取...")
    
    test_stocks = [
        ("000001", "平安银行"),
        ("000002", "万科A"),
        ("600519", "贵州茅台"),
        ("000858", "五粮液"),
    ]
    
    for code, name in test_stocks:
        try:
            symbol = f"sz{code}" if code.startswith("00") else f"sh{code}"
            data = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date="20240101",
                end_date="20240110",
                adjust=""
            )
            print(f"   ✅ {name}({code}): {len(data)} 条数据")
        except Exception as e:
            print(f"   ❌ {name}({code}): 失败 - {str(e)[:80]}")

def test_fund_data():
    """测试基金数据"""
    print("\n💰 测试基金数据获取...")
    
    try:
        # 获取基金列表
        fund_list = ak.fund_em_open_fund_daily()
        print(f"   ✅ 基金列表: {len(fund_list)} 只基金")
        
        # 获取单个基金数据
        if len(fund_list) > 0:
            fund_code = fund_list.iloc[0]['基金代码']
            fund_name = fund_list.iloc[0]['基金简称']
            print(f"   ✅ 示例基金: {fund_name}({fund_code})")
    except Exception as e:
        print(f"   ❌ 基金数据获取失败: {str(e)[:80]}")

def main():
    """主函数"""
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python版本: {sys.version.split()[0]}")
    print(f"📦 AkShare版本: {ak.__version__}")
    print("=" * 60)
    
    test_basic_functions()
    test_stock_data()
    test_fund_data()
    
    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    print("=" * 60)
    
    print("\n📋 总结:")
    print("  如果所有测试都通过 ✅，说明网络配置正常")
    print("  如果有测试失败 ❌，请检查:")
    print("    1. 网络连接")
    print("    2. 防火墙设置")
    print("    3. 代理配置")
    print("    4. AkShare版本")

if __name__ == "__main__":
    main()
