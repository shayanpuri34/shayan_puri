"""Unit tests for Market Model, Abnormal Returns, and CAR calculations."""

import numpy as np
import pandas as pd
import pytest
from src.event_study import EventStudyEngine, analyze_surprise_quintiles


def test_abnormal_returns_and_car():
    engine = EventStudyEngine(estimation_window=(-50, -10))

    # Generate synthetic prices
    dates = pd.date_range("2022-01-01", "2023-01-01", freq="B")
    np.random.seed(42)
    bench_returns = np.random.normal(0.0005, 0.01, len(dates))
    stock_returns = 0.0002 + 1.2 * bench_returns + np.random.normal(0, 0.005, len(dates))

    bench_prices = 100 * np.exp(np.cumsum(bench_returns))
    stock_prices = 50 * np.exp(np.cumsum(stock_returns))

    bench_df = pd.DataFrame({"Close": bench_prices}, index=dates)
    stock_df = pd.DataFrame({"Close": stock_prices}, index=dates)

    events_df = pd.DataFrame([{
        "ticker": "TEST",
        "announcement_date": "2022-08-15",
        "timing_class": "AMC",
        "eps_surprise_pct": 0.05
    }])

    price_dict = {"TEST": stock_df}
    res_df, ar_mat, stats_df = engine.compute_event_study(events_df, price_dict, bench_df)

    assert not res_df.empty
    assert "CAR[0,+1]" in res_df.columns
    assert "alpha" in res_df.columns
    assert "beta" in res_df.columns
    assert not np.isnan(res_df.iloc[0]["beta"])
    assert res_df.iloc[0]["beta"] == pytest.approx(1.2, abs=0.3)


def test_surprise_quintiles():
    np.random.seed(42)
    n = 100
    events = pd.DataFrame({
        "ticker": ["SYM"] * n,
        "announcement_date": pd.date_range("2020-01-01", periods=n, freq="W"),
        "eps_surprise_pct": np.linspace(-0.20, 0.20, n),
        "CAR[0,+1]": np.linspace(-0.03, 0.04, n) + np.random.normal(0, 0.005, n),
        "CAR[+1,+5]": np.linspace(-0.02, 0.03, n),
        "CAR[+1,+20]": np.linspace(-0.04, 0.05, n)
    })

    q_df = analyze_surprise_quintiles(events, q=5)
    assert len(q_df) == 5
    # Check monotonicity of surprise
    assert q_df.iloc[0]["Avg_Surprise_Pct"] < q_df.iloc[-1]["Avg_Surprise_Pct"]
    # Check monotonicity of CAR
    assert q_df.iloc[0]["Avg_CAR"] < q_df.iloc[-1]["Avg_CAR"]
