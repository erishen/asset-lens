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

- Python 3.9+
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

### Config Files

Config files use `.example` templates — copy to remove the `.example` suffix and customize.

---

## Tech Stack

- **Python 3.10+**
- **pandas / numpy** — data processing
- **click** — CLI framework
- **rich** — formatted output
- **LightGBM / XGBoost** — machine learning
- **scikit-learn** — model utilities
- **openai** — AI analysis (optional)
- **FastAPI** — Web API (optional)

---

## Disclaimer

This project is for personal learning and investment research only. **It does not constitute investment advice.**

---

## License

MIT License
