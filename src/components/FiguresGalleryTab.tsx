import React, { useState, useMemo } from 'react';
import { FigureItem } from '../types';
import { ImageIcon, ZoomIn, Download, Filter } from 'lucide-react';
import { FigureModal } from './FigureModal';

interface FiguresGalleryTabProps {
  figures: FigureItem[];
}

export const FiguresGalleryTab: React.FC<FiguresGalleryTabProps> = ({ figures }) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [activeModalFigure, setActiveModalFigure] = useState<FigureItem | null>(null);

  const categories = useMemo(() => {
    const set = new Set<string>();
    figures.forEach(f => set.add(f.category));
    return ['ALL', ...Array.from(set).sort()];
  }, [figures]);

  const filteredFigures = useMemo(() => {
    if (selectedCategory === 'ALL') return figures;
    return figures.filter(f => f.category === selectedCategory);
  }, [figures, selectedCategory]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <ImageIcon className="w-4 h-4 text-cyan-400" />
          Publication Graphics & Econometric Visualizations ({figures.length} Figures)
        </h2>
        <p className="text-xs text-slate-400 font-mono mt-1 leading-relaxed">
          High-resolution 300 DPI vector-rendered charts covering event study dynamics, earnings surprise distributions, PEAD drift curves, backtest profiles, machine learning ROC curves, and portfolio risk distributions.
        </p>
      </div>

      {/* Category Pills Filter */}
      <div className="flex flex-wrap items-center gap-2 pb-1">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1.5 text-xs font-mono rounded-md border transition cursor-pointer ${
              selectedCategory === cat
                ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300 font-semibold'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            {cat} {cat === 'ALL' ? `(${figures.length})` : ''}
          </button>
        ))}
      </div>

      {/* Figures Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredFigures.map(fig => (
          <div
            key={fig.id}
            className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg overflow-hidden shadow-sm flex flex-col group transition"
          >
            {/* Image Preview */}
            <div
              onClick={() => setActiveModalFigure(fig)}
              className="relative aspect-video bg-slate-950 cursor-pointer overflow-hidden border-b border-slate-800 flex items-center justify-center p-2"
            >
              <img
                src={fig.url}
                alt={fig.title}
                loading="lazy"
                className="max-h-full max-w-full object-contain transition duration-200 group-hover:scale-[1.02]"
              />
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2 text-white">
                <span className="px-2.5 py-1 rounded bg-black/75 border border-white/20 text-xs font-mono flex items-center gap-1.5">
                  <ZoomIn className="w-3.5 h-3.5" /> Enlarge View
                </span>
              </div>
            </div>

            {/* Card Content */}
            <div className="p-3.5 flex-1 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                    FIG {fig.id}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">{fig.category}</span>
                </div>
                <h4 className="text-xs font-semibold text-slate-200 line-clamp-1 group-hover:text-emerald-400 transition">
                  {fig.title}
                </h4>
              </div>

              <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono">
                <button
                  onClick={() => setActiveModalFigure(fig)}
                  className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
                >
                  <ZoomIn className="w-3 h-3" /> Preview
                </button>
                <a
                  href={fig.url}
                  download={fig.filename}
                  className="text-slate-400 hover:text-slate-200 flex items-center gap-1 transition"
                >
                  <Download className="w-3 h-3" /> Download
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Lightbox Modal */}
      <FigureModal
        figure={activeModalFigure}
        onClose={() => setActiveModalFigure(null)}
      />
    </div>
  );
};
