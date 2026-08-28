import React, { useState, useEffect } from 'react';
import { NavTab } from '../components/Navbar';
import {
  Coins,
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  Lock,
  RefreshCw,
  Clock,
  AlertTriangle,
  ExternalLink,
  Building2,
  Cpu,
  Layers,
  ArrowDownRight,
  ArrowUpRight,
  TrendingUp,
  Receipt,
  FileCheck
} from 'lucide-react';
import {
  fetchClientWallet,
  fetchSettlements,
  fetchEscrows,
  fetchSettlementSummary,
  ApiWallet,
  ApiSettlement,
  ApiEscrow,
  ApiSettlementSummary
} from '../services/api';
import { APTokenBadge } from '../components/APTokenBadge';

interface WalletPageProps {
  onNavigate: (tab: NavTab) => void;
  onSelectSettlement?: (settlementId: number) => void;
  onSelectTask?: (taskId: string) => void;
}

export const WalletPage: React.FC<WalletPageProps> = ({
  onNavigate,
  onSelectSettlement,
  onSelectTask,
}) => {
  const [wallet, setWallet] = useState<ApiWallet | null>(null);
  const [settlements, setSettlements] = useState<ApiSettlement[]>([]);
  const [escrows, setEscrows] = useState<ApiEscrow[]>([]);
  const [summary, setSummary] = useState<ApiSettlementSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'completed' | 'blocked'>('all');

  const loadData = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);

      const [wData, sData, eData, sumData] = await Promise.all([
        fetchClientWallet().catch(() => null),
        fetchSettlements().catch(() => []),
        fetchEscrows().catch(() => []),
        fetchSettlementSummary().catch(() => null),
      ]);

      setWallet(wData);
      setSettlements(sData);
      setEscrows(eData);
      setSummary(sumData);
    } catch (err) {
      console.error('Failed to load wallet data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredSettlements = settlements.filter((s) => {
    if (filter === 'all') return true;
    return s.status === filter;
  });

  return (
    <div className="max-w-6xl mx-auto py-10 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-800 border border-blue-200 text-xs font-mono font-bold mb-2">
            <Coins className="w-3.5 h-3.5 text-blue-600" />
            <span>Autonomous Financial Layer</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Requester Wallet & Escrow Ledger
          </h1>
          <p className="text-sm text-slate-600 max-w-2xl mt-1">
            Auditable balance tracking and conditional AP Credit settlements powered by independent verification.
          </p>
        </div>

        <button
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-semibold transition-all shadow-xs disabled:opacity-50 self-start sm:self-center"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh Balances
        </button>
      </div>

      {/* Simulated AP Notice */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-50/80 via-indigo-50/50 to-blue-50/80 border border-blue-200/80 text-xs text-blue-900 flex items-start gap-3 shadow-xs">
        <Coins className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong className="font-bold">Simulated Platform Currency:</strong> AP Credits are simulated platform tokens used for autonomous agent task coordination and conditional micropayments in this prototype.
        </div>
      </div>

      {/* 3-Card Balance Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Available AP */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm relative overflow-hidden transition-all hover:shadow-md">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Available AP
            </span>
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-200/60">
              <ArrowDownRight className="w-5 h-5" />
            </div>
          </div>
          <div className="flex items-baseline gap-2 mb-1">
            <APTokenBadge amount={wallet ? wallet.available_balance.toFixed(1) : '0.0'} size="lg" />
          </div>
          <p className="text-xs text-slate-500">
            Unallocated funds ready for new task bounties
          </p>
        </div>

        {/* Locked in Escrow */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm relative overflow-hidden transition-all hover:shadow-md">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Locked in Escrow
            </span>
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200/60">
              <Lock className="w-5 h-5" />
            </div>
          </div>
          <div className="flex items-baseline gap-2 mb-1">
            <APTokenBadge amount={wallet ? wallet.locked_balance.toFixed(1) : '0.0'} size="lg" />
          </div>
          <p className="text-xs text-slate-500">
            Reserved for assigned tasks awaiting verification
          </p>
        </div>

        {/* Total Spent */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm relative overflow-hidden transition-all hover:shadow-md">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Total Settled / Spent
            </span>
            <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center border border-purple-200/60">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="flex items-baseline gap-2 mb-1">
            <APTokenBadge amount={wallet ? wallet.total_spent.toFixed(1) : '0.0'} size="lg" />
          </div>
          <p className="text-xs text-slate-500">
            Released to agents upon verification PASS
          </p>
        </div>
      </div>

      {/* Recent Settlements Section */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Receipt className="w-5 h-5 text-blue-600" />
              Settlement History
            </h2>
            <p className="text-xs text-slate-500">
              Auditable records of conditional payouts executed by the settlement engine
            </p>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl self-start sm:self-auto">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                filter === 'all' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All ({settlements.length})
            </button>
            <button
              onClick={() => setFilter('completed')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                filter === 'completed' ? 'bg-white text-emerald-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Completed ({settlements.filter((s) => s.status === 'completed').length})
            </button>
            <button
              onClick={() => setFilter('blocked')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                filter === 'blocked' ? 'bg-white text-amber-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Blocked ({settlements.filter((s) => s.status === 'blocked').length})
            </button>
          </div>
        </div>

        {filteredSettlements.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-slate-200 rounded-2xl">
            <Receipt className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700">No settlements found</p>
            <p className="text-xs text-slate-400 mt-0.5">
              Settlements trigger automatically when tasks achieve an independent verification PASS.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                  <th className="pb-3 pr-4">Settlement Code</th>
                  <th className="pb-3 pr-4">Task</th>
                  <th className="pb-3 pr-4">Beneficiary</th>
                  <th className="pb-3 pr-4">Verification</th>
                  <th className="pb-3 pr-4">Amount</th>
                  <th className="pb-3 pr-4">Status</th>
                  <th className="pb-3 pr-4">Timestamp</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {filteredSettlements.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 pr-4 font-mono font-bold text-blue-700">
                      {s.settlement_code}
                    </td>
                    <td className="py-3.5 pr-4 max-w-[180px]">
                      <div className="truncate font-semibold text-slate-900">
                        {s.task_title || `Task #${s.task_id}`}
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">
                        {s.task_code || `ID: ${s.task_id}`}
                      </span>
                    </td>
                    <td className="py-3.5 pr-4">
                      <div className="font-semibold text-slate-900 truncate">
                        {s.worker_agent_name || `Agent #${s.worker_agent_id}`}
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">
                        {s.worker_wallet_code || `WL-${s.worker_wallet_id}`}
                      </span>
                    </td>
                    <td className="py-3.5 pr-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold ${
                        s.verification_decision === 'PASS'
                          ? 'text-emerald-700 bg-emerald-50'
                          : 'text-amber-700 bg-amber-50'
                      }`}>
                        {s.verification_decision === 'PASS' ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                        {s.verification_decision || 'PASS'}
                      </span>
                    </td>
                    <td className="py-3.5 pr-4 font-bold text-slate-900">
                      {s.amount.toFixed(1)} AP
                    </td>
                    <td className="py-3.5 pr-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold capitalize ${
                        s.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                          : s.status === 'blocked'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200/60'
                          : 'bg-slate-50 text-slate-700 border border-slate-200'
                      }`}>
                        {s.status}
                      </span>
                    </td>
                    <td className="py-3.5 pr-4 font-mono text-[11px] text-slate-500">
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 text-right">
                      <button
                        onClick={() => {
                          if (onSelectSettlement) {
                            onSelectSettlement(s.id);
                          } else {
                            onNavigate('settlement-details');
                          }
                        }}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-xs transition-colors"
                      >
                        Proof <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Escrows Overview */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
          <Lock className="w-5 h-5 text-indigo-600" />
          Active Escrow Accounts
        </h2>
        <p className="text-xs text-slate-500 mb-6">
          Atomic escrow locks reserving rewards while tasks progress through execution and independent verification
        </p>

        {escrows.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            No active escrow accounts at this time.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {escrows.slice(0, 6).map((e) => (
              <div
                key={e.id}
                className="p-4 rounded-2xl bg-slate-50/70 border border-slate-200/70 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono font-bold text-xs text-slate-900">
                    {e.escrow_code}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded capitalize ${
                    e.status === 'released'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                      : e.status === 'releasable'
                      ? 'bg-blue-50 text-blue-700 border border-blue-200/60'
                      : e.status === 'blocked'
                      ? 'bg-amber-50 text-amber-700 border border-amber-200/60'
                      : 'bg-slate-100 text-slate-700'
                  }`}>
                    {e.status}
                  </span>
                </div>
                <div className="text-xs text-slate-600 truncate mb-2">
                  Task: {e.task_code || `ID ${e.task_id}`}
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-slate-200/60 text-xs">
                  <span className="text-slate-500">Reserved Reward</span>
                  <span className="font-bold text-slate-900">{e.reward_amount} AP</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
