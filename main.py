"""
main.py — ESMA Closet Indexing Analysis for Estonian Pension Funds

Usage:
    python main.py                          # run with default settings
    python main.py --excel path/to/navs.xlsx
    python main.py --csv path/to/navs.csv
    python main.py --benchmark path/to/benchmark.csv

The script:
1. Loads monthly NAV data for Estonian pension funds
2. Loads benchmark index data
3. Calculates ESMA closet indexing metrics for each fund
4. Prints a report and saves results to data/processed/results.csv
"""

import argparse
import sys
import pandas as pd
from src.fetch_data import fetch_fund_navs, load_benchmark, load_from_excel, load_from_csv
from src.calculations import analyse_all
from src.report import print_report, save_csv


def parse_args():
    parser = argparse.ArgumentParser(
        description="ESMA closet indexing analysis for Estonian pension funds"
    )
    parser.add_argument("--excel", help="Path to NAV data Excel file")
    parser.add_argument("--csv", help="Path to NAV data CSV file")
    parser.add_argument("--benchmark", help="Path to benchmark CSV file (date,price)")
    return parser.parse_args()


def main():
    args = parse_args()

    # --- Load fund NAV data ---
    if args.excel:
        print(f"Loading fund NAVs from Excel: {args.excel}")
        nav_df = load_from_excel(args.excel)
    elif args.csv:
        print(f"Loading fund NAVs from CSV: {args.csv}")
        nav_df = load_from_csv(args.csv)
    else:
        print("Fetching fund NAV data...")
        nav_df = fetch_fund_navs()

    if nav_df.empty:
        print("\nNo fund data available. Please provide data via --excel or --csv.")
        print("See src/fetch_data.py for guidance on data sources.")
        sys.exit(1)

    print(f"Loaded {len(nav_df.columns)} funds, {len(nav_df)} months of data")
    print(f"Date range: {nav_df.index.min().date()} to {nav_df.index.max().date()}")

    # --- Load benchmark data ---
    if args.benchmark:
        from src.fetch_data import load_from_csv as load_csv
        benchmark_nav = load_csv(args.benchmark).squeeze()
    else:
        benchmark_nav = load_benchmark()

    if benchmark_nav.empty:
        print("\nNo benchmark data available.")
        print("Place benchmark CSV (date,price) in data/raw/benchmark.csv")
        sys.exit(1)

    # --- Run analysis ---
    print("\nRunning ESMA closet indexing analysis...")
    results = analyse_all(nav_df, benchmark_nav)

    # --- Report ---
    print_report(results)
    save_csv(results)


if __name__ == "__main__":
    main()
