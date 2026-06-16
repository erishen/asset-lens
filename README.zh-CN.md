# asset-lens

> 基于 Python 的个人资产操作系统。

---

## 🚀 快速开始

```bash
# 1. 安装
make setup

# 2. 每日数据更新与盈亏估算
make daily

# 3. 查看分析报告
make analyze
```

---

## 安装

### 前置要求

- Python 3.9+
- conda（推荐）或 pip

### 1. 克隆并安装

```bash
git clone https://github.com/erishen/asset-lens.git
cd asset-lens

# 使用 conda（推荐）
make setup

# 使用 pip
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m asset_lens system init
```

**验证:**
```bash
python -m asset_lens --version
```

### 2. 日常使用

```bash
make daily
```

### 3. 查看分析

```bash
make analyze           # 投资组合分析
make ai-analyze        # AI 分析（需 API Key）
make weekly            # 周报
```

---

## 项目结构

```
asset-lens/
├── asset_lens/          # Python 模块
│   ├── cli.py           # CLI 入口
│   ├── core/            # 核心计算
│   ├── data/            # 数据获取与处理
│   ├── ml/              # 机器学习模型
│   ├── strategy/        # 投资策略
│   └── analysis/        # 投资组合分析
├── scripts/             # 工具脚本（安全子集）
├── config/              # 配置文件
├── tests/               # 测试套件
└── Makefile             # 命令入口
```

---

## 核心命令

| 命令 | 说明 | 频率 |
|------|------|------|
| `make setup` | 完整安装 | 一次 |
| `make daily` | 数据更新 + 盈亏估算 | 每日 |
| `make analyze` | 投资组合分析 | 按需 |
| `make weekly` | 周报 | 每周 |
| `make ai-analyze` | AI 深度分析 | 按需 |
| `make ml-train-db` | 训练 ML 模型 | 每周 |
| `make ml-predict` | ML 预测 | 按需 |
| `make test` | 运行测试 | 开发 |
| `make lint` | 代码检查 | 开发 |

---

## 数据模式

| 模式 | 说明 | 用途 |
|------|------|------|
| `sample` | 匿名演示数据 | Demo、测试、开源 |
| `real` | 个人投资数据 | 日常个人使用 |

```bash
make mode-sample    # 切换到示例模式
make mode-real      # 切换到真实模式
```

真实数据路径已通过 `.gitignore` 排除，不会被追踪。

---

## 配置

### 环境变量

编辑 `.env` 文件：

```bash
# 数据模式
DATA_MODE=sample

# API Key（可选，用于实时行情）
ALPHAVANTAGE_API_KEY=your_key
FINNHUB_API_KEY=your_key

# AI 分析（可选）
OPENAI_API_KEY=your_key
```

### 配置文件

配置文件使用 `.example` 模板——复制并去掉 `.example` 后缀后自定义。

---

## 技术栈

- **Python 3.10+**
- **pandas / numpy** — 数据处理
- **click** — CLI 框架
- **rich** — 格式化输出
- **LightGBM / XGBoost** — 机器学习
- **scikit-learn** — 模型工具
- **openai** — AI 分析（可选）
- **FastAPI** — Web API（可选）

---

## 免责声明

本项目仅用于个人学习和投资研究，**不构成任何投资建议**。

---

## License

MIT License
