import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  Legend
} from 'recharts';
import { TrendingUp, Layers, HelpCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export const PEADTab: React.FC = () => {
  const quintilesData = [
    {
      quintile: 'Q1 (Extreme Neg)',
      n: 97,
      surprise_pct: -16.93,
      avg_car: -1.99,
      median_car: -2.12,
      win_rate: 27.84,
      pead_5d: -0.22,
      pead_20d: -0.34
    },
    {
      quintile: 'Q2 (Low Neg/Flat)',
      n: 72,
      surprise_pct: 2.77,
      avg_car: 0.45,
      median_car: 1.54,
      win_rate: 59.72,
      pead_5d: 0.25,
      pead_20d: -0.55
    },
    {
      quintile: 'Q3 (Neutral)',
      n: 84,
      surprise_pct: 7.24,
      avg_car: 0.85,
      median_car: 0.13,
      win_rate: 51.19,
      pead_5d: -0.47,
      pead_20d: -0.95
    },
    {
      quintile: 'Q4 (Strong Pos)',
      n: 84,
      surprise_pct: 13.82,
      avg_car: 1.41,
      median_car: 1.14,
      win_rate: 63.10,
      pead_5d: -0.63,
      pead_20d: -1.27
    },
    {
      quintile: 'Q5 (Extreme Pos)',
      n: 84,
      surprise_pct: 111.25,
      avg_car: 1.53,
      median_car: 1.16,
      win_rate: 60.71,
      pead_5d: -0.67,
      pead_20d: -0.46
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          Earnings Surprise Quintiles & Post-Earnings Announcement Drift (PEAD)
        </h2>
        <p className="text-xs text-slate-400 font-mono mt-1 leading-relaxed">
          Events partitioned into 5 surprise quintiles using strictly point-in-time consensus surprises.
          The spread between Q5 (top beats) and Q1 (deep misses) achieves an immediate event day abnormal return spread of <span className="text-emerald-400 font-bold">+3.52%</span>.
        </p>
      </div>

      {/* Chart: Event Day CAR vs 5D Drift by Quintile */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-slate-200 mb-1">
          Event Reaction (CAR[-1,+1]) vs Drift (CAR[+1,+5]) by Surprise Quintile
        </h3>
        <p className="text-xs text-slate-400 font-mono mb-4">
          Comparing immediate market reaction to post-announcement drift
        </p>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={quintilesData} margin={{ top: 15, right: 10, left: -10, bottom: 15 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
              <XAxis dataKey="quintile" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} unit="%" domain={[-2.5, 2.5]} />
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
              <Legend wrapperStyle={{ fontSize: '12px', fontFamily: 'monospace' }} />
              <Bar dataKey="avg_car" name="Immediate CAR[-1,+1] (%)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="pead_5d" name="PEAD Drift CAR[+1,+5] (%)" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Quintiles Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-sm">
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">
            Empirical Quintile Breakdown & Win Rate Statistics
          </h3>
          <span className="text-xs font-mono text-slate-400">Total N = 421 clean observations</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Quintile Group</th>
                <th className="py-3 px-4 text-right">Events (N)</th>
                <th className="py-3 px-4 text-right">Avg Surprise %</th>
                <th className="py-3 px-4 text-right">Avg CAR[-1,+1]</th>
                <th className="py-3 px-4 text-right">Median CAR</th>
                <th className="py-3 px-4 text-right">Win Rate</th>
                <th className="py-3 px-4 text-right">PEAD (+1 to +5D)</th>
                <th className="py-3 px-4 text-right">PEAD (+1 to +20D)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {quintilesData.map((q, idx) => {
                const isQ1 = idx === 0;
                const isQ5 = idx === 4;
                return (
                  <tr
                    key={idx}
                    className={`transition hover:bg-slate-800/40 ${
                      isQ5 ? 'bg-emerald-950/20' : isQ1 ? 'bg-rose-950/20' : ''
                    }`}
                  >
                    <td className="py-3 px-4 font-semibold text-slate-200 flex items-center gap-1.5">
                      {isQ5 ? (
                        <ArrowUpRight className="w-4 h-4 text-emerald-400" />
                      ) : isQ1 ? (
                        <ArrowDownRight className="w-4 h-4 text-rose-400" />
                      ) : null}
                      {q.quintile}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">{q.n}</td>
                    <td
                      className={`py-3 px-4 text-right font-medium ${
                        q.surprise_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {q.surprise_pct >= 0 ? `+${q.surprise_pct.toFixed(1)}%` : `${q.surprise_pct.toFixed(1)}%`}
                    </td>
                    <td
                      className={`py-3 px-4 text-right font-semibold ${
                        q.avg_car >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {q.avg_car >= 0 ? `+${q.avg_car.toFixed(2)}%` : `${q.avg_car.toFixed(2)}%`}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">{q.median_car.toFixed(2)}%</td>
                    <td className="py-3 px-4 text-right text-slate-300 font-semibold">{q.win_rate.toFixed(1)}%</td>
                    <td
                      className={`py-3 px-4 text-right ${
                        q.pead_5d >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {q.pead_5d >= 0 ? `+${q.pead_5d.toFixed(2)}%` : `${q.pead_5d.toFixed(2)}%`}
                    </td>
                    <td
                      className={`py-3 px-4 text-right ${
                        q.pead_20d >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {q.pead_20d >= 0 ? `+${q.pead_20d.toFixed(2)}%` : `${q.pead_20d.toFixed(2)}%`}
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
