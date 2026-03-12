#!/bin/bash
# 1万元投资监控系统部署脚本

echo "💰 1万元投资监控系统部署..."
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

# 3. 计算1万元投资金额
echo "📊 计算1万元投资金额..."
python3 calculate_investment_amounts.py 10000

if [ $? -eq 0 ]; then
    echo "✅ 投资金额计算完成"
else
    echo "❌ 投资金额计算失败"
    exit 1
fi

# 4. 创建1万元投资监控配置
echo "📋 创建1万元投资监控配置..."
mkdir -p config/investment_10000_monitor

# 创建重点产品监控配置
cat > config/investment_10000_monitor/focus_products.json << 'EOF'
{
  "focus_products": [
    {
      "name": "其他（理财/国债/现金等）",
      "code": "-",
      "type": "其他",
      "risk": "-",
      "investment_amount": 8444.00,
      "percentage": 84.44,
      "monitoring": {
        "priority": "high",
        "frequency": "monthly",
        "reason": "占比最大，但风险较低"
      }
    },
    {
      "name": "高腾微金美元货币基金",
      "code": "GSUSMM",
      "type": "美元基金（美元）",
      "risk": "低",
      "investment_amount": 383.00,
      "percentage": 3.83,
      "monitoring": {
        "priority": "high",
        "frequency": "weekly",
        "reason": "美元资产，关注汇率变化"
      }
    },
    {
      "name": "南方中债7-10年期国开行债券指数A",
      "code": "006227",
      "type": "债券",
      "risk": "中",
      "investment_amount": 134.00,
      "percentage": 1.34,
      "monitoring": {
        "priority": "high",
        "frequency": "weekly",
        "reason": "债券类重点产品"
      }
    },
    {
      "name": "纳指100ETF-Invesco QQQ Trust",
      "code": "QQQ",
      "type": "美股（美元）",
      "risk": "高",
      "investment_amount": 58.00,
      "percentage": 0.58,
      "monitoring": {
        "priority": "critical",
        "frequency": "daily",
        "reason": "高风险美股，波动大"
      }
    }
  ],
  "monitoring_thresholds": {
    "critical": 100.00,
    "high": 50.00,
    "medium": 20.00,
    "low": 10.00
  }
}
EOF

# 创建高风险产品监控配置
cat > config/investment_10000_monitor/high_risk_monitor.json << 'EOF'
{
  "high_risk_monitoring": {
    "daily_monitoring": [
      {
        "name": "纳指100ETF-Invesco QQQ Trust",
        "code": "QQQ",
        "amount": 58.00,
        "alert_threshold": 3.0,
        "check_time": "21:30"
      },
      {
        "name": "可口可乐",
        "code": "KO",
        "amount": 28.00,
        "alert_threshold": 5.0,
        "check_time": "21:30"
      },
      {
        "name": "能源指数ETF-SPDR XLE",
        "code": "XLE",
        "amount": 14.00,
        "alert_threshold": 4.0,
        "check_time": "21:30"
      }
    ],
    "weekly_monitoring": [
      {
        "name": "国联安沪深300指数增强A",
        "code": "020220",
        "amount": 25.00,
        "check_day": "friday"
      },
      {
        "name": "博道盛彦混合A",
        "code": "012124",
        "amount": 24.00,
        "check_day": "friday"
      },
      {
        "name": "易方达亚洲精选股票（QDII）",
        "code": "118001",
        "amount": 22.00,
        "check_day": "friday"
      }
    ],
    "alert_rules": {
      "price_drop_5pct": "单日跌幅 > 5%",
      "price_drop_10pct_week": "周跌幅 > 10%",
      "amount_loss_10pct": "损失金额 > 投资金额的10%",
      "high_risk_loss_20yuan": "高风险产品损失 > 20元"
    }
  }
}
EOF

# 创建投资金额预警配置
cat > config/investment_10000_monitor/amount_alerts.json << 'EOF'
{
  "amount_based_alerts": [
    {
      "level": "critical",
      "condition": "investment_amount >= 100",
      "action": "每日监控，设置价格预警",
      "products": ["其他（理财/国债/现金等）", "高腾微金美元货币基金", "南方中债7-10年期国开行债券指数A"]
    },
    {
      "level": "high",
      "condition": "investment_amount >= 50",
      "action": "每周检查，关注表现",
      "products": ["广发中债7-10年国开债指数A", "季季享-招商稳乐中短债90天持有期C", "纳指100ETF-Invesco QQQ Trust"]
    },
    {
      "level": "medium",
      "condition": "investment_amount >= 20",
      "action": "每月回顾，评估是否需要调整",
      "products": ["可口可乐", "国联安沪深300指数增强A", "博道盛彦混合A", "易方达亚洲精选股票（QDII）"]
    },
    {
      "level": "low",
      "condition": "investment_amount < 20",
      "action": "季度检查，长期持有为主",
      "products_count": 41
    }
  ],
  "loss_protection": {
    "max_single_loss": 10.0,
    "max_daily_loss": 50.0,
    "max_weekly_loss": 100.0,
    "stop_loss_percentage": 10.0
  }
}
EOF

echo "✅ 监控配置已生成"

# 5. 创建QQ提醒配置
echo "💬 创建QQ提醒配置..."
cat > config/investment_10000_monitor/qq_reminders.json << 'EOF'
{
  "qq_reminders": [
    {
      "name": "1万元投资每日提醒",
      "schedule": "0 9 * * *",
      "message": "💰 1万元投资每日提醒\\n📅 时间: 09:00\\n🎯 总投资: 10,000元\\n📊 今日关注:\\n   • 高风险美股: QQQ(58元)、KO(28元)\\n   • 重点债券: 006227(134元)、003376(97元)\\n💡 建议: 关注美股前日表现，检查债券稳定性",
      "priority": "high"
    },
    {
      "name": "高风险产品美股开盘提醒",
      "schedule": "0 21 * * *",
      "message": "🇺🇸 高风险美股开盘提醒\\n🕘 时间: 21:00 (北京时间)\\n📊 美股即将开盘\\n🎯 监控产品:\\n   • QQQ(纳指ETF): 58元\\n   • KO(可口可乐): 28元\\n   • XLE(能源ETF): 14元\\n💡 建议: 查看盘前期货，设置价格预警",
      "priority": "critical"
    },
    {
      "name": "投资金额周报提醒",
      "schedule": "0 17 * * 5",
      "message": "📋 1万元投资周报提醒\\n📅 时间: 周五 17:00\\n💰 本周回顾:\\n   • 总投资: 10,000元\\n   • 重点产品表现检查\\n   • 高风险产品波动评估\\n💡 建议: 检查是否需要调整仓位",
      "priority": "medium"
    },
    {
      "name": "大额投资月度回顾",
      "schedule": "0 20 28 * *",
      "message": "📊 大额投资月度回顾\\n📅 时间: 每月28日 20:00\\n🎯 重点关注:\\n   • 其他资产(8444元): 占比84.44%\\n   • 美元基金(383元): 关注汇率\\n   • 重点债券(134元): 检查收益\\n💡 建议: 评估整体投资策略，考虑再平衡",
      "priority": "high"
    }
  ]
}
EOF

echo "✅ QQ提醒配置已生成"

# 6. 创建定时任务
echo "📅 创建定时任务..."
cat > config/investment_10000_monitor/schedules.json << 'EOF'
{
  "schedules": [
    {
      "name": "每日投资晨报",
      "time": "09:00",
      "tasks": [
        "检查前日投资表现",
        "查看重点产品价格变化",
        "评估当日投资策略"
      ],
      "output": "logs/daily_morning_report.log"
    },
    {
      "name": "美股盘前检查",
      "time": "21:15",
      "tasks": [
        "检查QQQ、KO、XLE前日收盘价",
        "查看美股期货表现",
        "关注重要经济数据"
      ],
      "output": "logs/us_premarket_check.log"
    },
    {
      "name": "重点产品周度检查",
      "day": "friday",
      "time": "17:00",
      "tasks": [
        "检查投资金额 > 50元的产品",
        "评估高风险产品表现",
        "分析投资组合变化"
      ],
      "output": "logs/weekly_focus_check.log"
    },
    {
      "name": "投资金额月度分析",
      "day": "last_day",
      "time": "20:00",
      "tasks": [
        "分析月度收益表现",
        "检查投资金额分布变化",
        "调整监控优先级"
      ],
      "output": "logs/monthly_amount_analysis.log"
    }
  ]
}
EOF

echo "✅ 定时任务配置已生成"

# 7. 创建报告目录
echo "📁 创建报告目录..."
mkdir -p output/investment_10000_reports
mkdir -p logs/investment_10000
mkdir -p charts/investment_10000

# 8. 生成部署报告
echo "📋 生成部署报告..."
cat > INVESTMENT_10000_MONITOR_REPORT.md << 'EOF'
# 1万元投资监控系统部署报告

## 系统概述
基于1万元总投资假设，按占比计算各个产品的具体投资金额，并建立相应的监控系统。

## 投资金额分析
### 📊 总投资分布
- **总投资**: 10,000元
- **总产品数**: 50个
- **平均每产品**: 199.94元

### 🏷️ 按类型金额分布
1. **其他**: 8,444.00元 (84.44%)
2. **债券**: 741.00元 (7.41%)
3. **美元基金**: 383.00元 (3.83%)
4. **基金**: 245.00元 (2.45%)
5. **美股**: 100.00元 (1.00%)

### ⚠️ 按风险金额分布
1. **-**: 8,444.00元 (84.44%)
2. **中低**: 510.00元 (5.10%)
3. **低**: 383.00元 (3.83%)
4. **中**: 352.00元 (3.52%)
5. **中高**: 182.00元 (1.82%)
6. **高**: 126.00元 (1.26%)

## 重点监控产品
### 🎯 投资金额 > 50元 (重点关注)
1. **其他资产**: 8,444.00元 (占比84.44%)
2. **高腾微金美元货币基金**: 383.00元 (3.83%)
3. **南方中债7-10年期国开行债券指数A**: 134.00元 (1.34%)
4. **广发中债7-10年国开债指数A**: 97.00元 (0.97%)
5. **季季享-招商稳乐中短债90天持有期C**: 90.00元 (0.90%)
6. **纳指100ETF-Invesco QQQ Trust**: 58.00元 (0.58%)

### 🔥 高风险产品监控
#### ⚠️ 每日监控 (风险等级5)
1. **QQQ**: 58.00元 - 纳指ETF，波动大
2. **KO**: 28.00元 - 可口可乐，消费股
3. **XLE**: 14.00元 - 能源ETF，受油价影响

#### 🔸 每周监控 (风险等级4)
1. **020220**: 25.00元 - 沪深300指数增强
2. **012124**: 24.00元 - 混合基金
3. **118001**: 22.00元 - 亚洲精选股票

## 监控策略
### 💰 基于金额的监控优先级
1. **关键级** (>100元): 每日监控，设置价格预警
2. **高级** (50-100元): 每周检查，关注表现
3. **中级** (20-50元): 每月回顾，评估调整
4. **低级** (<20元): 季度检查，长期持有

### ⏰ 监控时间表
1. **每日 09:00**: 投资晨报
2. **每日 21:15**: 美股盘前检查
3. **每周五 17:00**: 重点产品周度检查
4. **每月底 20:00**: 投资金额月度分析

### 🚨 预警规则
1. **价格波动**: 单日跌幅 > 5%
2. **金额损失**: 损失 > 投资金额的10%
3. **高风险损失**: 高风险产品损失 > 20元
4. **连续下跌**: 连续3日下跌

## 系统配置
### 📁 配置文件
```
config/investment_10000_monitor/
├── focus_products.json      # 重点产品监控
├── high_risk_monitor.json   # 高风险产品监控
├── amount_alerts.json       # 金额预警配置
├── qq_reminders.json        # QQ提醒配置
└── schedules.json           # 定时任务配置
```

### 📊 报告输出
```
output/investment_reports/10000/      # 投资金额报告
output/investment_10000_reports/      # 监控报告
logs/investment_10000/                # 系统日志
charts/investment_10000/              # 图表文件
```

## 使用说明
### 🚀 快速启动
```bash
# 计算1万元投资金额
python3 calculate_investment_amounts.py 10000

# 查看最新报告
cat output/investment_reports/10000/investment_report_10000_*.txt
```

### 📈 监控命令
```bash
# 运行完整分析
python3 calculate_investment_amounts.py

# 指定不同总投资金额
python3 calculate_investment_amounts.py 50000  # 5万元
python3 calculate_investment_amounts.py 100000 # 10万元
```

### 💬 QQ提醒设置
系统已配置以下QQ提醒：
1. **每日 09:00**: 1万元投资每日提醒
2. **每日 21:00**: 高风险美股开盘提醒
3. **每周五 17:00**: 投资金额周报提醒
4. **每月28日 20:00**: 大额投资月度回顾

## 投资建议
### 💡 金额管理
1. **大额集中**: 84.44%集中在"其他"资产，需关注流动性
2. **美元资产**: 383元美元基金，关注汇率风险
3. **债券配置**: 741元债券投资，相对稳定
4. **高风险控制**: 126元高风险投资，占比合理

### 🛡️ 风险控制
1. **止损设置**: 单只产品最大损失不超过投资金额的10%
2. **仓位控制**: 高风险产品总投资不超过总投资的20%
3. **分散投资**: 50个产品分散投资，降低单一风险
4. **定期再平衡**: 每季度评估投资组合，调整仓位

### 📊 绩效评估
1. **绝对收益**: 检查是否达到预期收益目标
2. **相对收益**: 与基准比较表现
3. **风险调整收益**: 考虑波动性的实际收益
4. **金额加权收益**: 大额投资对整体收益影响更大

## 后续优化
### 🔄 短期计划
1. 集成实时行情数据
2. 设置自动金额预警
3. 优化报告可视化

### 🎯 长期计划
1. 连接实际持仓数据
2. 实现动态金额调整