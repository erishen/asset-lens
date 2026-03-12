#!/usr/bin/env python3
"""
腾讯数据源快捷脚本
直接使用腾讯数据源，绕过AkShare的网络问题
"""

import sys
import json
from datetime import datetime
from tencent_data_fetcher import TencentDataFetcher

def quick_market_report():
    """快速市场报告"""
    fetcher = TencentDataFetcher()
    
    # 主要指数
    indices = [
        ('sh000001', '上证指数'),
        ('sz399001', '深证成指'),
        ('sz399006', '创业板指'),
        ('sh000300', '沪深300'),
        ('sh000905', '中证500')
    ]
    
    print('📈 腾讯数据源实时行情')
    print('=' * 60)
    print(f'⏰ 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    results = []
    for code, name in indices:
        data = fetcher.get_index_data(code)
        if data:
            trend = '🟢' if data['change_pct'] > 0 else '🔴'
            results.append({
                'name': name,
                'price': data['price'],
                'change': data['change_pct'],
                'trend': trend
            })
            print(f'{trend} {name:10} {data["price"]:>8.2f} ({data["change_pct"]:>+7.2f}%)')
    
    # 保存到文件
    if results:
        report = {
            'timestamp': datetime.now().isoformat(),
            'data_source': 'tencent',
            'indices': results,
            'summary': {
                'up_count': len([r for r in results if r['change'] > 0]),
                'down_count': len([r for r in results if r['change'] < 0]),
                'total': len(results)
            }
        }
        
        import os
        os.makedirs('output/tencent_reports', exist_ok=True)
        filename = f'output/tencent_reports/market_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print()
        print(f'📄 报告已保存: {filename}')
    
    print()
    print('=' * 60)
    print('🎯 数据源: 腾讯财经（机器在腾讯，延迟最小）')
    print('💡 提示: 此脚本绕过AkShare，直接使用腾讯API')

def quick_stock_check(codes):
    """快速股票检查"""
    fetcher = TencentDataFetcher()
    
    if not codes:
        codes = ['sh600519', 'sz000858', 'sh600036']
    
    print('📊 股票实时行情')
    print('=' * 60)
    
    for code in codes:
        data = fetcher.get_stock_data(code)
        if data:
            trend = '🟢' if data['change_pct'] > 0 else '🔴'
            print(f'{trend} {data["name"]:10} {data["price"]:>8.2f} ({data["change_pct"]:>+7.2f}%)')
        else:
            print(f'❌ {code}: 获取失败')
    
    print()
    print('=' * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "stock":
            quick_stock_check(sys.argv[2:])
        else:
            print('用法: python3 quick_tencent.py [stock 代码1 代码2 ...]')
    else:
        quick_market_report()
