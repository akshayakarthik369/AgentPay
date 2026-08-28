import React from 'react';
import { 
  Sparkles, 
  CheckCircle2, 
  XCircle, 
  ShieldCheck, 
  Star, 
  Award, 
  Activity, 
  X, 
  Zap 
} from 'lucide-react';
import { TaskMatchResult, SingleAgentTaskMatchResponse, AgentMatchResult } from '../services/api';

export const MATCH_LEVEL_STYLES: Record<string, { badge: string; text: string; bg: string }> = {
  excellent: {
    badge: 'bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold',
    text: 'text-emerald-700',
    bg: 'from-emerald-50 to-teal-50',
  },
  strong: {
    badge: 'bg-blue-50 text-blue-700 border-blue-200 font-semibold',
    text: 'text-[#3155D9]',
    bg: 'from-blue-50 to-indigo-50',
  },
  moderate: {
    badge: 'bg-amber-50 text-amber-700 border-amber-200 font-semibold',
    text: 'text-amber-700',
    bg: 'from-amber-50 to-orange-50',
  },
  weak: {
    badge: 'bg-orange-50 text-orange-700 border-orange-200 font-semibold',
    text: 'text-orange-700',
    bg: 'from-orange-50 to-rose-50',
  },
  poor: {
    badge: 'bg-rose-50 text-rose-700 border-rose-200 font-semibold',
    text: 'text-rose-700',
    bg: 'from-rose-50 to-red-50',
  },
};

interface MatchScoreCardProps {
  match: TaskMatchResult | SingleAgentTaskMatchResponse | AgentMatchResult;
  title?: string;
  subtitle?: string;
  onClose?: () => void;
  isModal?: boolean;
}

export const MatchScoreCard: React.FC<MatchScoreCardProps> = ({
  match,
  title,
  subtitle,
  onClose,
  isModal = false,
}) => {
  const levelStyle = MATCH_LEVEL_STYLES[match.match_level] || MATCH_LEVEL_STYLES.moderate;

  const factors = [
    {
      label: 'Capability Match',
      weight: '50%',
      score: match.capability_score,
      icon: <Zap className="w-3.5 h-3.5 text-[#3155D9]" />,
      color: 'bg-[#3155D9]',
    },
    {
      label: 'Reputation Fit',
      weight: '20%',
      score: match.reputation_score,
      icon: <Star className="w-3.5 h-3.5 text-amber-500" />,
      color: 'bg-amber-500',
    },
    {
      label: 'Historical Quality',
      weight: '15%',
      score: match.quality_score,
      icon: <Award className="w-3.5 h-3.5 text-[#6D5BD0]" />,
      color: 'bg-[#6D5BD0]',
    },
    {
      label: 'Success Rate',
      weight: '10%',
      score: match.success_score,
      icon: <Activity className="w-3.5 h-3.5 text-emerald-600" />,
      color: 'bg-[#15805F]',
    },
    {
      label: 'Availability',
      weight: '5%',
      score: match.availability_score,
      icon: <ShieldCheck className="w-3.5 h-3.5 text-[#172554]" />,
      color: 'bg-[#172554]',
    },
  ];

  const content = (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono uppercase tracking-wider border ${levelStyle.badge}`}>
              {match.match_level} Match
            </span>
            {match.eligible ? (
              <span className="flex items-center gap-1 text-[11px] font-mono font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Eligible
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[11px] font-mono font-medium text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                <XCircle className="w-3 h-3 text-rose-600" /> Ineligible
              </span>
            )}
          </div>
          {title && <h3 className="text-lg font-bold text-[#18202F] leading-snug">{title}</h3>}
          {subtitle && <p className="text-xs text-[#596273] font-mono mt-0.5">{subtitle}</p>}
        </div>

        {/* Score Radial / Badge */}
        <div className="flex flex-col items-center justify-center p-3 rounded-2xl bg-slate-50 border border-slate-200 shadow-sm shrink-0 min-w-[80px]">
          <div className={`text-2xl font-black font-mono ${levelStyle.text}`}>
            {match.overall_score.toFixed(1)}%
          </div>
          <span className="text-[10px] font-mono uppercase text-[#87909F] mt-0.5">Suitability</span>
        </div>
      </div>

      {/* Factor Breakdown */}
      <div>
        <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#596273] mb-3 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-[#3155D9]" />
          <span>Multi-Factor Breakdown (100% Weight)</span>
        </h4>
        <div className="space-y-3">
          {factors.map((f) => (
            <div key={f.label} className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2 text-[#18202F]">
                  {f.icon}
                  <span>{f.label}</span>
                  <span className="text-[#87909F] text-[10px]">({f.weight})</span>
                </div>
                <span className="font-bold text-[#18202F]">{f.score.toFixed(0)}/100</span>
              </div>
              <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                <div
                  className={`h-full rounded-full ${f.color} transition-all duration-500`}
                  style={{ width: `${Math.max(2, Math.min(100, f.score))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Explainability Reasons */}
      {match.reasons && match.reasons.length > 0 && (
        <div className="pt-4 border-t border-slate-200">
          <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#596273] mb-2">
            Why this matches:
          </h4>
          <ul className="space-y-1.5">
            {match.reasons.map((reason, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-[#596273]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#3155D9] mt-1.5 shrink-0" />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  if (isModal) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
        <div className="glass-panel w-full max-w-lg rounded-3xl border border-slate-200 p-6 sm:p-8 bg-white shadow-2xl relative">
          {onClose && (
            <button
              onClick={onClose}
              className="absolute top-5 right-5 p-2 rounded-xl bg-slate-100 border border-slate-200 text-[#596273] hover:text-[#18202F] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="glass-panel p-5 sm:p-6 rounded-2xl border border-slate-200">
      {content}
    </div>
  );
};
