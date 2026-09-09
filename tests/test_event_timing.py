"""Unit tests for event timing classifications, trading calendar alignment, and look-ahead prevention."""

import pandas as pd
import pytest
from src.event_standardizer import (
    classify_announcement_timing,
    deduplicate_events,
    get_first_tradable_day,
    resolve_next_trading_day,
    resolve_strictly_next_trading_day,
    standardize_events,
)
from src.backtester import EventBacktester


def test_classify_announcement_timing():
    assert classify_announcement_timing("BMO") == "BMO"
    assert classify_announcement_timing("08:00") == "BMO"
    assert classify_announcement_timing("AMC") == "AMC"
    assert classify_announcement_timing("16:30") == "AMC"
    assert classify_announcement_timing("12:00") == "UNKNOWN"
    assert classify_announcement_timing(None) == "UNKNOWN"


def test_trading_calendar_resolution():
    calendar = [
        pd.Timestamp("2023-01-03"),  # Tuesday (Jan 2 was New Year holiday)
        pd.Timestamp("2023-01-04"),  # Wednesday
        pd.Timestamp("2023-01-05"),  # Thursday
        pd.Timestamp("2023-01-06"),  # Friday
        pd.Timestamp("2023-01-09"),  # Monday
    ]

    # Tuesday morning: next trading day is Tuesday
    assert resolve_next_trading_day("2023-01-03", calendar) == pd.Timestamp("2023-01-03")

    # Friday after market close: strictly next trading day is Monday
    assert resolve_strictly_next_trading_day("2023-01-06", calendar) == pd.Timestamp("2023-01-09")

    # Over weekend (Saturday 2023-01-07): next trading day is Monday
    assert resolve_next_trading_day("2023-01-07", calendar) == pd.Timestamp("2023-01-09")


def test_amc_handling_does_not_trade_pre_announcement_close():
    """CRITICAL TEST: Verifies that an AMC event does NOT generate a trade using the

    closing return that occurred before the earnings announcement.
    """
    trading_days = [
        pd.Timestamp("2023-04-20"),  # Day of AMC announcement
        pd.Timestamp("2023-04-21"),  # Day after AMC announcement (first tradable day)
        pd.Timestamp("2023-04-24"),  # Subsequent day
        pd.Timestamp("2023-04-25"),
    ]

    ann_date = "2023-04-20"
    timing = "AMC"

    first_tradable = get_first_tradable_day(ann_date, timing, trading_days)

    # AMC event announced after close on 2023-04-20 cannot trade on 2023-04-20
    assert first_tradable == pd.Timestamp("2023-04-21"), (
        f"AMC event must trade strictly on 2023-04-21, but got {first_tradable}"
    )
    assert first_tradable > pd.Timestamp(ann_date), "Entry date must be strictly after announcement date"


def test_bmo_handling():
    trading_days = [
        pd.Timestamp("2023-04-20"),  # Day of BMO announcement
        pd.Timestamp("2023-04-21"),
    ]
    ann_date = "2023-04-20"
    timing = "BMO"

    first_tradable = get_first_tradable_day(ann_date, timing, trading_days)
    # BMO event announced before open on 2023-04-20 trades on 2023-04-20
    assert first_tradable == pd.Timestamp("2023-04-20")


def test_unknown_timing_conservative():
    """Conservative policy mandates UNKNOWN timing trades no earlier than next full trading session."""
    trading_days = [
        pd.Timestamp("2023-04-20"),
        pd.Timestamp("2023-04-21"),
    ]
    first_tradable = get_first_tradable_day("2023-04-20", "UNKNOWN", trading_days)
    assert first_tradable == pd.Timestamp("2023-04-21")


def test_event_deduplication():
    raw_events = [
        {
            "ticker": "AAPL", "announcement_date": "2023-01-26",
            "fiscal_year": 2023, "fiscal_quarter": 1,
            "eps_actual": 1.88, "eps_estimate": 1.94,
            "source": "yfinance"
        },
        {
            "ticker": "AAPL", "announcement_date": "2023-01-26",
            "fiscal_year": 2023, "fiscal_quarter": 1,
            "eps_actual": 1.88, "eps_estimate": 1.94,
            "source": "alpha_vantage"  # Higher priority
        }
    ]
    std = standardize_events(raw_events)
    dedup, conflicts = deduplicate_events(std)
    assert len(dedup) == 1
    assert dedup.iloc[0]["source"] == "alpha_vantage"
    assert len(conflicts) == 1
