import React, { useState, useEffect, useCallback } from 'react';
import {
  Gavel, Clock, CheckCircle2, XCircle, AlertCircle, RefreshCw,
  ChevronRight, User, Shield, FileText, Hash, ChevronsUpDown,
  Activity, Filter, Eye, Play, Check, X, ChevronDown, ClipboardList
} from 'lucide-react';
import {
  HumanReview, HumanReviewAuditLog,
  fetchHumanReviews, fetchHumanReview, fetchHumanReviewAudit,
  startHumanReview, resolveHumanReview
} from '../services/api';

import { NavTab } from '../components/Navbar';

interface DisputesPageProps {
  onNavigate: (tab: NavTab) => void;
}

const STATUS_OPTIONS = ['all', 'pending', 'in_review', 'approved', 'rejected', 'resolved'];

const statusStyle: Record<string, string> = {
  pending:   'bg-yellow-50 text-yellow-800 border-yellow-300',
  in_review: 'bg-blue-50 text-blue-800 border-blue-300',
  approved:  'bg-emerald-50 text-emerald-800 border-emerald-300',
  rejected:  'bg-rose-50 text-rose-800 border-rose-300',
  resolved:  'bg-slate-100 text-slate-600 border-slate-300',
};

const statusIcon: Record<string, React.ReactNode> = {
  pending:   <Clock className="w-3.5 h-3.5" />,
  in_review: <Eye className="w-3.5 h-3.5 animate-pulse" />,
  approved:  <CheckCircle2 className="w-3.5 h-3.5" />,
  rejected:  <XCircle className="w-3.5 h-3.5" />,
  resolved:  <CheckCircle2 className="w-3.5 h-3.5" />,
};

function StatusPill({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${statusStyle[status] || 'bg-slate-100 text-slate-600 border-slate-200'}`}>
      {statusIcon[status] ?? <AlertCircle className="w-3.5 h-3.5" />}
      {status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
    </span>
  );
}

function AuditTimeline({ logs }: { logs: HumanReviewAuditLog[] }) {
  if (!logs.length) {
    return <p className="text-sm text-slate-500 italic text-center py-4">No audit events yet.</p>;
  }
  return (
    <ol className="relative border-l border-slate-200 ml-2 space-y-4">
      {logs.map((log, i) => (
        <li key={i} className="ml-4">
          <div className="absolute -left-1.5 w-3 h-3 rounded-full bg-blue-400 border-2 border-white mt-0.5" />
          <p className="text-xs text-slate-400 font-mono">{new Date(log.created_at).toLocaleString()}</p>
          <p className="text-xs font-semibold text-slate-700 capitalize mt-0.5">{log.action.replace(/_/g, ' ')}</p>
          {log.message && <p className="text-xs text-slate-500 mt-0.5">{log.message}</p>}
        </li>
      ))}
    </ol>
  );
}

export function DisputesPage({ onNavigate }: DisputesPageProps) {
  const [reviews, setReviews] = useState<HumanReview[]>([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selected, setSelected] = useState<HumanReview | null>(null);
  const [auditLogs, setAuditLogs] = useState<HumanReviewAuditLog[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const [resolveNote, setResolveNote] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadReviews = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHumanReviews(statusFilter === 'all' ? undefined : statusFilter);
      setReviews(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load reviews');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { loadReviews(); }, [loadReviews]);

  const openDetail = async (review: HumanReview) => {
    setSelected(review);
    setResolveNote('');
    setActionError(null);
    setActionSuccess(null);
    setAuditLogs([]);
    setAuditLoading(true);
    try {
      const logs = await fetchHumanReviewAudit(review.id);
      setAuditLogs(logs);
    } catch {
      setAuditLogs([]);
    } finally {
      setAuditLoading(false);
    }
  };

  const refreshSelected = async (id: number) => {
    try {
      const fresh = await fetchHumanReview(id);
      setSelected(fresh);
      setReviews(prev => prev.map(r => r.id === id ? fresh : r));
      const logs = await fetchHumanReviewAudit(id);
      setAuditLogs(logs);
    } catch { /* silent */ }
  };

  const handleStart = async () => {
    if (!selected) return;
    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      await startHumanReview(selected.id);
      setActionSuccess('Review started successfully.');
      await refreshSelected(selected.id);
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : 'Failed to start review');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async (decision: 'APPROVE' | 'REJECT') => {
    if (!selected) return;
    if (!resolveNote.trim()) {
      setActionError('A reviewer note is required to resolve.');
      return;
    }
    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      await resolveHumanReview(selected.id, { decision, reviewer_note: resolveNote });
      setActionSuccess(`Review ${decision === 'APPROVE' ? 'approved' : 'rejected'} successfully.`);
      await refreshSelected(selected.id);
      loadReviews();
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : 'Failed to resolve review');
    } finally {
      setActionLoading(false);
    }
  };

  const canStart    = selected?.status === 'pending';
  const canResolve  = selected?.status === 'in_review';
  const isResolved  = ['approved', 'rejected', 'resolved'].includes(selected?.status ?? '');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-amber-50/20 to-slate-100 px-4 py-8">
      <div className="max-w-7xl mx-auto">

        {/* ── Header ── */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-xl bg-amber-100 border border-amber-200">
              <Gavel className="w-6 h-6 text-amber-700" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Human Review</h1>
              <p className="text-sm text-slate-500">HITL arbitration for borderline verification outcomes</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 h-[calc(100vh-200px)]">

          {/* ── LEFT: Queue ── */}
          <div className="lg:col-span-2 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            {/* Filter bar */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100 bg-slate-50">
              <Filter className="w-4 h-4 text-slate-400 shrink-0" />
              <div className="flex items-center gap-1.5 overflow-x-auto">
                {STATUS_OPTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => { setStatusFilter(s); setSelected(null); }}
                    className={`shrink-0 px-2.5 py-0.5 rounded-full text-xs font-medium transition-all ${
                      statusFilter === s
                        ? 'bg-amber-500 text-white shadow'
                        : 'bg-white text-slate-600 border border-slate-200 hover:border-amber-300'
                    }`}
                  >
                    {s === 'all' ? 'All' : s.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </button>
                ))}
              </div>
              <button
                onClick={loadReviews}
                className="ml-auto shrink-0 p-1.5 rounded-lg hover:bg-slate-100 transition"
                title="Refresh"
              >
                <RefreshCw className={`w-4 h-4 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {/* Queue list */}
            <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
              {loading && (
                <div className="flex items-center justify-center py-16">
                  <RefreshCw className="w-6 h-6 animate-spin text-amber-500" />
                </div>
              )}
              {!loading && error && (
                <div className="p-6 text-center">
                  <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
                  <p className="text-sm text-rose-600">{error}</p>
                </div>
              )}
              {!loading && !error && reviews.length === 0 && (
                <div className="p-8 text-center">
                  <ClipboardList className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                  <p className="text-sm text-slate-500 font-medium">No reviews found</p>
                  <p className="text-xs text-slate-400 mt-1">Borderline verifications will appear here</p>
                </div>
              )}
              {!loading && reviews.map(r => (
                <button
                  key={r.id}
                  onClick={() => openDetail(r)}
                  className={`w-full text-left px-4 py-3 hover:bg-amber-50/60 transition-all group ${
                    selected?.id === r.id ? 'bg-amber-50 border-l-4 border-l-amber-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono font-bold text-amber-700">{r.review_code ?? `HR-${1000 + r.id}`}</span>
                        <StatusPill status={r.status} />
                      </div>
                      <p className="text-xs text-slate-500 truncate">Task #{r.task_id} · Sub #{r.submission_id} · Worker #{r.worker_agent_id}</p>
                      <p className="text-xs text-slate-400 mt-0.5">{new Date(r.created_at).toLocaleString()}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-amber-400 shrink-0 mt-1 transition" />
                  </div>
                </button>
              ))}
            </div>

            {/* Footer count */}
            <div className="px-4 py-2 border-t border-slate-100 bg-slate-50">
              <p className="text-xs text-slate-400">{reviews.length} review{reviews.length !== 1 ? 's' : ''} shown</p>
            </div>
          </div>

          {/* ── RIGHT: Detail Pane ── */}
          <div className="lg:col-span-3 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            {!selected ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                <div className="p-4 rounded-full bg-amber-50 border border-amber-100 mb-4">
                  <Gavel className="w-10 h-10 text-amber-400" />
                </div>
                <p className="text-base font-semibold text-slate-700 mb-1">Select a review to inspect</p>
                <p className="text-sm text-slate-400">Click any item in the queue to see details, verifier scores, and take action.</p>
              </div>
            ) : (
              <>
                {/* Detail header */}
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-amber-100">
                      <Gavel className="w-4 h-4 text-amber-700" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-800 font-mono">{selected.review_code ?? `HR-${1000 + selected.id}`}</p>
                      <p className="text-xs text-slate-500">Created {new Date(selected.created_at).toLocaleString()}</p>
                    </div>
                    <StatusPill status={selected.status} />
                  </div>
                  <button
                    onClick={() => refreshSelected(selected.id)}
                    className="p-1.5 rounded-lg hover:bg-slate-100 transition"
                    title="Refresh"
                  >
                    <RefreshCw className="w-4 h-4 text-slate-400" />
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {/* Entity IDs */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                      { label: 'Task ID', value: `#${selected.task_id}`, icon: <Hash className="w-3.5 h-3.5" /> },
                      { label: 'Submission', value: `#${selected.submission_id}`, icon: <FileText className="w-3.5 h-3.5" /> },
                      { label: 'Verification', value: `#${selected.verification_id}`, icon: <Shield className="w-3.5 h-3.5" /> },
                      { label: 'Worker Agent', value: `#${selected.worker_agent_id}`, icon: <User className="w-3.5 h-3.5" /> },
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

                  {/* Timeline */}
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: 'Started At', value: selected.started_at ? new Date(selected.started_at).toLocaleString() : '—' },
                      { label: 'Resolved At', value: selected.resolved_at ? new Date(selected.resolved_at).toLocaleString() : '—' },
                    ].map(item => (
                      <div key={item.label} className="flex items-start gap-2 bg-slate-50 rounded-xl border border-slate-200 p-3">
                        <Clock className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                        <div>
                          <p className="text-xs text-slate-400">{item.label}</p>
                          <p className="text-xs font-semibold text-slate-700 mt-0.5">{item.value}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Decision outcome */}
                  {isResolved && (
                    <div className={`rounded-xl border p-4 flex items-start gap-3 ${
                      selected.decision === 'APPROVE'
                        ? 'bg-emerald-50 border-emerald-200'
                        : 'bg-rose-50 border-rose-200'
                    }`}>
                      {selected.decision === 'APPROVE'
                        ? <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                        : <XCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                      }
                      <div>
                        <p className={`text-sm font-bold ${selected.decision === 'APPROVE' ? 'text-emerald-800' : 'text-rose-800'}`}>
                          {selected.decision === 'APPROVE' ? 'Approved — Escrow Released' : 'Rejected — Task Failed'}
                        </p>
                        {selected.reviewer_note && (
                          <p className="text-xs text-slate-600 mt-1 italic">"{selected.reviewer_note}"</p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  {!isResolved && (
                    <div className="rounded-xl border border-slate-200 p-4 space-y-4 bg-amber-50/50">
                      <p className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-amber-600" />
                        Arbitration Actions
                      </p>

                      {actionError && (
                        <div className="flex items-start gap-2 bg-rose-50 border border-rose-200 rounded-lg p-3">
                          <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                          <p className="text-xs text-rose-700">{actionError}</p>
                        </div>
                      )}
                      {actionSuccess && (
                        <div className="flex items-start gap-2 bg-emerald-50 border border-emerald-200 rounded-lg p-3">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                          <p className="text-xs text-emerald-700">{actionSuccess}</p>
                        </div>
                      )}

                      {canStart && (
                        <button
                          onClick={handleStart}
                          disabled={actionLoading}
                          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold transition disabled:opacity-50"
                        >
                          {actionLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                          Start Review
                        </button>
                      )}

                      {canResolve && (
                        <div className="space-y-3">
                          <div>
                            <label className="text-xs font-semibold text-slate-600 block mb-1.5">
                              Reviewer Note <span className="text-rose-500">*</span>
                            </label>
                            <textarea
                              value={resolveNote}
                              onChange={e => setResolveNote(e.target.value)}
                              rows={3}
                              placeholder="Provide justification for your decision (required)…"
                              className="w-full text-sm border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-400 resize-none bg-white"
                            />
                          </div>
                          <div className="flex gap-3">
                            <button
                              onClick={() => handleResolve('APPROVE')}
                              disabled={actionLoading}
                              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition disabled:opacity-50"
                            >
                              {actionLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                              Approve
                            </button>
                            <button
                              onClick={() => handleResolve('REJECT')}
                              disabled={actionLoading}
                              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-sm font-semibold transition disabled:opacity-50"
                            >
                              {actionLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4" />}
                              Reject
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Audit Trail */}
                  <div className="rounded-xl border border-slate-200 p-4 space-y-3">
                    <p className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                      <ClipboardList className="w-4 h-4 text-slate-500" />
                      Audit Trail
                    </p>
                    {auditLoading
                      ? <div className="flex items-center gap-2 text-xs text-slate-400"><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Loading…</div>
                      : <AuditTimeline logs={auditLogs} />
                    }
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DisputesPage;
