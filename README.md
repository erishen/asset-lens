# asset-lens

> A personal asset operating system built with Python.

---

## 🚀 Quick Start

```bash
# 1. Install
make setup

# 2. Daily data update & P&L estimation
make daily

# 3. View analysis report
make analyze
```

---

## Installation

### Prerequisites

- Python 3.11–3.13
- conda (recommended) or pip

### 1. Clone & Install

```bash
git clone https://github.com/erishen/asset-lens.git
cd asset-lens

# Using conda (recommended)
make setup

# Using pip
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m asset_lens system init
```

**Verify:**
```bash
python -m asset_lens --version
```

### 2. Daily Usage

```bash
make daily
```

### 3. View Analysis

```bash
make analyze           # Portfolio analysis
make ai-analyze        # AI-powered analysis (requires API key)
make weekly            # Weekly report
```

---

## Project Structure

```
asset-lens/
├── asset_lens/          # Python module
│   ├── cli.py           # CLI entry
│   ├── core/            # Core calculations
│   ├── data/            # Data fetching & processing
│   ├── ml/              # Machine learning models
│   ├── strategy/        # Investment strategies
│   └── analysis/        # Portfolio analysis
├── scripts/             # Utility scripts (safe subset)
├── config/              # Configuration files
├── tests/               # Test suite
└── Makefile             # Command entry points
```

---

## Core Commands

| Command | Description | Frequency |
|---------|-------------|-----------|
| `make setup` | Full installation | Once |
| `make daily` | Data update + P&L estimation | Daily |
| `make analyze` | Portfolio analysis | On demand |
| `make weekly` | Weekly report | Weekly |
| `make ai-analyze` | AI deep analysis | On demand |
| `make ml-train-db` | Train ML models | Weekly |
| `make ml-predict` | ML prediction | On demand |
| `make test` | Run tests | Development |
| `make lint` | Code linting | Development |

---

## Quantitative Toolkit (`quant`)

A dependency-light quantitative layer (only numpy / scipy / pandas) for portfolio risk and optimization.
All commands accept `--returns <csv>` (first column = date, remaining columns = per-period returns per asset);
omit it to try built-in deterministic demo data. Risk figures are **positive = loss** (e.g. `CVaR=0.03` means
a 3% average tail loss).

```bash
python -m asset_lens quant cvar --returns returns.csv --level 0.95
python -m asset_lens quant optimize --objective min_variance        # also: max_sharpe / min_cvar / target_return / frontier
python -m asset_lens quant simulate --method bootstrap --paths 1000 --horizon 252
python -m asset_lens quant mpc --lookback 60 --rebalance-every 5 --cost 0.001
```

| Method | CLI | What it does |
|--------|-----|--------------|
| CVaR | `quant cvar` / `optimize --objective min_cvar` | Historical & parametric CVaR; Rockafellar-Uryasev LP for minimum-CVaR weights |
| Markowitz | `quant optimize` / `frontier` | Min-variance, max-Sharpe, target-return (SLSQP) and efficient frontier |
| Monte Carlo | `quant simulate` | GBM & block-bootstrap paths, terminal VaR / CVaR / loss probability (seeded, reproducible) |
| MPC | `quant mpc` | Rolling-horizon rebalancing with transaction-cost penalty |

Python API: `from asset_lens.quant import historical_cvar, min_variance, minimize_cvar, simulate, rolling_rebalance`.
Input convention: return matrix shape `(T, N)` (T periods × N assets); weights sum to 1, long-only by default.

---

## Data Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `sample` | Anonymized demo data | Demo, testing, open source |
| `real` | Personal investment data | Daily personal use |

```bash
make mode-sample    # Switch to sample mode
make mode-real      # Switch to real mode
```

Real data paths are excluded by `.gitignore` and never tracked.

---

## Configuration

### Environment Variables

Edit `.env` file:

```bash
# Data mode
DATA_MODE=sample

# API Keys (optional, for real-time market data)
ALPHAVANTAGE_API_KEY=your_key
FINNHUB_API_KEY=your_key

# AI analysis (optional)
OPENAI_API_KEY=your_key
```

Data sources whose key is left unset are skipped, and the next source in the
fallback chain is tried instead.

### Config Files

Config files use `.example` templates — copy to remove the `.example` suffix and customize.

---

## Tech Stack

- **Python 3.11–3.13**
- **pandas / numpy** — data processing
- **click** — CLI framework
- **rich** — formatted output
- **LightGBM / XGBoost** — machine learning
- **scikit-learn** — model utilities
- **openai** — AI analysis (optional)
- **FastAPI** — Web API (optional)

---

## Ecosystem

asset-lens is the core data engine. Three companion apps in the same workspace consume its output for different analysis paradigms:

| App | Framework | Pattern | Input | Output |
|-----|-----------|---------|-------|--------|
| **[langgraph-csv-analyst](../langgraph-csv-analyst/)** | LangGraph | Deterministic pipeline (fan-out/fan-in) | CSV file | Charts + LLM analysis |
| **[autogen-asset-analyst](../autogen-asset-analyst/)** | AutoGen | Multi-agent roundtable debate | asset-lens JSON | Debate transcript + consensus |
| **[crewai-product-analyst](../crewai-product-analyst/)** | CrewAI | Role-based crew collaboration | Product data | Product analysis report |

### Key Differences

| Feature | langgraph-csv-analyst | autogen-asset-analyst | crewai-product-analyst |
|---------|----------------------|----------------------|----------------------|
| Architecture | StateGraph pipeline | SelectorGroupChat | Crew role delegation |
| Agent interaction | Sequential/parallel | Debate & veto | Task delegation |
| Decision making | Last node decides | Consensus through debate | Crew synthesis |
| Risk control | Assessment only | One-vote veto | Role-based review |
| Data source | CSV (any format) | asset-lens JSON | Product data |
| Strength | Deterministic, reproducible | Multi-perspective debate | Structured collaboration |

---

## Disclaimer

This project is for personal learning and investment research only. **It does not constitute investment advice.**

---

## License

MIT License
