# Demo Data

## 📁 Simulated Dataset

To support open-source and demonstration use cases, we've created a complete set of simulated investment data. This data preserves the structure and complexity of real data, but all amounts, returns, and other sensitive information have been anonymized.

## 📊 Data Characteristics

### Investment Types Covered
- **Money Market Funds**: Low-risk products (e.g., Yu'e Bao)
- **Index Funds**: CSI 300, CSI 500, Nasdaq 100, etc.
- **Bond Funds**: Government bond ETFs and fixed-income products
- **Mixed Funds**: Balanced allocation funds
- **A-Shares**: Chinese domestic stocks, tech stocks
- **US Stocks**: Apple, Microsoft, etc.
- **HK Stocks**: Tencent, etc.
- **QDII**: S&P 500 ETFs and overseas funds
- **Wealth Management**: Bank wealth management, time deposits
- **REITs**: Logistics REITs, etc.
- **Gold**: Gold ETFs

### Platform Distribution
- **WeChat**: US stock investments (Apple, Microsoft)
- **Alipay**: Domestic funds, A-shares, HK stocks, QDII (primary)

### DCA Strategy Showcase
The data includes all supported DCA (Dollar-Cost Averaging) modes:

1. **Fixed Amount DCA**: `2024/1/15-now:buy:200`
2. **Smart Range DCA**: `2024/2/1-now:buy:100~300`
3. **Floating Amount DCA**: `2024/7/1-now:buy:150±50`
4. **Valuation-Based DCA**: `2024/3/15-now:buy:80-200-400`
5. **Phased DCA**: `2024/1/1-2024/6/30:buy:100;2024/7/1-now:buy:150±50`

### Multi-Currency Support
- **CNY Investments**: Domestic funds, A-shares, etc.
- **USD Investments**: US stocks, USD funds
- **HKD Investments**: HK stocks, etc.
- **Exchange Rates**: Real-time rate conversion support
- **Market Indices**: SSE Composite, CSI 300, Nasdaq 100, etc.
- **Risk Indicators**: VIX, Federal Reserve interest rates, etc.

## 🔧 Usage

### 1. Run Demo
```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Run analysis with demo data
asset-lens analyze --data-mode sample
```

### 2. View Results
Analysis results are saved to `output/` directory.

### 3. Comparative Analysis
```bash
# Create multi-period demo data for comparison
asset-lens compare -- demo1 demo2 report
```

## 📈 Expected Output

After running with demo data, you will see:

- **Return Rankings**: Annualized returns across all investment products
- **Type Analysis**: Return distribution by investment type
- **DCA Effectiveness**: Return comparison across different DCA strategies
- **Risk Assessment**: Performance by risk level
- **Multi-Currency Statistics**: Exchange rate impact analysis on foreign investments

## 🔒 Privacy Protection

- ✅ All monetary data has been anonymized
- ✅ Return rates are reasonable simulated values
- ✅ Personal sensitive information completely removed
- ✅ Data structure integrity preserved

## 🎯 Educational Value

This demo dataset helps users:

1. **Understand System Capabilities**: Quickly grasp what the investment analysis system can do
2. **Learn DCA Strategies**: Understand different DCA modes through examples
3. **Master Usage**: Experience the full workflow without real data
4. **Technical Learning**: Study IRR calculations, data processing, and other technical implementations

## 📝 Custom Data

You can create your own test data based on this template:

1. Copy the `data/sample_data` folder
2. Modify product names and amounts
3. Adjust DCA strategies and time ranges
4. Run analysis to view results

---

**Note**: This data is for demonstration and learning purposes only and does not constitute investment advice.
