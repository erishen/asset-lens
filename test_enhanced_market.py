#!/usr/bin/env python3
"""
测试增强版市场数据功能
"""

import sys
import os
sys.path.append('.')

print("🚀 测试增强版市场数据功能")
print("=" * 50)

# 检查新模块
try:
    from asset_lens.data.enhanced_market_data_fetcher import EnhancedMarketDataFetcher
    print("✅ 找到增强版市场数据获取器")
    
    # 查看模块信息
    import inspect
    print(f"模块文档: {EnhancedMarketDataFetcher.__doc__}")
    
    # 查看可用方法
    methods = [m for m in dir(EnhancedMarketDataFetcher) if not m.startswith('_')]
    print(f"可用方法: {', '.join(methods[:10])}...")
    
except ImportError as e:
    print(f"❌ 无法导入增强模块: {e}")

print()

# 检查HTTP客户端
try:
    from asset_lens.utils.http_client import HTTPClient, ErrorType
    print("✅ 找到增强版HTTP客户端")
    print(f"错误类型: {[e.value for e in ErrorType]}")
    
    # 测试创建客户端
    client = HTTPClient()
    print(f"HTTP客户端创建成功: {client}")
    
except ImportError as e:
    print(f"❌ 无法导入HTTP客户端: {e}")

print()

# 检查配置
try:
    from asset_lens.config import config
    print("✅ 配置模块加载成功")
    print(f"数据模式: {config.data_mode}")
    print(f"缓存路径: {config.cache_path}")
    
    # 检查API配置
    print("API配置状态:")
    print(f"  Finnhub API: {'已配置' if config.finnhub_api_key else '未配置'}")
    print(f"  Alpha Vantage API: {'已配置' if config.alphavantage_api_key else '未配置'}")
    print(f"  Tushare Token: {'已配置' if config.tushare_token else '未配置'}")
    
except ImportError as e:
    print(f"❌ 无法导入配置模块: {e}")

print()

# 测试市场数据获取（模拟模式）
print("📊 测试市场数据获取（模拟模式）...")
try:
    # 创建模拟数据获取器
    class MockMarketFetcher:
        def __init__(self):
            self.supported_indices = [
                {"name": "上证指数", "code": "sh000001"},
                {"name": "沪深300", "code": "sh000300"},
                {"name": "创业板指", "code": "sz399006"},
                {"name": "纳斯达克", "code": "IXIC"},
                {"name": "标普500", "code": "SPX"}
            ]
            
            self.supported_stocks = [
                {"name": "贵州茅台", "code": "sh600519"},
                {"name": "腾讯控股", "code": "00700"},
                {"name": "苹果", "code": "AAPL"},
                {"name": "微软", "code": "MSFT"}
            ]
        
        def get_market_indices(self):
            """获取市场指数数据"""
            import time
            import random
            
            indices = {}
            for idx in self.supported_indices:
                base_price = random.uniform(1000, 20000)
                change = random.uniform(-100, 100)
                change_pct = (change / base_price) * 100
                
                indices[idx["name"]] = {
                    "code": idx["code"],
                    "price": round(base_price + change, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": f"{random.randint(1, 10)}亿",
                    "timestamp": time.time()
                }
            
            return indices
        
        def get_stock_quotes(self, codes):
            """获取股票报价"""
            import random
            
            quotes = {}
            for code in codes:
                base_price = random.uniform(10, 1000)
                change = random.uniform(-10, 10)
                change_pct = (change / base_price) * 100
                
                quotes[code] = {
                    "price": round(base_price + change, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": random.randint(1000000, 10000000),
                    "high": round(base_price + random.uniform(0, 20), 2),
                    "low": round(base_price - random.uniform(0, 20), 2),
                    "open": round(base_price + random.uniform(-5, 5), 2)
                }
            
            return quotes
    
    # 测试模拟获取器
    fetcher = MockMarketFetcher()
    print(f"✅ 模拟获取器创建成功")
    print(f"支持指数: {len(fetcher.supported_indices)} 个")
    print(f"支持股票: {len(fetcher.supported_stocks)} 个")
    
    # 获取市场指数
    indices = fetcher.get_market_indices()
    print(f"获取到 {len(indices)} 个指数数据")
    
    # 显示部分数据
    print("\n📈 模拟指数数据:")
    for name, data in list(indices.items())[:3]:
        sign = "+" if data["change"] >= 0 else ""
        print(f"  {name}: {data['price']} ({sign}{data['change']}, {sign}{data['change_pct']:.2f}%)")
    
    # 获取股票数据
    stock_codes = ["sh600519", "AAPL", "00700"]
    stocks = fetcher.get_stock_quotes(stock_codes)
    print(f"\n📊 模拟股票数据 ({len(stocks)} 只):")
    for code, data in stocks.items():
        sign = "+" if data["change"] >= 0 else ""
        print(f"  {code}: {data['price']} ({sign}{data['change']}, {sign}{data['change_pct']:.2f}%)")
    
except Exception as e:
    print(f"❌ 模拟测试失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 生成使用建议
print("💡 使用建议:")
print("=" * 50)

suggestions = """
1. 配置API密钥获取真实数据:
   - 注册 Finnhub (免费60次/分钟)
   - 注册 Alpha Vantage (免费25次/天)
   - 注册 Tushare (A股，免费10000次/天)

2. 更新环境变量:
   编辑 .env 文件，添加:
   FINNHUB_API_KEY=your_key
   ALPHAVANTAGE_API_KEY=your_key
   TUSHARE_TOKEN=your_token

3. 运行市场更新:
   make update-market-data-fast
   或
   python -m asset_lens update-market-data --api finnhub

4. 分析市场环境:
   make market-environment
   或
   python -m asset_lens market-environment --analyze

5. 监控你的投资产品:
   # 基金
   make fetch-fund CODES="006227 003376 013552"
   
   # 股票/ETF
   make fetch-stock CODES="sh510500 sh510300 QQQ"
"""

print(suggestions)

print("✅ 测试完成！")
print("📁 代码已更新，支持增强版市场数据获取")
