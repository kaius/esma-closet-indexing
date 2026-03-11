"""
calculations.py — ESMA closet indexing metrics.

Implements the quantitative indicators described in ESMA's 2016 report on
"Closet Indexing" (ESMA/2016/165) and subsequent supervisory work.

All metrics operate on monthly return series (as decimals, e.g. 0.02 = 2%).

Functions:
    monthly_returns(nav_series)         -> monthly return Series
    tracking_error(fund, benchmark)     -> annualised TE (float)
    r_squared(fund, benchmark)          -> R² (float)
    correlation(fund, benchmark)        -> Pearson r (float)
    beta(fund, benchmark)               -> beta (float)
    information_ratio(fund, benchmark)  -> IR (float)
    mean_return_difference(fund, bench) -> mean active return (float)
    analyse_fund(fund, benchmark, name) -> dict of all metrics
    analyse_all(nav_df, benchmark)      -> DataFrame of results
"""

import numpy as np
import pandas as pd
from scipy import stats


def monthly_returns(nav_series: pd.Series) -> pd.Series:
    """Convert a NAV price series to monthly percentage returns."""
    return nav_series.pct_change().dropna()


def tracking_error(fund_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    Annualised Tracking Error.

    TE = std(fund_return - benchmark_return) * sqrt(12)

    ESMA flag: TE < 3% (0.03) may indicate closet indexing.
    """
    aligned = _align(fund_returns, benchmark_returns)
    active_returns = aligned["fund"] - aligned["benchmark"]
    return float(active_returns.std() * np.sqrt(12))


def r_squared(fund_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    R² (coefficient of determination) from OLS regression of fund on benchmark.

    ESMA flag: R² > 0.95 may indicate closet indexing.
    """
    aligned = _align(fund_returns, benchmark_returns)
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        aligned["benchmark"], aligned["fund"]
    )
    return float(r_value ** 2)


def correlation(fund_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    Pearson correlation between fund and benchmark monthly returns.

    ESMA flag: correlation > 0.95 may indicate closet indexing.
    """
    aligned = _align(fund_returns, benchmark_returns)
    return float(aligned["fund"].corr(aligned["benchmark"]))


def beta(fund_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    Beta of the fund relative to the benchmark.

    beta = cov(fund, benchmark) / var(benchmark)

    A true closet indexer typically has beta close to 1.0.
    """
    aligned = _align(fund_returns, benchmark_returns)
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        aligned["benchmark"], aligned["fund"]
    )
    return float(slope)


def information_ratio(fund_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    Information Ratio (IR).

    IR = mean(active_return) / std(active_return)

    where active_return = fund_return - benchmark_return.
    Returns annualised IR (multiplied by sqrt(12)).
    """
    aligned = _align(fund_returns, benchmark_returns)
    active = aligned["fund"] - aligned["benchmark"]
    if active.std() == 0:
        return float("nan")
    return float((active.mean() / active.std()) * np.sqrt(12))


def mean_return_difference(
    fund_returns: pd.Series, benchmark_returns: pd.Series
) -> float:
    """
    Annualised mean active return.

    = mean(fund_return - benchmark_return) * 12
    """
    aligned = _align(fund_returns, benchmark_returns)
    active = aligned["fund"] - aligned["benchmark"]
    return float(active.mean() * 12)


def analyse_fund(
    fund_returns: pd.Series,
    benchmark_returns: pd.Series,
    fund_name: str = "Fund",
) -> dict:
    """
    Run all ESMA closet indexing metrics for a single fund.

    Returns a dict with keys:
        fund, n_months, tracking_error, r_squared, correlation,
        beta, information_ratio, mean_return_diff, closet_index_flag
    """
    aligned = _align(fund_returns, benchmark_returns)
    n = len(aligned)

    te = tracking_error(fund_returns, benchmark_returns)
    r2 = r_squared(fund_returns, benchmark_returns)
    corr = correlation(fund_returns, benchmark_returns)
    b = beta(fund_returns, benchmark_returns)
    ir = information_ratio(fund_returns, benchmark_returns)
    mrd = mean_return_difference(fund_returns, benchmark_returns)

    # Simple flag: flag if 2 or more of the primary ESMA indicators trigger
    flags = sum([
        te < 0.03,       # TE below 3%
        r2 > 0.95,       # R² above 95%
        corr > 0.95,     # correlation above 95%
    ])
    closet_flag = flags >= 2

    return {
        "fund": fund_name,
        "n_months": n,
        "tracking_error": round(te, 4),
        "r_squared": round(r2, 4),
        "correlation": round(corr, 4),
        "beta": round(b, 4),
        "information_ratio": round(ir, 4) if not np.isnan(ir) else None,
        "mean_return_diff": round(mrd, 4),
        "closet_index_flag": closet_flag,
    }


def analyse_all(nav_df: pd.DataFrame, benchmark_nav: pd.Series) -> pd.DataFrame:
    """
    Run closet indexing analysis for all funds in nav_df.

    Args:
        nav_df:         DataFrame with datetime index and fund NAV columns
        benchmark_nav:  Series with datetime index and benchmark NAV values

    Returns:
        DataFrame with one row per fund and all ESMA metrics as columns
    """
    benchmark_ret = monthly_returns(benchmark_nav)
    results = []
    for fund_name in nav_df.columns:
        fund_ret = monthly_returns(nav_df[fund_name].dropna())
        result = analyse_fund(fund_ret, benchmark_ret, fund_name=fund_name)
        results.append(result)
    return pd.DataFrame(results).set_index("fund")


def _align(fund_returns: pd.Series, benchmark_returns: pd.Series) -> pd.DataFrame:
    """Align two return series on their common dates and drop NaNs."""
    df = pd.DataFrame({"fund": fund_returns, "benchmark": benchmark_returns})
    return df.dropna()
