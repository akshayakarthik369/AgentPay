import React, { useState, useEffect } from 'react';
import { mockWorkerAgent } from '../mock/demoData';
import { NavTab } from '../components/Navbar';
import { StatusBadge } from '../components/StatusBadge';
import { TaskStatus } from '../types';
import { 
  fetchDiscoverableTasks, 
  fetchAgents, 
  fetchAgentBids,
  fetchAgentAssignedTasks,
  fetchTaskSubmission,
  startExecution,
  withdrawBid,
  ApiAgent, 
  TaskMatchResult, 
  ApiBid, 
  TaskSummaryForMatch,
  ApiAgentAssignedTask 
} from '../services/api';
import { MatchScoreCard, MATCH_LEVEL_STYLES } from '../components/MatchScoreCard';
import { SubmitBidModal } from '../components/SubmitBidModal';
import { EditBidModal } from '../components/EditBidModal';
import { 
  Bot, 
  Award, 
  Wallet, 
  CheckCircle2, 
  TrendingUp, 
  Play, 
  ShieldCheck, 
  Cpu, 
  Sparkles,
  ChevronRight,
  Send,
  Edit3,
  Trash2,
  Clock,
  Briefcase,
  Loader2,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  FileCheck
} from 'lucide-react';

interface AgentDashboardPageProps {
  onNavigate: (tab: NavTab) => void;
  onSelectTask: (taskId: string) => void;
  onSelectExecution?: (executionId: number) => void;
  onSelectSubmission?: (submissionId: number) => void;
}

const BID_STATUS_STYLES: Record<string, { badge: string }> = {
  pending:   { badge: 'bg-amber-50 text-amber-700 border-amber-200' },
  accepted:  { badge: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  rejected:  { badge: 'bg-rose-50 text-rose-700 border-rose-200' },
  withdrawn: { badge: 'bg-slate-500/10 text-[#596273] border-slate-500/30' },
};

export const AgentDashboardPage: React.FC<AgentDashboardPageProps> = ({ 
  onNavigate, 
  onSelectTask,
  onSelectExecution,
  onSelectSubmission 
}) => {
  const [agentsList, setAgentsList] = useState<ApiAgent[]>([]);
  const [activeAgent, setActiveAgent] = useState<ApiAgent | null>(null);
  const [assignedTasks, setAssignedTasks] = useState<ApiAgentAssignedTask[]>([]);
  const [rankedMatches, setRankedMatches] = useState<TaskMatchResult[]>([]);
  const [agentBids, setAgentBids] = useState<ApiBid[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<TaskMatchResult | null>(null);
  const [bidModalTask, setBidModalTask] = useState<{ task: TaskSummaryForMatch; matchScore: number } | null>(null);
  const [editModalBid, setEditModalBid] = useState<ApiBid | null>(null);
  const [startingTaskId, setStartingTaskId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadAgentDetails = (agentId: number) => {
    fetchDiscoverableTasks(agentId)
      .then(res => setRankedMatches(res.matches || []))
      .catch(() => setRankedMatches([]));

    fetchAgentBids(agentId)
      .then(res => setAgentBids(res.bids || []))
      .catch(() => setAgentBids([]));

    fetchAgentAssignedTasks(agentId)
      .then(res => setAssignedTasks(res.tasks || []))
      .catch(() => setAssignedTasks([]));
  };

  const loadData = () => {
    fetchAgents()
      .then((agents) => {
        if (agents && agents.length > 0) {
          setAgentsList(agents);
          const current = activeAgent 
            ? agents.find(a => a.id === activeAgent.id) || agents[0]
            : agents.find(a => a.agent_type === 'worker') || agents[0];
          setActiveAgent(current);
          loadAgentDetails(current.id);
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAgentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedId = Number(e.target.value);
    const found = agentsList.find(a => a.id === selectedId);
    if (found) {
      setActiveAgent(found);
      loadAgentDetails(found.id);
    }
  };

  const handleWithdraw = async (bidId: number) => {
    if (!confirm('Are you sure you want to withdraw this bid?')) return;
    try {
      await withdrawBid(bidId);
      if (activeAgent) loadAgentDetails(activeAgent.id);
    } catch (e: any) {
      alert(e.message || 'Failed to withdraw bid');
    }
  };

  const handleStartExecution = async (task: ApiAgentAssignedTask) => {
    setStartingTaskId(task.task_id);
    setActionError(null);
    try {
      if (task.execution_id) {
        if (onSelectExecution) {
          onSelectExecution(task.execution_id);
        } else {
          onNavigate('execution');
        }
        return;
      }

      const res = await startExecution(task.task_id);
      if (activeAgent) loadAgentDetails(activeAgent.id);
      
      if (onSelectExecution && res.id) {
        onSelectExecution(res.id);
      } else {
        onNavigate('execution');
      }
    } catch (err: any) {
      setActionError(err.message || 'Failed to start execution');
    } finally {
      setStartingTaskId(null);
    }
  };

  const handleOpenExecution = (executionId: number | null) => {
    if (executionId && onSelectExecution) {
      onSelectExecution(executionId);
    } else {
      onNavigate('execution');
    }
  };

  const agent = activeAgent || {
    id: 1,
    name: mockWorkerAgent.name,
    agent_code: 'AG-1001',
    agent_type: 'worker' as const,
    description: 'Autonomous worker',
    role: mockWorkerAgent.role,
    capabilities: mockWorkerAgent.capabilities,
    status: 'available' as const,
    is_active: true,
    reputation_score: mockWorkerAgent.reputation,
    wallet_balance: mockWorkerAgent.walletBalance,
    tasks_completed: mockWorkerAgent.completedTasks,
    tasks_failed: 0,
    total_earned: 1420,
    success_rate: mockWorkerAgent.successRate,
    average_verification_score: mockWorkerAgent.avgVerificationScore,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const formatStatus = (rawStatus: string): TaskStatus => {
    if (!rawStatus) return 'Open';
    const capitalized = rawStatus.charAt(0).toUpperCase() + rawStatus.slice(1).toLowerCase();
    return capitalized as TaskStatus;
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      
      {/* Agent Profile Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200 mb-8 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-600 p-0.5 glow-cyan shrink-0">
              <div className="w-full h-full bg-[#F7F8FA] rounded-[14px] flex items-center justify-center">
                <Bot className="w-9 h-9 text-[#3155D9]" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-[#172554]">{agent.name}</h1>
                <span className="px-2.5 py-0.5 text-xs font-mono font-bold bg-blue-50 text-[#3155D9] border border-blue-200 rounded-full">
                  {agent.agent_code} · {agent.agent_type.toUpperCase()}
                </span>
                <span className={`px-2 py-0.5 text-[10px] font-mono rounded-full uppercase font-bold border ${
                  agent.status === 'busy' 
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                }`}>
                  {agent.status}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-[#334155] mt-1">{agent.description || 'Autonomous Intelligence Agent'}</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            {agentsList.length > 1 && (
              <div className="relative">
                <select
                  value={activeAgent?.id || ''}
                  onChange={handleAgentChange}
                  className="appearance-none bg-white border border-slate-300 text-xs font-mono text-[#3155D9] rounded-xl px-4 py-2.5 pr-8 focus:outline-none focus:border-cyan-500"
                >
                  {agentsList.map(a => (
                    <option key={a.id} value={a.id}>
                      Switch: {a.name} ({a.agent_code})
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-[#596273] absolute right-2.5 top-3 pointer-events-none" />
              </div>
            )}

            <div className="flex flex-wrap items-center gap-2">
              {agent.capabilities.map((cap) => (
                <span key={cap} className="px-3 py-1 rounded-lg text-xs font-mono bg-white text-[#334155] border border-slate-200">
                  {cap}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <div className="glass-card p-5 rounded-2xl border border-slate-200 hover:border-yellow-500/40 transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-[#596273] uppercase">Reputation</span>
            <Award className="w-4 h-4 text-yellow-400" />
          </div>
          <div className="text-2xl font-extrabold text-[#172554]">{agent.reputation_score} <span className="text-xs text-[#596273] font-normal">/ 100</span></div>
          <p className="text-[10px] text-emerald-700 mt-1 font-mono">Tier: Trusted Agent</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-200 hover:border-purple-200 transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-[#596273] uppercase">Wallet</span>
            <Wallet className="w-4 h-4 text-[#6D5BD0]" />
          </div>
          <div className="text-2xl font-extrabold text-[#6D5BD0]">{typeof agent.wallet_balance === 'number' ? agent.wallet_balance.toFixed(0) : '0'} <span className="text-xs text-[#6D5BD0] font-normal">APT</span></div>
          <p className="text-[10px] text-[#596273] mt-1 font-mono">Liquid AP Balance</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-200 hover:border-blue-300 transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-[#596273] uppercase">Completed</span>
            <CheckCircle2 className="w-4 h-4 text-[#3155D9]" />
          </div>
          <div className="text-2xl font-extrabold text-[#3155D9]">{agent.tasks_completed ?? 0}</div>
          <p className="text-[10px] text-[#596273] mt-1 font-mono">Tasks Delivered</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-200 hover:border-emerald-500/40 transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-[#596273] uppercase">Success Rate</span>
            <TrendingUp className="w-4 h-4 text-emerald-700" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-700">{agent.success_rate && agent.success_rate > 0 ? `${agent.success_rate}%` : '100%'}</div>
          <p className="text-[10px] text-[#596273] mt-1 font-mono">Pass Ratio</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-200 hover:border-indigo-500/40 transition-colors col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-[#596273] uppercase">Avg Quality</span>
            <ShieldCheck className="w-4 h-4 text-[#1E3A8A]" />
          </div>
          <div className="text-2xl font-extrabold text-[#172554]">{agent.average_verification_score && agent.average_verification_score > 0 ? `${agent.average_verification_score}%` : '95%'}</div>
          <p className="text-[10px] text-[#596273] mt-1 font-mono">Audit Score</p>
        </div>
      </div>

      {actionError && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-rose-700 shrink-0" />
          <span className="text-sm text-rose-800 font-mono">{actionError}</span>
        </div>
      )}

      {/* PHASE 8: Assigned Work Section */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200 mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
          <div>
            <h3 className="text-lg font-bold text-[#18202F] flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-[#6D5BD0]" />
              Assigned Work ({assignedTasks.length})
            </h3>
            <p className="text-xs text-[#596273] mt-0.5">Tasks currently assigned to this autonomous agent for execution</p>
          </div>
          <span className="text-xs font-mono text-[#3155D9] bg-white px-3 py-1 rounded-full border border-slate-200">
            Phase 8 Task Execution
          </span>
        </div>

        {assignedTasks.length === 0 ? (
          <div className="text-center py-10 text-xs font-mono text-[#87909F]">
            No active assigned tasks right now. When a requester selects your winning bid, work will appear here.
          </div>
        ) : (
          <div className="space-y-4">
            {assignedTasks.map((t) => {
              const isStarting = startingTaskId === t.task_id;
              const hasExecution = !!t.execution_id;
              const executionStatus = t.execution_status || 'pending';
              const progress = t.execution_progress ?? 0;

              return (
                <div key={t.task_id} className="p-5 rounded-2xl border border-slate-200 bg-white hover:bg-white transition-all">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-3">
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="text-xs font-mono font-bold text-[#3155D9] px-2.5 py-0.5 rounded bg-white border border-slate-200">
                        {t.task_code || `TASK-${t.task_id}`}
                      </span>
                      <StatusBadge status={formatStatus(t.task_status)} />
                      {t.execution_code && (
                        <span className="text-xs font-mono text-[#6D5BD0] bg-purple-50 border border-purple-500/20 px-2 py-0.5 rounded">
                          {t.execution_code} ({executionStatus})
                        </span>
                      )}
                      <span className="text-xs font-mono text-[#596273]">
                        Capability: <strong className="text-[#18202F]">{t.required_capability}</strong>
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-xs font-mono">
                      <span className="text-[#596273]">
                        Reward: <strong className="text-emerald-700">{t.reward} APT</strong>
                      </span>
                      {t.bid_amount && (
                        <span className="text-[#596273]">
                          Selected Bid: <strong className="text-[#6D5BD0]">{t.bid_amount} APT</strong>
                        </span>
                      )}
                      <span className="text-[#596273] flex items-center gap-1">
                        <Clock className="w-3 h-3 text-[#87909F]" />
                        <span>Deadline: {t.deadline.split('T')[0]}</span>
                      </span>
                    </div>
                  </div>

                  <h4 className="text-base font-bold text-[#18202F] mb-2">{t.title}</h4>

                  {/* Progress bar if execution exists */}
                  {hasExecution && (
                    <div className="mt-3 mb-4 p-3 rounded-xl bg-slate-50 border border-slate-200">
                      <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                        <span className="text-[#596273] flex items-center gap-1.5">
                          <Cpu className="w-3.5 h-3.5 text-[#3155D9]" />
                          Execution Progress: <strong className="text-[#18202F] uppercase">{executionStatus}</strong>
                        </span>
                        <span className="text-[#3155D9] font-bold">{progress}%</span>
                      </div>
                      <div className="w-full bg-white rounded-full h-2 overflow-hidden border border-slate-200">
                        <div 
                          className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-full rounded-full transition-all duration-500"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Action buttons based on status */}
                  <div className="flex items-center justify-between pt-3 border-t border-slate-200 flex-wrap gap-2">
                    <button
                      onClick={() => onSelectTask(String(t.task_id))}
                      className="text-xs font-mono text-[#596273] hover:text-[#3155D9] flex items-center gap-1"
                    >
                      <span>View Task Specification</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>

                    <div className="flex items-center gap-3">
                      {/* State 1: Assigned (not yet started) */}
                      {t.task_status === 'assigned' && !hasExecution && (
                        <button
                          onClick={() => handleStartExecution(t)}
                          disabled={isStarting}
                          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-mono font-bold shadow-md glow-cyan transition-all disabled:opacity-50"
                        >
                          {isStarting ? (
                            <><Loader2 className="w-3.5 h-3.5 animate-spin" /><span>Starting...</span></>
                          ) : (
                            <><Play className="w-3.5 h-3.5 fill-white" /><span>Start Execution</span></>
                          )}
                        </button>
                      )}

                      {/* State 2: Executing (running or pending) */}
                      {(t.task_status === 'executing' || executionStatus === 'running' || executionStatus === 'pending') && (
                        <button
                          onClick={() => handleOpenExecution(t.execution_id)}
                          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-mono font-bold shadow-md glow-cyan transition-all"
                        >
                          <Play className="w-3.5 h-3.5 fill-white" />
                          <span>Open Execution</span>
                        </button>
                      )}

                      {/* State 3: Completed (needs submission) */}
                      {executionStatus === 'completed' && t.task_status !== 'submitted' && (
                        <button
                          onClick={() => handleOpenExecution(t.execution_id)}
                          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-400 hover:to-indigo-500 text-white text-xs font-mono font-bold shadow-md transition-all"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-800" />
                          <span>Review & Submit Result</span>
                        </button>
                      )}

                      {/* State 4: Submitted (Awaiting verification) */}
                      {(t.task_status === 'submitted' || executionStatus === 'submitted') && (
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-50 border border-purple-200 text-[#6D5BD0] text-xs font-mono">
                            <ShieldCheck className="w-4 h-4 text-[#6D5BD0]" />
                            <span>Awaiting Verification</span>
                          </span>
                          <button
                            onClick={async () => {
                              try {
                                const sub = await fetchTaskSubmission(t.task_id);
                                if (sub && onSelectSubmission) {
                                  onSelectSubmission(sub.id);
                                  onNavigate('submission-details');
                                } else if (t.execution_id) {
                                  handleOpenExecution(t.execution_id);
                                }
                              } catch {
                                if (t.execution_id) handleOpenExecution(t.execution_id);
                              }
                            }}
                            className="flex items-center gap-1 text-xs font-mono text-[#6D5BD0] hover:text-white px-3 py-1.5 rounded-lg bg-purple-600/20 border border-purple-200"
                          >
                            <FileCheck className="w-3.5 h-3.5" />
                            <span>View Submission</span>
                          </button>
                          <button
                            onClick={() => handleOpenExecution(t.execution_id)}
                            className="text-xs font-mono text-[#596273] hover:text-[#3155D9] px-3 py-1.5 rounded-lg bg-white border border-slate-200"
                          >
                            Console
                          </button>
                        </div>
                      )}

                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Grid: Recommended Tasks & Real Bids Log */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">

        {/* Recommended Tasks & Bidding Opportunities */}
        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200">
            <div>
              <h3 className="text-lg font-bold text-[#18202F] flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[#3155D9]" />
                Recommended Bidding Opportunities
              </h3>
              <p className="text-xs text-[#596273] mt-0.5">Autonomous task discovery & matching</p>
            </div>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-white text-[#3155D9] border border-slate-300">
              {rankedMatches.length} Opportunities
            </span>
          </div>

          <div className="space-y-4">
            {rankedMatches.length > 0 ? (
              rankedMatches.slice(0, 3).map((m) => {
                const lvl = MATCH_LEVEL_STYLES[m.match_level] || MATCH_LEVEL_STYLES.moderate;
                const canBid = m.overall_score >= 60;
                return (
                  <div key={m.task.id} className="glass-card p-5 rounded-2xl border border-slate-200 hover:border-blue-300 transition-all">
                    <div className="flex items-center justify-between text-xs font-mono mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${lvl.badge}`}>
                          {m.overall_score.toFixed(0)}% {m.match_level}
                        </span>
                        <span className="text-[#596273] text-[10px]">{m.task.required_capability}</span>
                      </div>
                      <span className="text-[#6D5BD0] font-extrabold">{m.task.reward} APT</span>
                    </div>
                    <h4 className="text-sm font-bold text-[#18202F] mb-1">{m.task.title}</h4>
                    
                    <div className="flex items-center justify-between pt-3 mt-2 border-t border-slate-200">
                      <button
                        onClick={() => setSelectedMatch(m)}
                        className="text-[11px] font-mono text-[#3155D9] hover:text-[#3155D9] flex items-center gap-1"
                      >
                        <span>Breakdown</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>

                      <button
                        onClick={() => setBidModalTask({ task: m.task, matchScore: m.overall_score })}
                        disabled={!canBid}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all shadow-sm ${
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
              })
            ) : (
              <div className="py-8 text-center text-xs font-mono text-[#87909F]">
                No active discoverable tasks matching this agent.
              </div>
            )}
          </div>
        </div>

        {/* Phase 7: My Submitted Bids Log Section */}
        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200">
            <div>
              <h3 className="text-lg font-bold text-[#18202F] flex items-center gap-2">
                <Send className="w-5 h-5 text-[#1E3A8A]" />
                My Submitted Bids ({agentBids.length})
              </h3>
              <p className="text-xs text-[#596273] mt-0.5">Live status of bids placed by this autonomous agent</p>
            </div>
            <span className="text-xs font-mono text-[#596273] bg-white px-3 py-1 rounded-full border border-slate-200">
              Real Bidding Log
            </span>
          </div>

          {agentBids.length === 0 ? (
            <div className="text-center py-8 text-xs font-mono text-[#87909F]">
              No bids placed yet. Submit a bid on any recommended task opportunity.
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {agentBids.map((b) => {
                const style = BID_STATUS_STYLES[b.status] || BID_STATUS_STYLES.pending;
                return (
                  <div key={b.id} className="p-4 rounded-2xl border border-slate-200 bg-white hover:bg-white transition-all flex flex-col justify-between gap-3">
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-mono font-bold text-[#3155D9]">{b.bid_code}</span>
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase border ${style.badge}`}>
                          {b.status}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-[#18202F] line-clamp-1">{b.task?.title || `Task #${b.task_id}`}</h4>
                      <p className="text-xs text-[#596273] line-clamp-2 mt-1 italic">"{b.proposal}"</p>
                    </div>

                    <div className="flex items-center justify-between pt-2.5 border-t border-slate-200 text-xs font-mono">
                      <div className="space-x-3 text-[#596273]">
                        <span>Bid: <strong className="text-[#6D5BD0]">{b.bid_amount} AP</strong></span>
                        <span>Score: <strong className="text-[#3155D9]">{b.selection_score}%</strong></span>
                      </div>

                      {b.status === 'pending' && (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setEditModalBid(b)}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-[#334155] text-xs font-mono border border-slate-300"
                            title="Edit Bid"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleWithdraw(b.id)}
                            className="p-1.5 rounded-lg bg-rose-50 hover:bg-rose-500/20 text-rose-700 text-xs font-mono border border-rose-200"
                            title="Withdraw Bid"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>

      {/* Match Breakdown Modal */}
      {selectedMatch && (
        <MatchScoreCard
          match={selectedMatch}
          title={selectedMatch.task.title}
          subtitle={`Task Code: ${selectedMatch.task.task_code} · Required Capability: ${selectedMatch.task.required_capability}`}
          isModal={true}
          onClose={() => setSelectedMatch(null)}
        />
      )}

      {/* Submit Bid Modal */}
      {bidModalTask && activeAgent && (
        <SubmitBidModal
          task={bidModalTask.task}
          agent={activeAgent}
          matchScore={bidModalTask.matchScore}
          onClose={() => setBidModalTask(null)}
          onSuccess={() => {
            setBidModalTask(null);
            if (activeAgent) loadAgentDetails(activeAgent.id);
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
            if (activeAgent) loadAgentDetails(activeAgent.id);
          }}
        />
      )}

    </div>
  );
};

export default AgentDashboardPage;
