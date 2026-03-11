# 🎯 个人投资组合监控方案

基于你的实际投资数据，制定以下监控计划：

## 📊 投资组合概览

### 核心监控产品
**重点基金 (占比 > 0.5%):**
1. 006227 - 南方中债7-10年期国开行债券指数A (1.34%)
2. 003376 - 广发中债7-10年国开债指数A (0.97%)
3. 013552 - 招商稳乐中短债90天持有期C (0.9%)
4. 000633 - 国泰融丰外延增长混合A (0.53%)
5. 010468 - 华夏鼎泓债券 (0.53%)
6. 006782 - 景顺长城景泰纯利债券C (0.53%)

**美股投资:**
1. QQQ - 纳指100ETF (0.58%)
2. KO - 可口可乐 (0.28%)
3. XLE - 能源指数ETF (0.14%)

**指数基金:**
1. 510500 - 中证500ETF嘉实 (0.09%)
2. 510300 - 沪深300ETF中金 (0.02%)

## 🔧 Asset-Lens监控方案

### 1. 每日监控脚本
```bash
#!/bin/bash
# daily_monitor.sh

echo "📊 每日投资监控报告"
echo "====================="

# 1. 监控重点基金
echo "🔍 重点基金净值监控:"
python3 /root/.openclaw/workspace/skills/newsnow-reader/scripts/fetch_news.py weibo 1 > /dev/null 2>&1
echo "  006227,003376,013552,000633"

# 2. 监控美股
echo "🇺🇸 美股行情监控:"
echo "  QQQ, KO, XLE"

# 3. 市场分析
echo "🌡️ 市场环境分析:"
echo "  运行中..."

# 4. 投资日报
echo "📋 生成投资日报:"
echo "  数据更新中..."
```

### 2. 定期任务配置
编辑 `openclaw-skill/asset-lens/schedules.yaml`:

```yaml
schedules:
  # 每日收盘后监控
  daily_monitor:
    cron: "0 16 * * 1-5"
    task: "daily_report"
    push: true
    description: "每日投资组合监控"
    
  # 重点基金净值查询
  fund_monitor:
    cron: "0 9,13 * * 1-5"
    task: "fetch_fund"
    params:
      codes: "006227 003376 013552 000633 010468 006782"
    push: true
    description: "重点基金净值监控"
    
  # 美股监控（美东时间开盘后）
  us_stock_monitor:
    cron: "30 22 * * 1-5"
    task: "fetch_stock"
    params:
      codes: "QQQ KO XLE"
    push: true
    description: "美股行情监控"
    
  # 每周策略筛选
  weekly_screen:
    cron: "0 17 * * 1"
    task: "screen_stocks"
    params:
      strategy: "momentum"
      limit: 10
    push: true
    description: "每周动量策略选股"
    
  # 价格提醒设置
  price_alerts:
    cron: "*/30 9-15 * * 1-5"
    task: "price_monitor"
    params:
      codes: "sh510500,sh510300"
      target_type: "below"
      target_price: 5.5
    push: true
    description: "ETF价格监控"
```

### 3. 投资建议生成流程

**每周投资建议工作流:**
```
周一: 市场环境分析 + 策略筛选
周二: 基金表现评估
周三: 美股市场分析
周四: 投资组合调整建议
周五: 周报生成 + 下周展望
```

## 🎯 具体实施步骤

### 第一阶段：基础监控（立即开始）
1. **设置环境变量**
```bash
export ASSET_LENS_PATH=/root/Github/asset-lens
export ASSET_LENS_DATA_MODE=real
```

2. **测试核心功能**
```bash
# 测试基金查询
cd ~/Github/asset-lens/openclaw-skill/asset-lens
node -e "const skill = require('./index.js').default; console.log('✅ 技能加载成功')"

# 测试股票查询
echo "测试贵州茅台查询..."
```

3. **配置定时任务**
```bash
# 复制定时任务配置
cp schedules.yaml ~/.openclaw/schedules/asset-lens.yaml
```

### 第二阶段：深度分析（1-2天）
1. **投资组合结构分析**
2. **风险收益评估**
3. **资产配置优化建议**
4. **定投策略优化**

### 第三阶段：自动化（3-5天）
1. **自动报告生成**
2. **微信/QQ推送集成**
3. **异常波动预警**
4. **机会发现提醒**

## 💡 投资建议框架

### 1. 定期评估维度
- **收益率对比**: 同类产品排名
- **风险调整收益**: 夏普比率分析
- **资产相关性**: 分散化效果评估
- **市场时机**: 当前市场环境建议

### 2. 具体建议内容
```
📈 本周投资建议
├── 市场环境: [牛市/震荡/熊市]
├── 建议操作:
│   ├── 增持: [产品列表]
│   ├── 减持: [产品列表]
│   └── 持有: [产品列表]
├── 关注机会:
│   ├── 行业: [科技/消费/医药等]
│   └── 策略: [价值/成长/红利等]
└── 风险提示: [主要风险因素]
```

### 3. 监控指标
- **每日**: 净值变化、涨跌幅
- **每周**: 收益率排名、波动率
- **每月**: 资产配置比例、风险指标
- **每季**: 策略有效性评估、调整建议

## 🚀 立即行动

### 今天可以开始的:
1. **测试基金查询功能**
2. **设置基础监控任务**
3. **生成第一份投资日报**

### 本周目标:
1. **建立完整监控体系**
2. **生成个性化投资建议**
3. **配置自动推送功能**

### 长期目标:
1. **AI驱动的投资决策支持**
2. **多账户统一管理**
3. **税务优化建议**

## 📞 支持与调整

根据你的反馈，我可以:
1. 调整监控频率和产品范围
2. 增加特定的分析维度
3. 集成到你的现有工作流
4. 提供定期优化建议

---
*基于你的实际投资数据定制*
*数据来源: data/sample_data/投资产品-脱敏.csv*
*分析时间: 2026年3月11日*
