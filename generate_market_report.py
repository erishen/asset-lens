#!/usr/bin/env python3
"""
生成详细行情报告
包括技术分析、投资建议和市场展望
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

def get_market_data():
    """获取市场数据"""
    print("📈 获取市场数据...")
    
    today = datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    data = {
        'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'indices': [],
        'stocks': [],
        'sectors': [],
        'analysis': {}
    }
    
    # 1. 获取指数数据
    print("  1. 获取指数数据...")
    indices = [
        ('sh000001', '上证指数', '大盘'),
        ('sz399001', '深证成指', '大盘'),
        ('sz399006', '创业板指', '成长'),
        ('sh000300', '沪深300', '蓝筹'),
        ('sh000905', '中证500', '中小盘'),
        ('sz399005', '中小板指', '中小盘')
    ]
    
    for code, name, category in indices:
        try:
            df = ak.stock_zh_index_daily(symbol=code)
            if len(df) >= 2:
                latest = df.iloc[0]
                prev = df.iloc[1]
                
                change = latest['close'] - prev['close']
                change_pct = (change / prev['close']) * 100
                
                # 计算技术指标
                ma5 = df['close'].head(5).mean() if len(df) >= 5 else latest['close']
                ma20 = df['close'].head(20).mean() if len(df) >= 20 else latest['close']
                
                data['indices'].append({
                    'name': name,
                    'code': code,
                    'category': category,
                    'price': round(latest['close'], 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'volume': round(latest.get('volume', 0) / 100000000, 2),
                    'ma5': round(ma5, 2),
                    'ma20': round(ma20, 2),
                    'trend': '上涨' if latest['close'] > ma5 else '下跌',
                    'support': round(min(df['close'].head(20)) if len(df) >= 20 else latest['close'], 2),
                    'resistance': round(max(df['close'].head(20)) if len(df) >= 20 else latest['close'], 2)
                })
        except Exception as e:
            print(f"      ❌ {name}获取失败: {e}")
    
    # 2. 获取重点股票数据
    print("  2. 获取重点股票数据...")
    key_stocks = [
        # 金融
        ('000001', '平安银行', '银行'),
        ('600036', '招商银行', '银行'),
        ('601318', '中国平安', '保险'),
        ('601988', '中国银行', '银行'),
        
        # 消费
        ('600519', '贵州茅台', '白酒'),
        ('000858', '五粮液', '白酒'),
        ('000333', '美的集团', '家电'),
        ('000651', '格力电器', '家电'),
        
        # 科技
        ('300750', '宁德时代', '新能源'),
        ('002475', '立讯精密', '消费电子'),
        ('000725', '京东方A', '面板'),
        ('002241', '歌尔股份', '消费电子'),
        ('300782', '卓胜微', '半导体'),
        
        # 医药
        ('600276', '恒瑞医药', '医药'),
        ('000538', '云南白药', '医药'),
        
        # 周期
        ('601857', '中国石油', '石油'),
        ('600028', '中国石化', '石化'),
        ('601088', '中国神华', '煤炭')
    ]
    
    for code, name, sector in key_stocks:
        try:
            df = ak.stock_zh_a_hist(symbol=code, period='daily', start_date='20240101', end_date=today, adjust='')
            if len(df) >= 2:
                latest = df.iloc[0]
                
                # 计算技术指标
                close_prices = df['收盘'].head(20).values if len(df) >= 20 else df['收盘'].values
                ma5 = df['收盘'].head(5).mean() if len(df) >= 5 else latest['收盘']
                ma20 = df['收盘'].head(20).mean() if len(df) >= 20 else latest['收盘']
                
                # 计算RSI（简化版）
                gains = []
                losses = []
                for i in range(1, min(15, len(df))):
                    change = df.iloc[i-1]['收盘'] - df.iloc[i]['收盘']
                    if change > 0:
                        gains.append(change)
                    else:
                        losses.append(abs(change))
                
                avg_gain = np.mean(gains) if gains else 0
                avg_loss = np.mean(losses) if losses else 0
                rsi = 100 - (100 / (1 + (avg_gain / avg_loss if avg_loss > 0 else 1)))
                
                data['stocks'].append({
                    'name': name,
                    'code': code,
                    'sector': sector,
                    'price': round(latest['收盘'], 2),
                    'change': round(latest['涨跌幅'], 2),
                    'change_pct': round(latest['涨跌幅'], 2),
                    'volume': round(latest['成交量'] / 10000, 2),
                    'turnover': round(latest['成交额'] / 100000000, 2),
                    'ma5': round(ma5, 2),
                    'ma20': round(ma20, 2),
                    'rsi': round(rsi, 1),
                    'trend': '强势' if latest['收盘'] > ma20 else '弱势',
                    'volatility': round(df['涨跌幅'].std(), 2) if len(df) > 1 else 0
                })
        except Exception as e:
            print(f"      ❌ {name}获取失败: {e}")
    
    return data

def analyze_market(data):
    """分析市场数据"""
    print("  3. 分析市场数据...")
    
    analysis = {
        'market_status': '',
        'sector_performance': {},
        'technical_signals': {},
        'risk_level': '',
        'investment_advice': []
    }
    
    # 市场状态
    up_indices = len([i for i in data['indices'] if i['change_pct'] > 0])
    total_indices = len(data['indices'])
    
    if up_indices / total_indices >= 0.7:
        analysis['market_status'] = '强势市场'
    elif up_indices / total_indices >= 0.4:
        analysis['market_status'] = '震荡市场'
    else:
        analysis['market_status'] = '弱势市场'
    
    # 板块表现
    sectors = {}
    for stock in data['stocks']:
        sector = stock['sector']
        if sector not in sectors:
            sectors[sector] = {'stocks': [], 'avg_change': 0}
        sectors[sector]['stocks'].append(stock)
    
    for sector, info in sectors.items():
        if info['stocks']:
            avg_change = sum(s['change_pct'] for s in info['stocks']) / len(info['stocks'])
            sectors[sector]['avg_change'] = round(avg_change, 2)
    
    # 按平均涨跌幅排序
    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1]['avg_change'], reverse=True)
    analysis['sector_performance'] = {sector: info['avg_change'] for sector, info in sorted_sectors}
    
    # 技术信号
    technical_signals = {
        'bullish_signals': [],
        'bearish_signals': [],
        'neutral_signals': []
    }
    
    # 检查主要指数技术面
    for idx in data['indices']:
        if idx['price'] > idx['ma20'] and idx['ma5'] > idx['ma20']:
            technical_signals['bullish_signals'].append(f"{idx['name']}: 均线多头排列")
        elif idx['price'] < idx['ma20'] and idx['ma5'] < idx['ma20']:
            technical_signals['bearish_signals'].append(f"{idx['name']}: 均线空头排列")
        else:
            technical_signals['neutral_signals'].append(f"{idx['name']}: 震荡整理")
    
    analysis['technical_signals'] = technical_signals
    
    # 风险等级
    avg_volatility = np.mean([s['volatility'] for s in data['stocks'] if s['volatility'] > 0])
    if avg_volatility > 3:
        analysis['risk_level'] = '高风险'
    elif avg_volatility > 2:
        analysis['risk_level'] = '中风险'
    else:
        analysis['risk_level'] = '低风险'
    
    # 投资建议
    advice = []
    
    # 基于板块表现的建议
    top_sectors = list(sorted_sectors[:3])
    for sector, info in top_sectors:
        if info['avg_change'] > 1:
            advice.append(f"关注{sector}板块: 近期表现强势，平均涨幅{info['avg_change']}%")
    
    # 基于技术面的建议
    if len(technical_signals['bullish_signals']) > len(technical_signals['bearish_signals']):
        advice.append("技术面偏多: 多数指数呈现多头排列")
    elif len(technical_signals['bearish_signals']) > len(technical_signals['bullish_signals']):
        advice.append("技术面偏空: 注意风险控制")
    else:
        advice.append("技术面震荡: 建议观望或短线操作")
    
    # 基于风险等级的建议
    if analysis['risk_level'] == '高风险':
        advice.append("市场波动较大: 建议降低仓位，控制风险")
    elif analysis['risk_level'] == '中风险':
        advice.append("市场正常波动: 可适度参与，注意止损")
    else:
        advice.append("市场波动较小: 适合稳健投资")
    
    analysis['investment_advice'] = advice
    
    data['analysis'] = analysis
    return data

def generate_report(data):
    """生成报告文件"""
    print("  4. 生成报告文件...")
    
    # 创建目录
    os.makedirs('output/market_reports', exist_ok=True)
    os.makedirs('output/market_reports/detailed', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # 1. JSON格式详细数据
    json_file = f'output/market_reports/detailed/market_report_detailed_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # 2. 文本格式简明报告
    txt_file = f'output/market_reports/market_report_{timestamp}.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(generate_text_report(data))
    
    # 3. HTML格式报告（可选）
    html_file = f'output/market_reports/detailed/market_report_{timestamp}.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(generate_html_report(data))
    
    return json_file, txt_file, html_file

def generate_text_report(data):
    """生成文本格式报告"""
    lines = []
    
    lines.append("📈 详细行情分析报告")
    lines.append("=" * 80)
    lines.append(f"📅 报告时间: {data['report_time']}")
    lines.append(f"📊 市场状态: {data['analysis']['market_status']}")
    lines.append(f"⚠️ 风险等级: {data['analysis']['risk_level']}")
    lines.append("")
    
    # 指数行情
    lines.append("一、📊 主要指数行情")
    lines.append("-" * 80)
    lines.append(f"{'指数':10} {'最新价':>8} {'涨跌幅':>8} {'趋势':>6} {'MA5':>8} {'MA20':>8}")
    lines.append("-" * 80)
    
    for idx in data['indices']:
        trend_emoji = "📈" if idx['change_pct'] > 0 else "📉"
        lines.append(f"{idx['name']:10} {idx['price']:>8.2f} {idx['change_pct']:>+7.2f}% {trend_emoji:>3} {idx['ma5']:>8.2f} {idx['ma20']:>8.2f}")
    
    lines.append("")
    
    # 板块表现
    lines.append("二、🏷️ 板块表现排名")
    lines.append("-" * 80)
    
    for i, (sector, avg_change) in enumerate(data['analysis']['sector_performance'].items(), 1):
        emoji = "🟢" if avg_change > 0 else "🔴"
        lines.append(f"{emoji} {i:2d}. {sector:10} 平均涨跌幅: {avg_change:>+6.2f}%")
    
    lines.append("")
    
    # 重点股票
    lines.append("三、🏆 重点股票表现")
    lines.append("-" * 80)
    lines.append(f"{'股票':8} {'代码':8} {'最新价':>8} {'涨跌幅':>8} {'板块':8} {'RSI':>6} {'趋势':>6}")
    lines.append("-" * 80)
    
    # 按涨跌幅排序
    sorted_stocks = sorted(data['stocks'], key=lambda x: x['change_pct'], reverse=True)
    
    for stock in sorted_stocks[:15]:  # 显示前15只
        trend = "强势" if stock['trend'] == '强势' else "弱势"
        rsi_status = "超买" if stock['rsi'] > 70 else "超卖" if stock['rsi'] < 30 else "正常"
        lines.append(f"{stock['name']:8} {stock['code']:8} {stock['price']:>8.2f} {stock['change_pct']:>+7.2f}% {stock['sector']:8} {rsi_status:>6} {trend:>6}")
    
    lines.append("")
    
    # 技术信号
    lines.append("四、📈 技术信号分析")
    lines.append("-" * 80)
    
    signals = data['analysis']['technical_signals']
    if signals['bullish_signals']:
        lines.append("✅ 看多信号:")
        for signal in signals['bullish_signals'][:5]:
            lines.append(f"   • {signal}")
    
    if signals['bearish_signals']:
        lines.append("")
        lines.append("❌ 看空信号:")
        for signal in signals['bearish_signals'][:5]:
            lines.append(f"   • {signal}")
    
    lines.append("")
    
    # 投资建议
    lines.append("五、💡 投资建议")
    lines.append("-" * 80)
    
    for i, advice in enumerate(data['analysis']['investment_advice'], 1):
        lines.append(f"{i:2d}. {advice}")
    
    lines.append("")
    
    # 风险提示
    lines.append("六、⚠️ 风险提示")
    lines.append("-" * 80)
    lines.append("1. 本报告基于公开数据，仅供参考")
    lines.append("2. 投资有风险，入市需谨慎")
    lines.append("3. 建议结合个人风险承受能力决策")
    lines.append("4. 过往表现不代表未来收益")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("📊 报告生成完成")
    lines.append("=" * 80)
    
    return "\n".join(lines)

def generate_html_report(data):
    """生成HTML格式报告"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>行情分析报告 - {data['report_time']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .section-title {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .up {{ color: green; }}
        .down {{ color: red; }}
        .advice {{ background: #e8f5e8; padding: 10px; border-left: 4px solid #4CAF50; margin: 10px 0; }}
        .warning {{ background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; }}
        .risk-high {{ color: #dc3545; font-weight: bold; }}
        .risk-medium {{ color: #ffc107; font-weight: bold; }}
        .risk-low {{ color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 详细行情分析报告</h1>
        <p><strong>报告时间:</strong> {data['report_time']}</p>
        <p><strong>市场状态:</strong> {data['analysis']['market_status']}</p>
        <p><strong>风险等级:</strong> 
            <span class="risk-{data['analysis']['risk_level'].replace('风险', '').lower()}">
                {data['analysis']['risk_level']}
            </span>
        </p>
    </div>
    
    <div class="section">
        <h2 class="section-title">一、📊 主要指数行情</h2>
        <table>
            <tr>
                <th>指数</th>
                <th>最新价</th>
                <th>涨跌幅</th>
                <th>趋势</th>
                <th>MA5</th>
                <th>MA20</th>
                <th>支撑位</th>
                <th>阻力位</th>
            </tr>
"""
    
    # 添加指数数据
    for idx in data['indices']:
        change_class = "up" if idx['change_pct'] > 0 else "down"
        html += f"""
            <tr>
                <td>{idx['name']}</td>
                <td>{idx['price']:.2f}</td>
                <td class="{change_class}">{idx['change_pct']:+.2f}%</td>
                <td>{idx['trend']}</td>
                <td>{idx['ma5']:.2f}</td>
                <td>{idx['ma20']:.2f}</td>
                <td>{idx['support']:.2f}</td>
                <td>{idx['resistance']:.2f}</td>
            </tr>
        """
    
    html += """
        </table>
    </div>
    
    <div class="section">
        <h2 class="section-title">二、🏷️ 板块表现排名</h2>
        <table>
            <tr>
                <th>排名</th>
                <th>板块</th>
                <th>平均涨跌幅</th>
                <th>表现</th>
            </tr>
    """
    
    # 添加板块数据
    for i, (sector, avg_change) in enumerate(data['analysis']['sector_performance'].items(), 1):
        change_class = "up" if avg_change > 0 else "down"
        performance = "强势" if avg_change > 1 else "一般" if avg_change > -1 else "弱势"
        html += f"""
            <tr>
                <td>{i}</td>
                <td>{sector}</td>
                <td class="{change_class}">{avg_change:+.2f}%</td>
                <td>{performance}</td>
            </tr>
        """
    
    html += """
        </table>
    </div>
    
    <div class="section">
        <h2 class="section-title">三、🏆 重点股票表现</h2>
        <table>
            <tr>
                <th>股票</th>
                <th>代码</th>
                <th>最新价</th>
                <th>涨跌幅</th>
                <th>板块</th>
                <th>RSI</th>
                <th>趋势</th>
                <th>波动率</th>
            </tr>
    """
    
    # 添加股票数据（前15只）
    sorted_stocks = sorted(data['stocks'], key=lambda x: x['change_pct'], reverse=True)
    for stock in sorted_stocks[:15]:
        change_class = "up" if stock['change_pct'] > 0 else "down"
        rsi_status = "超买" if stock['rsi'] > 70 else "超卖" if stock['rsi'] < 30 else "正常"
        rsi_class = "risk-high" if stock['rsi'] > 70 or stock['rsi'] < 30 else ""
        
        html += f"""
            <tr>
                <td>{stock['name']}</td>
                <td>{stock['code']}</td>
                <td>{stock['price']:.2f}</td>
                <td class="{change_class}">{stock['change_pct']:+.2f}%</td>
                <td>{stock['sector']}</td>
                <td class="{rsi_class}">{stock['rsi']:.1f} ({rsi_status})</td>
                <td>{stock['trend']}</td>
                <td>{stock['volatility']:.2f}%</td>
            </tr>
        """
    
    html += """
        </table>
    </div>
    
    <div class="section">
        <h2 class="section-title">四、📈 技术信号分析</h2>
    """
    
    signals = data['analysis']['technical_signals']
    
    if signals['bullish_signals']:
        html += """
        <div class="advice">
            <h3>✅ 看多信号</h3>
            <ul>
        """
        for signal in signals['bullish_signals'][:5]:
            html += f"<li>{signal}</li>"
        html += """
            </ul>
        </div>
        """
    
    if signals['bearish_signals']:
        html += """
        <div class="warning">
            <h3>❌ 看空信号</h3>
            <ul>
        """
        for signal in signals['bearish_signals'][:5]:
            html += f"<li>{signal}</li>"
        html += """
            </ul>
        </div>
        """
    
    html += """
    </div>
    
    <div class="section">
        <h2 class="section-title">五、💡 投资建议</h2>
        <div class="advice">
            <ol>
    """
    
    for advice in data['analysis']['investment_advice']:
        html += f"<li>{advice}</li>"
    
    html += """
            </ol>
        </div>
    </div>
    
    <div class="section">
        <h2 class="section-title">六、⚠️ 风险提示</h2>
        <div class="warning">
            <ol>
                <li>本报告基于公开数据，仅供参考</li>
                <li>投资有风险，入市需谨慎</li>
                <li>建议结合个人风险承受能力决策</li>
                <li>过往表现不代表未来收益</li>
                <li>市场有风险，投资需谨慎</li>
            </ol>
        </div>
    </div>
    
    <div style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
        <p>报告生成时间: {data['report_time']}</p>
        <p>数据来源: AkShare、东方财富等公开数据</p>
        <p>免责声明: 本报告仅供参考，不构成投资建议</p>
    </div>
</body>
</html>
"""
    
    return html

def main():
    """主函数"""
    print("📈 生成详细行情报告")
    print("=" * 60)
    
    try:
        # 获取数据
        data = get_market_data()
        
        # 分析数据
        data = analyze_market(data)
        
        # 生成报告
        json_file, txt_file, html_file = generate_report(data)
        
        print(f"\n✅ 报告生成完成！")
        print(f"   📄 详细数据: {json_file}")
        print(f"   📝 文本报告: {txt_file}")
        print(f"   🌐 HTML报告: {html_file}")
        
        # 显示简要报告
        print("\n" + "=" * 60)
        print("📊 简要行情概览")
        print("=" * 60)
        
        print(f"\n📅 报告时间: {data['report_time']}")
        print(f"📈 市场状态: {data['analysis']['market_status']}")
        print(f"⚠️ 风险等级: {data['analysis']['risk_level']}")
        
        print("\n🏆 表现最佳板块:")
        sectors = list(data['analysis']['sector_performance'].items())[:3]
        for sector, change in sectors:
            emoji = "🟢" if change > 0 else "🔴"
            print(f"   {emoji} {sector}: {change:+.2f}%")
        
        print("\n📈 表现最佳股票:")
        sorted_stocks = sorted(data['stocks'], key=lambda x: x['change_pct'], reverse=True)[:5]
        for stock in sorted_stocks:
            emoji = "🚀" if stock['change_pct'] > 3 else "📈" if stock['change_pct'] > 0 else "📉"
            print(f"   {emoji} {stock['name']}: {stock['change_pct']:+.2f}%")
        
        print("\n💡 主要建议:")
        for advice in data['analysis']['investment_advice'][:3]:
            print(f"   • {advice}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()