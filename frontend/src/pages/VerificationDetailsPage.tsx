import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  UserCheck,
  Award,
  FileCheck,
  Layers,
  Sparkles,
  ArrowLeft,
  RefreshCw,
  Hash,
  ExternalLink,
  ChevronRight,
  Info,
  Sliders,
  History,
  Lock,
  Cpu,
  Zap,
} from 'lucide-react';
import { Interactive3DCard } from '../components/Interactive3DCard';
import { DepthIcon } from '../components/DepthIcon';
import { AgentNode } from '../components/AgentNode';
import { MagneticButton } from '../components/MagneticButton';
import { StateBanner } from '../components/StateBanner';

import {
  fetchVerification,
  fetchVerificationAudit,
  fetchTaskSettlement,
  runVerification,
  ApiVerificationDetail,
  ApiVerificationAuditLog,
  ApiSettlement
} from '../services/api';
import { APTokenBadge } from '../components/APTokenBadge';
import { Coins } from 'lucide-react';

interface VerificationDetailsPageProps {
  verificationId: number;
  onBack: () => void;
  onNavigateToSubmission: (submissionId: number) => void;
  onNavigateToTask: (taskId: number) => void;
  onNavigateToSettlement?: (settlementId: number) => void;
}

export const VerificationDetailsPage: React.FC<VerificationDetailsPageProps> = ({
  verificationId,
  onBack,
  onNavigateToSubmission,
  onNavigateToTask,
  onNavigateToSettlement,
}) => {
  const [verification, setVerification] = useState<ApiVerificationDetail | null>(null);
  const [auditLogs, setAuditLogs] = useState<ApiVerificationAuditLog[]>([]);
  const [settlement, setSettlement] = useState<ApiSettlement | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'criteria' | 'snapshot' | 'audit'>('criteria');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [vData, aData] = await Promise.all([
        fetchVerification(verificationId),
        fetchVerificationAudit(verificationId).catch(() => []),
      ]);
      setVerification(vData);
      setAuditLogs(aData);

      if (vData?.task_id) {
        fetchTaskSettlement(vData.task_id)
          .then((s) => setSettlement(s))
          .catch(() => setSettlement(null));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load verification record');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [verificationId]);

  const handleRunEvaluation = async () => {
    try {
      setRunning(true);
      const updated = await runVerification(verificationId);
      setVerification(updated);
      const updatedAudit = await fetchVerificationAudit(verificationId).catch(() => []);
      setAuditLogs(updatedAudit);
    } catch (err: any) {
      alert(`Evaluation failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <RefreshCw className="w-10 h-10 text-[#3155D9] animate-spin mb-4" />
        <p className="text-[#596273] text-sm font-medium">Loading verification dossier...</p>
      </div>
    );
  }

  if (error || !verification) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-[#596273] hover:text-white mb-6 text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Verification Queue
        </button>
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center">
          <AlertTriangle className="w-12 h-12 text-rose-700 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-[#18202F] mb-1">Verification Record Unavailable</h2>
          <p className="text-[#596273] text-sm mb-4">{error || 'Verification not found'}</p>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const getDecisionBadge = (decision?: string | null) => {
    switch (decision) {
      case 'PASS':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold rounded-lg text-sm tracking-wide shadow-sm shadow-emerald-500/10">
            <CheckCircle2 className="w-4 h-4" /> VERIFIED PASS
          </span>
        );
      case 'FAIL':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-50 border border-rose-200 text-rose-700 font-bold rounded-lg text-sm tracking-wide shadow-sm shadow-rose-500/10">
            <XCircle className="w-4 h-4" /> VERIFICATION FAILED
          </span>
        );
      case 'REVIEW':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-200 text-amber-700 font-bold rounded-lg text-sm tracking-wide shadow-sm shadow-amber-500/10">
            <AlertTriangle className="w-4 h-4" /> HUMAN REVIEW REQUIRED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 border border-blue-200 text-[#3155D9] font-medium rounded-lg text-sm">
            <Clock className="w-4 h-4 animate-spin" /> PENDING EVALUATION
          </span>
        );
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-700';
    if (score >= 65) return 'text-amber-700';
    return 'text-rose-700';
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 65) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  const criteriaList = [
    {
      id: 'accuracy',
      title: 'Accuracy',
      weight: '30%',
      score: verification.accuracy_score,
      reasons: verification.reasons?.accuracy || []
    },
    {
      id: 'completeness',
      title: 'Completeness',
      weight: '25%',
      score: verification.completeness_score,
      reasons: verification.reasons?.completeness || []
    },
    {
      id: 'quality',
      title: 'Quality & Depth',
      weight: '20%',
      score: verification.quality_score,
      reasons: verification.reasons?.quality || []
    },
    {
      id: 'format_compliance',
      title: 'Format Compliance',
      weight: '15%',
      score: verification.format_compliance_score,
      reasons: verification.reasons?.format_compliance || []
    },
    {
      id: 'evidence_provenance',
      title: 'Evidence & Provenance',
      weight: '10%',
      score: verification.evidence_score,
      reasons: verification.reasons?.evidence_provenance || []
    }
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-[#596273] hover:text-white mb-2 text-sm transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Verification Queue
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-[#172554] tracking-tight flex items-center gap-2">
              <ShieldCheck className="w-7 h-7 text-[#3155D9]" />
              Verification Dossier: {verification.verification_code || `VR-${1000 + verification.id}`}
            </h1>
            {getDecisionBadge(verification.decision)}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigateToSubmission(verification.submission_id)}
            className="px-3.5 py-2 bg-white hover:bg-slate-50 text-[#18202F] border border-slate-200 rounded-xl text-sm font-semibold flex items-center gap-2 transition-colors shadow-sm cursor-pointer"
          >
            <Layers className="w-4 h-4 text-[#3155D9]" /> View Submission
          </button>
          <button
            onClick={() => onNavigateToTask(verification.task_id)}
            className="px-3.5 py-2 bg-white hover:bg-slate-50 text-[#18202F] border border-slate-200 rounded-xl text-sm font-semibold flex items-center gap-2 transition-colors shadow-sm cursor-pointer"
          >
            <FileCheck className="w-4 h-4 text-[#6D5BD0]" /> View Task
          </button>
          {(!verification.decision || verification.status === 'pending') && (
            <button
              onClick={handleRunEvaluation}
              disabled={running}
              className="px-4 py-2 bg-gradient-to-r from-[#172554] via-[#1E3A8A] to-[#3155D9] hover:brightness-110 text-white rounded-xl text-sm font-semibold flex items-center gap-2 transition-all shadow-md disabled:opacity-50 cursor-pointer"
            >
              {running ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Auditing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Run Audit Evaluation</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Workflow State Guidance Banner */}
      <StateBanner
        currentPhase={
          verification.decision === 'PASS'
            ? 'Cryptographically Verified (PASS)'
            : verification.decision === 'FAIL'
            ? 'Verification Evaluated (FAIL)'
            : 'Evaluation Pending'
        }
        nextAction={
          verification.decision === 'PASS'
            ? 'Automatic Settlement Completed'
            : verification.decision === 'FAIL'
            ? 'Dispute Resolution & Arbitration (Upcoming)'
            : 'Run 5-Criteria Audit Engine'
        }
        description={
          verification.decision === 'PASS'
            ? `Score: ${verification.overall_score.toFixed(1)}/100 (Required: ${verification.required_score.toFixed(0)}%). Quality, accuracy, format, completeness and provenance confirmed.`
            : verification.decision === 'FAIL'
            ? `Score: ${verification.overall_score.toFixed(1)}/100 was below the required threshold (${verification.required_score.toFixed(0)}%). Outcome contested or subject to arbitration.`
            : 'Click Run Audit Evaluation to compute the 5 explainable quality dimensions.'
        }
        nextButtonText={
          (!verification.decision || verification.status === 'pending')
            ? running ? 'Auditing...' : 'Run Audit Evaluation'
            : undefined
        }
        onNextClick={
          (!verification.decision || verification.status === 'pending')
            ? handleRunEvaluation
            : undefined
        }
      />

      {/* Phase 12 Settlement Success Banner */}
      {settlement && settlement.status === 'completed' && (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 border border-emerald-200/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100/80 text-emerald-700 flex items-center justify-center shrink-0 border border-emerald-300/60">
              <Coins className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                  Conditional Settlement Completed
                </span>
                <span className="text-[11px] font-mono font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded">
                  {settlement.settlement_code}
                </span>
              </div>
              <p className="text-xs text-slate-700 mt-0.5">
                <strong>{settlement.amount} AP</strong> automatically transferred from escrow to{' '}
                <strong className="text-slate-900">{settlement.worker_agent_name || `Agent #${settlement.worker_agent_id}`}</strong>.
              </p>
            </div>
          </div>

          {onNavigateToSettlement && (
            <button
              onClick={() => onNavigateToSettlement(settlement.id)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-all shadow-xs cursor-pointer shrink-0"
            >
              <span>View Settlement Proof</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Overall Score */}
        <Interactive3DCard level="hero" glowColor="cyan" className="p-5 rounded-2xl relative overflow-hidden">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold text-[#596273] uppercase tracking-wider">Overall Score</span>
            <Award className="w-5 h-5 text-[#3155D9]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-black ${getScoreColor(verification.overall_score)}`}>
              {verification.overall_score.toFixed(1)}%
            </span>
            <span className="text-xs text-[#596273]">
              / req: {verification.required_score.toFixed(0)}%
            </span>
          </div>
          <div className="mt-3 w-full bg-white h-2 rounded-full overflow-hidden border border-slate-200">
            <div
              className={`h-full ${getScoreBg(verification.overall_score)} transition-all duration-500`}
              style={{ width: `${Math.min(100, verification.overall_score)}%` }}
            />
          </div>
        </Interactive3DCard>

        {/* Cryptographic SHA-256 Check */}
        <Interactive3DCard level="interactive" glowColor="emerald" className="p-5 rounded-2xl">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold text-[#596273] uppercase tracking-wider">SHA-256 Integrity</span>
            <Hash className="w-5 h-5 text-emerald-700" />
          </div>
          <div className="flex items-center gap-2 mt-1">
            {verification.integrity_valid ? (
              <>
                <CheckCircle2 className="w-6 h-6 text-emerald-700 shrink-0" />
                <div>
                  <div className="text-sm font-bold text-[#18202F]">Cryptographically Valid</div>
                  <div className="text-xs text-[#596273]">Payload unaltered</div>
                </div>
              </>
            ) : (
              <>
                <XCircle className="w-6 h-6 text-rose-700 shrink-0" />
                <div>
                  <div className="text-sm font-bold text-rose-700">Hash Mismatch</div>
                  <div className="text-xs text-[#596273]">Payload tampered</div>
                </div>
              </>
            )}
          </div>
        </Interactive3DCard>

        {/* Independent Verifier */}
        <Interactive3DCard level="interactive" glowColor="purple" className="p-5 rounded-2xl">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold text-[#596273] uppercase tracking-wider">Assigned Verifier</span>
            <UserCheck className="w-5 h-5 text-[#6D5BD0]" />
          </div>
          <div className="text-sm font-bold text-[#18202F] truncate">
            {verification.verifier_snapshot?.name || `Verifier #${verification.verifier_agent_id}`}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="px-1.5 py-0.5 bg-purple-50 text-[#6D5BD0] font-mono text-[10px] rounded">
              {verification.verifier_snapshot?.verifier_code || `AG-${1000 + verification.verifier_agent_id}`}
            </span>
            <span className="text-xs text-[#596273]">
              Rep: {verification.verifier_snapshot?.reputation_score || 80}/100
            </span>
          </div>
        </Interactive3DCard>

        {/* Category Strategy */}
        <Interactive3DCard level="interactive" glowColor="indigo" className="p-5 rounded-2xl">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold text-[#596273] uppercase tracking-wider">Verifier Strategy</span>
            <Sliders className="w-5 h-5 text-[#3155D9]" />
          </div>
          <div className="text-sm font-bold text-[#18202F] truncate">
            {verification.verification_details?.category_verifier || 'Multi-Criterion Strategy'}
          </div>
          <div className="text-xs text-emerald-700 mt-1 flex items-center gap-1 font-mono">
            <Lock className="w-3 h-3" /> Verifier ≠ Worker Enforced
          </div>
        </Interactive3DCard>
      </div>


      {/* Declared Warnings Banner */}
      {verification.warnings && verification.warnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="text-sm font-bold text-amber-800">Auditor Observations & Warnings</div>
            <ul className="text-xs text-[#334155] list-disc list-inside space-y-0.5">
              {verification.warnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 flex items-center gap-2">
        <button
          onClick={() => setActiveTab('criteria')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'criteria'
              ? 'border-cyan-400 text-[#3155D9] font-bold'
              : 'border-transparent text-[#596273] hover:text-[#18202F]'
          }`}
        >
          <Sliders className="w-4 h-4" /> 5-Factor Criteria Evaluation
        </button>
        <button
          onClick={() => setActiveTab('snapshot')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'snapshot'
              ? 'border-cyan-400 text-[#3155D9] font-bold'
              : 'border-transparent text-[#596273] hover:text-[#18202F]'
          }`}
        >
          <UserCheck className="w-4 h-4" /> Verifier Snapshot
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'audit'
              ? 'border-cyan-400 text-[#3155D9] font-bold'
              : 'border-transparent text-[#596273] hover:text-[#18202F]'
          }`}
        >
          <History className="w-4 h-4" /> Audit Trail ({auditLogs.length})
        </button>
      </div>

      {/* Tab 1: 5 Criteria Cards */}
      {activeTab === 'criteria' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {criteriaList.map((crit) => (
              <div
                key={crit.id}
                className="bg-white border border-slate-200 rounded-xl p-5 space-y-3 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-[#18202F]">{crit.title}</span>
                    <span className="px-2 py-0.5 bg-slate-800 text-[#596273] text-[10px] font-mono rounded">
                      Weight: {crit.weight}
                    </span>
                  </div>
                  <span className={`text-lg font-black ${getScoreColor(crit.score)}`}>
                    {crit.score.toFixed(1)}%
                  </span>
                </div>

                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getScoreBg(crit.score)} transition-all duration-500`}
                    style={{ width: `${Math.min(100, crit.score)}%` }}
                  />
                </div>

                {/* Rationale Bullet Points */}
                <div className="pt-2 border-t border-slate-200">
                  <span className="text-[11px] font-semibold text-[#596273] uppercase tracking-wider block mb-1.5">
                    Verifier Rationale
                  </span>
                  {crit.reasons.length > 0 ? (
                    <ul className="space-y-1">
                      {crit.reasons.map((r, i) => (
                        <li key={i} className="text-xs text-[#334155] flex items-start gap-1.5">
                          <ChevronRight className="w-3.5 h-3.5 text-[#3155D9] shrink-0 mt-0.5" />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-[#596273] italic">No specific notes recorded for this criterion.</p>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Decision Policy Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 text-xs text-[#596273] space-y-2">
            <div className="flex items-center gap-2 text-[#334155] font-bold">
              <Info className="w-4 h-4 text-[#3155D9]" />
              <span>Independent Verification Decision Policy</span>
            </div>
            <p>
              • <strong>PASS:</strong> Weighted overall score ≥ required quality threshold ({verification.required_score.toFixed(0)}%). Task reaches <code className="text-[#3155D9]">verified</code> status.
            </p>
            <p>
              • <strong>REVIEW:</strong> Score is within 10 points below the required threshold. Task reaches <code className="text-amber-800">verifying</code> status for human-in-the-loop arbitration (Phase 14).
            </p>
            <p>
              • <strong>FAIL:</strong> Score is more than 10 points below threshold, or cryptographic SHA-256 validation fails. Task reaches <code className="text-rose-800">failed</code> status.
            </p>
          </div>
        </div>
      )}

      {/* Tab 2: Verifier Snapshot */}
      {activeTab === 'snapshot' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#18202F] flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-violet-400" />
              Immutable Verifier Agent State at Evaluation Time
            </h3>
            <span className="px-2 py-0.5 bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-mono rounded">
              Frozen Snapshot
            </span>
          </div>

          {verification.verifier_snapshot ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <span className="text-[#596273] block mb-1">Verifier Name & Code</span>
                <span className="text-[#18202F] font-bold text-sm">
                  {verification.verifier_snapshot.name} ({verification.verifier_snapshot.verifier_code})
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <span className="text-[#596273] block mb-1">Reputation at Verification</span>
                <span className="text-[#3155D9] font-bold text-sm">
                  {verification.verifier_snapshot.reputation_score} / 100
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <span className="text-[#596273] block mb-1">Agent Type</span>
                <span className="text-emerald-700 font-mono">
                  {verification.verifier_snapshot.agent_type}
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <span className="text-[#596273] block mb-1">Capabilities</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {verification.verifier_snapshot.capabilities?.map((c, i) => (
                    <span key={i} className="px-1.5 py-0.5 bg-slate-800 text-[#334155] text-[10px] rounded">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-[#596273]">Snapshot data not recorded.</p>
          )}

          <div className="mt-4 pt-4 border-t border-slate-200">
            <span className="text-xs font-semibold text-[#596273] block mb-1">Submission SHA-256 Hash Snapshot</span>
            <code className="text-xs text-[#334155] font-mono break-all bg-slate-50 px-3 py-1.5 rounded border border-slate-200 block">
              {verification.submission_hash_snapshot || 'N/A'}
            </code>
          </div>
        </div>
      )}

      {/* Tab 3: Chronological Audit Log */}
      {activeTab === 'audit' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6">
          <h3 className="text-sm font-bold text-[#18202F] flex items-center gap-2 mb-6">
            <History className="w-4 h-4 text-[#3155D9]" />
            Verification Audit Log Trail
          </h3>

          {auditLogs.length > 0 ? (
            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {auditLogs.map((log) => (
                <div key={log.id} className="relative group">
                  {/* Dot */}
                  <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-white border-2 border-cyan-400 group-hover:border-cyan-300 transition-colors" />
                  
                  <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-[#3155D9] font-mono uppercase tracking-wider">
                        {log.action}
                      </span>
                      <span className="text-[10px] text-[#596273] flex items-center gap-1 font-mono">
                        <Clock className="w-3 h-3" />
                        {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                    </div>

                    <p className="text-xs text-[#18202F]">{log.message}</p>

                    <div className="flex items-center gap-2 pt-1 text-[10px] text-[#596273] font-mono">
                      <span>Actor: <strong className="text-[#334155]">{log.actor_type}</strong></span>
                      {log.actor_id && <span>({log.actor_id})</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[#596273] italic">No audit log entries recorded yet.</p>
          )}
        </div>
      )}
    </div>
  );
};
