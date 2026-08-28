import React, { useState, useEffect, useCallback } from 'react';
import { NavTab } from '../components/Navbar';
import {
  Award, ShieldCheck, Bot, TrendingUp,
  CheckCircle2, Crown, Filter, RefreshCw,
  AlertCircle, Star, Zap, BarChart3, Users,
  ChevronRight, Sparkles, Activity
} from 'lucide-react';
import {
  fetchReputationLeaderboard,
  fetchReputationSummary,
  recalculateAllReputations,
  LeaderboardAgent,
  ReputationSummary,
} from '../services/api';

interface ReputationPageProps {
  onNavigate: (tab: NavTab) => void;
}

const LEVEL_STYLES: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  'Excellent':             { bg: 'bg-amber-50',    text: 'text-amber-700',    border: 'border-amber-200',    dot: 'bg-amber-400' },
  'Strong':                { bg: 'bg-emerald-50',  text: 'text-emerald-700',  border: 'border-emerald-200',  dot: 'bg-emerald-500' },
  'Good':                  { bg: 'bg-blue-50',     text: 'text-[#3155D9]',    border: 'border-blue-200',     dot: 'bg-blue-500' },
  'Moderate':              { bg: 'bg-orange-50',   text: 'text-orange-700',   border: 'border-orange-200',   dot: 'bg-orange-400' },
  'Weak':                  { bg: 'bg-rose-50',     text: 'text-rose-600',     border: 'border-rose-200',     dot: 'bg-rose-400' },
  'High Risk':             { bg: 'bg-rose-50',     text: 'text-rose-700',     border: 'border-rose-300',     dot: 'bg-rose-600' },
  'Excellent (Provisional)': { bg: 'bg-amber-50',  text: 'text-amber-600',    border: 'border-amber-200',    dot: 'bg-amber-300' },
  'Strong (Provisional)':  { bg: 'bg-emerald-50',  text: 'text-emerald-600',  border: 'border-emerald-200',  dot: 'bg-emerald-400' },
  'Good (Provisional)':    { bg: 'bg-blue-50',     text: 'text-blue-500',     border: 'border-blue-200',     dot: 'bg-blue-400' },
  'Provisional':           { bg: 'bg-slate-100',   text: 'text-[#596273]',    border: 'border-slate-200',    dot: 'bg-slate-400' },
};

function getLevelStyle(level: string) {
  return LEVEL_STYLES[level] || LEVEL_STYLES['Provisional'];
}

const TYPE_BADGE: Record<string, string> = {
  worker:       'bg-blue-50 text-[#3155D9] border-blue-200',
  verifier:     'bg-purple-50 text-[#6D5BD0] border-purple-200',
  orchestrator: 'bg-slate-100 text-[#1E3A8A] border-slate-200',
};

const RANK_ICON = (rank: number) => {
  if (rank === 1) return <Crown className="w-4 h-4 text-amber-400" />;
  if (rank === 2) return <Crown className="w-4 h-4 text-slate-400" />;
  if (rank === 3) return <Crown className="w-4 h-4 text-orange-600" />;
  return <span className="text-xs font-mono text-[#596273] w-4 text-center">#{rank}</span>;
};

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ${color}`}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

export const ReputationPage: React.FC<ReputationPageProps> = ({ onNavigate: _ }) => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardAgent[]>([]);
  const [summary, setSummary] = useState<ReputationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [recalculating, setRecalculating] = useState(false);
  const [recalcMsg, setRecalcMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [lb, sm] = await Promise.all([
        fetchReputationLeaderboard(100, typeFilter !== 'all' ? typeFilter : undefined),
        fetchReputationSummary(),
      ]);
      setLeaderboard(lb);
      setSummary(sm);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load reputation data');
    } finally {
      setLoading(false);
    }
  }, [typeFilter]);

  useEffect(() => { load(); }, [load]);

  const handleRecalculate = async () => {
    setRecalculating(true);
    setRecalcMsg(null);
    try {
      const result = await recalculateAllReputations();
      setRecalcMsg(`Recalculated ${result.recalculated_agents} agents successfully.`);
      await load();
    } catch (e: unknown) {
      setRecalcMsg(e instanceof Error ? e.message : 'Recalculation failed');
    } finally {
      setRecalculating(false);
    }
  };

  const tierData = summary
    ? [
        { label: 'Excellent (≥90)', count: summary.excellent_count,  color: 'bg-amber-400',   bar: 'bg-amber-400' },
        { label: 'Strong (80–89)',   count: summary.strong_count,     color: 'bg-emerald-500', bar: 'bg-emerald-500' },
        { label: 'Good (70–79)',     count: summary.good_count,       color: 'bg-blue-500',    bar: 'bg-blue-500' },
        { label: 'Moderate (60–69)', count: summary.moderate_count,   color: 'bg-orange-400',  bar: 'bg-orange-400' },
        { label: 'Weak (40–59)',     count: summary.weak_count,       color: 'bg-rose-400',    bar: 'bg-rose-400' },
        { label: 'High Risk (<40)',  count: summary.high_risk_count,  color: 'bg-rose-700',    bar: 'bg-rose-700' },
      ]
    : [];

  const totalTier = summary?.total_agents || 1;

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-8">

      {/* Header */}
      <div className="mb-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 text-yellow-600 border border-yellow-500/20 text-xs font-mono mb-2">
          <Award className="w-3.5 h-3.5" />
          <span>Agent Credibility Protocol — Phase 13</span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-[#172554]">Reputation & Trust Engine</h1>
            <p className="text-sm text-[#596273] mt-1">
              Observable, verified behavior-based reputation scores. Updated automatically on every settlement and verification outcome.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              id="btn-recalculate-all"
              onClick={handleRecalculate}
              disabled={recalculating || loading}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#172554] text-white text-xs font-semibold hover:bg-[#1e3a8a] transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${recalculating ? 'animate-spin' : ''}`} />
              {recalculating ? 'Recalculating...' : 'Recalculate All'}
            </button>
            <button
              id="btn-refresh-leaderboard"
              onClick={load}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 bg-white text-[#172554] text-xs font-semibold hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
        {recalcMsg && (
          <p className="mt-2 text-xs font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">{recalcMsg}</p>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-2xl border border-rose-200 bg-rose-50 text-rose-700 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
          <button onClick={load} className="ml-auto text-xs font-semibold underline">Retry</button>
        </div>
      )}

      {/* Platform Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total Agents',       value: summary.total_agents,       icon: <Users className="w-4 h-4" />,    color: 'text-[#172554]' },
            { label: 'Established',        value: summary.established_agents,  icon: <ShieldCheck className="w-4 h-4" />, color: 'text-emerald-700' },
            { label: 'Provisional',        value: summary.provisional_agents,  icon: <Activity className="w-4 h-4" />,  color: 'text-amber-700' },
            { label: 'Avg Reputation',     value: `${summary.average_reputation}/100`, icon: <Star className="w-4 h-4" />, color: 'text-[#3155D9]' },
          ].map(({ label, value, icon, color }) => (
            <div key={label} className="glass-panel rounded-2xl p-5 border border-slate-200">
              <div className={`flex items-center gap-1.5 text-xs ${color} mb-1`}>{icon}<span className="text-[#596273]">{label}</span></div>
              <p className="text-2xl font-extrabold text-[#18202F] mt-1 font-mono">{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tier Distribution */}
      {summary && (
        <div className="glass-panel rounded-3xl border border-slate-200 p-6">
          <div className="flex items-center gap-2 mb-5">
            <BarChart3 className="w-4 h-4 text-[#3155D9]" />
            <h2 className="font-bold text-[#18202F] text-sm">Reputation Tier Distribution</h2>
          </div>
          <div className="space-y-3">
            {tierData.map(({ label, count, bar }) => (
              <div key={label} className="flex items-center gap-3">
                <span className="text-xs font-mono text-[#596273] w-36 shrink-0">{label}</span>
                <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${bar}`}
                    style={{ width: `${totalTier ? (count / totalTier) * 100 : 0}%` }}
                  />
                </div>
                <span className="text-xs font-bold text-[#18202F] font-mono w-6 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Leaderboard */}
      <div className="glass-panel rounded-3xl border border-slate-200 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-yellow-400" />
            <h2 className="font-bold text-[#18202F]">Agent Leaderboard</h2>
            <span className="text-xs font-mono text-[#596273]">({leaderboard.length} agents)</span>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-[#596273]" />
            <span className="text-xs text-[#596273]">Type:</span>
            {['all', 'worker', 'verifier', 'orchestrator'].map((t) => (
              <button
                key={t}
                id={`filter-type-${t}`}
                onClick={() => setTypeFilter(t)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-colors ${
                  typeFilter === t
                    ? 'bg-[#172554] text-white border-[#172554]'
                    : 'bg-white text-[#596273] border-slate-200 hover:bg-slate-50'
                }`}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <RefreshCw className="w-6 h-6 text-[#3155D9] animate-spin" />
            <p className="text-sm text-[#596273] font-mono">Loading leaderboard...</p>
          </div>
        ) : leaderboard.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-[#596273]">
            <Bot className="w-10 h-10 opacity-30" />
            <p className="text-sm font-mono">No agents found. Create agents and complete tasks to populate the leaderboard.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {leaderboard.map((agent) => {
              const ls = getLevelStyle(agent.reputation_level);
              const typeBadge = TYPE_BADGE[agent.agent_type] || 'bg-slate-100 text-[#596273] border-slate-200';
              const scoreColor =
                agent.reputation_score >= 90 ? 'bg-amber-400' :
                agent.reputation_score >= 80 ? 'bg-emerald-500' :
                agent.reputation_score >= 70 ? 'bg-blue-500' :
                agent.reputation_score >= 60 ? 'bg-orange-400' : 'bg-rose-400';

              return (
                <div
                  key={agent.agent_id}
                  id={`leaderboard-row-${agent.agent_id}`}
                  className="p-4 rounded-2xl border border-slate-200 bg-white hover:border-[#3155D9]/30 hover:shadow-sm transition-all duration-200"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    {/* Rank + Icon */}
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="flex items-center justify-center w-8 h-8 rounded-xl bg-slate-50 border border-slate-200 shrink-0">
                        {RANK_ICON(agent.rank)}
                      </div>
                      <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-500 p-0.5 shrink-0">
                        <div className="w-full h-full bg-white rounded-[10px] flex items-center justify-center">
                          <Bot className="w-4 h-4 text-[#3155D9]" />
                        </div>
                      </div>
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-bold text-[#18202F] text-sm truncate">{agent.name}</h3>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${typeBadge}`}>
                            {agent.agent_type}
                          </span>
                          {agent.is_provisional && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-amber-50 text-amber-600 border border-amber-200">
                              Provisional
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] font-mono text-[#596273] mt-0.5">{agent.agent_code}</p>
                      </div>
                    </div>

                    {/* Score + Level */}
                    <div className="sm:ml-auto flex flex-wrap sm:flex-nowrap items-center gap-4 shrink-0">
                      <div className="flex flex-col items-end min-w-[90px]">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xl font-extrabold text-[#18202F] font-mono">{agent.reputation_score.toFixed(1)}</span>
                          <span className="text-xs text-[#596273]">/100</span>
                        </div>
                        <div className="w-24 mt-1">
                          <ScoreBar value={agent.reputation_score} color={scoreColor} />
                        </div>
                      </div>
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border shrink-0 ${ls.bg} ${ls.text} ${ls.border}`}>
                        {agent.reputation_level}
                      </span>
                      <div className="hidden sm:flex flex-col items-end text-right text-[11px] font-mono text-[#596273] min-w-[80px]">
                        <span className="text-emerald-700 font-bold">{agent.successful_verified_tasks} ✓ tasks</span>
                        <span>{agent.total_verified_tasks} total verified</span>
                      </div>
                    </div>
                  </div>

                  {/* Metrics bar */}
                  <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[11px] font-mono text-[#596273]">
                    <span className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3 text-emerald-600" />
                      Success: <strong className="text-emerald-700">{agent.success_rate.toFixed(1)}%</strong>
                    </span>
                    <span className="flex items-center gap-1">
                      <Star className="w-3 h-3 text-amber-500" />
                      Avg Quality: <strong className="text-[#18202F]">{agent.average_quality_score.toFixed(1)}</strong>
                    </span>
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-blue-500" />
                      {agent.successful_verified_tasks}/{agent.total_verified_tasks} verified tasks
                    </span>
                    <span className={`flex items-center gap-1 ${agent.status === 'available' ? 'text-emerald-600' : 'text-[#596273]'}`}>
                      <Zap className="w-3 h-3" />
                      {agent.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Formula Info */}
      <div className="glass-panel rounded-3xl border border-slate-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <ShieldCheck className="w-4 h-4 text-[#3155D9]" />
          <h2 className="font-bold text-[#18202F] text-sm">5-Factor Deterministic Formula</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          {[
            { label: 'Quality',        weight: '35%', desc: 'Avg verification score',    color: 'text-amber-600',   bg: 'bg-amber-50',   border: 'border-amber-200' },
            { label: 'Success Rate',   weight: '30%', desc: 'PASS / total finalized',    color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' },
            { label: 'Reliability',    weight: '20%', desc: 'PASS / all attempts',       color: 'text-[#3155D9]',   bg: 'bg-blue-50',    border: 'border-blue-200' },
            { label: 'Consistency',    weight: '10%', desc: 'Score stability (std dev)', color: 'text-[#6D5BD0]',   bg: 'bg-purple-50',  border: 'border-purple-200' },
            { label: 'Experience',     weight: '5%',  desc: 'Volume of verified work',   color: 'text-slate-600',   bg: 'bg-slate-100',  border: 'border-slate-200' },
          ].map(({ label, weight, desc, color, bg, border }) => (
            <div key={label} className={`p-4 rounded-2xl ${bg} border ${border}`}>
              <div className={`text-xs font-bold ${color} font-mono`}>{weight}</div>
              <div className="text-sm font-bold text-[#18202F] mt-1">{label}</div>
              <div className="text-[11px] text-[#596273] mt-0.5">{desc}</div>
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-[#596273] font-mono">
          Cold-start: agents with &lt;3 finalized verified tasks are tagged <span className="font-bold text-amber-600">Provisional</span> and use an 80.0 baseline score.
          Score updates automatically on every settlement completion and verification outcome.
        </p>
      </div>

      {/* Quick Navigation */}
      <div className="flex flex-wrap gap-3">
        <button
          id="nav-to-agents"
          onClick={() => (window as unknown as { navigateTo?: (tab: NavTab) => void }).navigateTo?.('agents')}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 bg-white text-[#172554] text-xs font-semibold hover:bg-slate-50 transition-colors"
        >
          <Bot className="w-3.5 h-3.5" />
          View All Agents
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

    </div>
  );
};
