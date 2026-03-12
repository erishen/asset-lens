#!/bin/bash
# 简单的数据获取脚本 - 直接用工具，不写多余代码

echo "📊 获取真实市场数据"
echo "========================"

# 1. 检查网络
echo "🔧 检查网络连接..."
ping -c 2 quote.eastmoney.com > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 网络连接正常"
else
    echo "❌ 网络连接问题"
fi

echo

# 2. 获取上证指数
echo "📈 获取上证指数..."
SH_DATA=$(curl -s "https://qt.gtimg.cn/q=sh000001" | iconv -f gbk -t utf-8 2>/dev/null)

if [ -n "$SH_DATA" ]; then
    # 解析数据
    SH_NAME=$(echo "$SH_DATA" | cut -d'"' -f2 | cut -d'~' -f2)
    SH_CODE=$(echo "$SH_DATA" | cut -d'"' -f2 | cut -d'~' -f3)
    SH_PRICE=$(echo "$SH_DATA" | cut -d'"' -f2 | cut -d'~' -f4)
    SH_CHANGE=$(echo "$SH_DATA" | cut -d'"' -f2 | cut -d'~' -f32)
    SH_CHANGE_PCT=$(echo "$SH_DATA" | cut -d'"' -f2 | cut -d'~' -f33)
    SH_TIME=$(echo "$SH_DATA" | cut -d'"' -f2 | cut -d'~' -f31)
    
    echo "✅ $SH_NAME ($SH_CODE)"
    echo "   最新价: $SH_PRICE"
    echo "   涨跌额: $SH_CHANGE"
    echo "   涨跌幅: $SH_CHANGE_PCT%"
    echo "   时间: ${SH_TIME:0:4}-${SH_TIME:4:2}-${SH_TIME:6:2} ${SH_TIME:8:2}:${SH_TIME:10:2}:${SH_TIME:12:2}"
else
    echo "❌ 获取上证指数失败"
fi

echo

# 3. 获取深证成指
echo "📈 获取深证成指..."
SZ_DATA=$(curl -s "https://qt.gtimg.cn/q=sz399001" | iconv -f gbk -t utf-8 2>/dev/null)

if [ -n "$SZ_DATA" ]; then
    SZ_NAME=$(echo "$SZ_DATA" | cut -d'"' -f2 | cut -d'~' -f2)
    SZ_PRICE=$(echo "$SZ_DATA" | cut -d'"' -f2 | cut -d'~' -f4)
    SZ_CHANGE=$(echo "$SZ_DATA" | cut -d'"' -f2 | cut -d'~' -f32)
    SZ_CHANGE_PCT=$(echo "$SZ_DATA" | cut -d'"' -f2 | cut -d'~' -f33)
    
    echo "✅ $SZ_NAME"
    echo "   最新价: $SZ_PRICE"
    echo "   涨跌额: $SZ_CHANGE"
    echo "   涨跌幅: $SZ_CHANGE_PCT%"
else
    echo "❌ 获取深证成指失败"
fi

echo

# 4. 获取创业板指
echo "📈 获取创业板指..."
CYB_DATA=$(curl -s "https://qt.gtimg.cn/q=sz399006" | iconv -f gbk -t utf-8 2>/dev/null)

if [ -n "$CYB_DATA" ]; then
    CYB_NAME=$(echo "$CYB_DATA" | cut -d'"' -f2 | cut -d'~' -f2)
    CYB_PRICE=$(echo "$CYB_DATA" | cut -d'"' -f2 | cut -d'~' -f4)
    CYB_CHANGE=$(echo "$CYB_DATA" | cut -d'"' -f2 | cut -d'~' -f32)
    CYB_CHANGE_PCT=$(echo "$CYB_DATA" | cut -d'"' -f2 | cut -d'~' -f33)
    
    echo "✅ $CYB_NAME"
    echo "   最新价: $CYB_PRICE"
    echo "   涨跌额: $CYB_CHANGE"
    echo "   涨跌幅: $CYB_CHANGE_PCT%"
else
    echo "❌ 获取创业板指失败"
fi

echo
echo "========================"
echo "📝 数据说明"
echo "========================"
echo "1. 数据源: 腾讯财经 (https://qt.gtimg.cn)"
echo "2. 获取方式: curl 命令"
echo "3. 编码转换: gbk → utf-8"
echo "4. 数据格式: v_sh000001=\"1~上证指数~000001~价格~...\""
echo "5. 优点: 简单、快速、不依赖复杂库"
echo
echo "💡 教训: 直接用工具，不写多余代码"
echo "       网络问题修网络，数据异常查数据源"