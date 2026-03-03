# asset-lens

> 一个以 Python 为核心构建的个人资产操作系统
> A personal asset operating system built with Python.

---

## 📌 项目背景

asset-lens 起初只是一个用于记录每周投资收益的简单脚本。

在持续记录银行、基金、股票资产数据的过程中，逐渐意识到：

- 手动统计效率低
- 缺乏结构化分析
- 投资行为难以复盘
- 无法系统验证定投策略效果

因此，将零散的 TypeScript / Python 脚本重构为一个长期演进的资产分析系统。

本项目既是个人投资工具，也是一个工程与数据能力的长期实践项目。

---

## 🎯 项目定位

asset-lens 不是量化交易系统，也不是自动下单平台。

它是：

- 个人资产数据管理系统
- 收益与风险分析工具
- 投资行为复盘工具
- 策略验证实验平台
- AI 辅助分析框架

目标是构建一个结构清晰、可扩展、可长期演进的资产操作系统。

---

## 📋 数据模式（隐私保护）

asset-lens 支持两种数据模式，确保隐私安全：

### Sample 模式（示例数据）
- 使用脱敏的模拟数据进行演示和测试
- 所有金额和敏感信息都是模拟值
- 代码可以安全地对外展示和分享
- 适合学习、演示和开源

### Real 模式（真实数据）
- 使用真实的个人投资数据
- 数据保存在本地，不会提交到代码仓库
- 私人数据严格保密
- 适合个人日常使用

**重要**: 真实数据路径（`data/real/`）已在 `.gitignore` 中配置，不会被 Git 追踪。

---

## 🧱 当前功能（v1）

### 基础功能
- ✅ 资产交易记录管理（CSV）
- ✅ 年化收益率计算
- ✅ IRR（内部收益率）计算
- ✅ 最大回撤分析
- ✅ 波动率统计
- ✅ 定投策略（DCA）模拟 - 支持4种模式
- ✅ 周度收益报告生成
- ✅ 多币种支持（USD/HKD 转 CNY）
- ✅ 资产汇总数据管理（资产汇总.csv / 资产汇总-表格 1.csv）
- ✅ 卖出记录管理（卖出记录.csv / 卖出记录-表格 1.csv）

### 高级分析功能
- ✅ **实时盈亏估算** - 基于市场指数的日/周盈亏估算
  - 产品-指数智能映射
  - 风险等级敏感度调整
  - 支持A股、美股、黄金等多种指数
- ✅ **对比分析** - 两期投资对比和趋势分析
  - 任意两期投资对比
  - 按投资类型统计分析
  - 资金流动分析
- ✅ **已卖出投资分析** - 已实现收益详细分析
  - 总体收益统计
  - 按风险等级分组
  - 年化收益率计算
- ✅ **按投资时间分组分析** - 短期/中期/长期投资分组
  - 按持有时间分组
  - 按投资起始年份分组
  - 分组收益统计

### AI 分析功能（新增）
- ✅ **AI 投资分析** - 使用 DeepSeek/OpenAI API 进行深度分析
  - 投资摘要生成
  - 风险评估
  - 投资建议生成
  - 风险警告
  - 综合评分（0-100 分）
  - 推荐资产配置（保守型/平衡型/激进型）
  - 缓存机制（默认 1 小时）

### 投资组合专业指标（新增）
- ✅ **业绩指标**
  - 总收益率、年化收益率
  - 波动率（年化）
  - 夏普比率、索提诺比率
  - 最大回撤、卡玛比率
  - 胜率、盈亏比
- ✅ **风险指标**
  - VaR (95%, 99%)
  - CVaR（预期亏损）
  - Beta 系数
  - 跟踪误差、信息比率

### 开发工具（新增）
- ✅ **日志系统** - 彩色输出、敏感信息过滤、文件日志支持
- ✅ **进度条工具** - ProgressBar、Spinner、TaskProgress
- ✅ **pre-commit hooks** - black、isort、flake8、mypy 配置
- ✅ **GitHub Actions CI/CD** - 自动测试、代码检查、构建发布

---

## 🏗 项目结构

```
asset-lens/
├── asset_lens/
│   ├── __init__.py           # 主入口
│   ├── __main__.py           # CLI 入口
│   ├── cli.py                # 命令行接口
│   ├── config.py             # 配置管理
│   ├── data/                 # 数据模块
│   │   ├── models.py         # 数据模型
│   │   ├── csv_parser.py     # CSV 解析器
│   │   ├── asset_summary_parser.py  # 资产汇总解析器
│   │   ├── exchange_rate_parser.py  # 汇率历史解析器
│   │   ├── sell_record_parser.py    # 卖出记录解析器
│   │   ├── market_data_fetcher.py   # 市场数据获取
│   │   └── market_index.py          # 市场指数模型
│   ├── core/                 # 核心计算
│   │   ├── irr_calculator.py # IRR 计算
│   │   ├── dca_parser.py     # 定投策略解析
│   │   ├── ai_analyzer.py    # AI 分析模块
│   │   ├── portfolio_analytics.py  # 投资组合专业指标
│   │   ├── advanced_analytics.py   # 高级分析
│   │   ├── realtime_pnl.py   # 实时盈亏估算
│   │   ├── cache_manager.py  # 缓存管理
│   │   ├── config_validator.py     # 配置验证
│   │   └── exceptions.py     # 自定义异常
│   ├── utils/                # 工具模块
│   │   ├── currency_converter.py  # 货币转换
│   │   ├── logger.py         # 日志系统
│   │   └── progress.py       # 进度条工具
│   └── report/               # 报告生成
│       └── analyzer.py       # 分析报告
├── data/
│   ├── sample_data/           # 示例数据（可提交）
│   │   ├── 投资产品.csv
│   │   ├── 资产汇总.csv
│   │   └── 卖出记录.csv
│   └── real/                 # 真实数据（不提交）
│       └── money_csv_20260301/
│           ├── 投资产品-表格 1.csv
│           ├── 资产汇总-表格 1.csv
│           └── 卖出记录-表格 1.csv
├── tests/                    # 测试文件
├── output/                   # 输出文件
├── cache/                    # 缓存文件
├── .github/workflows/        # GitHub Actions
├── requirements.txt          # Python 依赖
├── .env.example             # 配置示例
├── .pre-commit-config.yaml  # pre-commit 配置
└── README.md                # 项目说明
```

设计原则：

- 模块化
- 低耦合
- 可扩展
- 长期维护

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖（可选）
pip install -r requirements.txt pytest pytest-cov black isort flake8 mypy pre-commit
```

### 2. 初始化项目

```bash
# 创建必要的目录和配置文件
python -m asset_lens init

# 初始化示例数据（可选）
python -m asset_lens init-sample
```

### 3. 配置环境

编辑 `.env` 文件：

```bash
# 数据模式选择
# sample: 使用示例数据（适合演示和测试）
# real: 使用真实数据（私人数据，不会提交到代码仓库）
DATA_MODE=sample

# API Keys (用于获取实时市场数据)
FINNHUB_API_KEY=your_actual_finnhub_api_key_here

# AI 分析配置（可选）
# 支持 OpenAI 兼容 API（如 DeepSeek、通义千问等）
# OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_BASE_URL=https://api.deepseek.com
# OPENAI_MODEL=deepseek-chat

# AI 缓存配置
AI_CACHE_TTL=3600  # 缓存有效期（秒），默认 1 小时
```

### 4. 配置投资平台和品种（可选）

asset-lens 支持动态配置投资平台和品种，你可以根据自己的实际情况自定义。

#### 4.1 复制示例配置文件

```bash
# 复制平台配置示例文件
cp config/platforms.json.example config/platforms.json

# 复制投资品种配置示例文件
cp config/investment_types.json.example config/investment_types.json
```

#### 4.2 编辑配置文件

**config/platforms.json** - 配置你的投资平台：

```json
{
    "platforms": [
        {
            "id": "wechat",
            "name": "微信",
            "field": "wechat_amount",
            "type": "third_party",
            "description": "微信理财"
        },
        {
            "id": "alipay",
            "name": "支付宝",
            "field": "alipay_amount",
            "type": "third_party",
            "description": "支付宝理财"
        },
        {
            "id": "cmb",
            "name": "招商银行",
            "field": "cmb_amount",
            "type": "bank",
            "description": "招商银行理财"
        }
    ],
    "platform_types": {
        "third_party": "第三方平台",
        "bank": "银行",
        "securities": "证券"
    }
}
```

**config/investment_types.json** - 配置投资品种：

```json
{
    "types": [
        {"id": "stock", "name": "股票"},
        {"id": "fund", "name": "基金"},
        {"id": "bond", "name": "债券"},
        {"id": "monetary", "name": "货币"}
    ]
}
```

#### 4.3 配置文件说明

- `config/platforms.json` 和 `config/investment_types.json` 不会被 Git 追踪
- 如果没有创建配置文件，系统会使用默认配置
- 配置文件修改后需要重新运行分析命令才能生效

### 5. 运行分析

```bash
# 使用示例数据进行分析
python -m asset_lens analyze --data-mode sample

# 或使用真实数据
python -m asset_lens analyze --data-mode real

# 只输出控制台报告
python -m asset_lens analyze --data-mode sample --output-format console

# 输出所有格式
python -m asset_lens analyze --data-mode sample --output-format all
```

### 6. AI 分析（新功能）

```bash
# AI 分析投资组合（需要配置 OPENAI_API_KEY）
python -m asset_lens ai-analyze

# 指定风险偏好
python -m asset_lens ai-analyze --risk-preference conservative  # 保守型
python -m asset_lens ai-analyze --risk-preference balanced      # 平衡型（默认）
python -m asset_lens ai-analyze --risk-preference aggressive    # 激进型

# 使用 Makefile 命令
make ai-analyze
```

### 7. 投资组合专业指标（新功能）

```bash
# 计算投资组合专业指标
python -m asset_lens portfolio-metrics

# 使用 Makefile 命令
make portfolio-metrics
```

### 8. 其他常用命令

```bash
# 查看资产汇总
python -m asset_lens show-asset-summary --data-mode real

# 查看汇率历史
python -m asset_lens show-exchange-rate-history --data-mode real

# 查看卖出记录
python -m asset_lens show-sell-records --data-mode real

# 实时盈亏估算
python -m asset_lens estimate-pnl

# 已卖出投资分析
python -m asset_lens analyze-sold

# 按投资时间分组分析
python -m asset_lens analyze-by-time

# 更新市场指数数据
python -m asset_lens update-market-data
```

---

## 🛠️ 使用 Makefile

asset-lens 提供了 Makefile 来简化常用命令的执行。只需运行 `make help` 即可查看所有可用命令。

### 快速开始

```bash
# 查看所有可用命令
make help

# 检查项目状态
make check

# 安装依赖
make install

# 初始化项目
make init

# 运行分析（使用示例数据）
make analyze
```

### 常用命令

#### 环境管理

```bash
make env-create     # 创建 conda 环境 asset-lens
make env-list       # 列出所有 conda 环境
make env-remove     # 删除 conda 环境 asset-lens
```

#### 依赖管理

```bash
make install        # 安装项目依赖
make install-dev    # 安装开发依赖
make update         # 更新项目依赖
make list-pkgs      # 列出已安装的包
```

#### 项目运行

```bash
make analyze        # 分析投资组合 (sample 模式)
make analyze-real   # 分析投资组合 (real 模式)
make calculate      # 快捷计算收益率
make calculate-real # 快捷计算收益率 (real 模式)
make weekly         # 生成周度报告
make ai-analyze     # AI 分析投资组合
make portfolio-metrics  # 计算投资组合专业指标
```

#### 数据模式切换

```bash
make mode-sample    # 切换到 sample 模式
make mode-real      # 切换到 real 模式
make show-config    # 显示当前配置
```

#### 测试和代码质量

```bash
make test           # 运行测试
make test-cov       # 运行测试并生成覆盖率报告
make lint           # 运行代码检查
make format         # 格式化代码
make ci             # 完整 CI 流程（格式化+检查+测试）
```

#### 清理命令

```bash
make clean          # 清理输出文件
make clean-cache    # 清理缓存文件
make clean-all      # 清理所有生成的文件
```

#### 快捷命令

```bash
make run            # 快捷运行分析（等同于 make analyze）
make demo           # 初始化并运行示例
make dev            # 开发流程：安装依赖、格式化、检查、测试
make quick          # 快速查看：更新数据+估算盈亏
```

**注意**: Makefile 使用 conda 环境 `asset-lens` 运行命令。如果环境不存在，请先运行 `make env-create`。

---

## 💡 使用示例

### 基础命令

```bash
# 分析投资组合
python -m asset_lens analyze

# 快捷计算命令
python -m asset_lens calculate

# 生成周度报告
python -m asset_lens weekly-report

# 查看当前配置
python -m asset_lens show-config

# 切换数据模式
python -m asset_lens switch-mode --target-mode real
```

### AI 分析示例

```bash
# AI 分析（需要配置 OPENAI_API_KEY）
make ai-analyze

# 输出示例：
# ╭──────────────────────────────── 📋 投资摘要 ─────────────────────────────────╮
# │ 该投资组合总市值约32.8万元，累计收益6.1万元，整体收益率22.8%，表现良好。   │
# ╰──────────────────────────────────────────────────────────────────────────────╯
# 
# ╭──────────────────────────────── 📊 综合评分 ─────────────────────────────────╮
# │ 综合评分: 78 分 (良好)                                                       │
# ╰──────────────────────────────────────────────────────────────────────────────╯
# 
# 💡 投资建议:
#   1. 优化低效资产：建议逐步赎回或转换年化收益率为0的产品
#   2. 调整权益类结构：适度增加A股核心宽基指数基金配置
#   3. 加强资产再平衡：定期检查组合风险分布
```

### 投资组合专业指标示例

```bash
# 计算专业指标
make portfolio-metrics

# 输出示例：
# 📈 业绩指标
# ┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
# ┃ 指标           ┃       值 ┃
# ┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
# │ 总收益率       │   5.42%  │
# │ 年化收益率     │   4.89%  │
# │ 波动率（年化） │  12.35%  │
# │ 夏普比率       │    0.35  │
# │ 最大回撤       │   8.72%  │
# │ 胜率           │   56.2%  │
# │ 盈亏比         │    1.23  │
# │ 卡玛比率       │    0.56  │
# │ 索提诺比率     │    0.48  │
# └────────────────┴──────────┘
```

### 定投策略格式

asset-lens 支持 4 种定投模式：

1. **固定金额定投**:
   ```
   2024/1/15-now:buy:200
   ```

2. **智能区间定投**:
   ```
   2024/2/1-now:buy:100~300
   ```

3. **浮动金额定投**:
   ```
   2024/7/1-now:buy:150±50
   ```

4. **估值模式定投**:
   ```
   2024/3/15-now:buy:80-200-400
   ```

5. **分阶段定投**:
   ```
   2024/1/1-2024/6/30:buy:100;2024/7/1-now:buy:150±50
   ```

6. **暂停定投**:
   ```
   2024/1/15-now:buy:200; 2024/2/10-2024/2/15:stop
   ```

### 定投产品收益率计算

定投产品的收益率计算采用以下方式：

1. **收益率计算**：
   ```
   收益率 = (当前金额 - 初始金额) / 初始金额 × 100%
   ```

2. **年化收益率计算**：使用 IRR（内部收益率）计算
   - 现金流：`[-初始金额, 当前金额]`
   - 使用 `days360` 计算投资天数

3. **说明**：
   - 定投产品使用 CSV 中的 `初始金额` 作为净投入
   - 不再根据交易记录计算工作日和定投金额
   - 简化了计算逻辑，与 CSV 数据保持一致

### 智能定投格式说明

智能定投格式 `金额~天数`（如 `30~105`）表示：
- 每日定投金额根据市场情况在 `30` 到 `105` 之间浮动
- 系统不会自动计算定投金额，而是使用 CSV 中的初始金额作为净投入

---

## 📊 输出示例

### 控制台报告

```
============================================================
投资收益率分析报告 (SAMPLE 模式)
生成时间: 2026-02-28 10:00:00
============================================================

📊 投资组合概览
  产品总数: 20
  总资产: ¥256,680
  初始投资: ¥245,500
  总收益: ¥11,180
  整体收益率: 4.56%

🏆 收益率排名 Top 10
  1. 中证500ETF (指数基金)
     IRR年化: 49.30% | 当前金额: ¥25000
  2. 纳斯达克100 (指数基金)
     IRR年化: 60.80% | 当前金额: ¥18000
  ...

⚠️  风险提示
  • 发现 5 个收益率低于 2.0% 的产品（低于银行定期）
    - 嘉实稳祥纯债债券C: 年化 1.99%, 金额 5029元
    - 东方红配置精选混合C: 年化 1.98%, 金额 20164元
  • 发现 2 个严重亏损产品
    - 易方达上证科创板芯片ETF联接A: -6.85%
```

### CSV 文件

输出文件位于 `output/投资收益率分析_YYYYMMDD.csv`，包含以下字段：

- 投资类型
- 名称
- 风险等级
- 当前金额
- 初始金额
- 投资天数
- IRR年化收益率
- 平台
- 交易记录

---

## 🧠 技术栈

- **Python 3.10+**
- **pandas / numpy** - 数据处理
- **scipy** - IRR 计算
- **click** - CLI 框架
- **rich** - 美化控制台输出
- **pydantic** - 数据验证
- **python-dotenv** - 环境变量管理
- **openai** - AI 分析（可选）

---

## 🗺 演进路线

### 阶段一 ✅

- ✅ 构建稳定的资产数据模型与收益分析框架
- ✅ 支持 4 种定投策略
- ✅ 多币种支持

### 阶段二 ✅

- ✅ 加入股票 / 基金筛选与简单策略验证
- ✅ 实时市场数据获取
- ✅ 最大回撤和波动率计算
- ✅ AI 投资分析模块
- ✅ 投资组合专业指标

### 阶段三 🚧

- 🚧 Web 化与 API 化，形成完整系统结构
- 🚧 数据可视化图表
- 🚧 导出 PDF 报告

### 阶段四 📋

- 📋 引入基础机器学习模型，用于风险评分与策略辅助判断
- 📋 AI 投资建议系统增强

---

## 📊 项目意义

这个项目是一个长期实践项目，用于：

* 提升金融数据建模能力
* 强化工程结构设计能力
* 练习策略验证逻辑
* 探索 AI 在投资复盘中的应用
* 构建个人资产决策支持系统

---

## ⚠ 声明

本项目仅用于个人学习与资产分析研究，不构成任何投资建议。

---

## 📝 开发指南

### 添加新功能

1. 在相应的模块中添加功能
2. 在 CLI 中添加新命令
3. 更新 README 文档
4. 添加测试用例

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_ai_analyzer.py

# 运行测试并生成覆盖率报告
pytest --cov=asset_lens tests/
```

### 代码格式化

```bash
# 格式化代码
black asset_lens/
isort asset_lens/

# 运行代码检查
flake8 asset_lens/
mypy asset_lens/ --ignore-missing-imports
```

### pre-commit

```bash
# 安装 pre-commit hooks
pre-commit install

# 手动运行所有 hooks
pre-commit run --all-files
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 🔗 相关链接

- [ts-demo](../ts-demo/) - TypeScript 版本的实现
- [投资分析方法论](../ts-demo/docs/01-Investment/) - 投资分析相关文档
- [ai-analyze](../ai-analyze/) - AI 分析项目

---

## 📈 项目统计

- **测试用例**: 349 个
- **测试覆盖率**: 42%
- **代码行数**: ~5000 行
- **模块数量**: 20+ 个

---

**开发者**: [Your Name]
**开始时间**: 2024
**最后更新**: 2026-02-28
