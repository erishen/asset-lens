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
all: help

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
	@echo "    make ai-analyze       AI 分析投资组合（需要配置 OPENAI_API_KEY）"
	@echo "    make portfolio-metrics 计算投资组合专业指标（夏普比率、最大回撤等）"
	@echo "    make generate-charts  生成投资分析图表（资产配置、风险分布等）"
	@echo "    make generate-report      生成投资分析报告（PDF）"
	@echo "    make generate-report-ai  生成投资分析报告（PDF，包含 AI 分析）"
	@echo "    make generate-html-report  生成投资分析报告（HTML）"
	@echo "    make generate-html-report-ai 生成投资分析报告（HTML，包含 AI 分析）"
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
	@echo "  📊 投资策略系统:"
	@echo "    make stock-pool-list        列出股票池中的股票"
	@echo "    make stock-pool-status      查看股票池状态"
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
	@echo "    make task-status            查看任务状态"
	@echo ""
	@echo "  ⚙️  配置管理:"
	@echo "    make mode-sample      切换到 sample 模式"
	@echo "    make mode-real        切换到 real 模式"
	@echo "    make show-config      显示当前配置"
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

.PHONY: ai-analyze
ai-analyze: ## AI 分析投资组合（需要配置 OPENAI_API_KEY）
	@echo "🤖 AI 分析投资组合..."
	$(CONDA) python -m asset_lens ai-analyze

.PHONY: portfolio-metrics
portfolio-metrics: ## 计算投资组合专业指标
	@echo "📊 计算投资组合专业指标..."
	$(CONDA) python -m asset_lens portfolio-metrics

.PHONY: generate-charts
generate-charts: ## 生成投资分析图表
	@echo "📊 生成投资分析图表..."
	$(CONDA) python -m asset_lens generate-charts

.PHONY: generate-report
generate-report: ## 生成投资分析报告（PDF）
	@echo "📊 生成投资分析报告..."
	$(CONDA) python -m asset_lens generate-report

.PHONY: generate-report-ai
generate-report-ai: ## 生成投资分析报告（包含 AI 分析）
	@echo "📊 生成投资分析报告（包含 AI 分析）..."
	$(CONDA) python -m asset_lens generate-report --include-ai

.PHONY: generate-html-report
generate-html-report: ## 生成投资分析报告（HTML）
	@echo "📊 生成投资分析报告（HTML）..."
	$(CONDA) python -m asset_lens generate-html-report

.PHONY: generate-html-report-ai
generate-html-report-ai: ## 生成投资分析报告（HTML，包含 AI 分析）
	@echo "📊 生成投资分析报告（HTML，包含 AI 分析）..."
	$(CONDA) python -m asset_lens generate-html-report --include-ai

# ============================================
# 市场数据
# ============================================
.PHONY: update-market-data
update-market-data: ## 更新市场指数数据（使用 Alpha Vantage API，获取完整历史数据）
	@echo "📈 更新市场指数数据（Alpha Vantage API）..."
	$(CONDA) python -m asset_lens update-market-data --api alphavantage

.PHONY: update-market-data-fast
update-market-data-fast: ## 快速更新市场指数数据（使用 Finnhub API，仅实时数据）
	@echo "📈 更新市场指数数据（Finnhub API）..."
	$(CONDA) python -m asset_lens update-market-data --api finnhub

.PHONY: update-market-data-async
update-market-data-async: ## 异步并发更新市场指数数据（推荐）
	@echo "🚀 异步并发更新市场指数数据..."
	$(CONDA) python -m asset_lens update-market-data --async

.PHONY: daily
daily: update-market-data-fast pnl ## 快速日度分析（更新数据+估算盈亏）
	@echo ""
	@echo "✅ 日度分析完成！"

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
	$(CONDA) python -m asset_lens stock-pool list

.PHONY: stock-pool-status
stock-pool-status: ## 查看股票池状态
	@echo "📊 查看股票池状态..."
	$(CONDA) python -m asset_lens stock-pool status

.PHONY: strategy-list
strategy-list: ## 列出所有可用策略
	@echo "📊 列出所有可用策略..."
	$(CONDA) python -m asset_lens strategy list

.PHONY: strategy-show
strategy-show: ## 显示策略详情（make strategy-show NAME=value）
	@echo "📊 显示策略详情..."
	$(CONDA) python -m asset_lens strategy show --name $(NAME)

.PHONY: strategy-set
strategy-set: ## 设置当前策略（make strategy-set NAME=value）
	@echo "📊 设置当前策略..."
	$(CONDA) python -m asset_lens strategy set --name $(NAME)

.PHONY: strategy-screen
strategy-screen: ## 使用策略筛选股票（make strategy-screen NAME=value）
	@echo "📊 使用策略筛选股票..."
	$(CONDA) python -m asset_lens strategy screen --name $(NAME)

.PHONY: backtest
backtest: ## 策略回测（make backtest STRATEGY=value）
	@echo "📊 策略回测..."
	$(CONDA) python -m asset_lens backtest --strategy $(STRATEGY)

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

.PHONY: investment-report
investment-report: ## 生成投资报告
	@echo "📊 生成投资报告..."
	$(CONDA) python -m asset_lens investment-report

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

# ============================================
# 股票跟踪监控
# ============================================
.PHONY: track-record
track-record: ## 记录股票池每日数据
	@echo "📊 记录股票池每日数据..."
	$(CONDA) python -m asset_lens track-stocks record --fetch-market

.PHONY: track-detect
track-detect: ## 检测妖股信号
	@echo "📊 检测妖股信号..."
	$(CONDA) python -m asset_lens track-stocks detect

.PHONY: track-report
track-report: ## 生成跟踪报告
	@echo "📊 生成跟踪报告..."
	$(CONDA) python -m asset_lens track-stocks report

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
	$(CONDA) python -m asset_lens market-environment --adapt $(STRATEGY)

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
test: ## 运行测试（实时显示）
	@echo "🧪 运行测试..."
	python -m pytest -v --tb=short

.PHONY: test-cov
test-cov: ## 运行测试并生成覆盖率报告
	@echo "🧪 运行测试并生成覆盖率报告..."
	$(CONDA) pytest --cov=asset_lens --cov-report=html --cov-report=term
	@echo "✅ 测试完成，覆盖率报告已生成: htmlcov/index.html"

.PHONY: lint
lint: ## 运行代码检查
	@echo "🔍 运行代码检查..."
	$(CONDA) pylint asset_lens/ --disable=C0114,C0115,C0116,W0212,W0613 || true
	$(CONDA) mypy asset_lens/ --ignore-missing-imports || true

.PHONY: format
format: ## 格式化代码
	@echo "✨ 格式化代码..."
	$(CONDA) black asset_lens/ --line-length 100
	$(CONDA) isort asset_lens/ --profile black
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
.PHONY: check
check: ## 检查项目状态
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
