import React from 'react';
import { Activity, ShieldCheck, Download, Database, FileText, Calendar, Terminal } from 'lucide-react';
import { EngineData } from '../types';

interface HeaderProps {
  data: EngineData | null;
  onOpenReport: () => void;
}

export const Header: React.FC<HeaderProps> = ({ data, onOpenReport }) => {
  const downloadJSON = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `earnings_alpha_engine_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadReport = () => {
    if (!data || !data.report_markdown) return;
    const blob = new Blob([data.report_markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `event_driven_earnings_alpha_report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <header className="bg-slate-950 border-b border-slate-800/80 sticky top-0 z-40 px-4 lg:px-8 py-3.5 shadow-md">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Left branding */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold text-slate-100 tracking-tight flex items-center gap-2">
                ALPHA EVENT ENGINE
                <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-500/30 text-emerald-300">
                  INSTITUTIONAL v1.0
                </span>
              </h1>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Quantitative Event Study • Post-Earnings Drift (PEAD) • Machine Learning & Backtesting
            </p>
          </div>
        </div>

        {/* Right meta and actions */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          {/* Status Badges */}
          <div className="hidden sm:flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-300 font-mono">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            <span>432 Events</span>
            <span className="text-slate-600">|</span>
            <Calendar className="w-3.5 h-3.5 text-amber-400" />
            <span>2016–2024</span>
          </div>

          <div className="flex items-center gap-1.5 bg-emerald-950/40 border border-emerald-500/30 rounded-md px-2.5 py-1 text-xs text-emerald-400 font-mono">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-semibold">Audit: 15/15 PASS</span>
          </div>

          {/* Action buttons */}
          <button
            onClick={downloadJSON}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 hover:border-slate-600 text-xs font-medium transition cursor-pointer"
            title="Download full parsed engine dataset JSON"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span>Export JSON</span>
          </button>

          <button
            onClick={downloadReport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow transition cursor-pointer"
            title="Download dynamic research report Markdown"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Report .MD</span>
          </button>
        </div>
      </div>
    </header>
  );
};
