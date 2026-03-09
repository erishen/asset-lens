# Asset Lens 快速入门指南

## 🚀 5 分钟快速上手

### 第一步：初始化项目

```bash
# 查看帮助
make help

# 检查项目状态
make check

# 显示当前配置
make show-config
```

### 第二步：更新市场数据

```bash
# 快速更新市场数据（推荐）
make daily

# 或者手动更新
make update-market-data-fast
```

### 第三步：查看投资组合

```bash
# 分析投资组合
make analyze

# 计算收益
make calculate

# 查看盈亏
make pnl
```

---

## 📊 常用功能速查

### 1. 每日必做

```bash
# 一键完成：更新数据 + 估算盈亏
make daily
```

### 2. 查看股票行情

```bash
# 查询单只股票
make fetch-stock CODES="sh600519"

# 查询多只股票
make fetch-stock CODES="sh600519 sz000001 sh000001"
```

### 3. 查看基金净值

```bash
# 查询单只基金
make fetch-fund CODES="000001"

# 搜索基金
make search-fund KEYWORD="沪深300"
```

### 4. 股票筛选

```bash
# 综合筛选（推荐）
make screen-stocks

# 仅基本面筛选
make screen-fundamental

# 仅技术面筛选
make screen-technical
```

### 5. 生成周报

```bash
# 一键生成周报
make weekly
```

---

## 📈 投资策略系统

### 快速开始

```bash
# 1. 查看可用策略
make strategy-list

# 2. 使用策略筛选股票
make strategy-screen NAME=momentum

# 3. 查看股票池
make stock-pool-list
```

### 策略回测

```bash
# 动量策略回测
make backtest-momentum

# 价值策略回测
make backtest-value
```

---

## 🌐 Web 界面

```bash
# 启动 Web Dashboard
make web

# 然后打开浏览器访问
# http://localhost:8000
```

---

## 🔧 常见问题

### Q: 命令执行失败怎么办？

```bash
# 1. 检查项目状态
make check

# 2. 检查配置
make show-config

# 3. 查看帮助
make help
```

### Q: 数据获取失败？

```bash
# 确保网络连接正常
# 尝试重新获取数据
make update-market-data-fast
```

### Q: 如何切换数据模式？

```bash
# 切换到示例模式
make mode-sample

# 切换到真实模式
make mode-real
```

---

## 📚 更多帮助

- 查看 Makefile 了解所有可用命令
- 运行 `make help` 查看帮助
- 查看 README.md 了解详细信息
