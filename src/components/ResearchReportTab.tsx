import React, { useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FileText, Download, Copy, Check, Printer } from 'lucide-react';

interface ResearchReportTabProps {
  markdownContent: string;
}

export const ResearchReportTab: React.FC<ResearchReportTabProps> = ({ markdownContent }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(markdownContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([markdownContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `event_driven_earnings_alpha_report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-400" />
            Institutional Quantitative Research Report
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Auto-generated publication report summarizing hypotheses, market model statistics, and friction survival.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono transition cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy Text'}</span>
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span>Download .MD</span>
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-medium shadow transition cursor-pointer"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      {/* Markdown Document Reader */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 sm:p-10 shadow-sm">
        <div className="prose prose-invert max-w-none text-slate-200 text-sm leading-relaxed prose-headings:text-slate-100 prose-headings:font-mono prose-table:font-mono prose-table:text-xs prose-th:text-slate-300 prose-td:text-slate-300 prose-hr:border-slate-800 prose-code:text-emerald-300 prose-pre:bg-slate-950">
          <Markdown remarkPlugins={[remarkGfm]}>
            {markdownContent}
          </Markdown>
        </div>
      </div>
    </div>
  );
};
