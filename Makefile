# Makefile for asset-lens
# 个人资产操作系统 - Make 命令集成

# 代理设置（解决网络连接问题）
export HTTP_PROXY := http://127.0.0.1:7890
export HTTPS_PROXY := http://127.0.0.1:7890
export http_proxy := http://127.0.0.1:7890
export https_proxy := http://127.0.0.1:7890

# 变量定义
PYTHON := python
CONDA_ENV := asset-lens
CONDA := conda run -n $(CONDA_ENV)
UV := $(CONDA) uv
PROJECT_DIR := $(shell pwd)
VERSION := 1.0.0

# 直接使用 conda 环境中的 Python（避免 conda run 不传递环境变量的问题）
CONDA_PYTHON := /opt/anaconda3/envs/asset-lens/bin/python

# Python 命令
PY := python -m asset_lens

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
	@echo "    make uv-install       使用 uv 安装依赖（更快）"
	@echo "    make uv-sync          使用 uv 同步依赖"
	@echo "    make uv-lock          使用 uv 锁定依赖"
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

.PHONY: uv-install
uv-install: ## 使用 uv 安装依赖（更快）
	@echo "⚡ 使用 uv 安装依赖..."
	$(UV) pip install -e .
	@echo "✅ uv 安装完成"

.PHONY: uv-sync
uv-sync: ## 使用 uv 同步依赖
	@echo "🔄 使用 uv 同步依赖..."
	$(UV) sync
	@echo "✅ uv 同步完成"

.PHONY: uv-lock
uv-lock: ## 使用 uv 锁定依赖
	@echo "🔒 使用 uv 锁定依赖..."
	$(UV) lock
	@echo "✅ uv 锁定完成"

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
	$(PY) init
	@echo "✅ 项目初始化完成"

.PHONY: init-sample
init-sample: ## 初始化示例数据
	@echo "📋 初始化示例数据..."
	$(PY) init-sample
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
	$(PY) analyze --output-format all

.PHONY: calculate
calculate: ## 快捷计算收益率（显示收益率排名前10）
	@echo "🔢 计算收益率..."
	$(PY) calculate

.PHONY: compare
compare: ## 对比不同时期的投资收益变化
	@echo "📊 对比投资收益变化..."
	$(PY) compare

.PHONY: pnl
pnl: ## 实时盈亏估算（基于市场指数）
	@echo "💰 估算日盈亏..."
	$(PY) pnl

.PHONY: pnl-weekly
pnl-weekly: ## 周度盈亏估算（基于市场指数）
	@echo "💰 估算周盈亏..."
	$(PY) pnl --weekly

.PHONY: estimate
estimate: ## 全产品日收益估算（基于预期年化收益率）
	@echo "📊 全产品日收益估算..."
	$(PY) estimate

.PHONY: estimate-weekly
estimate-weekly: ## 全产品周收益估算（基于预期年化收益率）
	@echo "📊 全产品周收益估算..."
	$(PY) estimate --weekly

.PHONY: analyze-sold
analyze-sold: ## 分析已卖出投资
	@echo "📈 分析已卖出投资..."
	$(PY) analyze-sold

.PHONY: analyze-by-time
analyze-by-time: ## 按投资时间分组分析
	@echo "⏱️  按投资时间分组分析..."
	$(PY) analyze-by-time

.PHONY: report
report: ## 生成投资报告
	@echo "📊 生成投资报告..."
	$(PY) investment-report

.PHONY: ai-analyze
ai-analyze: ## AI 分析投资组合（需要配置 API 密钥）
	@echo "🤖 AI 分析投资组合..."
	$(PY) ai-analyze

.PHONY: generate-charts
generate-charts: ## 生成投资分析图表（资产配置、风险分布等）
	@echo "📊 生成投资分析图表..."
	$(PY) chart

.PHONY: generate-report
generate-report: ## 生成投资分析报告（PDF）
	@echo "📊 生成投资分析报告（PDF）..."
	$(PY) generate-report

.PHONY: generate-report-ai
generate-report-ai: ## 生成投资分析报告（PDF，包含 AI 分析）
	@echo "📊 生成投资分析报告（PDF，包含 AI 分析）..."
	$(PY) generate-report --include-ai

.PHONY: generate-html-report
generate-html-report: ## 生成投资分析报告（HTML）
	@echo "📊 生成投资分析报告（HTML）..."
	$(PY) generate-html-report

.PHONY: generate-html-report-ai
generate-html-report-ai: ## 生成投资分析报告（HTML，包含 AI 分析）
	@echo "📊 生成投资分析报告（HTML，包含 AI 分析）..."
	$(PY) generate-html-report --include-ai

# ============================================
# 市场数据
# ============================================
.PHONY: update-market-data
update-market-data: ## 更新市场指数数据
	@echo "📈 更新市场指数数据..."
	$(PY) update-market-data

.PHONY: update-market-data-fast
update-market-data-fast: ## 快速更新市场指数数据（仅关键指数）
	@echo "📈 更新市场指数数据（快速模式）..."
	$(PY) update-market-data --fast

.PHONY: daily
daily: ## 快速日度分析（更新数据+智能同步股票历史+估算盈亏+自动交易信号+基金持仓分析+基本面数据更新）
	@echo ""
	@echo "============================================================"
	@echo "🚀 开始日度分析"
	@echo "============================================================"
	@echo ""
	@echo "📌 步骤 1/6: 📈 更新市场指数数据"
	@$(MAKE) --no-print-directory update-market-data-fast
	@echo ""
	@echo "📌 步骤 2/6: 🔄 智能同步股票历史数据"
	@$(MAKE) --no-print-directory db-auto-sync
	@echo ""
	@echo "📌 步骤 3/6: 📊 更新基本面数据（资金流向）"
	@$(MAKE) --no-print-directory fundamental-update
	@echo ""
	@echo "📌 步骤 4/6: 💰 估算今日盈亏"
	@$(MAKE) --no-print-directory pnl
	@echo ""
	@echo "📌 步骤 5/6: 🤖 自动交易信号（模拟）"
	@$(MAKE) --no-print-directory auto-trade-dry
	@echo ""
	@echo "📌 步骤 6/6: 📊 基金持仓分析"
	@$(MAKE) --no-print-directory fund-holding
	@echo ""
	@echo "============================================================"
	@echo "✅ 日度分析完成！"
	@echo "============================================================"
	@echo ""
	@echo "📊 股票池管理:"
	@echo "  make stock-pool          查看股票池"
	@echo "  make auto-trade          执行自动交易"
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
	@echo "📊 基本面数据:"
	@echo "  make fundamental-status  查看更新状态"
	@echo "  make fundamental-update  每日更新"
	@echo ""
	@echo "  make help                显示所有命令"

# ============================================
# ML数据准备
# ============================================
.PHONY: ml-fetch-stocks
ml-fetch-stocks: ## 获取A股市场股票列表（用于ML训练）
	@echo "📊 获取A股市场股票列表..."
	$(PY) fetch-market-stocks --save

.PHONY: ml-fetch-history
ml-fetch-history: ## 批量获取股票历史K线数据（用于ML训练，make ml-fetch-history LIMIT=50）
ifndef LIMIT
	@echo "📊 批量获取所有股票历史数据..."
	$(PY) fetch-history-batch --use-market-stocks --days 250
else
	@echo "📊 批量获取前 $(LIMIT) 只股票历史数据..."
	$(PY) fetch-history-batch --use-market-stocks --limit $(LIMIT) --days 250
endif

.PHONY: ml-fetch-history-fast
ml-fetch-history-fast: ## 快速获取少量股票历史数据（用于测试，50只）
	@echo "📊 快速获取50只股票历史数据..."
	$(PY) fetch-history-batch --use-market-stocks --limit 50 --days 120 --delay 0.1

.PHONY: ml-prepare-data
ml-prepare-data: ml-fetch-stocks ml-fetch-history-fast ## 准备ML训练数据（获取股票列表+历史数据）
	@echo ""
	@echo "✅ ML训练数据准备完成！"
	@echo ""
	@echo "📊 数据统计:"
	$(PY) db stats
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
	$(PY) fetch-stock $(CODES)

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
	$(PY) fetch-fund $(CODES)

.PHONY: search-fund
search-fund: ## 搜索基金（make search-fund KEYWORD="沪深300"）
ifndef KEYWORD
	@echo "❌ 错误: 需要提供搜索关键词"
	@echo ""
	@echo "用法: make search-fund KEYWORD=\"沪深300\""
	@exit 1
endif
	@echo "🔍 搜索基金..."
	$(PY) search-fund $(KEYWORD)

.PHONY: fetch-portfolio-funds
fetch-portfolio-funds: ## 自动获取投资组合中所有基金的净值
	@echo "📊 自动获取投资组合基金净值..."
	$(PY) fetch-portfolio-funds

.PHONY: update-all-data
update-all-data: ## 一键更新所有数据（市场指数、基金净值、股票行情）
	@echo "📊 更新所有数据..."
	$(PY) update-all-data

.PHONY: filter-stocks
filter-stocks: ## 筛选自己投资的股票
	@echo "📊 筛选自己投资的股票..."
	$(PY) filter-stocks

.PHONY: filter-market-stocks
filter-market-stocks: ## 从市场获取股票列表并筛选
	@echo "📊 从市场获取股票列表并筛选..."
	$(PY) filter-stocks --fetch-market

.PHONY: volume-breakout
volume-breakout: ## 筛选放量突破股票
	@echo "📊 筛选放量突破股票..."
	$(PY) volume-breakout

.PHONY: screen-stocks
screen-stocks: ## 股票综合筛选（基本面+技术面+评分）
	@echo "📊 股票综合筛选..."
	$(PY) screen-stocks

.PHONY: screen-fundamental
screen-fundamental: ## 仅基本面筛选
	@echo "📊 基本面筛选..."
	$(PY) screen-stocks --strategy value

.PHONY: screen-technical
screen-technical: ## 仅技术面筛选
	@echo "📊 技术面筛选..."
	$(PY) screen-stocks --strategy momentum

.PHONY: predict-etf
predict-etf: ## 预测ETF表现（make predict-etf CODE=510300）
	@echo "📊 预测ETF表现..."
	$(PY) predict-etf

# ============================================
# 投资策略系统
# ============================================
.PHONY: stock-pool
stock-pool: ## 查看股票池
	@echo "📊 查看股票池..."
	$(PY) stock-pool

.PHONY: strategy-list
strategy-list: ## 列出所有可用策略
	@echo "📊 列出所有可用策略..."
	$(PY) strategy

.PHONY: strategy-show
strategy-show: ## 显示策略详情（make strategy-show NAME=momentum）
	@echo "📊 显示策略详情..."
	$(PY) strategy --strategy-name $(or $(NAME),momentum)

.PHONY: strategy-screen
strategy-screen: ## 使用策略筛选股票（make strategy-screen STRATEGY=momentum）
	@echo "📊 使用策略筛选股票..."
	$(PY) screen-stocks --strategy $(or $(STRATEGY),momentum)

.PHONY: backtest
backtest: ## 策略回测（make backtest STRATEGY=momentum）
	@echo "📊 策略回测..."
	$(PY) backtest --strategy $(or $(STRATEGY),momentum)

.PHONY: investment-status
investment-status: ## 查看投资系统状态
	@echo "📊 查看投资系统状态..."
	$(PY) investment-status

.PHONY: optimize-strategy
optimize-strategy: ## 策略优化（找出最佳策略）
	@echo "📊 策略优化..."
	$(PY) optimize-strategy

# ============================================
# 动量策略选股
# ============================================
.PHONY: momentum-screen
momentum-screen: ## 动量策略选股
	@echo "📊 动量策略选股..."
	$(PY) momentum-screen

.PHONY: momentum-screen-pool
momentum-screen-pool: ## 动量策略选股并添加到股票池
	@echo "📊 动量策略选股并添加到股票池..."
	$(PY) momentum-screen --add-to-pool

.PHONY: auto-trade
auto-trade: ## 自动交易 - 根据策略信号自动买入卖出
	@echo "🤖 自动交易系统"
	$(PY) auto-trade

.PHONY: auto-trade-dry
auto-trade-dry: ## 自动交易（仅显示信号，不执行）
	@echo "🤖 自动交易系统（模拟模式）"
	$(PY) auto-trade --dry-run

.PHONY: auto-trade-ai
auto-trade-ai: ## 自动交易 + AI 分析辅助决策
	@echo "🤖 自动交易系统（AI 增强版）"
	$(PY) auto-trade --use-ai

.PHONY: auto-trade-ai-dry
auto-trade-ai-dry: ## 自动交易 + AI 分析（仅显示信号，不执行）
	@echo "🤖 自动交易系统（AI 增强版，模拟模式）"
	$(PY) auto-trade --use-ai --dry-run

# ============================================
# 机器学习
# ============================================
.PHONY: ml-status
ml-status: ## 查看 ML 模块状态
	@echo "🤖 ML 模块状态..."
	$(PY) ml status

.PHONY: ml-train
ml-train: ## 训练机器学习模型
	@echo "🤖 训练机器学习模型..."
	$(PY) ml train

.PHONY: ml-predict
ml-predict: ## 使用模型预测股票（make ml-predict CODE=sh600519）
	@echo "🔮 预测股票..."
	$(PY) ml predict --code $(or $(CODE),sh600519)

.PHONY: ml-importance
ml-importance: ## 查看模型特征重要性
	@echo "📊 特征重要性分析..."
	$(PY) ml importance

.PHONY: ml-train-db
ml-train-db: ## 从数据库训练模型
	@echo "🤖 从数据库训练模型..."
	$(PY) ml train-db

.PHONY: ml-predict-db
ml-predict-db: ## 从数据库预测股票（make ml-predict-db CODE=sh600519）
	@echo "🔮 从数据库预测股票..."
	$(PY) ml predict-db $(or $(CODE),sh600519)

.PHONY: ml-predictions
ml-predictions: ## 查看历史预测记录
	@echo "📊 查看历史预测记录..."
	$(PY) ml predictions

.PHONY: ai-train-adaptive
ai-train-adaptive: ## AI驱动的自适应训练（根据市场行情调整策略）
	@echo "🤖 AI驱动的自适应训练..."
	$(PY) ml train-adaptive

.PHONY: ml-analyze-market
ml-analyze-market: ## ML分析当前市场行情
	@echo "📊 ML分析市场行情..."
	$(PY) ml analyze-market

.PHONY: ai-trade
ai-trade: ## 运行AI模拟交易会话
	@echo "🤖 运行AI模拟交易..."
	$(PY) ml trade

.PHONY: ai-trade-history
ai-trade-history: ## 查看AI模拟交易历史
	@echo "📜 查看交易历史..."
	$(PY) ml trade-history

.PHONY: ai-portfolio
ai-portfolio: ## 查看AI模拟交易投资组合
	@echo "📊 查看投资组合..."
	$(PY) ml portfolio

.PHONY: ml-sector
ml-sector: ## ML分析板块轮动情况
	@echo "📊 ML分析板块轮动..."
	$(PY) ml sector

.PHONY: ml-fund-sector
ml-fund-sector: ## 分析基金所属板块（make ml-fund-sector FUND="易方达科技创新混合"）
ifndef FUND
	@echo "❌ 错误: 需要提供基金名称"
	@echo ""
	@echo "用法: make ml-fund-sector FUND=\"基金名称\""
	@exit 1
endif
	@echo "📊 分析基金板块..."
	$(PY) ml fund-sector "$(FUND)"

# ============================================
# 高级机器学习
# ============================================
.PHONY: ml-optimize
ml-optimize: ## 使用 Optuna 优化超参数（make ml-optimize MODEL=lightgbm TRIALS=50）
	@echo "🔧 超参数优化..."
	$(PY) ml-advanced optimize --model $(or $(MODEL),lightgbm) --trials $(or $(TRIALS),50)

.PHONY: ml-train-cv
ml-train-cv: ## 使用时间序列交叉验证训练模型（make ml-train-cv MODEL=lightgbm）
	@echo "🎯 交叉验证训练..."
	$(PY) ml-advanced train --model $(or $(MODEL),lightgbm)

.PHONY: ml-train-optimize
ml-train-optimize: ## 优化超参数后训练模型
	@echo "🎯 优化后训练..."
	$(PY) ml-advanced train --model $(or $(MODEL),lightgbm) --optimize

.PHONY: ml-explain
ml-explain: ## 使用 SHAP 解释模型预测
	@echo "📊 模型解释..."
	$(PY) ml-advanced explain

.PHONY: ml-select-features
ml-select-features: ## 特征选择（make ml-select-features K=50）
	@echo "🔍 特征选择..."
	$(PY) ml-advanced select-features --k $(or $(K),50)

.PHONY: ml-ensemble
ml-ensemble: ## 训练集成模型
	@echo "🤖 训练集成模型..."
	$(PY) ml-advanced ensemble

.PHONY: ml-compare
ml-compare: ## 比较不同模型性能
	@echo "📊 模型性能比较..."
	$(PY) ml-advanced compare

# ============================================
# ML 训练和回测
# ============================================
.PHONY: ml-train-opt
ml-train-opt: ## 训练模型（含超参数优化，make ml-train-opt MODEL=lightgbm TRIALS=50）
	@echo "🚀 训练模型（含优化）..."
	$(PY) ml-train train --model $(or $(MODEL),lightgbm) --optimize --trials $(or $(TRIALS),50)

.PHONY: ml-train-ensemble
ml-train-ensemble: ## 训练集成模型（LightGBM + XGBoost）
	@echo "🔀 训练集成模型..."
	$(PY) ml-train ensemble

.PHONY: ml-backtest
ml-backtest: ## 运行 ML 模型回测
	@echo "📊 运行 ML 模型回测..."
	$(PY) ml-train backtest --capital $(or $(CAPITAL),100000)

.PHONY: ml-validate
ml-validate: ## 验证信号有效性
	@echo "📊 验证信号有效性..."
	$(PY) ml-train validate

.PHONY: ml-optimize-all
ml-optimize-all: ## 优化所有模型超参数
	@echo "🔧 优化所有模型超参数..."
	$(PY) ml-train optimize --trials $(or $(TRIALS),100)

# ============================================
# 基本面数据更新
# ============================================
.PHONY: fundamental-status
fundamental-status: ## 查看基本面数据更新状态
	@echo "📊 查看基本面数据更新状态..."
	PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m asset_lens.data.update_fundamental_data --mode status

.PHONY: fundamental-update
fundamental-update: ## 每日更新基本面数据（资金流向）
	@echo "📊 每日更新基本面数据..."
	PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m asset_lens.data.update_fundamental_data --mode daily

.PHONY: fundamental-update-full
fundamental-update-full: ## 全量更新基本面数据（PE/PB/ROE+资金流向）
	@echo "📊 全量更新基本面数据..."
	PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m asset_lens.data.update_fundamental_data --mode full

.PHONY: fundamental-update-incremental
fundamental-update-incremental: ## 增量更新基本面数据
	@echo "📊 增量更新基本面数据..."
	PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m asset_lens.data.update_fundamental_data --mode incremental

.PHONY: fundamental-cleanup
fundamental-cleanup: ## 清理过期的基本面数据缓存
	@echo "🧹 清理过期的基本面数据缓存..."
	PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m asset_lens.data.update_fundamental_data --mode cleanup --days 30

# ============================================
# 数据库管理
# ============================================
.PHONY: db-stats
db-stats: ## 显示数据库统计信息
	@echo "📊 数据库统计..."
	$(PY) db stats

.PHONY: db-migrate
db-migrate: ## 从JSON缓存迁移数据到数据库
	@echo "📦 迁移数据到数据库..."
	$(PY) db migrate

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
	$(PY) db fetch $(CODES)

.PHONY: db-kline
db-kline: ## 查询股票K线数据（make db-kline CODE=sh600519）
ifndef CODE
	@echo "❌ 错误: 需要提供股票代码"
	@echo ""
	@echo "用法: make db-kline CODE=sh600519"
	@exit 1
endif
	@echo "📊 查询K线数据..."
	$(PY) db kline $(CODE)

.PHONY: db-codes
db-codes: ## 列出所有有数据的股票代码
	@echo "📋 列出所有股票代码..."
	$(PY) db codes

.PHONY: db-clean
db-clean: ## 清理旧数据（保留最近365天）
	@echo "🧹 清理旧数据..."
	$(PY) db clean

.PHONY: db-verify
db-verify: ## 验证数据完整性
	@echo "🔍 验证数据完整性..."
	$(PY) db verify

.PHONY: db-update-missing
db-update-missing: ## 智能更新缺失或过期的股票数据（make db-update-missing DAYS=250 LIMIT=50）
	@echo "🔄 智能更新缺失股票数据..."
	$(PY) db update-missing --days $(or $(DAYS),250) --limit $(or $(LIMIT),50)

.PHONY: db-auto-sync
db-auto-sync: ## 智能同步股票历史数据（适合 daily 使用，自动补全数据）
	@echo "🔄 智能同步股票历史数据..."
	$(PY) db auto-sync --fast --days $(or $(DAYS),180) --daily-limit $(or $(LIMIT),50)

.PHONY: db-clean-old
db-clean-old: ## 清理旧数据，只保留最近N天（make db-clean-old DAYS=180）
	@echo "🧹 清理旧数据..."
	$(PY) db clean-old --days $(or $(DAYS),180)

.PHONY: db-clean-old-confirm
db-clean-old-confirm: ## 确认执行清理旧数据
	@echo "🧹 确认清理旧数据..."
	$(PY) db clean-old --days $(or $(DAYS),180) --confirm

.PHONY: db-batch-fetch
db-batch-fetch: ## 批量获取股票历史数据（make db-batch-fetch LIMIT=100 DAYS=250）
	@echo "📦 批量获取股票历史数据..."
	python scripts/batch_fetch_history.py --limit $(or $(LIMIT),0) --days $(or $(DAYS),250)

.PHONY: db-batch-fetch-all
db-batch-fetch-all: ## 获取所有股票历史数据（耗时较长）
	@echo "📦 获取所有股票历史数据..."
	python scripts/batch_fetch_history.py --days 250

# ============================================
# 股票跟踪监控
# ============================================
.PHONY: track-record
track-record: ## 记录股票池每日数据
	@echo "📊 记录股票池每日数据..."
	$(PY) track-stocks

# ============================================
# 市场环境分析
# ============================================
.PHONY: market-environment
market-environment: ## 分析市场环境
	@echo "📊 分析市场环境..."
	$(PY) market-environment

# ============================================
# 个人数据整合
# ============================================
.PHONY: personal-data
personal-data: ## 加载并显示个人数据
	@echo "📊 加载个人数据..."
	$(PY) personal-data

# ============================================
# 定时任务
# ============================================
.PHONY: run-daily-tasks
run-daily-tasks: ## 运行每日任务
	@echo "📊 运行每日任务..."
	$(PY) run-daily-tasks

# ============================================
# 配置管理
# ============================================
.PHONY: mode-sample
mode-sample: ## 切换到 sample 模式
	@echo "⚙️  切换到 sample 模式..."
	$(PY) switch-mode --target-mode sample
	@echo "✅ 已切换到 sample 模式"

.PHONY: mode-real
mode-real: ## 切换到 real 模式
	@echo "⚙️  切换到 real 模式..."
	$(PY) switch-mode --target-mode real
	@echo "✅ 已切换到 real 模式"

.PHONY: show-config
show-config: ## 显示当前配置
	@echo "📋 当前配置:"
	$(PY) show-config

# ============================================
# 测试和代码质量
# ============================================
.PHONY: test
test: ## 运行测试（排除网络相关测试，避免卡住）
	@echo "🧪 运行测试..."
	@echo "   正在启动测试进程..."
	@PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m pytest tests/ --tb=short

.PHONY: test-fast
test-fast: ## 快速测试（仅核心模块）
	@echo "🧪 快速测试..."
	@PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m pytest tests/test_cli.py tests/test_cli_registration.py tests/test_market_stock_fetcher.py tests/test_report_analyzer.py

.PHONY: test-all
test-all: ## 运行所有测试（包括网络测试，可能较慢）
	@echo "🧪 运行所有测试..."
	@PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m pytest tests/ --ignore=

.PHONY: test-cov
test-cov: ## 运行测试并生成覆盖率报告
	@echo "🧪 运行测试并生成覆盖率报告..."
	@PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m pytest tests/ --cov=asset_lens --cov-report=html --cov-report=term
	@echo "✅ 测试完成，覆盖率报告已生成: htmlcov/index.html"

.PHONY: test-verbose
test-verbose: ## 运行测试（详细输出）
	@echo "🧪 运行测试（详细模式）..."
	@PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m pytest tests/ -v --tb=long

.PHONY: test-failed
test-failed: ## 只运行上次失败的测试
	@echo "🧪 运行上次失败的测试..."
	@PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m pytest tests/ --lf

.PHONY: test-collect
test-collect: ## 收集测试用例（诊断用）
	@echo "📋 收集测试用例..."
	@PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore -m pytest tests/ --collect-only

.PHONY: lint
lint: ## 运行代码检查（并行执行）
	@echo "🔍 运行代码检查（并行执行）..."
	@python -m pylint asset_lens/ --disable=all --enable=E,F --exit-zero -j 0; \
	 python -m mypy asset_lens/ --no-error-summary || true
	@echo "✅ 代码检查完成"

.PHONY: format
format: ## 格式化代码
	@echo "✨ 格式化代码..."
	python -m black asset_lens/ --line-length 100
	python -m isort asset_lens/ --profile black
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
	@$(PY) --version
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
	python scripts/sync_data.py

.PHONY: sync-data-latest
sync-data-latest: ## 只同步最新的 ts-demo 数据
	@echo "🔄 同步最新 ts-demo 数据..."
	python scripts/sync_data.py --latest

.PHONY: sync-data-preview
sync-data-preview: ## 预览同步内容（不实际执行）
	@echo "🔄 预览同步内容..."
	python scripts/sync_data.py --dry-run

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
	$(PY) -m uvicorn asset_lens.web:app --host 0.0.0.0 --port 8000

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
	$(PY) -m uvicorn asset_lens.web:app --host 0.0.0.0 --port $(PORT)

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
	@$(PY) --help > /dev/null 2>&1 && echo "     ✅ CLI 帮助正常" || echo "     ❌ CLI 帮助失败"
	@echo ""
	@echo "  2️⃣  检查配置显示..."
	@$(PY) show-config > /dev/null 2>&1 && echo "     ✅ 配置显示正常" || echo "     ❌ 配置显示失败"
	@echo ""
	@echo "  3️⃣  检查版本显示..."
	@$(PY) version > /dev/null 2>&1 && echo "     ✅ 版本显示正常" || echo "     ❌ 版本显示失败"
	@echo ""
	@echo "  4️⃣  检查项目自检..."
	@$(PY) check > /dev/null 2>&1 && echo "     ✅ 项目自检正常" || echo "     ❌ 项目自检失败"
	@echo ""
	@echo "  5️⃣  检查数据加载..."
	@$(PY) -c "from asset_lens.data.csv_parser import CSVParser; CSVParser.load_data()" > /dev/null 2>&1 && echo "     ✅ 数据加载正常" || echo "     ❌ 数据加载失败"
	@echo ""
	@echo "  6️⃣  检查市场数据获取器..."
	@$(PY) -c "from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher" > /dev/null 2>&1 && echo "     ✅ 市场数据获取器正常" || echo "     ❌ 市场数据获取器失败"
	@echo ""
	@echo "  7️⃣  检查股票筛选器..."
	@$(PY) -c "from asset_lens.strategy.screener import StockScreener; StockScreener()" > /dev/null 2>&1 && echo "     ✅ 股票筛选器正常" || echo "     ❌ 股票筛选器失败"
	@echo ""
	@echo "  8️⃣  检查策略引擎..."
	@$(PY) -c "from asset_lens.strategy.engine import StrategyEngine; StrategyEngine()" > /dev/null 2>&1 && echo "     ✅ 策略引擎正常" || echo "     ❌ 策略引擎失败"
	@echo ""
	@echo "  9️⃣  检查 IRR 计算器..."
	@$(PY) -c "from asset_lens.core.irr_calculator import IRRCalculator; IRRCalculator()" > /dev/null 2>&1 && echo "     ✅ IRR 计算器正常" || echo "     ❌ IRR 计算器失败"
	@echo ""
	@echo "  🔟 检查 Web API..."
	@$(PY) -c "from asset_lens.web.api import app; print('OK')" > /dev/null 2>&1 && echo "     ✅ Web API 正常" || echo "     ❌ Web API 失败"
	@echo ""
	@echo "  ══════════════════════════════════════════════════════════════"
	@echo "  📊 股票基金查询命令..."
	@echo ""
	@echo "  1️⃣1️⃣ 检查股票行情获取..."
	@$(PY) fetch-stock --help > /dev/null 2>&1 && echo "     ✅ 股票行情获取正常" || echo "     ❌ 股票行情获取失败"
	@echo ""
	@echo "  1️⃣2️⃣ 检查基金净值获取..."
	@$(PY) fetch-fund --help > /dev/null 2>&1 && echo "     ✅ 基金净值获取正常" || echo "     ❌ 基金净值获取失败"
	@echo ""
	@echo "  1️⃣3️⃣ 检查基金搜索..."
	@$(PY) search-fund --help > /dev/null 2>&1 && echo "     ✅ 基金搜索正常" || echo "     ❌ 基金搜索失败"
	@echo ""
	@echo "  1️⃣4️⃣ 检查股票筛选..."
	@$(PY) screen-stocks --help > /dev/null 2>&1 && echo "     ✅ 股票筛选正常" || echo "     ❌ 股票筛选失败"
	@echo ""
	@echo "  1️⃣5️⃣ 检查放量突破..."
	@$(PY) volume-breakout --help > /dev/null 2>&1 && echo "     ✅ 放量突破正常" || echo "     ❌ 放量突破失败"
	@echo ""
	@echo "  ══════════════════════════════════════════════════════════════"
	@echo "  📈 投资策略系统命令..."
	@echo ""
	@echo "  1️⃣6️⃣ 检查股票池..."
	@$(PY) stock-pool --help > /dev/null 2>&1 && echo "     ✅ 股票池正常" || echo "     ❌ 股票池失败"
	@echo ""
	@echo "  1️⃣7️⃣ 检查策略管理..."
	@$(PY) strategy --help > /dev/null 2>&1 && echo "     ✅ 策略管理正常" || echo "     ❌ 策略管理失败"
	@echo ""
	@echo "  1️⃣8️⃣ 检查策略回测..."
	@$(PY) backtest --help > /dev/null 2>&1 && echo "     ✅ 策略回测正常" || echo "     ❌ 策略回测失败"
	@echo ""
	@echo "  1️⃣9️⃣ 检查投资状态..."
	@$(PY) investment-status --help > /dev/null 2>&1 && echo "     ✅ 投资状态正常" || echo "     ❌ 投资状态失败"
	@echo ""
	@echo "  2️⃣0️⃣ 检查市场环境..."
	@$(PY) market-environment --help > /dev/null 2>&1 && echo "     ✅ 市场环境正常" || echo "     ❌ 市场环境失败"
	@echo ""
	@echo "  ✅ 命令自检完成！"

# ============================================
# 周报和风向分析
# ============================================
.PHONY: weekly
weekly: ## 一键生成周报（市场行情+选股+风向分析）
	@echo "📊 生成投资周报..."
	@$(PY) weekly

.PHONY: weekly-full
weekly-full: ## 完整周报（同步数据+AI分析）
	@echo "📊 生成完整投资周报..."
	@$(PY) weekly --sync --analyze

.PHONY: sentiment
sentiment: ## 分析市场风向
	@$(PY) sentiment

# ============================================
# 基金持仓分析
# ============================================
.PHONY: fund-holding
fund-holding: ## 分析高仓位基金持仓汇总（股票仓位>=20%，排除债券类型）
	@echo "📊 分析高仓位基金持仓..."
	@PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore scripts/fund_holding_analysis.py --analyze

.PHONY: fund-holding-all
fund-holding-all: ## 分析所有基金持仓（包括低仓位和债券基金）
	@echo "📊 分析所有基金持仓..."
	@PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore scripts/fund_holding_analysis.py --all

.PHONY: fund-holding-bond
fund-holding-bond: ## 分析债券类型基金持仓
	@echo "📊 分析债券类型基金持仓..."
	@PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python -W ignore scripts/fund_holding_analysis.py --include-bond

.PHONY: fund-list
fund-list: ## 列出所有投资的基金
	@echo "📋 列出所有基金..."
	@python scripts/fund_holding_analysis.py --list

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
	@python scripts/fund_holding_analysis.py --detail $(CODE)

# ============================================
# 数据库优化
# ============================================
.PHONY: db-optimize
db-optimize: ## 优化数据库性能（WAL模式+索引+PRAGMA优化）
	@echo "⚡ 优化数据库性能..."
	$(PY) db optimize

.PHONY: db-indexes
db-indexes: ## 查看数据库索引
	@echo "📋 查看数据库索引..."
	$(PY) db indexes

.PHONY: db-benchmark
db-benchmark: ## 基准测试查询性能（make db-benchmark QUERY="SELECT COUNT(*) FROM stock_klines"）
ifndef QUERY
	@echo "❌ 错误: 需要提供查询语句"
	@echo ""
	@echo "用法: make db-benchmark QUERY=\"SELECT COUNT(*) FROM stock_klines\""
	@exit 1
endif
	@echo "📊 基准测试查询性能..."
	$(PY) db benchmark "$(QUERY)"

.PHONY: db-vacuum
db-vacuum: ## 清理数据库碎片，释放空间
	@echo "🧹 清理数据库碎片..."
	$(PY) db vacuum

# ============================================
# 风险预警系统
# ============================================
.PHONY: risk-status
risk-status: ## 查看风险预警状态
	@echo "📊 查看风险预警状态..."
	$(PY) risk status

.PHONY: risk-alerts
risk-alerts: ## 显示最近的预警列表（make risk-alerts HOURS=24）
	@echo "🚨 显示最近的预警列表..."
	$(PY) risk alerts --hours $(or $(HOURS),24)

.PHONY: risk-check
risk-check: ## 运行风险检查
	@echo "🔍 运行风险检查..."
	$(PY) risk check

.PHONY: risk-report
risk-report: ## 生成风险预警报告
	@echo "📊 生成风险预警报告..."
	$(PY) risk report

.PHONY: risk-config
risk-config: ## 配置风险预警阈值
	@echo "⚙️ 配置风险预警阈值..."
	$(PY) risk config

.PHONY: risk-clear
risk-clear: ## 清除所有预警
	@echo "🧹 清除所有预警..."
	$(PY) risk clear

# ============================================
# 通知系统
# ============================================
.PHONY: notify-status
notify-status: ## 显示通知服务状态
	@echo "📊 显示通知服务状态..."
	$(PY) notify status

.PHONY: notify-send
notify-send: ## 发送通知（make notify-send TITLE="标题" CONTENT="内容"）
ifndef TITLE
	@echo "❌ 错误: 需要提供标题"
	@echo ""
	@echo "用法: make notify-send TITLE=\"标题\" CONTENT=\"内容\""
	@exit 1
endif
	@echo "📤 发送通知..."
	$(PY) notify send "$(TITLE)" "$(CONTENT)"

.PHONY: notify-test
notify-test: ## 测试通知渠道（make notify-test CHANNEL=dingtalk）
ifndef CHANNEL
	@echo "❌ 错误: 需要提供渠道名称"
	@echo ""
	@echo "用法: make notify-test CHANNEL=dingtalk"
	@echo ""
	@echo "可用渠道: dingtalk, wecom, telegram, feishu, serverchan"
	@exit 1
endif
	@echo "🧪 测试通知渠道..."
	$(PY) notify test $(CHANNEL)

.PHONY: notify-history
notify-history: ## 显示通知历史
	@echo "📋 显示通知历史..."
	$(PY) notify history

# ============================================
# 定时任务调度器
# ============================================
.PHONY: scheduler-start
scheduler-start: ## 启动调度器
	@echo "▶️ 启动调度器..."
	$(PY) scheduler start

.PHONY: scheduler-stop
scheduler-stop: ## 停止调度器
	@echo "⏹️ 停止调度器..."
	$(PY) scheduler stop

.PHONY: scheduler-status
scheduler-status: ## 显示调度器状态
	@echo "📊 显示调度器状态..."
	$(PY) scheduler status

.PHONY: scheduler-run
scheduler-run: ## 手动运行任务（make scheduler-run TASK=risk_check）
ifndef TASK
	@echo "❌ 错误: 需要提供任务名称"
	@echo ""
	@echo "用法: make scheduler-run TASK=risk_check"
	@echo ""
	@echo "可用任务: update_data, risk_check, backup, daily_report"
	@exit 1
endif
	@echo "▶️ 运行任务..."
	$(PY) scheduler run $(TASK)

.PHONY: scheduler-list
scheduler-list: ## 列出所有可用任务
	@echo "📋 列出所有可用任务..."
	$(PY) scheduler list-tasks

.PHONY: scheduler-history
scheduler-history: ## 显示任务执行历史（make scheduler-history TASK=risk_check）
ifndef TASK
	@echo "❌ 错误: 需要提供任务名称"
	@echo ""
	@echo "用法: make scheduler-history TASK=risk_check"
	@exit 1
endif
	@echo "📋 显示任务执行历史..."
	$(PY) scheduler history $(TASK)
