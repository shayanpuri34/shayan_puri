import React from 'react';
import { X, Download, ZoomIn, ExternalLink } from 'lucide-react';
import { FigureItem } from '../types';

interface FigureModalProps {
  figure: FigureItem | null;
  onClose: () => void;
}

export const FigureModal: React.FC<FigureModalProps> = ({ figure, onClose }) => {
  if (!figure) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-5xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center gap-2.5">
            <span className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 text-xs font-mono font-bold">
              FIG {figure.id}
            </span>
            <h3 className="text-sm sm:text-base font-semibold text-slate-100 font-mono">
              {figure.title}
            </h3>
            <span className="hidden sm:inline-block text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
              {figure.category}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={figure.url}
              download={figure.filename}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
              title="Download High-Res PNG"
            >
              <Download className="w-4 h-4" />
            </a>
            <a
              href={figure.url}
              target="_blank"
              rel="noreferrer"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
              title="Open full image in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950 hover:text-rose-300 text-slate-400 transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Image Area */}
        <div className="p-4 sm:p-6 overflow-auto flex-1 flex items-center justify-center bg-slate-950/60">
          <img
            src={figure.url}
            alt={figure.title}
            className="max-w-full max-h-[70vh] object-contain rounded border border-slate-800 shadow-lg"
          />
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-950 text-xs font-mono text-slate-400 flex items-center justify-between">
          <span>Source: {figure.filename}</span>
          <span>DPI: 300 Institutional Publication Grade</span>
        </div>
      </div>
    </div>
  );
};
