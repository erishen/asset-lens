# Makefile for asset-lens
# 个人资产操作系统 - Make 命令集成

# 变量定义
PYTHON := python
CONDA_ENV := asset-lens
CONDA := conda run -n $(CONDA_ENV)
PROJECT_DIR := $(shell pwd)
VERSION := 1.0.0

# 默认目标
.PHONY: all
all: menu

# ============================================
# 交互式菜单
# ============================================
.PHONY: menu
menu: ## 显示交互式菜单
	@echo ""
	@echo "  ╔════════════════════════════════════════════════════════════╗"
	@echo "  ║           asset-lens - 个人资产操作系统 v$(VERSION)            ║"
	@echo "  ╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  🎯 快速开始:"
	@echo "    make daily            📊 每日分析（更新数据+估算盈亏）"
	@echo "    make weekly           📈 生成周报"
	@echo "    make analyze          📋 分析投资组合"
	@echo ""
	@echo "  📊 股票基金查询:"
	@echo "    make fetch-stock      📈 查询股票行情"
	@echo "    make fetch-fund       📊 查询基金净值"
	@echo "    make screen-stocks    🔍 股票筛选"
	@echo ""
	@echo "  📈 投资策略:"
	@echo "    make strategy-list    📋 查看策略列表"
	@echo "    make stock-pool-list  📊 查看股票池"
	@echo "    make backtest         📊 策略回测"
	@echo ""
	@echo "  🌐 Web 界面:"
	@echo "    make web              🚀 启动 Web Dashboard"
	@echo ""
	@echo "  📚 更多帮助:"
	@echo "    make help             📖 显示完整帮助"
	@echo "    make check            🔍 检查项目状态"
	@echo ""

# ============================================
# 帮助信息
# ============================================
.PHONY: help
help: ## 显示帮助信息
	@echo ""
	@echo "  ╔════════════════════════════════════════════════════════════╗"
	@echo "  ║           asset-lens - 个人资产操作系统 v$(VERSION)            ║"
	@echo "  ╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  📦 环境管理:"
	@echo "    make env-create       创建 conda 环境 asset-lens"
	@echo "    make env-list         列出所有 conda 环境"
	@echo "    make env-remove       删除 conda 环境 asset-lens"
	@echo ""
	@echo "  📥 依赖管理:"
	@echo "    make install          安装项目依赖"
	@echo "    make install-dev      安装开发依赖"
	@echo "    make update           更新项目依赖"
	@echo "    make list-pkgs        列出已安装的包"
	@echo ""
	@echo "  🚀 项目初始化:"
	@echo "    make init             初始化项目"
	@echo "    make init-sample      初始化示例数据"
	@echo "    make setup            完整初始化（环境+依赖+示例数据）"
	@echo ""
	@echo "  📊 分析命令:"
	@echo "    make analyze          分析投资组合（使用 .env 中的 DATA_MODE 设置）"
	@echo "    make calculate        快捷计算收益率"
	@echo "    make compare          对比不同时期的投资收益变化"
	@echo "    make analyze-sold     分析已卖出投资"
	@echo "    make analyze-by-time  按投资时间分组分析"
	@echo "    make ai-analyze       AI 分析投资组合（需要配置 API 密钥）"
	@echo "    make portfolio-metrics 计算投资组合专业指标（夏普比率、最大回撤等）"
	@echo "    make generate-charts  生成投资分析图表（资产配置、风险分布等）"
	@echo "    make generate-report  生成投资分析报告（PDF）"
	@echo "    make generate-html-report 生成投资分析报告（HTML）"
	@echo "    make report           生成投资报告"
	@echo "    make weekly           生成周度投资报告"
	@echo "    make sentiment        分析市场风向"
	@echo "    make predict-etf      预测 ETF 走势"
	@echo ""
	@echo "  💰 盈亏估算:"
	@echo "    make pnl             日度盈亏估算（基于市场指数）"
	@echo "    make pnl-weekly      周度盈亏估算（基于市场指数）"
	@echo "    make estimate        全产品日收益估算（基于预期年化收益率）"
	@echo "    make estimate-weekly 全产品周收益估算（基于预期年化收益率）"
	@echo "    make daily           快速日度分析（更新数据+估算盈亏）"
	@echo ""
	@echo "  📈 市场数据:"
	@echo "    make update-market-data    更新市场指数数据（完整历史数据）"
	@echo "    make update-market-data-fast 快速更新市场指数数据（仅实时数据）"
	@echo "    make update-market-data-async 异步并发更新市场指数数据（推荐）"
	@echo ""
	@echo "  📊 股票基金查询:"
	@echo "    make fetch-stock CODES=\"sh600519 sz000001\"  获取股票行情"
	@echo "    make fetch-fund CODES=\"000001 110022\"       获取基金净值"
	@echo "    make search-fund KEYWORD=\"沪深300\"          搜索基金"
	@echo "    make fetch-portfolio-funds  自动获取投资组合基金净值"
	@echo "    make update-all-data        一键更新所有数据（推荐）"
	@echo "    make filter-stocks          筛选自己投资的股票"
	@echo "    make filter-market-stocks   从市场获取股票列表并筛选"
	@echo "    make volume-breakout        筛选放量突破股票"
	@echo "    make volume-breakout-update 更新历史数据并筛选放量突破"
	@echo "    make screen-stocks          股票综合筛选（推荐）"
	@echo "    make screen-stocks-update   获取最新数据并筛选"
	@echo "    make screen-fundamental     仅基本面筛选"
	@echo "    make screen-technical       仅技术面筛选"
	@echo "    make predict-etf            根据股票活跃度预测ETF表现"
	@echo "    make predict-etf-portfolio  分析投资组合中的ETF相关产品并预测"
	@echo ""
	@echo "  🤖 机器学习:"
	@echo "    make ml-status        查看 ML 模块状态"
	@echo "    make ml-train         训练机器学习模型"
	@echo "    make ml-predict       预测股票 (CODE=sh600519)"
	@echo "    make ml-importance    查看特征重要性"
	@echo "    make ml-train-db      从数据库训练模型"
	@echo "    make ml-predictions   查看历史预测记录"
	@echo ""
	@echo "  🗄️  数据库管理:"
	@echo "    make db-stats         显示数据库统计"
	@echo "    make db-migrate       迁移JSON缓存到数据库"
	@echo "    make db-fetch         获取历史数据 (CODES=\"sh600519\")"
	@echo "    make db-kline         查询K线数据 (CODE=sh600519)"
	@echo "    make db-codes         列出所有股票代码"
	@echo "    make db-verify        验证数据完整性"
	@echo ""
	@echo "  📊 投资策略系统:"
	@echo "    make stock-pool-list        列出股票池中的股票"
	@echo "    make strategy-list          列出所有可用策略"
	@echo "    make strategy-show          显示策略详情 (NAME=value)"
	@echo "    make strategy-set           设置当前策略 (NAME=value)"
	@echo "    make strategy-screen        使用策略筛选股票 (NAME=value)"
	@echo "    make backtest               策略回测 (STRATEGY=value)"
	@echo "    make backtest-value         价值策略回测"
	@echo "    make backtest-momentum      动量策略回测"
	@echo "    make investment-status      查看投资系统状态"
	@echo "    make investment-report      生成投资报告"
	@echo "    make optimize-strategy      策略优化（找出最佳策略）"
	@echo "    make market-environment     分析市场环境"
	@echo "    make adapt-strategy         适配策略参数 (STRATEGY=value)"
	@echo "    make personal-data-load     加载个人每周数据"
	@echo "    make personal-data-summary  显示个人数据市场概况"
	@echo "    make run-daily-tasks        运行每日任务（立即执行）"
	@echo "    make start-scheduler        启动定时调度器（每日 09:30）"
	@echo "    make task-status            查看任务状态"
	@echo ""
	@echo "  ⚙️  配置管理:"
	@echo "    make mode-sample      切换到 sample 模式"
	@echo "    make mode-real        切换到 real 模式"
	@echo "    make show-config      显示当前配置"
	@echo ""
	@echo "  🔄 数据同步:"
	@echo "    make sync-data        同步 ts-demo 所有数据到 asset-lens"
	@echo "    make sync-data-latest 只同步最新数据"
	@echo "    make sync-data-preview 预览同步内容（不实际执行）"
	@echo ""
	@echo "  🧪 测试和代码质量:"
	@echo "    make test             运行测试"
	@echo "    make test-cov         运行测试并生成覆盖率报告"
	@echo "    make lint             运行代码检查"
	@echo "    make format           格式化代码"
	@echo "    make ci               完整 CI 流程（格式化+检查+测试）"
	@echo ""
	@echo "  🧹 清理命令:"
	@echo "    make clean            清理输出文件"
	@echo "    make clean-cache      清理缓存文件"
	@echo "    make clean-all        清理所有生成的文件"
	@echo ""
	@echo "  🌐 Web Dashboard:"
	@echo "    make web              启动 Web Dashboard (默认端口 8000)"
	@echo "    make web-port PORT=9000  启动 Web Dashboard (指定端口)"
	@echo "    make web-bg           后台启动 Web Dashboard"
	@echo "    make web-stop         停止 Web Dashboard"
	@echo ""
	@echo "  🔧 其他:"
	@echo "    make check            检查项目状态"
	@echo "    make version          显示版本信息"
	@echo "    make backup           备份数据文件"
	@echo ""

# ============================================
# 环境管理
# ============================================
.PHONY: env-create
env-create: ## 创建 conda 环境 asset-lens
	@echo "📦 创建 conda 环境 asset-lens..."
	conda create -n $(CONDA_ENV) --clone base -y || true
	@echo "✅ 环境创建成功"
	@echo "💡 请运行: conda activate $(CONDA_ENV)"

.PHONY: env-list
env-list: ## 列出所有 conda 环境
	@echo "📋 Conda 环境列表:"
	conda env list

.PHONY: env-remove
env-remove: ## 删除 conda 环境 asset-lens
	@echo "🗑️  删除 conda 环境 $(CONDA_ENV)..."
	conda env remove -n $(CONDA_ENV) -y
	@echo "✅ 环境已删除"

# ============================================
# 依赖管理
# ============================================
.PHONY: install
install: ## 安装项目依赖
	@echo "📥 安装项目依赖..."
	$(CONDA) pip install -r requirements.txt
	@echo "✅ 依赖安装完成"

.PHONY: install-dev
install-dev: ## 安装开发依赖
	@echo "📥 安装开发依赖..."
	$(CONDA) pip install -r requirements.txt
	$(CONDA) pip install black isort mypy pylint pytest pytest-cov
	@echo "✅ 开发依赖安装完成"

.PHONY: update
update: ## 更新项目依赖
	@echo "🔄 更新项目依赖..."
	$(CONDA) pip install --upgrade -r requirements.txt
	@echo "✅ 依赖更新完成"

.PHONY: list-pkgs
list-pkgs: ## 列出已安装的包
	@echo "📋 环境 $(CONDA_ENV) 中已安装的核心包:"
	@$(CONDA) pip list | grep -E "pandas|numpy|scipy|click|pydantic|rich|csvkit|pytest" || echo "   ⚠️  未找到相关包"

# ============================================
# 项目初始化
# ============================================
.PHONY: init
init: ## 初始化项目
	@echo "🚀 初始化 asset-lens 项目..."
	$(CONDA) python -m asset_lens init
	@echo "✅ 项目初始化完成"

.PHONY: init-sample
init-sample: ## 初始化示例数据
	@echo "📋 初始化示例数据..."
	$(CONDA) python -m asset_lens init-sample
	@echo "✅ 示例数据初始化完成"

.PHONY: setup
setup: env-create install init init-sample ## 完整初始化（环境+依赖+示例数据）
	@echo ""
	@echo "🎉 完整初始化完成！"
	@echo ""
	@echo "下一步操作:"
	@echo "  1. 运行 'conda activate $(CONDA_ENV)' 激活环境"
	@echo "  2. 运行 'make analyze' 分析投资组合"
	@echo "  3. 运行 'make update-market-data' 更新市场数据"
	@echo ""

# ============================================
# 分析命令
# ============================================
.PHONY: analyze
analyze: ## 分析投资组合（使用 .env 中的 DATA_MODE 设置）
	@echo "📊 分析投资组合..."
	$(CONDA) python -m asset_lens analyze --output-format all

.PHONY: calculate
calculate: ## 快捷计算收益率（显示收益率排名前10）
	@echo "🔢 计算收益率..."
	$(CONDA) python -m asset_lens calculate

.PHONY: compare
compare: ## 对比不同时期的投资收益变化
	@echo "📊 对比投资收益变化..."
	$(CONDA) python -m asset_lens compare

.PHONY: pnl
pnl: ## 实时盈亏估算（基于市场指数）
	@echo "💰 估算日盈亏..."
	$(CONDA) python -m asset_lens pnl

.PHONY: pnl-weekly
pnl-weekly: ## 周度盈亏估算（基于市场指数）
	@echo "💰 估算周盈亏..."
	$(CONDA) python -m asset_lens pnl --weekly

.PHONY: estimate
estimate: ## 全产品日收益估算（基于预期年化收益率）
	@echo "📊 全产品日收益估算..."
	$(CONDA) python -m asset_lens estimate

.PHONY: estimate-weekly
estimate-weekly: ## 全产品周收益估算（基于预期年化收益率）
	@echo "📊 全产品周收益估算..."
	$(CONDA) python -m asset_lens estimate --weekly

.PHONY: analyze-sold
analyze-sold: ## 分析已卖出投资
	@echo "📈 分析已卖出投资..."
	$(CONDA) python -m asset_lens analyze-sold

.PHONY: analyze-by-time
analyze-by-time: ## 按投资时间分组分析
	@echo "⏱️  按投资时间分组分析..."
	$(CONDA) python -m asset_lens analyze-by-time

.PHONY: report
report: ## 生成投资报告
	@echo "📊 生成投资报告..."
	$(CONDA) python -m asset_lens report

.PHONY: ai-analyze
ai-analyze: ## AI 分析投资组合（需要配置 API 密钥）
	@echo "🤖 AI 分析投资组合..."
	$(CONDA) python -m asset_lens ai-analyze

.PHONY: portfolio-metrics
portfolio-metrics: ## 计算投资组合专业指标（夏普比率、最大回撤等）
	@echo "📊 计算投资组合专业指标..."
	$(CONDA) python -m asset_lens portfolio-metrics

.PHONY: generate-charts
generate-charts: ## 生成投资分析图表（资产配置、风险分布等）
	@echo "📊 生成投资分析图表..."
	$(CONDA) python -m asset_lens generate-charts

.PHONY: generate-report
generate-report: ## 生成投资分析报告（PDF）
	@echo "📊 生成投资分析报告（PDF）..."
	$(CONDA) python -m asset_lens generate-report

.PHONY: generate-report-ai
generate-report-ai: ## 生成投资分析报告（PDF，包含 AI 分析）
	@echo "📊 生成投资分析报告（PDF，包含 AI 分析）..."
	$(CONDA) python -m asset_lens generate-report --include-ai

.PHONY: generate-html-report
generate-html-report: ## 生成投资分析报告（HTML）
	@echo "📊 生成投资分析报告（HTML）..."
	$(CONDA) python -m asset_lens generate-html-report

.PHONY: generate-html-report-ai
generate-html-report-ai: ## 生成投资分析报告（HTML，包含 AI 分析）
	@echo "📊 生成投资分析报告（HTML，包含 AI 分析）..."
	$(CONDA) python -m asset_lens generate-html-report --include-ai

.PHONY: investment-report
investment-report: ## 生成投资报告
	@echo "📊 生成投资报告..."
	$(CONDA) python -m asset_lens investment-report

# ============================================
# 市场数据
# ============================================
.PHONY: update-market-data
update-market-data: ## 更新市场指数数据（完整模式，更新所有指数）
	@echo "📈 更新市场指数数据（完整模式）..."
	$(CONDA) python -m asset_lens update-market-data

.PHONY: update-market-data-fast
update-market-data-fast: ## 快速更新市场指数数据（仅关键指数）
	@echo "📈 更新市场指数数据（快速模式）..."
	$(CONDA) python -m asset_lens update-market-data --fast

.PHONY: daily
daily: ## 快速日度分析（更新数据+智能同步股票历史+估算盈亏+自动交易信号+基金持仓分析）
	@echo ""
	@echo "============================================================"
	@echo "🚀 开始日度分析"
	@echo "============================================================"
	@echo ""
	@echo "📌 步骤 1/5: 📈 更新市场指数数据"
	@$(MAKE) --no-print-directory update-market-data-fast
	@echo ""
	@echo "📌 步骤 2/5: 🔄 智能同步股票历史数据"
	@$(MAKE) --no-print-directory db-auto-sync
	@echo ""
	@echo "📌 步骤 3/5: 💰 估算今日盈亏"
	@$(MAKE) --no-print-directory pnl
	@echo ""
	@echo "📌 步骤 4/5: 🤖 自动交易信号（模拟）"
	@$(MAKE) --no-print-directory auto-trade-dry
	@echo ""
	@echo "📌 步骤 5/5: 📊 基金持仓分析"
	@$(MAKE) --no-print-directory fund-holding
	@echo ""
	@echo "============================================================"
	@echo "✅ 日度分析完成！"
	@echo "============================================================"
	@echo ""
	@echo "📊 股票池管理:"
	@echo "  make stock-pool-list     查看股票池"
	@echo "  make auto-trade          执行自动交易"
	@echo "  make stock-pool-clear    清空股票池"
	@echo ""
	@echo "📈 分析报告:"
	@echo "  make pnl                 实时盈亏估算"
	@echo "  make report              生成投资报告"
	@echo "  make weekly              周度分析"
	@echo ""
	@echo "🤖 ML/AI 分析:"
	@echo "  make ml-sector           ML板块轮动分析"
	@echo "  make ml-analyze-market   ML市场行情分析"
	@echo "  make ai-trade            AI模拟交易"
	@echo ""
	@echo "📊 策略筛选:"
	@echo "  make strategy-list       查看所有策略"
	@echo "  make strategy-screen     策略筛选股票"
	@echo "  make backtest            策略回测"
	@echo ""
	@echo "🗄️ 数据管理:"
	@echo "  make db-stats            数据库统计"
	@echo "  make update-all-data     一键更新所有数据"
	@echo ""
	@echo "  make help                显示所有命令"

# ============================================
# ML数据准备
# ============================================
.PHONY: ml-fetch-stocks
ml-fetch-stocks: ## 获取A股市场股票列表（用于ML训练）
	@echo "📊 获取A股市场股票列表..."
	$(CONDA) python -m asset_lens fetch-market-stocks --save

.PHONY: ml-fetch-history
ml-fetch-history: ## 批量获取股票历史K线数据（用于ML训练，make ml-fetch-history LIMIT=50）
ifndef LIMIT
	@echo "📊 批量获取所有股票历史数据..."
	$(CONDA) python -m asset_lens fetch-history-batch --use-market-stocks --days 250
else
	@echo "📊 批量获取前 $(LIMIT) 只股票历史数据..."
	$(CONDA) python -m asset_lens fetch-history-batch --use-market-stocks --limit $(LIMIT) --days 250
endif

.PHONY: ml-fetch-history-fast
ml-fetch-history-fast: ## 快速获取少量股票历史数据（用于测试，50只）
	@echo "📊 快速获取50只股票历史数据..."
	$(CONDA) python -m asset_lens fetch-history-batch --use-market-stocks --limit 50 --days 120 --delay 0.1

.PHONY: ml-prepare-data
ml-prepare-data: ml-fetch-stocks ml-fetch-history-fast ## 准备ML训练数据（获取股票列表+历史数据）
	@echo ""
	@echo "✅ ML训练数据准备完成！"
	@echo ""
	@echo "📊 数据统计:"
	$(CONDA) python -m asset_lens db-stats
	@echo ""
	@echo "🤖 下一步:"
	@echo "  make ml-train-db         训练模型"

# ============================================
# 股票基金查询
# ============================================
.PHONY: fetch-stock
fetch-stock: ## 获取股票实时行情（make fetch-stock CODES="sh600519 sz000001"）
ifndef CODES
	@echo "❌ 错误: 需要提供股票代码"
	@echo ""
	@echo "用法: make fetch-stock CODES=\"sh600519 sz000001\""
	@echo ""
	@echo "示例:"
	@echo "  make fetch-stock CODES=\"sh600519\"        # 获取贵州茅台"
	@echo "  make fetch-stock CODES=\"sh600519 sz000001\"  # 获取多只股票"
	@echo ""
	@echo "常用股票代码:"
	@echo "  sh600519  贵州茅台"
	@echo "  sz000001  平安银行"
	@echo "  sh000001  上证指数"
	@echo "  sz399001  深证成指"
	@exit 1
endif
	@echo "📊 获取股票实时行情..."
	$(CONDA) python -m asset_lens fetch-stock $(CODES)

.PHONY: fetch-fund
fetch-fund: ## 获取基金净值（make fetch-fund CODES="000001 110022"）
ifndef CODES
	@echo "❌ 错误: 需要提供基金代码"
	@echo ""
	@echo "用法: make fetch-fund CODES=\"000001 110022\""
	@echo ""
	@echo "示例:"
	@echo "  make fetch-fund CODES=\"000001\"        # 获取华夏成长"
	@echo "  make fetch-fund CODES=\"000001 110022\"  # 获取多只基金"
	@exit 1
endif
	@echo "📊 获取基金净值..."
	$(CONDA) python -m asset_lens fetch-fund $(CODES)

.PHONY: search-fund
search-fund: ## 搜索基金（make search-fund KEYWORD="沪深300"）
ifndef KEYWORD
	@echo "❌ 错误: 需要提供搜索关键词"
	@echo ""
	@echo "用法: make search-fund KEYWORD=\"沪深300\""
	@exit 1
endif
	@echo "🔍 搜索基金..."
	$(CONDA) python -m asset_lens search-fund $(KEYWORD)

.PHONY: fetch-portfolio-funds
fetch-portfolio-funds: ## 自动获取投资组合中所有基金的净值
	@echo "📊 自动获取投资组合基金净值..."
	$(CONDA) python -m asset_lens fetch-portfolio-funds

.PHONY: update-all-data
update-all-data: ## 一键更新所有数据（市场指数、基金净值、股票行情）
	@echo "📊 更新所有数据..."
	$(CONDA) python -m asset_lens update-all-data

.PHONY: filter-stocks
filter-stocks: ## 筛选自己投资的股票
	@echo "📊 筛选自己投资的股票..."
	$(CONDA) python -m asset_lens filter-stocks

.PHONY: filter-market-stocks
filter-market-stocks: ## 从市场获取股票列表并筛选
	@echo "📊 从市场获取股票列表并筛选..."
	$(CONDA) python -m asset_lens filter-stocks --fetch-market

.PHONY: volume-breakout
volume-breakout: ## 筛选放量突破股票
	@echo "📊 筛选放量突破股票..."
	$(CONDA) python -m asset_lens volume-breakout

.PHONY: volume-breakout-update
volume-breakout-update: ## 更新历史数据并筛选放量突破股票
	@echo "📊 更新历史数据并筛选放量突破股票..."
	$(CONDA) python -m asset_lens volume-breakout --fetch-market --update-history

.PHONY: screen-stocks
screen-stocks: ## 股票综合筛选（基本面+技术面+评分）
	@echo "📊 股票综合筛选..."
	$(CONDA) python -m asset_lens screen-stocks

.PHONY: screen-stocks-update
screen-stocks-update: ## 获取最新市场数据并筛选
	@echo "📊 获取最新市场数据并筛选..."
	$(CONDA) python -m asset_lens screen-stocks --fetch-market

.PHONY: screen-fundamental
screen-fundamental: ## 仅基本面筛选
	@echo "📊 基本面筛选..."
	$(CONDA) python -m asset_lens screen-stocks --type fundamental

.PHONY: screen-technical
screen-technical: ## 仅技术面筛选
	@echo "📊 技术面筛选..."
	$(CONDA) python -m asset_lens screen-stocks --type technical

.PHONY: predict-etf
predict-etf: ## 根据股票活跃度预测ETF表现
	@echo "📊 根据股票活跃度预测ETF表现..."
	$(CONDA) python -m asset_lens predict-etf

.PHONY: predict-etf-portfolio
predict-etf-portfolio: ## 分析投资组合中的ETF相关产品并预测
	@echo "📊 分析投资组合中的ETF相关产品并预测..."
	$(CONDA) python -m asset_lens predict-etf --analyze-portfolio

# ============================================
# 投资策略系统
# ============================================
.PHONY: stock-pool-list
stock-pool-list: ## 列出股票池中的股票
	@echo "📊 列出股票池..."
	$(CONDA) python -m asset_lens.cli stock-pool --action list

.PHONY: stock-pool-clear
stock-pool-clear: ## 清空股票池
	@echo "🗑️ 清空股票池..."
	$(CONDA) python -m asset_lens stock-pool --action clear

.PHONY: stock-pool-clear-force
stock-pool-clear-force: ## 强制清空股票池（无需确认）
	@echo "🗑️ 强制清空股票池..."
	$(CONDA) python -m asset_lens stock-pool --action clear --force

.PHONY: strategy-list
strategy-list: ## 列出所有可用策略
	@echo "📊 列出所有可用策略..."
	$(CONDA) python -m asset_lens strategy --strategy-name list 2>/dev/null || echo "💡 使用 make help 查看可用命令"

.PHONY: strategy-show
strategy-show: ## 显示策略详情（make strategy-show NAME=momentum）
	@echo "📊 显示策略详情..."
	$(CONDA) python -m asset_lens strategy --strategy-name $(or $(NAME),momentum)

.PHONY: strategy-set
strategy-set: ## 设置当前策略（make strategy-set NAME=momentum）
	@echo "📊 设置当前策略..."
	$(CONDA) python -m asset_lens strategy --strategy-name $(or $(NAME),momentum)

.PHONY: strategy-screen
strategy-screen: ## 使用策略筛选股票（make strategy-screen STRATEGY=momentum）
	@echo "📊 使用策略筛选股票..."
	$(CONDA) python -m asset_lens screen-stocks --strategy $(or $(STRATEGY),momentum)

.PHONY: backtest
backtest: ## 策略回测（make backtest STRATEGY=momentum）
	@echo "📊 策略回测..."
	$(CONDA) python -m asset_lens backtest --strategy $(or $(STRATEGY),momentum)

.PHONY: backtest-value
backtest-value: ## 价值策略回测
	@echo "📊 价值策略回测..."
	$(CONDA) python -m asset_lens backtest --strategy value

.PHONY: backtest-momentum
backtest-momentum: ## 动量策略回测
	@echo "📊 动量策略回测..."
	$(CONDA) python -m asset_lens backtest --strategy momentum

.PHONY: investment-status
investment-status: ## 查看投资系统状态
	@echo "📊 查看投资系统状态..."
	$(CONDA) python -m asset_lens investment-status

.PHONY: optimize-strategy
optimize-strategy: ## 策略优化（找出最佳策略）
	@echo "📊 策略优化..."
	$(CONDA) python -m asset_lens optimize-strategy

# ============================================
# 动量策略选股
# ============================================
.PHONY: momentum-screen
momentum-screen: ## 动量策略选股
	@echo "📊 动量策略选股..."
	$(CONDA) python -m asset_lens momentum-screen

.PHONY: momentum-screen-pool
momentum-screen-pool: ## 动量策略选股并添加到股票池
	@echo "📊 动量策略选股并添加到股票池..."
	$(CONDA) python -m asset_lens momentum-screen --add-to-pool

.PHONY: auto-trade
auto-trade: ## 自动交易 - 根据策略信号自动买入卖出
	@echo "🤖 自动交易系统"
	$(CONDA) python -m asset_lens auto-trade

.PHONY: auto-trade-dry
auto-trade-dry: ## 自动交易（仅显示信号，不执行）
	@echo "🤖 自动交易系统（模拟模式）"
	$(CONDA) python -m asset_lens auto-trade --dry-run

.PHONY: auto-trade-ai
auto-trade-ai: ## 自动交易 + AI 分析辅助决策
	@echo "🤖 自动交易系统（AI 增强版）"
	$(CONDA) python -m asset_lens auto-trade --use-ai

.PHONY: auto-trade-ai-dry
auto-trade-ai-dry: ## 自动交易 + AI 分析（仅显示信号，不执行）
	@echo "🤖 自动交易系统（AI 增强版，模拟模式）"
	$(CONDA) python -m asset_lens auto-trade --use-ai --dry-run

# ============================================
# 机器学习
# ============================================
.PHONY: ml-status
ml-status: ## 查看 ML 模块状态
	@echo "🤖 ML 模块状态..."
	$(CONDA) python -m asset_lens ml status

.PHONY: ml-train
ml-train: ## 训练机器学习模型
	@echo "🤖 训练机器学习模型..."
	$(CONDA) python -m asset_lens ml train

.PHONY: ml-predict
ml-predict: ## 使用模型预测股票（make ml-predict CODE=sh600519）
	@echo "🔮 预测股票..."
	$(CONDA) python -m asset_lens ml predict --code $(or $(CODE),sh600519)

.PHONY: ml-importance
ml-importance: ## 查看模型特征重要性
	@echo "📊 特征重要性分析..."
	$(CONDA) python -m asset_lens ml importance

.PHONY: ml-train-db
ml-train-db: ## 从数据库训练模型
	@echo "🤖 从数据库训练模型..."
	$(CONDA) python -m asset_lens ml train-db

.PHONY: ml-predict-db
ml-predict-db: ## 从数据库预测股票（make ml-predict-db CODE=sh600519）
	@echo "🔮 从数据库预测股票..."
	$(CONDA) python -m asset_lens ml predict-db $(or $(CODE),sh600519)

.PHONY: ml-predictions
ml-predictions: ## 查看历史预测记录
	@echo "📊 查看历史预测记录..."
	$(CONDA) python -m asset_lens ml predictions

.PHONY: ai-train-adaptive
ai-train-adaptive: ## AI驱动的自适应训练（根据市场行情调整策略）
	@echo "🤖 AI驱动的自适应训练..."
	$(CONDA) python -m asset_lens ml train-adaptive

.PHONY: ml-analyze-market
ml-analyze-market: ## ML分析当前市场行情
	@echo "📊 ML分析市场行情..."
	$(CONDA) python -m asset_lens ml analyze-market

.PHONY: ai-trade
ai-trade: ## 运行AI模拟交易会话
	@echo "🤖 运行AI模拟交易..."
	$(CONDA) python -m asset_lens ml trade

.PHONY: ai-trade-history
ai-trade-history: ## 查看AI模拟交易历史
	@echo "📜 查看交易历史..."
	$(CONDA) python -m asset_lens ml trade-history

.PHONY: ai-portfolio
ai-portfolio: ## 查看AI模拟交易投资组合
	@echo "📊 查看投资组合..."
	$(CONDA) python -m asset_lens ml portfolio

.PHONY: ml-sector
ml-sector: ## ML分析板块轮动情况
	@echo "📊 ML分析板块轮动..."
	$(CONDA) python -m asset_lens ml sector

.PHONY: ml-fund-sector
ml-fund-sector: ## 分析基金所属板块（make ml-fund-sector FUND="易方达科技创新混合"）
ifndef FUND
	@echo "❌ 错误: 需要提供基金名称"
	@echo ""
	@echo "用法: make ml-fund-sector FUND=\"基金名称\""
	@exit 1
endif
	@echo "📊 分析基金板块..."
	$(CONDA) python -m asset_lens ml fund-sector "$(FUND)"

# ============================================
# 数据库管理
# ============================================
.PHONY: db-stats
db-stats: ## 显示数据库统计信息
	@echo "📊 数据库统计..."
	$(CONDA) python -m asset_lens db stats

.PHONY: db-migrate
db-migrate: ## 从JSON缓存迁移数据到数据库
	@echo "📦 迁移数据到数据库..."
	$(CONDA) python -m asset_lens db migrate

.PHONY: db-fetch
db-fetch: ## 获取股票历史数据到数据库（make db-fetch CODES="sh600519 sz000001"）
ifndef CODES
	@echo "❌ 错误: 需要提供股票代码"
	@echo ""
	@echo "用法: make db-fetch CODES=\"sh600519 sz000001\""
	@echo ""
	@echo "示例:"
	@echo "  make db-fetch CODES=\"sh600519\"           # 获取贵州茅台"
	@echo "  make db-fetch CODES=\"sh600519 sz000001\"  # 获取多只股票"
	@exit 1
endif
	@echo "📡 获取股票历史数据..."
	$(CONDA) python -m asset_lens db fetch $(CODES)

.PHONY: db-kline
db-kline: ## 查询股票K线数据（make db-kline CODE=sh600519）
ifndef CODE
	@echo "❌ 错误: 需要提供股票代码"
	@echo ""
	@echo "用法: make db-kline CODE=sh600519"
	@exit 1
endif
	@echo "📊 查询K线数据..."
	$(CONDA) python -m asset_lens db kline $(CODE)

.PHONY: db-codes
db-codes: ## 列出所有有数据的股票代码
	@echo "📋 列出所有股票代码..."
	$(CONDA) python -m asset_lens db codes

.PHONY: db-clean
db-clean: ## 清理旧数据（保留最近365天）
	@echo "🧹 清理旧数据..."
	$(CONDA) python -m asset_lens db clean

.PHONY: db-verify
db-verify: ## 验证数据完整性
	@echo "🔍 验证数据完整性..."
	$(CONDA) python -m asset_lens db verify

.PHONY: db-update-missing
db-update-missing: ## 智能更新缺失或过期的股票数据（make db-update-missing DAYS=250 LIMIT=50）
	@echo "🔄 智能更新缺失股票数据..."
	$(CONDA) python -m asset_lens db update-missing --days $(or $(DAYS),250) --limit $(or $(LIMIT),50)

.PHONY: db-auto-sync
db-auto-sync: ## 智能同步股票历史数据（适合 daily 使用，自动补全数据）
	@echo "🔄 智能同步股票历史数据..."
	$(CONDA) python -m asset_lens db auto-sync --days $(or $(DAYS),180) --daily-limit $(or $(LIMIT),50)

.PHONY: db-clean-old
db-clean-old: ## 清理旧数据，只保留最近N天（make db-clean-old DAYS=180）
	@echo "🧹 清理旧数据..."
	$(CONDA) python -m asset_lens db clean-old --days $(or $(DAYS),180)

.PHONY: db-clean-old-confirm
db-clean-old-confirm: ## 确认执行清理旧数据
	@echo "🧹 确认清理旧数据..."
	$(CONDA) python -m asset_lens db clean-old --days $(or $(DAYS),180) --confirm

.PHONY: db-batch-fetch
db-batch-fetch: ## 批量获取股票历史数据（make db-batch-fetch LIMIT=100 DAYS=250）
	@echo "📦 批量获取股票历史数据..."
	$(CONDA) python scripts/batch_fetch_history.py --limit $(or $(LIMIT),0) --days $(or $(DAYS),250)

.PHONY: db-batch-fetch-all
db-batch-fetch-all: ## 获取所有股票历史数据（耗时较长）
	@echo "📦 获取所有股票历史数据..."
	$(CONDA) python scripts/batch_fetch_history.py --days 250

# ============================================
# 股票跟踪监控
# ============================================
.PHONY: track-record
track-record: ## 记录股票池每日数据
	@echo "📊 记录股票池每日数据..."
	$(CONDA) python -m asset_lens track-stocks --action list

.PHONY: track-detect
track-detect: ## 检测妖股信号
	@echo "📊 检测妖股信号..."
	$(CONDA) python -m asset_lens track-stocks --action list

.PHONY: track-report
track-report: ## 生成跟踪报告
	@echo "📊 生成跟踪报告..."
	$(CONDA) python -m asset_lens track-stocks --action list

# ============================================
# 市场环境分析
# ============================================
.PHONY: market-environment
market-environment: ## 分析市场环境
	@echo "📊 分析市场环境..."
	$(CONDA) python -m asset_lens market-environment --analyze

.PHONY: adapt-strategy
adapt-strategy: ## 适配策略参数（make adapt-strategy STRATEGY=momentum）
	@echo "📊 适配策略参数..."
	$(CONDA) python -m asset_lens market-environment --adapt $(or $(STRATEGY),momentum)

# ============================================
# 个人数据整合
# ============================================
.PHONY: personal-data-load
personal-data-load: ## 加载个人每周数据
	@echo "📊 加载个人每周数据..."
	$(CONDA) python -m asset_lens personal-data load

.PHONY: personal-data-summary
personal-data-summary: ## 显示个人数据市场概况
	@echo "📊 显示个人数据市场概况..."
	$(CONDA) python -m asset_lens personal-data summary

# ============================================
# 定时任务
# ============================================
.PHONY: run-daily-tasks
run-daily-tasks: ## 运行每日任务（立即执行）
	@echo "📊 运行每日任务..."
	$(CONDA) python -m asset_lens run-daily-tasks --run-now

.PHONY: start-scheduler
start-scheduler: ## 启动定时调度器（每日 09:30 自动执行）
	@echo "🚀 启动定时调度器..."
	$(CONDA) python -m asset_lens run-daily-tasks --schedule

.PHONY: task-status
task-status: ## 查看任务状态
	@echo "📊 查看任务状态..."
	$(CONDA) python -m asset_lens task-status

# ============================================
# 投资报告
# ============================================
.PHONY: report-strategy
report-strategy: ## 生成策略报告
	@echo "📊 生成策略报告..."
	$(CONDA) python -m asset_lens report strategy --strategy momentum

.PHONY: report-pool
report-pool: ## 生成股票池报告
	@echo "📊 生成股票池报告..."
	$(CONDA) python -m asset_lens report pool --pool-name momentum

.PHONY: report-comparison
report-comparison: ## 生成策略对比报告
	@echo "📊 生成策略对比报告..."
	$(CONDA) python -m asset_lens report comparison

.PHONY: report-risk
report-risk: ## 生成风险评估报告
	@echo "📊 生成风险评估报告..."
	$(CONDA) python -m asset_lens report risk --pool-name momentum

# ============================================
# 风险管理
# ============================================
.PHONY: risk-summary
risk-summary: ## 查看风险摘要
	@echo "📊 查看风险摘要..."
	$(CONDA) python -m asset_lens risk-summary --pool-name momentum

.PHONY: position-advice
position-advice: ## 获取仓位建议
	@echo "📊 获取仓位建议..."
	$(CONDA) python -m asset_lens position-advice --pool-name momentum --capital 100000

# ============================================
# 配置管理
# ============================================
.PHONY: mode-sample
mode-sample: ## 切换到 sample 模式
	@echo "⚙️  切换到 sample 模式..."
	$(CONDA) python -m asset_lens switch-mode --target-mode sample
	@echo "✅ 已切换到 sample 模式"

.PHONY: mode-real
mode-real: ## 切换到 real 模式
	@echo "⚙️  切换到 real 模式..."
	$(CONDA) python -m asset_lens switch-mode --target-mode real
	@echo "✅ 已切换到 real 模式"

.PHONY: show-config
show-config: ## 显示当前配置
	@echo "📋 当前配置:"
	$(CONDA) python -m asset_lens show-config

# ============================================
# 测试和代码质量
# ============================================
.PHONY: test
test: ## 运行测试（排除网络相关测试，避免卡住）
	@echo "🧪 运行测试..."
	@echo ""
	@echo "⚠️  注意: 测试可能需要 3-5 分钟，请耐心等待..."
	@echo "   - 已排除网络相关测试（websocket, scheduler, http_client）"
	@echo "   - 快速测试请使用: make test-fast"
	@echo ""
	@echo "📋 收集测试用例..."
	@$(CONDA) python -m pytest tests/ --collect-only -q --ignore=tests/test_websocket.py --ignore=tests/test_scheduler.py --ignore=tests/test_scheduler_advanced.py --ignore=tests/test_http_client.py --ignore=tests/test_web_api.py --ignore=tests/test_multi_source_fetcher.py 2>&1 | tail -5
	@echo ""
	@echo "🚀 开始执行测试..."
	@$(CONDA) python -m pytest tests/ -v --tb=short --ignore=tests/test_websocket.py --ignore=tests/test_scheduler.py --ignore=tests/test_scheduler_advanced.py --ignore=tests/test_http_client.py --ignore=tests/test_web_api.py --ignore=tests/test_multi_source_fetcher.py

.PHONY: test-fast
test-fast: ## 快速测试（仅核心模块）
	@echo "🧪 快速测试..."
	@echo "   预计耗时: 10-20 秒"
	@echo ""
	@$(CONDA) python -m pytest tests/test_cli.py tests/test_cli_registration.py tests/test_market_stock_fetcher.py tests/test_report_analyzer.py -v --tb=short

.PHONY: test-all
test-all: ## 运行所有测试（包括网络测试，可能较慢）
	@echo "🧪 运行所有测试..."
	@echo ""
	@echo "⚠️  注意: 包含网络相关测试，可能需要 10+ 分钟"
	@echo "   - WebSocket 测试"
	@echo "   - Scheduler 测试"
	@echo "   - HTTP 客户端测试"
	@echo "   - 如遇卡住，请按 Ctrl+C 终止"
	@echo ""
	@$(CONDA) python -m pytest tests/ -v --tb=short

.PHONY: test-cov
test-cov: ## 运行测试并生成覆盖率报告
	@echo "🧪 运行测试并生成覆盖率报告..."
	@echo ""
	@echo "⚠️  注意: 测试可能需要 3-5 分钟，请耐心等待..."
	@echo ""
	@$(CONDA) python -m pytest tests/ --cov=asset_lens --cov-report=html --cov-report=term -v --tb=short --ignore=tests/test_websocket.py --ignore=tests/test_scheduler.py --ignore=tests/test_scheduler_advanced.py --ignore=tests/test_http_client.py --ignore=tests/test_web_api.py --ignore=tests/test_multi_source_fetcher.py
	@echo "✅ 测试完成，覆盖率报告已生成: htmlcov/index.html"

.PHONY: test-collect
test-collect: ## 收集测试用例（诊断用）
	@echo "📋 收集测试用例..."
	@$(CONDA) python -m pytest tests/ --collect-only -q --ignore=tests/test_websocket.py --ignore=tests/test_scheduler.py --ignore=tests/test_scheduler_advanced.py --ignore=tests/test_http_client.py --ignore=tests/test_web_api.py --ignore=tests/test_multi_source_fetcher.py

.PHONY: lint
lint: ## 运行代码检查（并行执行）
	@echo "🔍 运行代码检查（并行执行）..."
	@$(CONDA) python -m pylint asset_lens/ --disable=all --enable=E,F --exit-zero -j 0; \
	 $(CONDA) python -m mypy asset_lens/ --no-error-summary || true
	@echo "✅ 代码检查完成"

.PHONY: format
format: ## 格式化代码
	@echo "✨ 格式化代码..."
	$(CONDA) python -m black asset_lens/ --line-length 100
	$(CONDA) python -m isort asset_lens/ --profile black
	@echo "✅ 代码格式化完成"

.PHONY: ci
ci: format lint test ## 完整 CI 流程（格式化+检查+测试）
	@echo ""
	@echo "✅ CI 流程完成！"

# ============================================
# 清理命令
# ============================================
.PHONY: clean
clean: ## 清理输出文件
	@echo "🧹 清理输出文件..."
	@find output -name "*.csv" -delete 2>/dev/null || true
	@find output -name "*.json" -delete 2>/dev/null || true
	@echo "✅ 输出文件已清理"

.PHONY: clean-cache
clean-cache: ## 清理缓存文件
	@echo "🧹 清理缓存文件..."
	@rm -rf cache/*.json 2>/dev/null || true
	@echo "✅ 缓存文件已清理"

.PHONY: clean-all
clean-all: clean clean-cache ## 清理所有生成的文件
	@echo "🧹 清理所有生成的文件..."
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@rm -rf __pycache__/ 2>/dev/null || true
	@rm -rf asset_lens/__pycache__/ 2>/dev/null || true
	@rm -rf asset_lens/*/__pycache__/ 2>/dev/null || true
	@rm -rf .mypy_cache/ 2>/dev/null || true
	@rm -rf .ruff_cache/ 2>/dev/null || true
	@echo "✅ 所有生成的文件已清理"

# ============================================
# 其他
# ============================================
.PHONY: status
status: ## 检查项目状态
	@echo ""
	@echo "  ╔════════════════════════════════════════════════════════════╗"
	@echo "  ║                  项目状态检查                               ║"
	@echo "  ╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  1️⃣  Conda 环境:"
	@conda env list | grep $(CONDA_ENV) || echo "     ⚠️  环境 $(CONDA_ENV) 不存在"
	@echo ""
	@echo "  2️⃣  Python 版本:"
	@$(CONDA) python --version
	@echo ""
	@echo "  3️⃣  核心依赖:"
	@$(CONDA) pip list | grep -E "pandas|numpy|scipy|click|pydantic|rich|csvkit" || echo "     ⚠️  某些依赖未安装"
	@echo ""
	@echo "  4️⃣  项目文件:"
	@test -f .env && echo "     ✅ .env 配置文件存在" || echo "     ⚠️  .env 配置文件不存在"
	@test -d data/sample_data && echo "     ✅ 示例数据目录存在" || echo "     ⚠️  示例数据目录不存在"
	@test -d data/real && echo "     ✅ 真实数据目录存在" || echo "     ⚠️  真实数据目录不存在"
	@test -d output && echo "     ✅ 输出目录存在" || echo "     ⚠️  输出目录不存在"
	@test -d cache && echo "     ✅ 缓存目录存在" || echo "     ⚠️  缓存目录不存在"
	@echo ""
	@echo "  5️⃣  市场数据缓存:"
	@test -f cache/market_index_domestic.json && echo "     ✅ 国内市场数据存在" || echo "     ⚠️  国内市场数据不存在"
	@test -f cache/market_index_foreign.json && echo "     ✅ 海外市场数据存在" || echo "     ⚠️  海外市场数据不存在"
	@echo ""

.PHONY: version
version: ## 显示版本信息
	@echo ""
	@echo "  asset-lens v$(VERSION)"
	@echo "  个人资产操作系统"
	@echo ""

.PHONY: backup
backup: ## 备份数据文件
	@echo "💾 备份数据文件..."
	@mkdir -p backup/$(shell date +%Y%m%d)
	@test -d data && cp -r data backup/$(shell date +%Y%m%d)/ || true
	@test -d cache && cp -r cache backup/$(shell date +%Y%m%d)/ || true
	@test -d output && cp -r output backup/$(shell date +%Y%m%d)/ || true
	@echo "✅ 数据已备份到: backup/$(shell date +%Y%m%d)/"

# ============================================
# 数据同步
# ============================================
.PHONY: sync-data
sync-data: ## 同步 ts-demo 真实数据到 asset-lens
	@echo "🔄 同步 ts-demo 数据..."
	$(CONDA) python scripts/sync_data.py

.PHONY: sync-data-latest
sync-data-latest: ## 只同步最新的 ts-demo 数据
	@echo "🔄 同步最新 ts-demo 数据..."
	$(CONDA) python scripts/sync_data.py --latest

.PHONY: sync-data-preview
sync-data-preview: ## 预览同步内容（不实际执行）
	@echo "🔄 预览同步内容..."
	$(CONDA) python scripts/sync_data.py --dry-run

# ============================================
# 快捷命令
# ============================================
.PHONY: run
run: analyze ## 快捷运行分析（等同于 make analyze）

.PHONY: sample
sample: init-sample analyze ## 初始化并运行示例

.PHONY: dev
dev: install-dev format lint test ## 开发流程：安装依赖、格式化、检查、测试

.PHONY: quick
quick: update-market-data-fast estimate-pnl ## 快速查看：更新数据+估算盈亏

# ============================================
# Web Dashboard
# ============================================
.PHONY: web
web: ## 启动 Web Dashboard (默认端口 8000)
	@echo "🌐 启动 Web Dashboard..."
	@echo "📊 Dashboard 地址: http://localhost:8000"
	@echo "📚 API 文档地址: http://localhost:8000/docs"
	@echo ""
	@echo "🛑 检查并关闭 8000 端口上的进程..."
	@pkill -9 -f "uvicorn" 2>/dev/null || true
	@pkill -9 -f "python.*web" 2>/dev/null || true
	@lsof -ti :8000 | xargs kill -9 2>/dev/null || true
	@sleep 2
	@echo "✅ 端口已清理"
	@echo ""
	$(CONDA) python -m uvicorn asset_lens.web:app --host 0.0.0.0 --port 8000

.PHONY: web-port
web-port: ## 启动 Web Dashboard (指定端口, make web-port PORT=9000)
ifndef PORT
	@echo "❌ 错误: 需要提供端口号"
	@echo ""
	@echo "用法: make web-port PORT=9000"
	@exit 1
endif
	@echo "🌐 启动 Web Dashboard (端口: $(PORT))..."
	@echo "📊 Dashboard 地址: http://localhost:$(PORT)"
	@echo "📚 API 文档地址: http://localhost:$(PORT)/docs"
	@echo ""
	$(CONDA) python -m uvicorn asset_lens.web:app --host 0.0.0.0 --port $(PORT)

.PHONY: web-bg
web-bg: ## 后台启动 Web Dashboard
	@echo "🌐 后台启动 Web Dashboard..."
	@echo "📊 Dashboard 地址: http://localhost:8000"
	@echo "📚 API 文档地址: http://localhost:8000/docs"
	@echo ""
	$(CONDA) nohup python -m uvicorn asset_lens.web:app --host 0.0.0.0 --port 8000 > web.log 2>&1 &
	@echo "✅ Web Dashboard 已在后台启动"
	@echo "💡 查看日志: tail -f web.log"
	@echo "💡 停止服务: make web-stop"

.PHONY: web-stop
web-stop: ## 停止 Web Dashboard
	@echo "🛑 停止 Web Dashboard..."
	@pkill -f "python -m uvicorn asset_lens.web:app" 2>/dev/null || true
	@echo "✅ Web Dashboard 已停止"

# ============================================
# 项目自检
# ============================================
.PHONY: check
check: check-privacy check-git check-cache check-size ## 完整自检（隐私+Git+缓存+大小）

.PHONY: check-privacy
check-privacy: ## 检查隐私数据是否被 Git 追踪
	@echo "🔒 检查隐私数据保护..."
	@echo ""
	@echo "=== 检查敏感目录是否被忽略 ==="
	@git check-ignore -v data/real/ 2>/dev/null && echo "✅ data/real/ 已被忽略" || echo "⚠️ data/real/ 未被忽略！"
	@git check-ignore -v cache/ 2>/dev/null && echo "✅ cache/ 已被忽略" || echo "⚠️ cache/ 未被忽略！"
	@git check-ignore -v output/*.csv output/*.json 2>/dev/null && echo "✅ output/*.csv, *.json 已被忽略" || echo "⚠️ output 文件未被忽略！"
	@git check-ignore -v .env 2>/dev/null && echo "✅ .env 已被忽略" || echo "⚠️ .env 未被忽略！"
	@echo ""
	@echo "=== 检查 Git 追踪的敏感文件 ==="
	@tracked=$$(git ls-files | grep -E "money_csv|money_|投资产品|资产汇总|卖出记录|\.env$$" 2>/dev/null); \
	if [ -z "$$tracked" ]; then \
		echo "✅ 没有追踪敏感文件"; \
	else \
		echo "⚠️ 发现追踪的敏感文件:"; \
		echo "$$tracked"; \
	fi
	@echo ""
	@echo "=== 检查代码中的硬编码敏感数据 ==="
	@found=$$(grep -rn "[0-9]\{7,\}" --include="*.py" asset_lens/ 2>/dev/null | grep -v "100000\|10000\|100000000\|test_\|_test\." | head -5); \
	if [ -z "$$found" ]; then \
		echo "✅ 没有发现硬编码的大额数字"; \
	else \
		echo "⚠️ 发现可能的硬编码数据:"; \
		echo "$$found"; \
	fi
	@echo ""
	@echo "🔒 隐私检查完成！"

.PHONY: check-git
check-git: ## 检查 Git 状态
	@echo "📋 检查 Git 状态..."
	@echo ""
	@echo "=== 当前分支 ==="
	@git branch --show-current
	@echo ""
	@echo "=== 未提交的更改 ==="
	@git status --short
	@echo ""
	@echo "=== 最近 5 次提交 ==="
	@git log --oneline -5
	@echo ""
	@echo "📋 Git 检查完成！"

.PHONY: check-cache
check-cache: ## 检查缓存目录
	@echo "🗂️ 检查缓存目录..."
	@echo ""
	@echo "=== cache 目录内容 ==="
	@ls -la cache/ 2>/dev/null || echo "cache/ 目录不存在"
	@echo ""
	@echo "=== 缓存大小 ==="
	@du -sh cache/ 2>/dev/null || echo "无法计算"
	@echo ""
	@echo "=== 空目录 ==="
	@find cache -type d -empty 2>/dev/null | while read dir; do echo "📁 $$dir (空)"; done || echo "无空目录"
	@echo ""
	@echo "🗂️ 缓存检查完成！"

.PHONY: check-size
check-size: ## 检查项目大小
	@echo "📊 检查项目大小..."
	@echo ""
	@echo "=== 项目总大小 ==="
	@du -sh .
	@echo ""
	@echo "=== 主要目录大小 ==="
	@du -sh asset_lens/ cache/ config/ data/ docs/ output/ scripts/ tests/ web-react/ 2>/dev/null | sort -hr
	@echo ""
	@echo "=== 大文件 (>1MB) ==="
	@find . -type f -size +1M -not -path "./.git/*" -not -path "./web-react/node_modules/*" 2>/dev/null | head -10
	@echo ""
	@echo "📊 大小检查完成！"

.PHONY: check-clean
check-clean: ## 清理缓存和临时文件
	@echo "🧹 清理缓存和临时文件..."
	@rm -rf .cache .mypy_cache .pytest_cache htmlcov 2>/dev/null
	@rm -f .coverage coverage.json 2>/dev/null
	@find . -name ".DS_Store" -delete 2>/dev/null
	@rm -rf tests/__pycache__ 2>/dev/null
	@rm -rf asset_lens/**/__pycache__ 2>/dev/null
	@echo "✅ 清理完成！"
	@echo ""
	@du -sh .

.PHONY: check-commands
check-commands: ## 自检所有命令是否正常工作
	@echo ""
	@echo "  ╔════════════════════════════════════════════════════════════╗"
	@echo "  ║                  命令自检                                   ║"
	@echo "  ╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  🔍 检查核心命令..."
	@echo ""
	@echo "  1️⃣  检查 CLI 帮助..."
	@$(CONDA) python -m asset_lens.cli --help > /dev/null 2>&1 && echo "     ✅ CLI 帮助正常" || echo "     ❌ CLI 帮助失败"
	@echo ""
	@echo "  2️⃣  检查配置显示..."
	@$(CONDA) python -m asset_lens.cli show-config > /dev/null 2>&1 && echo "     ✅ 配置显示正常" || echo "     ❌ 配置显示失败"
	@echo ""
	@echo "  3️⃣  检查版本显示..."
	@$(CONDA) python -m asset_lens.cli version > /dev/null 2>&1 && echo "     ✅ 版本显示正常" || echo "     ❌ 版本显示失败"
	@echo ""
	@echo "  4️⃣  检查项目自检..."
	@$(CONDA) python -m asset_lens.cli check > /dev/null 2>&1 && echo "     ✅ 项目自检正常" || echo "     ❌ 项目自检失败"
	@echo ""
	@echo "  5️⃣  检查数据加载..."
	@$(CONDA) python -c "from asset_lens.data.csv_parser import CSVParser; CSVParser.load_data()" > /dev/null 2>&1 && echo "     ✅ 数据加载正常" || echo "     ❌ 数据加载失败"
	@echo ""
	@echo "  6️⃣  检查市场数据获取器..."
	@$(CONDA) python -c "from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher" > /dev/null 2>&1 && echo "     ✅ 市场数据获取器正常" || echo "     ❌ 市场数据获取器失败"
	@echo ""
	@echo "  7️⃣  检查股票筛选器..."
	@$(CONDA) python -c "from asset_lens.strategy.screener import StockScreener; StockScreener()" > /dev/null 2>&1 && echo "     ✅ 股票筛选器正常" || echo "     ❌ 股票筛选器失败"
	@echo ""
	@echo "  8️⃣  检查策略引擎..."
	@$(CONDA) python -c "from asset_lens.strategy.engine import StrategyEngine; StrategyEngine()" > /dev/null 2>&1 && echo "     ✅ 策略引擎正常" || echo "     ❌ 策略引擎失败"
	@echo ""
	@echo "  9️⃣  检查 IRR 计算器..."
	@$(CONDA) python -c "from asset_lens.core.irr_calculator import IRRCalculator; IRRCalculator()" > /dev/null 2>&1 && echo "     ✅ IRR 计算器正常" || echo "     ❌ IRR 计算器失败"
	@echo ""
	@echo "  🔟 检查 Web API..."
	@$(CONDA) python -c "from asset_lens.web.api import app; print('OK')" > /dev/null 2>&1 && echo "     ✅ Web API 正常" || echo "     ❌ Web API 失败"
	@echo ""
	@echo "  ══════════════════════════════════════════════════════════════"
	@echo "  📊 股票基金查询命令..."
	@echo ""
	@echo "  1️⃣1️⃣ 检查股票行情获取..."
	@$(CONDA) python -m asset_lens.cli fetch-stock --help > /dev/null 2>&1 && echo "     ✅ 股票行情获取正常" || echo "     ❌ 股票行情获取失败"
	@echo ""
	@echo "  1️⃣2️⃣ 检查基金净值获取..."
	@$(CONDA) python -m asset_lens.cli fetch-fund --help > /dev/null 2>&1 && echo "     ✅ 基金净值获取正常" || echo "     ❌ 基金净值获取失败"
	@echo ""
	@echo "  1️⃣3️⃣ 检查基金搜索..."
	@$(CONDA) python -m asset_lens.cli search-fund --help > /dev/null 2>&1 && echo "     ✅ 基金搜索正常" || echo "     ❌ 基金搜索失败"
	@echo ""
	@echo "  1️⃣4️⃣ 检查股票筛选..."
	@$(CONDA) python -m asset_lens.cli screen-stocks --help > /dev/null 2>&1 && echo "     ✅ 股票筛选正常" || echo "     ❌ 股票筛选失败"
	@echo ""
	@echo "  1️⃣5️⃣ 检查放量突破..."
	@$(CONDA) python -m asset_lens.cli volume-breakout --help > /dev/null 2>&1 && echo "     ✅ 放量突破正常" || echo "     ❌ 放量突破失败"
	@echo ""
	@echo "  ══════════════════════════════════════════════════════════════"
	@echo "  📈 投资策略系统命令..."
	@echo ""
	@echo "  1️⃣6️⃣ 检查股票池..."
	@$(CONDA) python -m asset_lens.cli stock-pool --help > /dev/null 2>&1 && echo "     ✅ 股票池正常" || echo "     ❌ 股票池失败"
	@echo ""
	@echo "  1️⃣7️⃣ 检查策略管理..."
	@$(CONDA) python -m asset_lens.cli strategy --help > /dev/null 2>&1 && echo "     ✅ 策略管理正常" || echo "     ❌ 策略管理失败"
	@echo ""
	@echo "  1️⃣8️⃣ 检查策略回测..."
	@$(CONDA) python -m asset_lens.cli backtest --help > /dev/null 2>&1 && echo "     ✅ 策略回测正常" || echo "     ❌ 策略回测失败"
	@echo ""
	@echo "  1️⃣9️⃣ 检查投资状态..."
	@$(CONDA) python -m asset_lens.cli investment-status --help > /dev/null 2>&1 && echo "     ✅ 投资状态正常" || echo "     ❌ 投资状态失败"
	@echo ""
	@echo "  2️⃣0️⃣ 检查市场环境..."
	@$(CONDA) python -m asset_lens.cli market-environment --help > /dev/null 2>&1 && echo "     ✅ 市场环境正常" || echo "     ❌ 市场环境失败"
	@echo ""
	@echo "  ✅ 命令自检完成！"

# ============================================
# 周报和风向分析
# ============================================
.PHONY: weekly
weekly: ## 一键生成周报（市场行情+选股+风向分析）
	@echo "📊 生成投资周报..."
	@$(CONDA) python -m asset_lens.cli weekly

.PHONY: weekly-full
weekly-full: ## 完整周报（同步数据+AI分析）
	@echo "📊 生成完整投资周报..."
	@$(CONDA) python -m asset_lens.cli weekly --sync --analyze

.PHONY: sentiment
sentiment: ## 分析市场风向
	@$(CONDA) python -m asset_lens.cli sentiment

# ============================================
# 基金持仓分析
# ============================================
.PHONY: fund-holding
fund-holding: ## 分析高仓位基金持仓汇总（股票仓位>=20%，排除债券类型）
	@echo "📊 分析高仓位基金持仓..."
	@$(CONDA) python scripts/fund_holding_analysis.py --analyze

.PHONY: fund-holding-all
fund-holding-all: ## 分析所有基金持仓（包括低仓位和债券基金）
	@echo "📊 分析所有基金持仓..."
	@$(CONDA) python scripts/fund_holding_analysis.py --all

.PHONY: fund-holding-bond
fund-holding-bond: ## 分析债券类型基金持仓
	@echo "📊 分析债券类型基金持仓..."
	@$(CONDA) python scripts/fund_holding_analysis.py --include-bond

.PHONY: fund-list
fund-list: ## 列出所有投资的基金
	@echo "📋 列出所有基金..."
	@$(CONDA) python scripts/fund_holding_analysis.py --list

.PHONY: fund-detail
fund-detail: ## 查看单只基金持仓明细（make fund-detail CODE=020220）
ifndef CODE
	@echo "❌ 错误: 需要提供基金代码"
	@echo ""
	@echo "用法: make fund-detail CODE=020220"
	@echo ""
	@echo "示例:"
	@echo "  make fund-detail CODE=020220  # 查看国联安沪深300指数增强A"
	@echo "  make fund-detail CODE=004512  # 查看海富通沪深300指数增强C"
	@exit 1
endif
	@echo "📊 查看基金持仓明细..."
	@$(CONDA) python scripts/fund_holding_analysis.py --detail $(CODE)
