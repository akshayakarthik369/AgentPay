import React, { useState, useEffect, useCallback } from 'react';
import { NavTab } from '../components/Navbar';
import {
  fetchSubmission,
  fetchSubmissionIntegrity,
  fetchSubmissionAudit,
  fetchSubmissionVerification,
  startVerification,
  runVerification,
  ApiResultSubmissionDetail,
  ApiSubmissionAuditLog,
  ApiSubmissionIntegrityResponse,
  ApiVerificationDetail,
} from '../services/api';
import {
  ArrowLeft,
  ShieldCheck,
  Lock,
  FileCheck,
  Bot,
  Briefcase,
  Cpu,
  Clock,
  CheckCircle2,
  Copy,
  Check,
  AlertTriangle,
  FileText,
  TrendingUp,
  Code2,
  BarChart3,
  BookOpen,
  History,
  Layers,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  ShieldAlert,
  Loader2,
  Sparkles,
  Database,
  Hash,
  Award,
} from 'lucide-react';
import { Interactive3DCard } from '../components/Interactive3DCard';
import { DepthIcon } from '../components/DepthIcon';
import { APTokenBadge } from '../components/APTokenBadge';
import { MagneticButton } from '../components/MagneticButton';
import { StateBanner } from '../components/StateBanner';


interface SubmissionDetailsPageProps {
  onNavigate: (tab: NavTab) => void;
  submissionId: number | null;
  onSelectTask?: (taskId: number) => void;
  onSelectAgent?: (agentId: number) => void;
  onSelectVerification?: (verificationId: number) => void;
}

export function SubmissionDetailsPage({
  onNavigate,
  submissionId,
  onSelectTask,
  onSelectAgent,
  onSelectVerification,
}: SubmissionDetailsPageProps) {
  const [submission, setSubmission] = useState<ApiResultSubmissionDetail | null>(null);
  const [auditLogs, setAuditLogs] = useState<ApiSubmissionAuditLog[]>([]);
  const [integrityStatus, setIntegrityStatus] = useState<ApiSubmissionIntegrityResponse | null>(null);
  const [verification, setVerification] = useState<ApiVerificationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifyingIntegrity, setVerifyingIntegrity] = useState(false);
  const [startingVerification, setStartingVerification] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedOutput, setCopiedOutput] = useState(false);
  const [activeSnapshotTab, setActiveSnapshotTab] = useState<'task' | 'agent' | 'bid' | 'execution' | 'raw'>('task');
  const [showSnapshots, setShowSnapshots] = useState(false);

  const loadData = useCallback(async () => {
    if (!submissionId) {
      setError('No submission ID provided.');
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const [subData, auditData, verifData] = await Promise.all([
        fetchSubmission(submissionId),
        fetchSubmissionAudit(submissionId).catch(() => []),
        fetchSubmissionVerification(submissionId).catch(() => null),
      ]);
      setSubmission(subData);
      setAuditLogs(auditData);
      setVerification(verifData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load submission package.');
    } finally {
      setLoading(false);
    }
  }, [submissionId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStartVerification = async () => {
    if (!submissionId) return;
    try {
      setStartingVerification(true);
      const startRes = await startVerification(submissionId);
      const updatedVerif = await runVerification(startRes.verification_id);
      setVerification(updatedVerif);
      if (onSelectVerification) {
        onSelectVerification(updatedVerif.id);
        onNavigate('verification-details');
      }
    } catch (err: any) {
      alert(`Verification failed: ${err.message}`);
    } finally {
      setStartingVerification(false);
    }
  };


  const handleVerifyIntegrity = async () => {
    if (!submissionId) return;
    try {
      setVerifyingIntegrity(true);
      const res = await fetchSubmissionIntegrity(submissionId);
      setIntegrityStatus(res);
      // Refresh audit logs in case integrity check logged an event
      const logs = await fetchSubmissionAudit(submissionId).catch(() => []);
      setAuditLogs(logs);
    } catch (err: any) {
      alert(`Integrity verification failed: ${err.message}`);
    } finally {
      setVerifyingIntegrity(false);
    }
  };

  const handleCopyHash = () => {
    if (!submission?.integrity_hash) return;
    navigator.clipboard.writeText(submission.integrity_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleCopyOutput = () => {
    if (!submission?.output_text) return;
    navigator.clipboard.writeText(submission.output_text);
    setCopiedOutput(true);
    setTimeout(() => setCopiedOutput(false), 2000);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="w-10 h-10 text-[#3155D9] animate-spin" />
        <p className="text-[#596273] text-sm">Loading submission package & audit snapshot...</p>
      </div>
    );
  }

  if (error || !submission) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <div className="p-8 rounded-2xl bg-rose-50 border border-rose-200 max-w-md mx-auto">
          <AlertTriangle className="w-12 h-12 text-rose-700 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-[#18202F] mb-2">Submission Not Found</h2>
          <p className="text-[#596273] text-sm mb-6">{error || 'Could not find the requested submission package.'}</p>
          <button
            onClick={() => onNavigate('tasks')}
            className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition"
          >
            Back to Marketplace
          </button>
        </div>
      </div>
    );
  }

  const structured = submission.structured_output || {};
  const taskSnap = submission.task_snapshot || {};
  const agentSnap = submission.agent_snapshot || {};
  const bidSnap = submission.bid_snapshot || {};
  const execSnap = submission.execution_snapshot || {};
  const selfAssess = submission.self_assessment || {};
  const provenance = submission.provenance || {};
  const evidence = submission.evidence || {};
  const limitations = submission.limitations || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* ── Top Bar & Breadcrumb ────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('tasks')}
            className="p-2 rounded-xl bg-white border border-slate-200 text-[#596273] hover:text-white hover:bg-slate-800 transition"
            title="Back to Tasks"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 text-xs font-medium text-[#596273] mb-1">
              <span>Task #{taskSnap.id || submission.task_id}</span>
              <span>/</span>
              <span className="text-[#6D5BD0] font-semibold">{submission.submission_code || `RS-${submission.id}`}</span>
              <span>/</span>
              <span className="text-[#87909F]">v{submission.version}.0</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#172554] flex items-center gap-3">
              <span>Result Submission Package</span>
              <span className="text-xs px-2.5 py-1 rounded-full font-mono bg-purple-50 border border-purple-200 text-[#6D5BD0]">
                {submission.submission_code || `RS-${submission.id}`}
              </span>
            </h1>
          </div>
        </div>

        {/* Badges / Actions */}
        <div className="flex flex-wrap items-center gap-3">
          {submission.is_locked && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 border border-slate-300 text-[#18202F] text-xs font-semibold">
              <Lock className="w-3.5 h-3.5 text-amber-700" />
              <span>Locked & Immutable</span>
            </div>
          )}

          {submission.verification_ready ? (
            <div className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold animate-pulse">
              <ShieldCheck className="w-4 h-4" />
              <span>Ready for Verification</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-xs font-semibold">
              <Clock className="w-4 h-4" />
              <span>Pending Finalization</span>
            </div>
          )}
          <button
            onClick={handleVerifyIntegrity}
            disabled={verifyingIntegrity}
            className="flex items-center gap-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 border border-blue-200 text-[#3155D9] rounded-xl text-xs font-semibold transition disabled:opacity-50 cursor-pointer"
          >
            {verifyingIntegrity ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Checking...</span>
              </>
            ) : (
              <>
                <Hash className="w-3.5 h-3.5" />
                <span>Verify Fingerprint</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Workflow State Guidance Banner */}
      <StateBanner
        currentPhase={
          verification?.status === 'completed' && verification?.decision === 'PASS'
            ? 'Cryptographically Verified (PASS)'
            : verification?.status === 'completed' && verification?.decision === 'FAIL'
            ? 'Verification Evaluated (FAIL)'
            : verification?.status === 'in_progress'
            ? 'Verification in Progress'
            : 'Result Frozen & SHA-256 Hash Locked'
        }
        nextAction={
          verification?.status === 'completed' && verification?.decision === 'PASS'
            ? 'Settlement (Next Phase)'
            : verification?.status === 'completed' && verification?.decision === 'FAIL'
            ? 'Dispute Resolution (Upcoming)'
            : verification?.status === 'in_progress'
            ? 'View Verification Dossier'
            : 'Start Independent Verification'
        }
        description={
          verification?.status === 'completed'
            ? `5-criteria score: ${verification.overall_score.toFixed(1)}/100 (Required: ${verification.required_score.toFixed(0)}%). Deliverable outcome: ${verification.decision}.`
            : 'Worker AI deliverable package is frozen with SHA-256. Ready for non-worker verification.'
        }
        nextButtonText={
          verification?.status === 'completed'
            ? 'View Verification Dossier'
            : !verification
            ? startingVerification
              ? 'Starting Verification...'
              : 'Run Independent Verification'
            : undefined
        }
        onNextClick={
          verification?.status === 'completed'
            ? () => {
                if (onSelectVerification) onSelectVerification(verification.id);
                onNavigate('verification-details');
              }
            : !verification
            ? handleStartVerification
            : undefined
        }
      />

      {/* ── Integrity Status Banner (if checked) ────────────────────────── */}
      {integrityStatus && (
        <div
          className={`p-4 rounded-2xl border flex items-center justify-between gap-4 transition animate-in fade-in duration-200 ${
            integrityStatus.valid
              ? 'bg-emerald-950/40 border-emerald-200 text-emerald-800'
              : 'bg-rose-950/40 border-rose-200 text-rose-800'
          }`}
        >
          <div className="flex items-center gap-3">
            {integrityStatus.valid ? (
              <CheckCircle2 className="w-6 h-6 text-emerald-700 shrink-0" />
            ) : (
              <ShieldAlert className="w-6 h-6 text-rose-700 shrink-0" />
            )}
            <div>
              <div className="font-bold text-sm">
                {integrityStatus.valid
                  ? 'SHA-256 Fingerprint Matches: Result is 100% Intact & Untampered'
                  : 'Integrity Check Failed: Content does not match original fingerprint!'}
              </div>
              <div className="text-xs opacity-80 mt-0.5">
                Algorithm: {integrityStatus.algorithm} • Stored Fingerprint:{' '}
                <span className="font-mono">{integrityStatus.stored_hash?.slice(0, 24)}...</span>
              </div>
            </div>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-lg font-semibold bg-emerald-500/20 border border-emerald-200 text-emerald-200">
            {integrityStatus.valid ? 'VALIDATED' : 'TAMPERED'}
          </span>
        </div>
      )}

      {/* ── Context Snapshots Bar ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Task Snapshot */}
        <Interactive3DCard level="interactive" glowColor="cyan" className="p-4 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs text-[#596273]">
            <span className="flex items-center gap-1.5 font-medium">
              <Briefcase className="w-3.5 h-3.5 text-[#3155D9]" />
              Task Snapshot
            </span>
            <span className="font-mono text-[#3155D9] font-bold">{taskSnap.task_code || `AP-${taskSnap.id}`}</span>
          </div>
          <div className="font-bold text-[#18202F] text-sm truncate" title={taskSnap.title}>
            {taskSnap.title || 'Untitled Task'}
          </div>
          <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-200 text-[#596273]">
            <span>Reward: <strong className="text-emerald-700 font-mono">{taskSnap.reward} AP</strong></span>
            <span>Cat: <strong className="text-[#334155]">{taskSnap.category}</strong></span>
          </div>
        </Interactive3DCard>

        {/* Worker Agent Snapshot */}
        <Interactive3DCard level="interactive" glowColor="purple" className="p-4 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs text-[#596273]">
            <span className="flex items-center gap-1.5 font-medium">
              <Bot className="w-3.5 h-3.5 text-[#6D5BD0]" />
              Agent Snapshot
            </span>
            <span className="font-mono text-[#6D5BD0] font-bold">{agentSnap.agent_code || `AG-${agentSnap.id}`}</span>
          </div>
          <div className="font-bold text-[#18202F] text-sm truncate" title={agentSnap.name}>
            {agentSnap.name || 'Worker Agent'}
          </div>
          <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-200 text-[#596273]">
            <span>Reputation: <strong className="text-amber-700 font-mono">{agentSnap.reputation_score || 80}/100</strong></span>
            <span>Success: <strong className="text-emerald-700 font-mono">{agentSnap.success_rate || 100}%</strong></span>
          </div>
        </Interactive3DCard>

        {/* Bid Snapshot */}
        <Interactive3DCard level="interactive" glowColor="emerald" className="p-4 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs text-[#596273]">
            <span className="flex items-center gap-1.5 font-medium">
              <FileCheck className="w-3.5 h-3.5 text-emerald-700" />
              Winning Bid
            </span>
            <span className="font-mono text-emerald-700 font-bold">{bidSnap.bid_code || `BD-${bidSnap.id}`}</span>
          </div>
          <div className="font-bold text-[#18202F] text-sm truncate">
            {bidSnap.bid_amount ? `${bidSnap.bid_amount} AP Credits` : 'Accepted Offer'}
          </div>
          <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-200 text-[#596273]">
            <span>Est: <strong className="text-[#334155]">{bidSnap.estimated_completion_minutes || 30}m</strong></span>
            <span>Match: <strong className="text-[#3155D9] font-mono">{Math.round((bidSnap.match_score_snapshot || 0.85) * 100)}%</strong></span>
          </div>
        </Interactive3DCard>

        {/* Execution Snapshot */}
        <Interactive3DCard level="interactive" glowColor="amber" className="p-4 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs text-[#596273]">
            <span className="flex items-center gap-1.5 font-medium">
              <Cpu className="w-3.5 h-3.5 text-amber-700" />
              Execution
            </span>
            <span className="font-mono text-amber-700 font-bold">{execSnap.execution_code || `EX-${execSnap.id}`}</span>
          </div>
          <div className="font-bold text-[#18202F] text-sm truncate">
            {execSnap.provider || 'Local Deterministic'}
          </div>
          <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-200 text-[#596273]">
            <span>Attempt: <strong className="text-[#334155]">#{execSnap.attempt_number || 1}</strong></span>
            <span>Progress: <strong className="text-emerald-700 font-mono">100%</strong></span>
          </div>
        </Interactive3DCard>
      </div>


      {/* ── Main 2-Column Content ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Result Summary, Structured Findings & Final Output */}
        <div className="lg:col-span-2 space-y-6">
          {/* Result Summary */}
          {submission.result_summary && (
            <div className="p-5 rounded-2xl bg-white border border-purple-500/20 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-2xl pointer-events-none" />
              <div className="flex items-center gap-2 text-xs font-semibold text-[#6D5BD0] uppercase tracking-wider mb-2">
                <Sparkles className="w-4 h-4" />
                Result Summary
              </div>
              <p className="text-[#18202F] text-sm leading-relaxed font-medium">
                {submission.result_summary}
              </p>
            </div>
          )}

          {/* Structured Output Cards */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-[#18202F]">
                <BarChart3 className="w-4 h-4 text-[#3155D9]" />
                Structured Result Evaluation
              </div>
              <span className="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-[#596273] font-mono">
                {taskSnap.category || 'General'}
              </span>
            </div>

            {/* Render Category-Specific Output */}
            {/* Sentiment / NLP */}
            {structured.sentiment_distribution && (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="text-xs font-semibold text-[#596273] uppercase tracking-wider">Sentiment Analysis</div>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200">
                    <div className="text-xs text-emerald-700">Positive</div>
                    <div className="text-lg font-bold text-emerald-800">{structured.sentiment_distribution.positive || '0%'}</div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-500/10 border border-slate-500/20">
                    <div className="text-xs text-[#596273]">Neutral</div>
                    <div className="text-lg font-bold text-[#334155]">{structured.sentiment_distribution.neutral || '0%'}</div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200">
                    <div className="text-xs text-rose-700">Negative</div>
                    <div className="text-lg font-bold text-rose-800">{structured.sentiment_distribution.negative || '0%'}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Research / Findings */}
            {Array.isArray(structured.findings) && structured.findings.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-[#596273] uppercase tracking-wider">Key Findings</div>
                <div className="space-y-2">
                  {structured.findings.map((f: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3">
                      <span className="w-5 h-5 rounded-full bg-blue-50 text-[#3155D9] font-mono text-xs flex items-center justify-center shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <div className="text-xs text-[#334155] leading-relaxed">
                        {typeof f === 'string' ? f : (f.title || f.finding || JSON.stringify(f))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Themes */}
            {Array.isArray(structured.themes) && structured.themes.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-[#596273] uppercase tracking-wider">Identified Themes</div>
                <div className="flex flex-wrap gap-2">
                  {structured.themes.map((t: string, idx: number) => (
                    <span key={idx} className="px-3 py-1 rounded-lg bg-blue-50 border border-blue-200 text-[#3155D9] text-xs font-medium">
                      #{t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Key Metrics (Data analysis) */}
            {structured.key_metrics && typeof structured.key_metrics === 'object' && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-[#596273] uppercase tracking-wider">Computed Metrics</div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {Object.entries(structured.key_metrics).map(([k, v]: [string, any]) => (
                    <div key={k} className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                      <div className="text-xs text-[#596273] capitalize">{k.replace(/_/g, ' ')}</div>
                      <div className="text-sm font-bold text-[#18202F] font-mono mt-0.5">{String(v)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Code Quality & Issues */}
            {Array.isArray(structured.issues) && structured.issues.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-[#596273] uppercase tracking-wider">Issues Identified</div>
                <div className="space-y-2">
                  {structured.issues.map((issue: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl bg-amber-500/5 border border-amber-200 flex items-start gap-2 text-xs text-amber-200">
                      <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                      <span>{typeof issue === 'string' ? issue : (issue.description || JSON.stringify(issue))}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Content Sections */}
            {Array.isArray(structured.sections) && structured.sections.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-[#596273] uppercase tracking-wider">Generated Sections</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {structured.sections.map((sec: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs text-[#334155]">
                      <span className="font-semibold text-[#18202F]">{sec.title || `Section ${idx + 1}`}</span>
                      <span className="text-[#87909F] font-mono">{sec.word_count ? `${sec.word_count} words` : 'Drafted'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Final Output Text Card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-[#18202F]">
                <FileText className="w-4 h-4 text-emerald-700" />
                Final Output Payload
              </div>
              <button
                onClick={handleCopyOutput}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-[#334155] text-xs font-medium transition"
              >
                {copiedOutput ? <Check className="w-3.5 h-3.5 text-emerald-700" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedOutput ? 'Copied' : 'Copy Output'}</span>
              </button>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-[#334155] font-mono text-xs whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto select-all">
              {submission.output_text || 'No output text provided.'}
            </div>
          </div>
        </div>

        {/* Right Col: Evidence, Self-Assessment, Integrity, Audit Timeline */}
        <div className="space-y-6">
          {/* Worker Self-Assessment Card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-[#18202F]">
                <TrendingUp className="w-4 h-4 text-[#6D5BD0]" />
                Worker Self-Assessment
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-purple-50 border border-purple-500/20 text-[#6D5BD0] font-medium">
                Internal Score
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <div className="text-xs text-[#596273]">Confidence</div>
                <div className="text-lg font-bold text-[#6D5BD0] font-mono mt-1">
                  {submission.confidence_score !== null ? `${submission.confidence_score}%` : `${selfAssess.confidence || 85}%`}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <div className="text-xs text-[#596273]">Completeness</div>
                <div className="text-lg font-bold text-[#3155D9] font-mono mt-1">
                  {selfAssess.completeness || 90}%
                </div>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <div className="text-xs text-[#596273]">Compliance</div>
                <div className="text-lg font-bold text-emerald-800 font-mono mt-1">
                  {selfAssess.format_compliance || 100}%
                </div>
              </div>
            </div>

            {/* Prominent Verification Notice */}
            <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-500/20 text-xs text-[#6D5BD0]/90 leading-relaxed">
              <strong className="text-purple-200">Note:</strong> These scores were produced by the worker execution and have not yet been independently verified. Independent verification occurs in <strong>Phase 10</strong>.
            </div>
          </div>

          {/* Evidence & Provenance Card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-[#18202F]">
                <Database className="w-4 h-4 text-[#3155D9]" />
                Evidence & Provenance
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-[#3155D9] font-medium">
                Auditable
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50/50 border border-slate-200">
                <span className="text-[#596273]">Input Source:</span>
                <span className="text-white font-medium">{provenance.input_source || 'Task Specification'}</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50/50 border border-slate-200">
                <span className="text-[#596273]">External Dataset:</span>
                <span className="text-[#334155]">{provenance.external_dataset_used ? 'Yes' : 'No (Synthetic Context)'}</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50/50 border border-slate-200">
                <span className="text-[#596273]">External Sources:</span>
                <span className="text-[#334155]">{provenance.external_sources_used ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50/50 border border-slate-200">
                <span className="text-[#596273]">Provider:</span>
                <span className="text-[#3155D9] font-mono">{provenance.execution_provider || 'local_deterministic'}</span>
              </div>
            </div>

            {/* Transparency Demo Badge */}
            <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800/90 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
              <span>Synthetic/Demo evidence explicitly labeled for evaluation.</span>
            </div>
          </div>

          {/* Explicit Limitations Card */}
          {limitations.length > 0 && (
            <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-[#18202F]">
                <AlertTriangle className="w-4 h-4 text-amber-700" />
                Declared Limitations
              </div>
              <ul className="space-y-2 text-xs text-[#334155]">
                {limitations.map((lim: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                    <span>{lim}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* SHA-256 Integrity Card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-[#18202F]">
                <Hash className="w-4 h-4 text-emerald-700" />
                Integrity Fingerprint
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 font-mono">
                SHA-256
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <div className="text-xs text-[#596273] mb-1">Cryptographic Fingerprint:</div>
              <div className="font-mono text-xs text-emerald-700 break-all select-all">
                {submission.integrity_hash || 'Pending Generation'}
              </div>
            </div>

            <button
              onClick={handleCopyHash}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-[#334155] text-xs font-semibold transition"
            >
              {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-700" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedHash ? 'Hash Copied to Clipboard' : 'Copy Full Fingerprint'}</span>
            </button>
          </div>

          {/* Chronological Audit Trail */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-[#18202F]">
                <History className="w-4 h-4 text-[#3155D9]" />
                Audit Trail ({auditLogs.length})
              </div>
              <span className="text-xs text-[#87909F] font-mono">Chronological</span>
            </div>

            <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {auditLogs.map((log, idx) => (
                <div key={log.id || idx} className="relative text-xs">
                  <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-cyan-400 ring-4 ring-slate-950" />
                  <div className="font-bold text-[#18202F] flex items-center justify-between">
                    <span className="capitalize">{log.action.replace(/_/g, ' ')}</span>
                    <span className="text-[#87909F] text-[10px] font-mono">
                      {log.created_at ? new Date(log.created_at).toLocaleTimeString() : ''}
                    </span>
                  </div>
                  <div className="text-[#596273] text-[11px] mt-0.5">{log.message}</div>
                  <div className="text-[#87909F] text-[10px] font-mono mt-0.5">
                    Actor: <span className="text-[#596273]">{log.actor_type}</span> {log.actor_id ? `(${log.actor_id})` : ''}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Snapshot Inspector (Judge / Audit Mode) ─────────────────────── */}
      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <button
          onClick={() => setShowSnapshots(!showSnapshots)}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-850/50 transition text-left"
        >
          <div className="flex items-center gap-2 text-sm font-bold text-[#18202F]">
            <Layers className="w-4 h-4 text-[#6D5BD0]" />
            <span>Immutable Snapshot Inspector</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-purple-50 text-[#6D5BD0] font-mono">
              Audit Data
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-[#596273]">
            <span>{showSnapshots ? 'Hide Snapshots' : 'Inspect Frozen JSON Context'}</span>
            {showSnapshots ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </div>
        </button>

        {showSnapshots && (
          <div className="p-6 border-t border-slate-200 space-y-4">
            {/* Tabs */}
            <div className="flex flex-wrap gap-2">
              {[
                { id: 'task', label: 'Task Snapshot' },
                { id: 'agent', label: 'Agent Snapshot' },
                { id: 'bid', label: 'Bid Snapshot' },
                { id: 'execution', label: 'Execution Snapshot' },
                { id: 'raw', label: 'Complete Raw Package' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveSnapshotTab(tab.id as any)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                    activeSnapshotTab === tab.id
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-800 text-[#596273] hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* JSON Content */}
            <pre className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-[#334155] font-mono text-xs max-h-96 overflow-y-auto leading-relaxed select-all">
              {JSON.stringify(
                activeSnapshotTab === 'task'
                  ? taskSnap
                  : activeSnapshotTab === 'agent'
                  ? agentSnap
                  : activeSnapshotTab === 'bid'
                  ? bidSnap
                  : activeSnapshotTab === 'execution'
                  ? execSnap
                  : submission,
                null,
                2
              )}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
