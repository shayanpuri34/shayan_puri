import React, { useState, useEffect } from 'react';
import { EngineData, TabKey } from './types';
import { Header } from './components/Header';
import { NavigationTabs } from './components/NavigationTabs';
import { MetricCards } from './components/MetricCards';
import { PerformanceTab } from './components/PerformanceTab';
import { EventStudyTab } from './components/EventStudyTab';
import { PEADTab } from './components/PEADTab';
import { MLModelsTab } from './components/MLModelsTab';
import { RobustnessTab } from './components/RobustnessTab';
import { RegimeSectorTab } from './components/RegimeSectorTab';
import { LeakageAuditTab } from './components/LeakageAuditTab';
import { TradeLogTab } from './components/TradeLogTab';
import { FiguresGalleryTab } from './components/FiguresGalleryTab';
import { ResearchReportTab } from './components/ResearchReportTab';
import { Loader2, AlertCircle, RefreshCw, Terminal, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [data, setData] = useState<EngineData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>('performance');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/data/engine_data.json');
      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}: Failed to load engine dataset`);
      }
      const json: EngineData = await response.json();
      setData(json);
    } catch (err: any) {
      console.error('Failed to load engine data:', err);
      setError(err?.message || 'Failed to initialize engine telemetry');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-emerald-500/30 selection:text-emerald-200">
      {/* Top Institutional Header */}
      <Header data={data} onOpenReport={() => setActiveTab('report')} />

      {/* Main Tab Navigation */}
      <NavigationTabs
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        tradeCount={data?.trades?.length || 176}
        figureCount={data?.figures?.length || 29}
      />

      {/* Main Dashboard Canvas */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6">
        {loading ? (
          <div className="h-96 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
            <div className="text-sm font-mono tracking-wide">
              Ingesting Institutional Earnings Telemetry...
            </div>
          </div>
        ) : error ? (
          <div className="bg-rose-950/40 border border-rose-800 rounded-lg p-6 max-w-xl mx-auto my-12 text-center">
            <AlertCircle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-rose-200 mb-1">
              Data Ingestion Error
            </h3>
            <p className="text-xs text-rose-300/80 font-mono mb-4">{error}</p>
            <button
              onClick={loadData}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-rose-600 hover:bg-rose-500 text-white text-xs font-mono font-medium transition cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry Ingestion
            </button>
          </div>
        ) : data ? (
          <div className="space-y-6">
            {/* Bento KPI Summary Cards */}
            <MetricCards metrics={data.metrics} />

            {/* Active Tab Content */}
            <div className="transition-all duration-150">
              {activeTab === 'performance' && (
                <PerformanceTab equityCurve={data.equity_curve} metrics={data.metrics} />
              )}
              {activeTab === 'event_study' && (
                <EventStudyTab eventStudy={data.event_study} />
              )}
              {activeTab === 'pead' && <PEADTab />}
              {activeTab === 'ml_models' && (
                <MLModelsTab models={data.model_comparison} />
              )}
              {activeTab === 'robustness' && (
                <RobustnessTab robustness={data.robustness} />
              )}
              {activeTab === 'regime_sector' && (
                <RegimeSectorTab
                  sectors={data.sector_results}
                  regimes={data.regime_results}
                />
              )}
              {activeTab === 'leakage_audit' && (
                <LeakageAuditTab auditChecks={data.audit_report} />
              )}
              {activeTab === 'trades' && <TradeLogTab trades={data.trades} />}
              {activeTab === 'figures' && (
                <FiguresGalleryTab figures={data.figures} />
              )}
              {activeTab === 'report' && (
                <ResearchReportTab markdownContent={data.report_markdown} />
              )}
            </div>
          </div>
        ) : null}
      </main>

      {/* Institutional Status Footer */}
      <footer className="bg-slate-950 border-t border-slate-800/80 px-4 lg:px-8 py-4 text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Engine Online
            </span>
            <span className="text-slate-700">|</span>
            <span>Sample: 2016–2024 (432 Announcements)</span>
            <span className="text-slate-700">|</span>
            <span>Timing: AMC (T+1) • BMO (T0)</span>
          </div>

          <div className="flex items-center gap-3">
            <span>Frictions: 10 bps (2 commission + 5 slippage + 3 spread)</span>
            <span className="text-slate-700">|</span>
            <span className="text-slate-400">Apache 2.0 License</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
