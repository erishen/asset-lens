#!/usr/bin/env python3
"""
诊断网络功能问题
"""

import os
import sys
import requests
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

def check_env_vars():
    """检查环境变量"""
    print("🔧 检查环境变量")
    print("=" * 60)
    
    load_dotenv()
    
    env_vars = {
        'DATA_MODE': '数据模式',
        'FINNHUB_API_KEY': 'Finnhub API Key',
        'TUSHARE_TOKEN': 'Tushare Token',
        'ALPHAVANTAGE_API_KEY': 'Alpha Vantage API Key'
    }
    
    issues = []
    for key, desc in env_vars.items():
        value = os.getenv(key)
        if value:
            if 'your_' in value or 'here' in value:
                print(f"❌ {desc}: 设置为默认占位符")
                issues.append(f"{desc} 需要有效值")
            elif len(value) < 10:
                print(f"⚠️ {desc}: 值过短 ({value})")
                issues.append(f"{desc} 可能无效")
            else:
                print(f"✅ {desc}: 已设置")
        else:
            print(f"❌ {desc}: 未设置")
            issues.append(f"{desc} 未设置")
    
    return issues

def check_network_connectivity():
    """检查网络连接"""
    print("\n🌐 检查网络连接")
    print("=" * 60)
    
    test_urls = [
        ('东方财富', 'http://quote.eastmoney.com/', '主要数据源'),
        ('腾讯财经', 'https://qt.gtimg.cn/', '备用数据源'),
        ('新浪财经', 'http://hq.sinajs.cn/', 'AkShare默认源'),
        ('百度', 'http://www.baidu.com/', '网络测试')
    ]
    
    issues = []
    for name, url, purpose in test_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: 连接正常 ({purpose})")
            elif response.status_code == 403:
                print(f"❌ {name}: 访问被禁止 (403) - {purpose}")
                issues.append(f"{name} 被403禁止")
            else:
                print(f"⚠️ {name}: 状态码 {response.status_code} - {purpose}")
                issues.append(f"{name} 状态码异常")
        except requests.exceptions.Timeout:
            print(f"❌ {name}: 连接超时 - {purpose}")
            issues.append(f"{name} 连接超时")
        except Exception as e:
            print(f"❌ {name}: 错误 - {str(e)[:30]} - {purpose}")
            issues.append(f"{name} 连接错误")
    
    return issues

def check_akshare_functions():
    """检查AkShare功能"""
    print("\n📊 检查AkShare功能")
    print("=" * 60)
    
    try:
        import akshare as ak
        print(f"✅ AkShare版本: {ak.__version__}")
        
        # 测试不同数据源
        print("\n测试不同数据源接口:")
        
        # 1. 腾讯财经接口
        try:
            print("  测试 stock_zh_index_spot_em (腾讯财经)...")
            df = ak.stock_zh_index_spot_em()
            if df is not None and len(df) > 0:
                print(f"  ✅ 成功获取 {len(df)} 个指数")
            else:
                print("  ❌ 返回空数据")
        except Exception as e:
            print(f"  ❌ 失败: {str(e)[:50]}")
        
        # 2. 新浪接口
        try:
            print("  测试 stock_zh_index_spot (新浪财经)...")
            df = ak.stock_zh_index_spot()
            if df is not None and len(df) > 0:
                print(f"  ✅ 成功获取 {len(df)} 个指数")
            else:
                print("  ❌ 返回空数据")
        except Exception as e:
            print(f"  ❌ 失败: {str(e)[:50]}")
        
        # 3. 简单数据
        try:
            print("  测试 stock_info_a_code_name (A股列表)...")
            df = ak.stock_info_a_code_name()
            if df is not None and len(df) > 0:
                print(f"  ✅ 成功获取 {len(df)} 只A股")
            else:
                print("  ❌ 返回空数据")
        except Exception as e:
            print(f"  ❌ 失败: {str(e)[:50]}")
            
    except ImportError:
        print("❌ AkShare未安装")
        return ["AkShare未安装"]
    except Exception as e:
        print(f"❌ AkShare检查失败: {e}")
        return ["AkShare异常"]
    
    return []

def check_asset_lens_data_fetchers():
    """检查asset-lens数据获取器"""
    print("\n🔍 检查asset-lens数据获取器")
    print("=" * 60)
    
    try:
        from asset_lens.data.enhanced_market_data_fetcher import EnhancedMarketDataFetcher
        
        fetcher = EnhancedMarketDataFetcher()
        print("✅ EnhancedMarketDataFetcher 初始化成功")
        
        # 检查数据源配置
        if hasattr(fetcher, 'sources'):
            print(f"  配置的数据源: {list(fetcher.sources.keys())}")
        
        # 测试腾讯数据源
        try:
            print("  测试腾讯数据源获取上证指数...")
            data = fetcher._fetch_from_tencent('sh000001')
            if data:
                print(f"  ✅ 成功获取: {data.get('current_price', 'N/A')}")
            else:
                print("  ❌ 返回空数据")
        except Exception as e:
            print(f"  ❌ 失败: {str(e)[:50]}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return ["asset-lens数据获取器异常"]
    
    return []

def main():
    """主函数"""
    print("🚨 网络功能问题诊断")
    print("=" * 60)
    
    all_issues = []
    
    # 1. 检查环境变量
    env_issues = check_env_vars()
    all_issues.extend(env_issues)
    
    # 2. 检查网络连接
    network_issues = check_network_connectivity()
    all_issues.extend(network_issues)
    
    # 3. 检查AkShare
    akshare_issues = check_akshare_functions()
    all_issues.extend(akshare_issues)
    
    # 4. 检查asset-lens
    asset_lens_issues = check_asset_lens_data_fetchers()
    all_issues.extend(asset_lens_issues)
    
    # 总结
    print("\n📋 问题总结")
    print("=" * 60)
    
    if all_issues:
        print("❌ 发现以下问题:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n💡 解决方案:")
        print("  1. 检查.env文件中的API Key是否有效")
        print("  2. 新浪财经数据源被403，需要切换数据源")
        print("  3. 使用腾讯财经作为主要数据源")
        print("  4. 配置有效的Tushare Token获取A股数据")
        print("  5. 检查网络代理设置")
    else:
        print("✅ 所有检查通过，网络功能正常")
    
    print("\n🎯 建议操作:")
    print("  1. 修改.env文件，使用有效API Key")
    print("  2. 测试腾讯财经数据源: curl -s 'https://qt.gtimg.cn/q=sh000001'")
    print("  3. 配置asset-lens使用腾讯数据源")
    print("  4. 使用Tushare获取A股数据（需要有效Token）")

if __name__ == "__main__":
    main()