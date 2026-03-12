# Asset-Lens 市场数据获取指南

## 📊 支持的市场数据类型

### 1. 实时行情数据
- **A股股票**: sh600519 (茅台), sz000001 (平安银行)
- **指数**: sh000001 (上证), sh000300 (沪深300), sz399006 (创业板)
- **基金**: 006227, 003376, 013552 等
- **美股**: QQQ, KO, XLE, AAPL, MSFT
- **港股**: 00700 (腾讯), 00941 (中移动)

### 2. 历史数据
- 日K线数据 (开盘、收盘、最高、最低、成交量)
- 周K线、月K线数据
- 技术指标 (MA, MACD, RSI, BOLL等)

### 3. 市场分析数据
- 市场环境分析
- 行业板块表现
- 资金流向
- 市场情绪指标

## 🔧 使用方法

### 方法1: 使用Make命令 (推荐)
```bash
# 更新市场数据
make update-market-data-fast

# 分析市场环境
make market-environment

# 查询具体股票
make fetch-stock CODES="sh600519 sz000001"

# 查询基金
make fetch-fund CODES="006227 003376"
```

### 方法2: 使用Python模块
```bash
# 激活conda环境
conda activate asset-lens

# 运行市场分析
python -m asset_lens market-environment --analyze

# 更新数据
python -m asset_lens update-market-data --api finnhub
```

### 方法3: 使用OpenClaw技能
已为你定制了OpenClaw技能，可以直接调用:
- `fetch_stock(codes="sh600519")` - 查询股票
- `fetch_fund(codes="006227")` - 查询基金
- `market_environment()` - 市场分析
- `screen_stocks(strategy="momentum")` - 策略筛选

## 🔑 API配置

### 必需API密钥
1. **Finnhub** (推荐): https://finnhub.io
   - 免费: 60次/分钟
   - 支持: 全球股票、指数、外汇

2. **Alpha Vantage**: https://www.alphavantage.co
   - 免费: 25次/天
   - 支持: 历史数据完整

3. **Tushare** (A股专用): https://tushare.pro
   - 免费: 10000次/天
   - 支持: A股完整数据

### 配置方法
创建 `~/Github/asset-lens/.env` 文件:
```bash
# API Keys
FINNHUB_API_KEY=your_finnhub_api_key_here
ALPHAVANTAGE_API_KEY=your_alphavantage_api_key_here
TUSHARE_TOKEN=your_tushare_token_here

# 数据模式
DATA_MODE=real  # 或 sample
```

## 📈 你的投资组合相关数据

### 重点监控产品
基于你的投资数据，建议关注以下市场数据:

#### 1. 基金类 (债券基金)
- **006227** - 南方中债7-10年期国开行债券指数A
- **003376** - 广发中债7-10年国开债指数A
- **013552** - 招商稳乐中短债90天持有期C

**监控命令**:
```bash
make fetch-fund CODES="006227 003376 013552"
```

#### 2. 美股持仓
- **QQQ** - 纳指100ETF
- **KO** - 可口可乐
- **XLE** - 能源指数ETF

**监控命令**:
```bash
# 需要Finnhub API
make fetch-stock CODES="QQQ KO XLE"
```

#### 3. A股ETF
- **510500** - 中证500ETF
- **510300** - 沪深300ETF

**监控命令**:
```bash
make fetch-stock CODES="sh510500 sh510300"
```

## 🚀 快速开始脚本

我已创建了以下实用脚本:

### 1. 市场数据报告
```bash
python3 get_market_data.py
```
生成完整的市场分析报告，包含:
- 主要指数表现
- 行业板块分析
- 市场情绪指标
- 投资建议

### 2. 投资监控
```bash
python3 investment_workflow.py
```
基于你的实际投资数据，提供:
- 投资组合分析
- 监控命令生成
- 定时任务配置

### 3. 环境检查
```bash
./test_investment_monitor.sh
```
检查系统配置和功能完整性。

## 💡 高级功能

### 1. 策略筛选
```bash
# 动量策略
make screen-stocks STRATEGY=momentum LIMIT=10

# 价值策略
make screen-stocks STRATEGY=value LIMIT=10

# 红利策略
make screen-stocks STRATEGY=dividend LIMIT=10
```

### 2. 市场预测
```bash
# ETF预测
make predict-etf

# 市场风向
make market-sentiment
```

### 3. 自动化监控
配置 `schedules.yaml` 实现:
- 每日收盘后自动更新数据
- 价格异常自动提醒
- 定期生成投资报告

## 🎯 最佳实践

### 数据更新频率
- **实时数据**: 每30分钟更新一次 (交易时间)
- **日度数据**: 每日收盘后更新
- **周度分析**: 每周一生成
- **月度报告**: 每月初生成

### 监控重点
1. **你的持仓产品** - 006227, 003376, QQQ等
2. **相关指数** - 沪深300, 纳指100
3. **行业板块** - 科技、新能源、医药
4. **市场情绪** - 资金流向、风险偏好

### 风险控制
1. 设置价格预警线
2. 监控异常波动
3. 定期评估风险收益比
4. 保持资产配置平衡

## 📞 技术支持

### 常见问题
1. **API限制** - 使用多个API源轮换
2. **数据延迟** - 配置缓存机制
3. **网络问题** - 设置重试机制
4. **格式错误** - 使用数据验证

### 扩展建议
1. 集成到OpenClaw工作流
2. 开发Web管理界面
3. 添加AI投资建议
4. 支持多账户管理

---

*最后更新: 2026-03-11*
*基于你的实际投资数据定制*
