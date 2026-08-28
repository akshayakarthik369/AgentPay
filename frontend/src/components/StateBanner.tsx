import React from 'react';
import { ArrowRight, CheckCircle2, Sparkles } from 'lucide-react';

interface StateBannerProps {
  currentPhase: string;
  nextAction: string;
  description?: string;
  nextButtonText?: string;
  onNextClick?: () => void;
  className?: string;
}

export const StateBanner: React.FC<StateBannerProps> = ({
  currentPhase,
  nextAction,
  description,
  nextButtonText,
  onNextClick,
  className = '',
}) => {
  return (
    <div className={`glass-panel p-4 sm:p-5 rounded-2xl border border-blue-200 bg-gradient-to-r from-blue-50/80 via-indigo-50/50 to-purple-50/80 shadow-sm ${className}`}>
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        
        {/* Left: Phase Indicators */}
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-300">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              <span>Current: {currentPhase}</span>
            </span>

            <span className="text-slate-400 font-bold">→</span>

            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-100 text-[#172554] font-bold border border-blue-300">
              <Sparkles className="w-3 h-3 text-[#3155D9]" />
              <span>Next: {nextAction}</span>
            </span>
          </div>

          {description && (
            <p className="text-xs text-[#596273] font-sans pt-0.5">{description}</p>
          )}
        </div>

        {/* Right: Optional CTA to proceed */}
        {onNextClick && nextButtonText && (
          <button
            onClick={onNextClick}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-[#172554] via-[#1E3A8A] to-[#3155D9] hover:brightness-110 text-white font-semibold text-xs shadow-sm transition-all shrink-0 cursor-pointer"
          >
            <span>{nextButtonText}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
