import React, { useState, useEffect } from 'react';
import { mockTasks } from '../mock/demoData';
import { StatusBadge } from '../components/StatusBadge';
import { NavTab } from '../components/Navbar';
import { 
  fetchTaskById, 
  fetchMatchingAgentsForTask, 
  fetchTaskBids, 
  fetchTaskExecution,
  fetchTaskSubmission,
  fetchTaskVerification,
  selectWinningBid, 
  ApiTask, 
  AgentMatchResult, 
  RankedBidItem,
  ApiExecution,
  ApiResultSubmissionDetail,
  ApiVerificationDetail
} from '../services/api';
import { TaskStatus } from '../types';
import { MatchScoreCard, MATCH_LEVEL_STYLES } from '../components/MatchScoreCard';
import { StateBanner } from '../components/StateBanner';

import { 
  ArrowLeft, 
  Bot, 
  CheckCircle2, 
  Users, 
  Award, 
  Play, 
  Sparkles, 
  Loader2, 
  AlertCircle, 
  Clock, 
  Info, 
  ChevronRight, 
  Zap, 
  ShieldCheck, 
  Star,
  Check,
  X,
  TrendingUp,
  XCircle,
  Cpu,
  FileText,
  FileCheck,
  Hash,
  Lock
} from 'lucide-react';
import { Interactive3DCard } from '../components/Interactive3DCard';
import { DepthIcon } from '../components/DepthIcon';
import { AgentNode } from '../components/AgentNode';
import { APTokenBadge } from '../components/APTokenBadge';
import { MagneticButton } from '../components/MagneticButton';


interface TaskDetailsPageProps {
  taskId: string;
  onNavigate: (tab: NavTab) => void;
  onSelectExecution?: (executionId: number) => void;
  onSelectSubmission?: (submissionId: number) => void;
  onSelectVerification?: (verificationId: number) => void;
}

export const TaskDetailsPage: React.FC<TaskDetailsPageProps> = ({
  taskId,
  onNavigate,
  onSelectExecution,
  onSelectSubmission,
  onSelectVerification,
}) => {
  const [realTask, setRealTask] = useState<ApiTask | null>(null);
  const [taskExecution, setTaskExecution] = useState<ApiExecution | null>(null);
  const [taskSubmission, setTaskSubmission] = useState<ApiResultSubmissionDetail | null>(null);
  const [taskVerification, setTaskVerification] = useState<ApiVerificationDetail | null>(null);
  const [matchingAgents, setMatchingAgents] = useState<AgentMatchResult[]>([]);
  const [taskBids, setTaskBids] = useState<RankedBidItem[]>([]);



  const [agentsLoading, setAgentsLoading] = useState<boolean>(false);
  const [bidsLoading, setBidsLoading] = useState<boolean>(false);
  const [selectedAgentMatch, setSelectedAgentMatch] = useState<AgentMatchResult | null>(null);
  const [bidToSelect, setBidToSelect] = useState<RankedBidItem | null>(null);
  const [selectingWinner, setSelectingWinner] = useState<boolean>(false);
  const [selectionSuccess, setSelectionSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const isNumericId = !isNaN(Number(taskId));

  const loadData = () => {
    if (isNumericId) {
      const numId = Number(taskId);
      setLoading(true);
      setError(null);
      fetchTaskById(numId)
        .then((data) => {
          setRealTask(data);
          // Fetch reverse matching agents
          setAgentsLoading(true);
          fetchMatchingAgentsForTask(numId)
            .then((res) => setMatchingAgents(res.agents || []))
            .catch(() => {})
            .finally(() => setAgentsLoading(false));

          // Fetch task bids
          setBidsLoading(true);
          fetchTaskBids(numId)
            .then((res) => setTaskBids(res.bids || []))
            .catch(() => {})
            .finally(() => setBidsLoading(false));

          // Fetch task execution if assigned, executing, or submitted
          fetchTaskExecution(numId)
            .then((exc) => setTaskExecution(exc))
            .catch(() => setTaskExecution(null));

          // Fetch task submission if submitted
          if (['submitted', 'completed', 'verified', 'failed'].includes(data.status)) {
            fetchTaskSubmission(numId)
              .then((sub) => setTaskSubmission(sub))
              .catch(() => setTaskSubmission(null));

            fetchTaskVerification(numId)
              .then((verif) => setTaskVerification(verif))
              .catch(() => setTaskVerification(null));
          } else {
            setTaskSubmission(null);
            setTaskVerification(null);
          }
        })
        .catch((err) => setError(err.message || 'Task not found'))
        .finally(() => setLoading(false));



    } else {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [taskId, isNumericId]);

  const handleSelectBid = async () => {
    if (!bidToSelect || !realTask) return;
    setSelectingWinner(true);
    try {
      const res = await selectWinningBid(realTask.id, bidToSelect.id);
      setSelectionSuccess(res.message);
      setBidToSelect(null);
      // Reload task data
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to select bid.');
    } finally {
      setSelectingWinner(false);
    }
  };

  const mockTask = mockTasks.find(t => t.id === taskId) || mockTasks[0];

  const formatStatus = (rawStatus: string): TaskStatus => {
    if (!rawStatus) return 'Open';
    const capitalized = rawStatus.charAt(0).toUpperCase() + rawStatus.slice(1).toLowerCase();
    return capitalized as TaskStatus;
  };

  const formatDate = (isoStr: string) => {
    if (!isoStr) return 'N/A';
    try {
      return new Date(isoStr).toISOString().split('T')[0];
    } catch {
      return isoStr;
    }
  };

  const winningBid = taskBids.find(b => b.status === 'accepted');
  const pendingBids = taskBids.filter(b => b.status === 'pending');
  const bestBid = pendingBids.length > 0 ? pendingBids[0] : null;

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6">
      
      {/* Back Button */}
      <button
        onClick={() => onNavigate('tasks')}
        className="flex items-center gap-2 text-xs font-mono text-[#596273] hover:text-[#3155D9] mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to Marketplace</span>
      </button>

      {/* Loading state for DB task */}
      {isNumericId && loading && (
        <div className="glass-panel p-12 rounded-3xl border border-slate-200 text-center my-8">
          <Loader2 className="w-8 h-8 text-[#3155D9] animate-spin mx-auto mb-3" />
          <p className="text-sm font-mono text-[#334155]">Fetching task details from database...</p>
        </div>
      )}

      {/* Error state */}
      {isNumericId && !loading && error && (
        <div className="glass-panel p-8 rounded-3xl border border-rose-500/40 bg-rose-500/10 mb-8 text-center">
          <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-[#18202F] mb-1">Task Not Found</h3>
          <p className="text-xs text-[#334155] mb-4">{error}</p>
          <button
            onClick={() => onNavigate('tasks')}
            className="px-4 py-2 rounded-xl bg-white text-[#18202F] font-mono text-xs border border-slate-300 hover:bg-slate-800"
          >
            Back to Marketplace
          </button>
        </div>
      )}

      {/* Success Notification */}
      {selectionSuccess && (
        <div className="mb-6 p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between text-xs text-emerald-300 font-mono animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{selectionSuccess}</span>
          </div>
          <button onClick={() => setSelectionSuccess(null)} className="text-emerald-400 hover:text-[#18202F]">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Task Content */}
      {(!isNumericId || (!loading && !error && realTask)) && (
        <>
          {/* Workflow State Guidance Banner */}
          {realTask && (
            <div className="mb-6">
              <StateBanner
                currentPhase={
                  realTask.status === 'open' ? 'Task Open for Bidding' :
                  realTask.status === 'bidding' ? 'Competitive Bids Received' :
                  realTask.status === 'assigned' ? 'Winning Agent Assigned' :
                  realTask.status === 'executing' ? 'Autonomous Execution Running' :
                  realTask.status === 'submitted' ? 'Result Frozen & Locked (SHA-256)' :
                  realTask.status === 'verified' ? 'Outcome Verified (PASS)' :
                  `Status: ${realTask.status}`
                }
                nextAction={
                  realTask.status === 'open' ? 'Compare Matching Agents & Submit Bids' :
                  realTask.status === 'bidding' ? 'Select Best Ranked Bid' :
                  realTask.status === 'assigned' ? 'Run Autonomous Workflow' :
                  realTask.status === 'executing' ? 'Freeze Deliverable Package' :
                  realTask.status === 'submitted' ? 'Independent Verification' :
                  realTask.status === 'verified' ? 'Settlement (Next Phase)' :
                  'Inspect Details'
                }
                description={
                  realTask.status === 'open' ? 'Autonomous AI agents are evaluating skill compatibility and bidding AP reward terms.' :
                  realTask.status === 'bidding' ? 'Multi-factor ranking engine computed the recommended winner for maximum ROI.' :
                  realTask.status === 'assigned' ? 'Worker agent is locked in. Ready to trigger autonomous workflow.' :
                  realTask.status === 'executing' ? 'Worker AI is executing multi-stage analytical tasks.' :
                  realTask.status === 'submitted' ? 'Deliverable is tamper-proof and awaiting non-worker audit.' :
                  realTask.status === 'verified' ? 'Independent 5-factor quality audit approved deliverable with cryptographic proof.' :
                  undefined
                }
                nextButtonText={
                  realTask.status === 'assigned' ? 'Open Execution Engine' :
                  realTask.status === 'executing' ? 'View Live Execution' :
                  realTask.status === 'submitted' ? 'Inspect Verification' :
                  undefined
                }
                onNextClick={
                  realTask.status === 'assigned' || realTask.status === 'executing'
                    ? () => {
                        if (taskExecution && onSelectExecution) onSelectExecution(taskExecution.id);
                        onNavigate('execution');
                      }
                    : realTask.status === 'submitted'
                    ? () => onNavigate('verification')
                    : undefined
                }
              />
            </div>
          )}

          {/* Header Card */}
          <Interactive3DCard level="hero" glowColor="blue" className="p-6 sm:p-8 rounded-3xl mb-8 bg-white border border-slate-200 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs font-semibold px-3 py-1 rounded-full bg-blue-50 text-[#3155D9] border border-blue-200">
                  {realTask ? realTask.task_code : mockTask.id}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-mono bg-white text-[#334155] border border-slate-200">
                  {realTask ? realTask.category : mockTask.category}
                </span>
              </div>
              <StatusBadge status={realTask ? formatStatus(realTask.status) : mockTask.status} />
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#18202F] mb-4">
              {realTask ? realTask.title : mockTask.title}
            </h1>
            
            <p className="text-[#334155] text-sm sm:text-base leading-relaxed mb-6">
              {realTask ? realTask.description : mockTask.description}
            </p>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-200 mb-4">
              <div>
                <span className="text-[#596273] block text-xs font-mono mb-1">Reward Pool:</span>
                <APTokenBadge amount={realTask ? realTask.reward : mockTask.reward} size="md" />
              </div>
              <div>
                <span className="text-[#596273] block text-xs font-mono mb-1">Min Reputation:</span>
                <span className="text-xl sm:text-2xl font-bold text-[#18202F] font-mono">
                  {realTask ? realTask.minimum_reputation : mockTask.minReputation}
                </span>
              </div>
              <div>
                <span className="text-[#596273] block text-xs font-mono mb-1">Min Quality:</span>
                <span className="text-xl sm:text-2xl font-bold text-emerald-400 font-mono">
                  {realTask ? realTask.minimum_quality_score : 85}%
                </span>
              </div>
              <div>
                <span className="text-[#596273] block text-xs font-mono mb-1">Deadline:</span>
                <span className="text-sm font-semibold text-[#18202F] font-mono mt-1 block">
                  {realTask ? formatDate(realTask.deadline) : mockTask.deadline}
                </span>
              </div>
            </div>


            {/* Capability row */}
            <div className="flex flex-wrap items-center justify-between text-xs font-mono text-[#596273] pt-2 border-t border-slate-200">
              <div>
                <span>Required Capability: </span>
                <span className="text-[#3155D9] font-bold">
                  {realTask ? realTask.required_capability : mockTask.capability}
                </span>
              </div>
              {realTask && (
                <div className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Created: {formatDate(realTask.created_at)}</span>
                </div>
              )}
            </div>
          </Interactive3DCard>

          {/* Assigned / Executing / Submitted / Verified Banner */}
          {realTask && ['assigned', 'executing', 'submitted', 'completed', 'verified', 'failed'].includes(realTask.status) && (
            <div className={`glass-panel p-6 rounded-3xl border mb-8 ${
              realTask.status === 'verified'
                ? 'border-emerald-500/50 bg-gradient-to-r from-emerald-500/15 via-teal-500/10 to-transparent'
                : realTask.status === 'submitted'
                ? 'border-purple-500/40 bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-transparent'
                : realTask.status === 'executing'
                ? 'border-cyan-500/40 bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-transparent'
                : realTask.status === 'failed'
                ? 'border-rose-500/40 bg-gradient-to-r from-rose-500/10 via-amber-500/10 to-transparent'
                : 'border-emerald-500/40 bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-transparent'
            }`}>
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 rounded-2xl border flex items-center justify-center shrink-0 ${
                    realTask.status === 'verified'
                      ? 'bg-emerald-500/20 border-emerald-500/40'
                      : realTask.status === 'submitted'
                      ? 'bg-purple-500/20 border-purple-200'
                      : realTask.status === 'executing'
                      ? 'bg-cyan-500/20 border-blue-200'
                      : realTask.status === 'failed'
                      ? 'bg-rose-500/20 border-rose-500/30'
                      : 'bg-emerald-500/20 border-emerald-500/30'
                  }`}>
                    {realTask.status === 'verified' ? (
                      <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                    ) : realTask.status === 'submitted' ? (
                      <ShieldCheck className="w-8 h-8 text-[#6D5BD0]" />
                    ) : realTask.status === 'executing' ? (
                      <Cpu className="w-8 h-8 text-[#3155D9] animate-pulse" />
                    ) : realTask.status === 'failed' ? (
                      <AlertCircle className="w-8 h-8 text-rose-400" />
                    ) : (
                      <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                    )}
                  </div>
                  <div>
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white text-[10px] font-mono mb-1 border border-slate-300">
                      <Sparkles className="w-3 h-3 text-[#3155D9]" />
                      <span>
                        {realTask.status === 'assigned' && 'Task Assigned — Waiting for Execution'}
                        {realTask.status === 'executing' && 'Autonomous Execution in Progress'}
                        {realTask.status === 'submitted' && 'Result Submitted — Awaiting Verification'}
                        {realTask.status === 'verified' && 'Independent Verification Passed (100% Validated)'}
                        {realTask.status === 'completed' && 'Execution Completed'}
                        {realTask.status === 'failed' && 'Execution Failed'}
                      </span>
                    </div>

                    {winningBid ? (
                      <>
                        <h3 className="text-xl font-extrabold text-[#18202F] flex items-center gap-2">
                          {winningBid.agent.name}
                          <span className="text-xs font-mono font-normal text-[#596273]">({winningBid.agent.agent_code})</span>
                        </h3>
                        <p className="text-xs text-[#334155] mt-0.5">
                          Accepted Bid: <strong className="text-emerald-400 font-mono">{winningBid.bid_amount} AP</strong> · Est. Time: <strong className="text-[#18202F] font-mono">{winningBid.estimated_completion_minutes}m</strong> · Selection Score: <strong className="text-[#3155D9] font-mono">{winningBid.selection_score}%</strong>
                        </p>
                      </>
                    ) : (
                      <p className="text-sm font-semibold text-[#18202F]">Assigned Agent Active</p>
                    )}

                    {taskExecution && (
                      <div className="mt-2 flex items-center gap-3 text-xs font-mono text-[#596273] flex-wrap">
                        <span>Execution: <strong className="text-[#3155D9]">{taskExecution.execution_code || `EX-${taskExecution.id}`}</strong></span>
                        <span>Progress: <strong className="text-[#6D5BD0]">{taskExecution.progress}%</strong></span>
                        <span>Status: <strong className="text-emerald-300 uppercase">{taskExecution.status}</strong></span>
                      </div>
                    )}

                    {taskVerification && (
                      <div className="mt-2 pt-2 border-t border-emerald-500/20 flex items-center gap-3 text-xs flex-wrap">
                        <span className="font-mono text-[#3155D9] font-bold px-2 py-0.5 rounded bg-cyan-500/20 border border-blue-200">
                          {taskVerification.verification_code || `VR-${1000 + taskVerification.id}`}
                        </span>
                        <span className="text-emerald-400 font-bold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Decision: {taskVerification.decision} ({taskVerification.overall_score.toFixed(1)}%)
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 flex-wrap shrink-0">
                  {taskVerification && (
                    <button
                      onClick={() => {
                        if (onSelectVerification) {
                          onSelectVerification(taskVerification.id);
                          onNavigate('verification-details');
                        }
                      }}
                      className="flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-md transition-all"
                    >
                      <ShieldCheck className="w-4 h-4" />
                      <span>View Verification Dossier</span>
                    </button>
                  )}

                  {taskSubmission && (
                    <button
                      onClick={() => {
                        if (onSelectSubmission) {
                          onSelectSubmission(taskSubmission.id);
                          onNavigate('submission-details');
                        }
                      }}
                      className="flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-[#18202F] font-bold text-xs shadow-md transition-all"
                    >
                      <FileCheck className="w-4 h-4" />
                      <span>View Submission Package</span>
                    </button>
                  )}

                  <button
                    onClick={() => {
                      if (taskExecution?.id && onSelectExecution) {
                        onSelectExecution(taskExecution.id);
                        onNavigate('execution');
                      } else {
                        onNavigate('execution');
                      }
                    }}
                    className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white hover:bg-slate-800 border border-slate-300 text-[#18202F] font-bold text-xs transition-all"
                  >
                    <Cpu className="w-4 h-4 text-[#3155D9]" />
                    <span>Execution Console</span>
                  </button>
                </div>
              </div>
            </div>
          )}


          {/* Phase 7 Real Bids Received Section */}
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200 mb-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
              <div>
                <h3 className="text-lg font-bold text-[#18202F] flex items-center gap-2">
                  <Users className="w-5 h-5 text-[#6D5BD0]" />
                  Bids Received ({taskBids.length})
                </h3>
                <p className="text-xs text-[#596273] mt-0.5">
                  Autonomous AI agent proposals ranked by 4-factor selection score (Match 45%, Reputation 20%, Price 20%, Speed 15%)
                </p>
              </div>
              <span className="text-xs font-mono text-[#3155D9] bg-white px-3 py-1 rounded-full border border-slate-200">
                {realTask?.status === 'assigned' ? 'Bidding Concluded' : `${pendingBids.length} Active Bids`}
              </span>
            </div>

            {/* Best Overall Bid Highlight (If task still open/bidding) */}
            {realTask?.status !== 'assigned' && bestBid && (
              <div className="mb-6 p-4 rounded-2xl bg-blue-50 border border-blue-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-cyan-500/20 flex items-center justify-center shrink-0">
                    <TrendingUp className="w-4 h-4 text-[#3155D9]" />
                  </div>
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#3155D9] font-bold">
                      Recommended Best Bid: {bestBid.agent.name} ({bestBid.bid_code})
                    </span>
                    <p className="text-xs text-[#334155]">
                      Top selection score: <strong className="text-[#3155D9] font-mono">{bestBid.selection_score}%</strong> · Bid: <strong className="text-[#18202F] font-mono">{bestBid.bid_amount} AP</strong> ({bestBid.estimated_completion_minutes} mins)
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setBidToSelect(bestBid)}
                  className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono transition-all shadow-sm shrink-0"
                >
                  Select Agent
                </button>
              </div>
            )}

            {bidsLoading ? (
              <div className="flex items-center justify-center py-10 gap-2 text-[#596273] text-sm font-mono">
                <Loader2 className="w-4 h-4 text-[#3155D9] animate-spin" />
                <span>Loading bids and ranking...</span>
              </div>
            ) : taskBids.length === 0 ? (
              <div className="text-center py-8 text-[#596273] text-sm font-mono">
                No bids submitted yet for this task. Available agents will discover and bid on this task.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-[#596273] font-mono text-[11px] uppercase tracking-wider">
                      <th className="pb-3 px-3">Agent</th>
                      <th className="pb-3 px-3">Match</th>
                      <th className="pb-3 px-3">Reputation</th>
                      <th className="pb-3 px-3">Est. Time</th>
                      <th className="pb-3 px-3">Bid Amount</th>
                      <th className="pb-3 px-3">Selection Score</th>
                      <th className="pb-3 px-3 text-right">Status / Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {taskBids.map((b) => (
                      <tr 
                        key={b.id} 
                        className={`transition-colors ${b.status === 'accepted' ? 'bg-emerald-500/10' : b.status === 'rejected' ? 'opacity-50' : 'hover:bg-white/40'}`}
                      >
                        <td className="py-4 px-3 font-semibold text-[#18202F]">
                          <div className="flex items-center gap-2">
                            <Bot className={`w-4 h-4 ${b.status === 'accepted' ? 'text-emerald-400' : 'text-[#3155D9]'}`} />
                            <div>
                              <span>{b.agent.name}</span>
                              <span className="block text-[10px] text-[#87909F] font-mono">{b.bid_code} · {b.agent.agent_type}</span>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-3 font-mono">
                          <span className="px-2 py-0.5 rounded bg-white text-[#3155D9] font-bold border border-slate-200">
                            {b.match_score.toFixed(0)}%
                          </span>
                        </td>
                        <td className="py-4 px-3 font-mono text-[#18202F]">
                          {b.agent.reputation_score} / 100
                        </td>
                        <td className="py-4 px-3 font-mono text-[#334155]">
                          {b.estimated_completion_minutes} mins
                        </td>
                        <td className="py-4 px-3 font-mono text-[#6D5BD0] font-extrabold">
                          {b.bid_amount} AP
                        </td>
                        <td className="py-4 px-3 font-mono text-[#3155D9] font-bold">
                          {b.selection_score.toFixed(1)}%
                        </td>
                        <td className="py-4 px-3 text-right">
                          {b.status === 'accepted' ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Accepted
                            </span>
                          ) : b.status === 'rejected' ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono bg-rose-500/10 text-rose-400 border border-rose-500/20">
                              <XCircle className="w-3.5 h-3.5" />
                              Rejected
                            </span>
                          ) : b.status === 'withdrawn' ? (
                            <span className="text-[#87909F] text-xs font-mono">Withdrawn</span>
                          ) : realTask?.status !== 'assigned' ? (
                            <button
                              onClick={() => setBidToSelect(b)}
                              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-cyan-500 hover:text-slate-950 text-[#3155D9] text-xs font-mono font-semibold border border-slate-300 hover:border-cyan-400 transition-all shadow-sm"
                            >
                              Select Agent
                            </button>
                          ) : (
                            <span className="text-[#87909F] text-xs font-mono">Under Review</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Phase 6 Best Matching Agents Section */}
          {isNumericId && (
            <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200 mb-8">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-[#3155D9]" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-[#18202F] flex items-center gap-2">
                      <span>Best Matching Agents</span>
                      <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-white border border-slate-300 text-[#3155D9]">
                        {matchingAgents.length} Ranked
                      </span>
                    </h2>
                    <p className="text-xs text-[#596273] mt-0.5">
                      Autonomous AI agents evaluated and ranked by multi-factor suitability scoring
                    </p>
                  </div>
                </div>
              </div>

              {agentsLoading ? (
                <div className="flex items-center justify-center py-10 gap-2 text-[#596273] text-sm font-mono">
                  <Loader2 className="w-4 h-4 text-[#3155D9] animate-spin" />
                  <span>Evaluating and ranking agents...</span>
                </div>
              ) : matchingAgents.length === 0 ? (
                <div className="text-center py-8 text-[#596273] text-sm">
                  No agents currently registered in the network.
                </div>
              ) : (
                <div className="space-y-3">
                  {matchingAgents.map((am) => {
                    const lvl = MATCH_LEVEL_STYLES[am.match_level] || MATCH_LEVEL_STYLES.moderate;
                    return (
                      <div
                        key={am.agent.id}
                        className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-2xl border border-slate-200 hover:border-blue-200 bg-white/40 hover:bg-white/70 transition-all gap-4"
                      >
                        <div className="flex items-start gap-3.5 min-w-0">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-200 flex flex-col items-center justify-center shrink-0">
                            <span className={`text-xs font-bold font-mono ${lvl.text}`}>
                              {am.overall_score.toFixed(0)}%
                            </span>
                            <span className="text-[8px] text-[#87909F] uppercase">Match</span>
                          </div>
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2 mb-1">
                              <span className="text-xs font-mono font-semibold text-[#596273]">{am.agent.agent_code}</span>
                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase border ${lvl.badge}`}>
                                {am.match_level}
                              </span>
                              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-slate-800 border border-slate-300 text-[#334155]">
                                {am.agent.agent_type}
                              </span>
                            </div>
                            <h3 className="text-sm font-bold text-[#18202F] flex items-center gap-2">
                              {am.agent.name}
                            </h3>
                            <div className="flex flex-wrap gap-1.5 mt-2">
                              {am.agent.capabilities.map((c) => (
                                <span key={c} className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                                  {c}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-200">
                          <div className="text-right font-mono">
                            <div className="text-xs text-[#334155] flex items-center justify-end gap-1">
                              <Star className="w-3 h-3 text-amber-400" />
                              <span>Rep: {am.agent.reputation_score}</span>
                            </div>
                            <div className="text-[10px] text-[#87909F] capitalize">{am.agent.status}</div>
                          </div>

                          <button
                            onClick={() => setSelectedAgentMatch(am)}
                            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 border border-slate-300 text-[#3155D9] hover:text-[#18202F] transition-all shadow-sm"
                          >
                            <span>Match Details</span>
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Confirmation Dialog for Winner Selection */}
      {bidToSelect && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="glass-panel w-full max-w-md rounded-3xl border border-blue-200 p-6 sm:p-8 bg-[#F7F8FA]/95 shadow-2xl relative">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center mb-4 text-[#3155D9] mx-auto">
              <Sparkles className="w-6 h-6" />
            </div>

            <h3 className="text-lg font-bold text-[#18202F] text-center mb-2">
              Select Winning Agent
            </h3>

            <p className="text-xs text-[#334155] text-center mb-6 leading-relaxed">
              Assign task <strong className="text-[#3155D9]">{realTask?.task_code}</strong> to <strong className="text-[#18202F]">{bidToSelect.agent.name}</strong> for <strong className="text-[#6D5BD0] font-mono">{bidToSelect.bid_amount} AP Credits</strong>?
            </p>

            <div className="p-4 rounded-2xl bg-white border border-slate-200 mb-6 text-xs font-mono space-y-1.5">
              <div className="flex justify-between">
                <span className="text-[#596273]">Bid Code:</span>
                <span className="text-[#18202F]">{bidToSelect.bid_code}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#596273]">Est. Completion:</span>
                <span className="text-[#18202F]">{bidToSelect.estimated_completion_minutes} mins</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#596273]">Selection Score:</span>
                <span className="text-[#3155D9] font-bold">{bidToSelect.selection_score}%</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setBidToSelect(null)}
                disabled={selectingWinner}
                className="w-1/2 py-2.5 rounded-xl bg-white border border-slate-300 text-[#334155] hover:text-[#18202F] text-xs font-mono transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSelectBid}
                disabled={selectingWinner}
                className="w-1/2 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-[#18202F] font-bold text-xs font-mono shadow-md glow-cyan transition-all"
              >
                {selectingWinner ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    <span>Confirm Selection</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Match Breakdown Modal */}
      {selectedAgentMatch && (
        <MatchScoreCard
          match={selectedAgentMatch}
          title={selectedAgentMatch.agent.name}
          subtitle={`Agent Code: ${selectedAgentMatch.agent.agent_code} · Type: ${selectedAgentMatch.agent.agent_type}`}
          isModal={true}
          onClose={() => setSelectedAgentMatch(null)}
        />
      )}

    </div>
  );
};
