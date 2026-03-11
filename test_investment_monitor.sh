#!/bin/bash

echo "🎯 个人投资组合监控测试"
echo "========================"
echo ""

# 设置环境变量
export ASSET_LENS_PATH=$(pwd)
export ASSET_LENS_DATA_MODE=sample

echo "📁 项目路径: $ASSET_LENS_PATH"
echo "📊 数据模式: $ASSET_LENS_DATA_MODE"
echo ""

# 1. 测试投资组合分析
echo "1. 📈 投资组合结构分析"
echo "   运行: make analyze"
echo "   预计输出: 各类型占比、风险分布"
echo ""

# 2. 测试基金查询
echo "2. 📊 重点基金净值查询"
echo "   监控基金: 006227 003376 013552"
echo "   命令: make fetch-fund CODES=\"006227 003376 013552\""
echo ""

# 3. 测试市场分析
echo "3. 🌡️ 市场环境分析"
echo "   运行: make market-environment"
echo "   预计输出: 当前市场状态、建议"
echo ""

# 4. 测试策略筛选
echo "4. 🔍 投资策略筛选"
echo "   策略: 动量策略 (momentum)"
echo "   命令: make screen-stocks STRATEGY=momentum LIMIT=5"
echo ""

# 5. 测试日报生成
echo "5. 📋 投资日报生成"
echo "   运行: make daily"
echo "   预计输出: 每日收益、持仓分析"
echo ""

echo "🚀 开始测试..."
echo ""

# 实际运行测试
echo "=== 测试1: 投资组合分析 ==="
make analyze 2>/dev/null | head -20

echo ""
echo "=== 测试2: 市场环境分析 ==="
make market-environment 2>/dev/null | head -15

echo ""
echo "=== 测试3: 策略筛选 ==="
make screen-stocks STRATEGY=momentum LIMIT=5 2>/dev/null | head -10

echo ""
echo "✅ 测试完成！"
echo ""
echo "💡 下一步建议:"
echo "1. 安装必要的Python依赖"
echo "2. 配置真实数据模式"
echo "3. 设置定时监控任务"
echo "4. 集成到OpenClaw技能"
