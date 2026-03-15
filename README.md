# asset-lens

> 一个以 Python 为核心构建的个人资产操作系统
> A personal asset operating system built with Python.

---

## 🚀 3 步快速开始

```bash
# 1️⃣ 安装
make setup

# 2️⃣ 每日更新数据
make daily

# 3️⃣ 查看分析报告
make analyze
```

**就这么简单！** 3 步即可完成从安装到使用的全流程。

---

## 📋 详细安装步骤

### 前置要求

- Python 3.9+ 
- conda 或 pip

### 步骤 1: 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/asset-lens.git
cd asset-lens

# 安装（推荐使用 conda）
make setup

# 或手动安装
pip install -r requirements.txt
python -m asset_lens system init
```

**验证安装**:
```bash
python -m asset_lens --version
# 输出: Asset-Lens v1.0.0
```

### 步骤 2: 每日使用

```bash
# 更新市场数据 + 估算盈亏
make daily

# 等同于:
# python -m asset_lens update-market-data
# python -m asset_lens pnl
```

### 步骤 3: 查看分析

```bash
# 投资组合分析
make analyze

# AI 分析（需配置 API Key）
make ai-analyze

# 生成周报
make weekly
```

---

## 📁 项目结构

```
asset-lens/
├── asset_lens/          # Python 模块
│   ├── cli.py           # CLI 入口
│   ├── core/            # 核心计算
│   ├── data/            # 数据模块
│   └── utils/           # 工具模块
├── scripts/
│   ├── openclaw/        # OpenClaw 监控脚本
│   └── shell/           # Shell 脚本
├── config/              # 配置文件
├── docs/                # 文档
├── openclaw/            # OpenClaw 技能
├── tests/               # 测试文件
└── Makefile             # 命令入口
```

---

## 🎯 核心命令速查

| 命令 | 说明 | 频率 |
|------|------|------|
| `make setup` | 初始化安装 | 一次性 |
| `make daily` | 更新数据 + 盈亏估算 | 每日 |
| `make analyze` | 投资组合分析 | 按需 |
| `make weekly` | 生成周报 | 每周 |
| `make ai-analyze` | AI 深度分析 | 按需 |
| `make test` | 运行测试 | 开发时 |
| `make lint` | 代码检查 | 开发时 |
| `make clean` | 清理输出 | 按需 |

---

## 📋 数据模式

asset-lens 支持两种数据模式，确保隐私安全：

| 模式 | 说明 | 用途 |
|------|------|------|
| `sample` | 脱敏模拟数据 | 演示、测试、开源分享 |
| `real` | 真实投资数据 | 个人日常使用 |

```bash
# 切换数据模式
make mode-sample    # 切换到 sample 模式
make mode-real      # 切换到 real 模式
make show-config    # 显示当前配置
```

**重要**: 真实数据路径已在 `.gitignore` 中配置，不会被 Git 追踪。

---

## 🔧 配置

### 环境变量

编辑 `.env` 文件：

```bash
# 数据模式
DATA_MODE=sample

# API Keys（可选，用于获取实时市场数据）
ALPHAVANTAGE_API_KEY=your_key
FINNHUB_API_KEY=your_key

# AI 分析（可选）
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

### 配置文件

| 文件 | 说明 |
|------|------|
| `config/platforms.json` | 投资平台配置 |
| `config/investment_types.json` | 投资品种配置 |

---

## 📖 高级功能

<details>
<summary>点击展开高级功能列表</summary>

### 策略筛选

```bash
# 动量策略筛选
make momentum-screen

# 价值策略筛选
make value-screen

# 红利策略筛选
make dividend-screen
```

### 股票池管理

```bash
# 查看股票池
make stock-pool-list

# 模拟买入
python -m asset_lens stock-pool buy --code sh600519 --reason "突破均线"

# 模拟卖出
python -m asset_lens stock-pool sell --code sh600519 --reason "止盈"
```

### 自动交易

```bash
# 交易报告
make auto-trade-report

# 交易评价
make auto-trade-evaluate
```

### Web 界面

```bash
# 启动 Web 服务
make web

# 访问 http://localhost:8000
```

</details>

---

## 📊 输出示例

```
============================================================
投资收益率分析报告 (SAMPLE 模式)
生成时间: 2026-03-15 10:00:00
============================================================

📊 投资组合概览
  产品总数: 20
  总资产: ¥256,680
  初始投资: ¥245,500
  总收益: ¥11,180
  整体收益率: 4.56%

🏆 收益率排名 Top 5
  1. 中证500ETF: IRR年化 49.30%
  2. 纳斯达克100: IRR年化 60.80%
  ...

⚠️ 风险提示
  • 发现 5 个收益率低于 2.0% 的产品
```

---

## 🧠 技术栈

- **Python 3.10+**
- **pandas / numpy** - 数据处理
- **click** - CLI 框架
- **rich** - 美化输出
- **openai** - AI 分析（可选）

---

## 📚 文档

- [快速开始指南](docs/guides/QUICKSTART.md)
- [CLI 命令参考](docs/guides/CLI_REFERENCE.md)
- [系统架构](docs/architecture/ARCHITECTURE.md)
- [OpenClaw 技能](openclaw/skill/SKILL.md)

---

## 🗺 演进路线

| 阶段 | 状态 | 内容 |
|------|------|------|
| 阶段一 | ✅ | 资产数据模型与收益分析框架 |
| 阶段二 | ✅ | 股票/基金筛选、实时数据、AI 分析 |
| 阶段三 | 🚧 | Web 化、数据可视化、PDF 报告 |
| 阶段四 | 📋 | 机器学习、AI 建议增强 |

---

## ⚠ 声明

本项目仅用于个人学习与资产分析研究，不构成任何投资建议。

---

## 📄 许可证

MIT License
