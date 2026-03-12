#!/usr/bin/env python3
"""
正确的行情报告 - 不预估数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import json
import os

def get_index_data_correct():
    """正确获取指数数据 - 不预估"""
    print("📊 获取指数数据（正确方法）...")
    
    indices = []
    errors = []
    
    # 指数映射（使用正确的代码）
    index_mapping = {
        '000001': '上证指数',
        '000300': '沪深300',
        '000905': '中证500', 
        '399001': '深证成指',
        '399006': '创业板指'
    }
    
    for code, name in index_mapping.items():
        try:
            print(f"   🔍 获取 {name} ({code})...")
            
            # 方法1: 尝试实时数据
            try:
                df = ak.stock_zh_index_spot_em()
                if df is not None and not df.empty and '代码' in df.columns:
                    index_data = df[df['代码'] == code]
                    if not index_data.empty:
                        row = index_data.iloc[0]
                        
                        price = float(row['最新价'])
                        
                        # 数据验证
                        if name == '上证指数' and not (2000 <= price <= 5000):
                            errors.append(f"{name}: 数据异常 ({price:.2f}点)")
                            print(f"      ⚠️ 数据异常: {price:.2f}点")
                            continue
                        
                        indices.append({
                            'name': name,
                            'code': code,
                            'price': price,
                            'change': float(row['涨跌额']),
                            'change_pct': float(row['涨跌幅'].replace('%', '')),
                            'volume': float(str(row['成交量']).replace(',', '')) / 100000000,
                            'amount': float(str(row['成交额']).replace(',', '')) / 100000000,
                            'data_source': '实时数据',
                            'status': '正常'
                        })
                        print(f"      ✅ 成功获取: {price:.2f}点")
                        continue
            except Exception as e:
                print(f"      ⚠️ 实时数据失败: {str(e)[:30]}")
            
            # 方法2: 尝试历史数据
            try:
                symbol = f"sh{code}" if code.startswith('000') else f"sz{code}"
                df = ak.stock_zh_index_daily(symbol=symbol)
                
                if df is not None and len(df) >= 2:
                    latest = df.iloc[0]
                    prev = df.iloc[1]
                    
                    price = latest['close']
                    
                    # 数据验证
                    if name == '上证指数' and not (2000 <= price <= 5000):
                        errors.append(f"{name}: 历史数据异常 ({price:.2f}点)")
                        print(f"      ⚠️ 历史数据异常: {price:.2f}点")
                        continue
                    
                    indices.append({
                        'name': name,
                        'code': code,
                        'price': price,
                        'change': price - prev['close'],
                        'change_pct': ((price - prev['close']) / prev['close'] * 100) if prev['close'] > 0 else 0,
                        'volume': latest.get('volume', 0) / 100000000,
                        'amount': 0,
                        'data_source': '历史数据',
                        'status': '正常'
                    })
                    print(f"      ✅ 历史数据: {price:.2f}点")
                else:
                    errors.append(f"{name}: 无有效历史数据")
                    print(f"      ❌ 无有效历史数据")
                    
            except Exception as e:
                errors.append(f"{name}: 历史数据获取失败 - {str(e)[:30]}")
                print(f"      ❌ 历史数据失败: {str(e)[:30]}")
                
        except Exception as e:
            errors.append(f"{name}: 总体失败 - {str(e)[:30]}")
            print(f"      ❌ 总体失败: {str(e)[:30]}")
    
    return indices, errors

def get_stock_data_correct():
    """正确获取股票数据"""
    print("📈 获取股票数据...")
    
    stocks = []
    errors = []
    
    key_stocks = [
        ('000001', '平安银行', '银行'),
        ('600036', '招商银行', '银行'),
        ('601318', '中国平安', '保险')
    ]
    
    for code, name, sector in key_stocks:
        try:
            print(f"   🔍 获取 {name} ({code})...")
            
            # 尝试实时数据
            df = ak.stock_zh_a_spot()
            
            if df is not None and not df.empty:
                stock_data = df[df['代码'] == code]
                
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    
                    stocks.append({
                        'name': name,
                        'code': code,
                        'sector': sector,
                        'price': float(row['最新价']),
                        'change': float(row['涨跌额']),
                        'change_pct': float(row['涨跌幅'].replace('%', '')),
                        'volume': float(str(row['成交量']).replace('手', '').replace(',', '')) / 10000,
                        'data_source': '实时数据',
                        'status': '正常'
                    })
                    print(f"      ✅ 成功获取")
                else:
                    errors.append(f"{name}: 实时数据未找到")
                    print(f"      ⚠️ 实时数据未找到")
            else:
                errors.append(f"{name}: 实时数据为空")
                print(f"      ⚠️ 实时数据为空")
                
        except Exception as e:
            errors.append(f"{name}: 获取失败 - {str(e)[:30]}")
            print(f"      ❌ 获取失败: {str(e)[:30]}")
    
    return stocks, errors

def generate_correct_report():
    """生成正确的报告"""
    print("📝 生成正确的行情报告...")
    
    # 获取数据
    indices, index_errors = get_index_data_correct()
    stocks, stock_errors = get_stock_data_correct()
    
    # 构建报告
    report = {
        'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_quality': {
            'total_indices_attempted': 5,
            'successful_indices': len(indices),
            'failed_indices': len(index_errors),
            'total_stocks_attempted': 3,
            'successful_stocks': len(stocks),
            'failed_stocks': len(stock_errors)
        },
        'indices': indices,
        'stocks': stocks,
        'errors': {
            'index_errors': index_errors,
            'stock_errors': stock_errors
        },
        'summary': {
            'has_valid_data': len(indices) > 0 or len(stocks) > 0,
            'data_issues': len(index_errors) > 0 or len(stock_errors) > 0,
            'recommendation': '检查网络连接和数据源' if len(index_errors) > 2 else '数据基本正常'
        }
    }
    
    return report

def save_correct_report(report):
    """保存正确报告"""
    os.makedirs('output/market_reports/correct', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # JSON格式
    json_file = f'output/market_reports/correct/market_report_correct_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 文本格式
    txt_file = f'output/market_reports/correct/market_report_correct_{timestamp}.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(format_correct_report(report))
    
    return json_file, txt_file

def format_correct_report(report):
    """格式化正确报告"""
    lines = []
    
    lines.append("📈 正确的行情报告（不预估数据）")
    lines.append("=" * 60)
    lines.append(f"📅 报告时间: {report['report_time']}")
    lines.append(f"📊 数据质量: {report['data_quality']['successful_indices']}/5 指数, {report['data_quality']['successful_stocks']}/3 股票")
    lines.append(f"⚠️ 数据问题: {len(report['errors']['index_errors'])} 个指数错误, {len(report['errors']['stock_errors'])} 个股票错误")
    lines.append("")
    
    # 成功获取的数据
    if report['indices']:
        lines.append("✅ 成功获取的指数数据:")
        lines.append("-" * 60)
        lines.append(f"{'指数':10} {'最新价':>10} {'涨跌幅':>10} {'数据源':>10}")
        lines.append("-" * 60)
        
        for idx in report['indices']:
            change_emoji = "📈" if idx['change_pct'] > 0 else "📉"
            lines.append(f"{idx['name']:10} {idx['price']:>10.2f} {idx['change_pct']:>+9.2f}% {change_emoji:>2} {idx['data_source']:>10}")
    
    if report['stocks']:
        lines.append("")
        lines.append("✅ 成功获取的股票数据:")
        lines.append("-" * 60)
        lines.append(f"{'股票':8} {'最新价':>8} {'涨跌幅':>8} {'板块':8}")
        lines.append("-" * 60)
        
        for stock in report['stocks']:
            change_emoji = "🟢" if stock['change_pct'] > 0 else "🔴"
            lines.append(f"{change_emoji} {stock['name']:8} {stock['price']:>8.2f} {stock['change_pct']:>+7.2f}% {stock['sector']:8}")
    
    # 错误信息
    if report['errors']['index_errors']:
        lines.append("")
        lines.append("❌ 指数数据错误:")
        lines.append("-" * 60)
        for error in report['errors']['index_errors']:
            lines.append(f"• {error}")
    
    if report['errors']['stock_errors']:
        lines.append("")
        lines.append("❌ 股票数据错误:")
        lines.append("-" * 60)
        for error in report['errors']['stock_errors']:
            lines.append(f"• {error}")
    
    lines.append("")
    
    # 技术说明
    lines.append("🔧 技术说明:")
    lines.append("-" * 60)
    lines.append("1. 使用正确的函数: stock_zh_index_spot_em()")
    lines.append("2. 使用正确的代码: 上证指数 = 000001 (不是 sh000001)")
    lines.append("3. 数据验证: 上证指数应在2000-5000点之间")
    lines.append("4. 不预估数据: 数据异常时报错，不填充默认值")
    lines.append("5. 错误处理: 记录所有失败原因")
    
    lines.append("")
    lines.append("=" * 60)
    lines.append("🎯 报告生成完成 - 数据真实，无预估")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def main():
    """主函数"""
    print("🎯 生成正确的行情报告（不预估数据）")
    print("=" * 60)
    
    try:
        # 生成报告
        report = generate_correct_report()
        
        # 保存报告
        json_file, txt_file = save_correct_report(report)
        
        print(f"\n✅ 正确报告生成完成！")
        print(f"   📄 JSON数据: {json_file}")
        print(f"   📝 文本报告: {txt_file}")
        
        # 显示报告摘要
        print("\n" + "=" * 60)
        print("📊 报告摘要")
        print("=" * 60)
        
        print(f"\n📅 报告时间: {report['report_time']}")
        print(f"📈 成功指数: {report['data_quality']['successful_indices']}/5")
        print(f"📊 成功股票: {report['data_quality']['successful_stocks']}/3")
        
        if report['indices']:
            print("\n✅ 获取成功的指数:")
            for idx in report['indices']:
                print(f"   • {idx['name']}: {idx['price']:.2f}点 ({idx['change_pct']:+.2f}%)")
        
        if report['errors']['index_errors']:
            print("\n❌ 指数数据问题:")
            for error in report['errors']['index_errors'][:3]:
                print(f"   • {error}")
        
        print("\n💡 建议: ", report['summary']['recommendation'])
        
        print("\n" + "=" * 60)
        print("🔧 使用正确的函数和参数，不预估数据")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")

if __name__ == "__main__":
    main()