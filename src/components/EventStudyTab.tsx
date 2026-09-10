import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, ReferenceLine } from 'recharts';
import { EventStudyWindow } from '../types';
import { Calculator, CheckCircle, HelpCircle } from 'lucide-react';

interface EventStudyTabProps {
  eventStudy: EventStudyWindow[];
}

export const EventStudyTab: React.FC<EventStudyTabProps> = ({ eventStudy }) => {
  const chartData = eventStudy.map(w => ({
    window: w.Window,
    mean_car: (w.Mean_CAR * 100),
    median_car: (w.Median_CAR * 100),
    t_stat: w.t_statistic,
    p_val: w.p_value,
    significant: w.Significant_5pct
  }));

  return (
    <div className="space-y-6">
      {/* Overview & Methodology Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Calculator className="w-4 h-4 text-cyan-400" />
              Market Model Event Study & Abnormal Return Dynamics
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-1 leading-relaxed">
              abnormal return specification: <span className="text-slate-200">AR_i,t = R_i,t - (α_i + β_i · R_m,t)</span>.
              Parameters are estimated strictly over the pre-event window <span className="text-slate-200">T ∈ [-252, -30]</span> trading days against SPY benchmark, with zero post-announcement data contamination.
            </p>
          </div>
          <div className="hidden sm:block text-right">
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-cyan-300">
              Benchmark: SPY
            </span>
          </div>
        </div>
      </div>

      {/* Bar Chart: Mean vs Median CAR across Windows */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Cumulative Abnormal Returns Across Pre- & Post-Event Windows
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Mean abnormal return (bps) across 421 clean corporate announcements
            </p>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 15, right: 10, left: -10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
              <XAxis
                dataKey="window"
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                angle={-20}
                textAnchor="end"
              />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                unit="%"
                domain={['auto', 'auto']}
              />
              <ReferenceLine y={0} stroke="#475569" strokeWidth={1} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#090d16',
                  borderColor: '#1e293b',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontFamily: 'monospace'
                }}
                formatter={(val: any, name: string) => [
                  `${Number(val).toFixed(3)}%`,
                  name === 'mean_car' ? 'Mean CAR' : 'Median CAR'
                ]}
              />
              <Bar dataKey="mean_car" name="Mean CAR (%)" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.mean_car >= 0 ? '#10b981' : '#f43f5e'}
                    fillOpacity={0.85}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Econometrics Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-sm">
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">
            Statistical Significance & Two-Tailed t-Tests
          </h3>
          <span className="text-xs font-mono text-slate-400">
            Degrees of freedom: N - 1 | α = 0.05
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Event Window</th>
                <th className="py-3 px-4 text-right">Sample (N)</th>
                <th className="py-3 px-4 text-right">Mean CAR</th>
                <th className="py-3 px-4 text-right">Median CAR</th>
                <th className="py-3 px-4 text-right">Std Dev</th>
                <th className="py-3 px-4 text-right">t-Stat</th>
                <th className="py-3 px-4 text-right">p-Value</th>
                <th className="py-3 px-4 text-right">95% Conf. Interval</th>
                <th className="py-3 px-4 text-center">Sig. (5%)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {eventStudy.map((row, idx) => {
                const isSig = row.Significant_5pct;
                const isPos = row.Mean_CAR >= 0;
                return (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-4 font-semibold text-slate-200">{row.Window}</td>
                    <td className="py-2.5 px-4 text-right text-slate-400">{row.N}</td>
                    <td
                      className={`py-2.5 px-4 text-right font-medium ${
                        isPos ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {(row.Mean_CAR * 100).toFixed(2)}%
                    </td>
                    <td className="py-2.5 px-4 text-right text-slate-300">
                      {(row.Median_CAR * 100).toFixed(2)}%
                    </td>
                    <td className="py-2.5 px-4 text-right text-slate-400">
                      {(row.Std_Dev * 100).toFixed(2)}%
                    </td>
                    <td className="py-2.5 px-4 text-right text-slate-300">{row.t_statistic.toFixed(3)}</td>
                    <td className="py-2.5 px-4 text-right text-slate-400">{row.p_value.toFixed(4)}</td>
                    <td className="py-2.5 px-4 text-right text-slate-400">
                      [{(row.CI_95_Lower * 100).toFixed(2)}%, {(row.CI_95_Upper * 100).toFixed(2)}%]
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      {isSig ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 text-[11px] font-semibold">
                          <CheckCircle className="w-3 h-3" /> Significant
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[11px]">
                          p &gt; 0.05
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
