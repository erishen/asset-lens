# asset-lens TODO List

> 最后更新: 2026-02-28

---

## 🔴 高优先级 (High Priority)

### 1. 代码质量

- [x] **添加单元测试** ✅ 已完成
  - [x] `irr_calculator.py` 测试覆盖 (76%)
  - [x] `realtime_pnl.py` 测试覆盖 (86%)
  - [x] `csv_parser.py` 测试覆盖 (67%)
  - [x] `advanced_analytics.py` 测试覆盖 (82%)
  - [x] `exceptions.py` 测试覆盖 (100%)
  - [x] `cache_manager.py` 测试覆盖 (86%)
  - [x] `config_validator.py` 测试覆盖 (86%)
  - [x] `market_data_fetcher.py` 测试覆盖 ✅ 新增
  - 当前覆盖率: 42%（349个测试用例）

- [x] **类型注解完善** ✅ 已完成
  - [x] 添加 py.typed 文件
  - [x] 配置 mypy 静态类型检查
  - [x] 修复主要类型注解问题（Path | None, Decimal 等）
  - [x] 核心函数添加类型注解
  - [ ] 使用 mypy 进行静态类型检查（剩余 125 个警告）

- [x] **文档字符串** ✅ 已完成
  - [x] 核心模块添加 docstring
  - [x] 核心类添加 docstring
  - [x] 核心公共函数添加 docstring

### 2. 功能增强

- [x] **市场数据缓存优化** ✅ 已完成
  - [x] 添加缓存过期机制
  - [x] 支持离线模式
  - [ ] 支持增量更新（只更新变化的数据）

- [x] **错误处理增强** ✅ 已完成
  - [x] 添加自定义异常类
  - [x] 改进错误提示信息（使用自定义异常）
  - [ ] 添加错误恢复机制

- [x] **配置验证** ✅ 已完成
  - [x] 添加 .env 配置验证
  - [x] 添加 API Key 有效性检查
  - [ ] 添加配置迁移脚本

---

## 🟡 中优先级 (Medium Priority)

### 3. 功能增强

- [x] **投资分析增强** ✅ 已完成
  - [x] 添加最大回撤计算
  - [x] 添加夏普比率计算
  - [x] 添加波动率统计
  - [x] 添加相关性分析
  - [x] 添加 Beta 和 Alpha 计算

- [x] **收益率计算优化** ✅ 已完成
  - [x] 添加 days360 函数（金融计算方法）
  - [x] 使用 days360 计算投资天数
  - [x] 对有交易记录的产品使用 IRR 计算年化收益率
  - [x] 时间加权年化收益率使用复利公式
  - [x] 与 ts-demo 计算逻辑保持一致

- [x] **AI 分析模块** ✅ 已完成
  - [x] 支持 OpenAI/DeepSeek API 进行深度分析
  - [x] 规则分析作为后备（无 API 时使用）
  - [x] 缓存机制（默认 1 小时）
  - [x] 投资摘要生成
  - [x] 风险评估
  - [x] 投资建议生成
  - [x] 风险警告
  - [x] 综合评分（0-100 分）
  - [x] 推荐资产配置（保守型/平衡型/激进型）

- [x] **投资组合专业指标** ✅ 已完成
  - [x] 总收益率、年化收益率
  - [x] 波动率（年化）
  - [x] 夏普比率
  - [x] 最大回撤
  - [x] 胜率、盈亏比
  - [x] 卡玛比率、索提诺比率
  - [x] VaR (95%, 99%)
  - [x] CVaR (预期亏损)
  - [x] Beta 系数
  - [x] 跟踪误差、信息比率

- [ ] **报告功能增强**
  - [ ] 添加 PDF 报告导出
  - [ ] 添加 HTML 报告导出
  - [ ] 添加图表生成（matplotlib/plotly）
  - [ ] 添加邮件发送功能

- [ ] **数据导入增强**
  - [ ] 支持 Excel 文件导入
  - [ ] 支持 JSON 文件导入
  - [ ] 支持从数据库导入
  - [ ] 添加数据校验和清洗

- [ ] **实时数据增强**
  - [ ] 添加更多市场指数（恒生指数、日经225等）
  - [ ] 添加个股实时价格
  - [ ] 添加基金净值实时更新
  - [ ] 添加汇率实时更新

### 4. 性能优化

- [ ] **数据加载优化**
  - [ ] 使用 pandas 的 lazy loading
  - [ ] 添加数据分块加载
  - [ ] 优化内存使用

- [ ] **并发请求**
  - [ ] 使用 asyncio 并发获取市场数据
  - [ ] 使用多线程处理大量数据
  - [ ] 添加请求限流机制

- [ ] **缓存优化**
  - [ ] 使用 Redis 缓存（可选）
  - [ ] 添加缓存压缩
  - [ ] 添加缓存统计

### 5. 用户体验

- [x] **CLI 增强** ✅ 已完成
  - [x] 添加进度条显示
  - [x] 添加彩色输出主题
  - [ ] 添加交互式命令（问卷式输入）
  - [ ] 添加命令自动补全

- [x] **日志系统** ✅ 已完成
  - [x] 添加结构化日志
  - [x] 添加日志级别控制
  - [x] 添加日志文件轮转
  - [x] 添加敏感信息过滤

---

## 🟢 低优先级 (Low Priority)

### 6. DevOps

- [x] **CI/CD 配置** ✅ 已完成
  - [x] 添加 GitHub Actions 配置
  - [x] 自动运行测试
  - [x] 自动代码检查
  - [x] 自动发布到 PyPI

- [ ] **Docker 支持**
  - [ ] 添加 Dockerfile
  - [ ] 添加 docker-compose.yml
  - [ ] 添加 Docker 镜像发布

- [ ] **代码质量工具**
  - [x] 配置 pre-commit hooks
  - [x] 配置 black 自动格式化
  - [x] 配置 isort 自动排序
  - [x] 配置 flake8 代码检查
  - [x] 配置 mypy 静态类型检查
  - [ ] 配置 pylint 检查规则

### 7. 文档完善

- [ ] **API 文档**
  - [ ] 使用 Sphinx 生成 API 文档
  - [ ] 添加使用示例
  - [ ] 添加常见问题解答

- [ ] **架构文档**
  - [ ] 添加系统架构图
  - [ ] 添加数据流图
  - [ ] 添加模块依赖图

- [ ] **使用指南**
  - [ ] 添加快速入门指南
  - [ ] 添加高级功能教程
  - [ ] 添加最佳实践文档

### 8. 扩展功能

- [ ] **Web 界面**
  - [ ] 添加 Flask/FastAPI Web 服务
  - [ ] 添加 REST API
  - [ ] 添加 Web Dashboard

- [ ] **数据可视化**
  - [ ] 添加收益曲线图
  - [ ] 添加资产配置饼图
  - [ ] 添加风险分布图

- [ ] **AI 功能**
  - [ ] 添加投资建议生成
  - [ ] 添加风险评估模型
  - [ ] 添加智能定投建议

- [ ] **数据同步**
  - [ ] 添加云存储同步
  - [ ] 添加多设备同步
  - [ ] 添加数据加密

---

## 📋 已完成 (Completed)

- [x] 实时盈亏估算功能
- [x] 已卖出投资分析
- [x] 按投资时间分组分析
- [x] 市场指数数据获取（Alpha Vantage + Finnhub）
- [x] 历史走势数据支持
- [x] 周期表现计算
- [x] 技术状态估算（RSI、MACD）
- [x] Makefile 完善
- [x] 备份功能
- [x] 项目状态检查增强
- [x] 单元测试覆盖（核心模块）
  - [x] `exceptions.py`: 100%
  - [x] `models.py`: 99%
  - [x] `time_group.py`: 99%
  - [x] `sold_investment.py`: 87%
  - [x] `realtime_pnl.py`: 86%
  - [x] `cache_manager.py`: 86%
  - [x] `config_validator.py`: 86%
  - [x] `advanced_analytics.py`: 82%
  - [x] `irr_calculator.py`: 76%
  - [x] `csv_parser.py`: 67%
  - [x] `config.py`: 65%
  - [x] `market_index.py`: 64%
  - [x] `market_data_fetcher.py`: 新增
  - [x] `portfolio_analytics.py`: 新增
  - [x] `ai_analyzer.py`: 新增
  - [x] `logger.py`: 新增
  - [x] `progress.py`: 新增
  - 总体覆盖率: 42%（349个测试用例）
- [x] 高级分析模块
  - [x] 最大回撤计算
  - [x] 夏普比率计算
  - [x] 波动率统计
  - [x] 相关性分析
  - [x] Beta/Alpha 计算
- [x] 自定义异常类
- [x] 缓存管理器（支持过期机制、离线模式）
- [x] 配置验证器（.env 验证、API Key 检查）
- [x] py.typed 文件和 mypy 配置
- [x] **收益率计算与 ts-demo 对齐** ✅ 2026-02-28
  - [x] 添加 days360 函数（金融计算方法）
  - [x] 投资天数使用 days360 计算
  - [x] 年化收益率使用 IRR 计算（中长期投资）
  - [x] 时间加权年化收益率使用复利公式
  - [x] 数据同步（ts-demo 和 asset-lens 使用相同数据）
  - [x] 修复类型注解问题（Path | None, Decimal 等）
- [x] **风险提示显示优化** ✅ 2026-02-28
  - [x] 显示更多产品信息（从 3 个增加到 5 个）
  - [x] 根据不同类型警告显示不同信息
  - [x] 显示年化收益率、投资天数、金额等详细信息
- [x] **代码质量优化** ✅ 2026-02-28
  - [x] 解决 mypy 类型警告（从 143 个减少到 125 个）
  - [x] 修复主要类型注解问题
  - [x] 添加核心函数类型注解
- [x] **AI 分析模块集成** ✅ 2026-02-28
  - [x] 支持 OpenAI/DeepSeek API 进行深度分析
  - [x] 规则分析作为后备
  - [x] 缓存机制（默认 1 小时）
  - [x] 投资摘要、风险评估、建议、警告、综合评分
  - [x] 推荐资产配置（保守型/平衡型/激进型）
- [x] **投资组合专业指标** ✅ 2026-02-28
  - [x] 总收益率、年化收益率、波动率、夏普比率
  - [x] 最大回撤、胜率、盈亏比
  - [x] 卡玛比率、索提诺比率
  - [x] VaR (95%, 99%)、CVaR、Beta、跟踪误差、信息比率
  - [x] **日志系统** ✅ 2026-02-28
  - [x] 彩色输出、敏感信息过滤、文件日志支持
  - [x] **进度条工具** ✅ 2026-02-28
  - [x] ProgressBar、Spinner、TaskProgress
- [x] **pre-commit hooks** ✅ 2026-02-28
  - [x] black、isort、flake8、mypy 配置
- [x] **GitHub Actions CI/CD** ✅ 2026-02-28
  - [x] 多版本 Python 测试（3.10, 3.11, 3.12）
  - [x] 自动代码检查（black、isort、flake8、mypy）
  - [x] 自动构建和发布
- [x] **Makefile 命令更新** ✅ 2026-02-28
  - [x] `make ai-analyze`: AI 分析投资组合
  - [x] `make portfolio-metrics`: 计算投资组合专业指标
  - [x] 测试用例从 282 个增加到 349 个
  - [x] 所有测试通过，所有命令正常工作

---

## 🐛 已知问题 (Known Issues)

1. ~~**卖出记录解析警告**~~ ✅ 已修复
   - ~~第 36 行卖出记录数据解析失败~~
   - 原因：第 36 行是汇总行，不是卖出记录
   - 解决：跳过没有名称的行

2. **IRR 计算数值稳定性**
   - 某些情况下会出现 OverflowError
   - 已添加异常处理，但可能需要更好的算法

3. **国内市场历史数据**
   - 新浪财经 API 不提供历史数据
   - 当前方案是从缓存文件读取历史数据

4. **Alpha Vantage API 限制**
   - 免费版 25 次/天
   - 需要等待 12 秒才能获取下一个数据

5. **mypy 类型检查警告**
   - 当前有 125 个类型警告
   - 主要涉及 Optional 类型和 Decimal 类型
   - 不影响功能运行

---

## 📝 备注 (Notes)

### API Key 管理

- Finnhub API: https://finnhub.io/dashboard (推荐，60次/分钟)
- Alpha Vantage API: https://www.alphavantage.co/support/#api-key (备用，25次/天)
- DeepSeek API: https://platform.deepseek.com (可选，用于 AI 分析）

### 数据格式

- 国内市场数据: `cache/market_index_domestic.json`
- 海外市场数据: `cache/market_index_foreign.json`
- 数据格式与 ts-demo 保持一致

### 更新频率建议

- **每日更新**: 使用 `make quick` 快速更新实时数据
- **每周更新**: 使用 `make update-market-data` 获取完整历史数据
- **每月备份**: 使用 `make backup` 备份数据文件

### 收益率计算说明

- **投资天数**: 使用 days360 函数计算（金融计算方法，假设每年 360 天，每月 30 天）
- **年化收益率**:
  - 短期投资（<180天）：使用简单年化公式
  - 中长期投资（>=180天）：使用 IRR（内部收益率）计算
- **时间加权年化收益率**: 使用复利公式 `(1 + r)^(1/y) - 1`

### AI 分析配置

在 `.env` 文件中添加：
```env
# AI 分析配置（可选）
# 支持 OpenAI 兼容 API（如 DeepSeek、通义千问等）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat

# AI 缓存配置
AI_CACHE_TTL=3600  # 缓存有效期（秒），默认 1 小时
```

### Makefile 命令

| 命令 | 说明 |
|------|------|
| `make test` | 运行所有测试 |
| `make ai-analyze` | AI 分析投资组合（需要配置 OPENAI_API_KEY） |
| `make portfolio-metrics` | 计算投资组合专业指标（夏普比率、最大回撤等） |
| `make analyze` | 分析投资组合（使用 .env 中的 DATA_MODE 设置） |
| `make analyze-real` | 分析投资组合（强制使用 real 模式） |
| `make calculate` | 快捷计算收益率 |
| `make calculate-real` | 快捷计算收益率 (real 模式） |
| `make weekly` | 生成周度报告 |
| `make analyze-sold` | 分析已卖出投资 |
| `make analyze-by-time` | 按投资时间分组分析 |
| `make estimate-pnl` | 估算日盈亏（基于市场指数） |
| `make daily` | 快速日度分析（更新数据+估算盈亏） |
| `make update-market-data` | 更新市场指数数据（完整历史数据） |
| `make update-market-data-fast` | 快速更新市场指数数据（仅实时数据） |
| `make mode-sample` | 切换到 sample 模式 |
| `make mode-real` | 切换到 real 模式 |
| `make show-config` | 显示当前配置 |
| `make check` | 检查项目状态 |
| `make version` | 显示版本信息 |
| `make backup` | 备份数据文件 |
| `make clean` | 清理输出文件 |
| `make clean-cache` | 清理缓存文件 |
| `make clean-all` | 清理所有生成的文件 |
| `make format` | 格式化代码 |
| `make lint` | 运行代码检查 |
| `make ci` | 完整 CI 流程（格式化+检查+测试） |
| `make dev` | 开发流程：安装依赖、格式化、检查、测试 |
| `make quick` | 快速查看：更新数据+估算盈亏 |
| `make run` | 快捷运行分析（等同于 make analyze） |

---

## 🎯 下一步计划 (Next Steps)

1. ~~完成单元测试覆盖（目标 80%+）~~ 当前 42%（349个测试用例）
2. ~~添加最大回撤和夏普比率计算~~ ✅ 已完成
3. ~~优化错误处理和用户提示~~ ✅ 已完成
4. ~~收益率计算与 ts-demo 对齐~~ ✅ 已完成
5. ~~代码质量优化（类型注解、文档字符串、错误提示）~~ ✅ 已完成
6. ~~AI 分析模块集成~~ ✅ 已完成
7. ~~投资组合专业指标模块~~ ✅ 已完成
8. ~~日志系统和进度条工具~~ ✅ 已完成
9. ~~pre-commit hooks 和 GitHub Actions CI/CD~~ ✅ 已完成
10. 添加 PDF 报告导出功能
11. 添加 HTML 报告导出功能
12. 添加图表生成（matplotlib/plotly）
13. 添加邮件发送功能
14. 配置 CI/CD 自动化流程
15. 解决剩余的 mypy 类型警告（125 个）
16. 添加数据可视化功能
17. 添加 Web Dashboard
