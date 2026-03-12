#!/bin/bash

echo "🚀 个人投资监控系统演示"
echo "========================"
echo ""

# 设置环境
export ASSET_LENS_PATH=$(pwd)
export ASSET_LENS_DATA_MODE=sample

echo "📁 环境配置:"
echo "  ASSET_LENS_PATH: $ASSET_LENS_PATH"
echo "  ASSET_LENS_DATA_MODE: $ASSET_LENS_DATA_MODE"
echo ""

echo "🎯 演示内容:"
echo "  1. 📊 投资数据分析"
echo "  2. 🔧 监控命令生成"
echo "  3. ⏰ 定时任务配置"
echo "  4. 💡 投资建议框架"
echo ""

# 1. 投资数据分析
echo "=== 1. 📊 投资数据分析 ==="
python3 -c "
import csv
data_file = 'data/sample_data/投资产品-脱敏.csv'
with open(data_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    data = list(reader)

print('✅ 投资组合概览:')
print(f'   总产品数: {len(data)}')
print(f'   重点产品: {sum(1 for item in data if float(item.get(\"占比(%)\", 0)) > 0.5)}')

# 计算总投资占比（排除其他）
total_weight = sum(float(item.get('占比(%)', 0)) for item in data if item.get('类型') != '其他')
print(f'   投资占比: {total_weight:.2f}% (排除其他)')
"

echo ""

# 2. 监控命令生成
echo "=== 2. 🔧 监控命令生成 ==="
echo "📈 基金监控命令:"
echo "  make fetch-fund CODES=\"006227 003376 013552 000633\""
echo ""
echo "📊 股票监控命令:"
echo "  make fetch-stock CODES=\"sh510500 sh510300\""
echo ""
echo "🔍 策略筛选命令:"
echo "  make screen-stocks STRATEGY=momentum LIMIT=10"
echo "  make screen-stocks STRATEGY=value LIMIT=10"
echo ""

# 3. 定时任务配置
echo "=== 3. ⏰ 定时任务配置 ==="
cat << 'SCHEDULE'
每日监控计划:
  09:00 - 开盘前准备
  09:30 - A股开盘监控
  12:00 - 午间分析
  15:00 - 收盘总结
  22:30 - 美股监控
  23:59 - 日报生成

定时任务配置 (schedules.yaml):
  daily_report:
    cron: "0 16 * * 1-5"
    task: "daily_report"
    
  fund_monitor:
    cron: "0 9,13 * * 1-5"
    task: "fetch_fund"
    
  weekly_screen:
    cron: "0 17 * * 1"
    task: "screen_stocks"
SCHEDULE

echo ""

# 4. 投资建议框架
echo "=== 4. 💡 投资建议框架 ==="
cat << 'ADVICE'
📊 本周投资建议模板:
────────────────────
市场环境: [牛市/震荡/熊市]
投资表现: [收益率、排名]
核心建议: [操作方向]

具体操作:
├── 增持: [产品/行业]
├── 减持: [产品/行业]
└── 持有: [核心持仓]

关注机会:
├── 行业: [科技/消费/医药]
└── 策略: [价值/成长/红利]

风险提示:
[主要风险因素]
ADVICE

echo ""

# 5. OpenClaw技能集成
echo "=== 5. 🤖 OpenClaw技能集成 ==="
echo "技能功能:"
echo "  ✅ 股票基金查询"
echo "  ✅ 投资策略筛选"
echo "  ✅ 市场环境分析"
echo "  ✅ 投资组合管理"
echo "  ✅ 价格监控提醒"
echo ""
echo "使用示例:"
echo "  用户: 查询茅台股价"
echo "  OpenClaw: fetch_stock(codes=\"sh600519\")"
echo ""
echo "  用户: 生成投资日报"
echo "  OpenClaw: daily_report()"
echo ""

# 6. 下一步行动
echo "=== 6. 🚀 下一步行动 ==="
echo "立即可以做的:"
echo "  1. 安装Python依赖: pip install akshare pandas"
echo "  2. 测试监控命令: make fetch-fund CODES=\"006227\""
echo "  3. 配置环境变量: 编辑 ~/.bashrc"
echo "  4. 设置定时任务: 配置 schedules.yaml"
echo ""
echo "长期计划:"
echo "  1. 集成到OpenClaw工作流"
echo "  2. 配置微信/QQ推送"
echo "  3. 开发AI投资建议"
echo "  4. 多账户统一管理"
echo ""

echo "🎉 演示完成！"
echo ""
echo "💡 提示: 所有配置文件和脚本已生成"
echo "📁 查看: ls -la investment_*.py investment_*.sh"
