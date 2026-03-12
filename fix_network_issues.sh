#!/bin/bash
# 修复Asset-Lens网络问题

echo "🔧 修复Asset-Lens网络问题..."
echo "=========================================="

# 1. 设置环境变量
echo "1. 设置环境变量..."
export ASSET_LENS_PATH="/root/Github/asset-lens"
export ASSET_LENS_DATA_MODE="real"  # 使用真实数据模式

echo "   ASSET_LENS_PATH = $ASSET_LENS_PATH"
echo "   ASSET_LENS_DATA_MODE = $ASSET_LENS_DATA_MODE"

# 2. 创建配置文件
echo "2. 创建配置文件..."
mkdir -p config

cat > config/data_config.json << 'EOF'
{
  "data_mode": "real",
  "timeout": 30,
  "retry_count": 3,
  "use_cache": true,
  "cache_days": 7,
  "data_sources": {
    "akshare": {
      "enabled": true,
      "timeout": 30
    },
    "tushare": {
      "enabled": false,
      "token": ""
    },
    "baostock": {
      "enabled": false
    }
  }
}
EOF

# 3. 创建AkShare优化配置
echo "3. 创建AkShare优化配置..."
cat > config/akshare_config.json << 'EOF'
{
  "timeout": 30,
  "retry": 3,
  "proxy": "",
  "verify": true,
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "cache_enabled": true,
  "cache_dir": "cache/akshare",
  "cache_days": 7
}
EOF

# 4. 测试网络连接
echo "4. 测试网络连接..."
echo "   测试百度..."
curl -s --connect-timeout 10 https://www.baidu.com > /dev/null && echo "   ✅ 百度连接正常" || echo "   ❌ 百度连接失败"

echo "   测试东方财富..."
curl -s --connect-timeout 10 https://quote.eastmoney.com > /dev/null && echo "   ✅ 东方财富连接正常" || echo "   ❌ 东方财富连接失败"

# 5. 测试AkShare
echo "5. 测试AkShare..."
source venv/bin/activate

echo "   测试简单数据获取..."
python3 -c "
import akshare as ak
import pandas as pd

print('   🚀 开始测试...')
try:
    # 测试1: 获取股票列表
    print('   1. 获取股票列表...')
    stock_list = ak.stock_info_a_code_name()
    print(f'      ✅ 成功获取 {len(stock_list)} 只A股')
    
    # 测试2: 获取单个股票数据
    print('   2. 获取单个股票数据...')
    stock_data = ak.stock_zh_a_hist(symbol='000001', period='daily', start_date='20240101', end_date='20240110')
    print(f'      ✅ 成功获取平安银行 {len(stock_data)} 条数据')
    
    # 测试3: 获取指数数据
    print('   3. 获取指数数据...')
    index_data = ak.stock_zh_index_daily(symbol='sh000001')
    print(f'      ✅ 成功获取上证指数 {len(index_data)} 条数据')
    
    print('   🎉 所有测试通过！')
    
except Exception as e:
    print(f'   ❌ 测试失败: {e}')
    import traceback
    traceback.print_exc()
"

# 6. 测试Asset-Lens命令
echo "6. 测试Asset-Lens命令..."
echo "   测试投资分析..."
python3 -m asset_lens analyze --help 2>&1 | head -5

echo "   测试策略列表..."
python3 -m asset_lens strategy list

# 7. 创建快速测试脚本
echo "7. 创建快速测试脚本..."
cat > test_asset_lens.py << 'EOF'
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
EOF

chmod +x test_asset_lens.py

echo ""
echo "🎉 修复完成！"
echo "=========================================="
echo ""
echo "📝 下一步操作:"
echo "  1. 运行快速测试: python3 test_asset_lens.py"
echo "  2. 测试Asset-Lens命令: python3 -m asset_lens analyze"
echo "  3. 如果仍有问题，尝试离线模式:"
echo "     export ASSET_LENS_DATA_MODE=\"sample\""
echo ""
echo "🔧 已创建的配置文件:"
echo "  - config/data_config.json"
echo "  - config/akshare_config.json"
echo "  - test_asset_lens.py"
echo ""
echo "💡 环境变量已设置:"
echo "  ASSET_LENS_PATH = /root/Github/asset-lens"
echo "  ASSET_LENS_DATA_MODE = real"