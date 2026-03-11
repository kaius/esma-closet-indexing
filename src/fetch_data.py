"""
fetch_data.py — Download Estonian pension fund NAV data.

Data source: Pensionikeskus (https://www.pensionikeskus.ee)
The site provides monthly NAV data for all Estonian pension funds (II and III pillar).

Usage:
    from src.fetch_data import fetch_fund_navs, load_benchmark

    navs = fetch_fund_navs()        # returns DataFrame: date x fund
    benchmark = load_benchmark()    # returns Series: date -> index value
"""

import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_fund_navs(save_cache: bool = True) -> pd.DataFrame:
    """
    Download monthly NAV data for all Estonian pension funds.

    Returns a DataFrame with:
        - index: datetime (monthly, end-of-month)
        - columns: fund names
        - values: NAV (net asset value per unit)

    TODO: Implement actual data download from Pensionikeskus or another source.
    Currently returns an empty placeholder DataFrame.
    """
    cache_path = RAW_DIR / "fund_navs.csv"

    if cache_path.exists():
        print(f"Loading cached NAV data from {cache_path}")
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return df

    # --- TODO: Replace with actual data source ---
    # Option 1: Pensionikeskus website (scrape or API)
    # Option 2: Nasdaq Baltic (https://nasdaqbaltic.com)
    # Option 3: Load from a manually downloaded Excel/CSV file

    print("WARNING: No data source configured. Returning empty DataFrame.")
    print("Please implement fetch_fund_navs() in src/fetch_data.py")
    df = pd.DataFrame()

    if save_cache and not df.empty:
        df.to_csv(cache_path)
        print(f"Saved NAV data to {cache_path}")

    return df


def load_from_excel(filepath: str) -> pd.DataFrame:
    """
    Load NAV data from a manually downloaded Excel file.

    Expected format:
        - First column: dates
        - Subsequent columns: one per fund, fund name as header
        - Values: NAV per unit

    Args:
        filepath: Path to the Excel file

    Returns:
        DataFrame with datetime index and fund columns
    """
    df = pd.read_excel(filepath, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def load_from_csv(filepath: str) -> pd.DataFrame:
    """
    Load NAV data from a CSV file.

    Args:
        filepath: Path to the CSV file

    Returns:
        DataFrame with datetime index and fund columns
    """
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def load_benchmark(ticker: str = "URTH", source: str = "manual") -> pd.Series:
    """
    Load benchmark index data (e.g., MSCI World ETF).

    Args:
        ticker:  Benchmark ticker symbol (e.g., "URTH" for MSCI World ETF)
        source:  "manual" to load from data/raw/benchmark.csv,
                 or extend with other sources as needed

    Returns:
        Series with datetime index and price values
    """
    benchmark_path = RAW_DIR / "benchmark.csv"

    if benchmark_path.exists():
        s = pd.read_csv(benchmark_path, index_col=0, parse_dates=True).squeeze()
        s.name = ticker
        return s

    print(f"WARNING: No benchmark file found at {benchmark_path}")
    print("Please place a CSV with date,price columns in data/raw/benchmark.csv")
    return pd.Series(dtype=float, name=ticker)
