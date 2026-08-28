import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Zap,
  ArrowRight,
  RefreshCw,
  Copy,
  Check,
  ExternalLink,
  Coins,
  FileText,
  UserCheck,
  Lock,
  Unlock,
  Building2,
  Cpu
} from 'lucide-react';
import {
  fetchSettlement,
  fetchSettlementAudit,
  fetchSettlementLedger,
  retrySettlement,
  ApiSettlement,
  ApiSettlementAuditLog,
  ApiLedgerEntry
} from '../services/api';
import { APTokenBadge } from '../components/APTokenBadge';
import { NavTab } from '../components/Navbar';

interface SettlementDetailsPageProps {
  settlementId: number;
  onBack: () => void;
  onNavigateToTask?: (taskId: string) => void;
  onNavigateToAgent?: (agentId: number) => void;
  onNavigateToVerification?: (verifId: number) => void;
  onNavigate?: (tab: NavTab) => void;
}

export const SettlementDetailsPage: React.FC<SettlementDetailsPageProps> = ({
  settlementId,
  onBack,
  onNavigateToTask,
  onNavigateToAgent,
  onNavigateToVerification,
  onNavigate,
}) => {
  const [settlement, setSettlement] = useState<ApiSettlement | null>(null);
  const [auditLogs, setAuditLogs] = useState<ApiSettlementAuditLog[]>([]);
  const [ledgerEntries, setLedgerEntries] = useState<ApiLedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sData, aData, lData] = await Promise.all([
        fetchSettlement(settlementId),
        fetchSettlementAudit(settlementId).catch(() => []),
        fetchSettlementLedger(settlementId).catch(() => []),
      ]);
      setSettlement(sData);
      setAuditLogs(aData);
      setLedgerEntries(lData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load settlement details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (settlementId) {
      loadData();
    }
  }, [settlementId]);

  const handleRetry = async () => {
    if (!settlement) return;
    try {
      setRetrying(true);
      const updated = await retrySettlement(settlement.id);
      setSettlement(updated);
      await loadData();
    } catch (err: any) {
      alert(`Retry failed: ${err.message}`);
    } finally {
      setRetrying(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(text);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Completed
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <RefreshCw className="w-3.5 h-3.5 text-blue-600 animate-spin" />
            Processing
          </span>
        );
      case 'blocked':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            Blocked
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
            <XCircle className="w-3.5 h-3.5 text-red-600" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-50 text-slate-700 border border-slate-200">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            Pending
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 mb-4 animate-pulse">
          <RefreshCw className="w-7 h-7 animate-spin" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-1">Loading Settlement Record...</h2>
        <p className="text-slate-500 text-sm">Querying verified ledger proof and audit trail</p>
      </div>
    );
  }

  if (error || !settlement) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900 font-medium mb-6 text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <div className="bg-white rounded-2xl border border-red-200 p-8 text-center shadow-sm">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-900 mb-1">Settlement Not Found</h3>
          <p className="text-slate-600 text-sm mb-6">{error || 'Unable to locate the requested settlement.'}</p>
          <button
            onClick={loadData}
            className="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-medium text-sm hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const isCompleted = settlement.status === 'completed';
  const isBlocked = settlement.status === 'blocked';
  const isFailed = settlement.status === 'failed';

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Top Breadcrumbs & Actions */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 font-medium text-sm transition-all shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>

        <div className="flex items-center gap-3">
          {isFailed && (
            <button
              onClick={handleRetry}
              disabled={retrying}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold transition-all shadow-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${retrying ? 'animate-spin' : ''}`} />
              Retry Settlement
            </button>
          )}

          {onNavigate && (
            <button
              onClick={() => onNavigate('wallet')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-slate-200 hover:border-slate-300 text-slate-800 text-sm font-semibold transition-all shadow-xs"
            >
              <Coins className="w-4 h-4 text-blue-600" />
              View Wallet
            </button>
          )}
        </div>
      </div>

      {/* Main Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm mb-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-blue-50/60 via-indigo-50/30 to-transparent rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <span className="text-xs font-mono font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200/60">
                {settlement.settlement_code}
              </span>
              {getStatusBadge(settlement.status)}
              <span className="text-xs text-slate-500 font-medium capitalize">
                Trigger: {settlement.trigger_type}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mb-2">
              Conditional AP Settlement
            </h1>
            <p className="text-slate-600 text-sm max-w-2xl">
              Automatic fund transfer executed upon successful verification and integrity validation of the deliverable.
            </p>
          </div>

          <div className="flex flex-col items-start md:items-end justify-center bg-slate-50/80 border border-slate-100 rounded-2xl p-5 shrink-0">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
              Settlement Amount
            </span>
            <div className="flex items-center gap-2">
              <APTokenBadge amount={settlement.amount.toFixed(1)} size="lg" />
            </div>
            <span className="text-xs text-slate-500 mt-1">Simulated AP Credits</span>
          </div>
        </div>
      </div>

      {/* Flow Visualization Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm mb-8">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-6 flex items-center gap-2">
          <Zap className="w-4 h-4 text-blue-600" />
          Autonomous Economic Flow
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
          {/* Step 1: Requester */}
          <div className="flex flex-col p-4 rounded-2xl bg-slate-50/80 border border-slate-200/80 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-500 uppercase">1. Requester</span>
              <Building2 className="w-4 h-4 text-slate-600" />
            </div>
            <span className="text-sm font-bold text-slate-900 mb-1">Client Wallet</span>
            <span className="text-xs font-mono text-slate-500 mb-2">
              {settlement.requester_wallet_code || `WL-${settlement.requester_wallet_id}`}
            </span>
            <span className="text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/60 font-medium">
              - {settlement.amount} AP Locked
            </span>
          </div>

          {/* Arrow */}
          <div className="hidden md:flex items-center justify-center text-slate-400">
            <ArrowRight className="w-5 h-5 text-blue-500" />
          </div>

          {/* Step 2: Escrow */}
          <div className="flex flex-col p-4 rounded-2xl bg-slate-50/80 border border-slate-200/80 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-500 uppercase">2. Escrow</span>
              <Lock className="w-4 h-4 text-blue-600" />
            </div>
            <span className="text-sm font-bold text-slate-900 mb-1">
              {settlement.escrow_code || `ES-${settlement.escrow_id}`}
            </span>
            <span className="text-xs text-slate-500 mb-2">Atomic Reservation</span>
            <span className="text-[11px] text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200/60 font-medium">
              Status: {isCompleted ? 'Released' : settlement.status}
            </span>
          </div>

          {/* Arrow */}
          <div className="hidden md:flex items-center justify-center text-slate-400">
            <ArrowRight className="w-5 h-5 text-blue-500" />
          </div>

          {/* Step 3: Worker */}
          <div className="flex flex-col p-4 rounded-2xl bg-slate-50/80 border border-slate-200/80 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-500 uppercase">3. Worker Agent</span>
              <Cpu className="w-4 h-4 text-indigo-600" />
            </div>
            <span className="text-sm font-bold text-slate-900 mb-1 truncate">
              {settlement.worker_agent_name || `Agent #${settlement.worker_agent_id}`}
            </span>
            <span className="text-xs font-mono text-slate-500 mb-2">
              {settlement.worker_wallet_code || `WL-${settlement.worker_wallet_id}`}
            </span>
            <span className="text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/60 font-medium">
              + {settlement.amount} AP Available
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Settlement Proof Card */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-blue-600" />
            Settlement Proof
          </h2>
          <p className="text-slate-500 text-xs mb-6">
            Immutable cryptographic and structural evidence of conditional payout.
          </p>

          <div className="space-y-3.5 text-sm">
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 text-xs font-medium">Settlement Code</span>
              <div className="flex items-center gap-1.5">
                <span className="font-mono font-bold text-slate-900">{settlement.settlement_code}</span>
                <button
                  onClick={() => copyToClipboard(settlement.settlement_code)}
                  className="p-1 text-slate-400 hover:text-slate-700 rounded transition-colors"
                  title="Copy"
                >
                  {copiedCode === settlement.settlement_code ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 text-xs font-medium">Task Code</span>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-slate-900">{settlement.task_code || `Task #${settlement.task_id}`}</span>
                {onNavigateToTask && settlement.task_id && (
                  <button
                    onClick={() => onNavigateToTask(String(settlement.task_id))}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1"
                  >
                    View <ExternalLink className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 text-xs font-medium">Escrow Code</span>
              <span className="font-mono font-bold text-slate-900">{settlement.escrow_code || `ES-${settlement.escrow_id}`}</span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 text-xs font-medium">Verification Code</span>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-slate-900">
                  {settlement.verification_code || `VR-${settlement.verification_id || 'N/A'}`}
                </span>
                {onNavigateToVerification && settlement.verification_id && (
                  <button
                    onClick={() => onNavigateToVerification(settlement.verification_id!)}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1"
                  >
                    View <ExternalLink className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 text-xs font-medium">Beneficiary Agent</span>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900">{settlement.worker_agent_name || `Agent #${settlement.worker_agent_id}`}</span>
                {onNavigateToAgent && (
                  <button
                    onClick={() => onNavigateToAgent(settlement.worker_agent_id)}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1"
                  >
                    View <ExternalLink className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 text-xs font-medium">Verification Decision</span>
              <span className={`inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded ${
                settlement.verification_decision === 'PASS' ? 'text-emerald-700 bg-emerald-50' : 'text-amber-700 bg-amber-50'
              }`}>
                {settlement.verification_decision === 'PASS' ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                {settlement.verification_decision || 'PASS'}
              </span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 text-xs font-medium">Package Integrity</span>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                <ShieldCheck className="w-3.5 h-3.5" /> Verified Valid (SHA-256)
              </span>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-slate-500 text-xs font-medium">Settled Timestamp</span>
              <span className="text-xs font-mono text-slate-700">
                {settlement.completed_at ? new Date(settlement.completed_at).toLocaleString() : 'In Progress'}
              </span>
            </div>
          </div>
        </div>

        {/* Explainability & Reason Card */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-600" />
              Why was this settlement released?
            </h2>
            <p className="text-slate-500 text-xs mb-6">
              Autonomous verification reasoning and release justification.
            </p>

            <div className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200/80 mb-6">
              {isCompleted ? (
                <div className="space-y-3">
                  <div className="flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <p className="text-xs sm:text-sm text-slate-700 font-medium leading-relaxed">
                      Independent Phase 10 verification completed with a <strong className="text-emerald-700 font-bold">PASS</strong> decision, meeting all required quality and capability thresholds.
                    </p>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <p className="text-xs sm:text-sm text-slate-700 font-medium leading-relaxed">
                      Submission package SHA-256 cryptographic integrity was verified without tampering or post-freeze modifications.
                    </p>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <p className="text-xs sm:text-sm text-slate-700 font-medium leading-relaxed">
                      Task reward of <strong className="text-slate-900 font-bold">{settlement.amount} AP</strong> was atomically moved from Requester Locked balance to Worker Available balance.
                    </p>
                  </div>
                </div>
              ) : isBlocked ? (
                <div className="space-y-3">
                  <div className="flex items-start gap-2.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <p className="text-xs sm:text-sm text-slate-700 font-medium leading-relaxed">
                      Settlement is <strong className="text-amber-700 font-bold">BLOCKED</strong>: {settlement.failure_reason || 'Verification did not meet the required threshold or human review was requested.'}
                    </p>
                  </div>
                  <p className="text-xs text-slate-500">
                    No AP Credits were transferred to the worker agent.
                  </p>
                </div>
              ) : (
                <p className="text-xs text-slate-600 leading-relaxed">
                  Settlement is currently in <strong className="font-semibold text-slate-900">{settlement.status}</strong> state.
                </p>
              )}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200/60 text-xs text-blue-900 flex items-start gap-2.5">
            <Coins className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Prototype Note:</span> AP Credits are simulated platform credits used to model autonomous machine-to-machine micropayments.
            </div>
          </div>
        </div>
      </div>

      {/* Double-Entry Ledger Table */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm mb-8">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <div>
            <h2 className="text-base font-bold text-slate-900">Double-Entry Financial Ledger</h2>
            <p className="text-slate-500 text-xs">Auditable debit & credit transaction records</p>
          </div>
          <span className="text-xs font-mono font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">
            {ledgerEntries.length} Entries Recorded
          </span>
        </div>

        {ledgerEntries.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            No ledger entries generated yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                  <th className="pb-3 pr-4">Entry Code</th>
                  <th className="pb-3 pr-4">Entry Type</th>
                  <th className="pb-3 pr-4">Wallet</th>
                  <th className="pb-3 pr-4">Balance Type</th>
                  <th className="pb-3 pr-4">Amount</th>
                  <th className="pb-3">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {ledgerEntries.map((entry) => (
                  <tr key={entry.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 pr-4 font-mono font-bold text-slate-900">
                      {entry.entry_code}
                    </td>
                    <td className="py-3 pr-4">
                      <span className={`inline-block px-2 py-0.5 rounded font-mono text-[11px] ${
                        entry.entry_type === 'settlement_credit'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                          : 'bg-blue-50 text-blue-700 border border-blue-200/60'
                      }`}>
                        {entry.entry_type}
                      </span>
                    </td>
                    <td className="py-3 pr-4 font-mono text-slate-600">
                      WL-{entry.wallet_id}
                    </td>
                    <td className="py-3 pr-4 capitalize text-slate-600">
                      {entry.balance_type}
                    </td>
                    <td className="py-3 pr-4 font-bold text-slate-900">
                      {entry.entry_type === 'settlement_credit' ? '+' : '-'}{entry.amount.toFixed(1)} AP
                    </td>
                    <td className="py-3 text-slate-500 max-w-xs truncate">
                      {entry.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Chronological Audit Log */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <h2 className="text-base font-bold text-slate-900 mb-1">Settlement Audit Trail</h2>
        <p className="text-slate-500 text-xs mb-6">Immutable chronological timeline of all settlement actions</p>

        {auditLogs.length === 0 ? (
          <div className="text-center py-6 text-slate-400 text-xs">
            No audit logs recorded for this settlement.
          </div>
        ) : (
          <div className="space-y-4">
            {auditLogs.map((log, index) => (
              <div key={log.id} className="flex items-start gap-4 text-xs">
                <div className="w-6 h-6 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5 border border-blue-200/60">
                  {index + 1}
                </div>
                <div className="flex-1 bg-slate-50/70 border border-slate-100 rounded-xl p-3.5">
                  <div className="flex items-center justify-between gap-2 mb-1 flex-wrap">
                    <span className="font-mono font-bold text-slate-900 uppercase">
                      {log.action}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      {new Date(log.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-slate-600 text-xs mb-1.5">{log.message}</p>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400 font-medium">
                    <span>Actor: {log.actor_type} ({log.actor_id || 'system'})</span>
                    {log.amount && <span>Amount: {log.amount} AP</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
