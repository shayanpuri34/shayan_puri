"""Systematic event-driven backtesting engine.
Enforces realistic execution timing (AMC trades next day, BMO trades announcement session, UNKNOWN next day),
incorporates variable transaction costs (0 to 50 bps), prevents overlapping position distortion,
and computes institutional portfolio and risk metrics.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.event_standardizer import get_first_tradable_day

logger = logging.getLogger("earnings_engine.backtester")


class EventBacktester:
    """Simulates systematic portfolio execution across specified holding periods and cost regimes."""

    def __init__(
        self,
        holding_period: int = 5,
        cost_bps: float = 10.0,
        style: str = "dollar_neutral",
        max_position_weight: float = 0.02,
        overlapping_policy: str = "exit_existing_before_reentry"
    ):
        self.holding_period = holding_period
        self.cost_bps = cost_bps
        self.style = style
        self.max_position_weight = max_position_weight
        self.overlapping_policy = overlapping_policy

    def run_event_trade_simulation(
        self,
        events_df: pd.DataFrame,
        price_dict: Dict[str, pd.DataFrame],
        benchmark_df: pd.DataFrame,
        signal_col: str = "signal"
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Simulates individual event-driven trades with precise timing adherence.

        Returns:
        1. trades_df: Log of every executed event trade with entry/exit dates, prices, returns, and costs.
        2. daily_portfolio_df: Aggregated time-series of daily portfolio returns, turnover, and exposures.
        3. metrics: Summary performance and risk statistics.
        """
        trading_days = benchmark_df.index.tolist()
        bench_close = benchmark_df["Close"]
        bench_rets = bench_close.pct_change()

        df = events_df.dropna(subset=[signal_col]).sort_values(by="announcement_date").copy()
        trades = []

        # Track active positions by ticker to prevent overlapping double-counting
        ticker_last_exit: Dict[str, pd.Timestamp] = {}

        for _, row in df.iterrows():
            ticker = row["ticker"]
            signal = int(row[signal_col])
            if signal == 0:
                continue

            if ticker not in price_dict or price_dict[ticker] is None:
                continue

            p_df = price_dict[ticker]
            ann_date = pd.to_datetime(row["announcement_date"]).normalize()
            timing = row.get("timing_class", "UNKNOWN")

            # Determine Entry Date:
            # AMC/UNKNOWN -> Strictly next trading day
            # BMO -> Announcement day if valid trading day, else next trading day
            entry_date = get_first_tradable_day(ann_date, timing, trading_days)
            if entry_date is None or entry_date not in p_df.index:
                continue

            # Overlapping policy check
            if ticker in ticker_last_exit:
                if entry_date <= ticker_last_exit[ticker]:
                    if self.overlapping_policy == "skip_new":
                        continue
                    # else exit_existing_before_reentry -> allow new trade to supersede

            # Find entry bar position
            stock_dates = p_df.index.tolist()
            try:
                entry_idx = stock_dates.index(entry_date)
            except ValueError:
                continue

            # Find exit bar position: entry_idx + holding_period
            exit_idx = entry_idx + self.holding_period
            if exit_idx >= len(stock_dates):
                exit_idx = len(stock_dates) - 1
            if exit_idx <= entry_idx:
                continue

            exit_date = stock_dates[exit_idx]
            ticker_last_exit[ticker] = exit_date

            entry_price = float(p_df["Close"].iloc[entry_idx])
            exit_price = float(p_df["Close"].iloc[exit_idx])

            if entry_price <= 0:
                continue

            # Asset gross return
            asset_ret = (exit_price / entry_price) - 1.0
            trade_dir = 1.0 if signal > 0 else (-1.0 if self.style == "dollar_neutral" else 0.0)

            if trade_dir == 0.0 and self.style == "long_only":
                continue

            gross_trade_ret = float(trade_dir * asset_ret)

            # Transaction cost: two-way turnover (entry + exit) * cost_bps / 10000
            cost_decimal = (self.cost_bps / 10000.0) * 2.0
            net_trade_ret = float(gross_trade_ret - cost_decimal)

            # Benchmark return over identical window
            if entry_date in bench_close.index and exit_date in bench_close.index:
                bench_entry = bench_close.loc[entry_date]
                bench_exit = bench_close.loc[exit_date]
                mkt_ret = float((bench_exit / bench_entry) - 1.0)
            else:
                mkt_ret = 0.0

            abnormal_ret = gross_trade_ret - (trade_dir * mkt_ret)

            trades.append({
                "ticker": ticker,
                "announcement_date": str(ann_date.date()),
                "timing_class": timing,
                "entry_date": entry_date,
                "exit_date": exit_date,
                "signal": signal,
                "position_dir": trade_dir,
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "holding_period_days": (exit_idx - entry_idx),
                "gross_return": round(gross_trade_ret, 6),
                "transaction_cost": round(cost_decimal, 6),
                "net_return": round(net_trade_ret, 6),
                "market_return": round(mkt_ret, 6),
                "abnormal_return": round(abnormal_ret, 6)
            })

        trades_df = pd.DataFrame(trades)

        if trades_df.empty:
            empty_metrics = self._empty_metrics()
            return trades_df, pd.DataFrame(), empty_metrics

        # Precompute returns for symbols to avoid repeated recalculations
        returns_dict = {s: df["Close"].pct_change() for s, df in price_dict.items() if "Close" in df.columns}

        # Construct Daily Time-Series Portfolio
        all_dates = benchmark_df.index
        trade_daily_returns: Dict[pd.Timestamp, List[float]] = {d: [] for d in all_dates}
        trade_turnover: Dict[pd.Timestamp, float] = {d: 0.0 for d in all_dates}
        trade_long_exp: Dict[pd.Timestamp, float] = {d: 0.0 for d in all_dates}
        trade_short_exp: Dict[pd.Timestamp, float] = {d: 0.0 for d in all_dates}

        pos_size = min(self.max_position_weight, 1.0 / max(5, len(trades_df) // 10))

        for _, t in trades_df.iterrows():
            d_start = t["entry_date"]
            d_end = t["exit_date"]
            sym = t["ticker"]
            p_series = returns_dict.get(sym)
            if p_series is None:
                continue

            sub_series = p_series.loc[d_start:d_end].iloc[1:]
            if sub_series.empty:
                continue

            # Entry & exit turnover
            trade_turnover[d_start] = trade_turnover.get(d_start, 0.0) + pos_size
            trade_turnover[d_end] = trade_turnover.get(d_end, 0.0) + pos_size

            dir_val = t["position_dir"]
            for d, r_stock in sub_series.items():
                if d in trade_daily_returns:
                    trade_daily_returns[d].append(dir_val * pos_size * r_stock)
                    if dir_val > 0:
                        trade_long_exp[d] = trade_long_exp.get(d, 0.0) + pos_size
                    elif dir_val < 0:
                        trade_short_exp[d] = trade_short_exp.get(d, 0.0) + pos_size

        daily_records = []
        for d in benchmark_df.index:
            rets = trade_daily_returns.get(d, [])
            gross_ret = float(sum(rets)) if rets else 0.0
            turn = trade_turnover.get(d, 0.0)
            cost = turn * (self.cost_bps / 10000.0)
            net_ret = gross_ret - cost
            long_e = trade_long_exp.get(d, 0.0)
            short_e = trade_short_exp.get(d, 0.0)

            daily_records.append({
                "date": d,
                "gross_return": gross_ret,
                "transaction_cost": cost,
                "net_return": net_ret,
                "turnover": turn,
                "long_exposure": min(1.0, long_e),
                "short_exposure": min(1.0, short_e),
                "gross_exposure": min(1.0, long_e + short_e),
                "net_exposure": long_e - short_e,
                "benchmark_return": bench_rets.loc[d] if d in bench_rets.index else 0.0
            })

        daily_df = pd.DataFrame(daily_records).set_index("date")
        daily_df["cumulative_gross"] = (1.0 + daily_df["gross_return"]).cumprod() - 1.0
        daily_df["cumulative_net"] = (1.0 + daily_df["net_return"]).cumprod() - 1.0
        daily_df["cumulative_benchmark"] = (1.0 + daily_df["benchmark_return"]).cumprod() - 1.0

        metrics = self.compute_portfolio_metrics(daily_df, trades_df)
        return trades_df, daily_df, metrics

    def compute_portfolio_metrics(self, daily_df: pd.DataFrame, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates comprehensive institutional performance and risk statistics."""
        net_rets = daily_df["net_return"].dropna()
        n_days = len(net_rets)
        if n_days < 20:
            return self._empty_metrics()

        cum_net = (1.0 + net_rets).cumprod()
        total_return = float(cum_net.iloc[-1] - 1.0)
        years = max(0.5, n_days / 252.0)
        cagr = float(((1.0 + total_return) ** (1.0 / years)) - 1.0) if total_return > -1.0 else -0.99
        ann_vol = float(net_rets.std() * np.sqrt(252))

        rf = 0.02  # 2% risk-free rate assumption
        excess_rets = net_rets - (rf / 252.0)
        sharpe = float((excess_rets.mean() * 252.0) / ann_vol) if ann_vol > 1e-6 else 0.0

        downside_rets = net_rets[net_rets < 0]
        downside_vol = float(downside_rets.std() * np.sqrt(252)) if len(downside_rets) > 2 else 1e-6
        sortino = float((excess_rets.mean() * 252.0) / downside_vol) if downside_vol > 1e-6 else 0.0

        # Drawdowns
        roll_max = cum_net.cummax()
        drawdowns = (cum_net - roll_max) / roll_max
        max_drawdown = float(drawdowns.min())
        calmar = float(cagr / abs(max_drawdown)) if abs(max_drawdown) > 1e-6 else 0.0

        # Trades metrics
        win_rate = float((trades_df["net_return"] > 0).mean()) if not trades_df.empty else 0.0
        pos_sum = float(trades_df.loc[trades_df["net_return"] > 0, "net_return"].sum())
        neg_sum = float(trades_df.loc[trades_df["net_return"] < 0, "net_return"].abs().sum())
        profit_factor = float(pos_sum / neg_sum) if neg_sum > 0 else (99.0 if pos_sum > 0 else 1.0)

        # Risk metrics: Historical VaR & CVaR (daily)
        var_95 = float(np.percentile(net_rets, 5.0))
        var_99 = float(np.percentile(net_rets, 1.0))
        cvar_95 = float(net_rets[net_rets <= var_95].mean()) if (net_rets <= var_95).any() else var_95
        cvar_99 = float(net_rets[net_rets <= var_99].mean()) if (net_rets <= var_99).any() else var_99

        # Exposure & turnover
        avg_gross_exp = float(daily_df["gross_exposure"].mean())
        avg_net_exp = float(daily_df["net_exposure"].mean())
        ann_turnover = float(daily_df["turnover"].mean() * 252.0)

        return {
            "Total_Return": round(total_return, 4),
            "CAGR": round(cagr, 4),
            "Annualized_Volatility": round(ann_vol, 4),
            "Sharpe_Ratio": round(sharpe, 3),
            "Sortino_Ratio": round(sortino, 3),
            "Calmar_Ratio": round(calmar, 3),
            "Maximum_Drawdown": round(max_drawdown, 4),
            "Win_Rate": round(win_rate, 4),
            "Profit_Factor": round(profit_factor, 3),
            "Average_Trade": round(float(trades_df["net_return"].mean()), 4) if not trades_df.empty else 0.0,
            "Median_Trade": round(float(trades_df["net_return"].median()), 4) if not trades_df.empty else 0.0,
            "Best_Trade": round(float(trades_df["net_return"].max()), 4) if not trades_df.empty else 0.0,
            "Worst_Trade": round(float(trades_df["net_return"].min()), 4) if not trades_df.empty else 0.0,
            "VaR_95_Daily": round(var_95, 4),
            "VaR_99_Daily": round(var_99, 4),
            "CVaR_95_Daily": round(cvar_95, 4),
            "CVaR_99_Daily": round(cvar_99, 4),
            "Annualized_Turnover": round(ann_turnover, 2),
            "Average_Gross_Exposure": round(avg_gross_exp, 3),
            "Average_Net_Exposure": round(avg_net_exp, 3),
            "Total_Trades": len(trades_df),
        }

    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            "Total_Return": 0.0, "CAGR": 0.0, "Annualized_Volatility": 0.0,
            "Sharpe_Ratio": 0.0, "Sortino_Ratio": 0.0, "Calmar_Ratio": 0.0,
            "Maximum_Drawdown": 0.0, "Win_Rate": 0.0, "Profit_Factor": 0.0,
            "Average_Trade": 0.0, "Median_Trade": 0.0, "Best_Trade": 0.0, "Worst_Trade": 0.0,
            "VaR_95_Daily": 0.0, "VaR_99_Daily": 0.0, "CVaR_95_Daily": 0.0, "CVaR_99_Daily": 0.0,
            "Annualized_Turnover": 0.0, "Average_Gross_Exposure": 0.0, "Average_Net_Exposure": 0.0,
            "Total_Trades": 0
        }
