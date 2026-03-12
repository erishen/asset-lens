#!/usr/bin/env python3
"""
腾讯数据源获取器
专门使用腾讯财经数据源，机器在腾讯那，延迟最小
"""

import requests
import json
from datetime import datetime
from typing import Dict, Optional
import re

class TencentDataFetcher:
    """腾讯财经数据获取器"""
    
    def __init__(self):
        self.base_url = "https://qt.gtimg.cn/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def parse_tencent_data(self, raw_data: str) -> Dict:
        """解析腾讯财经数据格式"""
        # 格式: v_sh000001="1~上证指数~000001~价格~..."
        if not raw_data or '=' not in raw_data:
            return {}
        
        try:
            # 提取数据部分
            data_str = raw_data.split('="')[1].rstrip('";')
            fields = data_str.split('~')
            
            if len(fields) < 40:
                return {}
            
            return {
                'name': fields[1],          # 名称
                'code': fields[2],          # 代码
                'price': float(fields[3]),  # 最新价
                'prev_close': float(fields[4]),  # 昨收
                'open': float(fields[5]),   # 今开
                'high': float(fields[33]),  # 最高
                'low': float(fields[34]),   # 最低
                'volume': float(fields[36]),  # 成交量(手)
                'amount': float(fields[37]),  # 成交额(万)
                'change': float(fields[31]),  # 涨跌额
                'change_pct': float(fields[32]),  # 涨跌幅
                'time': fields[30],         # 时间
                'status': '正常'
            }
        except Exception as e:
            print(f"解析失败: {e}")
            return {}
    
    def get_index_data(self, code: str) -> Optional[Dict]:
        """获取指数数据"""
        # 腾讯代码格式: sh000001, sz399001
        url = f"{self.base_url}q={code}"
        
        try:
            response = self.session.get(url, timeout=5)
            response.encoding = 'gbk'
            
            if response.status_code == 200:
                data = self.parse_tencent_data(response.text)
                if data:
                    data['source'] = '腾讯财经'
                    data['fetch_time'] = datetime.now().isoformat()
                    return data
            else:
                print(f"请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"获取数据失败: {e}")
        
        return None
    
    def get_stock_data(self, code: str) -> Optional[Dict]:
        """获取股票数据"""
        # A股代码: sh600519, sz000858
        return self.get_index_data(code)
    
    def get_multiple_data(self, codes: list) -> Dict[str, Dict]:
        """批量获取数据"""
        if not codes:
            return {}
        
        # 腾讯支持批量查询，用逗号分隔
        code_str = ','.join(codes)
        url = f"{self.base_url}q={code_str}"
        
        results = {}
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'gbk'
            
            if response.status_code == 200:
                lines = response.text.strip().split(';')
                for line in lines:
                    if line:
                        data = self.parse_tencent_data(line + ';')
                        if data and 'code' in data:
                            results[data['code']] = data
        
        except Exception as e:
            print(f"批量获取失败: {e}")
        
        return results

def test_tencent_fetcher():
    """测试腾讯数据获取器"""
    print("🚀 测试腾讯数据源（机器在腾讯那，延迟最小）")
    print("=" * 60)
    
    fetcher = TencentDataFetcher()
    
    # 测试主要指数
    test_codes = [
        'sh000001',  # 上证指数
        'sz399001',  # 深证成指
        'sz399006',  # 创业板指
        'sh000300',  # 沪深300
    ]
    
    print("📊 获取主要指数数据:")
    print("-" * 60)
    
    for code in test_codes:
        data = fetcher.get_index_data(code)
        if data:
            print(f"✅ {data['name']}({data['code']}):")
            print(f"   最新价: {data['price']:.2f}")
            print(f"   涨跌幅: {data['change_pct']:.2f}%")
            print(f"   成交量: {data['volume']/10000:.2f}万手")
            print(f"   时间: {data['time']}")
            print(f"   数据源: {data['source']}")
            print()
        else:
            print(f"❌ {code}: 获取失败")
    
    # 测试批量获取
    print("📈 批量获取测试:")
    print("-" * 60)
    
    batch_results = fetcher.get_multiple_data(test_codes[:2])
    print(f"批量获取成功: {len(batch_results)} 个指数")
    
    # 测试股票
    print("\n📈 测试股票数据:")
    print("-" * 60)
    
    stock_codes = ['sh600519', 'sz000858']  # 贵州茅台, 五粮液
    for code in stock_codes:
        data = fetcher.get_stock_data(code)
        if data:
            print(f"✅ {data['name']}: {data['price']:.2f} ({data['change_pct']:+.2f}%)")
        else:
            print(f"❌ {code}: 获取失败")
    
    print()
    print("=" * 60)
    print("🎯 腾讯数据源测试完成")
    print("💡 优势: 机器在腾讯，延迟最小，访问稳定")
    print("📊 支持: 指数、股票、批量查询")
    print("=" * 60)

def get_market_report():
    """获取市场报告"""
    print("📈 腾讯数据源市场报告")
    print("=" * 60)
    
    fetcher = TencentDataFetcher()
    
    # 主要市场指数
    indices = {
        'sh000001': '上证指数',
        'sz399001': '深证成指', 
        'sz399006': '创业板指',
        'sh000300': '沪深300',
        'sh000905': '中证500'
    }
    
    print("🏆 市场表现:")
    print("-" * 60)
    
    market_data = []
    for code, name in indices.items():
        data = fetcher.get_index_data(code)
        if data:
            market_data.append(data)
            trend = "📈" if data['change_pct'] > 0 else "📉"
            print(f"{trend} {name}: {data['price']:.2f} ({data['change_pct']:+.2f}%)")
    
    if market_data:
        # 计算市场状态
        up_count = len([d for d in market_data if d['change_pct'] > 0])
        total = len(market_data)
        
        print()
        print("📊 市场状态:")
        print("-" * 60)
        print(f"上涨指数: {up_count}/{total}")
        print(f"下跌指数: {total-up_count}/{total}")
        
        if up_count / total >= 0.7:
            print("📈 市场状态: 强势")
        elif up_count / total >= 0.4:
            print("↔️ 市场状态: 震荡")
        else:
            print("📉 市场状态: 弱势")
    
    print()
    print("💡 数据源: 腾讯财经（机器在腾讯，延迟最小）")
    print("⏰ 报告时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

if __name__ == "__main__":
    # 测试数据获取器
    test_tencent_fetcher()
    
    print("\n" + "=" * 60)
    print("📋 市场报告")
    print("=" * 60)
    
    get_market_report()