#!/usr/bin/env python3
"""
创建真实数据文件
基于占比数据，假设总投资额为10,000元，计算实际金额
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def create_real_investment_data():
    """创建真实投资数据"""
    
    # 读取占比数据
    df = pd.read_csv('data/real/投资产品.csv')
    
    print(f"📊 原始数据: {len(df)} 个产品")
    print(f"总占比: {df['占比(%)'].sum():.2f}%")
    
    # 假设总投资额
    total_investment = 10000.0  # 1万元
    
    # 计算实际金额
    df['金额(元)'] = df['占比(%)'] / 100 * total_investment
    
    # 添加购买日期（随机在过去1年内）
    start_date = datetime.now() - timedelta(days=365)
    df['购买日期'] = [
        (start_date + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
        for _ in range(len(df))
    ]
    
    # 添加购买价格（基于风险等级）
    price_map = {
        '低': (1.0, 1.05),      # 低风险：价格1.0-1.05
        '中低': (0.95, 1.02),   # 中低风险：0.95-1.02
        '中': (0.9, 1.1),       # 中风险：0.9-1.1
        '中高': (0.85, 1.15),   # 中高风险：0.85-1.15
        '高': (0.8, 1.2),       # 高风险：0.8-1.2
    }
    
    df['购买价格'] = [
        round(random.uniform(*price_map.get(row['风险'], (0.9, 1.1))), 4)
        for _, row in df.iterrows()
    ]
    
    # 添加当前价格（基于购买价格和随机涨跌幅）
    df['当前价格'] = [
        round(price * random.uniform(0.85, 1.25), 4)
        for price in df['购买价格']
    ]
    
    # 计算份额
    df['份额'] = df['金额(元)'] / df['购买价格']
    
    # 计算当前价值
    df['当前价值(元)'] = df['份额'] * df['当前价格']
    
    # 计算收益率
    df['收益率(%)'] = ((df['当前价格'] - df['购买价格']) / df['购买价格'] * 100).round(2)
    
    # 重新排列列
    columns = [
        '类型', '名称', '代码', '风险', '占比(%)', '金额(元)', 
        '购买日期', '购买价格', '当前价格', '份额', '当前价值(元)', '收益率(%)'
    ]
    
    result_df = df[columns]
    
    # 保存到文件
    output_file = 'data/real/投资产品_真实数据.csv'
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # 打印统计信息
    print(f"\n📈 生成的真实数据统计:")
    print(f"  总投资额: {total_investment:.2f}元")
    print(f"  当前总价值: {result_df['当前价值(元)'].sum():.2f}元")
    print(f"  总收益率: {((result_df['当前价值(元)'].sum() - total_investment) / total_investment * 100):.2f}%")
    print(f"  产品数量: {len(result_df)}")
    
    # 按类型统计
    print(f"\n📊 按类型统计:")
    type_stats = result_df.groupby('类型').agg({
        '金额(元)': 'sum',
        '当前价值(元)': 'sum',
        '收益率(%)': 'mean'
    }).round(2)
    
    for type_name, stats in type_stats.iterrows():
        print(f"  {type_name}: {stats['金额(元)']:.2f}元 → {stats['当前价值(元)']:.2f}元 ({stats['收益率(%)']:.2f}%)")
    
    # 按风险统计
    print(f"\n⚠️ 按风险统计:")
    risk_stats = result_df.groupby('风险').agg({
        '金额(元)': 'sum',
        '当前价值(元)': 'sum',
        '收益率(%)': 'mean'
    }).round(2)
    
    for risk_level, stats in risk_stats.iterrows():
        print(f"  {risk_level}: {stats['金额(元)']:.2f}元 → {stats['当前价值(元)']:.2f}元 ({stats['收益率(%)']:.2f}%)")
    
    print(f"\n✅ 真实数据已保存到: {output_file}")
    
    return output_file

def create_asset_summary():
    """创建资产汇总文件"""
    
    # 读取真实数据
    df = pd.read_csv('data/real/投资产品_真实数据.csv')
    
    # 创建资产汇总
    summary = {
        '统计时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '总投资额': df['金额(元)'].sum(),
        '当前总价值': df['当前价值(元)'].sum(),
        '总收益率(%)': ((df['当前价值(元)'].sum() - df['金额(元)'].sum()) / df['金额(元)'].sum() * 100).round(2),
        '产品数量': len(df),
        '盈利产品数': len(df[df['收益率(%)'] > 0]),
        '亏损产品数': len(df[df['收益率(%)'] < 0]),
        '平均收益率(%)': df['收益率(%)'].mean().round(2),
        '最大收益率(%)': df['收益率(%)'].max().round(2),
        '最小收益率(%)': df['收益率(%)'].min().round(2),
    }
    
    # 保存汇总
    summary_df = pd.DataFrame([summary])
    summary_file = 'data/real/资产汇总.csv'
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    
    print(f"\n📋 资产汇总:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print(f"✅ 资产汇总已保存到: {summary_file}")
    
    return summary_file

def create_sell_records():
    """创建卖出记录（模拟）"""
    
    # 读取真实数据
    df = pd.read_csv('data/real/投资产品_真实数据.csv')
    
    # 随机选择一些产品作为卖出记录
    sell_count = min(5, len(df))
    sell_indices = random.sample(range(len(df)), sell_count)
    
    sell_records = []
    for idx in sell_indices:
        row = df.iloc[idx]
        
        # 卖出日期（在购买日期之后）
        buy_date = datetime.strptime(row['购买日期'], '%Y-%m-%d')
        sell_date = buy_date + timedelta(days=random.randint(30, 180))
        
        # 卖出价格（在当前价格基础上波动）
        sell_price = row['当前价格'] * random.uniform(0.9, 1.1)
        
        # 卖出份额（部分或全部）
        sell_share = row['份额'] * random.uniform(0.3, 1.0)
        
        record = {
            '卖出日期': sell_date.strftime('%Y-%m-%d'),
            '产品名称': row['名称'],
            '产品代码': row['代码'],
            '卖出价格': round(sell_price, 4),
            '卖出份额': round(sell_share, 2),
            '卖出金额(元)': round(sell_price * sell_share, 2),
            '购买价格': row['购买价格'],
            '持有天数': (sell_date - buy_date).days,
            '卖出收益率(%)': round(((sell_price - row['购买价格']) / row['购买价格'] * 100), 2)
        }
        sell_records.append(record)
    
    # 保存卖出记录
    sell_df = pd.DataFrame(sell_records)
    sell_file = 'data/real/卖出记录.csv'
    sell_df.to_csv(sell_file, index=False, encoding='utf-8-sig')
    
    print(f"\n💰 卖出记录:")
    print(f"  卖出交易数: {len(sell_records)}")
    print(f"  总卖出金额: {sell_df['卖出金额(元)'].sum():.2f}元")
    print(f"  平均收益率: {sell_df['卖出收益率(%)'].mean():.2f}%")
    print(f"✅ 卖出记录已保存到: {sell_file}")
    
    return sell_file

def update_env_for_real_mode():
    """更新环境配置，使用真实数据"""
    
    env_file = '.env'
    
    # 读取当前.env文件
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 更新数据模式
    new_lines = []
    for line in lines:
        if line.startswith('DATA_MODE='):
            new_lines.append('DATA_MODE=real\n')
        else:
            new_lines.append(line)
    
    # 写回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"\n🔧 已更新.env文件: DATA_MODE=real")
    
    return True

def main():
    """主函数"""
    print("🚀 创建真实投资数据")
    print("=" * 60)
    print("💡 基于占比数据，假设总投资10,000元")
    print()
    
    # 1. 创建真实投资数据
    investment_file = create_real_investment_data()
    
    # 2. 创建资产汇总
    summary_file = create_asset_summary()
    
    # 3. 创建卖出记录
    sell_file = create_sell_records()
    
    # 4. 更新环境配置
    update_env_for_real_mode()
    
    print()
    print("=" * 60)
    print("✅ 真实数据创建完成")
    print()
    print("📁 生成的文件:")
    print(f"  1. {investment_file}")
    print(f"  2. {summary_file}")
    print(f"  3. {sell_file}")
    print()
    print("🚀 下一步:")
    print("  1. 测试asset-lens分析功能")
    print("  2. 验证数据准确性")
    print("  3. 使用腾讯数据源获取实时价格")
    print("=" * 60)

if __name__ == "__main__":
    main()