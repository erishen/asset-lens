---
name: "investment-assistant"
description: "Investment strategy system assistant. Invoke when user asks about stock screening, strategy management, backtesting, stock pool, or investment reports."
---

# Investment Strategy System Assistant

This skill helps you automatically select and execute the appropriate investment strategy commands based on user's natural language requests.

## 🔄 累积选股机制

股票池支持**累积选股**，每天运行策略筛选时：

- **新股票** → 添加到股票池，记录首次入选日期
- **已存在股票** → 累计入选项数，记录本次入选信息
- **入选历史** → 每次入选都会记录日期、价格、得分

```
Day 1: 筛选出 A, B, C → 添加到池子 (入选 1 次)
Day 2: 筛选出 B, C, D → B, C 累计入选 2 次，D 新增
Day 3: 筛选出 A, E   → A 累计入选 2 次，E 新增
```

**累积数据可用于**：
- 识别"常客"股票（多次入选可能更值得关注）
- 分析策略稳定性（股票是否持续符合条件）
- 优化策略参数（根据入选频率调整）

## 🌍 市场环境感知

策略选股受市场环境影响，系统提供**市场环境分析**功能：

| 环境类型 | 特征 | 推荐策略 |
|----------|------|----------|
| **牛市** | 20日涨幅 > 10%，60日涨幅 > 20% | momentum, value |
| **熊市** | 20日跌幅 > 10%，60日跌幅 > 20% | dividend, reversal |
| **震荡市** | 波动率 > 3%，涨跌幅不大 | value, dividend |

### 每日自动任务 (make daily)

`make daily` 是日度分析的核心命令，每天运行一次即可完成全部数据更新：

| 步骤 | 命令 | 功能 |
|------|------|------|
| 1 | `update-market-data-fast` | 更新市场指数 |
| 2 | `db-auto-sync` | 智能同步股票历史数据 |
| 3 | `pnl` | 估算今日盈亏 |
| 4 | `auto-trade-dry` | 自动交易信号 |
| 5 | `fund-holding` | 基金持仓分析 |

**使用方式：**
```bash
make daily
```

**参数设置：**
```bash
# 自定义同步参数
make db-auto-sync DAYS=180 LIMIT=50  # 获取180天历史，每天同步50只
```

### 策略自适应

系统会根据市场环境**自动调整策略参数**：

| 环境条件 | 参数调整 |
|----------|----------|
| 牛市 | 放宽动量条件，适度放宽估值 |
| 熊市 | 提高动量要求，提高安全边际 |
| 高波动 | 收紧止损 |
| 悲观情绪 | 降低仓位 |
| 乐观情绪 | 适度提高仓位 |

### 市场环境命令

| 用户说 | 执行命令 |
|--------|----------|
| "市场环境" / "分析市场" | `asset-lens market-environment --analyze` |
| "适配策略" / "调整参数" | `asset-lens market-environment --adapt <strategy>` |

## 📊 个人数据整合

系统可以整合您每周记录的个人数据：

### 支持的数据

| 数据类型 | 来源 | 说明 |
|----------|------|------|
| **国内指数** | 股市指数-表格 1.csv | 沪深300、中证500、上证指数、创业板指等 |
| **海外ETF** | 美元ETF-表格 1.csv | QQQ、SPY、GLD、VXX |
| **汇率** | 资产汇总-表格 1.csv | 美元汇率、港元汇率 |

### 个人数据命令

| 用户说 | 执行命令 |
|--------|----------|
| "加载个人数据" / "我的数据" | `asset-lens personal-data load` |
| "市场概况" / "指数概况" | `asset-lens personal-data summary` |
| "指数历史" | `asset-lens personal-data history --index 上证指数 --days 60` |

## Command Mapping

### Stock Screening (股票筛选)

| User Intent | Command |
|-------------|---------|
| "筛选股票" / "选股" / "找股票" | `make screen-stocks` |
| "基本面筛选" / "价值投资" | `make screen-fundamental` |
| "技术面筛选" / "趋势选股" | `make screen-technical` |
| "放量突破" / "成交量放大" | `make volume-breakout` |
| "用策略筛选" / "策略选股" | `make strategy-screen NAME=<strategy>` |

### Strategy Management (策略管理)

| User Intent | Command |
|-------------|---------|
| "查看策略" / "有哪些策略" / "策略列表" | `make strategy-list` |
| "策略详情" / "策略说明" | `make strategy-show NAME=<name>` |
| "设置策略" / "选择策略" | `make strategy-set NAME=<name>` |
| "优化策略" / "最佳策略" | `make optimize-strategy` |

### Stock Pool Management (股票池管理)

| User Intent | Command |
|-------------|---------|
| "股票池" / "观察列表" | `make stock-pool-list` |
| "股票池状态" / "持仓情况" | `make stock-pool-status` |
| "添加股票" | `asset-lens stock-pool add --code <code> --name <name> --price <price>` |
| "模拟买入" | `asset-lens stock-pool buy --code <code> --price <price>` |
| "模拟卖出" | `asset-lens stock-pool sell --code <code> --price <price>` |

### Backtesting (回测)

| User Intent | Command |
|-------------|---------|
| "回测" / "测试策略" | `make backtest STRATEGY=<name>` |
| "价值策略回测" | `make backtest-value` |
| "动量策略回测" | `make backtest-momentum` |

### Investment Reports (投资报告)

| User Intent | Command |
|-------------|---------|
| "投资状态" / "系统状态" | `make investment-status` |
| "投资报告" / "导出数据" | `make investment-report` |

### Market Data (市场数据)

| User Intent | Command |
|-------------|---------|
| "更新数据" / "获取数据" | `make update-all-data` |
| "市场数据" / "指数数据" | `make update-market-data-async` |
| "ETF预测" / "行业预测" | `make predict-etf` |
| "我的ETF" / "持仓ETF预测" | `make predict-etf-portfolio` |

### Data Sync (数据同步)

| User Intent | Command |
|-------------|---------|
| "同步数据" / "同步 ts-demo 数据" / "同步最新数据" | `make sync-data` |
| "同步最新" / "只同步最新数据" | `make sync-data-latest` |
| "预览同步" / "查看同步内容" / "同步预览" | `make sync-data-preview` |

### Analysis (分析)

| User Intent | Command |
|-------------|---------|
| "分析投资" / "投资组合分析" | `make analyze` |
| "盈亏估算" / "今天盈亏" | `make pnl` |
| "周盈亏" | `make pnl-weekly` |
| "收益估算" | `make estimate` |

### Database Management (数据库管理)

| User Intent | Command |
|-------------|---------|
| "数据库状态" / "数据统计" | `make db-stats` |
| "同步股票数据" / "智能同步" | `make db-auto-sync` |
| "清理旧数据" / "清理过期数据" | `make db-clean-old` |
| "批量获取数据" | `make db-batch-fetch LIMIT=100 DAYS=180` |

### Testing (测试)

| User Intent | Command |
|-------------|---------|
| "运行测试" / "测试" | `make test` |
| "快速测试" / "核心测试" | `make test-fast` |
| "测试覆盖率" | `make test-cov` |
| "收集测试用例" | `make test-collect` |

## Available Strategies

1. **value** - 价值投资策略
   - 低估值、稳健增长
   - PE < 20, 市值 50-500亿, 换手率 1-5%

2. **momentum** - 成长动量策略
   - 追踪强势股
   - 放量突破, 涨幅 3-9%, 换手率 5-15%

3. **reversal** - 困境反转策略
   - 抄底超跌股
   - 5日跌幅 > 15%, PB < 1.5

4. **dividend** - 稳健红利策略
   - 高股息、低波动
   - PE < 15, 市值 > 200亿, 低换手

## Usage Examples

When user says:
- "帮我筛选一些股票" → Execute `make screen-stocks`
- "用价值策略选股" → Execute `make strategy-screen NAME=value`
- "看看股票池" → Execute `make stock-pool-list`
- "回测一下动量策略" → Execute `make backtest-momentum`
- "今天盈亏怎么样" → Execute `make pnl`
- "更新下数据" → Execute `make update-all-data`

## Workflow

1. **Initial Setup**: `make update-all-data` - Update all market data
2. **Strategy Selection**: `make strategy-list` → `make strategy-set NAME=<name>`
3. **Stock Screening**: `make strategy-screen NAME=<name>`
4. **Stock Pool**: Add stocks → Simulate buy/sell
5. **Backtesting**: `make backtest STRATEGY=<name>`
6. **Optimization**: `make optimize-strategy`
7. **Reports**: `make investment-status` or `make investment-report`

## Notes

- All commands should be run in the `asset-lens` directory
- Use `make help` to see all available commands
- Strategy names: value, momentum, reversal, dividend
- Stock codes format: sh600519, sz000001, hk00700
