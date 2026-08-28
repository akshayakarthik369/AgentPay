import React, { useState, useEffect } from 'react';
import {
  Cpu, ArrowLeft, RefreshCw, AlertCircle,
  CheckCircle2, XCircle, Clock, Star, Wallet,
  Award, ChevronRight, Zap, ShieldCheck, ToggleLeft, ToggleRight,
  Sparkles, Info, Send, Edit3, Trash2
} from 'lucide-react';
import { NavTab } from '../components/Navbar';
import {
  fetchAgentById, fetchDiscoverableTasks, fetchAgentBids,
  activateAgent, deactivateAgent, withdrawBid,
  ApiAgent, TaskMatchResult, ApiBid, TaskSummaryForMatch
} from '../services/api';
import { MatchScoreCard, MATCH_LEVEL_STYLES } from '../components/MatchScoreCard';
import { SubmitBidModal } from '../components/SubmitBidModal';
import { EditBidModal } from '../components/EditBidModal';

interface AgentDetailsPageProps {
  agentId: number;
  onNavigate: (tab: NavTab) => void;
}

const STATUS_COLORS: Record<string, string> = {
  available: 'text-emerald-700 bg-emerald-50 border-emerald-200',
  busy:      'text-amber-700  bg-amber-50  border-amber-200',
  offline:   'text-[#596273]  bg-slate-500/10  border-slate-500/30',
  suspended: 'text-rose-700   bg-rose-50   border-rose-200',
};

const TYPE_BADGE: Record<string, string> = {
  worker:       'text-[#3155D9]    bg-blue-50    border-blue-200',
  verifier:     'text-[#6D5BD0]  bg-purple-50  border-purple-200',
  orchestrator: 'text-[#1E3A8A]  bg-slate-100  border-slate-200',
};

const BID_STATUS_STYLES: Record<string, { badge: string }> = {
  pending:   { badge: 'bg-amber-50 text-amber-700 border-amber-200' },
  accepted:  { badge: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  rejected:  { badge: 'bg-rose-50 text-rose-700 border-rose-200' },
  withdrawn: { badge: 'bg-slate-500/10 text-[#596273] border-slate-500/30' },
};

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  switch (status) {
    case 'available': return <CheckCircle2 className="w-3.5 h-3.5" />;
    case 'busy':      return <Clock className="w-3.5 h-3.5" />;
    case 'offline':   return <XCircle className="w-3.5 h-3.5" />;
    case 'suspended': return <AlertCircle className="w-3.5 h-3.5" />;
    default:          return null;
  }
};

const StatCard: React.FC<{ label: string; value: string | number; icon: React.ReactNode; color?: string }> = ({
  label, value, icon, color = 'text-[#334155]'
}) => (
  <div className="glass-panel rounded-xl p-4 border border-slate-200 flex flex-col gap-1">
    <div className={`flex items-center gap-1.5 text-xs ${color}`}>
      {icon}
      <span className="text-[#596273]">{label}</span>
    </div>
    <p className="text-xl font-bold text-[#18202F] mt-1">{value}</p>
  </div>
);

export const AgentDetailsPage: React.FC<AgentDetailsPageProps> = ({ agentId, onNavigate }) => {
  const [agent, setAgent] = useState<ApiAgent | null>(null);
  const [matches, setMatches] = useState<TaskMatchResult[]>([]);
  const [bids, setBids] = useState<ApiBid[]>([]);
  const [loading, setLoading] = useState(true);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [bidsLoading, setBidsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState(false);
  
  // Modals state
  const [selectedMatch, setSelectedMatch] = useState<TaskMatchResult | null>(null);
  const [bidModalTask, setBidModalTask] = useState<{ task: TaskSummaryForMatch; matchScore: number } | null>(null);
  const [editModalBid, setEditModalBid] = useState<ApiBid | null>(null);
  const [minScoreFilter, setMinScoreFilter] = useState<number>(0);

  const loadAgentData = async () => {
    if (!agentId) return;
    try {
      const a = await fetchAgentById(agentId);
      setAgent(a);

      setTasksLoading(true);
      fetchDiscoverableTasks(agentId)
        .then((d) => setMatches(d.matches || []))
        .catch(() => {})
        .finally(() => setTasksLoading(false));

      setBidsLoading(true);
      fetchAgentBids(agentId)
        .then((res) => setBids(res.bids || []))
        .catch(() => {})
        .finally(() => setBidsLoading(false));
    } catch (e: any) {
      setError(e.message ?? 'Failed to load agent');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    loadAgentData();
  }, [agentId]);

  const handleToggle = async () => {
    if (!agent) return;
    setToggling(true);
    setError(null);
    try {
      const updated = agent.is_active ? await deactivateAgent(agent.id) : await activateAgent(agent.id);
      setAgent(updated);
      const d = await fetchDiscoverableTasks(agent.id);
      setMatches(d.matches || []);
    } catch (e: any) {
      setError(`Failed to update agent: ${e.message}`);
    } finally {
      setToggling(false);
    }
  };

  const handleWithdrawBid = async (bidId: number) => {
    if (!confirm('Are you sure you want to withdraw this bid?')) return;
    try {
      await withdrawBid(bidId);
      loadAgentData();
    } catch (e: any) {
      alert(e.message || 'Failed to withdraw bid');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F7F8FA] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <RefreshCw className="w-8 h-8 text-cyan-500 animate-spin" />
          <p className="text-[#596273] text-sm">Loading agent details…</p>
        </div>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="min-h-screen bg-[#F7F8FA] px-4 sm:px-6 lg:px-8 py-10">
        <div className="max-w-3xl mx-auto">
          <button onClick={() => onNavigate('agents')} className="flex items-center gap-2 text-[#596273] hover:text-[#18202F] text-sm mb-6">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <div className="glass-panel rounded-2xl border border-rose-200 p-8 text-center">
            <AlertCircle className="w-10 h-10 text-rose-700 mx-auto mb-3" />
            <p className="text-rose-800 font-semibold">{error ?? 'Agent not found'}</p>
          </div>
        </div>
      </div>
    );
  }

  const successRate = agent.tasks_completed + agent.tasks_failed > 0
    ? Math.round((agent.tasks_completed / (agent.tasks_completed + agent.tasks_failed)) * 100)
    : 100;

  const filteredMatches = matches.filter(m => m.overall_score >= minScoreFilter);

  return (
    <div className="min-h-screen bg-[#F7F8FA] px-4 sm:px-6 lg:px-8 py-10">
      <div className="max-w-5xl mx-auto space-y-6">

        {/* Back */}
        <button onClick={() => onNavigate('agents')} className="flex items-center gap-2 text-[#596273] hover:text-[#18202F] text-sm transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Agent Directory
        </button>

        {/* Agent Header Card */}
        <div className="glass-panel rounded-2xl border border-slate-200 p-6">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 border border-blue-200 flex items-center justify-center shrink-0">
                <Cpu className="w-8 h-8 text-[#3155D9]" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-[#18202F]">{agent.name}</h1>
                <p className="text-sm font-mono text-[#87909F] mt-0.5">{agent.agent_code}</p>
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  <span className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border uppercase tracking-wider ${STATUS_COLORS[agent.status] ?? STATUS_COLORS.offline}`}>
                    <StatusIcon status={agent.status} />
                    {agent.status}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${TYPE_BADGE[agent.agent_type] ?? TYPE_BADGE.worker}`}>
                    {agent.agent_type}
                  </span>
                  {!agent.is_active && (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold border border-slate-600 text-[#87909F] bg-slate-800">
                      Inactive
                    </span>
                  )}
                </div>
              </div>
            </div>
            {/* Toggle */}
            <button
              onClick={handleToggle}
              disabled={toggling}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border transition-all disabled:opacity-50 cursor-pointer ${
                agent.is_active
                  ? 'border-rose-200 text-rose-700 bg-rose-50 hover:bg-rose-100'
                  : 'border-emerald-200 text-emerald-700 bg-emerald-50 hover:bg-emerald-100'
              }`}
            >
              {toggling ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Updating...</span>
                </>
              ) : agent.is_active ? (
                <>
                  <ToggleRight className="w-4 h-4" />
                  <span>Deactivate Agent</span>
                </>
              ) : (
                <>
                  <ToggleLeft className="w-4 h-4" />
                  <span>Activate Agent</span>
                </>
              )}
            </button>
          </div>

          {/* Description */}
          <p className="mt-4 text-sm text-[#596273] leading-relaxed">{agent.description}</p>

          {/* Capabilities */}
          <div className="mt-4 flex flex-wrap gap-2">
            {agent.capabilities.map(cap => (
              <span key={cap} className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 text-[#172554] border border-slate-200">
                {cap}
              </span>
            ))}
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Reputation" value={agent.reputation_score} icon={<Star className="w-3.5 h-3.5" />} color="text-amber-700" />
          <StatCard label="Tasks Done" value={agent.tasks_completed} icon={<CheckCircle2 className="w-3.5 h-3.5" />} color="text-emerald-700" />
          <StatCard label="Success Rate" value={`${successRate}%`} icon={<Award className="w-3.5 h-3.5" />} color="text-[#1E3A8A]" />
          <StatCard label="Wallet (APT)" value={agent.wallet_balance.toFixed(2)} icon={<Wallet className="w-3.5 h-3.5" />} color="text-[#3155D9]" />
        </div>

        {/* Phase 7: My Submitted Bids */}
        <div className="glass-panel rounded-2xl border border-slate-200 p-6">
          <div className="flex items-center justify-between gap-4 mb-4 pb-3 border-b border-slate-200">
            <div className="flex items-center gap-2">
              <Send className="w-4 h-4 text-[#6D5BD0]" />
              <h2 className="font-bold text-[#18202F] text-sm sm:text-base">
                Agent Bids History ({bids.length})
              </h2>
            </div>
            <span className="text-xs font-mono text-[#596273]">Autonomous Bidding Log</span>
          </div>

          {bidsLoading ? (
            <div className="text-center py-6 text-[#87909F] text-xs font-mono">
              Loading bid history...
            </div>
          ) : bids.length === 0 ? (
            <div className="text-center py-6 text-[#87909F] text-xs font-mono">
              No bids submitted yet by this agent.
            </div>
          ) : (
            <div className="space-y-3">
              {bids.map((b) => {
                const style = BID_STATUS_STYLES[b.status] || BID_STATUS_STYLES.pending;
                return (
                  <div key={b.id} className="p-4 rounded-xl border border-slate-200 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono font-bold text-[#3155D9]">{b.bid_code}</span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase border ${style.badge}`}>
                          {b.status}
                        </span>
                        <span className="text-xs text-[#596273] font-medium">
                          {b.task?.title || `Task #${b.task_id}`}
                        </span>
                      </div>
                      <p className="text-xs text-[#596273] mt-1 line-clamp-1 italic">"{b.proposal}"</p>
                      <div className="flex items-center gap-4 text-[11px] font-mono text-[#87909F] mt-2">
                        <span>Bid: <strong className="text-[#6D5BD0]">{b.bid_amount} AP</strong></span>
                        <span>Est: <strong className="text-[#334155]">{b.estimated_completion_minutes}m</strong></span>
                        <span>Score: <strong className="text-[#3155D9]">{b.selection_score}%</strong></span>
                      </div>
                    </div>

                    {b.status === 'pending' && (
                      <div className="flex items-center gap-2 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-200">
                        <button
                          onClick={() => setEditModalBid(b)}
                          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-[#334155] text-xs font-mono flex items-center gap-1 border border-slate-300"
                        >
                          <Edit3 className="w-3 h-3" />
                          <span>Edit</span>
                        </button>
                        <button
                          onClick={() => handleWithdrawBid(b.id)}
                          className="px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-500/20 text-rose-700 text-xs font-mono flex items-center gap-1 border border-rose-200"
                        >
                          <Trash2 className="w-3 h-3" />
                          <span>Withdraw</span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Recommended Tasks with Multi-Factor Ranking & Submit Bid CTA */}
        <div className="glass-panel rounded-2xl border border-slate-200 p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-[#3155D9]" />
              </div>
              <div>
                <h2 className="font-bold text-[#18202F] flex items-center gap-2">
                  <span>Recommended Tasks & Bidding Opportunities</span>
                  <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-[#3155D9] border border-slate-300">
                    {filteredMatches.length} Matches
                  </span>
                </h2>
                <p className="text-xs text-[#596273]">Ranked by 5-factor deterministic matching algorithm (Requires $\ge 60\%$ suitability to bid)</p>
              </div>
            </div>
            
            {/* Filter by min score */}
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="text-[#596273]">Min Score:</span>
              <select
                value={minScoreFilter}
                onChange={(e) => setMinScoreFilter(Number(e.target.value))}
                className="px-2.5 py-1 bg-white border border-slate-300 rounded-lg text-[#18202F] focus:outline-none focus:border-cyan-500 text-xs"
              >
                <option value={0}>All Scores (0%+)</option>
                <option value={60}>Eligible to Bid (60%+)</option>
                <option value={75}>Strong+ (75%+)</option>
                <option value={90}>Excellent (90%+)</option>
              </select>
            </div>
          </div>

          {tasksLoading ? (
            <div className="flex items-center gap-2 py-10 justify-center text-[#87909F] text-sm">
              <RefreshCw className="w-4 h-4 animate-spin" /> Calculating suitability match scores…
            </div>
          ) : filteredMatches.length === 0 ? (
            <div className="py-10 text-center">
              <p className="text-[#596273] text-sm">No compatible open tasks meet the criteria for this agent.</p>
              <p className="text-[#87909F] text-xs mt-1">
                {!agent.is_active ? 'Agent must be active to discover tasks.' : 'Post a task requiring capabilities matching this agent.'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredMatches.map((m) => {
                const lvl = MATCH_LEVEL_STYLES[m.match_level] || MATCH_LEVEL_STYLES.moderate;
                const canBid = m.overall_score >= 60 && agent.is_active && agent.status === 'available';

                return (
                  <div
                    key={m.task.id}
                    className="flex flex-col md:flex-row md:items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-blue-200 bg-white hover:bg-white transition-all gap-4"
                  >
                    <div className="flex items-start gap-3.5 min-w-0">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-200 flex flex-col items-center justify-center shrink-0">
                        <span className={`text-xs font-bold font-mono ${lvl.text}`}>
                          {m.overall_score.toFixed(0)}%
                        </span>
                        <span className="text-[9px] text-[#87909F] uppercase">Match</span>
                      </div>
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <span className="text-xs font-mono font-semibold text-[#3155D9]">{m.task.task_code}</span>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase border ${lvl.badge}`}>
                            {m.match_level}
                          </span>
                          <span className="text-[11px] font-mono text-[#596273]">
                            Req: {m.task.required_capability}
                          </span>
                        </div>
                        <h3 className="text-sm font-semibold text-[#18202F] truncate">
                          {m.task.title}
                        </h3>
                        {m.reasons && m.reasons.length > 0 && (
                          <p className="text-xs text-[#596273] mt-1 line-clamp-1 flex items-center gap-1.5">
                            <Info className="w-3 h-3 text-[#3155D9] shrink-0" />
                            <span>{m.reasons[0]}</span>
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between md:justify-end gap-3 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-slate-200">
                      <div className="text-right">
                        <div className="text-sm font-bold font-mono text-white">{m.task.reward} APT</div>
                        <div className="text-[10px] text-[#87909F] font-mono">Min Rep: {m.task.minimum_reputation}</div>
                      </div>

                      <button
                        onClick={() => setSelectedMatch(m)}
                        className="px-3 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 border border-slate-300 text-[#334155] hover:text-white transition-all shadow-sm"
                      >
                        Breakdown
                      </button>

                      <button
                        onClick={() => setBidModalTask({ task: m.task, matchScore: m.overall_score })}
                        disabled={!canBid}
                        className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all shadow-sm ${
                          canBid
                            ? 'bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white glow-cyan'
                            : 'bg-white border border-slate-200 text-slate-600 cursor-not-allowed'
                        }`}
                      >
                        <Send className="w-3 h-3" />
                        <span>Submit Bid</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Meta */}
        <div className="text-xs text-slate-600 text-right">
          Registered: {new Date(agent.created_at).toLocaleString()} · Updated: {new Date(agent.updated_at).toLocaleString()}
        </div>
      </div>

      {/* Match Breakdown Modal */}
      {selectedMatch && (
        <MatchScoreCard
          match={selectedMatch}
          title={selectedMatch.task.title}
          subtitle={`Task Code: ${selectedMatch.task.task_code} · Required: ${selectedMatch.task.required_capability}`}
          isModal={true}
          onClose={() => setSelectedMatch(null)}
        />
      )}

      {/* Submit Bid Modal */}
      {bidModalTask && agent && (
        <SubmitBidModal
          task={bidModalTask.task}
          agent={agent}
          matchScore={bidModalTask.matchScore}
          onClose={() => setBidModalTask(null)}
          onSuccess={() => {
            setBidModalTask(null);
            loadAgentData();
          }}
        />
      )}

      {/* Edit Bid Modal */}
      {editModalBid && (
        <EditBidModal
          bid={editModalBid}
          onClose={() => setEditModalBid(null)}
          onSuccess={() => {
            setEditModalBid(null);
            loadAgentData();
          }}
        />
      )}
    </div>
  );
};

export default AgentDetailsPage;
