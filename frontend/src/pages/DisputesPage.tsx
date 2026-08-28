import React, { useState, useEffect, useCallback } from 'react';
import {
  Gavel, Clock, CheckCircle2, XCircle, AlertCircle, RefreshCw,
  ChevronRight, User, Shield, FileText, Hash,
  Activity, Filter, Eye, Play, Check, X, ClipboardList,
  AlertTriangle, PlusCircle, ShieldAlert, FilePlus2, Send,
  Lock, ArrowRight, CornerDownRight, CheckSquare, Sparkles, Scale
} from 'lucide-react';
import {
  HumanReview, HumanReviewAuditLog,
  fetchHumanReviews, fetchHumanReview, fetchHumanReviewAudit,
  startHumanReview, resolveHumanReview,
  Dispute, DisputeEvidence, DisputeAuditLog,
  fetchDisputes, fetchDispute, fetchDisputeAudit, fetchDisputeEvidence,
  createDispute, addDisputeEvidence, markDisputeReady, cancelDispute
} from '../services/api';
import { NavTab } from '../components/Navbar';

interface DisputesPageProps {
  onNavigate: (tab: NavTab) => void;
}

const HR_STATUS_OPTIONS = ['all', 'pending', 'in_review', 'approved', 'rejected', 'resolved'];
const DP_STATUS_OPTIONS = ['all', 'open', 'evidence_pending', 'ready_for_arbitration', 'under_arbitration', 'resolved', 'rejected', 'cancelled'];

const DISPUTE_REASONS = [
  { id: 'unfair_verification', label: 'Unfair / Inaccurate Verification' },
  { id: 'rubric_misinterpretation', label: 'Rubric Misinterpretation by Verifier' },
  { id: 'evidence_ignored', label: 'Valid Output Evidence Ignored' },
  { id: 'technical_error', label: 'Platform / Technical Submission Glitch' },
  { id: 'other', label: 'Other Outcome Disagreement' }
];

const hrStatusStyle: Record<string, string> = {
  pending:   'bg-yellow-50 text-yellow-800 border-yellow-300',
  in_review: 'bg-blue-50 text-blue-800 border-blue-300',
  approved:  'bg-emerald-50 text-emerald-800 border-emerald-300',
  rejected:  'bg-rose-50 text-rose-800 border-rose-300',
  resolved:  'bg-slate-100 text-slate-600 border-slate-300',
};

const dpStatusStyle: Record<string, string> = {
  open:                  'bg-amber-50 text-amber-800 border-amber-300',
  evidence_pending:      'bg-blue-50 text-blue-800 border-blue-300',
  ready_for_arbitration: 'bg-purple-50 text-purple-800 border-purple-300',
  under_arbitration:     'bg-indigo-50 text-indigo-800 border-indigo-300',
  resolved:              'bg-emerald-50 text-emerald-800 border-emerald-300',
  rejected:              'bg-rose-50 text-rose-800 border-rose-300',
  cancelled:             'bg-slate-100 text-slate-600 border-slate-300',
};

function StatusPill({ status, type = 'hr' }: { status: string; type?: 'hr' | 'dp' }) {
  const styles = type === 'hr' ? hrStatusStyle : dpStatusStyle;
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles[status] || 'bg-slate-100 text-slate-600 border-slate-200'}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
    </span>
  );
}

export function DisputesPage({ onNavigate }: DisputesPageProps) {
  const [activeSubTab, setActiveSubTab] = useState<'disputes' | 'human_review'>('disputes');

  // ── Phase 15 Dispute Center State ──────────────────────────────────────────
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [dpStatusFilter, setDpStatusFilter] = useState('all');
  const [dpLoading, setDpLoading] = useState(true);
  const [dpError, setDpError] = useState<string | null>(null);

  const [selectedDispute, setSelectedDispute] = useState<Dispute | null>(null);
  const [disputeEvidence, setDisputeEvidence] = useState<DisputeEvidence[]>([]);
  const [disputeAudit, setDisputeAudit] = useState<DisputeAuditLog[]>([]);
  const [dpDetailLoading, setDpDetailLoading] = useState(false);

  // Modals & Action Forms
  const [showRaiseModal, setShowRaiseModal] = useState(false);
  const [raiseTaskId, setRaiseTaskId] = useState('');
  const [raiseReason, setRaiseReason] = useState('unfair_verification');
  const [raiseDescription, setRaiseDescription] = useState('');
  const [raiseEvidenceTitle, setRaiseEvidenceTitle] = useState('');
  const [raiseEvidenceDesc, setRaiseEvidenceDesc] = useState('');
  const [raiseLoading, setRaiseLoading] = useState(false);
  const [raiseError, setRaiseError] = useState<string | null>(null);

  const [showAddEvidenceModal, setShowAddEvidenceModal] = useState(false);
  const [newEvidenceTitle, setNewEvidenceTitle] = useState('');
  const [newEvidenceDesc, setNewEvidenceDesc] = useState('');
  const [newEvidenceData, setNewEvidenceData] = useState('');
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);

  const [dpActionLoading, setDpActionLoading] = useState(false);
  const [dpActionMsg, setDpActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // ── Phase 14 Human Review State ────────────────────────────────────────────
  const [hrReviews, setHrReviews] = useState<HumanReview[]>([]);
  const [hrStatusFilter, setHrStatusFilter] = useState('all');
  const [hrLoading, setHrLoading] = useState(true);
  const [hrError, setHrError] = useState<string | null>(null);
  const [selectedHr, setSelectedHr] = useState<HumanReview | null>(null);
  const [hrAuditLogs, setHrAuditLogs] = useState<HumanReviewAuditLog[]>([]);
  const [hrAuditLoading, setHrAuditLoading] = useState(false);
  const [resolveNote, setResolveNote] = useState('');
  const [hrActionLoading, setHrActionLoading] = useState(false);
  const [hrActionMsg, setHrActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // ── Loaders ────────────────────────────────────────────────────────────────
  const loadDisputes = useCallback(async () => {
    setDpLoading(true);
    setDpError(null);
    try {
      const data = await fetchDisputes(dpStatusFilter === 'all' ? undefined : dpStatusFilter);
      setDisputes(data);
    } catch (e: unknown) {
      setDpError(e instanceof Error ? e.message : 'Failed to load disputes');
    } finally {
      setDpLoading(false);
    }
  }, [dpStatusFilter]);

  const loadHumanReviews = useCallback(async () => {
    setHrLoading(true);
    setHrError(null);
    try {
      const data = await fetchHumanReviews(hrStatusFilter === 'all' ? undefined : hrStatusFilter);
      setHrReviews(data);
    } catch (e: unknown) {
      setHrError(e instanceof Error ? e.message : 'Failed to load human reviews');
    } finally {
      setHrLoading(false);
    }
  }, [hrStatusFilter]);

  useEffect(() => {
    if (activeSubTab === 'disputes') {
      loadDisputes();
    } else {
      loadHumanReviews();
    }
  }, [activeSubTab, loadDisputes, loadHumanReviews]);

  // ── Dispute Handlers ───────────────────────────────────────────────────────
  const openDisputeDetail = async (disp: Dispute) => {
    setSelectedDispute(disp);
    setDpActionMsg(null);
    setDpDetailLoading(true);
    try {
      const [evList, audList] = await Promise.all([
        fetchDisputeEvidence(disp.id).catch(() => []),
        fetchDisputeAudit(disp.id).catch(() => [])
      ]);
      setDisputeEvidence(evList);
      setDisputeAudit(audList);
    } finally {
      setDpDetailLoading(false);
    }
  };

  const refreshSelectedDispute = async (id: number) => {
    try {
      const fresh = await fetchDispute(id);
      setSelectedDispute(fresh);
      setDisputes(prev => prev.map(d => d.id === id ? fresh : d));
      const [evList, audList] = await Promise.all([
        fetchDisputeEvidence(id).catch(() => []),
        fetchDisputeAudit(id).catch(() => [])
      ]);
      setDisputeEvidence(evList);
      setDisputeAudit(audList);
    } catch { /* silent */ }
  };

  const handleRaiseDispute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!raiseTaskId || !raiseDescription.trim()) {
      setRaiseError('Task ID and Description are required.');
      return;
    }
    setRaiseLoading(true);
    setRaiseError(null);
    try {
      const created = await createDispute({
        task_id: parseInt(raiseTaskId, 10),
        reason: raiseReason,
        description: raiseDescription,
        raised_by_type: 'worker',
        initial_evidence_title: raiseEvidenceTitle.trim() || undefined,
        initial_evidence_description: raiseEvidenceDesc.trim() || undefined,
      });
      setShowRaiseModal(false);
      setRaiseTaskId('');
      setRaiseDescription('');
      setRaiseEvidenceTitle('');
      setRaiseEvidenceDesc('');
      loadDisputes();
      openDisputeDetail(created);
    } catch (err: unknown) {
      setRaiseError(err instanceof Error ? err.message : 'Failed to create dispute');
    } finally {
      setRaiseLoading(false);
    }
  };

  const handleAddEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDispute || !newEvidenceTitle.trim() || !newEvidenceDesc.trim()) {
      setEvidenceError('Title and description are required.');
      return;
    }
    setEvidenceLoading(true);
    setEvidenceError(null);
    try {
      await addDisputeEvidence(selectedDispute.id, {
        title: newEvidenceTitle.trim(),
        description: newEvidenceDesc.trim(),
        evidence_data: newEvidenceData.trim() || undefined,
      });
      setShowAddEvidenceModal(false);
      setNewEvidenceTitle('');
      setNewEvidenceDesc('');
      setNewEvidenceData('');
      await refreshSelectedDispute(selectedDispute.id);
    } catch (err: unknown) {
      setEvidenceError(err instanceof Error ? err.message : 'Failed to add evidence');
    } finally {
      setEvidenceLoading(false);
    }
  };

  const handleMarkReady = async () => {
    if (!selectedDispute) return;
    setDpActionLoading(true);
    setDpActionMsg(null);
    try {
      await markDisputeReady(selectedDispute.id);
      setDpActionMsg({ type: 'success', text: 'Dispute marked Ready for Arbitration (Phase 16).' });
      await refreshSelectedDispute(selectedDispute.id);
      loadDisputes();
    } catch (err: unknown) {
      setDpActionMsg({ type: 'error', text: err instanceof Error ? err.message : 'Failed to update dispute' });
    } finally {
      setDpActionLoading(false);
    }
  };

  const handleCancelDispute = async () => {
    if (!selectedDispute) return;
    if (!confirm('Are you sure you want to cancel this dispute? The task will revert to failed status.')) return;
    setDpActionLoading(true);
    setDpActionMsg(null);
    try {
      await cancelDispute(selectedDispute.id);
      setDpActionMsg({ type: 'success', text: 'Dispute cancelled. Task reverted to failed.' });
      await refreshSelectedDispute(selectedDispute.id);
      loadDisputes();
    } catch (err: unknown) {
      setDpActionMsg({ type: 'error', text: err instanceof Error ? err.message : 'Failed to cancel dispute' });
    } finally {
      setDpActionLoading(false);
    }
  };

  // ── Human Review Handlers ──────────────────────────────────────────────────
  const openHrDetail = async (hr: HumanReview) => {
    setSelectedHr(hr);
    setResolveNote('');
    setHrActionMsg(null);
    setHrAuditLoading(true);
    try {
      const logs = await fetchHumanReviewAudit(hr.id);
      setHrAuditLogs(logs);
    } catch {
      setHrAuditLogs([]);
    } finally {
      setHrAuditLoading(false);
    }
  };

  const handleStartHr = async () => {
    if (!selectedHr) return;
    setHrActionLoading(true);
    setHrActionMsg(null);
    try {
      await startHumanReview(selectedHr.id);
      const fresh = await fetchHumanReview(selectedHr.id);
      setSelectedHr(fresh);
      setHrReviews(prev => prev.map(r => r.id === fresh.id ? fresh : r));
      const logs = await fetchHumanReviewAudit(fresh.id);
      setHrAuditLogs(logs);
      setHrActionMsg({ type: 'success', text: 'Review lock acquired.' });
    } catch (e: unknown) {
      setHrActionMsg({ type: 'error', text: e instanceof Error ? e.message : 'Failed to start review' });
    } finally {
      setHrActionLoading(false);
    }
  };

  const handleResolveHr = async (decision: 'APPROVE' | 'REJECT') => {
    if (!selectedHr) return;
    if (!resolveNote.trim()) {
      setHrActionMsg({ type: 'error', text: 'A justification note is required to resolve.' });
      return;
    }
    setHrActionLoading(true);
    setHrActionMsg(null);
    try {
      await resolveHumanReview(selectedHr.id, { decision, reviewer_note: resolveNote });
      const fresh = await fetchHumanReview(selectedHr.id);
      setSelectedHr(fresh);
      setHrReviews(prev => prev.map(r => r.id === fresh.id ? fresh : r));
      const logs = await fetchHumanReviewAudit(fresh.id);
      setHrAuditLogs(logs);
      setHrActionMsg({ type: 'success', text: `Review ${decision.toLowerCase()}d successfully.` });
      loadHumanReviews();
    } catch (e: unknown) {
      setHrActionMsg({ type: 'error', text: e instanceof Error ? e.message : 'Failed to resolve review' });
    } finally {
      setHrActionLoading(false);
    }
  };

  const isDisputeActive = selectedDispute && ['open', 'evidence_pending', 'ready_for_arbitration', 'under_arbitration'].includes(selectedDispute.status);
  const canMarkReady = selectedDispute && ['open', 'evidence_pending'].includes(selectedDispute.status);
  const canAddEvidence = selectedDispute && ['open', 'evidence_pending', 'ready_for_arbitration'].includes(selectedDispute.status);
  const canCancelDispute = selectedDispute && isDisputeActive;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100/60 to-slate-200/50 px-4 py-8">
      <div className="max-w-7xl mx-auto">

        {/* ── Top Header & Tab Navigation ── */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="p-2.5 rounded-xl bg-indigo-100 border border-indigo-200">
                <Scale className="w-6 h-6 text-indigo-700" />
              </div>
              <div>
                <h1 className="text-2xl font-black text-slate-900 tracking-tight">Dispute & Resolution Center</h1>
                <p className="text-xs text-slate-500">Autonomous economic arbitration and human-in-the-loop review</p>
              </div>
            </div>
          </div>

          {/* Sub-tab switcher */}
          <div className="flex items-center gap-2 bg-white border border-slate-200 p-1 rounded-2xl shadow-sm">
            <button
              onClick={() => setActiveSubTab('disputes')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeSubTab === 'disputes'
                  ? 'bg-amber-500 text-white shadow-md'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <ShieldAlert className="w-4 h-4" />
              <span>Dispute Center (Phase 15)</span>
            </button>
            <button
              onClick={() => setActiveSubTab('human_review')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeSubTab === 'human_review'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <Gavel className="w-4 h-4" />
              <span>Human Review Queue (Phase 14)</span>
            </button>
          </div>
        </div>

        {/* ══════════════════════════════════════════════════════════════════════
            TAB 1: PHASE 15 DISPUTE RESOLUTION CENTER
        ══════════════════════════════════════════════════════════════════════ */}
        {activeSubTab === 'disputes' && (
          <div>
            {/* Quick Action Banner */}
            <div className="mb-4 flex items-center justify-between bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/5 border border-amber-300 rounded-2xl p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-amber-500 text-white shadow-sm">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-amber-950">Outcome Disagreement or Inaccurate Verification?</h4>
                  <p className="text-xs text-amber-800/80">Raising a dispute pauses settlement and prepares the case for Phase 16 AI arbitration.</p>
                </div>
              </div>
              <button
                onClick={() => setShowRaiseModal(true)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold shadow-md transition"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Raise New Dispute</span>
              </button>
            </div>

            {/* Main Dispute Split View */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 h-[calc(100vh-250px)]">

              {/* ── LEFT: Dispute Queue ── */}
              <div className="lg:col-span-2 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                {/* Filter bar */}
                <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100 bg-slate-50">
                  <Filter className="w-4 h-4 text-slate-400 shrink-0" />
                  <div className="flex items-center gap-1.5 overflow-x-auto">
                    {DP_STATUS_OPTIONS.map(s => (
                      <button
                        key={s}
                        onClick={() => { setDpStatusFilter(s); setSelectedDispute(null); }}
                        className={`shrink-0 px-2.5 py-0.5 rounded-full text-xs font-medium transition-all ${
                          dpStatusFilter === s
                            ? 'bg-amber-500 text-white shadow'
                            : 'bg-white text-slate-600 border border-slate-200 hover:border-amber-300'
                        }`}
                      >
                        {s === 'all' ? 'All' : s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={loadDisputes}
                    className="ml-auto shrink-0 p-1.5 rounded-lg hover:bg-slate-100 transition"
                    title="Refresh"
                  >
                    <RefreshCw className={`w-4 h-4 text-slate-400 ${dpLoading ? 'animate-spin' : ''}`} />
                  </button>
                </div>

                {/* Dispute List */}
                <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                  {dpLoading && (
                    <div className="flex items-center justify-center py-16">
                      <RefreshCw className="w-6 h-6 animate-spin text-amber-500" />
                    </div>
                  )}
                  {!dpLoading && dpError && (
                    <div className="p-6 text-center">
                      <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
                      <p className="text-sm text-rose-600">{dpError}</p>
                    </div>
                  )}
                  {!dpLoading && !dpError && disputes.length === 0 && (
                    <div className="p-8 text-center">
                      <ShieldAlert className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                      <p className="text-sm text-slate-500 font-medium">No disputes active</p>
                      <p className="text-xs text-slate-400 mt-1">Disputed failed tasks will be listed here</p>
                    </div>
                  )}
                  {!dpLoading && disputes.map(d => (
                    <button
                      key={d.id}
                      onClick={() => openDisputeDetail(d)}
                      className={`w-full text-left px-4 py-3.5 hover:bg-amber-50/60 transition-all group ${
                        selectedDispute?.id === d.id ? 'bg-amber-50/80 border-l-4 border-l-amber-500' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-mono font-black text-amber-800">{d.dispute_code ?? `DP-${1000 + d.id}`}</span>
                            <StatusPill status={d.status} type="dp" />
                          </div>
                          <p className="text-xs font-semibold text-slate-800 truncate capitalize">{d.reason.replace(/_/g, ' ')}</p>
                          <p className="text-[11px] text-slate-500 truncate mt-0.5">Task #{d.task_id} · Worker #{d.worker_agent_id}</p>
                          <p className="text-[10px] text-slate-400 mt-1 font-mono">{new Date(d.created_at).toLocaleString()}</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-amber-500 shrink-0 mt-1 transition" />
                      </div>
                    </button>
                  ))}
                </div>

                <div className="px-4 py-2 border-t border-slate-100 bg-slate-50">
                  <p className="text-xs text-slate-400">{disputes.length} dispute{disputes.length !== 1 ? 's' : ''} listed</p>
                </div>
              </div>

              {/* ── RIGHT: Dispute Dossier & Evidence ── */}
              <div className="lg:col-span-3 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                {!selectedDispute ? (
                  <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                    <div className="p-4 rounded-full bg-amber-50 border border-amber-100 mb-4">
                      <Scale className="w-10 h-10 text-amber-500" />
                    </div>
                    <p className="text-base font-semibold text-slate-700 mb-1">Select a dispute case</p>
                    <p className="text-sm text-slate-400">Click any dispute on the left to inspect evidence, submit additions, and prepare for arbitration.</p>
                  </div>
                ) : (
                  <>
                    {/* Header */}
                    <div className="px-6 py-3.5 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-amber-100">
                          <ShieldAlert className="w-4 h-4 text-amber-700" />
                        </div>
                        <div>
                          <p className="text-sm font-black text-slate-900 font-mono">{selectedDispute.dispute_code ?? `DP-${1000 + selectedDispute.id}`}</p>
                          <p className="text-xs text-slate-500 capitalize">{selectedDispute.reason.replace(/_/g, ' ')}</p>
                        </div>
                        <StatusPill status={selectedDispute.status} type="dp" />
                      </div>
                      <button
                        onClick={() => refreshSelectedDispute(selectedDispute.id)}
                        className="p-1.5 rounded-lg hover:bg-slate-100 transition"
                        title="Refresh"
                      >
                        <RefreshCw className={`w-4 h-4 text-slate-400 ${dpDetailLoading ? 'animate-spin' : ''}`} />
                      </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-6">

                      {/* Prominent Settlement Paused Banner */}
                      {isDisputeActive && (
                        <div className="flex items-start gap-3 bg-amber-50 border border-amber-300 rounded-xl p-4 shadow-sm">
                          <Lock className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                          <div>
                            <p className="text-xs font-black uppercase tracking-wider text-amber-900">Settlement Paused — Dispute Active</p>
                            <p className="text-xs text-amber-800 mt-0.5 leading-relaxed">
                              AP Credit settlement is strictly frozen in escrow. No funds will be transferred until Phase 16 AI arbitration evaluates this case.
                            </p>
                          </div>
                        </div>
                      )}

                      {dpActionMsg && (
                        <div className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
                          dpActionMsg.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'
                        }`}>
                          {dpActionMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />}
                          <span>{dpActionMsg.text}</span>
                        </div>
                      )}

                      {/* Linked Entities Grid */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        {[
                          { label: 'Task ID', value: `#${selectedDispute.task_id}`, icon: <Hash className="w-3.5 h-3.5" /> },
                          { label: 'Worker Agent', value: `#${selectedDispute.worker_agent_id}`, icon: <User className="w-3.5 h-3.5" /> },
                          { label: 'Escrow ID', value: `#${selectedDispute.escrow_id}`, icon: <Lock className="w-3.5 h-3.5" /> },
                          { label: 'Raised By', value: selectedDispute.raised_by_type.toUpperCase(), icon: <Shield className="w-3.5 h-3.5" /> },
                        ].map(item => (
                          <div key={item.label} className="bg-slate-50 rounded-xl border border-slate-200 p-3">
                            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
                              {item.icon}
                              <span className="text-xs">{item.label}</span>
                            </div>
                            <p className="text-sm font-bold text-slate-800 font-mono">{item.value}</p>
                          </div>
                        ))}
                      </div>

                      {/* Dispute Explanation */}
                      <div className="bg-slate-50 rounded-xl border border-slate-200 p-4">
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Dispute Statement</p>
                        <p className="text-sm text-slate-800 leading-relaxed">{selectedDispute.description}</p>
                      </div>

                      {/* ── Evidence Section (Immutable items) ── */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <FilePlus2 className="w-4 h-4 text-amber-600" />
                            <span>Submitted Evidence ({disputeEvidence.length})</span>
                          </p>
                          {canAddEvidence && (
                            <button
                              onClick={() => setShowAddEvidenceModal(true)}
                              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold transition"
                            >
                              <PlusCircle className="w-3.5 h-3.5" />
                              <span>Add Evidence</span>
                            </button>
                          )}
                        </div>

                        {disputeEvidence.length === 0 ? (
                          <p className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center">
                            No additional evidence attached yet.
                          </p>
                        ) : (
                          <div className="space-y-2.5">
                            {disputeEvidence.map((ev) => (
                              <div key={ev.id} className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-sm space-y-1.5">
                                <div className="flex items-center justify-between gap-2">
                                  <h5 className="text-xs font-bold text-slate-900">{ev.title}</h5>
                                  <span className="text-[10px] font-mono text-slate-400">{new Date(ev.created_at).toLocaleString()}</span>
                                </div>
                                <p className="text-xs text-slate-600 leading-relaxed">{ev.description}</p>
                                {ev.evidence_data && (
                                  <pre className="text-[10px] font-mono bg-slate-900 text-slate-200 p-2.5 rounded-lg overflow-x-auto">
                                    {ev.evidence_data}
                                  </pre>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* ── Action Controls ── */}
                      {isDisputeActive && (
                        <div className="flex flex-wrap gap-3 pt-2 border-t border-slate-100">
                          {canMarkReady && (
                            <button
                              onClick={handleMarkReady}
                              disabled={dpActionLoading}
                              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow transition disabled:opacity-50"
                            >
                              <Sparkles className="w-4 h-4" />
                              <span>Mark Ready for Arbitration</span>
                            </button>
                          )}
                          {canCancelDispute && (
                            <button
                              onClick={handleCancelDispute}
                              disabled={dpActionLoading}
                              className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold border border-slate-200 transition disabled:opacity-50"
                            >
                              <X className="w-4 h-4" />
                              <span>Withdraw Dispute</span>
                            </button>
                          )}
                        </div>
                      )}

                      {/* ── Audit Timeline ── */}
                      <div className="space-y-3 pt-2 border-t border-slate-100">
                        <p className="text-sm font-bold text-slate-800 flex items-center gap-2">
                          <ClipboardList className="w-4 h-4 text-slate-500" />
                          <span>Dispute Audit History</span>
                        </p>
                        <ol className="relative border-l border-slate-200 ml-2 space-y-3">
                          {disputeAudit.map((log) => (
                            <li key={log.id} className="ml-4">
                              <div className="absolute -left-1.5 w-3 h-3 rounded-full bg-amber-500 border-2 border-white mt-0.5" />
                              <p className="text-[10px] text-slate-400 font-mono">{new Date(log.created_at).toLocaleString()}</p>
                              <p className="text-xs font-semibold text-slate-700 capitalize mt-0.5">{log.action.replace(/_/g, ' ')}</p>
                              {log.message && <p className="text-xs text-slate-500 mt-0.5">{log.message}</p>}
                            </li>
                          ))}
                        </ol>
                      </div>

                    </div>
                  </>
                )}
              </div>

            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════════
            TAB 2: PHASE 14 HUMAN REVIEW QUEUE
        ══════════════════════════════════════════════════════════════════════ */}
        {activeSubTab === 'human_review' && (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 h-[calc(100vh-200px)]">
            {/* Left Queue */}
            <div className="lg:col-span-2 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100 bg-slate-50">
                <Filter className="w-4 h-4 text-slate-400 shrink-0" />
                <div className="flex items-center gap-1.5 overflow-x-auto">
                  {HR_STATUS_OPTIONS.map(s => (
                    <button
                      key={s}
                      onClick={() => { setHrStatusFilter(s); setSelectedHr(null); }}
                      className={`shrink-0 px-2.5 py-0.5 rounded-full text-xs font-medium transition-all ${
                        hrStatusFilter === s
                          ? 'bg-indigo-600 text-white shadow'
                          : 'bg-white text-slate-600 border border-slate-200 hover:border-indigo-300'
                      }`}
                    >
                      {s === 'all' ? 'All' : s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </button>
                  ))}
                </div>
                <button
                  onClick={loadHumanReviews}
                  className="ml-auto shrink-0 p-1.5 rounded-lg hover:bg-slate-100 transition"
                  title="Refresh"
                >
                  <RefreshCw className={`w-4 h-4 text-slate-400 ${hrLoading ? 'animate-spin' : ''}`} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                {hrLoading && (
                  <div className="flex items-center justify-center py-16">
                    <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
                  </div>
                )}
                {!hrLoading && hrError && (
                  <div className="p-6 text-center">
                    <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
                    <p className="text-sm text-rose-600">{hrError}</p>
                  </div>
                )}
                {!hrLoading && hrReviews.map(r => (
                  <button
                    key={r.id}
                    onClick={() => openHrDetail(r)}
                    className={`w-full text-left px-4 py-3 hover:bg-indigo-50/60 transition-all group ${
                      selectedHr?.id === r.id ? 'bg-indigo-50 border-l-4 border-l-indigo-600' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-mono font-bold text-indigo-700">{r.review_code ?? `HR-${1000 + r.id}`}</span>
                          <StatusPill status={r.status} type="hr" />
                        </div>
                        <p className="text-xs text-slate-500 truncate">Task #{r.task_id} · Sub #{r.submission_id} · Worker #{r.worker_agent_id}</p>
                        <p className="text-[10px] text-slate-400 mt-0.5">{new Date(r.created_at).toLocaleString()}</p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-indigo-400 shrink-0 mt-1 transition" />
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Right Review Detail */}
            <div className="lg:col-span-3 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              {!selectedHr ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                  <Gavel className="w-10 h-10 text-indigo-400 mb-3" />
                  <p className="text-base font-semibold text-slate-700">Select a review from the queue</p>
                </div>
              ) : (
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-slate-900 font-mono">{selectedHr.review_code ?? `HR-${1000 + selectedHr.id}`}</p>
                      <p className="text-xs text-slate-500">Task #{selectedHr.task_id} · Worker #{selectedHr.worker_agent_id}</p>
                    </div>
                    <StatusPill status={selectedHr.status} type="hr" />
                  </div>

                  {hrActionMsg && (
                    <div className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
                      hrActionMsg.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'
                    }`}>
                      {hrActionMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />}
                      <span>{hrActionMsg.text}</span>
                    </div>
                  )}

                  {selectedHr.status === 'pending' && (
                    <button
                      onClick={handleStartHr}
                      disabled={hrActionLoading}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition disabled:opacity-50"
                    >
                      <Play className="w-4 h-4" />
                      <span>Start Review / Acquire Lock</span>
                    </button>
                  )}

                  {selectedHr.status === 'in_review' && (
                    <div className="space-y-3 bg-indigo-50/40 p-4 rounded-xl border border-indigo-100">
                      <label className="text-xs font-bold text-slate-700 block">Reviewer Decision Justification *</label>
                      <textarea
                        value={resolveNote}
                        onChange={e => setResolveNote(e.target.value)}
                        rows={3}
                        placeholder="Provide detailed justification note..."
                        className="w-full text-xs border border-slate-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
                      />
                      <div className="flex gap-3">
                        <button
                          onClick={() => handleResolveHr('APPROVE')}
                          disabled={hrActionLoading}
                          className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow transition disabled:opacity-50"
                        >
                          <Check className="w-4 h-4" />
                          <span>Approve & Release Escrow</span>
                        </button>
                        <button
                          onClick={() => handleResolveHr('REJECT')}
                          disabled={hrActionLoading}
                          className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow transition disabled:opacity-50"
                        >
                          <X className="w-4 h-4" />
                          <span>Reject & Fail Task</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Audit Logs */}
                  <div className="space-y-3 pt-4 border-t border-slate-100">
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Review Audit Trail</p>
                    <ol className="relative border-l border-slate-200 ml-2 space-y-3">
                      {hrAuditLogs.map(log => (
                        <li key={log.id} className="ml-4">
                          <div className="absolute -left-1.5 w-3 h-3 rounded-full bg-indigo-500 border-2 border-white mt-0.5" />
                          <p className="text-[10px] text-slate-400 font-mono">{new Date(log.created_at).toLocaleString()}</p>
                          <p className="text-xs font-semibold text-slate-700 capitalize mt-0.5">{log.action.replace(/_/g, ' ')}</p>
                          {log.message && <p className="text-xs text-slate-500 mt-0.5">{log.message}</p>}
                        </li>
                      ))}
                    </ol>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

      </div>

      {/* ── MODAL: Raise New Dispute ── */}
      {showRaiseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <span>Raise Dispute for Failed Outcome</span>
              </h3>
              <button onClick={() => setShowRaiseModal(false)} className="p-1 rounded-lg hover:bg-slate-100 text-slate-400">
                <X className="w-4 h-4" />
              </button>
            </div>

            {raiseError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{raiseError}</span>
              </div>
            )}

            <form onSubmit={handleRaiseDispute} className="space-y-3.5">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Task ID *</label>
                <input
                  type="number"
                  value={raiseTaskId}
                  onChange={e => setRaiseTaskId(e.target.value)}
                  placeholder="e.g. 1"
                  required
                  className="w-full text-xs border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Dispute Reason Category *</label>
                <select
                  value={raiseReason}
                  onChange={e => setRaiseReason(e.target.value)}
                  className="w-full text-xs border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white"
                >
                  {DISPUTE_REASONS.map(r => (
                    <option key={r.id} value={r.id}>{r.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Dispute Explanation & Argument *</label>
                <textarea
                  value={raiseDescription}
                  onChange={e => setRaiseDescription(e.target.value)}
                  rows={3}
                  placeholder="Explain why the failed verification or rejected review is incorrect..."
                  required
                  className="w-full text-xs border border-slate-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <p className="text-xs font-bold text-slate-700">Initial Supporting Evidence (Optional)</p>
                <input
                  type="text"
                  value={raiseEvidenceTitle}
                  onChange={e => setRaiseEvidenceTitle(e.target.value)}
                  placeholder="Evidence Title (e.g. Supplementary Benchmark Log)"
                  className="w-full text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-white"
                />
                <textarea
                  value={raiseEvidenceDesc}
                  onChange={e => setRaiseEvidenceDesc(e.target.value)}
                  rows={2}
                  placeholder="Evidence Description..."
                  className="w-full text-xs border border-slate-200 rounded-lg p-2 bg-white"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRaiseModal(false)}
                  className="flex-1 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={raiseLoading}
                  className="flex-1 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold shadow disabled:opacity-50"
                >
                  {raiseLoading ? 'Submitting...' : 'Submit Dispute'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: Add Evidence ── */}
      {showAddEvidenceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FilePlus2 className="w-5 h-5 text-amber-500" />
                <span>Append Immutable Evidence</span>
              </h3>
              <button onClick={() => setShowAddEvidenceModal(false)} className="p-1 rounded-lg hover:bg-slate-100 text-slate-400">
                <X className="w-4 h-4" />
              </button>
            </div>

            {evidenceError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{evidenceError}</span>
              </div>
            )}

            <form onSubmit={handleAddEvidence} className="space-y-3.5">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Evidence Title *</label>
                <input
                  type="text"
                  value={newEvidenceTitle}
                  onChange={e => setNewEvidenceTitle(e.target.value)}
                  placeholder="e.g. Model Output Raw JSON"
                  required
                  className="w-full text-xs border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Description & Argument *</label>
                <textarea
                  value={newEvidenceDesc}
                  onChange={e => setNewEvidenceDesc(e.target.value)}
                  rows={3}
                  placeholder="Explain why this evidence supports your dispute..."
                  required
                  className="w-full text-xs border border-slate-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Structured JSON / Log Snippet (Optional)</label>
                <textarea
                  value={newEvidenceData}
                  onChange={e => setNewEvidenceData(e.target.value)}
                  rows={3}
                  placeholder='{"accuracy_delta": "+15%", "verified_timestamp": "2026-08-28"}'
                  className="w-full text-xs font-mono border border-slate-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-amber-400 bg-slate-50"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddEvidenceModal(false)}
                  className="flex-1 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={evidenceLoading}
                  className="flex-1 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold shadow disabled:opacity-50"
                >
                  {evidenceLoading ? 'Appending...' : 'Attach Evidence'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}

export default DisputesPage;
