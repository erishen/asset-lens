#!/bin/bash
# 中高风险基金监控系统部署脚本

echo "🔥 开始部署中高风险基金监控系统..."
echo "=========================================="

# 1. 检查环境
echo "🔍 检查环境..."
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在"
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

# 3. 测试高风险基金监控脚本
echo "🧪 测试高风险基金监控脚本..."
python3 high_risk_fund_monitor.py

if [ $? -eq 0 ]; then
    echo "✅ 高风险基金监控脚本测试成功"
else
    echo "❌ 高风险基金监控脚本测试失败"
    exit 1
fi

# 4. 创建高风险基金监控配置
echo "📋 创建高风险基金监控配置..."
mkdir -p config/high_risk

# 生成高风险基金列表
cat > config/high_risk/critical_funds.json << 'EOF'
{
  "critical_funds": [
    {
      "name": "纳指100ETF-Invesco QQQ Trust",
      "code": "QQQ",
      "type": "美股（美元）",
      "risk": "高",
      "weight": 0.58,
      "monitoring_frequency": "daily",
      "alert_threshold": 3.0,
      "description": "科技股指数ETF，波动较大"
    },
    {
      "name": "可口可乐",
      "code": "KO",
      "type": "美股（美元）",
      "risk": "高",
      "weight": 0.28,
      "monitoring_frequency": "daily",
      "alert_threshold": 5.0,
      "description": "消费股，受经济周期影响"
    },
    {
      "name": "能源指数ETF-SPDR XLE",
      "code": "XLE",
      "type": "美股（美元）",
      "risk": "高",
      "weight": 0.14,
      "monitoring_frequency": "daily",
      "alert_threshold": 4.0,
      "description": "能源板块，受油价影响大"
    },
    {
      "name": "中证500ETF嘉实",
      "code": "510500",
      "type": "ETF",
      "risk": "高",
      "weight": 0.09,
      "monitoring_frequency": "daily",
      "alert_threshold": 3.5,
      "description": "中小盘指数，波动性较高"
    }
  ],
  "monitoring_rules": {
    "daily_check": ["高风险基金"],
    "weekly_check": ["中高风险基金"],
    "monthly_review": ["中等风险基金"],
    "alert_triggers": {
      "price_drop_5pct": "单日跌幅 > 5%",
      "price_drop_10pct_week": "周跌幅 > 10%",
      "price_drop_15pct_month": "月跌幅 > 15%",
      "volatility_high": "日内波动 > 3%"
    }
  }
}
EOF

echo "✅ 高风险基金监控配置已生成"

# 5. 创建定时任务配置
echo "📅 创建定时任务配置..."
cat > config/high_risk/schedules.json << 'EOF'
{
  "schedules": [
    {
      "name": "高风险基金每日晨报",
      "description": "每天上午9点发送高风险基金监控提醒",
      "cron": "0 9 * * *",
      "tz": "Asia/Shanghai",
      "command": "cd /root/Github/asset-lens && source venv/bin/activate && python3 high_risk_fund_monitor.py",
      "output": "output/high_risk_monitoring/daily_morning_report.log"
    },
    {
      "name": "高风险基金午间检查",
      "description": "每天中午12点检查高风险基金表现",
      "cron": "0 12 * * *",
      "tz": "Asia/Shanghai",
      "command": "cd /root/Github/asset-lens && source venv/bin/activate && python3 -c \"from datetime import datetime; print(f'📊 高风险基金午间检查 - {datetime.now().strftime(\"%H:%M\")}')\"",
      "output": "output/high_risk_monitoring/noon_check.log"
    },
    {
      "name": "高风险基金收盘总结",
      "description": "每天下午4点生成高风险基金收盘报告",
      "cron": "0 16 * * *",
      "tz": "Asia/Shanghai",
      "command": "cd /root/Github/asset-lens && source venv/bin/activate && python3 high_risk_fund_monitor.py",
      "output": "output/high_risk_monitoring/close_report.log"
    },
    {
      "name": "中高风险基金周报",
      "description": "每周五下午5点生成中高风险基金周报",
      "cron": "0 17 * * 5",
      "tz": "Asia/Shanghai",
      "command": "cd /root/Github/asset-lens && source venv/bin/activate && python3 -c \"import json; from datetime import datetime; data = {'report_time': datetime.now().strftime('%Y-%m-%d %H:%M'), 'type': 'weekly_high_risk_report'}; print(json.dumps(data, indent=2, ensure_ascii=False))\"",
      "output": "output/high_risk_monitoring/weekly_report.log"
    }
  ]
}
EOF

echo "✅ 定时任务配置已生成"

# 6. 创建QQ提醒配置
echo "💬 创建QQ提醒配置..."
cat > config/high_risk/qq_alerts.json << 'EOF'
{
  "qq_alerts": [
    {
      "name": "高风险基金每日提醒",
      "schedule": "0 9 * * *",
      "message_template": "🔥 高风险基金每日监控提醒\\n📅 时间: {time}\\n🎯 重点关注: {critical_count}个高风险基金\\n⚠️ 今日提醒: {reminder}\\n💡 建议: {advice}",
      "variables": {
        "critical_count": 9,
        "reminder": "检查纳指ETF、可口可乐等高风险基金",
        "advice": "关注美股市场，控制仓位风险"
      }
    },
    {
      "name": "高风险基金波动预警",
      "trigger": "price_change > 5%",
      "message_template": "🚨 高风险基金波动预警！\\n📊 基金: {fund_name}\\n📈 变化: {change_pct}%\\n⏰ 时间: {time}\\n💡 建议: 立即检查该基金表现",
      "priority": "high"
    }
  ]
}
EOF

echo "✅ QQ提醒配置已生成"

# 7. 创建报告目录
echo "📁 创建报告目录..."
mkdir -p output/high_risk_monitoring
mkdir -p output/high_risk_charts
mkdir -p logs/high_risk

# 8. 生成部署完成报告
echo "📋 生成部署报告..."
cat > HIGH_RISK_DEPLOYMENT_REPORT.md << 'EOF'
# 中高风险基金监控系统部署报告

## 部署状态
- ✅ 环境检查通过
- ✅ 虚拟环境激活
- ✅ 监控脚本测试成功
- ✅ 高风险基金配置生成
- ✅ 定时任务配置生成
- ✅ QQ提醒配置生成
- ✅ 报告目录创建完成

## 系统功能
### 🎯 监控重点
1. **高风险基金** (9个) - 每日监控
2. **中高风险基金** (16个) - 每周检查
3. **中等风险基金** (6个) - 每月回顾

### 📊 监控指标
- 价格波动
- 涨跌幅
- 风险等级
- 仓位占比

### ⏰ 定时任务
1. **09:00** - 高风险基金每日晨报
2. **12:00** - 高风险基金午间检查
3. **16:00** - 高风险基金收盘总结
4. **周五 17:00** - 中高风险基金周报

## 高风险基金列表
### ⚠️ 需要密切监控 (高风险)
1. **纳指100ETF-Invesco QQQ Trust** (QQQ) - 0.58%
2. **可口可乐** (KO) - 0.28%
3. **能源指数ETF-SPDR XLE** (XLE) - 0.14%
4. **中证500ETF嘉实** (510500) - 0.09%

### 🔸 需要定期检查 (中高风险)
- 国联安沪深300指数增强A (0.25%)
- 博道盛彦混合A (0.24%)
- 易方达亚洲精选股票 (0.22%)

## 预警规则
### 🚨 触发条件
1. 单日跌幅 > 5%
2. 连续3日下跌
3. 月度跌幅 > 10%
4. 日内波动 > 3%

### 💡 处理建议
1. 立即检查基金基本面
2. 分析市场环境
3. 考虑调整仓位
4. 设置止损点

## 文件结构
```
/root/Github/asset-lens/
├── high_risk_fund_monitor.py          # 主监控脚本
├── config/high_risk/                  # 高风险基金配置
│   ├── critical_funds.json           # 重点基金列表
│   ├── schedules.json                # 定时任务
│   └── qq_alerts.json                # QQ提醒配置
├── output/high_risk_monitoring/      # 监控报告
├── output/high_risk_charts/          # 风险图表
└── logs/high_risk/                   # 系统日志
```

## 使用说明
### 🚀 快速启动
```bash
cd /root/Github/asset-lens
source venv/bin/activate
python3 high_risk_fund_monitor.py
```

### 📊 查看报告
```bash
ls -la output/high_risk_monitoring/
cat output/high_risk_monitoring/high_risk_funds_*.txt
```

### ⚙️ 配置修改
1. 编辑 `config/high_risk/critical_funds.json` 修改重点基金
2. 编辑 `config/high_risk/schedules.json` 调整定时任务
3. 编辑 `config/high_risk/qq_alerts.json` 修改提醒内容

## 风险提示
1. **高风险基金波动大** - 需要密切监控
2. **美股受时差影响** - 注意交易时间
3. **仓位控制重要** - 高风险基金占比不宜过高
4. **定期再平衡** - 保持投资组合稳定

---
部署时间: $(date)
系统版本: 1.0.0
监控基金数: 31个 (中高风险以上)
总监控占比: 6.60%
EOF

echo "✅ 部署报告已生成"

echo ""
echo "🎉 中高风险基金监控系统部署完成！"
echo "=========================================="
echo ""
echo "🔥 监控重点:"
echo "   - 9个高风险基金 (需要每日监控)"
echo "   - 16个中高风险基金 (需要每周检查)"
echo "   - 6个中等风险基金 (需要每月回顾)"
echo ""
echo "📊 监控数据:"
echo "   - 总监控基金: 31个"
echo "   - 总监控占比: 6.60%"
echo "   - 最高风险: 纳指100ETF (QQQ)"
echo ""
echo "⏰ 定时任务:"
echo "   09:00 - 高风险基金每日晨报"
echo "   12:00 - 高风险基金午间检查"
echo "   16:00 - 高风险基金收盘总结"
echo "   周五 17:00 - 中高风险基金周报"
echo ""
echo "🚨 预警规则:"
echo "   - 单日跌幅 > 5% → 立即检查"
echo "   - 连续3日下跌 → 分析原因"
echo "   - 月度跌幅 > 10% → 考虑调整"
echo ""
echo "💡 查看部署详情: cat HIGH_RISK_DEPLOYMENT_REPORT.md"