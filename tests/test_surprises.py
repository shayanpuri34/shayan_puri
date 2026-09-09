"""Unit tests for earnings and revenue surprise calculations and zero-estimate safety."""

import numpy as np
import pandas as pd
import pytest
from src.feature_engineering import (
    compute_eps_surprise,
    compute_eps_surprise_pct,
    compute_revenue_surprise,
    compute_revenue_surprise_pct,
    compute_point_in_time_sue,
)


def test_eps_surprise_basic():
    # Actual 1.25, estimate 1.00 -> surprise +0.25, +25%
    assert compute_eps_surprise(1.25, 1.00) == pytest.approx(0.25)
    assert compute_eps_surprise_pct(1.25, 1.00) == pytest.approx(0.25)

    # Actual 0.80, estimate 1.00 -> surprise -0.20, -20%
    assert compute_eps_surprise(0.80, 1.00) == pytest.approx(-0.20)
    assert compute_eps_surprise_pct(0.80, 1.00) == pytest.approx(-0.20)


def test_zero_estimate_handling():
    # Zero estimate must return NaN, not infinity or ZeroDivisionError
    res_pct = compute_eps_surprise_pct(0.15, 0.0)
    assert np.isnan(res_pct), "Expected NaN when estimate is zero"

    res_rev = compute_revenue_surprise_pct(100.0, 0.0)
    assert np.isnan(res_rev), "Expected NaN when revenue estimate is zero"


def test_missing_and_nan_values():
    assert np.isnan(compute_eps_surprise(np.nan, 1.0))
    assert np.isnan(compute_eps_surprise(1.0, np.nan))
    assert np.isnan(compute_eps_surprise_pct(np.nan, 1.0))
    assert np.isnan(compute_revenue_surprise(None, 50.0))


def test_point_in_time_sue_no_future_leakage():
    # Construct a sample event series for a ticker
    events = pd.DataFrame([
        {"ticker": "AAPL", "announcement_date": "2020-01-28", "eps_surprise": 0.10},
        {"ticker": "AAPL", "announcement_date": "2020-04-28", "eps_surprise": 0.12},
        {"ticker": "AAPL", "announcement_date": "2020-07-28", "eps_surprise": 0.15},
        {"ticker": "AAPL", "announcement_date": "2020-10-28", "eps_surprise": 0.50},
    ])
    sue = compute_point_in_time_sue(events, min_prior_events=2)
    assert len(sue) == 4
    # Event 0 has 0 prior events
    assert not np.isnan(sue.iloc[0])
    # Event 3 SUE must be computed using std of events 0, 1, 2 only, NOT event 3
    prior_std = np.std([0.10, 0.12, 0.15], ddof=1)
    expected_sue_3 = 0.50 / prior_std
    assert sue.iloc[3] == pytest.approx(expected_sue_3, rel=1e-3)
