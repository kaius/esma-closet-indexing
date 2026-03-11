"""
demo_data.py — Generate realistic synthetic NAV data for demonstration.

Uses actual Estonian II pillar pension fund names and simulates funds with
varying degrees of closet indexing behaviour so the full analysis pipeline
can be tested without a live internet connection.
"""

import numpy as np
import pandas as pd

# Actual Estonian II pillar pension fund names (as of 2024)
FUND_PROFILES = [
    # (name, beta_to_bench, alpha_monthly, tracking_noise, label)
    # Funds with beta≈1 and low noise → closet indexers
    ("LHV Pensionifond XL",           1.00,  0.000,  0.003, "closet"),
    ("Swedbank Pensionifond K90",      0.98,  0.001,  0.004, "closet"),
    ("SEB Progressiivne Pensionifond", 0.97,  0.000,  0.005, "closet"),
    # Funds with moderate tracking error → borderline
    ("Luminor B Pensionifond",         0.90, -0.001,  0.010, "borderline"),
    ("LHV Pensionifond M",             0.85,  0.001,  0.012, "borderline"),
    # Funds with genuine active management → not closet indexers
    ("Tuleva Maailma Aktsiate PF",     0.70,  0.003,  0.025, "active"),
    ("Kawe Kapital Pensionifond",      0.60,  0.002,  0.030, "active"),
    ("Avaron Konservatiivne PF",       0.30,  0.001,  0.015, "conservative"),
]


def generate_demo_data(
    start: str = "2010-01-01",
    end: str = "2025-12-31",
    benchmark_monthly_return: float = 0.008,  # ~10% annual
    benchmark_monthly_vol: float = 0.040,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Generate synthetic monthly NAV data and benchmark prices.

    Returns:
        nav_df:       DataFrame, month-end index, one column per fund (NAV per unit)
        benchmark:    Series, month-end index, benchmark price
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start, end=end, freq="ME")
    n = len(dates)

    # --- Benchmark ---
    bench_returns = rng.normal(benchmark_monthly_return, benchmark_monthly_vol, n)
    bench_prices = 100 * np.cumprod(1 + bench_returns)
    benchmark = pd.Series(bench_prices, index=dates, name="URTH (synthetic)")

    # --- Funds ---
    fund_navs = {}
    for name, beta, alpha, noise, _ in FUND_PROFILES:
        idiosyncratic = rng.normal(0, noise, n)
        fund_returns = alpha + beta * bench_returns + idiosyncratic
        nav = 10 * np.cumprod(1 + fund_returns)
        fund_navs[name] = nav

    nav_df = pd.DataFrame(fund_navs, index=dates)
    return nav_df, benchmark
