# Asset-Lens 架构文档

> 最后更新：2026年3月12日
> 版本：v1.0

---

## 📋 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [模块说明](#模块说明)
4. [数据流](#数据流)
5. [设计决策](#设计决策)
6. [扩展指南](#扩展指南)

---

## 系统概述

### 项目定位

Asset-Lens 是一个**个人资产操作系统**，专注于：

- 资产数据管理
- 收益分析计算
- 投资行为复盘
- 策略验证实验

**不是**：
- 量化交易系统
- 自动下单平台
- 实时交易系统

### 技术栈

| 层级 | 技术 |
|------|------|
| CLI | Click + Rich |
| 核心 | Python 3.11+ |
| 数据处理 | pandas + numpy |
| 数据库 | CSV 文件（轻量级） |
| AI 分析 | OpenAI API |
| 测试 | pytest + pytest-cov |

---

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────┐
│                    CLI Layer                         │
│  (cli.py, cli_modules/)                             │
│  - 命令解析、参数验证、输出格式化                      │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                   Core Layer                         │
│  (core/)                                             │
│  - 业务逻辑、计算引擎、策略分析                        │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                   Data Layer                         │
│  (data/)                                             │
│  - 数据获取、数据解析、数据模型                        │
│  ├── fetchers/      # 数据获取器                      │
│  │   ├── base.py    # 基类                           │
│  │   ├── stock.py   # 股票数据                       │
│  │   ├── fund.py    # 基金数据                       │
│  │   └── crypto.py  # 加密货币数据                    │
│  └── parsers/       # 数据解析器                      │
│      └── unified_parser.py                          │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                   Utils Layer                        │
│  (utils/)                                            │
│  - 工具函数、日志系统、进度条                          │
└─────────────────────────────────────────────────────┘
```

### 配置中心模式

```
所有模块 → PlatformConfig (配置中心)
          ├── 数据模式 (Sample/Real)
          ├── API Keys
          ├── 缓存路径
          └── 日志配置
```

**优势**：
- 环境感知
- 集中管理
- 易于切换

---

## 模块说明

### 1. CLI Layer (cli_modules/)

**职责**：命令行接口层

| 模块 | 功能 |
|------|------|
| `analysis.py` | 投资分析命令 |
| `data.py` | 数据管理命令 |
| `report.py` | 报告生成命令 |
| `strategy.py` | 策略管理命令 |

**设计原则**：
- 只负责参数解析和输出格式化
- 不包含业务逻辑
- 调用 Core 层完成实际工作

### 2. Core Layer (core/)

**职责**：核心业务逻辑

| 模块 | 功能 | 行数 |
|------|------|------|
| `irr_calculator.py` | IRR 计算 | ~200 |
| `portfolio_analytics.py` | 投资组合分析 | ~300 |
| `ai_analyzer.py` | AI 分析 | ~500 |
| `realtime_pnl.py` | 实时盈亏估算 | ~400 |
| `advanced_analytics.py` | 高级分析 | ~600 |

**设计原则**：
- 单一职责
- 高内聚低耦合
- 可独立测试

### 3. Data Layer (data/)

**职责**：数据获取和解析

#### 3.1 Fetchers (数据获取器)

```
BaseFetcher (抽象基类)
    ├── StockFetcher     # 股票数据
    ├── FundFetcher      # 基金数据
    ├── CryptoFetcher    # 加密货币数据
    ├── FuturesFetcher   # 期货数据
    └── UnifiedFetcher   # 统一接口
```

**数据源优先级**：

| 类型 | 优先级 | 数据源 |
|------|--------|--------|
| 国内指数 | 1 | 腾讯财经 |
| 国内指数 | 2 | 新浪财经 |
| 国内指数 | 3 | AkShare |
| 国外指数 | 1 | AkShare |
| 国外指数 | 2 | 东方财富 |
| 国外指数 | 3 | Alpha Vantage |

#### 3.2 Parsers (数据解析器)

```python
DataParser (统一解析器)
    ├── DateParser           # 日期解析
    ├── InvestmentTypeParser # 投资类型解析
    └── parse_csv_row()      # CSV 行解析
```

### 4. Utils Layer (utils/)

**职责**：通用工具

| 模块 | 功能 |
|------|------|
| `logger.py` | 日志系统 |
| `progress.py` | 进度条 |
| `http_client.py` | HTTP 客户端 |
| `currency_converter.py` | 货币转换 |

---

## 数据流

### 1. 投资分析流程

```
用户输入 → CLI 解析
    ↓
加载配置 (PlatformConfig)
    ↓
读取 CSV 数据 (CSVParser)
    ↓
计算收益 (PortfolioCalculator)
    ↓
生成报告 (ReportGenerator)
    ↓
输出结果 (Rich 格式化)
```

### 2. 市场数据更新流程

```
用户命令 → update_market_data
    ↓
获取指数列表 (MarketIndex)
    ↓
并发获取数据 (ThreadPoolExecutor)
    ↓
多数据源故障转移
    ↓
缓存数据 (内存 + 文件)
    ↓
更新 CSV 文件
```

### 3. AI 分析流程

```
用户命令 → ai_analyze
    ↓
加载投资组合数据
    ↓
构建 Prompt (PromptBuilder)
    ↓
调用 OpenAI API
    ↓
解析结果 (ResultParser)
    ↓
缓存结果 (1小时)
    ↓
输出分析报告
```

---

## 设计决策

### 1. 为什么使用 CSV 而不是数据库？

**决策**：使用 CSV 文件存储数据

**原因**：
- 个人项目，数据量小
- 易于查看和编辑
- 无需数据库维护
- 便于版本控制

**权衡**：
- ✅ 简单易用
- ✅ 无需额外依赖
- ❌ 不适合大数据量
- ❌ 无事务支持

### 2. 为什么使用配置中心模式？

**决策**：所有模块通过 PlatformConfig 获取配置

**原因**：
- 统一配置管理
- 支持多环境切换
- 便于测试 Mock

**实现**：
```python
# 所有模块通过 config 获取配置
from asset_lens.config import config

data_path = config.data_path
api_key = config.finnhub_api_key
```

### 3. 为什么使用多数据源冗余？

**决策**：每个数据类型配置多个备用数据源

**原因**：
- 提高可用性
- 避免单点故障
- 应对 API 限流

**实现**：
```python
fetchers = [
    ("akshare", self._fetch_from_akshare),
    ("eastmoney", self._fetch_from_eastmoney),
    ("alpha_vantage", self._fetch_from_alpha_vantage),
]
```

---

## 扩展指南

### 1. 添加新的数据源

**步骤**：

1. 创建新的 Fetcher 类：

```python
# asset_lens/data/fetchers/new_source.py
from .base import BaseFetcher, FetchResult

class NewSourceFetcher(BaseFetcher):
    def fetch(self, symbol: str, **kwargs) -> FetchResult:
        # 实现数据获取逻辑
        pass
    
    def fetch_batch(self, symbols: List[str], **kwargs) -> Dict[str, FetchResult]:
        # 实现批量获取逻辑
        pass
```

2. 注册到 UnifiedFetcher：

```python
# asset_lens/data/unified_fetcher.py
from .fetchers.new_source import NewSourceFetcher

class UnifiedFetcher:
    def __init__(self):
        self.new_source = NewSourceFetcher()
```

### 2. 添加新的分析指标

**步骤**：

1. 在 `core/portfolio_analytics.py` 添加计算函数：

```python
def calculate_new_metric(self, data: pd.DataFrame) -> float:
    """计算新指标"""
    # 实现计算逻辑
    return result
```

2. 在 CLI 中添加命令：

```python
# asset_lens/cli_modules/analysis.py
@cli.command()
def new_metric():
    """计算新指标"""
    result = calculator.calculate_new_metric(data)
    click.echo(f"新指标: {result}")
```

### 3. 添加新的报告格式

**步骤**：

1. 创建新的报告生成器：

```python
# asset_lens/report/new_format_generator.py
class NewFormatGenerator:
    def generate(self, data: Dict) -> str:
        """生成新格式报告"""
        pass
```

2. 集成到 ReportGenerator：

```python
# asset_lens/report/report_generator.py
from .new_format_generator import NewFormatGenerator

class ReportGenerator:
    def __init__(self):
        self.new_format = NewFormatGenerator()
```

---

## 架构健康度

### 当前状态

| 维度 | 得分 | 评价 |
|------|------|------|
| 模块内聚度 | 85/100 | Data 层有改进空间 |
| 依赖解耦 | 80/100 | 配置中心模式良好 |
| 流程复杂度 | 88/100 | 最大深度 7 步 |
| 测试覆盖 | 90/100 | 测试内聚度 1.0 |
| 代码规模 | 75/100 | 部分类过大 |

### 改进路线

**短期（1-2周）**：
- 重构 Data 层（内聚度 0.50 → 0.75+）
- 拆分大型类（ReportGenerator, AIAnalyzer）

**中期（1个月）**：
- 完善架构文档
- 优化执行流程

**长期（持续）**：
- 保持测试覆盖
- 监控架构健康度

---

## 参考资料

- [GitNexus 分析报告](./GITNEXUS_ANALYSIS_REPORT.md)
- [README](./README.md)
- [投资分析方法论](../ts-demo/docs/01-Investment/)
