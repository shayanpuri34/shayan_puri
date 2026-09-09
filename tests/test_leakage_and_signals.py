"""Unit tests for anti-leakage guards and signal generation integrity."""

import numpy as np
import pandas as pd
import pytest
from src.leakage_audit import LeakageAuditor
from src.signal_engine import SignalEngine


def test_signal_cannot_use_future_returns():
    """CRITICAL TEST: Verifies that signal generation at event t relies exclusively on

    information available at or before announcement, and contains NO forward-looking returns.
    """
    se = SignalEngine(upper_quantile=0.80, lower_quantile=0.20)

    # DataFrame with historical surprises and future returns
    df = pd.DataFrame([
        {"ticker": "AAPL", "announcement_date": "2021-01-28", "eps_surprise_pct": 0.10, "future_return_5d": -0.05},
        {"ticker": "AAPL", "announcement_date": "2021-04-28", "eps_surprise_pct": 0.15, "future_return_5d": 0.08},
        {"ticker": "AAPL", "announcement_date": "2021-07-28", "eps_surprise_pct": -0.05, "future_return_5d": 0.12},
        {"ticker": "AAPL", "announcement_date": "2021-10-28", "eps_surprise_pct": 0.25, "future_return_5d": -0.02},
        {"ticker": "AAPL", "announcement_date": "2022-01-28", "eps_surprise_pct": -0.10, "future_return_5d": -0.09},
    ])

    res = se.generate_surprise_signals(df, signal_col="eps_surprise_pct")

    # Verify that signal is NOT correlated with future_return_5d when surprise contradicts future return
    # E.g. Event 2: negative surprise (-0.05) must produce signal <= 0 despite positive future return (+0.12)
    ev2 = res.iloc[2]
    assert ev2["signal"] <= 0, f"Signal should not anticipate future positive return; got {ev2['signal']}"

    # E.g. Event 3: positive surprise (+0.25) must produce signal >= 0 despite negative future return (-0.02)
    ev3 = res.iloc[3]
    assert ev3["signal"] >= 0, f"Signal should not anticipate future negative return; got {ev3['signal']}"


def test_leakage_audit_catches_leaked_target_in_features():
    auditor = LeakageAuditor()
    events_df = pd.DataFrame([{"ticker": "AAPL", "announcement_date": "2023-01-01", "timing_class": "AMC"}])
    trades_df = pd.DataFrame([{
        "ticker": "AAPL",
        "announcement_date": "2023-01-01",
        "entry_date": pd.Timestamp("2023-01-02"),
        "timing_class": "AMC",
        "transaction_cost": 0.001
    }])

    # Purposely include forbidden future target column in feature list
    tainted_features = ["pre_ret_21d", "CAR[+1,+5]", "future_return"]
    passed, report = auditor.run_full_audit(events_df, trades_df, tainted_features)

    # Must FAIL check 15
    assert not passed, "Auditor should fail when future target returns are present in feature list"
    c15 = report[report["Check_ID"] == 15].iloc[0]
    assert c15["Status"] == "FAIL"


def test_leakage_audit_passes_on_clean_data():
    auditor = LeakageAuditor()
    events_df = pd.DataFrame([{"ticker": "AAPL", "announcement_date": "2023-01-01", "timing_class": "AMC"}])
    trades_df = pd.DataFrame([{
        "ticker": "AAPL",
        "announcement_date": "2023-01-01",
        "entry_date": pd.Timestamp("2023-01-02"),
        "timing_class": "AMC",
        "transaction_cost": 0.001
    }])

    clean_features = ["pre_ret_21d", "pre_vol_21d", "sue", "eps_surprise_pct"]
    passed, report = auditor.run_full_audit(events_df, trades_df, clean_features)

    assert passed, f"Auditor should pass on clean pipeline. Report: {report.to_dict()}"
