import React from 'react';
import { TabKey } from '../types';
import {
  Activity,
  Calculator,
  Layers,
  Cpu,
  Sliders,
  Compass,
  ShieldCheck,
  Clock,
  ImageIcon,
  FileText
} from 'lucide-react';

interface NavigationTabsProps {
  activeTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  tradeCount: number;
  figureCount: number;
}

export const NavigationTabs: React.FC<NavigationTabsProps> = ({
  activeTab,
  onSelectTab,
  tradeCount,
  figureCount
}) => {
  const tabs = [
    { key: 'performance' as TabKey, label: 'Performance & Curve', icon: Activity },
    { key: 'event_study' as TabKey, label: 'Event Study (CAR)', icon: Calculator },
    { key: 'pead' as TabKey, label: 'Surprise & PEAD', icon: Layers },
    { key: 'ml_models' as TabKey, label: 'Machine Learning', icon: Cpu },
    { key: 'robustness' as TabKey, label: 'Robustness & Costs', icon: Sliders },
    { key: 'regime_sector' as TabKey, label: 'Regimes & Sectors', icon: Compass },
    { key: 'leakage_audit' as TabKey, label: 'Leakage Audit', icon: ShieldCheck, badge: 'PASS' },
    { key: 'trades' as TabKey, label: 'Trade Log', icon: Clock, badge: `${tradeCount}` },
    { key: 'figures' as TabKey, label: '29 Figures', icon: ImageIcon, badge: `${figureCount}` },
    { key: 'report' as TabKey, label: 'Research Report', icon: FileText },
  ];

  return (
    <div className="border-b border-slate-800/90 bg-slate-950/60 overflow-x-auto scrollbar-none">
      <div className="max-w-7xl mx-auto flex items-center gap-1 px-4 lg:px-8">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => onSelectTab(tab.key)}
              className={`flex items-center gap-2 py-3 px-3.5 text-xs font-mono whitespace-nowrap border-b-2 transition cursor-pointer ${
                isActive
                  ? 'border-emerald-400 text-emerald-400 font-semibold bg-slate-900/60'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                    tab.badge === 'PASS'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-600/40'
                      : 'bg-slate-800 text-slate-300'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
