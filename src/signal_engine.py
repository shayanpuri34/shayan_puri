"""Signal construction and position sizing module.
Transforms surprises and ML outputs into actionable portfolio weights with risk scaling and constraints.
"""

import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger("earnings_engine.signal_engine")


class SignalEngine:
    """Computes trading signals, composite scores, and risk-constrained position sizes."""

    def __init__(
        self,
        upper_quantile: float = 0.80,
        lower_quantile: float = 0.20,
        composite_weights: Optional[Dict[str, float]] = None,
        max_position_weight: float = 0.02
    ):
        self.upper_quantile = upper_quantile
        self.lower_quantile = lower_quantile
        self.max_position_weight = max_position_weight
        self.weights = composite_weights or {
            "w1_eps_surprise": 0.35,
            "w2_revenue_surprise": 0.25,
            "w3_momentum": 0.15,
            "w4_volume_shock": 0.15,
            "w5_historical_reaction": 0.10,
        }

    def generate_surprise_signals(
        self,
        events_df: pd.DataFrame,
        signal_col: str = "eps_surprise_pct"
    ) -> pd.DataFrame:
        """Generates ternary (+1, 0, -1) earnings surprise signal based on point-in-time quantile thresholds."""
        df = events_df.copy()
        df["signal"] = 0

        # Sort chronologically to determine thresholds point-in-time
        df = df.sort_values(by="announcement_date").reset_index(drop=True)

        if signal_col not in df.columns:
            logger.warning(f"Signal column '{signal_col}' not found in events DataFrame.")
            return df

        valid_vals = df[signal_col].dropna()
        if len(valid_vals) < 10:
            return df

        # Expanding window or fixed historical quantile to avoid look-ahead bias
        # For base research, use expanding percentile
        expanding_q_high = df[signal_col].expanding(min_periods=10).quantile(self.upper_quantile)
        expanding_q_low = df[signal_col].expanding(min_periods=10).quantile(self.lower_quantile)

        # Signal assignment
        df["signal"] = np.where(
            df[signal_col] >= expanding_q_high,
            1,
            np.where(df[signal_col] <= expanding_q_low, -1, 0)
        )
        return df

    def generate_composite_score(self, events_df: pd.DataFrame) -> pd.DataFrame:
        """Computes multi-factor composite score combining EPS surprise, Revenue surprise,

        momentum, volume shock, and historical reaction.
        """
        df = events_df.copy()

        def _standardize(col_name: str) -> pd.Series:
            if col_name in df.columns:
                s = df[col_name].fillna(0)
                std_val = s.std()
                return (s - s.mean()) / (std_val if std_val > 0 else 1.0)
            return pd.Series(0.0, index=df.index)

        z_eps = _standardize("eps_surprise_pct")
        z_rev = _standardize("revenue_surprise_pct")
        z_mom = _standardize("pre_ret_21d")
        z_vol = _standardize("pre_volume_zscore")
        z_react = _standardize("sue")

        df["composite_score"] = (
            self.weights.get("w1_eps_surprise", 0.35) * z_eps +
            self.weights.get("w2_revenue_surprise", 0.25) * z_rev +
            self.weights.get("w3_momentum", 0.15) * z_mom +
            self.weights.get("w4_volume_shock", 0.15) * z_vol +
            self.weights.get("w5_historical_reaction", 0.10) * z_react
        )

        # Composite signal thresholding
        high_thresh = df["composite_score"].expanding(min_periods=10).quantile(self.upper_quantile)
        low_thresh = df["composite_score"].expanding(min_periods=10).quantile(self.lower_quantile)

        df["composite_signal"] = np.where(
            df["composite_score"] >= high_thresh,
            1,
            np.where(df["composite_score"] <= low_thresh, -1, 0)
        )
        return df

    def calculate_position_sizes(
        self,
        signals_df: pd.DataFrame,
        sizing_method: str = "equal_weight",
        style: str = "dollar_neutral",
        target_gross_exposure: float = 1.0
    ) -> pd.Series:
        """Sizes individual trade positions subject to style, sizing method, and max 2% single-position cap."""
        df = signals_df.copy()
        weights = pd.Series(0.0, index=df.index)

        signal_series = df.get("signal", pd.Series(0, index=df.index))
        active_mask = signal_series != 0
        if not active_mask.any():
            return weights

        # Base sizing factor
        if sizing_method == "volatility_scaling" and "pre_vol_21d" in df.columns:
            # Weight inversely proportional to 21-day volatility
            vol = df["pre_vol_21d"].clip(lower=0.05, upper=1.0).fillna(0.20)
            raw_weights = signal_series / vol
        elif sizing_method == "confidence_scaling" and "composite_score" in df.columns:
            raw_weights = signal_series * df["composite_score"].abs().clip(lower=0.1, upper=5.0)
        else:  # equal_weight
            raw_weights = signal_series.astype(float)

        if style == "long_only":
            longs = raw_weights.clip(lower=0.0)
            tot_long = longs.sum()
            if tot_long > 0:
                weights = (longs / tot_long) * target_gross_exposure
        else:  # dollar_neutral
            longs = raw_weights.clip(lower=0.0)
            shorts = raw_weights.clip(upper=0.0).abs()

            tot_long = longs.sum()
            tot_short = shorts.sum()

            target_leg = target_gross_exposure / 2.0
            w_long = (longs / tot_long * target_leg) if tot_long > 0 else longs
            w_short = (shorts / tot_short * target_leg) if tot_short > 0 else shorts
            weights = w_long - w_short

        # Apply maximum position limit constraint (default 2% per position)
        weights = weights.clip(lower=-self.max_position_weight, upper=self.max_position_weight)

        # Normalize back to target gross exposure if non-zero
        gross = weights.abs().sum()
        if gross > target_gross_exposure and gross > 0:
            weights = weights * (target_gross_exposure / gross)

        return weights
