"""Event standardization, deduplication, and trading calendar alignment module.
Enforces strict schema consistency, conservative timing rules (BMO/AMC/UNKNOWN), and holiday/weekend handling.
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger("earnings_engine.event_standardizer")

SOURCE_PRIORITY = {
    "alpha_vantage": 1,
    "fmp": 2,
    "yfinance": 3,
    "sec": 4,
    "cached": 5,
    "fallback": 6
}


def create_event_id(ticker: str, date: str, fy: Optional[int], fq: Optional[int]) -> str:
    """Creates a deterministic unique identifier for an earnings event."""
    raw = f"{ticker.upper()}_{date}_{fy}_{fq}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def classify_announcement_timing(
    time_str: Optional[str],
    default_timing: str = "UNKNOWN"
) -> str:
    """Classifies earnings announcement time into BMO, AMC, or UNKNOWN.

    - BMO: Before Market Open (typically before 09:30 AM EST)
    - AMC: After Market Close (typically at or after 16:00 EST / 4:00 PM)
    - UNKNOWN: Timing cannot be proven with high confidence
    """
    if time_str is None or pd.isna(time_str):
        return "UNKNOWN"

    s = str(time_str).strip().upper()

    if "BMO" in s or "BEFORE" in s or "PRE" in s:
        return "BMO"
    if "AMC" in s or "AFTER" in s or "POST" in s:
        return "AMC"

    # Try parsing HH:MM or ISO timestamp
    try:
        if "T" in s or ":" in s:
            # Handle ISO or HH:MM:SS
            time_part = s.split("T")[-1].split("Z")[0].split("+")[0].strip()
            parts = time_part.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0

            # US market hours: 09:30 - 16:00
            if hour < 9 or (hour == 9 and minute < 30):
                return "BMO"
            elif hour >= 16:
                return "AMC"
            else:
                # During market hours or uncertain
                return "UNKNOWN"
    except Exception:
        pass

    return default_timing


def resolve_next_trading_day(
    target_date: Union[str, pd.Timestamp],
    trading_days: List[pd.Timestamp]
) -> Optional[pd.Timestamp]:
    """Finds the earliest valid trading day on or after the target date.

    If target_date is a trading day and strictly_after=False, returns target_date.
    If target_date falls on a weekend or exchange holiday, advances to next trading day.
    """
    ts = pd.to_datetime(target_date).normalize()
    # Filter trading days >= ts
    valid = [d for d in trading_days if d >= ts]
    if valid:
        return min(valid)
    return None


def resolve_strictly_next_trading_day(
    target_date: Union[str, pd.Timestamp],
    trading_days: List[pd.Timestamp]
) -> Optional[pd.Timestamp]:
    """Finds the earliest valid trading day strictly after the target date."""
    ts = pd.to_datetime(target_date).normalize()
    valid = [d for d in trading_days if d > ts]
    if valid:
        return min(valid)
    return None


def resolve_previous_trading_day(
    target_date: Union[str, pd.Timestamp],
    trading_days: List[pd.Timestamp]
) -> Optional[pd.Timestamp]:
    """Finds the latest valid trading day strictly before the target date."""
    ts = pd.to_datetime(target_date).normalize()
    valid = [d for d in trading_days if d < ts]
    if valid:
        return max(valid)
    return None


def get_first_tradable_day(
    announcement_date: Union[str, pd.Timestamp],
    timing_class: str,
    trading_days: List[pd.Timestamp]
) -> Optional[pd.Timestamp]:
    """Determines the first feasible trading day where position can be established.

    Timing Rules:
    - BMO (Before Market Open): The market opens after announcement, so the announcement
      day itself is tradable at open/next session if it is a trading day.
    - AMC (After Market Close): Market has already closed. Trading MUST occur on the
      next trading day.
    - UNKNOWN: To prevent look-ahead bias, conservative rule dictates trading occurs
      no earlier than the NEXT full trading session.
    """
    ts = pd.to_datetime(announcement_date).normalize()

    if timing_class == "BMO":
        # Can trade on announcement day if it is a trading day; otherwise next trading day
        return resolve_next_trading_day(ts, trading_days)
    elif timing_class in ("AMC", "UNKNOWN"):
        # Must trade strictly on the next trading day
        return resolve_strictly_next_trading_day(ts, trading_days)
    else:
        return resolve_strictly_next_trading_day(ts, trading_days)


def standardize_events(raw_events: List[Dict[str, Any]]) -> pd.DataFrame:
    """Converts heterogeneous event records into the standardized schema.

    Standard Schema:
    - ticker: str
    - announcement_date: str (YYYY-MM-DD)
    - announcement_time: Optional[str]
    - timing_class: 'BMO' | 'AMC' | 'UNKNOWN'
    - fiscal_year: Optional[int]
    - fiscal_quarter: Optional[int]
    - eps_actual: float (NaN if missing)
    - eps_estimate: float (NaN if missing)
    - eps_surprise: float (NaN if missing)
    - eps_surprise_pct: float (NaN if missing or zero estimate)
    - revenue_actual: float (NaN if missing)
    - revenue_estimate: float (NaN if missing)
    - revenue_surprise: float (NaN if missing)
    - revenue_surprise_pct: float (NaN if missing or zero estimate)
    - source: str
    - event_id: str
    """
    records = []
    for item in raw_events:
        ticker = str(item.get("ticker", "")).strip().upper()
        if not ticker:
            continue

        # Parse date
        raw_date = item.get("announcement_date") or item.get("date")
        if not raw_date:
            continue
        try:
            dt = pd.to_datetime(raw_date).date()
            date_str = str(dt)
        except Exception:
            continue

        raw_time = item.get("announcement_time") or item.get("time")
        timing_class = item.get("timing_class") or classify_announcement_timing(raw_time)

        # Fiscal year & quarter
        fy = item.get("fiscal_year")
        fq = item.get("fiscal_quarter")
        try:
            fy = int(fy) if fy is not None and not pd.isna(fy) else None
        except Exception:
            fy = None
        try:
            fq = int(fq) if fq is not None and not pd.isna(fq) else None
        except Exception:
            fq = None

        # Numerical fields
        def _to_float(v):
            if v is None or pd.isna(v) or str(v).strip() == "":
                return np.nan
            try:
                val = float(v)
                return np.nan if np.isinf(val) else val
            except (ValueError, TypeError):
                return np.nan

        eps_act = _to_float(item.get("eps_actual", item.get("reportedEPS")))
        eps_est = _to_float(item.get("eps_estimate", item.get("estimatedEPS")))
        rev_act = _to_float(item.get("revenue_actual", item.get("reportedRevenue")))
        rev_est = _to_float(item.get("revenue_estimate", item.get("estimatedRevenue")))

        # Calculate surprise safely (handling zero denominator)
        if not np.isnan(eps_act) and not np.isnan(eps_est):
            eps_surp = eps_act - eps_est
            eps_surp_pct = np.nan if eps_est == 0.0 else (eps_act - eps_est) / abs(eps_est)
        else:
            eps_surp = _to_float(item.get("eps_surprise"))
            eps_surp_pct = _to_float(item.get("eps_surprise_pct"))

        if not np.isnan(rev_act) and not np.isnan(rev_est):
            rev_surp = rev_act - rev_est
            rev_surp_pct = np.nan if rev_est == 0.0 else (rev_act - rev_est) / abs(rev_est)
        else:
            rev_surp = _to_float(item.get("revenue_surprise"))
            rev_surp_pct = _to_float(item.get("revenue_surprise_pct"))

        source = str(item.get("source", "unknown")).lower()
        event_id = item.get("event_id") or create_event_id(ticker, date_str, fy, fq)

        records.append({
            "ticker": ticker,
            "announcement_date": date_str,
            "announcement_time": str(raw_time) if raw_time is not None else None,
            "timing_class": timing_class,
            "fiscal_year": fy,
            "fiscal_quarter": fq,
            "eps_actual": eps_act,
            "eps_estimate": eps_est,
            "eps_surprise": eps_surp,
            "eps_surprise_pct": eps_surp_pct,
            "revenue_actual": rev_act,
            "revenue_estimate": rev_est,
            "revenue_surprise": rev_surp,
            "revenue_surprise_pct": rev_surp_pct,
            "source": source,
            "event_id": event_id
        })

    if not records:
        cols = [
            "ticker", "announcement_date", "announcement_time", "timing_class",
            "fiscal_year", "fiscal_quarter", "eps_actual", "eps_estimate",
            "eps_surprise", "eps_surprise_pct", "revenue_actual", "revenue_estimate",
            "revenue_surprise", "revenue_surprise_pct", "source", "event_id"
        ]
        return pd.DataFrame(columns=cols)

    return pd.DataFrame(records)


def deduplicate_events(events_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Deduplicates events across data sources using priority hierarchy.

    Key: (ticker, announcement_date, fiscal_year, fiscal_quarter).
    Priority: Alpha Vantage > FMP > yfinance > SEC > cached > fallback.
    Records duplicate audit conflicts instead of silently dropping them.
    """
    if events_df.empty:
        return events_df, []

    df = events_df.copy()
    df["source_rank"] = df["source"].map(lambda s: SOURCE_PRIORITY.get(str(s).lower(), 99))

    # Identify duplicate groups
    dup_cols = ["ticker", "announcement_date", "fiscal_year", "fiscal_quarter"]
    duplicates_mask = df.duplicated(subset=dup_cols, keep=False)

    conflict_log = []
    if duplicates_mask.any():
        groups = df[duplicates_mask].groupby(dup_cols)
        for name, grp in groups:
            conflict_log.append({
                "key": name,
                "sources": grp["source"].tolist(),
                "selected_source": grp.sort_values("source_rank").iloc[0]["source"],
                "row_count": len(grp)
            })

    # Sort by key and priority rank ascending, then keep the first (highest priority)
    df_dedup = df.sort_values(by=["ticker", "announcement_date", "source_rank"]).drop_duplicates(
        subset=dup_cols,
        keep="first"
    ).drop(columns=["source_rank"]).reset_index(drop=True)

    logger.info(f"Deduplicated {len(df)} raw events into {len(df_dedup)} unique events. Resolved {len(conflict_log)} conflicts.")
    return df_dedup, conflict_log
