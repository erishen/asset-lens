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
	@echo "    make analyze-real     分析投资组合（强制使用 real 模式）"
	@echo "    make calculate        快捷计算收益率"
	@echo "    make calculate-real   快捷计算收益率 (real 模式)"
	@echo "    make weekly           生成周度报告"
	@echo "    make analyze-sold     分析已卖出投资"
	@echo "    make analyze-by-time  按投资时间分组分析"
	@echo "    make ai-analyze       AI 分析投资组合（需要配置 OPENAI_API_KEY）"
	@echo "    make portfolio-metrics 计算投资组合专业指标（夏普比率、最大回撤等）"
	@echo ""
	@echo "  💰 盈亏估算:"
	@echo "    make estimate-pnl     估算日盈亏（基于市场指数）"
	@echo "    make estimate-pnl-weekly 估算周盈亏（基于市场指数）"
	@echo "    make daily            快速日度分析（更新数据+估算盈亏）"
	@echo ""
	@echo "  📈 市场数据:"
	@echo "    make update-market-data    更新市场指数数据（完整历史数据）"
	@echo "    make update-market-data-fast 快速更新市场指数数据（仅实时数据）"
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

.PHONY: analyze-real
analyze-real: ## 分析投资组合（强制使用 real 模式）
	@echo "📊 分析投资组合 (real 模式)..."
	$(CONDA) python -m asset_lens analyze --data-mode real --output-format all

.PHONY: calculate
calculate: ## 快捷计算收益率
	@echo "🔢 计算收益率..."
	$(CONDA) python -m asset_lens calculate

.PHONY: calculate-real
calculate-real: ## 快捷计算收益率 (real 模式)
	@echo "🔢 计算收益率 (real 模式)..."
	$(CONDA) python -m asset_lens calculate --data-mode real

.PHONY: weekly
weekly: ## 生成周度报告
	@echo "📅 生成周度报告..."
	$(CONDA) python -m asset_lens weekly-report

.PHONY: pnl
pnl: ## 实时盈亏计算
	@echo "💰 计算实时盈亏..."
	$(CONDA) python -m asset_lens pnl

.PHONY: estimate-pnl
estimate-pnl: ## 估算日盈亏（基于市场指数）
	@echo "💰 估算日盈亏..."
	$(CONDA) python -m asset_lens estimate-pnl

.PHONY: estimate-pnl-weekly
estimate-pnl-weekly: ## 估算周盈亏（基于市场指数）
	@echo "💰 估算周盈亏..."
	$(CONDA) python -m asset_lens estimate-pnl --weekly

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

.PHONY: daily
daily: update-market-data-fast estimate-pnl ## 快速日度分析（更新数据+估算盈亏）
	@echo ""
	@echo "✅ 日度分析完成！"

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
