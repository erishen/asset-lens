# asset-lens TODO List

> 最后更新: 2026-03-09

---

## ✅ 已完成 (Completed)

### 2026-03-09 新增

- [x] **K 线技术指标**
  - [x] MA 均线 (MA5/MA10/MA20)
  - [x] MACD 指标 (DIF/DEA/MACD柱)
  - [x] KDJ 指标 (K/D/J)
  - [x] 指标显示/隐藏切换

- [x] **实时数据推送**
  - [x] WebSocket 服务端支持
  - [x] 前端 useWebSocket Hook
  - [x] 自动刷新功能 (默认关闭)
  - [x] 页面可见性检测

- [x] **股票池功能增强**
  - [x] 股票池 API 端点
  - [x] 过滤北交所股票
  - [x] 显示策略信息
  - [x] 清理测试文件

- [x] **投资组合表格增强**
  - [x] 添加年化收益率列
  - [x] UI 布局优化
  - [x] 按钮样式优化

- [x] **收益曲线修复**
  - [x] 修复数据目录路径
  - [x] 类型名称中文化

### 2026-03-08 新增

- [x] **代码覆盖率提升**
  - [x] 从 55% 提升到 61%
  - [x] 新增 test_market_stock_fetcher.py 测试
  - [x] 新增 test_report_generator.py 测试
  - [x] 新增 test_csv_parser_advanced.py 测试
  - [x] 新增 test_scheduler_advanced.py 测试
  - [x] 新增 test_stock_history_fetcher_advanced.py 测试
  - [x] 新增 test_international_stock_fetcher.py 测试
  - [x] 测试用例从 1129 增加到 1242 个

- [x] **循环导入问题修复**
  - [x] 修复 backtester.py 循环导入警告
  - [x] 使用 TYPE_CHECKING 延迟导入
  - [x] 更新相关测试用例

- [x] **股票追踪去重**
  - [x] 修复 record_daily 重复记录问题
  - [x] 添加返回值表示是否成功记录
  - [x] 清理历史重复数据
  - [x] 更新测试用例

- [x] **Cron Job 优化**
  - [x] 执行时间从 09:30 改为 15:30（收盘后）
  - [x] 每天执行，周末自动获取上周五数据
  - [x] 更新 setup_cron.sh 脚本

- [x] **Web Dashboard 移动端优化**
  - [x] 添加响应式 CSS 媒体查询 (768px, 480px)
  - [x] 实现汉堡菜单导航
  - [x] 优化卡片和图表布局
  - [x] 优化表格横向滚动
  - [x] 触摸友好的按钮尺寸 (min-height: 44px)
  - [x] 图表自适应移动端显示
  - [x] 禁止用户缩放 (user-scalable=no)

- [x] **架构优化 - 缓存机制**
  - [x] IRRCalculator 添加 @lru_cache 缓存优化
  - [x] 新增 PortfolioCalculator 服务类
  - [x] 统一汇率转换逻辑 `_convert_amount()`
  - [x] 实例级缓存 + `clear_cache()` 方法
  - [x] 测试用例增加到 1246 个

### 2026-03-07 新增

- [x] **数据同步功能**
  - [x] 创建 `scripts/sync_data.py` 数据同步脚本
  - [x] 添加 `make sync-data` 命令
  - [x] 添加 `make sync-data-latest` 命令
  - [x] 添加 `make sync-data-preview` 命令
  - [x] 更新 Skill 和文档支持自然语言唤起

- [x] **定时任务优化**
  - [x] 添加网络请求超时机制
  - [x] 修复 `make run-daily-tasks` 卡住问题
  - [x] 添加进度输出显示
  - [x] 添加 `make start-scheduler` 命令
  - [x] 配置 cron 定时任务文档

- [x] **股票池去重**
  - [x] 修复同一天重复入选问题
  - [x] 清理历史重复数据
  - [x] 更新测试用例

- [x] **基金代码匹配**
  - [x] 添加易方达国防军工混合C (015035)
  - [x] 添加华宝油气A (162411)

- [x] **交易记录解析完善**
  - [x] 创建 `transaction_parser.py` 模块
  - [x] 支持定投期间解析 (`2025/9/19-now:buy:100`)
  - [x] 支持智能定投 (`50~150`)
  - [x] 支持浮动定投 (`100±20`)
  - [x] 支持估值模式定投 (`100-300-500`)
  - [x] 支持暂停期间 (`:stop`)
  - [x] 与 ts-demo 计算逻辑保持一致

- [x] **综合评价计算优化**
  - [x] 使用交易记录计算净投入
  - [x] 定投基金类型使用 CSV 初始金额
  - [x] 智能定投使用 CSV 初始金额
  - [x] 数据与 ts-demo 保持一致

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

---

## 🚧 进行中 (In Progress)

### 阶段三：Web 化与可视化

- [x] **Web Dashboard 增强**
  - [x] 添加实时行情展示
  - [x] 添加 K 线图表 (React 版本)
  - [x] 添加收益曲线图
  - [x] 添加持仓分布饼图
  - [x] 添加风险仪表盘
  - [x] 添加移动端适配
  - [x] 添加主题切换功能
  - [x] 添加搜索筛选功能
  - [x] 添加 CSV 导出功能

- [x] **数据可视化**
  - [x] ECharts 交互式图表
  - [x] K 线图表组件
  - [x] 收益曲线图组件
  - [x] 多周期切换 (日K/周K/月K)

- [x] **报告导出**
  - [x] HTML 报告导出
  - [x] 报告模板设计
  - [x] 持仓明细嵌入

- [x] **React 前端完善**
  - [x] K 线技术指标 (MA/MACD/KDJ)
  - [x] 实时数据推送
  - [ ] 更多图表类型

---

## 📋 待开发 (Planned)

### 阶段四：AI 增强

- [ ] **机器学习模型**
  - [ ] 风险评分模型
  - [ ] 策略效果预测
  - [ ] 市场趋势预测
  - [ ] 股票推荐模型

- [ ] **AI 投资建议增强**
  - [ ] 多模型支持 (DeepSeek, GPT-4, Claude)
  - [ ] 投资建议历史记录
  - [ ] 建议效果追踪
  - [ ] 个性化推荐

- [ ] **智能分析**
  - [ ] 新闻情感分析
  - [ ] 舆情监控
  - [ ] 行业轮动分析
  - [ ] 资金流向分析

### 功能增强

- [ ] **回测系统增强**
  - [ ] 支持更多策略类型
  - [ ] 支持自定义指标
  - [ ] 支持多品种回测
  - [ ] 回测报告优化

- [x] **数据源扩展**
  - [x] 支持更多 A 股数据源
  - [x] 支持加密货币数据 (CCXT - Binance, OKX, Coinbase 等)
  - [x] 支持宏观经济数据 (FRED API, World Bank API)
  - [x] 支持期货行情 (AkShare - 国内期货、国际期货)

- [ ] **通知系统增强**
  - [ ] 钉钉机器人通知
  - [ ] Telegram 通知
  - [ ] 自定义 Webhook
  - [ ] 通知规则配置

### 用户体验

- [ ] **CLI 增强**
  - [ ] 交互式命令向导
  - [ ] 命令历史记录
  - [ ] 自动补全优化
  - [ ] 彩色输出增强

- [ ] **配置管理**
  - [ ] 配置文件热重载
  - [ ] 多配置文件支持
  - [ ] 配置验证增强
  - [ ] 配置导入导出

### DevOps

- [ ] **Docker 增强**
  - [ ] 多阶段构建优化
  - [ ] Docker Compose 完整配置
  - [ ] Kubernetes 部署配置
  - [ ] CI/CD 流水线优化

- [ ] **监控告警**
  - [ ] Prometheus 指标
  - [ ] Grafana 仪表盘
  - [ ] 日志聚合
  - [ ] 性能监控

---

## 🐛 已知问题 (Known Issues)

- [x] ~~Baostock 登录可能偶尔失败，需要重试机制~~ ✅ 已修复 (2026-03-08)
  - 添加 `_baostock_login_with_retry()` 方法
  - 最大重试 3 次，每次间隔 2 秒
  - 添加重试成功测试用例
- [x] ~~部分港股/美股数据获取不稳定~~ ✅ 已修复 (2026-03-08)
  - 添加 `_fetch_with_retry()` 通用重试方法
  - 所有港股/美股/期货获取方法都支持重试
  - 最大重试 3 次，每次间隔 2 秒
- [x] ~~Web Dashboard 在移动端显示需要优化~~ ✅ 已修复 (2026-03-08)
  - 添加响应式布局
  - 汉堡菜单导航
  - 图表自适应
- [x] ~~大量数据时图表渲染较慢~~ ✅ 已修复 (2026-03-08)
  - ECharts large 模式 (大数据量优化)
  - 数据采样算法 (sampleData 函数)
  - 表格分页 (每页 15 条)
  - 防抖处理 resize 事件 (150ms)
  - 骨架屏加载状态
  - 图表懒加载 (setTimeout 50ms)
  - 动画优化 (elasticOut 缓动)

---

## 📊 系统状态

| 指标 | 状态 |
|------|------|
| 测试用例 | ✅ 1242 个通过 |
| Lint 警告 | ✅ 0 个 |
| Mypy 检查 | ✅ 0 个错误 |
| Pylint 评分 | ✅ 9.31/10 |
| 代码覆盖率 | 📊 61% |
| Web Dashboard | ✅ 基础版已完成 |
| 文档完整性 | 📚 用户手册已更新 |

---

## 📦 新增模块汇总

| 模块 | 文件 | 功能 |
|------|------|------|
| 定时任务 | `scheduler.py` | 每日自动执行任务 |
| 报告生成 | `report_generator.py` | 生成各类投资报告 |
| 图表生成 | `chart_generator.py` | 生成图表数据 |
| 风险管理 | `risk_manager.py` | 仓位管理、风险预警 |
| 智能推荐 | `intelligent_recommender.py` | 策略和股票智能推荐 |
| 国际股票 | `international_stock_fetcher.py` | 港股、美股、期货数据获取 |
| 多数据源 | `multi_source_fetcher.py` | 多数据源管理和故障切换 |
| 通知系统 | `notification_manager.py` | 邮件和微信通知 |
| 备份管理 | `backup_manager.py` | 数据自动备份和恢复 |
| Web API | `web/api.py` | FastAPI REST API 服务 |
| AI 顾问 | `ai_stock_advisor.py` | 智能选股和策略建议 |
| 交易解析 | `transaction_parser.py` | 交易记录智能解析 |

---

**免责声明**: 本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。