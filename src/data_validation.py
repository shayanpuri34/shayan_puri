"""Data validation and quality audit module.
Performs integrity checks on market prices and corporate earnings event records.
"""

import logging
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger("earnings_engine.data_validation")


def validate_market_dataset(
    ticker: str,
    df: pd.DataFrame,
    extreme_jump_threshold: float = 0.50
) -> Dict[str, Any]:
    """Validates an OHLCV market price dataset.

    Checks:
    - Empty dataset
    - Duplicate timestamps
    - Invalid OHLC logic (e.g. High < Low, Low > High, Open <= 0, Close <= 0)
    - Missing close / adjusted close
    - Negative volume
    - Extreme jumps
    - Malformed dates / nonnumeric observations
    """
    if df is None or df.empty:
        return {
            "asset": ticker,
            "rows": 0,
            "start_date": None,
            "end_date": None,
            "missing_percent": 100.0,
            "duplicate_count": 0,
            "invalid_rows": 0,
            "usable": False,
            "errors": ["Dataset is empty or None"]
        }

    errors: List[str] = []
    rows = len(df)
    start_date = str(df.index.min().date()) if hasattr(df.index.min(), "date") else str(df.index.min())
    end_date = str(df.index.max().date()) if hasattr(df.index.max(), "date") else str(df.index.max())

    # Check duplicate index timestamps
    duplicate_count = int(df.index.duplicated().sum())
    if duplicate_count > 0:
        errors.append(f"Found {duplicate_count} duplicate timestamps.")

    # Required columns
    req_cols = ["Open", "High", "Low", "Close", "Volume"]
    missing_cols = [c for c in req_cols if c not in df.columns]
    if missing_cols:
        return {
            "asset": ticker,
            "rows": rows,
            "start_date": start_date,
            "end_date": end_date,
            "missing_percent": 100.0,
            "duplicate_count": duplicate_count,
            "invalid_rows": rows,
            "usable": False,
            "errors": [f"Missing required columns: {missing_cols}"]
        }

    # Missing values percentage
    total_cells = rows * len(req_cols)
    missing_cells = df[req_cols].isna().sum().sum()
    missing_percent = float((missing_cells / total_cells) * 100.0) if total_cells > 0 else 100.0

    # Invalid OHLC relationships
    invalid_hl = (df["High"] < df["Low"]).sum()
    invalid_prices = ((df["Open"] <= 0) | (df["High"] <= 0) | (df["Low"] <= 0) | (df["Close"] <= 0)).sum()
    invalid_volume = (df["Volume"] < 0).sum()

    # Extreme jumps (daily absolute return > threshold)
    returns = df["Close"].pct_change().abs()
    extreme_jumps = int((returns > extreme_jump_threshold).sum())
    if extreme_jumps > 0:
        errors.append(f"Detected {extreme_jumps} return jumps > {extreme_jump_threshold*100:.0f}%.")

    invalid_rows = int(invalid_hl + invalid_prices + invalid_volume)

    # Dataset usable criteria: at least 250 rows, missing percent < 5%, no fatal price errors
    usable = (rows >= 100) and (missing_percent < 5.0) and (invalid_hl == 0) and (invalid_prices == 0)

    return {
        "asset": ticker,
        "rows": rows,
        "start_date": start_date,
        "end_date": end_date,
        "missing_percent": round(missing_percent, 2),
        "duplicate_count": duplicate_count,
        "invalid_rows": invalid_rows,
        "extreme_jumps": extreme_jumps,
        "usable": usable,
        "errors": errors
    }


def validate_earnings_events(
    events_df: pd.DataFrame,
    price_dict: Dict[str, pd.DataFrame]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Performs a thorough quality audit on earnings events dataset.

    Returns cleaned usable events and an audit metrics dictionary.
    """
    if events_df is None or events_df.empty:
        return pd.DataFrame(), {
            "total_events": 0,
            "valid_events": 0,
            "missing_eps_estimate": 0,
            "missing_eps_actual": 0,
            "missing_revenue_estimate": 0,
            "missing_revenue_actual": 0,
            "missing_timing": 0,
            "duplicate_events": 0,
            "invalid_events": 0,
            "missing_prices": 0,
            "usable_events": 0,
        }

    total_events = len(events_df)
    df = events_df.copy()

    # Audit missing fields
    missing_eps_est = int(df["eps_estimate"].isna().sum()) if "eps_estimate" in df.columns else total_events
    missing_eps_act = int(df["eps_actual"].isna().sum()) if "eps_actual" in df.columns else total_events
    missing_rev_est = int(df["revenue_estimate"].isna().sum()) if "revenue_estimate" in df.columns else total_events
    missing_rev_act = int(df["revenue_actual"].isna().sum()) if "revenue_actual" in df.columns else total_events
    missing_timing = int((df["timing_class"] == "UNKNOWN").sum()) if "timing_class" in df.columns else total_events

    # Duplicate detection by (ticker, announcement_date, fiscal_year, fiscal_quarter)
    dup_cols = ["ticker", "announcement_date", "fiscal_year", "fiscal_quarter"]
    avail_dup_cols = [c for c in dup_cols if c in df.columns]
    duplicate_events = int(df.duplicated(subset=avail_dup_cols).sum()) if avail_dup_cols else 0

    # Check for invalid numerical fields (e.g. infinite or unparseable)
    invalid_mask = pd.Series(False, index=df.index)
    if "eps_actual" in df.columns:
        invalid_mask = invalid_mask | np.isinf(df["eps_actual"].fillna(0))
    if "eps_estimate" in df.columns:
        invalid_mask = invalid_mask | np.isinf(df["eps_estimate"].fillna(0))
    invalid_events = int(invalid_mask.sum())

    # Check price coverage
    missing_prices = 0
    usable_mask = pd.Series(True, index=df.index)

    for idx, row in df.iterrows():
        ticker = row.get("ticker")
        if ticker not in price_dict or price_dict[ticker] is None or price_dict[ticker].empty:
            missing_prices += 1
            usable_mask.loc[idx] = False
            continue
        p_df = price_dict[ticker]
        event_dt = pd.to_datetime(row.get("announcement_date"))
        if event_dt < p_df.index.min() or event_dt > p_df.index.max():
            missing_prices += 1
            usable_mask.loc[idx] = False

    # Filter usable events: must have valid ticker, valid date, non-duplicate, non-infinite, and price coverage
    usable_events_df = df[usable_mask & (~invalid_mask)].drop_duplicates(subset=avail_dup_cols).copy()
    usable_count = len(usable_events_df)
    valid_events = total_events - invalid_events - duplicate_events

    audit_summary = {
        "total_events": total_events,
        "valid_events": valid_events,
        "missing_eps_estimate": missing_eps_est,
        "missing_eps_actual": missing_eps_act,
        "missing_revenue_estimate": missing_rev_est,
        "missing_revenue_actual": missing_rev_act,
        "missing_timing": missing_timing,
        "duplicate_events": duplicate_events,
        "invalid_events": invalid_events,
        "missing_prices": missing_prices,
        "usable_events": usable_count,
    }

    # Breakdowns
    if not usable_events_df.empty:
        usable_events_df["year"] = pd.to_datetime(usable_events_df["announcement_date"]).dt.year
        audit_summary["events_per_year"] = usable_events_df["year"].value_counts().sort_index().to_dict()
        audit_summary["events_per_ticker"] = usable_events_df["ticker"].value_counts().to_dict()

    return usable_events_df, audit_summary
