# Asset-Lens：个人资产分析系统

> 一个功能完整的个人资产分析系统，从投资组合管理到策略回测，从数据获取到智能分析

---

## 🎯 项目定位

Asset-Lens 是为个人投资者设计的资产分析系统，解决以下痛点：

- **投资组合分散**：多个平台、多种类型资产难以统一管理
- **数据获取困难**：需要从多个渠道获取股票、基金数据
- **策略验证复杂**：缺少便捷的策略回测工具
- **风险监控缺失**：无法及时发现投资风险

---

## 🌟 核心功能

### 1. 投资组合管理

```
┌─────────────────────────────────────────────────────────────┐
│                    投资组合管理                              │
├─────────────────────────────────────────────────────────────┤
│  • 多平台数据整合（银行、券商、第三方平台）                    │
│  • 多资产类型支持（股票、基金、债券、理财、黄金等）            │
│  • 实时净值计算与收益追踪                                    │
│  • IRR 内部收益率计算                                        │
│  • 资产配置分析与优化建议                                    │
└─────────────────────────────────────────────────────────────┘
```

**支持的资产类型**：

| 类型 | 说明 |
|------|------|
| 股票 | A股、港股、美股 |
| 基金 | 公募基金、ETF、QDII |
| 债券 | 国债、企业债、可转债 |
| 理财 | 银行理财、券商理财 |
| 黄金 | 实物黄金、纸黄金 |
| 存款 | 定期存款、大额存单 |

### 2. 股票池策略系统

三层架构设计，提供完整的策略开发、回测、评估能力：

```
┌─────────────────────────────────────────────────────────────┐
│  第一层：股票池构建 (StockPoolBuilder)                       │
├─────────────────────────────────────────────────────────────┤
│  基本面筛选                    技术面筛选                     │
│  ├── PE/PB 估值               ├── 均线系统                   │
│  ├── ROE 盈利能力             ├── 突破形态                   │
│  ├── 营收增长                 ├── 成交量分析                 │
│  ├── 现金流                   └── MACD/KDJ                   │
│  └── 负债率                                                  │
│                                                              │
│  情绪面筛选                    行业轮动                       │
│  ├── 主力资金流向              ├── 板块热度                   │
│  ├── 北向资金                  ├── 行业轮动                   │
│  ├── 融资融券                  └── 概念题材                   │
│  └── 机构持仓                                                │
│                                                              │
│  财务质量                      因子分层                       │
│  ├── 盈利质量                  ├── 价值因子                   │
│  ├── 运营效率                  ├── 成长因子                   │
│  └── 偿债能力                  └── 质量因子                   │
├─────────────────────────────────────────────────────────────┤
│  输出：入池理由矩阵 + 备选股票池                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  第二层：策略模拟 (StrategySimulator)                        │
├─────────────────────────────────────────────────────────────┤
│  再平衡控制                    风险控制                       │
│  ├── 日/周/月/季频率           ├── 固定止损                   │
│  ├── 触发条件                  ├── 追踪止损                   │
│  └── 调仓逻辑                  ├── ATR止损                    │
│                                └── 止盈策略                   │
│  持仓管理                      交易成本                       │
│  ├── 最大持仓数                ├── 手续费                     │
│  ├── 权重限制                  ├── 滑点                       │
│  ├── 分散度控制                └── 印花税                     │
│  └── 最小持有期                                              │
├─────────────────────────────────────────────────────────────┤
│  输出：收益曲线 + 交易明细 + 风险指标                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  第三层：策略评估 (StrategyEvaluator)                        │
├─────────────────────────────────────────────────────────────┤
│  收益分析                      风险分析                       │
│  ├── 总收益率                  ├── 最大回撤                   │
│  ├── 年化收益                  ├── 波动率                     │
│  ├── 超额收益                  ├── 夏普比率                   │
│  └── 分阶段收益                └── 索提诺比率                 │
│                                                              │
│  因子贡献                      可用性判定                     │
│  ├── 各因子贡献度              ├── 策略评分                   │
│  ├── 失效期分析                ├── 风险提示                   │
│  └── 风格敏感度                └── 优化建议                   │
├─────────────────────────────────────────────────────────────┤
│  输出：策略可用性判定 + 风险提示 + 优化建议                    │
└─────────────────────────────────────────────────────────────┘
```

### 3. 策略筛选

内置多种投资策略：

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| **价值策略** | 低估值、稳健增长 | 长期投资 |
| **动量策略** | 追踪强势股 | 趋势市场 |
| **红利策略** | 高股息、低波动 | 防御配置 |
| **困境反转** | 抄底超跌股 | 逆向投资 |

### 4. 自动化监控

```
┌─────────────────────────────────────────────────────────────┐
│                    自动化监控系统                            │
├─────────────────────────────────────────────────────────────┤
│  定时任务                                                      │
│  ├── 每日净值更新                                              │
│  ├── 每周策略筛选                                              │
│  ├── 每月资产报告                                              │
│  └── 到期提醒                                                  │
│                                                              │
│  风险预警                                                      │
│  ├── 单资产占比过高                                            │
│  ├── 高风险产品集中                                            │
│  ├── 产品即将到期                                              │
│  └── 收益率异常                                                │
│                                                              │
│  消息推送                                                      │
│  ├── 企业微信                                                  │
│  ├── 钉钉                                                      │
│  └── 邮件                                                      │
└─────────────────────────────────────────────────────────────┘
```

### 5. 智能分析

- **AI 投资建议**：基于 LLM 的投资建议生成
- **市场情绪分析**：综合多维度指标判断市场情绪
- **个性化推荐**：根据持仓和偏好推荐投资标的

---

## 🏗️ 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      展示层 (Presentation)                   │
├─────────────────────────────────────────────────────────────┤
│  CLI (Click+Rich)     │  Web API (FastAPI)  │  WebSocket    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      业务层 (Business)                       │
├─────────────────────────────────────────────────────────────┤
│  Portfolio Manager    │  Strategy Engine   │  Risk Manager  │
│  Stock Pool Builder   │  Strategy Simulator│  Alert System  │
│  Report Generator     │  Strategy Evaluator│  AI Analyzer   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据层 (Data)                           │
├─────────────────────────────────────────────────────────────┤
│  Data Fetchers        │  Data Parsers       │  Cache        │
│  ├── AkShare          │  ├── CSV Parser     │  ├── Memory   │
│  ├── Tushare          │  ├── JSON Parser    │  └── Disk     │
│  ├── Baostock         │  └── Excel Parser   │               │
│  └── Multi-Source     │                      │               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      基础设施层 (Infrastructure)             │
├─────────────────────────────────────────────────────────────┤
│  Config Center        │  Logger             │  HTTP Client  │
│  Scheduler            │  Notification       │  Currency     │
└─────────────────────────────────────────────────────────────┘
```

### 目录结构

```
asset-lens/
├── asset_lens/
│   ├── cli.py                    # CLI 入口
│   ├── config.py                 # 配置中心
│   │
│   ├── core/                     # 核心业务
│   │   ├── portfolio_analytics.py    # 投资组合分析
│   │   ├── irr_calculator.py         # IRR 计算
│   │   ├── ai_analyzer.py            # AI 分析
│   │   ├── market_sentiment.py       # 市场情绪
│   │   └── realtime_pnl.py           # 实时盈亏
│   │
│   ├── trading/                  # 交易策略
│   │   ├── stock_pool_builder.py     # 股票池构建
│   │   ├── strategy_simulator.py     # 策略模拟
│   │   ├── strategy_evaluator.py     # 策略评估
│   │   └── auto_trader.py            # 自动交易
│   │
│   ├── strategy/                 # 策略引擎
│   │   ├── engine.py                 # 策略引擎
│   │   ├── screener.py               # 股票筛选
│   │   └── backtester.py             # 回测框架
│   │
│   ├── data/                     # 数据层
│   │   ├── models.py                 # 数据模型
│   │   ├── parsers/                  # 数据解析器
│   │   ├── fetchers/                 # 数据获取器
│   │   └── providers/                # 数据源提供者
│   │
│   ├── web/                      # Web API
│   │   ├── api.py                    # API 入口
│   │   └── routes/                   # 路由模块
│   │
│   ├── report/                   # 报告生成
│   │   ├── analyzer.py               # 分析报告
│   │   ├── charts.py                 # 图表生成
│   │   └── templates/                # 报告模板
│   │
│   └── utils/                    # 工具函数
│       ├── logger.py                 # 日志系统
│       ├── http_client.py            # HTTP 客户端
│       └── progress.py               # 进度条
│
├── tests/                        # 测试用例
├── docs/                         # 文档
├── pyproject.toml                # 项目配置
├── Makefile                      # 命令集成
└── README.md                     # 项目说明
```

---

## 🔧 技术选型

### 核心技术栈

| 类别 | 技术 | 选型理由 |
|------|------|----------|
| **语言** | Python 3.10+ | 丰富的金融数据分析库 |
| **Web 框架** | FastAPI | 高性能、自动文档、类型提示 |
| **CLI** | Click + Rich | 强大的命令行工具 + 美观输出 |
| **数据处理** | Pandas + NumPy | 金融数据分析标准工具 |
| **计算** | SciPy | 科学计算、统计分析 |
| **可视化** | Matplotlib | 图表生成 |

### 数据源

| 数据源 | 类型 | 特点 |
|--------|------|------|
| **AkShare** | 开源免费 | 无需注册，数据全面 |
| **Tushare** | 需注册 | 数据更完整，需积分 |
| **Baostock** | 免费 | 包含换手率等指标 |
| **新浪/腾讯** | 实时行情 | 免费，实时性好 |

### 质量保障

| 工具 | 用途 |
|------|------|
| **pytest** | 单元测试 |
| **pytest-xdist** | 并行测试 |
| **pylint** | 代码检查 |
| **mypy** | 类型检查 |
| **ruff** | 快速 linter |
| **pre-commit** | 提交前检查 |
| **GitHub Actions** | CI/CD |

---

## 💡 设计理念

### 1. 模块化设计

每个模块遵循单一职责原则：

```python
# 股票池构建器只负责构建
builder = StockPoolBuilder()
builder.add_fundamental_filters()
builder.add_technical_filters()
pool = builder.build_pool(data)

# 策略模拟器只负责模拟
simulator = StrategySimulator(config)
result = simulator.run_simulation(pool, prices, start, end)

# 策略评估器只负责评估
evaluator = StrategyEvaluator()
evaluation = evaluator.evaluate("strategy", result)
```

### 2. 配置中心化

所有配置统一管理：

```python
# config.py
class Config:
    # 数据源配置
    akshare_enabled: bool = True
    tushare_token: str | None = None
    
    # 默认汇率
    default_usd_rate: float = 6.90
    default_hkd_rate: float = 0.89
    
    # 风险阈值
    min_return_threshold: float = 2.0

config = Config()  # 全局单例
```

### 3. 数据模型化

使用 dataclass 定义清晰的数据模型：

```python
@dataclass
class InvestmentProduct:
    investment_type: InvestmentType
    name: str
    risk_level: RiskLevel
    current_amount: Decimal | None = None
    profit_amount: Decimal | None = None
    return_rate: Decimal | None = None
    annual_return: Decimal | None = None
```

### 4. 错误处理

多数据源故障切换：

```python
class MultiSourceFetcher:
    def fetch(self, code: str):
        for source in self.sources:
            try:
                return source.fetch(code)
            except Exception:
                continue
        raise AllSourcesFailedError()
```

---

## 📊 性能优化

### 测试优化

| 优化项 | 优化前 | 优化后 | 提升 |
|--------|--------|--------|------|
| 测试时间 | 191s | 44s | **77%** |
| 并行执行 | 无 | pytest-xdist | 新增 |

### 数据缓存

```python
class CacheManager:
    def get_with_cache(self, key: str, fetcher: Callable, ttl: int):
        if cached := self.read_cache(key):
            if self.is_valid(key, ttl):
                return cached
        
        data = fetcher()
        self.write_cache(key, data)
        return data
```

### 大文件拆分

| 文件 | 拆分前 | 拆分后 |
|------|--------|--------|
| web/api.py | 1277 行 | 4 个模块 (~180行/个) |
| report/analyzer.py | 1082 行 | 3 个模块 (~150行/个) |
| data/csv_parser.py | 940 行 | 3 个模块 (~100行/个) |

---

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/asset-lens/asset-lens.git
cd asset-lens

# 安装依赖
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"
```

### 基本使用

```bash
# 交互式界面
make interactive

# 分析投资组合
make analyze

# 策略筛选
make momentum-screen

# 启动 Web API
make web

# 运行测试
make test

# 代码检查
make lint
```

### 股票池策略示例

```python
from asset_lens.trading import (
    StockPoolBuilder,
    StrategySimulator,
    StrategyEvaluator,
    SimulationConfig,
    RebalanceFrequency,
)

# 1. 构建股票池
builder = StockPoolBuilder()
builder.add_filter("pe", "<", 30)
builder.add_filter("roe", ">", 15)
builder.add_filter("revenue_growth", ">", 10)
pool = builder.build_pool(stock_data_list, min_score=60)

# 2. 配置策略
config = SimulationConfig(
    initial_capital=1000000,
    max_positions=10,
    rebalance_frequency=RebalanceFrequency.WEEKLY,
    stop_loss_pct=0.08,
    take_profit_pct=0.20,
    min_holding_days=5,
)

# 3. 运行模拟
simulator = StrategySimulator(config)
result = simulator.run_simulation(
    pool, 
    price_history, 
    "2024-01-01", 
    "2024-12-31"
)

# 4. 评估策略
evaluator = StrategyEvaluator()
evaluation = evaluator.evaluate("value_strategy", result.to_dict())

print(f"总收益率: {result.total_return:.2f}%")
print(f"最大回撤: {result.max_drawdown:.2f}%")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
print(f"策略可用性: {evaluation.usability.value}")
```

---

## 📈 项目质量

| 指标 | 数值 |
|------|------|
| Python 文件数 | 148 |
| 代码行数 | 43,000+ |
| 测试用例数 | 1,680 |
| 测试通过率 | 100% |
| Lint 分值 | 10.00/10 |
| mypy 检查 | 通过 |

---

## 🎯 未来规划

### 短期 (1-3月)

- [ ] Web Dashboard 可视化界面
- [ ] 更多数据源支持
- [ ] 策略市场（分享/下载策略）

### 中期 (3-6月)

- [ ] 机器学习因子挖掘
- [ ] 实盘交易接口
- [ ] 移动端 App

### 长期 (6-12月)

- [ ] 社区版 vs 企业版
- [ ] 多账户管理
- [ ] 家族财富管理

---

## 🤝 贡献指南

欢迎贡献代码、报告问题、提出建议！

```bash
# 1. Fork 项目
# 2. 创建特性分支
git checkout -b feature/amazing-feature

# 3. 提交更改
git commit -m 'Add amazing feature'

# 4. 推送到分支
git push origin feature/amazing-feature

# 5. 创建 Pull Request
```

### 代码规范

- Lint 分值：10.00/10
- 类型检查：mypy 通过
- 测试覆盖：新增代码需要测试

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢以下开源项目：

- [AkShare](https://github.com/akfamily/akshare) - 开源金融数据接口
- [Tushare](https://tushare.pro/) - 金融数据接口
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Web 框架
- [Rich](https://github.com/Textualize/rich) - 终端美化库
- [Pandas](https://pandas.pydata.org/) - 数据分析库

---

*最后更新：2026-03-16*
