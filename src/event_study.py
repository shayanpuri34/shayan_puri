"""Event study methodology module.
Implements the Market Model, Abnormal Returns (AR), Cumulative Abnormal Returns (CAR),
Average Abnormal Returns (AAR), CAAR, PEAD drift analysis, and bootstrap hypothesis testing.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from src.event_standardizer import resolve_next_trading_day, resolve_strictly_next_trading_day

logger = logging.getLogger("earnings_engine.event_study")


class EventStudyEngine:
    """Executes market-model event studies with correct relative-day timeline indexing."""

    def __init__(
        self,
        estimation_window: Tuple[int, int] = (-252, -30),
        min_estimation_obs: int = 60,
        random_state: int = 42
    ):
        self.estimation_window = estimation_window
        self.min_estimation_obs = min_estimation_obs
        self.rng = np.random.RandomState(random_state)

    def compute_event_study(
        self,
        events_df: pd.DataFrame,
        price_dict: Dict[str, pd.DataFrame],
        benchmark_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Computes abnormal returns and event windows for every event in events_df.

        Returns:
        1. event_results_df: events_df augmented with CAR[-1,+1], CAR[-2,+2], CAR[0,+1], CAR[0,+5], CAR[0,+20], CAR[+1,+5], CAR[+1,+20]
        2. daily_ar_matrix: DataFrame of shape (N_events, 41) spanning relative days t = -20 to +20
        3. window_summary: statistical test table for each primary window
        """
        bench_close = benchmark_df["Close"]
        bench_returns = bench_close.pct_change().dropna()
        trading_days = benchmark_df.index.tolist()

        augmented_events = events_df.copy()

        # Initialize result columns
        target_windows = [
            ("CAR[-5,+5]", -5, 5),
            ("CAR[-2,+2]", -2, 2),
            ("CAR[-1,+1]", -1, 1),
            ("CAR[0,+1]", 0, 1),
            ("CAR[0,+5]", 0, 5),
            ("CAR[0,+20]", 0, 20),
            ("CAR[+1,+5]", 1, 5),    # PEAD 5-day
            ("CAR[+1,+20]", 1, 20),  # PEAD 20-day
        ]
        for name, _, _ in target_windows:
            augmented_events[name] = np.nan

        augmented_events["alpha"] = np.nan
        augmented_events["beta"] = np.nan
        augmented_events["event_t0_date"] = pd.NaT

        relative_days = list(range(-20, 21))
        ar_records = []
        valid_indices = []

        for idx, row in augmented_events.iterrows():
            ticker = row["ticker"]
            if ticker not in price_dict or price_dict[ticker] is None:
                continue

            p_df = price_dict[ticker]
            ann_date = pd.to_datetime(row["announcement_date"]).normalize()
            timing = row.get("timing_class", "UNKNOWN")

            # Determine Event Day T0:
            # - For BMO: announcement occurred before market open. T0 is the announcement date.
            # - For AMC: announcement occurred after market close. T0 is the NEXT trading session.
            # - For UNKNOWN: conservative assignment uses the NEXT trading session.
            if timing == "BMO":
                t0 = resolve_next_trading_day(ann_date, trading_days)
            else:  # AMC or UNKNOWN
                t0 = resolve_strictly_next_trading_day(ann_date, trading_days)

            if t0 is None or t0 not in p_df.index or t0 not in bench_returns.index:
                continue

            # Locate t0 integer position in stock calendar
            stock_days = p_df.index.tolist()
            try:
                t0_pos = stock_days.index(t0)
            except ValueError:
                continue

            # Check estimation window availability [-252, -30]
            est_start_pos = t0_pos + self.estimation_window[0]
            est_end_pos = t0_pos + self.estimation_window[1]

            if est_start_pos < 0 or est_end_pos <= est_start_pos:
                # Fallback to shorter historical window if available
                est_start_pos = max(0, t0_pos - 120)
                est_end_pos = max(10, t0_pos - 10)
                if est_end_pos - est_start_pos < 30:
                    continue

            # Estimate market model: R_i = alpha + beta * R_m
            stock_rets = p_df["Close"].pct_change().dropna()
            est_stock = stock_rets.iloc[est_start_pos:est_end_pos]
            est_bench = bench_returns.reindex(est_stock.index).dropna()
            common = est_stock.index.intersection(est_bench.index)

            if len(common) < 20:
                continue

            x = est_bench.loc[common].values
            y = est_stock.loc[common].values
            slope, intercept, _, _, _ = stats.linregress(x, y)

            alpha = intercept
            beta = slope if not np.isnan(slope) else 1.0

            augmented_events.loc[idx, "alpha"] = alpha
            augmented_events.loc[idx, "beta"] = beta
            augmented_events.loc[idx, "event_t0_date"] = t0

            # Compute AR for t in [-20, +20]
            event_ars = {}
            for t in relative_days:
                bar_pos = t0_pos + t
                if 0 <= bar_pos < len(stock_days):
                    dt_bar = stock_days[bar_pos]
                    if dt_bar in stock_rets.index and dt_bar in bench_returns.index:
                        r_i = stock_rets.loc[dt_bar]
                        r_m = bench_returns.loc[dt_bar]
                        ar = r_i - (alpha + beta * r_m)
                        event_ars[t] = ar
                    else:
                        event_ars[t] = np.nan
                else:
                    event_ars[t] = np.nan

            ar_records.append(event_ars)
            valid_indices.append(idx)

            # Compute CAR for each target window
            for w_name, w_start, w_end in target_windows:
                w_ars = [event_ars.get(d, np.nan) for d in range(w_start, w_end + 1)]
                if not any(np.isnan(w_ars)):
                    augmented_events.loc[idx, w_name] = float(np.sum(w_ars))

        ar_matrix = pd.DataFrame(ar_records, index=valid_indices)

        # Statistical testing for each window
        summary_rows = []
        for w_name, _, _ in target_windows:
            series = augmented_events[w_name].dropna()
            if len(series) >= 5:
                n = len(series)
                mean_car = float(series.mean())
                median_car = float(series.median())
                std_car = float(series.std(ddof=1))
                t_stat, p_val = stats.ttest_1samp(series, 0.0)

                # Bootstrap 95% confidence interval
                boot_means = [
                    np.mean(self.rng.choice(series.values, size=n, replace=True))
                    for _ in range(1000)
                ]
                ci_lower = float(np.percentile(boot_means, 2.5))
                ci_upper = float(np.percentile(boot_means, 97.5))

                summary_rows.append({
                    "Window": w_name,
                    "N": n,
                    "Mean_CAR": round(mean_car, 4),
                    "Median_CAR": round(median_car, 4),
                    "Std_Dev": round(std_car, 4),
                    "t_statistic": round(t_stat, 3),
                    "p_value": round(p_val, 5),
                    "CI_95_Lower": round(ci_lower, 4),
                    "CI_95_Upper": round(ci_upper, 4),
                    "Significant_5pct": bool(p_val < 0.05)
                })

        summary_df = pd.DataFrame(summary_rows)
        return augmented_events, ar_matrix, summary_df


def analyze_surprise_quintiles(
    events_df: pd.DataFrame,
    surprise_col: str = "eps_surprise_pct",
    car_col: str = "CAR[0,+1]",
    q: int = 5
) -> pd.DataFrame:
    """Sorts events into surprise quintiles and evaluates monotonicity and post-announcement drift."""
    valid = events_df.dropna(subset=[surprise_col, car_col]).copy()
    if len(valid) < q * 2:
        return pd.DataFrame()

    # Sort into quantile buckets
    valid["bucket"] = pd.qcut(valid[surprise_col], q=q, labels=[f"Q{i+1}" for i in range(q)])

    stats_list = []
    for b_name, grp in valid.groupby("bucket"):
        n = len(grp)
        avg_surp = float(grp[surprise_col].mean())
        avg_car = float(grp[car_col].mean())
        med_car = float(grp[car_col].median())
        win_rate = float((grp[car_col] > 0).mean())
        pead_5d = float(grp["CAR[+1,+5]"].mean()) if "CAR[+1,+5]" in grp.columns else np.nan
        pead_20d = float(grp["CAR[+1,+20]"].mean()) if "CAR[+1,+20]" in grp.columns else np.nan

        stats_list.append({
            "Quintile": b_name,
            "N": n,
            "Avg_Surprise_Pct": round(avg_surp, 4),
            "Avg_CAR": round(avg_car, 4),
            "Median_CAR": round(med_car, 4),
            "Win_Rate": round(win_rate, 4),
            "PEAD_CAR[+1,+5]": round(pead_5d, 4),
            "PEAD_CAR[+1,+20]": round(pead_20d, 4),
        })

    return pd.DataFrame(stats_list)
