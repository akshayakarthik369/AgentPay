import React, { useState, useEffect, useCallback } from 'react';
import { NavTab } from '../components/Navbar';
import { StatusBadge } from '../components/StatusBadge';
import {
  fetchExecution,
  fetchExecutionLogs,
  runExecution,
  submitExecution,
  retryExecution,
  fetchTaskSubmission,
  ApiExecution,
  ApiExecutionLog,
} from '../services/api';
import {
  Bot,
  CheckCircle2,
  Clock,
  Terminal,
  Send,
  ArrowLeft,
  Cpu,
  BarChart3,
  ShieldCheck,
  Play,
  RefreshCw,
  AlertTriangle,
  Loader2,
  FileText,
  TrendingUp,
  Code2,
  BookOpen,
  FileCheck,
  Sparkles,
  Activity,
  Zap,
} from 'lucide-react';
import { AgentNode } from '../components/AgentNode';
import { Interactive3DCard } from '../components/Interactive3DCard';
import { APTokenBadge } from '../components/APTokenBadge';
import { DepthIcon } from '../components/DepthIcon';
import { MagneticButton } from '../components/MagneticButton';
import { StateBanner } from '../components/StateBanner';


interface ExecutionPageProps {
  onNavigate: (tab: NavTab) => void;
  executionId: number | null;
  onSelectSubmission?: (submissionId: number) => void;
}


const STATUS_CONFIGS: Record<string, { label: string; color: string; bg: string }> = {
  pending:   { label: 'Pending',   color: 'text-amber-700',  bg: 'bg-amber-50 border-amber-200' },
  running:   { label: 'Running',   color: 'text-[#3155D9]',   bg: 'bg-blue-50 border-blue-200' },
  completed: { label: 'Completed', color: 'text-emerald-700',bg: 'bg-emerald-50 border-emerald-200' },
  submitted: { label: 'Submitted', color: 'text-[#6D5BD0]', bg: 'bg-purple-50 border-purple-200' },
  failed:    { label: 'Failed',    color: 'text-rose-700',   bg: 'bg-rose-50 border-rose-200' },
  cancelled: { label: 'Cancelled', color: 'text-[#596273]',  bg: 'bg-slate-500/10 border-slate-500/30' },
};

const LOG_LEVEL_COLORS: Record<string, string> = {
  info:    'text-[#3155D9]',
  warning: 'text-amber-700',
  error:   'text-rose-700',
};

const PROGRESS_STAGES = [
  { pct: 0,   label: 'Queued' },
  { pct: 10,  label: 'Preparing' },
  { pct: 20,  label: 'Routing' },
  { pct: 35,  label: 'Analysing' },
  { pct: 60,  label: 'Generating' },
  { pct: 85,  label: 'Formatting' },
  { pct: 100, label: 'Complete' },
];

function getProgressStageLabel(progress: number): string {
  for (let i = PROGRESS_STAGES.length - 1; i >= 0; i--) {
    if (progress >= PROGRESS_STAGES[i].pct) return PROGRESS_STAGES[i].label;
  }
  return 'Queued';
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString(undefined, { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function StructuredOutputCard({ structuredJson, category }: { structuredJson: string | null; category?: string }) {
  if (!structuredJson) return null;
  let data: Record<string, any> = {};
  try { data = JSON.parse(structuredJson); } catch { return null; }

  const executor: string = data.executor || '';
  const isNLP = executor.toLowerCase().includes('nlp') || 'sentiment_distribution' in data;
  const isData = 'dataset_profile' in data;
  const isCode = 'issues_found' in data;
  const isResearch = 'findings' in data && !isCode;
  const isContent = 'word_count_estimate' in data;

  return (
    <div className="space-y-4">
      {/* Common header */}
      {data.confidence && (
        <div className="flex items-center gap-3">
          <TrendingUp className="w-4 h-4 text-[#1E3A8A] shrink-0" />
          <span className="text-xs font-mono text-[#334155]">
            Model Confidence: <strong className="text-white">{Math.round(data.confidence * 100)}%</strong>
          </span>
        </div>
      )}

      {/* NLP — Sentiment distribution */}
      {isNLP && data.sentiment_distribution && (
        <div>
          <p className="text-xs font-mono text-[#596273] mb-2">Sentiment Distribution</p>
          <div className="grid grid-cols-3 gap-3 text-center text-xs font-mono">
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200">
              <span className="block text-[#596273] text-[10px] mb-1">Positive</span>
              <span className="text-xl font-extrabold text-emerald-700">{data.sentiment_distribution.positive_pct}%</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-800 border border-slate-300">
              <span className="block text-[#596273] text-[10px] mb-1">Neutral</span>
              <span className="text-xl font-extrabold text-[#334155]">{data.sentiment_distribution.neutral_pct}%</span>
            </div>
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200">
              <span className="block text-[#596273] text-[10px] mb-1">Negative</span>
              <span className="text-xl font-extrabold text-rose-700">{data.sentiment_distribution.negative_pct}%</span>
            </div>
          </div>
          {data.dominant_themes?.length > 0 && (
            <div className="mt-3">
              <p className="text-[10px] font-mono text-[#596273] mb-2">Dominant Themes</p>
              <div className="flex flex-wrap gap-2">
                {data.dominant_themes.map((t: string, i: number) => (
                  <span key={i} className="px-2 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs font-mono text-[#172554]">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Research — findings */}
      {isResearch && data.findings?.length > 0 && (
        <div>
          <p className="text-xs font-mono text-[#596273] mb-2">Key Findings</p>
          <ul className="space-y-2">
            {data.findings.slice(0, 4).map((f: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[#334155]">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700 shrink-0 mt-0.5" />
                <span>{f}</span>
              </li>
            ))}
          </ul>
          {data.methodology && (
            <p className="text-[10px] font-mono text-[#87909F] mt-2">Methodology: {data.methodology}</p>
          )}
        </div>
      )}

      {/* Data analysis — dataset profile */}
      {isData && data.dataset_profile && (
        <div>
          <p className="text-xs font-mono text-[#596273] mb-2">Dataset Profile</p>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(data.dataset_profile).map(([k, v]) => (
              <div key={k} className="p-2 rounded-lg bg-white border border-slate-200">
                <p className="text-[10px] text-[#87909F]">{k.replace(/_/g, ' ')}</p>
                <p className="text-sm font-bold text-[#18202F]">{String(v)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Code — issues */}
      {isCode && data.issues_found?.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
            <p className="text-xs font-mono text-[#596273]">Issues Found ({data.issue_count})</p>
          </div>
          <ul className="space-y-1.5">
            {data.issues_found.map((issue: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[#334155]">
                <span className="text-amber-700 shrink-0">⚠</span>
                <span>{issue}</span>
              </li>
            ))}
          </ul>
          {data.quality_score != null && (
            <div className="mt-3 flex items-center gap-3">
              <span className="text-[10px] font-mono text-[#596273]">Quality Score</span>
              <span className="text-sm font-extrabold text-emerald-700">{data.quality_score}/10</span>
            </div>
          )}
        </div>
      )}

      {/* Content — sections */}
      {isContent && data.sections?.length > 0 && (
        <div>
          <p className="text-xs font-mono text-[#596273] mb-2">Generated Sections</p>
          <ul className="space-y-1.5">
            {data.sections.map((s: any, i: number) => (
              <li key={i} className="flex items-center gap-2 text-xs text-[#334155]">
                <BookOpen className="w-3.5 h-3.5 text-[#6D5BD0] shrink-0" />
                <span className="font-semibold">{s.title}</span>
              </li>
            ))}
          </ul>
          {data.word_count_estimate && (
            <p className="text-[10px] font-mono text-[#87909F] mt-2">~{data.word_count_estimate} words · Tone: {data.tone}</p>
          )}
        </div>
      )}

      {/* Fallback — steps performed */}
      {data.routing_note && (
        <div className="text-xs font-mono text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-2">
          {data.routing_note}
        </div>
      )}

      {/* Demo note */}
      {data.demo_note && (
        <p className="text-[10px] text-[#87909F] italic border-t border-slate-200 pt-2">{data.demo_note}</p>
      )}
    </div>
  );
}

export const ExecutionPage: React.FC<ExecutionPageProps> = ({ 
  onNavigate, 
  executionId,
  onSelectSubmission 
}) => {
  const [execution, setExecution] = useState<ApiExecution | null>(null);
  const [logs, setLogs] = useState<ApiExecutionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const loadExecution = useCallback(async () => {
    if (!executionId) return;
    try {
      const [exc, logsResp] = await Promise.all([
        fetchExecution(executionId),
        fetchExecutionLogs(executionId),
      ]);
      setExecution(exc);
      setLogs(logsResp.logs);
    } catch (e: any) {
      setError(e.message || 'Failed to load execution');
    } finally {
      setLoading(false);
    }
  }, [executionId]);

  useEffect(() => {
    setLoading(true);
    loadExecution();
  }, [loadExecution]);

  const handleRun = async () => {
    if (!execution) return;
    setRunning(true);
    setError(null);
    try {
      const updated = await runExecution(execution.id);
      setExecution(updated);
      const logsResp = await fetchExecutionLogs(execution.id);
      setLogs(logsResp.logs);
    } catch (e: any) {
      setError(e.message || 'Failed to run execution');
    } finally {
      setRunning(false);
    }
  };

  const handleSubmit = async () => {
    if (!execution) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await submitExecution(execution.id);
      await loadExecution();
      setSuccessMsg('Result submitted for verification successfully!');
      if (res.submission_id && onSelectSubmission) {
        onSelectSubmission(res.submission_id);
        setTimeout(() => {
          onNavigate('submission-details');
        }, 600);
      }
    } catch (e: any) {
      setError(e.message || 'Failed to submit execution');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenSubmission = async () => {
    if (!execution) return;
    try {
      const sub = await fetchTaskSubmission(execution.task_id);
      if (sub && onSelectSubmission) {
        onSelectSubmission(sub.id);
        onNavigate('submission-details');
      } else {
        setError('Submission package not found for this task.');
      }
    } catch (e: any) {
      setError('Could not open submission: ' + e.message);
    }
  };


  const handleRetry = async () => {
    if (!execution) return;
    setRetrying(true);
    setError(null);
    try {
      const updated = await retryExecution(execution.id);
      setExecution(updated);
      const logsResp = await fetchExecutionLogs(execution.id);
      setLogs(logsResp.logs);
    } catch (e: any) {
      setError(e.message || 'Failed to retry execution');
    } finally {
      setRetrying(false);
    }
  };

  if (!executionId) {
    return (
      <div className="max-w-5xl mx-auto py-8 px-4 text-center">
        <p className="text-[#596273] text-sm">No execution selected. Navigate from your Agent Dashboard.</p>
        <button onClick={() => onNavigate('agent-dashboard')} className="mt-4 text-[#3155D9] hover:text-[#3155D9] text-xs font-mono">
          ← Return to Agent Dashboard
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-20 flex flex-col items-center gap-4">
        <Loader2 className="w-8 h-8 text-[#3155D9] animate-spin" />
        <p className="text-[#596273] text-sm font-mono">Loading execution…</p>
      </div>
    );
  }

  if (!execution) {
    return (
      <div className="max-w-5xl mx-auto py-8 px-4 text-center">
        <p className="text-rose-700 text-sm">Execution not found.</p>
        <button onClick={() => onNavigate('agent-dashboard')} className="mt-4 text-[#3155D9] hover:text-[#3155D9] text-xs font-mono">
          ← Return to Agent Dashboard
        </button>
      </div>
    );
  }

  const statusCfg = STATUS_CONFIGS[execution.status] || STATUS_CONFIGS.pending;
  const stageLabel = getProgressStageLabel(execution.progress);
  const isRunnable = execution.status === 'running' || execution.status === 'pending';
  const isSubmittable = execution.status === 'completed';
  const isSubmitted = execution.status === 'submitted';
  const isFailed = execution.status === 'failed';

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6">

      {/* Back */}
      <button
        onClick={() => onNavigate('agent-dashboard')}
        className="flex items-center gap-2 text-xs font-mono text-[#596273] hover:text-[#3155D9] mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to Agent Dashboard</span>
      </button>

      {/* Success / Error banners */}
      {successMsg && (
        <div className="mb-4 p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-700 shrink-0" />
          <span className="text-sm text-emerald-800 font-mono">{successMsg}</span>
        </div>
      )}
      {error && (
        <div className="mb-4 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-700 shrink-0" />
          <span className="text-sm text-rose-800 font-mono">{error}</span>
        </div>
      )}

      {/* Workflow State Guidance Banner */}
      <div className="mb-6">
        <StateBanner
          currentPhase={
            execution.status === 'pending' ? 'Agent Ready to Execute' :
            execution.status === 'running' ? 'Autonomous Execution Running' :
            execution.status === 'completed' ? 'Deliverable Output Generated' :
            execution.status === 'submitted' ? 'Result Frozen & Locked (SHA-256)' :
            `Status: ${execution.status}`
          }
          nextAction={
            execution.status === 'pending' ? 'Run Autonomous Workflow' :
            execution.status === 'running' ? 'Package Result with SHA-256' :
            execution.status === 'completed' ? 'Submit Package for Verification' :
            execution.status === 'submitted' ? 'Independent Verification' :
            'Review Execution Log'
          }
          description={
            execution.status === 'pending' ? 'Worker AI is assigned and waiting for execution trigger.' :
            execution.status === 'running' ? 'Agent is executing multi-stage analytical processing in real time.' :
            execution.status === 'completed' ? 'Autonomous workflow completed. Ready to freeze immutable evidence.' :
            execution.status === 'submitted' ? 'Submission package created with SHA-256 integrity hash.' :
            undefined
          }
          nextButtonText={
            execution.status === 'completed' ? 'Submit for Verification' :
            execution.status === 'submitted' ? 'View Verification' :
            undefined
          }
          onNextClick={
            execution.status === 'completed' ? handleSubmit :
            execution.status === 'submitted' ? () => onNavigate('verification') :
            undefined
          }
        />
      </div>

      {/* Header Panel */}
      <Interactive3DCard level="hero" glowColor="cyan" className="p-6 sm:p-8 rounded-3xl mb-6 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-xs font-mono font-bold text-[#3155D9] px-3 py-1 rounded-lg bg-white border border-slate-200">
              {execution.execution_code || `EX-${execution.id}`}
            </span>
            <span className={`text-xs font-mono font-bold px-3 py-1 rounded-lg border ${statusCfg.bg} ${statusCfg.color}`}>
              {statusCfg.label}
            </span>
            {execution.attempt_number > 1 && (
              <span className="text-xs font-mono text-amber-700 bg-amber-50 border border-amber-200 px-2 py-1 rounded-lg">
                Attempt #{execution.attempt_number}
              </span>
            )}
          </div>

          <AgentNode
            name={execution.agent?.name || `Agent #${execution.agent_id}`}
            code={execution.agent?.agent_code || `AG-${1000 + execution.agent_id}`}
            agentType={(execution.agent?.agent_type as any) || 'worker'}
            status="busy"
            reputation={execution.agent?.reputation_score}
            showDetails
          />

        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#172554] mb-2">
          {execution.task?.title || `Task #${execution.task_id}`}
        </h1>
        <p className="text-xs sm:text-sm text-[#596273] mb-6 line-clamp-2">
          {execution.task?.description}
        </p>

        {/* Meta row */}
        <div className="flex flex-wrap items-center gap-4 mb-6 text-xs font-mono text-[#596273]">
          <span>Capability: <span className="text-[#3155D9] font-bold">{execution.task?.required_capability}</span></span>
          <span>Category: <span className="text-[#172554]">{execution.task?.category}</span></span>
          <div className="flex items-center gap-2">
            <span>Reward:</span>
            <APTokenBadge amount={execution.task?.reward || 0} size="sm" showLabel={false} />
          </div>
          {execution.bid && (
            <div className="flex items-center gap-1.5">
              <span>Accepted Bid:</span>
              <APTokenBadge amount={execution.bid.bid_amount || 0} size="sm" showLabel={false} />
              <span className="text-[#87909F]">({execution.bid.bid_code})</span>
            </div>
          )}
        </div>

        {/* 5-Stage Autonomous Execution Pipeline */}
        <div className="p-4 rounded-2xl bg-slate-50/70 border border-slate-200">
          <div className="flex items-center justify-between text-xs font-mono mb-2">
            <span className="text-[#334155] font-semibold flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#3155D9]" />
              <span>Current Stage: <strong className="text-[#3155D9]">{stageLabel}</strong></span>
            </span>
            <span className="text-[#3155D9] font-extrabold text-sm">{execution.progress}%</span>
          </div>

          <div className="w-full bg-white rounded-full h-3 overflow-hidden border border-slate-200">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                isFailed
                  ? 'bg-rose-500'
                  : isSubmitted
                  ? 'bg-gradient-to-r from-purple-500 to-indigo-500'
                  : 'bg-gradient-to-r from-cyan-500 via-indigo-500 to-purple-500 glow-cyan'
              }`}
              style={{ width: `${execution.progress}%` }}
            />
          </div>

          {/* Stage labels */}
          <div className="flex justify-between mt-2 text-[10px] font-mono">
            {PROGRESS_STAGES.filter(s => s.pct <= 100).map((s) => (
              <span
                key={s.pct}
                className={`hidden sm:block transition-colors ${
                  execution.progress >= s.pct ? 'text-[#3155D9] font-bold' : 'text-slate-600'
                }`}
              >
                {s.label}
              </span>
            ))}
          </div>
        </div>
      </Interactive3DCard>


      {/* Body grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

        {/* Execution Timeline */}
        <div className="glass-panel p-6 rounded-3xl border border-slate-200">
          <h3 className="text-lg font-bold text-[#18202F] mb-5 pb-3 border-b border-slate-200 flex items-center gap-2">
            <Clock className="w-5 h-5 text-[#1E3A8A]" />
            Execution Timeline
          </h3>

          {logs.length === 0 ? (
            <p className="text-xs text-[#87909F] font-mono">No logs yet. Start execution to see timeline.</p>
          ) : (
            <div className="space-y-4 relative before:absolute before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {logs.map((log, idx) => (
                <div key={log.id} className="flex items-start gap-4 relative">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 z-10 ${
                    log.level === 'error'
                      ? 'bg-rose-500/20 text-rose-700 border border-rose-500/40'
                      : log.level === 'warning'
                      ? 'bg-amber-500/20 text-amber-700 border border-amber-500/40'
                      : idx === logs.length - 1 && execution.status === 'running'
                      ? 'bg-blue-50 text-[#3155D9] border border-blue-300 animate-pulse'
                      : 'bg-emerald-500/20 text-emerald-700 border border-emerald-500/40'
                  }`}>
                    {log.level === 'error' ? (
                      <AlertTriangle className="w-3.5 h-3.5" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs font-semibold ${LOG_LEVEL_COLORS[log.level] || 'text-[#334155]'}`}>
                        {log.step || log.level}
                      </span>
                      <span className="text-[10px] font-mono text-[#87909F]">{formatTime(log.created_at)}</span>
                    </div>
                    <p className="text-xs text-[#596273] mt-0.5 leading-relaxed">{log.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live Log Terminal + Structured Output */}
        <div className="glass-panel p-6 rounded-3xl border border-slate-200 flex flex-col gap-5">
          {/* Terminal */}
          <div>
            <div className="flex items-center justify-between mb-3 pb-3 border-b border-slate-200">
              <h3 className="text-base font-bold text-[#18202F] flex items-center gap-2">
                <Terminal className="w-5 h-5 text-[#3155D9]" />
                Agent Activity Log
              </h3>
              {execution.status === 'running' && (
                <span className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  Live
                </span>
              )}
            </div>
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 font-mono text-xs space-y-1.5 max-h-52 overflow-y-auto">
              {logs.length === 0 ? (
                <span className="text-slate-600">Awaiting execution…</span>
              ) : logs.map((log) => (
                <div key={log.id} className="flex items-start gap-2 text-[#334155]">
                  <span className="text-[#87909F] text-[10px] shrink-0">[{formatTime(log.created_at)}]</span>
                  <span className={LOG_LEVEL_COLORS[log.level] || 'text-[#3155D9]'}>›</span>
                  <span className="leading-relaxed">{log.message}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Structured output */}
          {(execution.structured_output || execution.error_message) && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="w-4 h-4 text-[#6D5BD0]" />
                <h3 className="text-sm font-bold text-[#18202F]">
                  {isFailed ? 'Error Details' : 'Structured Result'}
                </h3>
              </div>
              <div className="p-4 rounded-2xl bg-white border border-slate-200">
                {isFailed ? (
                  <p className="text-xs font-mono text-rose-700">{execution.error_message}</p>
                ) : (
                  <StructuredOutputCard
                    structuredJson={execution.structured_output}
                    category={execution.task?.category}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Generated Output */}
      {execution.output_text && (
        <div className="glass-panel p-6 rounded-3xl border border-slate-200 mb-6">
          <h3 className="text-lg font-bold text-[#18202F] mb-4 pb-3 border-b border-slate-200 flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-700" />
            Generated Result
          </h3>
          <div className="prose prose-invert prose-sm max-w-none">
            <pre className="whitespace-pre-wrap text-xs font-sans text-[#334155] leading-relaxed bg-white p-4 rounded-xl border border-slate-200 max-h-96 overflow-y-auto">
              {execution.output_text}
            </pre>
          </div>
        </div>
      )}

      {/* Action Footer */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-xs text-[#596273] font-mono">
          {isSubmitted && (
            <span className="flex items-center gap-2 text-[#6D5BD0]">
              <ShieldCheck className="w-4 h-4" />
              Result submitted — awaiting independent verification
            </span>
          )}
          {isRunnable && !running && 'Click "Run Agent" to begin task execution.'}
          {running && 'Agent is processing the task… please wait.'}
          {isSubmittable && !isSubmitted && 'Execution complete — submit for verification when ready.'}
          {isFailed && `Execution failed on attempt ${execution.attempt_number}. You may retry.`}
        </div>

        <div className="flex flex-wrap gap-3 justify-end">
          {/* Run Agent */}
          {isRunnable && (
            <button
              id="run-agent-btn"
              onClick={handleRun}
              disabled={running}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-[#18202F] font-bold text-xs shadow-md glow-cyan transition-all"
            >
              {running ? (
                <><Loader2 className="w-4 h-4 animate-spin" /><span>Agent is working…</span></>
              ) : (
                <><Play className="w-4 h-4" /><span>Run Agent</span></>
              )}
            </button>
          )}

          {/* Retry */}
          {isFailed && (
            <button
              id="retry-execution-btn"
              onClick={handleRetry}
              disabled={retrying || (execution.attempt_number >= 3)}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed text-[#18202F] font-bold text-xs transition-all"
            >
              {retrying ? (
                <><Loader2 className="w-4 h-4 animate-spin" /><span>Retrying…</span></>
              ) : (
                <><RefreshCw className="w-4 h-4" /><span>Retry {execution.attempt_number >= 3 ? '(Max Reached)' : ''}</span></>
              )}
            </button>
          )}

          {/* Submit for Verification */}
          {isSubmittable && (
            <button
              id="submit-verification-btn"
              onClick={handleSubmit}
              disabled={submitting}
              className="flex items-center gap-2 px-8 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-[#18202F] font-bold text-xs shadow-md transition-all"
            >
              {submitting ? (
                <><Loader2 className="w-4 h-4 animate-spin" /><span>Submitting…</span></>
              ) : (
                <><Send className="w-4 h-4" /><span>Submit for Verification</span></>
              )}
            </button>
          )}

          {/* Submitted — frozen */}
          {isSubmitted && (
            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-50 border border-purple-200 text-[#6D5BD0] font-bold text-xs">
                <ShieldCheck className="w-4 h-4 text-[#6D5BD0]" />
                <span>Result Locked</span>
              </div>
              <button
                id="view-submission-btn"
                onClick={handleOpenSubmission}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-[#18202F] font-bold text-xs shadow-md transition-all"
              >
                <FileCheck className="w-4 h-4" />
                <span>View Submission Package</span>
              </button>
            </div>
          )}

        </div>
      </div>

    </div>
  );
};
