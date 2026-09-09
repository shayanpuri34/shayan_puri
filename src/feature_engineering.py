"""Feature engineering module for corporate earnings event studies.
Calculates point-in-time SUE, pre-event momentum, volatility, volume z-scores,
and pre-event market betas with strict anti-leakage guards.
"""

import logging
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger("earnings_engine.feature_engineering")


def compute_eps_surprise(actual: float, estimate: float) -> float:
    """Computes dollar EPS surprise."""
    if pd.isna(actual) or pd.isna(estimate):
        return np.nan
    return float(actual - estimate)


def compute_eps_surprise_pct(actual: float, estimate: float) -> float:
    """Computes percentage EPS surprise.

    Guards against zero denominator division by returning NaN instead of infinity.
    """
    if pd.isna(actual) or pd.isna(estimate) or estimate == 0.0:
        return np.nan
    return float((actual - estimate) / abs(estimate))


def compute_revenue_surprise(actual: float, estimate: float) -> float:
    """Computes dollar revenue surprise."""
    if pd.isna(actual) or pd.isna(estimate):
        return np.nan
    return float(actual - estimate)


def compute_revenue_surprise_pct(actual: float, estimate: float) -> float:
    """Computes percentage revenue surprise.

    Guards against zero denominator division by returning NaN instead of infinity.
    """
    if pd.isna(actual) or pd.isna(estimate) or estimate == 0.0:
        return np.nan
    return float((actual - estimate) / abs(estimate))


def compute_point_in_time_sue(
    events_df: pd.DataFrame,
    min_prior_events: int = 2
) -> pd.Series:
    """Computes Standardized Unexpected Earnings (SUE) using ONLY historical surprises prior to event t.

    SUE_t = (EPSActual_t - EPSEstimate_t) / std(prior_surprises_{< t})
    If fewer than min_prior_events prior events exist, returns standardized z-score using expanding sample.
    """
    df = events_df.sort_values(by=["ticker", "announcement_date"]).copy()
    sue_values = []

    for ticker, group in df.groupby("ticker"):
        prior_surprises = []
        for idx, row in group.iterrows():
            surp = row.get("eps_surprise")
            if pd.isna(surp):
                sue_values.append((idx, np.nan))
                continue

            if len(prior_surprises) >= min_prior_events:
                hist_std = float(np.std(prior_surprises, ddof=1))
                if hist_std > 1e-4:
                    sue = float(surp / hist_std)
                else:
                    sue = float(np.sign(surp))
            elif len(prior_surprises) > 0:
                hist_std = float(np.std(prior_surprises, ddof=0))
                sue = float(surp / max(hist_std, 0.05))
            else:
                sue = float(np.sign(surp))  # Prior fallback

            sue_values.append((idx, sue))
            prior_surprises.append(surp)

    sue_df = pd.DataFrame(sue_values, columns=["index", "sue"]).set_index("index")
    return sue_df.loc[events_df.index, "sue"]


def build_pre_event_features(
    events_df: pd.DataFrame,
    price_dict: Dict[str, pd.DataFrame],
    benchmark_df: pd.DataFrame,
    vix_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """Constructs comprehensive pre-event features for each earnings event.

    CRITICAL ANTI-LEAKAGE RULE:
    All market observations must strictly terminate on or before the last trading day
    prior to the information becoming tradable.

    Features generated:
    - pre_event_return_5d, 10d, 21d, 63d
    - pre_event_vol_10d, 21d, 63d
    - pre_event_vol_zscore (21d volume vs 63d volume baseline)
    - pre_event_drawdown_63d
    - pre_event_market_return_21d
    - pre_event_beta (252d to 30d window)
    - pre_event_vix
    - sue (point-in-time)
    """
    df = events_df.copy()

    # Calculate point-in-time SUE
    df["sue"] = compute_point_in_time_sue(df)

    # Output feature columns
    feat_cols = [
        "pre_ret_5d", "pre_ret_10d", "pre_ret_21d", "pre_ret_63d",
        "pre_vol_10d", "pre_vol_21d", "pre_vol_63d",
        "pre_volume_zscore", "pre_drawdown_63d",
        "pre_market_ret_21d", "market_beta", "pre_vix"
    ]
    for c in feat_cols:
        df[c] = np.nan

    # Benchmark returns
    bench_close = benchmark_df["Close"]
    bench_returns = bench_close.pct_change()

    for idx, row in df.iterrows():
        ticker = row["ticker"]
        if ticker not in price_dict or price_dict[ticker] is None or price_dict[ticker].empty:
            continue

        p_df = price_dict[ticker]
        ann_date = pd.to_datetime(row["announcement_date"]).normalize()
        timing = row.get("timing_class", "UNKNOWN")

        # Determine cutoff date:
        # If BMO: info arrives before market opens on ann_date. The last observable close is prior trading day.
        # If AMC: info arrives after market closes on ann_date. The close on ann_date is observable BEFORE trading next morning.
        # If UNKNOWN: conservative cutoff is prior trading day to eliminate any possibility of look-ahead.
        if timing == "BMO" or timing == "UNKNOWN":
            prior_dates = p_df.index[p_df.index < ann_date]
        else:  # AMC
            prior_dates = p_df.index[p_df.index <= ann_date]

        if len(prior_dates) < 65:
            continue

        cutoff_idx = prior_dates[-1]
        p_slice = p_df.loc[:cutoff_idx]
        close_series = p_slice["Close"]
        vol_series = p_slice["Volume"]

        if len(close_series) < 64:
            continue

        # Returns
        p_now = close_series.iloc[-1]
        df.loc[idx, "pre_ret_5d"] = float((p_now / close_series.iloc[-6]) - 1.0) if len(close_series) >= 6 else np.nan
        df.loc[idx, "pre_ret_10d"] = float((p_now / close_series.iloc[-11]) - 1.0) if len(close_series) >= 11 else np.nan
        df.loc[idx, "pre_ret_21d"] = float((p_now / close_series.iloc[-22]) - 1.0) if len(close_series) >= 22 else np.nan
        df.loc[idx, "pre_ret_63d"] = float((p_now / close_series.iloc[-64]) - 1.0) if len(close_series) >= 64 else np.nan

        # Volatilities (annualized 252 days)
        daily_rets = close_series.pct_change().dropna()
        df.loc[idx, "pre_vol_10d"] = float(daily_rets.iloc[-10:].std() * np.sqrt(252)) if len(daily_rets) >= 10 else np.nan
        df.loc[idx, "pre_vol_21d"] = float(daily_rets.iloc[-21:].std() * np.sqrt(252)) if len(daily_rets) >= 21 else np.nan
        df.loc[idx, "pre_vol_63d"] = float(daily_rets.iloc[-63:].std() * np.sqrt(252)) if len(daily_rets) >= 63 else np.nan

        # Volume z-score: 5d avg vs 63d mean / std
        if len(vol_series) >= 63:
            v_base = vol_series.iloc[-63:]
            std_v = v_base.std()
            df.loc[idx, "pre_volume_zscore"] = float((vol_series.iloc[-5:].mean() - v_base.mean()) / (std_v if std_v > 0 else 1.0))

        # Max drawdown in prior 63 days
        roll_max = close_series.iloc[-63:].cummax()
        dd = (close_series.iloc[-63:] - roll_max) / roll_max
        df.loc[idx, "pre_drawdown_63d"] = float(dd.min())

        # Pre-event market return
        bench_slice = bench_close.loc[:cutoff_idx]
        if len(bench_slice) >= 22:
            df.loc[idx, "pre_market_ret_21d"] = float((bench_slice.iloc[-1] / bench_slice.iloc[-22]) - 1.0)

        # Market Beta: estimated over [-252, -30] relative trading days
        if len(daily_rets) >= 120:
            stock_sub = daily_rets.iloc[-252:-30] if len(daily_rets) >= 252 else daily_rets.iloc[:-30]
            bench_sub = bench_returns.reindex(stock_sub.index).dropna()
            common_idx = stock_sub.index.intersection(bench_sub.index)
            if len(common_idx) >= 30:
                cov = np.cov(stock_sub.loc[common_idx], bench_sub.loc[common_idx])[0, 1]
                var_m = np.var(bench_sub.loc[common_idx])
                df.loc[idx, "market_beta"] = float(cov / var_m) if var_m > 1e-6 else 1.0
            else:
                df.loc[idx, "market_beta"] = 1.0
        else:
            df.loc[idx, "market_beta"] = 1.0

        # VIX
        if vix_df is not None and not vix_df.empty:
            vix_slice = vix_df.loc[:cutoff_idx]
            if not vix_slice.empty and "Close" in vix_slice.columns:
                df.loc[idx, "pre_vix"] = float(vix_slice["Close"].iloc[-1])

    return df
