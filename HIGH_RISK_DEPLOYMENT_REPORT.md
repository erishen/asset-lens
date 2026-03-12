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
