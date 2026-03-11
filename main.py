"""
main.py — ESMA Closet Indexing Analysis for Estonian Pension Funds

Usage:
    python main.py                              # auto-download from Pensionikeskus + Yahoo Finance
    python main.py --pillar iii                 # use III pillar funds (default: ii)
    python main.py --ticker EUNL.DE             # use different benchmark (default: URTH)
    python main.py --date-from 2015-01-01       # custom start date
    python main.py --excel path/to/navs.xlsx    # load fund data from local Excel
    python main.py --csv   path/to/navs.csv     # load fund data from local CSV
    python main.py --benchmark path/to/bm.csv   # load benchmark from local CSV

The script:
1. Downloads monthly NAV-per-unit data for Estonian pension funds (Pensionikeskus)
2. Downloads benchmark index data (Yahoo Finance)
3. Calculates ESMA closet indexing metrics for each fund
4. Prints a report and saves results to data/processed/results.csv
"""

import argparse
import sys
from src.fetch_data import fetch_pensionikeskus, load_benchmark, load_from_excel, load_from_csv
from src.calculations import analyse_all
from src.report import print_report, save_csv


def parse_args():
    parser = argparse.ArgumentParser(
        description="ESMA closet indexing analysis for Estonian pension funds"
    )
    parser.add_argument(
        "--pillar", choices=["ii", "iii"], default="ii",
        help="Pension pillar: 'ii' (mandatory) or 'iii' (supplementary). Default: ii"
    )
    parser.add_argument(
        "--ticker", default="URTH",
        help="Yahoo Finance benchmark ticker. Default: URTH (iShares MSCI World ETF). "
             "Other options: EUNL.DE, IWDA.AS, ^STOXX50E"
    )
    parser.add_argument(
        "--date-from", default="2010-01-01",
        help="Start date for NAV data (YYYY-MM-DD). Default: 2010-01-01"
    )
    parser.add_argument("--excel", help="Path to local fund NAV Excel file (skips download)")
    parser.add_argument("--csv",   help="Path to local fund NAV CSV file (skips download)")
    parser.add_argument("--benchmark", help="Path to local benchmark CSV file (skips Yahoo Finance)")
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Ignore cached files and re-download everything"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    use_cache = not args.no_cache

    # --- Load fund NAV data ---
    if args.excel:
        print(f"Loading fund NAVs from Excel: {args.excel}")
        nav_df = load_from_excel(args.excel)
    elif args.csv:
        print(f"Loading fund NAVs from CSV: {args.csv}")
        nav_df = load_from_csv(args.csv)
    else:
        nav_df = fetch_pensionikeskus(
            pillar=args.pillar,
            date_from=args.date_from,
            use_cache=use_cache,
        )

    if nav_df.empty:
        print()
        print("No fund data available. Options:")
        print("  1. Try manual download from https://www.pensionikeskus.ee/en/statistics/")
        print("     and run:  python main.py --excel path/to/downloaded.xls")
        print("  2. Re-run with --no-cache to force a fresh download attempt")
        sys.exit(1)

    print(f"Loaded {len(nav_df.columns)} funds, {len(nav_df)} months of data")
    print(f"Date range: {nav_df.index.min().date()} to {nav_df.index.max().date()}")

    # --- Load benchmark data ---
    if args.benchmark:
        benchmark_nav = load_from_csv(args.benchmark).squeeze()
        benchmark_nav.name = args.ticker
    else:
        benchmark_nav = load_benchmark(ticker=args.ticker, use_cache=use_cache)

    if benchmark_nav.empty:
        print()
        print(f"No benchmark data for '{args.ticker}'.")
        print("Try a different ticker with --ticker, or provide a local file with --benchmark")
        sys.exit(1)

    # --- Run analysis ---
    print(f"\nRunning ESMA closet indexing analysis (benchmark: {args.ticker})...")
    results = analyse_all(nav_df, benchmark_nav)

    # --- Report ---
    print_report(results)
    save_csv(results)


if __name__ == "__main__":
    main()
