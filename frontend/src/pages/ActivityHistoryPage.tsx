import React, { useState, useEffect } from 'react';
import { NavTab } from '../components/Navbar';
import {
  Activity,
  Coins,
  ShieldCheck,
  ShieldAlert,
  Gavel,
  Award,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Filter,
  RefreshCw,
  Search,
  User,
  Layers,
  Lock,
  ArrowDownRight,
  ArrowUpRight,
  TrendingUp,
  Receipt,
  Scale,
  Clock,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import {
  fetchActivity,
  fetchAllTransactions,
  ActivityEvent,
  TransactionItem
} from '../services/api';
import { APTokenBadge } from '../components/APTokenBadge';

interface ActivityHistoryPageProps {
  onNavigate: (tab: NavTab) => void;
  onSelectTask?: (taskId: string) => void;
  onSelectAgent?: (agentId: number) => void;
}

export const ActivityHistoryPage: React.FC<ActivityHistoryPageProps> = ({
  onNavigate,
  onSelectTask,
  onSelectAgent,
}) => {
  const [activeView, setActiveView] = useState<'events' | 'transactions'>('events');
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedEventType, setSelectedEventType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadData = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);

      const [activityData, txData] = await Promise.all([
        fetchActivity({ limit: 150 }).catch(() => []),
        fetchAllTransactions(100).catch(() => []),
      ]);

      setEvents(activityData);
      setTransactions(txData);
    } catch (err) {
      console.error('Failed to load activity/transaction data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const eventTypeFilters = [
    { id: 'all', label: 'All Lifecycle Events' },
    { id: 'task_created', label: 'Tasks Created' },
    { id: 'bid_submitted', label: 'Bids' },
    { id: 'worker_selected', label: 'Assignments' },
    { id: 'escrow_locked', label: 'Escrow' },
    { id: 'execution_started', label: 'Executions' },
    { id: 'result_submitted', label: 'Submissions' },
    { id: 'verification_passed', label: 'Verifications' },
    { id: 'dispute_opened', label: 'Disputes' },
    { id: 'arbitration_decision', label: 'Arbitration' },
    { id: 'settlement_completed', label: 'Settlements' },
    { id: 'reputation_updated', label: 'Reputation' },
  ];

  const filteredEvents = events.filter((ev) => {
    const matchesType =
      selectedEventType === 'all' ||
      ev.event_type === selectedEventType ||
      (selectedEventType === 'verification_passed' &&
        ['verification_passed', 'verification_failed', 'verification_review'].includes(ev.event_type)) ||
      (selectedEventType === 'settlement_completed' &&
        ['settlement_completed', 'settlement_blocked'].includes(ev.event_type));

    const matchesSearch =
      searchQuery === '' ||
      ev.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ev.related_entity_code && ev.related_entity_code.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesType && matchesSearch;
  });

  const filteredTransactions = transactions.filter((tx) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (tx.entry_code && tx.entry_code.toLowerCase().includes(q)) ||
      (tx.settlement_code && tx.settlement_code.toLowerCase().includes(q)) ||
      (tx.escrow_code && tx.escrow_code.toLowerCase().includes(q)) ||
      (tx.task_title && tx.task_title.toLowerCase().includes(q)) ||
      tx.description.toLowerCase().includes(q)
    );
  });

  const getEventBadge = (type: string, status?: string | null) => {
    switch (type) {
      case 'task_created':
        return {
          icon: <Layers className="w-4 h-4 text-blue-600" />,
          bg: 'bg-blue-50 border-blue-200 text-blue-800',
          label: 'Task Published',
        };
      case 'bid_submitted':
        return {
          icon: <FileText className="w-4 h-4 text-purple-600" />,
          bg: 'bg-purple-50 border-purple-200 text-purple-800',
          label: 'Bid Offer',
        };
      case 'worker_selected':
        return {
          icon: <User className="w-4 h-4 text-indigo-600" />,
          bg: 'bg-indigo-50 border-indigo-200 text-indigo-800',
          label: 'Worker Assigned',
        };
      case 'escrow_locked':
        return {
          icon: <Lock className="w-4 h-4 text-amber-600" />,
          bg: 'bg-amber-50 border-amber-200 text-amber-800',
          label: 'Escrow Locked',
        };
      case 'execution_started':
      case 'execution_completed':
        return {
          icon: <Clock className="w-4 h-4 text-cyan-600" />,
          bg: 'bg-cyan-50 border-cyan-200 text-cyan-800',
          label: 'Execution',
        };
      case 'result_submitted':
        return {
          icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />,
          bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
          label: 'Result Submitted',
        };
      case 'verification_passed':
        return {
          icon: <ShieldCheck className="w-4 h-4 text-emerald-600" />,
          bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
          label: 'Verification PASS',
        };
      case 'verification_failed':
        return {
          icon: <ShieldAlert className="w-4 h-4 text-rose-600" />,
          bg: 'bg-rose-50 border-rose-200 text-rose-800',
          label: 'Verification FAIL',
        };
      case 'verification_review':
        return {
          icon: <AlertTriangle className="w-4 h-4 text-amber-600" />,
          bg: 'bg-amber-50 border-amber-200 text-amber-800',
          label: 'Human Review Req',
        };
      case 'human_review':
        return {
          icon: <Scale className="w-4 h-4 text-orange-600" />,
          bg: 'bg-orange-50 border-orange-200 text-orange-800',
          label: 'Human Review',
        };
      case 'dispute_opened':
        return {
          icon: <AlertTriangle className="w-4 h-4 text-rose-600" />,
          bg: 'bg-rose-50 border-rose-200 text-rose-800',
          label: 'Dispute Raised',
        };
      case 'arbitration_decision':
        return {
          icon: <Gavel className="w-4 h-4 text-indigo-600" />,
          bg: 'bg-indigo-50 border-indigo-200 text-indigo-800',
          label: 'AI Arbitration',
        };
      case 'settlement_completed':
        return {
          icon: <Coins className="w-4 h-4 text-emerald-600" />,
          bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
          label: 'Settlement Paid',
        };
      case 'settlement_blocked':
        return {
          icon: <Lock className="w-4 h-4 text-amber-600" />,
          bg: 'bg-amber-50 border-amber-200 text-amber-800',
          label: 'Settlement Blocked',
        };
      case 'reputation_updated':
        return {
          icon: <Award className="w-4 h-4 text-amber-600" />,
          bg: 'bg-amber-50 border-amber-200 text-amber-800',
          label: 'Reputation Delta',
        };
      default:
        return {
          icon: <Activity className="w-4 h-4 text-slate-600" />,
          bg: 'bg-slate-50 border-slate-200 text-slate-800',
          label: status || 'Event',
        };
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-800 border border-blue-200 text-xs font-mono font-bold mb-2">
            <Activity className="w-3.5 h-3.5 text-blue-600" />
            <span>Phase 17 — Complete Lifecycle Audit</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Transaction & Activity History
          </h1>
          <p className="text-sm text-slate-600 max-w-3xl mt-1">
            Immutable end-to-end timeline tracing the lifecycle of autonomous tasks: from creation, bidding, and escrow, to execution, verification, dispute arbitration, AP settlement, and reputation updates.
          </p>
        </div>

        <button
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-semibold transition-all shadow-xs disabled:opacity-50 self-start sm:self-center"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh Audit Trail
        </button>
      </div>

      {/* Traceability Flow Banner */}
      <div className="p-5 rounded-3xl bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-blue-300 uppercase tracking-wider mb-1">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>Full Deterministic Traceability</span>
            </div>
            <p className="text-sm text-slate-200 font-medium">
              Every state transition is cryptographically verifiable & linked across the autonomous agent network.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono bg-white/10 backdrop-blur-md px-4 py-2 rounded-xl border border-white/20">
            <span className="text-cyan-300">Task</span>
            <span className="text-slate-400">→</span>
            <span className="text-purple-300">Worker</span>
            <span className="text-slate-400">→</span>
            <span className="text-amber-300">Verification</span>
            <span className="text-slate-400">→</span>
            <span className="text-emerald-300">Settlement</span>
            <span className="text-slate-400">→</span>
            <span className="text-yellow-300">Reputation</span>
          </div>
        </div>
      </div>

      {/* Main Tabs & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-4 rounded-3xl border border-slate-200 shadow-xs">
        {/* Toggle between Lifecycle Events and Financial Ledger */}
        <div className="flex items-center gap-2 bg-slate-100 p-1.5 rounded-2xl">
          <button
            onClick={() => setActiveView('events')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeView === 'events'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Activity className="w-4 h-4 text-blue-600" />
            <span>Lifecycle Events ({filteredEvents.length})</span>
          </button>

          <button
            onClick={() => setActiveView('transactions')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeView === 'transactions'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Receipt className="w-4 h-4 text-emerald-600" />
            <span>Financial Ledger ({filteredTransactions.length})</span>
          </button>
        </div>

        {/* Search input */}
        <div className="relative min-w-[260px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by code, title, or details..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 hover:bg-slate-100/80 focus:bg-white text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-900 placeholder:text-slate-400 transition"
          />
        </div>
      </div>

      {/* Content for View 1: Lifecycle Events Timeline */}
      {activeView === 'events' && (
        <div className="space-y-6">
          {/* Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1 shrink-0 mr-1">
              <Filter className="w-3.5 h-3.5" /> Filter:
            </span>
            {eventTypeFilters.map((f) => (
              <button
                key={f.id}
                onClick={() => setSelectedEventType(f.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition-all border ${
                  selectedEventType === f.id
                    ? 'bg-blue-900 text-white border-blue-900 shadow-xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="text-center py-16 bg-white rounded-3xl border border-slate-200">
              <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-700">Loading audit events...</p>
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-3xl border border-dashed border-slate-200">
              <Activity className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p className="text-base font-bold text-slate-800">No matching lifecycle events</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                No events found matching your search and filter criteria. Try selecting "All Lifecycle Events".
              </p>
            </div>
          ) : (
            <div className="relative pl-6 md:pl-8 space-y-4 before:content-[''] before:absolute before:left-3 md:before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-200">
              {filteredEvents.map((ev, idx) => {
                const badge = getEventBadge(ev.event_type, ev.status);
                return (
                  <div
                    key={`${ev.event_type}-${ev.created_at}-${idx}`}
                    className="relative bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs hover:shadow-md transition-all group"
                  >
                    {/* Timeline Node Icon */}
                    <div className="absolute -left-[31px] md:-left-[35px] top-5 w-7 h-7 rounded-full bg-white border-2 border-slate-300 group-hover:border-blue-600 flex items-center justify-center shadow-xs transition-colors">
                      {badge.icon}
                    </div>

                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${badge.bg}`}>
                          {badge.label}
                        </span>

                        {ev.related_entity_code && (
                          <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                            {ev.related_entity_code}
                          </span>
                        )}

                        {ev.amount !== null && ev.amount !== undefined && (
                          <span className="inline-flex items-center gap-1 text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                            <Coins className="w-3 h-3 text-amber-600" />
                            {ev.amount > 0 && ev.event_type === 'reputation_updated' ? `+${ev.amount}` : ev.amount} AP
                          </span>
                        )}
                      </div>

                      <span className="text-[11px] font-mono text-slate-400">
                        {ev.created_at ? new Date(ev.created_at).toLocaleString() : 'N/A'}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-slate-900 mb-1">{ev.title}</h3>
                    <p className="text-xs text-slate-600 leading-relaxed">{ev.description}</p>

                    {/* Action Links */}
                    {(ev.task_id || ev.agent_id) && (
                      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-3 text-xs">
                        {ev.task_id && (
                          <button
                            onClick={() => {
                              if (onSelectTask) onSelectTask(String(ev.task_id));
                              else onNavigate('tasks');
                            }}
                            className="inline-flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-800 hover:underline"
                          >
                            <span>Task #{ev.task_id}</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        )}

                        {ev.agent_id && (
                          <button
                            onClick={() => {
                              if (onSelectAgent) onSelectAgent(ev.agent_id!);
                              else onNavigate('agents');
                            }}
                            className="inline-flex items-center gap-1 font-semibold text-purple-600 hover:text-purple-800 hover:underline"
                          >
                            <span>Agent #{ev.agent_id}</span>
                            <ExternalLink className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Content for View 2: Financial Ledger Transactions */}
      {activeView === 'transactions' && (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Receipt className="w-5 h-5 text-emerald-600" />
              Real AP Movements Ledger
            </h2>
            <p className="text-xs text-slate-500">
              Only authentic financial records (Escrow Locks, Settlement Debits, and Settlement Credits). No simulated or fabricated transactions.
            </p>
          </div>

          {loading ? (
            <div className="text-center py-16">
              <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-700">Loading ledger entries...</p>
            </div>
          ) : filteredTransactions.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-slate-200 rounded-2xl">
              <Receipt className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-700">No transactions recorded</p>
              <p className="text-xs text-slate-400 mt-0.5">
                Financial ledger entries are recorded when escrows are locked or settlements are completed.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                    <th className="pb-3 pr-4">Entry Code</th>
                    <th className="pb-3 pr-4">Type & Direction</th>
                    <th className="pb-3 pr-4">Task & Reference</th>
                    <th className="pb-3 pr-4">Amount</th>
                    <th className="pb-3 pr-4">Balance Type</th>
                    <th className="pb-3 pr-4">Description</th>
                    <th className="pb-3 pr-4">Status</th>
                    <th className="pb-3 text-right">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                  {filteredTransactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3.5 pr-4 font-mono font-bold text-blue-700">
                        {tx.entry_code || `LE-${tx.id}`}
                      </td>
                      <td className="py-3.5 pr-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold ${
                            tx.direction === 'credit'
                              ? 'text-emerald-700 bg-emerald-50 border border-emerald-200/60'
                              : tx.direction === 'debit'
                              ? 'text-purple-700 bg-purple-50 border border-purple-200/60'
                              : 'text-amber-700 bg-amber-50 border border-amber-200/60'
                          }`}
                        >
                          {tx.direction === 'credit' && <ArrowDownRight className="w-3 h-3" />}
                          {tx.direction === 'debit' && <ArrowUpRight className="w-3 h-3" />}
                          {tx.direction === 'lock' && <Lock className="w-3 h-3" />}
                          {tx.entry_type.replace('_', ' ').toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3.5 pr-4 max-w-[180px]">
                        <div className="truncate font-semibold text-slate-900">
                          {tx.task_title || (tx.task_id ? `Task #${tx.task_id}` : 'Platform Action')}
                        </div>
                        <span className="text-[11px] font-mono text-slate-400">
                          {tx.settlement_code || tx.escrow_code || (tx.wallet_id ? `Wallet #${tx.wallet_id}` : '')}
                        </span>
                      </td>
                      <td className="py-3.5 pr-4 font-bold text-slate-900">
                        <span
                          className={
                            tx.direction === 'credit'
                              ? 'text-emerald-700'
                              : tx.direction === 'debit'
                              ? 'text-purple-700'
                              : 'text-slate-900'
                          }
                        >
                          {tx.direction === 'credit' ? '+' : tx.direction === 'debit' ? '-' : ''}
                          {tx.amount.toFixed(1)} AP
                        </span>
                      </td>
                      <td className="py-3.5 pr-4 capitalize text-slate-600 font-mono text-[11px]">
                        {tx.balance_type}
                      </td>
                      <td className="py-3.5 pr-4 text-slate-600 max-w-[220px] truncate" title={tx.description}>
                        {tx.description}
                      </td>
                      <td className="py-3.5 pr-4">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/60 capitalize">
                          {tx.status}
                        </span>
                      </td>
                      <td className="py-3.5 text-right font-mono text-[11px] text-slate-500 whitespace-nowrap">
                        {tx.created_at ? new Date(tx.created_at).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
