"""Market regime classification and sector attribution module.
Analyzes strategy performance conditioned on market trend (Bull/Bear), volatility (Low/Normal/High),
and industry sector without future information leakage.
"""

import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger("earnings_engine.regime_sector")


def classify_market_regimes(
    benchmark_df: pd.DataFrame,
    vix_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """Classifies every trading day into trend regimes (Bull/Bear) and volatility regimes (Low/Normal/High)

    using only lagged point-in-time information (e.g. 200-day simple moving average).
    """
    df = pd.DataFrame(index=benchmark_df.index)
    close = benchmark_df["Close"]

    # Trend regime: Bull if Close >= 200D SMA, else Bear
    sma_200 = close.rolling(window=200, min_periods=50).mean()
    df["trend_regime"] = np.where(close >= sma_200, "Bull", "Bear")

    # Volatility regime
    if vix_df is not None and not vix_df.empty and "Close" in vix_df.columns:
        vix_series = vix_df["Close"].reindex(df.index).ffill()
        df["vol_regime"] = np.where(
            vix_series < 16.0, "Low_Vol",
            np.where(vix_series > 24.0, "High_Vol", "Normal_Vol")
        )
    else:
        # 21-day realized volatility of benchmark as fallback
        realized_vol = close.pct_change().rolling(21).std() * np.sqrt(252)
        q33 = realized_vol.expanding(min_periods=60).quantile(0.33)
        q66 = realized_vol.expanding(min_periods=60).quantile(0.66)
        df["vol_regime"] = np.where(
            realized_vol < q33, "Low_Vol",
            np.where(realized_vol > q66, "High_Vol", "Normal_Vol")
        )

    return df


def analyze_regime_performance(
    daily_portfolio_df: pd.DataFrame,
    regimes_df: pd.DataFrame
) -> pd.DataFrame:
    """Computes strategy return, volatility, Sharpe ratio, and hit rate across distinct market regimes."""
    if daily_portfolio_df.empty or "net_return" not in daily_portfolio_df.columns:
        return pd.DataFrame()

    merged = daily_portfolio_df[["net_return"]].join(regimes_df, how="inner")
    rows = []

    for reg_col in ["trend_regime", "vol_regime"]:
        if reg_col not in merged.columns:
            continue
        for reg_val, grp in merged.groupby(reg_col):
            rets = grp["net_return"].dropna()
            if len(rets) < 10:
                continue

            ann_ret = float(rets.mean() * 252.0)
            ann_vol = float(rets.std() * np.sqrt(252))
            sharpe = float(ann_ret / ann_vol) if ann_vol > 1e-4 else 0.0
            win_rate = float((rets > 0).mean())

            rows.append({
                "Regime_Type": reg_col.replace("_regime", "").capitalize(),
                "Regime": str(reg_val),
                "Days": len(rets),
                "Ann_Return": round(ann_ret, 4),
                "Ann_Volatility": round(ann_vol, 4),
                "Sharpe_Ratio": round(sharpe, 3),
                "Daily_Win_Rate": round(win_rate, 4),
            })

    return pd.DataFrame(rows)


def analyze_sector_performance(
    events_df: pd.DataFrame,
    trades_df: pd.DataFrame,
    sector_map: Dict[str, str]
) -> pd.DataFrame:
    """Evaluates earnings surprise magnitude, event abnormal returns, and strategy trade win rate grouped by sector."""
    if events_df.empty:
        return pd.DataFrame()

    df_events = events_df.copy()
    df_events["sector"] = df_events["ticker"].map(lambda t: sector_map.get(t, "Other"))

    trades_by_ticker = {}
    if not trades_df.empty:
        for ticker, grp in trades_df.groupby("ticker"):
            trades_by_ticker[ticker] = {
                "trade_count": len(grp),
                "avg_net_return": float(grp["net_return"].mean()),
                "win_rate": float((grp["net_return"] > 0).mean())
            }

    rows = []
    for sector, grp in df_events.groupby("sector"):
        n_events = len(grp)
        avg_surp = float(grp["eps_surprise_pct"].dropna().mean()) if "eps_surprise_pct" in grp.columns else np.nan
        avg_car01 = float(grp["CAR[0,+1]"].dropna().mean()) if "CAR[0,+1]" in grp.columns else np.nan
        avg_pead5 = float(grp["CAR[+1,+5]"].dropna().mean()) if "CAR[+1,+5]" in grp.columns else np.nan

        # Match trades in this sector
        sec_tickers = grp["ticker"].unique()
        sec_trades = [trades_by_ticker[t] for t in sec_tickers if t in trades_by_ticker]

        tot_trades = sum(t["trade_count"] for t in sec_trades)
        if tot_trades > 0:
            avg_trade_ret = float(np.average([t["avg_net_return"] for t in sec_trades], weights=[t["trade_count"] for t in sec_trades]))
            sec_win_rate = float(np.average([t["win_rate"] for t in sec_trades], weights=[t["trade_count"] for t in sec_trades]))
        else:
            avg_trade_ret = 0.0
            sec_win_rate = 0.0

        rows.append({
            "Sector": sector,
            "Total_Events": n_events,
            "Avg_Surprise_Pct": round(avg_surp, 4) if not np.isnan(avg_surp) else 0.0,
            "Avg_CAR[0,+1]": round(avg_car01, 4) if not np.isnan(avg_car01) else 0.0,
            "Avg_PEAD_CAR[+1,+5]": round(avg_pead5, 4) if not np.isnan(avg_pead5) else 0.0,
            "Strategy_Trades": tot_trades,
            "Avg_Trade_Return": round(avg_trade_ret, 4),
            "Trade_Win_Rate": round(sec_win_rate, 4),
        })

    return pd.DataFrame(rows)
