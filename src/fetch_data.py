"""
fetch_data.py — Download Estonian pension fund NAV data from Pensionikeskus.

Data source: https://www.pensionikeskus.ee/en/statistics/
- II pillar: /ii-pillar/nav-of-funded-pension/
- III pillar: /iii-pillar/nav-of-suppl-funded-pension/

Data is downloaded as XLS (Excel) files with daily NAV per unit.
We resample to month-end values for ESMA analysis.

Usage:
    from src.fetch_data import fetch_pensionikeskus, load_benchmark
    from src.fetch_data import load_from_excel, load_from_csv

    navs = fetch_pensionikeskus()      # returns DataFrame: date x fund
    benchmark = load_benchmark()       # returns Series: date -> price
"""

import io
import requests
import pandas as pd
from pathlib import Path
from datetime import date

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Pensionikeskus XLS download endpoints
_BASE_URL = "https://www.pensionikeskus.ee/en/statistics"
_PILLAR_URLS = {
    "ii":  f"{_BASE_URL}/ii-pillar/nav-of-funded-pension/",
    "iii": f"{_BASE_URL}/iii-pillar/nav-of-suppl-funded-pension/",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_pensionikeskus(
    pillar: str = "ii",
    date_from: str = "2010-01-01",
    date_to: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Download NAV-per-unit data for all Estonian pension funds from Pensionikeskus.

    Args:
        pillar:     "ii" (mandatory) or "iii" (supplementary)
        date_from:  Start date as YYYY-MM-DD string
        date_to:    End date as YYYY-MM-DD (defaults to today)
        use_cache:  If True, return cached file if it exists in data/raw/

    Returns:
        DataFrame with month-end datetime index and one column per fund.
        Values are NAV per unit (price), resampled to last business day of month.
    """
    if date_to is None:
        date_to = date.today().isoformat()

    cache_path = RAW_DIR / f"pensionikeskus_pillar{pillar}.csv"

    if use_cache and cache_path.exists():
        print(f"Loading cached data from {cache_path}")
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return df

    url = _PILLAR_URLS.get(pillar)
    if url is None:
        raise ValueError(f"pillar must be 'ii' or 'iii', got '{pillar}'")

    params = {
        "download": "xls",
        "date_from": date_from,
        "date_to": date_to,
    }

    print(f"Downloading Pensionikeskus pillar {pillar.upper()} data ({date_from} to {date_to})...")
    try:
        response = requests.get(url, params=params, headers=_HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Download failed: {e}")
        print()
        print("Manual download instructions:")
        print(f"  1. Go to {url}")
        print(f"  2. Set date range: {date_from} to {date_to}")
        print("  3. Click 'Download XLS'")
        print(f"  4. Save the file to: data/raw/pensionikeskus_pillar{pillar}.xlsx")
        print(f"  5. Run: python main.py --excel data/raw/pensionikeskus_pillar{pillar}.xlsx")
        return pd.DataFrame()

    df = _parse_pensionikeskus_xls(io.BytesIO(response.content))
    if df.empty:
        return df

    # Resample daily NAV to month-end
    df = df.resample("ME").last()

    df.to_csv(cache_path)
    print(f"Saved {len(df.columns)} funds, {len(df)} months to {cache_path}")
    return df


def _parse_pensionikeskus_xls(fileobj) -> pd.DataFrame:
    """
    Parse a Pensionikeskus XLS download into a wide DataFrame.

    Expected XLS structure (long format):
        Date | Fund name | NAV per unit | ...

    Returns wide DataFrame: date index x fund columns.
    """
    try:
        raw = pd.read_excel(fileobj, header=0)
    except Exception as e:
        print(f"Failed to parse XLS: {e}")
        return pd.DataFrame()

    # Normalise column names
    raw.columns = [str(c).strip().lower() for c in raw.columns]

    # Try to identify date, fund name, and NAV columns
    # Pensionikeskus typically uses: date, fund (or name/shortname), nav_per_unit
    date_col = _find_col(raw, ["date", "kuupäev", "date"])
    fund_col = _find_col(raw, ["fund", "name", "shortname", "fond", "lühinimi"])
    nav_col  = _find_col(raw, ["nav per unit", "nav/unit", "nav per osakut", "osakuväärtus", "nav"])

    if date_col is None or fund_col is None or nav_col is None:
        print("Could not identify columns in the downloaded file.")
        print(f"Found columns: {list(raw.columns)}")
        print("Please open the file and use load_from_excel() with a pre-formatted file.")
        return pd.DataFrame()

    raw[date_col] = pd.to_datetime(raw[date_col])
    raw[nav_col]  = pd.to_numeric(raw[nav_col], errors="coerce")

    df = raw.pivot_table(index=date_col, columns=fund_col, values=nav_col, aggfunc="last")
    df.index.name = "date"
    df.columns.name = None
    df = df.sort_index()
    return df


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first column name that contains any of the candidate strings."""
    for col in df.columns:
        for c in candidates:
            if c in col:
                return col
    return None


def load_from_excel(filepath: str) -> pd.DataFrame:
    """
    Load NAV data from a manually downloaded or pre-formatted Excel file.

    Accepts two formats:
      Wide:  first column = date, remaining columns = funds (NAV per unit)
      Long:  columns include date, fund name, nav per unit (auto-detected)

    Returns DataFrame with month-end datetime index and fund columns.
    """
    raw = pd.read_excel(filepath, index_col=None, header=0)
    raw.columns = [str(c).strip() for c in raw.columns]

    # Detect wide vs long format
    if raw.shape[1] > 10:
        # Probably wide (many fund columns)
        df = raw.set_index(raw.columns[0])
        df.index = pd.to_datetime(df.index)
        df = df.apply(pd.to_numeric, errors="coerce")
    else:
        # Try long format parsing
        df = _parse_pensionikeskus_xls(filepath)
        if df.empty:
            # Fallback: treat first column as date index
            df = raw.set_index(raw.columns[0])
            df.index = pd.to_datetime(df.index)
            df = df.apply(pd.to_numeric, errors="coerce")

    df = df.sort_index()
    # Resample to month-end if data appears daily (>100 rows per year on average)
    years = max(1, (df.index.max() - df.index.min()).days / 365)
    if len(df) / years > 50:
        df = df.resample("ME").last()

    return df.dropna(how="all")


def load_from_csv(filepath: str) -> pd.DataFrame:
    """
    Load NAV data from a CSV file.

    Returns DataFrame with datetime index and fund columns.
    """
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def load_benchmark(ticker: str = "URTH", use_cache: bool = True) -> pd.Series:
    """
    Load benchmark index data via yfinance or from a local cache file.

    Default benchmark: URTH (iShares MSCI World ETF) — a common proxy
    for the global equity benchmark most Estonian pension funds target.

    Other useful tickers:
        "EUNL.DE"  iShares Core MSCI World (EUR, Xetra)
        "IWDA.AS"  iShares Core MSCI World (EUR, Amsterdam)
        "^STOXX50E" Euro Stoxx 50
        "^GSPC"    S&P 500

    Args:
        ticker:    Yahoo Finance ticker symbol
        use_cache: Return cached file if available

    Returns:
        Series with month-end datetime index and adjusted close prices.
    """
    cache_path = RAW_DIR / f"benchmark_{ticker.replace('.', '_')}.csv"

    if use_cache and cache_path.exists():
        print(f"Loading cached benchmark from {cache_path}")
        s = pd.read_csv(cache_path, index_col=0, parse_dates=True).squeeze()
        s.name = ticker
        return s

    try:
        import yfinance as yf
    except ImportError:
        print("yfinance not installed. Run: pip install yfinance")
        print(f"Or place a benchmark CSV in {cache_path} with columns: date, price")
        return pd.Series(dtype=float, name=ticker)

    print(f"Downloading benchmark data for {ticker} from Yahoo Finance...")
    data = yf.download(ticker, start="2005-01-01", auto_adjust=True, progress=False)

    if data.empty:
        print(f"No data returned for ticker '{ticker}'")
        return pd.Series(dtype=float, name=ticker)

    # Use adjusted close, resample to month-end
    close = data["Close"].squeeze()
    monthly = close.resample("ME").last()
    monthly.index = monthly.index.normalize()
    monthly.name = ticker

    monthly.to_csv(cache_path, header=["price"])
    print(f"Saved benchmark data ({len(monthly)} months) to {cache_path}")
    return monthly
