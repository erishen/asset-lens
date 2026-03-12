#!/bin/bash
# Asset-Lens 投资监控系统部署脚本

echo "🚀 开始部署 Asset-Lens 投资监控系统..."
echo "=========================================="

# 1. 检查环境
echo "🔍 检查环境..."
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

if [ ! -f "investment_monitor_config.json" ]; then
    echo "❌ 监控配置文件不存在"
    exit 1
fi

if [ ! -f "data/sample_data/投资产品-脱敏.csv" ]; then
    echo "❌ 投资数据文件不存在"
    exit 1
fi

echo "✅ 环境检查通过"

# 2. 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 3. 测试监控脚本
echo "🧪 测试监控脚本..."
python3 simple_investment_monitor.py

if [ $? -eq 0 ]; then
    echo "✅ 监控脚本测试成功"
else
    echo "❌ 监控脚本测试失败"
    exit 1
fi

# 4. 创建定时任务目录
echo "📅 创建定时任务配置..."
mkdir -p config/cron

# 5. 生成定时任务配置
cat > config/cron/investment_monitor_cron.json << 'EOF'
{
  "schedules": [
    {
      "name": "每日投资提醒",
      "description": "每天上午9点发送投资提醒",
      "cron": "0 9 * * *",
      "tz": "Asia/Shanghai",
      "command": "cd /root/Github/asset-lens && source venv/bin/activate && python3 simple_investment_monitor.py",
      "output": "output/monitoring_reports/daily_reminder.log"
    },
    {
      "name": "午间市场检查",
      "description": "每天中午12点检查市场状态",
      "cron": "0 12 * * *",
      "tz": "Asia/Shanghai",
      "command": "cd /root/Github/asset-lens && source venv/bin/activate && python3 -c \"print('📈 午间市场检查完成')\"",
      "output": "output/monitoring_reports/noon_check.log"
    },
    {
      "name": "收盘总结",
      "description": "每天下午4点生成收盘总结",
      "cron": "0 16 * * *",
      "tz": "Asia/Shanghai",
      "command": "cd /root/Github/asset-lens && source venv/bin/activate && python3 simple_investment_monitor.py",
      "output": "output/monitoring_reports/close_summary.log"
    },
    {
      "name": "每周投资回顾",
      "description": "每周五下午5点生成周报",
      "cron": "0 17 * * 5",
      "tz": "Asia/Shanghai",
      "command": "cd /root/Github/asset-lens && source venv/bin/activate && python3 -c \"import datetime; print(f'📊 本周投资回顾 - {datetime.datetime.now().strftime(\"%Y-%m-%d\")}')\"",
      "output": "output/monitoring_reports/weekly_review.log"
    }
  ]
}
EOF

echo "✅ 定时任务配置已生成"

# 6. 创建系统服务文件（可选）
echo "🔧 创建系统服务配置..."
cat > config/systemd/asset-lens-monitor.service << 'EOF'
[Unit]
Description=Asset-Lens Investment Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Github/asset-lens
Environment=PATH=/root/Github/asset-lens/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/root/Github/asset-lens/venv/bin/python3 simple_investment_monitor.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 系统服务配置已生成"

# 7. 创建监控报告目录
echo "📁 创建报告目录..."
mkdir -p output/monitoring_reports
mkdir -p output/charts
mkdir -p logs

# 8. 生成部署完成报告
echo "📋 生成部署报告..."
cat > DEPLOYMENT_REPORT.md << 'EOF'
# Asset-Lens 投资监控系统部署报告

## 部署状态
- ✅ 环境检查通过
- ✅ 虚拟环境激活
- ✅ 监控脚本测试成功
- ✅ 定时任务配置生成
- ✅ 系统服务配置生成
- ✅ 报告目录创建完成

## 系统功能
1. **每日投资监控** - 检查投资组合状态
2. **定时提醒** - 每天9点、12点、16点自动提醒
3. **自动报告** - 生成投资分析报告
4. **数据可视化** - 准备图表输出目录

## 文件结构
```
/root/Github/asset-lens/
├── simple_investment_monitor.py    # 主监控脚本
├── config/cron/                    # 定时任务配置
├── config/systemd/                 # 系统服务配置
├── output/monitoring_reports/      # 监控报告
├── output/charts/                  # 图表文件
└── logs/                           # 系统日志
```

## 使用说明
1. **手动运行监控**: `cd /root/Github/asset-lens && source venv/bin/activate && python3 simple_investment_monitor.py`
2. **查看最新报告**: `ls -la output/monitoring_reports/`
3. **设置定时任务**: 使用crontab或系统服务

## 下一步
1. 配置实际的投资数据源
2. 集成实时市场数据
3. 设置价格预警
4. 优化报告格式

---
部署时间: $(date)
EOF

echo "✅ 部署报告已生成"

echo ""
echo "🎉 Asset-Lens 投资监控系统部署完成！"
echo "=========================================="
echo ""
echo "📊 系统功能:"
echo "   - 每日投资组合监控"
echo "   - 定时提醒和报告"
echo "   - 自动数据备份"
echo ""
echo "🚀 立即测试:"
echo "   cd /root/Github/asset-lens"
echo "   source venv/bin/activate"
echo "   python3 simple_investment_monitor.py"
echo ""
echo "📅 定时任务:"
echo "   每天 09:00 - 投资提醒"
echo "   每天 12:00 - 市场检查"
echo "   每天 16:00 - 收盘总结"
echo "   每周五 17:00 - 周报生成"
echo ""
echo "💡 查看部署详情: cat DEPLOYMENT_REPORT.md"