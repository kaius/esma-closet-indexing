# ESMA Closet Indexing Analysis — Estonian Pension Funds

This project downloads monthly NAV (Net Asset Value) data for Estonian pension funds and performs **closet indexing checks** based on ESMA guidelines.

## What is Closet Indexing?

Closet indexing occurs when an actively managed fund closely mimics a benchmark index while charging active management fees. ESMA (European Securities and Markets Authority) has defined quantitative thresholds to detect such funds.

## Metrics Calculated

| Metric | ESMA Threshold | Description |
|--------|---------------|-------------|
| **Tracking Error (TE)** | < 3% | Annualised std dev of fund vs benchmark return differences |
| **Active Share (R²)** | > 0.95 | Coefficient of determination vs benchmark |
| **Correlation** | > 0.95 | Pearson correlation of monthly returns |
| **Beta** | ≈ 1.0 | Sensitivity of fund returns to benchmark |
| **Information Ratio (IR)** | — | Excess return per unit of tracking error |
| **Mean Return Difference** | — | Average monthly return difference vs benchmark |

## Project Structure

```
esma-closet-indexing/
├── src/
│   ├── fetch_data.py       # Download fund NAV data
│   ├── calculations.py     # ESMA metric formulas
│   └── report.py           # Output results
├── data/
│   ├── raw/                # Downloaded NAV data (gitignored)
│   └── processed/          # Cleaned data (gitignored)
├── main.py                 # Entry point
└── requirements.txt        # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Data Sources

- Estonian pension fund NAVs: [Pensionikeskus](https://www.pensionikeskus.ee)
- Benchmark index data: configurable (e.g., MSCI World, S&P 500)

## Requirements

- Python 3.9+
- See `requirements.txt` for dependencies
