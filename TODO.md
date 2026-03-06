# asset-lens TODO List

> 最后更新: 2026-03-06

---

## ✅ 已完成 (Completed)

### 高优先级 (2026-03-06)

- [x] **修复回测系统历史数据获取问题**
  - [x] 优化 Baostock 登录登出，减少频繁连接
  - [x] 添加 `baostock_logout()` 方法
  - [x] 批量获取后统一登出

- [x] **添加自动每日记录功能**
  - [x] 创建 `scheduler.py` 定时任务模块
  - [x] 支持每日数据更新、策略选股、股票跟踪、妖股检测
  - [x] 添加 `make run-daily-tasks` 命令
  - [x] 添加 `make task-status` 命令

- [x] **优化妖股识别算法**
  - [x] 新增 4 种信号类型
  - [x] 加速上涨检测 (15分)
  - [x] 创新高检测 (12分)
  - [x] 跳空高开检测 (10分)
  - [x] 波动突破检测 (8分)

- [x] **添加投资策略系统测试**
  - [x] 14 个测试用例全部通过
  - [x] StockPool 测试 (5个)
  - [x] StrategyEngine 测试 (3个)
  - [x] StockTracker 测试 (2个)
  - [x] MarketEnvironment 测试 (3个)
  - [x] Integration 测试 (1个)

### 中优先级 (2026-03-06)

- [x] **添加投资策略报告**
  - [x] 创建 `report_generator.py` 模块
  - [x] 策略报告 (`make report-strategy`)
  - [x] 股票池报告 (`make report-pool`)
  - [x] 策略对比报告 (`make report-comparison`)
  - [x] 风险评估报告 (`make report-risk`)

- [x] **添加股票池收益曲线图**
  - [x] 创建 `chart_generator.py` 模块
  - [x] 收益曲线图数据生成
  - [x] 策略对比图数据生成
  - [x] 妖股信号图数据生成
  - [x] 风险仪表盘数据生成

- [x] **添加仓位管理建议**
  - [x] 创建 `risk_manager.py` 模块
  - [x] 根据市场环境动态调整仓位建议
  - [x] 止损止盈位计算
  - [x] 持仓集中度分析
  - [x] `make position-advice` 命令

- [x] **添加风险预警系统**
  - [x] 市场风险预警
  - [x] 持仓集中度预警
  - [x] 止损触发预警
  - [x] 胜率预警
  - [x] 风险评分系统 (0-100分)
  - [x] `make risk-summary` 命令

### 代码质量 (2026-03-06)

- [x] **修复测试问题**
  - [x] 702 个测试全部通过
  - [x] 修复方法名变更导致的测试失败
  - [x] 更新 `test_market_data_fetcher.py`
  - [x] 更新 `test_investment_system.py`

- [x] **修复 lint 警告**
  - [x] 从 138 个错误减少到 0 个 (减少 100%)
  - [x] 修复 18 个文件的类型标注问题
  - [x] 修复方法名引用错误
  - [x] 使用 `# type: ignore` 忽略第三方库类型问题
  - [x] 优化代码风格

---

## 🔴 高优先级 (High Priority)

### 数据质量

- [ ] **历史数据获取优化**
  - [ ] 添加数据缓存机制
  - [ ] 添加数据完整性检查
  - [ ] 支持增量更新
  - [ ] 添加更多数据源备用

### 功能完善

- [ ] **策略引擎优化**
  - [ ] 添加策略回测验证
  - [ ] 添加策略参数优化功能
  - [ ] 支持自定义策略创建
  - [ ] 添加策略组合功能

---

## 🟡 中优先级 (Medium Priority)

### 用户体验优化

- [ ] **CLI 命令优化**
  - [ ] 添加命令自动补全
  - [ ] 添加交互式命令（问卷式输入）
  - [ ] 优化错误提示信息

- [ ] **数据可视化**
  - [ ] 添加图表渲染功能（matplotlib/plotly）
  - [ ] 添加 HTML 报告导出

### 功能增强

- [ ] **智能推荐**
  - [ ] 基于历史表现推荐策略
  - [ ] 基于市场环境推荐股票

- [ ] **数据源扩展**
  - [ ] 添加港股数据支持
  - [ ] 添加美股数据支持
  - [ ] 添加期货数据支持

---

## � 低优先级 (Low Priority)

### 扩展功能

- [ ] **Web 界面**
  - [ ] 添加 Flask/FastAPI Web 服务
  - [ ] 添加 REST API
  - [ ] 添加 Web Dashboard

- [ ] **自动化功能**
  - [ ] 添加定时任务（每日更新）
  - [ ] 添加邮件/微信通知
  - [ ] 添加自动备份

- [ ] **AI 功能增强**
  - [ ] 添加智能选股建议
  - [ ] 添加策略参数优化建议
  - [ ] 添加市场预测模型

### DevOps

- [ ] **Docker 支持**
  - [ ] 添加 Dockerfile
  - [ ] 添加 docker-compose.yml

---

## � 新增模块汇总

| 模块 | 文件 | 功能 |
|------|------|------|
| 定时任务 | `scheduler.py` | 每日自动执行任务 |
| 报告生成 | `report_generator.py` | 生成各类投资报告 |
| 图表生成 | `chart_generator.py` | 生成图表数据 |
| 风险管理 | `risk_manager.py` | 仓位管理、风险预警 |

## 📋 新增命令汇总

```bash
# 定时任务
make run-daily-tasks    # 运行每日任务
make task-status        # 查看任务状态

# 投资报告
make report-strategy    # 策略报告
make report-pool        # 股票池报告
make report-comparison  # 策略对比报告
make report-risk        # 风险评估报告

# 风险管理
make risk-summary       # 风险摘要
make position-advice    # 仓位建议
```

---

## 📊 系统状态

| 指标 | 状态 |
|------|------|
| 测试用例 | ✅ 702 个通过 |
| Lint 警告 | ✅ 0 个 |
| 代码覆盖率 | 📊 待补充 |
| 文档完整性 | 📚 用户手册已更新 |

---

**免责声明**: 本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。
