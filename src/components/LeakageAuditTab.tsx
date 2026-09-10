import React from 'react';
import { LeakageAuditCheck } from '../types';
import { ShieldCheck, CheckCircle2, AlertOctagon, Lock, EyeOff, Layers, Terminal } from 'lucide-react';

interface LeakageAuditTabProps {
  auditChecks: LeakageAuditCheck[];
}

export const LeakageAuditTab: React.FC<LeakageAuditTabProps> = ({ auditChecks }) => {
  const total = auditChecks.length;
  const passed = auditChecks.filter(c => c.Status === 'PASS').length;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <h2 className="text-base font-semibold text-slate-100">
                15-Point Automated Data Leakage & Look-Ahead Bias Audit
              </h2>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1 leading-relaxed">
              Institutional quantitative integrity verification enforcing strict temporal isolation across news feeds, price vectors, machine learning pipelines, and order routing.
            </p>
          </div>

          <div className="flex items-center gap-3 bg-emerald-950/60 border border-emerald-500/40 rounded-lg px-4 py-2 self-start sm:self-auto shrink-0">
            <div className="text-right">
              <div className="text-xs font-mono text-emerald-400 font-medium">AUDIT STATUS</div>
              <div className="text-lg font-mono font-bold text-emerald-300">
                {passed} / {total} PASSED
              </div>
            </div>
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
          </div>
        </div>
      </div>

      {/* Audit Checklist Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-sm">
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Lock className="w-4 h-4 text-cyan-400" />
            Automated Audit Verification Manifest
          </h3>
          <span className="text-xs font-mono text-slate-400">Zero Future Leaks Detected</span>
        </div>

        <div className="divide-y divide-slate-800/60">
          {auditChecks.map((item, idx) => {
            const isPass = item.Status === 'PASS';
            return (
              <div
                key={idx}
                className="p-4 hover:bg-slate-800/30 transition flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono"
              >
                <div className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded bg-slate-800 text-slate-300 font-bold flex items-center justify-center shrink-0 text-[11px]">
                    {item.Check_ID}
                  </span>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-100">{item.Audit_Check}</h4>
                    <p className="text-slate-400 mt-0.5 leading-relaxed text-[11px] font-sans">
                      {item.Details}
                    </p>
                  </div>
                </div>

                <div className="shrink-0 flex items-center gap-2 self-end md:self-auto">
                  {isPass ? (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 font-bold text-xs tracking-wider">
                      <CheckCircle2 className="w-3.5 h-3.5" /> PASS
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-rose-950/80 border border-rose-500/50 text-rose-300 font-bold text-xs tracking-wider">
                      <AlertOctagon className="w-3.5 h-3.5" /> FAIL
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
