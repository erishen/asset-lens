#!/bin/bash
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
echo "  3. 测试AkShare: python3 -c "import akshare as ak; print(ak.__version__)""
echo ""
