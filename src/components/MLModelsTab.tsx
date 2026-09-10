import React from 'react';
import { MLModelRow } from '../types';
import { Cpu, ShieldCheck, CheckCircle2, TrendingUp, AlertTriangle } from 'lucide-react';

interface MLModelsTabProps {
  models: MLModelRow[];
}

export const MLModelsTab: React.FC<MLModelsTabProps> = ({ models }) => {
  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          Walk-Forward Machine Learning Alpha Engine
        </h2>
        <p className="text-xs text-slate-400 font-mono mt-1 leading-relaxed">
          Evaluation methodology strictly enforces walk-forward <span className="text-slate-200">TimeSeriesSplit (5 folds)</span>. All missing-value imputers and standard scalers are fitted exclusively within each training split to prevent in-sample information leakage.
        </p>
      </div>

      {/* Model Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>BEST CLASSIFIER ACCURACY</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">51.14%</div>
          <div className="text-xs text-slate-400 font-mono mt-1">
            Random Forest & Gradient Boosting
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>BEST OUT-OF-SAMPLE AUC</span>
            <TrendingUp className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-400">0.5057</div>
          <div className="text-xs text-slate-400 font-mono mt-1">
            Random Forest Classifier (500 Trees)
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>REGRESSION MEAN ABS ERROR</span>
            <ShieldCheck className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-200">2.81%</div>
          <div className="text-xs text-slate-400 font-mono mt-1">
            Ridge Regressor (L2 Penalty α=1.0)
          </div>
        </div>
      </div>

      {/* Models Comparison Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-sm">
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">
            Out-of-Sample Performance Comparison Matrix
          </h3>
          <span className="text-xs font-mono text-slate-400">5-Fold Expanding Window</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Model Architecture</th>
                <th className="py-3 px-4">Task Type</th>
                <th className="py-3 px-4 text-right">Directional Acc.</th>
                <th className="py-3 px-4 text-right">ROC-AUC</th>
                <th className="py-3 px-4 text-right">Precision</th>
                <th className="py-3 px-4 text-right">Recall</th>
                <th className="py-3 px-4 text-right">F1 Score</th>
                <th className="py-3 px-4 text-right">MAE</th>
                <th className="py-3 px-4 text-right">RMSE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {models.map((m, idx) => {
                const isTop = m.Directional_Accuracy >= 0.51;
                return (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-semibold text-slate-200 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                      {m.Model.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] ${
                          m.Type === 'Classification'
                            ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/60'
                            : 'bg-purple-950 text-purple-300 border border-purple-800/60'
                        }`}
                      >
                        {m.Type}
                      </span>
                    </td>
                    <td
                      className={`py-3 px-4 text-right font-semibold ${
                        isTop ? 'text-emerald-400' : 'text-slate-300'
                      }`}
                    >
                      {(m.Directional_Accuracy * 100).toFixed(2)}%
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">
                      {m.AUC ? m.AUC.toFixed(4) : '—'}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">
                      {m.Precision ? (m.Precision * 100).toFixed(2) + '%' : '—'}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">
                      {m.Recall ? (m.Recall * 100).toFixed(2) + '%' : '—'}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">
                      {m.F1 ? m.F1.toFixed(4) : '—'}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">
                      {m.MAE ? (m.MAE * 100).toFixed(2) + '%' : '—'}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">
                      {m.RMSE ? (m.RMSE * 100).toFixed(2) + '%' : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Feature Engineering Architecture Notes */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-slate-200 mb-2 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Point-In-Time Feature Pipeline & Pre-Event Feature Vector
        </h3>
        <p className="text-xs text-slate-400 font-mono leading-relaxed">
          Features fed to estimators: SUE (Standardized Unexpected Earnings), EPS Dollar Surprise, Percentage Surprise, Consensus Dispersion, Pre-Event 20D Runup Return, Pre-Event 60D Beta, 20D Realized Volatility, 20D Average Daily Volume Ratio, and VIX Macro Level.
          Post-earnings reaction data ($R_0$ or post-announcement closes) is strictly banned from feature construction.
        </p>
      </div>
    </div>
  );
};
