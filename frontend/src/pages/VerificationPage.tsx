import React, { useState, useEffect } from 'react';
import { NavTab } from '../components/Navbar';
import { 
  fetchPendingVerifications,
  fetchVerifications,
  startVerification,
  runVerification,
  ApiPendingVerificationItem,
  ApiVerificationSummary
} from '../services/api';
import { 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  ArrowRight, 
  Bot, 
  AlertTriangle, 
  RefreshCw, 
  ShieldAlert, 
  Clock, 
  FileCheck, 
  Hash, 
  ExternalLink, 
  Layers, 
  Lock,
  Sparkles,
  Sliders,
  Award,
  History,
  Eye,
  Check
} from 'lucide-react';
import { Interactive3DCard } from '../components/Interactive3DCard';
import { DepthIcon } from '../components/DepthIcon';
import { MagneticButton } from '../components/MagneticButton';
import { StateBanner } from '../components/StateBanner';


interface VerificationPageProps {
  onNavigate: (tab: NavTab) => void;
  onSelectSubmission?: (submissionId: number) => void;
  onSelectVerification?: (verificationId: number) => void;
}

export const VerificationPage: React.FC<VerificationPageProps> = ({
  onNavigate,
  onSelectSubmission,
  onSelectVerification
}) => {
  const [activeView, setActiveView] = useState<'queue' | 'history'>('queue');
  const [pendingSubmissions, setPendingSubmissions] = useState<ApiPendingVerificationItem[]>([]);
  const [verifications, setVerifications] = useState<ApiVerificationSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [processingId, setProcessingId] = useState<number | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [pendingData, verifsData] = await Promise.all([
        fetchPendingVerifications().catch(() => []),
        fetchVerifications().catch(() => [])
      ]);
      setPendingSubmissions(pendingData || []);
      setVerifications(verifsData || []);
    } catch (err) {
      console.error('Failed to load verification data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleStartAndRun = async (submissionId: number) => {
    try {
      setProcessingId(submissionId);
      // 1. Start verification
      const startRes = await startVerification(submissionId);
      // 2. Run verification pipeline
      await runVerification(startRes.verification_id);
      // 3. Navigate to verification details
      if (onSelectVerification) {
        onSelectVerification(startRes.verification_id);
        onNavigate('verification-details');
      }
    } catch (err: any) {
      alert(`Verification initiation failed: ${err.message}`);
    } finally {
      setProcessingId(null);
      loadData();
    }
  };

  const getDecisionBadge = (decision?: string | null) => {
    switch (decision) {
      case 'PASS':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold rounded-lg text-xs tracking-wide">
            <CheckCircle2 className="w-3.5 h-3.5" /> PASS
          </span>
        );
      case 'FAIL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-rose-50 border border-rose-200 text-rose-700 font-bold rounded-lg text-xs tracking-wide">
            <XCircle className="w-3.5 h-3.5" /> FAIL
          </span>
        );
      case 'REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-amber-50 border border-amber-200 text-amber-700 font-bold rounded-lg text-xs tracking-wide">
            <AlertTriangle className="w-3.5 h-3.5" /> REVIEW
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-blue-50 border border-blue-200 text-[#3155D9] font-medium rounded-lg text-xs">
            <Clock className="w-3.5 h-3.5 animate-spin" /> PENDING
          </span>
        );
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-8">
      
      {/* Protocol Banner */}
      <div className="glass-panel p-6 rounded-3xl border border-slate-200 bg-gradient-to-r from-blue-50/60 via-white to-purple-50/60 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-6 h-6 text-[#3155D9]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase tracking-wider text-[#3155D9] font-bold">
                Phase 10 Independent Verification Protocol
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
                Active Engine
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-[#172554] mt-0.5">
              Autonomous Result Verification & Quality Auditing
            </h1>
            <p className="text-xs text-[#334155] mt-1 max-w-2xl">
              Submitted work packages are independently evaluated by specialized verifier agents (<code className="text-[#3155D9]">Verifier ≠ Worker</code> enforced). Evaluates SHA-256 integrity and 5 explainable quality criteria before release.
            </p>
          </div>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white hover:bg-slate-50 text-[#18202F] border border-slate-200 text-xs font-semibold transition shrink-0 cursor-pointer shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Workflow State Guidance Banner */}
      <StateBanner
        currentPhase="Independent Verification Engine"
        nextAction="5-Criteria Scoring & Cryptographic PASS/FAIL"
        description="Worker AI outputs are evaluated by specialized verifiers (V ≠ W enforced) on Accuracy (30%), Completeness (25%), Quality (20%), Format (15%), and Evidence (10%)."
        nextButtonText={pendingSubmissions.length > 0 ? `Verify Next Item (${pendingSubmissions.length} Pending)` : undefined}
        onNextClick={
          pendingSubmissions.length > 0
            ? () => handleStartAndRun(pendingSubmissions[0].id)
            : undefined
        }
      />

      {/* View Switcher Tabs */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveView('queue')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all cursor-pointer ${
              activeView === 'queue'
                ? 'bg-[#172554] text-white shadow-sm'
                : 'bg-white text-[#596273] hover:text-[#18202F] border border-slate-200 hover:bg-slate-50'
            }`}
          >
            <FileCheck className="w-4 h-4" />
            <span>Pending Queue</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-mono ${
              activeView === 'queue' ? 'bg-white/20 text-white font-bold' : 'bg-slate-100 text-[#3155D9]'
            }`}>
              {pendingSubmissions.length}
            </span>
          </button>

          <button
            onClick={() => setActiveView('history')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all cursor-pointer ${
              activeView === 'history'
                ? 'bg-[#172554] text-white shadow-sm'
                : 'bg-white text-[#596273] hover:text-[#18202F] border border-slate-200 hover:bg-slate-50'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Verification Dossiers</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-mono ${
              activeView === 'history' ? 'bg-white/20 text-white font-bold' : 'bg-slate-100 text-[#596273]'
            }`}>
              {verifications.length}
            </span>
          </button>
        </div>

        <div className="hidden sm:flex items-center gap-4 text-xs font-mono text-[#596273]">
          <span className="flex items-center gap-1.5"><Lock className="w-3.5 h-3.5 text-emerald-700" /> Verifier Independence</span>
          <span className="flex items-center gap-1.5"><Hash className="w-3.5 h-3.5 text-[#3155D9]" /> SHA-256 Hashing</span>
        </div>
      </div>

      {/* VIEW 1: Pending Queue */}
      {activeView === 'queue' && (
        <div className="space-y-4">
          {pendingSubmissions.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pendingSubmissions.map((sub) => (
                <div
                  key={sub.id}
                  className="bg-white border border-slate-200 hover:border-blue-300 rounded-2xl p-5 space-y-4 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-[#6D5BD0] px-2.5 py-1 rounded-lg bg-purple-50 border border-purple-200">
                        {sub.submission_code || `RS-${sub.id}`}
                      </span>
                      <span className="text-[11px] font-mono text-[#596273]">
                        Task #{sub.task_id} · Worker #{sub.agent_id}
                      </span>
                    </div>

                    <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Locked & Ready
                    </span>
                  </div>

                  {sub.result_summary && (
                    <p className="text-xs text-[#334155] line-clamp-2 italic bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                      "{sub.result_summary}"
                    </p>
                  )}

                  <div className="text-[11px] font-mono text-[#596273] space-y-1">
                    {sub.integrity_hash && (
                      <div className="truncate flex items-center gap-1" title={sub.integrity_hash}>
                        <Hash className="w-3 h-3 text-[#3155D9] shrink-0" />
                        <span className="text-[#87909F]">Hash:</span> {sub.integrity_hash.slice(0, 26)}...
                      </div>
                    )}
                    <div className="flex items-center justify-between pt-1">
                      <span>Submitted: {sub.submitted_at ? new Date(sub.submitted_at).toLocaleTimeString() : 'Recent'}</span>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-200 flex items-center justify-between gap-3">
                    <button
                      onClick={() => {
                        if (onSelectSubmission) {
                          onSelectSubmission(sub.id);
                          onNavigate('submission-details');
                        }
                      }}
                      className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-[#18202F] text-xs font-semibold flex items-center gap-1.5 transition border border-slate-200 cursor-pointer"
                    >
                      <Layers className="w-3.5 h-3.5 text-[#6D5BD0]" />
                      <span>Inspect Submission</span>
                    </button>

                    <button
                      onClick={() => handleStartAndRun(sub.id)}
                      disabled={processingId === sub.id}
                      className="px-4 py-1.5 rounded-xl bg-[#172554] hover:bg-[#1E3A8A] text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition disabled:opacity-50 cursor-pointer"
                    >
                      {processingId === sub.id ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Auditing...</span>
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-3.5 h-3.5 text-blue-300" />
                          <span>Run Verifier Audit</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="glass-panel p-12 rounded-3xl border border-slate-200 text-center space-y-3">
              <CheckCircle2 className="w-12 h-12 text-emerald-700 mx-auto" />
              <h3 className="text-base font-bold text-[#18202F]">Verification Queue Clear</h3>
              <p className="text-xs text-[#596273] max-w-md mx-auto">
                No submitted work packages are currently awaiting verification. Tasks completed and submitted by worker agents will automatically appear here.
              </p>
            </div>
          )}
        </div>
      )}

      {/* VIEW 2: Historical Verifications */}
      {activeView === 'history' && (
        <div className="space-y-4">
          {verifications.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {verifications.map((verif) => (
                <div
                  key={verif.id}
                  className="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl p-5 space-y-4 transition"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-[#3155D9] px-2.5 py-1 rounded-lg bg-blue-50 border border-blue-200">
                        {verif.verification_code || `VR-${1000 + verif.id}`}
                      </span>
                      <span className="text-[11px] font-mono text-[#596273]">
                        Task #{verif.task_id}
                      </span>
                    </div>
                    {getDecisionBadge(verif.decision)}
                  </div>

                  {/* Score Gauge */}
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-[#596273] tracking-wider block">
                        Evaluation Score
                      </span>
                      <span className="text-xl font-black text-[#172554]">
                        {verif.overall_score.toFixed(1)}%
                      </span>
                      <span className="text-[11px] text-[#596273] ml-1.5">
                        (Req: {verif.required_score.toFixed(0)}%)
                      </span>
                    </div>

                    <div className="text-right text-[11px] font-mono space-y-0.5">
                      <div className="text-[#596273]">Worker: <strong className="text-[#18202F]">#{verif.worker_agent_id}</strong></div>
                      <div className="text-[#596273]">Verifier: <strong className="text-violet-300">#{verif.verifier_agent_id}</strong></div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                    <span className="text-[10px] font-mono text-[#596273]">
                      {verif.completed_at ? new Date(verif.completed_at).toLocaleString() : 'Pending'}
                    </span>

                    <button
                      onClick={() => {
                        if (onSelectVerification) {
                          onSelectVerification(verif.id);
                          onNavigate('verification-details');
                        }
                      }}
                      className="px-3.5 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-50 text-[#3155D9] border border-blue-200 text-xs font-semibold flex items-center gap-1.5 transition"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect Dossier</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="glass-panel p-12 rounded-3xl border border-slate-200 text-center space-y-3">
              <History className="w-12 h-12 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-[#18202F]">No Verification Dossiers Yet</h3>
              <p className="text-xs text-[#596273] max-w-md mx-auto">
                Completed independent verifications will be logged here with complete 5-criteria score breakdowns and cryptographic audit logs.
              </p>
            </div>
          )}
        </div>
      )}

      {/* 5-Criteria Framework Explanation Card */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200 space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-[#18202F] flex items-center gap-2">
            <DepthIcon icon={<Sliders className="w-4 h-4 text-[#3155D9]" />} color="cyan" size="sm" />
            <span>The 5 Explainable Verification Dimensions</span>
          </h3>
          <span className="text-xs font-mono text-[#3155D9] bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
            Total: 100% Weight
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 text-xs">
          <Interactive3DCard level="interactive" glowColor="cyan" className="p-4 rounded-xl space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#18202F]">Accuracy</span>
              <span className="font-mono text-[#3155D9] font-bold">30%</span>
            </div>
            <p className="text-[11px] text-[#596273] leading-relaxed">Relevance to task objective and domain analytical alignment.</p>
          </Interactive3DCard>

          <Interactive3DCard level="interactive" glowColor="indigo" className="p-4 rounded-xl space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#18202F]">Completeness</span>
              <span className="font-mono text-[#172554] font-bold">25%</span>
            </div>
            <p className="text-[11px] text-[#596273] leading-relaxed">Structured sections, executive summary, and insights populated.</p>
          </Interactive3DCard>

          <Interactive3DCard level="interactive" glowColor="purple" className="p-4 rounded-xl space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#18202F]">Quality</span>
              <span className="font-mono text-[#6D5BD0] font-bold">20%</span>
            </div>
            <p className="text-[11px] text-[#596273] leading-relaxed">Substantial depth, absence of placeholders or raw template marks.</p>
          </Interactive3DCard>

          <Interactive3DCard level="interactive" glowColor="blue" className="p-4 rounded-xl space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#18202F]">Format</span>
              <span className="font-mono text-blue-300 font-bold">15%</span>
            </div>
            <p className="text-[11px] text-[#596273] leading-relaxed">Valid JSON schema compliance and structural integrity.</p>
          </Interactive3DCard>

          <Interactive3DCard level="interactive" glowColor="emerald" className="p-4 rounded-xl space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#18202F]">Evidence</span>
              <span className="font-mono text-emerald-800 font-bold">10%</span>
            </div>
            <p className="text-[11px] text-[#596273] leading-relaxed">Provenance transparency and truthful dataset disclosure.</p>
          </Interactive3DCard>
        </div>
      </div>
    </div>
  );
};

