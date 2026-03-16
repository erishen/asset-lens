# Asset-Lens 项目优化分享

> 从代码问题修复到工程化提升的完整实践

---

## 📋 项目背景

Asset-Lens 是一个个人资产分析系统，提供投资组合分析、股票基金查询、策略筛选、自动化监控等功能。本次优化主要解决了代码问题和工程化缺陷。

---

## 🔍 问题发现

通过代码审查，发现了以下问题：

### 1. 代码逻辑问题

| 问题 | 文件 | 影响 |
|------|------|------|
| `min_score/min_pass_rate` 用 `or` 判断会覆盖 0 值 | `stock_pool_builder.py` | 筛选条件失效 |
| `execute_buy` 缺少 `price <= 0` 校验 | `strategy_simulator.py` | 可能买入无效价格 |
| `min_holding_days` 未使用 | `strategy_simulator.py` | 功能缺失 |
| `FilterCondition.evaluate` 数值转换异常 | `stock_pool_builder.py` | 运行时错误 |
| `contribution_pct` 命名误导 | `strategy_evaluator.py` | 语义不清晰 |
| `min_holding_days` 在 rebalance 卖出时不生效 | `strategy_simulator.py` | 功能缺陷 |
| 多次运行状态污染 | `strategy_simulator.py` | 结果不准确 |

### 2. 工程化问题

| 问题 | 影响 |
|------|------|
| 大文件 (>1000行) | 难以维护 |
| 缺少 CI/CD | 代码质量无保障 |
| 缺少 pre-commit | 提交前无检查 |
| 测试速度慢 | 开发效率低 |

---

## 🛠️ 解决方案

### 一、代码问题修复

#### 1. 条件判断修复

```python
# 修复前
min_score = config.min_score or 60  # 如果 min_score=0 会被覆盖

# 修复后
min_score = config.min_score if config.min_score is not None else 60
```

#### 2. 价格校验添加

```python
def execute_buy(self, code: str, price: float, ...):
    if price <= 0:
        return None  # 添加提前返回
```

#### 3. 最小持有天数实现

```python
def can_sell_position(self, code: str, date: str, reason: str) -> bool:
    """检查是否可以卖出持仓（考虑最小持有天数）"""
    if reason in ("stop_loss", "take_profit", "max_holding"):
        return True  # 止盈止损和最大持有期不受限制
    
    holding_days = (current - entry).days
    return holding_days >= self.config.min_holding_days
```

#### 4. 状态重置

```python
def run_simulation(self, ...):
    # 重置状态，避免多次运行污染
    self.positions = {}
    self.trades = []
    self.daily_values = []
    self.cash = self.config.initial_capital
    self.last_rebalance_date = None
```

---

### 二、大文件拆分

#### 1. web/api.py (1277行) → 4 个路由模块

```
web/api.py
├── web/routes/stock.py      # 股票相关 API (~180行)
├── web/routes/portfolio.py  # 投资组合 API (~160行)
├── web/routes/strategy.py   # 策略相关 API (~120行)
└── web/routes/market.py     # 市场数据 API (~180行)
```

#### 2. report/analyzer.py (1082行) → 3 个分析模块

```
report/analyzer.py
├── report/summary.py        # 投资组合摘要 (~185行)
├── report/risk_analysis.py  # 风险分析 (~115行)
└── report/performance.py    # 绩效分析 (~160行)
```

#### 3. data/csv_parser.py (940行) → 3 个解析器模块

```
data/csv_parser.py
├── data/parsers/field_parsers.py   # 字段解析器 (~110行)
├── data/parsers/product_parser.py  # 产品解析器 (~140行)
└── data/parsers/csv_loader.py      # CSV 加载器 (~70行)
```

---

### 三、工程化提升

#### 1. pyproject.toml 现代化配置

```toml
[project]
name = "asset-lens"
version = "1.0.0"
requires-python = ">=3.10"

[project.optional-dependencies]
dev = ["pytest", "pylint", "mypy", "black"]
ai = ["litellm"]
web = ["fastapi", "uvicorn"]

[tool.ruff]
line-length = 120
select = ["E", "W", "F", "I", "B", "C4", "UP"]
```

#### 2. GitHub Actions CI/CD

```yaml
jobs:
  lint:
    - pylint
    - mypy
  test:
    - Python 3.10/3.11/3.12
    - pytest -n auto
  build:
    - python -m build
```

#### 3. pre-commit 钩子

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

---

## 📊 优化效果

### 代码质量

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| Lint 分值 | 10.00/10 | 10.00/10 |
| mypy 检查 | 通过 | 通过 |
| 测试用例 | 1675 | 1675 |
| 测试时间 | 191s | **44s** |

### 工程化

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 大文件数 (>1000行) | 3 | **0** |
| CI/CD | 无 | **GitHub Actions** |
| pre-commit | 无 | **完整配置** |
| 配置文件 | requirements.txt | **pyproject.toml** |

---

## 💡 经验总结

### 1. 代码审查要点

- **边界条件**: 检查 `or`、`and` 等逻辑运算符是否会覆盖有效值
- **输入校验**: 所有关键函数都应有输入参数校验
- **状态管理**: 有状态的服务类需要在入口处重置状态
- **命名规范**: 变量名应准确反映其含义

### 2. 大文件拆分策略

- **按功能拆分**: 相关功能聚合，不相关功能分离
- **保持接口**: 原有公开 API 保持不变
- **渐进式重构**: 先拆分，后优化

### 3. 工程化最佳实践

- **pyproject.toml**: 统一项目配置
- **CI/CD**: 自动化质量保障
- **pre-commit**: 提交前检查
- **并行测试**: pytest-xdist 加速

---

## 🎯 后续建议

1. **继续拆分**: 还有 6 个文件超过 500 行
2. **API 文档**: 使用 Sphinx/MkDocs 生成文档
3. **覆盖率报告**: 集成 codecov
4. **性能优化**: 考虑使用 polars 替代 pandas

---

## 📚 参考资料

- [Python 项目现代配置](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [pre-commit 框架](https://pre-commit.com/)
- [ruff linter](https://docs.astral.sh/ruff/)

---

*分享时间: 2026-03-16*
