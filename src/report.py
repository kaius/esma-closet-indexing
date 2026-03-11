"""
report.py — Format and output ESMA closet indexing results.
"""

import pandas as pd
from tabulate import tabulate
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def print_report(results: pd.DataFrame) -> None:
    """Print a formatted table of closet indexing results to stdout."""
    display = results.copy()
    display["tracking_error"] = display["tracking_error"].map("{:.2%}".format)
    display["r_squared"] = display["r_squared"].map("{:.4f}".format)
    display["correlation"] = display["correlation"].map("{:.4f}".format)
    display["beta"] = display["beta"].map("{:.4f}".format)
    display["mean_return_diff"] = display["mean_return_diff"].map("{:.2%}".format)
    display["closet_index_flag"] = display["closet_index_flag"].map(
        lambda x: "YES ⚠" if x else "No"
    )

    print("\n=== ESMA Closet Indexing Analysis — Estonian Pension Funds ===\n")
    print(tabulate(display, headers="keys", tablefmt="github"))
    flagged = results[results["closet_index_flag"]].index.tolist()
    if flagged:
        print(f"\nFlagged as potential closet indexers: {', '.join(flagged)}")
    else:
        print("\nNo funds flagged as potential closet indexers.")


def save_csv(results: pd.DataFrame, filename: str = "results.csv") -> Path:
    """Save results DataFrame to data/processed/."""
    out_path = PROCESSED_DIR / filename
    results.to_csv(out_path)
    print(f"Results saved to {out_path}")
    return out_path
