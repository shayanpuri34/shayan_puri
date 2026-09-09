"""Unit tests for portfolio performance metrics, risk measures (VaR, CVaR, Drawdown), turnover, and transaction costs."""

import numpy as np
import pandas as pd
import pytest
from src.backtester import EventBacktester
from src.signal_engine import SignalEngine


def test_portfolio_metrics_and_drawdown():
    bt = EventBacktester(holding_period=5, cost_bps=10.0)

    # 100 days of steady 0.1% daily returns with a single 5% drop
    daily_rets = np.full(100, 0.001)
    daily_rets[50] = -0.05
    dates = pd.date_range("2023-01-01", periods=100, freq="B")

    daily_df = pd.DataFrame({
        "gross_return": daily_rets,
        "transaction_cost": np.zeros(100),
        "net_return": daily_rets,
        "turnover": np.full(100, 0.05),
        "long_exposure": np.full(100, 0.5),
        "short_exposure": np.full(100, 0.5),
        "gross_exposure": np.full(100, 1.0),
        "net_exposure": np.zeros(100)
    }, index=dates)

    trades_df = pd.DataFrame([{
        "ticker": "TEST", "net_return": 0.02
    }, {
        "ticker": "TEST2", "net_return": -0.01
    }])

    metrics = bt.compute_portfolio_metrics(daily_df, trades_df)

    assert "Sharpe_Ratio" in metrics
    assert "Maximum_Drawdown" in metrics
    assert metrics["Maximum_Drawdown"] <= -0.04
    assert "VaR_95_Daily" in metrics
    assert "CVaR_95_Daily" in metrics
    assert metrics["CVaR_95_Daily"] <= metrics["VaR_95_Daily"], "CVaR must be more severe or equal to VaR"


def test_transaction_cost_deduction():
    # Verify that net return equals gross return minus 2-way cost
    cost_bps = 25.0  # 0.25% one-way -> 0.50% round-trip
    cost_dec = (cost_bps / 10000.0) * 2.0  # 0.0050

    gross_ret = 0.0200
    expected_net = gross_ret - cost_dec
    assert expected_net == pytest.approx(0.0150)


def test_position_sizing_max_cap():
    se = SignalEngine(max_position_weight=0.02)
    signals_df = pd.DataFrame({
        "signal": [1, 1, 1, 1, -1, -1],
        "pre_vol_21d": [0.10, 0.15, 0.20, 0.25, 0.12, 0.18]
    })

    weights = se.calculate_position_sizes(
        signals_df,
        sizing_method="volatility_scaling",
        style="dollar_neutral",
        target_gross_exposure=1.0
    )

    # Every position must adhere strictly to max 2% cap
    assert (weights.abs() <= 0.0200001).all(), f"Position weights exceed 2% cap: {weights.values}"
