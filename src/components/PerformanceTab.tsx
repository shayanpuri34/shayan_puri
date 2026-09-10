import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  AreaChart,
  Area
} from 'recharts';
import { EquityCurvePoint, PerformanceMetrics } from '../types';
import { TrendingUp, ShieldCheck, DollarSign, Activity } from 'lucide-react';

interface PerformanceTabProps {
  equityCurve: EquityCurvePoint[];
  metrics: PerformanceMetrics;
}

export const PerformanceTab: React.FC<PerformanceTabProps> = ({ equityCurve, metrics }) => {
  const [chartView, setChartView] = useState<'cumulative' | 'drawdown' | 'exposure'>('cumulative');

  // Compute drawdown series from cumulative net returns
  let peak = -Infinity;
  const drawdownData = equityCurve.map(pt => {
    const val = 1 + pt.cumulative_net;
    if (val > peak) peak = val;
    const dd = (val - peak) / peak;
    return {
      date: pt.date ? pt.date.slice(0, 10) : '',
      drawdown: dd * 100,
      net_return: pt.cumulative_net * 100
    };
  });

  const formattedEquityData = equityCurve.map(pt => ({
    date: pt.date ? pt.date.slice(0, 10) : '',
    strategy_net: (pt.cumulative_net * 100),
    strategy_gross: (pt.cumulative_gross * 100),
    benchmark: (pt.cumulative_benchmark * 100),
    long_exposure: (pt.long_exposure * 100),
    short_exposure: (pt.short_exposure * 100),
    net_exposure: (pt.net_exposure * 100),
  }));

  return (
    <div className="space-y-6">
      {/* Chart Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 sm:p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              Systematic Equity Curve & Portfolio Trajectory
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Dollar-neutral long/short earnings event factor across 2016–2024
            </p>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-md border border-slate-800 self-start sm:self-auto">
            <button
              onClick={() => setChartView('cumulative')}
              className={`px-3 py-1 text-xs font-mono rounded transition cursor-pointer ${
                chartView === 'cumulative'
                  ? 'bg-slate-800 text-emerald-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Cumulative (%)
            </button>
            <button
              onClick={() => setChartView('drawdown')}
              className={`px-3 py-1 text-xs font-mono rounded transition cursor-pointer ${
                chartView === 'drawdown'
                  ? 'bg-slate-800 text-rose-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Underwater DD (%)
            </button>
            <button
              onClick={() => setChartView('exposure')}
              className={`px-3 py-1 text-xs font-mono rounded transition cursor-pointer ${
                chartView === 'exposure'
                  ? 'bg-slate-800 text-cyan-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Exposure Mix (%)
            </button>
          </div>
        </div>

        {/* Chart Canvas */}
        <div className="h-80 w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            {chartView === 'cumulative' ? (
              <LineChart data={formattedEquityData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={d => (d ? d.slice(0, 7) : '')}
                  minTickGap={45}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  unit="%"
                  domain={['auto', 'auto']}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#090d16',
                    borderColor: '#1e293b',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontFamily: 'monospace'
                  }}
                  formatter={(val: any) => [`${Number(val).toFixed(2)}%`]}
                />
                <Legend
                  wrapperStyle={{ fontSize: '12px', paddingTop: '8px', fontFamily: 'monospace' }}
                />
                <Line
                  type="monotone"
                  dataKey="strategy_net"
                  name="Strategy Net (10 bps)"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="strategy_gross"
                  name="Strategy Gross (0 bps)"
                  stroke="#38bdf8"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="benchmark"
                  name="SPY Benchmark (SPX)"
                  stroke="#f59e0b"
                  strokeWidth={1}
                  dot={false}
                  opacity={0.4}
                />
              </LineChart>
            ) : chartView === 'drawdown' ? (
              <AreaChart data={drawdownData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  minTickGap={45}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  unit="%"
                  domain={[-3, 0.5]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#090d16',
                    borderColor: '#1e293b',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontFamily: 'monospace'
                  }}
                  formatter={(val: any) => [`${Number(val).toFixed(2)}%`, 'Drawdown']}
                />
                <Area
                  type="monotone"
                  dataKey="drawdown"
                  name="Portfolio Drawdown"
                  stroke="#f43f5e"
                  fill="#f43f5e"
                  fillOpacity={0.2}
                  strokeWidth={1.5}
                />
              </AreaChart>
            ) : (
              <LineChart data={formattedEquityData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  minTickGap={45}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  unit="%"
                  domain={[-5, 5]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#090d16',
                    borderColor: '#1e293b',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontFamily: 'monospace'
                  }}
                  formatter={(val: any) => [`${Number(val).toFixed(2)}%`]}
                />
                <Legend
                  wrapperStyle={{ fontSize: '12px', paddingTop: '8px', fontFamily: 'monospace' }}
                />
                <Line
                  type="monotone"
                  dataKey="long_exposure"
                  name="Long Exposure"
                  stroke="#10b981"
                  strokeWidth={1.5}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="short_exposure"
                  name="Short Exposure"
                  stroke="#f43f5e"
                  strokeWidth={1.5}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="net_exposure"
                  name="Net Market Exposure"
                  stroke="#a855f7"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* Metrics Breakdown Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk-Adjusted Ratios */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            Performance & Risk-Adjusted Profile
          </h3>
          <div className="divide-y divide-slate-800/80 text-xs font-mono">
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Total Cumulative Return</span>
              <span className="font-semibold text-emerald-400">
                +{(metrics.Total_Return * 100).toFixed(2)}%
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Compound Annual Growth (CAGR)</span>
              <span className="font-semibold text-emerald-400">
                +{(metrics.CAGR * 100).toFixed(2)}%
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Annualized Volatility</span>
              <span className="font-semibold text-slate-200">
                {(metrics.Annualized_Volatility * 100).toFixed(2)}%
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Annualized Sharpe Ratio (Rf=0)</span>
              <span className="font-semibold text-rose-400">
                {metrics.Sharpe_Ratio.toFixed(3)}
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Sortino Ratio (Downside Deviation)</span>
              <span className="font-semibold text-rose-400">
                {metrics.Sortino_Ratio.toFixed(3)}
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Calmar Ratio (CAGR / Max DD)</span>
              <span className="font-semibold text-slate-200">
                {metrics.Calmar_Ratio.toFixed(3)}
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Maximum Drawdown</span>
              <span className="font-semibold text-rose-400">
                {(metrics.Maximum_Drawdown * 100).toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        {/* Trade Execution & Tail Risk */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-cyan-400" />
            Trade Distribution & Extreme Tail Risk
          </h3>
          <div className="divide-y divide-slate-800/80 text-xs font-mono">
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Win Rate (% Positive PnL)</span>
              <span className="font-semibold text-emerald-400">
                {(metrics.Win_Rate * 100).toFixed(2)}%
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Profit Factor (Gross Wins / Losses)</span>
              <span className="font-semibold text-emerald-400">
                {metrics.Profit_Factor.toFixed(3)}x
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Average Trade Return</span>
              <span className="font-semibold text-emerald-400">
                +{(metrics.Average_Trade * 100).toFixed(2)}%
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Best / Worst Single Trade</span>
              <span className="font-semibold text-slate-200">
                +{(metrics.Best_Trade * 100).toFixed(1)}% / {(metrics.Worst_Trade * 100).toFixed(1)}%
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Daily Parametric VaR (95% / 99%)</span>
              <span className="font-semibold text-slate-300">
                {(metrics.VaR_95_Daily * 100).toFixed(3)}% / {(metrics.VaR_99_Daily * 100).toFixed(3)}%
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Daily Expected Shortfall (CVaR 95%)</span>
              <span className="font-semibold text-rose-400">
                {(metrics.CVaR_95_Daily * 100).toFixed(3)}%
              </span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-slate-400">Annualized Portfolio Turnover</span>
              <span className="font-semibold text-cyan-400">
                {(metrics.Annualized_Turnover * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
