#!/usr/bin/env python3
"""
网络诊断和配置脚本
检查Asset-Lens网络问题并提供解决方案
"""

import os
import sys
import requests
import socket
import subprocess
import json
from datetime import datetime

def print_header(title):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_basic_network():
    """检查基础网络连接"""
    print_header("基础网络连接检查")
    
    test_urls = [
        ("百度", "https://www.baidu.com"),
        ("腾讯云", "https://cloud.tencent.com"),
        ("东方财富", "https://quote.eastmoney.com"),
        ("新浪财经", "https://finance.sina.com.cn"),
        ("AkShare数据源", "https://akshare.akfamily.xyz")
    ]
    
    for name, url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"{status} {name:15} {url:40} 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {name:15} {url:40} 错误: {str(e)[:50]}")

def check_dns_resolution():
    """检查DNS解析"""
    print_header("DNS解析检查")
    
    domains = [
        "baidu.com",
        "eastmoney.com",
        "sina.com.cn",
        "akshare.akfamily.xyz",
        "quote.eastmoney.com"
    ]
    
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
            print(f"✅ {domain:30} -> {ip}")
        except Exception as e:
            print(f"❌ {domain:30} DNS解析失败: {e}")

def check_proxy_settings():
    """检查代理设置"""
    print_header("代理设置检查")
    
    proxy_vars = [
        "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
        "NO_PROXY", "no_proxy", "ALL_PROXY", "all_proxy"
    ]
    
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"⚠️  {var:15} = {value}")
        else:
            print(f"✅  {var:15} = 未设置")
    
    print("\n📝 建议:")
    print("  1. 如果不需要代理，请取消代理设置:")
    print("     unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy")
    print("  2. 如果需要代理，请确保代理服务器可用")

def check_python_packages():
    """检查Python包版本"""
    print_header("Python包版本检查")
    
    packages = [
        "akshare",
        "requests",
        "pandas",
        "numpy",
        "aiohttp"
    ]
    
    for package in packages:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {package}; print({package}.__version__)"],
                capture_output=True, text=True, timeout=5
            )
            version = result.stdout.strip()
            print(f"✅ {package:15} = {version}")
        except Exception as e:
            print(f"❌ {package:15} 无法获取版本: {e}")

def check_akshare_specific_issues():
    """检查AkShare特定问题"""
    print_header("AkShare特定问题检查")
    
    print("1. 测试简单数据获取...")
    try:
        import akshare as ak
        
        # 测试简单的数据获取
        print("  尝试获取股票代码列表...")
        stock_info_a_code_name_df = ak.stock_info_a_code_name()
        print(f"  ✅ 成功获取股票代码列表，行数: {len(stock_info_a_code_name_df)}")
        
        # 测试单个股票数据
        print("  尝试获取单个股票数据...")
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20240101", end_date="20240110")
        print(f"  ✅ 成功获取股票历史数据，行数: {len(stock_zh_a_hist_df)}")
        
    except Exception as e:
        print(f"  ❌ AkShare数据获取失败: {e}")
        print(f"     错误详情: {type(e).__name__}")
        
        # 提供具体解决方案
        print("\n🔧 可能的解决方案:")
        print("  1. 检查网络连接，特别是到东方财富的访问")
        print("  2. 尝试使用代理（如果需要）")
        print("  3. 更新AkShare到最新版本:")
        print("     pip install akshare --upgrade")
        print("  4. 检查防火墙设置")

def check_firewall_and_ports():
    """检查防火墙和端口"""
    print_header("防火墙和端口检查")
    
    # 检查常用端口
    ports_to_check = [
        (80, "HTTP"),
        (443, "HTTPS"),
        (8080, "代理端口")
    ]
    
    for port, desc in ports_to_check:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("8.8.8.8", port))
            status = "✅" if result == 0 else "❌"
            print(f"{status} 端口 {port:4} ({desc:10}) - {'开放' if result == 0 else '关闭/被阻'}")
            sock.close()
        except Exception as e:
            print(f"❌ 端口 {port:4} ({desc:10}) - 检查失败: {e}")

def check_system_network_config():
    """检查系统网络配置"""
    print_header("系统网络配置")
    
    print("1. 检查网络接口:")
    try:
        result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True)
        interfaces = [line for line in result.stdout.split('\n') if 'inet ' in line]
        for iface in interfaces[:3]:  # 只显示前3个
            print(f"   {iface.strip()}")
    except:
        print("   无法获取网络接口信息")
    
    print("\n2. 检查路由表:")
    try:
        result = subprocess.run(["ip", "route", "show"], capture_output=True, text=True)
        routes = result.stdout.split('\n')[:5]  # 只显示前5条
        for route in routes:
            if route.strip():
                print(f"   {route.strip()}")
    except:
        print("   无法获取路由表信息")

def check_asset_lens_config():
    """检查Asset-Lens配置"""
    print_header("Asset-Lens配置检查")
    
    config_paths = [
        "/root/Github/asset-lens/config",
        "/root/Github/asset-lens/data",
        "/root/Github/asset-lens/venv"
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            print(f"✅ {path:40} 存在")
        else:
            print(f"❌ {path:40} 不存在")
    
    # 检查环境变量
    print("\n环境变量检查:")
    env_vars = ["ASSET_LENS_PATH", "ASSET_LENS_DATA_MODE"]
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var:25} = {value}")
        else:
            print(f"⚠️  {var:25} = 未设置")

def generate_solutions():
    """生成解决方案"""
    print_header("网络问题解决方案")
    
    print("🔧 解决方案 1: 设置代理（如果需要）")
    print("""
    export HTTP_PROXY="http://your-proxy:port"
    export HTTPS_PROXY="http://your-proxy:port"
    export NO_PROXY="localhost,127.0.0.1"
    """)
    
    print("\n🔧 解决方案 2: 取消代理（如果不需要）")
    print("""
    unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
    """)
    
    print("\n🔧 解决方案 3: 使用国内镜像源")
    print("""
    # 临时使用清华镜像源
    pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    # 永久配置
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
    """)
    
    print("\n🔧 解决方案 4: 配置AkShare超时设置")
    print("""
    # 在代码中增加超时设置
    import akshare as ak
    import requests
    
    # 设置全局超时
    session = requests.Session()
    session.request = lambda method, url, **kwargs: requests.request(
        method, url, timeout=30, **kwargs
    )
    ak.session = session
    """)
    
    print("\n🔧 解决方案 5: 使用备用数据源")
    print("""
    # 如果东方财富不可用，尝试其他数据源
    # 1. Tushare (需要注册)
    # 2. Baostock (免费)
    # 3. Yahoo Finance (国际数据)
    """)
    
    print("\n🔧 解决方案 6: 离线模式运行")
    print("""
    # 设置环境变量使用离线数据
    export ASSET_LENS_DATA_MODE="sample"
    
    # 或者直接修改配置
    echo '{"data_mode": "sample"}' > config/data_config.json
    """)

def create_network_config_script():
    """创建网络配置脚本"""
    print_header("创建网络配置脚本")
    
    script_content = """#!/bin/bash
# Asset-Lens网络配置脚本

echo "🔧 配置Asset-Lens网络环境..."
echo "=========================================="

# 1. 设置环境变量
echo "1. 设置环境变量..."
export ASSET_LENS_PATH="/root/Github/asset-lens"
export ASSET_LENS_DATA_MODE="real"  # 或 "sample" 用于离线模式

# 2. 配置代理（如果需要）
# 取消下面几行的注释并设置你的代理
# export HTTP_PROXY="http://your-proxy:port"
# export HTTPS_PROXY="http://your-proxy:port"
# export NO_PROXY="localhost,127.0.0.1"

# 3. 设置Python包镜像源
echo "2. 配置Python镜像源..."
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 120
EOF

# 4. 创建AkShare配置文件
echo "3. 创建AkShare配置文件..."
mkdir -p ~/.akshare
cat > ~/.akshare/config.json << EOF
{
  "timeout": 30,
  "retry": 3,
  "proxy": "",
  "verify": true,
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
EOF

# 5. 测试网络连接
echo "4. 测试网络连接..."
echo "测试百度..."
curl -s --connect-timeout 10 https://www.baidu.com > /dev/null && echo "✅ 百度连接正常" || echo "❌ 百度连接失败"

echo "测试东方财富..."
curl -s --connect-timeout 10 https://quote.eastmoney.com > /dev/null && echo "✅ 东方财富连接正常" || echo "❌ 东方财富连接失败"

echo ""
echo "🎉 网络配置完成！"
echo "=========================================="
echo ""
echo "📝 使用说明:"
echo "  1. 运行此脚本: source network_config.sh"
echo "  2. 激活虚拟环境: source venv/bin/activate"
echo "  3. 测试AkShare: python3 -c \"import akshare as ak; print(ak.__version__)\""
echo ""
"""
    
    script_path = "/root/Github/asset-lens/network_config.sh"
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod(script_path, 0o755)
    
    print(f"✅ 网络配置脚本已创建: {script_path}")
    print("\n📝 使用方法:")
    print(f"  source {script_path}")
    print("  然后激活虚拟环境: source venv/bin/activate")

def main():
    """主函数"""
    print("🔧 Asset-Lens网络诊断工具")
    print("=" * 60)
    print(f"📅 诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python版本: {sys.version.split()[0]}")
    print(f"📁 工作目录: {os.getcwd()}")
    print("=" * 60)
    
    # 运行各项检查
    check_basic_network()
    check_dns_resolution()
    check_proxy_settings()
    check_python_packages()
    check_akshare_specific_issues()
    check_firewall_and_ports()
    check_system_network_config()
    check_asset_lens_config()
    
    # 生成解决方案
    generate_solutions()
    
    # 创建配置脚本
    create_network_config_script()
    
    print("\n" + "=" * 60)
    print("🎉 诊断完成！")
    print("=" * 60)
    print("\n📋 总结建议:")
    print("  1. 首先运行网络配置脚本: source network_config.sh")
    print("  2. 如果仍有问题，尝试使用离线模式")
    print("  3. 检查防火墙和代理设置")
    print("  4. 考虑使用备用数据源")
    print("\n💡 快速测试:")
    print("  cd /root/Github/asset-lens")
    print("  source venv/bin/activate")
    print('  python3 -c "import akshare as ak; print(f\"AkShare版本: {ak.__version__}\")"')

if __name__ == "__main__":
    main()
