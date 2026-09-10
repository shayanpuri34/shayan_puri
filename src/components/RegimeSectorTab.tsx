import React from 'react';
import { SectorResult, RegimeResult } from '../types';
import { Compass, PieChart, Activity, CheckCircle, BarChart } from 'lucide-react';

interface RegimeSectorTabProps {
  sectors: SectorResult[];
  regimes: RegimeResult[];
}

export const RegimeSectorTab: React.FC<RegimeSectorTabProps> = ({ sectors, regimes }) => {
  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <Compass className="w-4 h-4 text-cyan-400" />
          Sector & Macro Regime Attribution
        </h2>
        <p className="text-xs text-slate-400 font-mono mt-1 leading-relaxed">
          Decomposing event alpha across macroeconomic market states (trend and volatility regimes) and S&P GICS sectors.
          The strategy demonstrates asymmetric alpha generation during <span className="text-emerald-400 font-semibold">High Volatility regimes (Sharpe 0.776)</span> and <span className="text-cyan-400 font-semibold">Information Technology / Consumer Discretionary sectors</span>.
        </p>
      </div>

      {/* Macro Regime Breakdown */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-sm">
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            Macro Market Regime Breakdown (Bull/Bear & Volatility Tiers)
          </h3>
          <span className="text-xs font-mono text-slate-400">Total Trading Days: 2,263</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Regime Type</th>
                <th className="py-3 px-4">Regime State</th>
                <th className="py-3 px-4 text-right">Trading Days</th>
                <th className="py-3 px-4 text-right">Annualized Return</th>
                <th className="py-3 px-4 text-right">Ann. Volatility</th>
                <th className="py-3 px-4 text-right">Sharpe Ratio</th>
                <th className="py-3 px-4 text-right">Daily Win Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {regimes.map((r, idx) => {
                const isHigh = r.Sharpe_Ratio > 0.5;
                const isPos = r.Sharpe_Ratio >= 0;
                return (
                  <tr
                    key={idx}
                    className={`transition hover:bg-slate-800/40 ${
                      isHigh ? 'bg-emerald-950/20' : ''
                    }`}
                  >
                    <td className="py-3 px-4 font-semibold text-slate-300">{r.Regime_Type}</td>
                    <td className="py-3 px-4 font-semibold text-slate-100 flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          r.Regime === 'High_Vol' || r.Regime === 'Bull'
                            ? 'bg-emerald-400'
                            : r.Regime === 'Bear'
                            ? 'bg-rose-400'
                            : 'bg-cyan-400'
                        }`}
                      ></span>
                      {r.Regime.replace('_', ' ')}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">{r.Days}</td>
                    <td
                      className={`py-3 px-4 text-right font-medium ${
                        r.Ann_Return >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {(r.Ann_Return * 100).toFixed(2)}%
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">
                      {(r.Ann_Volatility * 100).toFixed(2)}%
                    </td>
                    <td
                      className={`py-3 px-4 text-right font-bold ${
                        isPos ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {r.Sharpe_Ratio.toFixed(3)}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-200">
                      {(r.Daily_Win_Rate * 100).toFixed(2)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Sector Performance Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-sm">
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <PieChart className="w-4 h-4 text-cyan-400" />
            GICS Sector Event Study & Strategy PnL
          </h3>
          <span className="text-xs font-mono text-slate-400">Large-Cap Core Universe</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">GICS Sector</th>
                <th className="py-3 px-4 text-right">Total Events</th>
                <th className="py-3 px-4 text-right">Avg Surprise %</th>
                <th className="py-3 px-4 text-right">Avg CAR[0,+1]</th>
                <th className="py-3 px-4 text-right">PEAD (+1 to +5D)</th>
                <th className="py-3 px-4 text-right">Strategy Trades</th>
                <th className="py-3 px-4 text-right">Avg Trade Return</th>
                <th className="py-3 px-4 text-right">Win Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {sectors.map((s, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-semibold text-slate-200">{s.Sector}</td>
                  <td className="py-3 px-4 text-right text-slate-400">{s.Total_Events}</td>
                  <td className="py-3 px-4 text-right text-emerald-400 font-medium">
                    +{(s.Avg_Surprise_Pct * 100).toFixed(1)}%
                  </td>
                  <td
                    className={`py-3 px-4 text-right font-medium ${
                      s['Avg_CAR[0,+1]'] >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {(s['Avg_CAR[0,+1]'] * 100).toFixed(2)}%
                  </td>
                  <td
                    className={`py-3 px-4 text-right font-medium ${
                      s['Avg_PEAD_CAR[+1,+5]'] >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {(s['Avg_PEAD_CAR[+1,+5]'] * 100).toFixed(2)}%
                  </td>
                  <td className="py-3 px-4 text-right text-slate-300">{s.Strategy_Trades}</td>
                  <td
                    className={`py-3 px-4 text-right font-semibold ${
                      s.Avg_Trade_Return >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {(s.Avg_Trade_Return * 100).toFixed(2)}%
                  </td>
                  <td className="py-3 px-4 text-right text-emerald-400 font-semibold">
                    {(s.Trade_Win_Rate * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
