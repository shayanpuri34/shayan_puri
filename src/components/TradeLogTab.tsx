import React, { useState, useMemo } from 'react';
import { TradeRecord } from '../types';
import { Search, Filter, ArrowUpRight, ArrowDownRight, Clock, Download } from 'lucide-react';

interface TradeLogTabProps {
  trades: TradeRecord[];
}

export const TradeLogTab: React.FC<TradeLogTabProps> = ({ trades }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [tickerFilter, setTickerFilter] = useState('ALL');
  const [directionFilter, setDirectionFilter] = useState('ALL');
  const [outcomeFilter, setOutcomeFilter] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const tickers = useMemo(() => {
    const set = new Set<string>();
    trades.forEach(t => set.add(t.ticker));
    return ['ALL', ...Array.from(set).sort()];
  }, [trades]);

  const filteredTrades = useMemo(() => {
    return trades.filter(t => {
      const matchSearch =
        searchTerm === '' ||
        t.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.announcement_date.includes(searchTerm) ||
        t.entry_date.includes(searchTerm);

      const matchTicker = tickerFilter === 'ALL' || t.ticker === tickerFilter;
      const matchDir =
        directionFilter === 'ALL' ||
        (directionFilter === 'LONG' && t.position_dir > 0) ||
        (directionFilter === 'SHORT' && t.position_dir < 0);

      const matchOutcome =
        outcomeFilter === 'ALL' ||
        (outcomeFilter === 'WIN' && t.net_return > 0) ||
        (outcomeFilter === 'LOSS' && t.net_return <= 0);

      return matchSearch && matchTicker && matchDir && matchOutcome;
    });
  }, [trades, searchTerm, tickerFilter, directionFilter, outcomeFilter]);

  const totalPages = Math.ceil(filteredTrades.length / pageSize) || 1;
  const paginatedTrades = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredTrades.slice(start, start + pageSize);
  }, [filteredTrades, currentPage]);

  const downloadTradesCSV = () => {
    const headers = [
      'Ticker',
      'Announcement_Date',
      'Timing_Class',
      'Entry_Date',
      'Exit_Date',
      'Direction',
      'Entry_Price',
      'Exit_Price',
      'Holding_Days',
      'Gross_Return_Pct',
      'Cost_bps',
      'Net_Return_Pct',
      'Market_Return_Pct',
      'Abnormal_Return_Pct'
    ];
    const rows = filteredTrades.map(t => [
      t.ticker,
      t.announcement_date,
      t.timing_class,
      t.entry_date,
      t.exit_date,
      t.position_dir > 0 ? 'LONG' : 'SHORT',
      t.entry_price,
      t.exit_price,
      t.holding_period_days,
      (t.gross_return * 100).toFixed(4),
      (t.transaction_cost * 10000).toFixed(0),
      (t.net_return * 100).toFixed(4),
      (t.market_return * 100).toFixed(4),
      (t.abnormal_return * 100).toFixed(4)
    ]);
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `earnings_event_trades_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-400" />
              Event Trade Execution Log ({trades.length} Executed Signals)
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Every position strictly obeys timing boundaries (AMC = T+1 entry, BMO = T0 entry). Net returns reflect two-way 10 bps friction costs.
            </p>
          </div>

          <button
            onClick={downloadTradesCSV}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-md text-xs font-mono transition cursor-pointer self-start sm:self-auto"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Filtered CSV ({filteredTrades.length})</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-wrap items-center gap-3 text-xs font-mono">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search by ticker or date..."
            value={searchTerm}
            onChange={e => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full bg-slate-950 border border-slate-800 rounded-md pl-9 pr-3 py-1.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-slate-700"
          />
        </div>

        {/* Ticker Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Ticker:</span>
          <select
            value={tickerFilter}
            onChange={e => {
              setTickerFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none"
          >
            {tickers.map(t => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        {/* Direction Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Direction:</span>
          <select
            value={directionFilter}
            onChange={e => {
              setDirectionFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none"
          >
            <option value="ALL">All Directions</option>
            <option value="LONG">Long (+1)</option>
            <option value="SHORT">Short (-1)</option>
          </select>
        </div>

        {/* Outcome Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Outcome:</span>
          <select
            value={outcomeFilter}
            onChange={e => {
              setOutcomeFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none"
          >
            <option value="ALL">All Outcomes</option>
            <option value="WIN">Winners (Net &gt; 0)</option>
            <option value="LOSS">Losses (Net ≤ 0)</option>
          </select>
        </div>
      </div>

      {/* Trades Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Ticker</th>
                <th className="py-3 px-4">Announce</th>
                <th className="py-3 px-4">Timing</th>
                <th className="py-3 px-4">Entry Date</th>
                <th className="py-3 px-4">Exit Date</th>
                <th className="py-3 px-4">Direction</th>
                <th className="py-3 px-4 text-right">Entry $</th>
                <th className="py-3 px-4 text-right">Exit $</th>
                <th className="py-3 px-4 text-right">Days</th>
                <th className="py-3 px-4 text-right">Gross %</th>
                <th className="py-3 px-4 text-right">Net %</th>
                <th className="py-3 px-4 text-right">Alpha (AR)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {paginatedTrades.map((t, idx) => {
                const isLong = t.position_dir > 0;
                const isWin = t.net_return > 0;
                return (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-4 font-bold text-slate-200">{t.ticker}</td>
                    <td className="py-2.5 px-4 text-slate-400">{t.announcement_date}</td>
                    <td className="py-2.5 px-4">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                        {t.timing_class}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-300">{t.entry_date}</td>
                    <td className="py-2.5 px-4 text-slate-300">{t.exit_date}</td>
                    <td className="py-2.5 px-4">
                      <span
                        className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded text-[10px] font-bold ${
                          isLong
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60'
                            : 'bg-rose-950 text-rose-400 border border-rose-800/60'
                        }`}
                      >
                        {isLong ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {isLong ? 'LONG' : 'SHORT'}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right text-slate-300">${t.entry_price.toFixed(2)}</td>
                    <td className="py-2.5 px-4 text-right text-slate-300">${t.exit_price.toFixed(2)}</td>
                    <td className="py-2.5 px-4 text-right text-slate-400">{t.holding_period_days}D</td>
                    <td
                      className={`py-2.5 px-4 text-right font-medium ${
                        t.gross_return >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {t.gross_return >= 0
                        ? `+${(t.gross_return * 100).toFixed(2)}%`
                        : `${(t.gross_return * 100).toFixed(2)}%`}
                    </td>
                    <td
                      className={`py-2.5 px-4 text-right font-bold ${
                        isWin ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {t.net_return >= 0
                        ? `+${(t.net_return * 100).toFixed(2)}%`
                        : `${(t.net_return * 100).toFixed(2)}%`}
                    </td>
                    <td
                      className={`py-2.5 px-4 text-right ${
                        t.abnormal_return >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {t.abnormal_return >= 0
                        ? `+${(t.abnormal_return * 100).toFixed(2)}%`
                        : `${(t.abnormal_return * 100).toFixed(2)}%`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination controls */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
          <div>
            Showing {(currentPage - 1) * pageSize + 1} to{' '}
            {Math.min(currentPage * pageSize, filteredTrades.length)} of {filteredTrades.length} trades
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 transition"
            >
              Previous
            </button>
            <span>
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 transition"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
