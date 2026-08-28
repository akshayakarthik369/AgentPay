import React, { useState, useEffect, useCallback } from 'react';
import {
  Users, PlusCircle, Search, Filter, RefreshCw,
  Cpu, CheckCircle2, XCircle, AlertCircle, Clock,
  Star, Wallet, Award, ChevronRight, Zap, Shield, ShieldOff
} from 'lucide-react';
import { NavTab } from '../components/Navbar';
import {
  fetchAgents, ApiAgent, AgentFilterParams,
  activateAgent, deactivateAgent
} from '../services/api';
import { Interactive3DCard } from '../components/Interactive3DCard';
import { AgentNode } from '../components/AgentNode';

interface AgentsPageProps {
  onNavigate: (tab: NavTab) => void;
  onSelectAgent: (id: number) => void;
}

const STATUS_COLORS: Record<string, string> = {
  available: 'text-emerald-800 bg-emerald-50 border-emerald-300 font-semibold',
  busy:      'text-amber-800  bg-amber-50  border-amber-300 font-semibold',
  offline:   'text-slate-600  bg-slate-100 border-slate-200 font-semibold',
  suspended: 'text-rose-800   bg-rose-50   border-rose-300 font-semibold',
};

const TYPE_COLORS: Record<string, string> = {
  worker:       'text-[#3155D9] bg-blue-50 border-blue-200 font-semibold',
  verifier:     'text-[#6D5BD0] bg-purple-50 border-purple-200 font-semibold',
  orchestrator: 'text-[#172554] bg-slate-100 border-slate-200 font-semibold',
};

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  switch (status) {
    case 'available': return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />;
    case 'busy':      return <Clock className="w-3.5 h-3.5 text-amber-600" />;
    case 'offline':   return <XCircle className="w-3.5 h-3.5 text-slate-500" />;
    case 'suspended': return <AlertCircle className="w-3.5 h-3.5 text-rose-600" />;
    default:          return null;
  }
};

const AgentCard: React.FC<{
  agent: ApiAgent;
  onSelect: () => void;
  onToggle: () => void;
  toggling: boolean;
}> = ({ agent, onSelect, onToggle, toggling }) => (
  <Interactive3DCard
    level="interactive"
    maxRotation={2.5}
    maxTranslation={3}
    glowColor={agent.agent_type === 'verifier' ? 'violet' : agent.agent_type === 'orchestrator' ? 'navy' : 'blue'}
    className="p-5 sm:p-6 rounded-2xl bg-white border border-slate-200 shadow-sm cursor-pointer flex flex-col gap-4 justify-between h-full hover:border-slate-300 hover:shadow-md transition-all overflow-hidden"
    onClick={onSelect}
  >
    {/* Fully Responsive Header with AgentNode Motif & Badges */}
    <div className="flex flex-col sm:flex-row items-start sm:items-start justify-between gap-3 w-full min-w-0">
      <div className="min-w-0 flex-1 w-full">
        <AgentNode
          name={agent.name}
          code={agent.agent_code}
          agentType={agent.agent_type as any}
          status={agent.status as any}
          reputation={agent.reputation_score}
          showDetails
          className="w-full min-w-0"
        />
      </div>

      <div className="flex flex-row sm:flex-col items-start sm:items-end gap-1.5 shrink-0 flex-wrap">
        {/* NON-CLICKABLE STATUS BADGE */}
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] border uppercase tracking-wider whitespace-nowrap shrink-0 ${STATUS_COLORS[agent.status] ?? STATUS_COLORS.offline}`}>
          <StatusIcon status={agent.status} />
          <span>{agent.status}</span>
        </span>
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold border capitalize whitespace-nowrap shrink-0 ${TYPE_COLORS[agent.agent_type] ?? TYPE_COLORS.worker}`}>
          {agent.agent_type}
        </span>
        {/* Phase 18: Risk badge */}
        {agent.risk_score !== undefined && agent.risk_score > 0 && (
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border whitespace-nowrap shrink-0 ${
            (agent.risk_score ?? 0) >= 80 ? 'bg-rose-100 text-rose-700 border-rose-300' :
            (agent.risk_score ?? 0) >= 60 ? 'bg-orange-100 text-orange-700 border-orange-300' :
            (agent.risk_score ?? 0) >= 30 ? 'bg-amber-100 text-amber-700 border-amber-300' :
                                             'bg-slate-100 text-slate-500 border-slate-200'
          }`}>
            <Shield className="w-2.5 h-2.5" />
            Risk {agent.risk_score?.toFixed(0)}
          </span>
        )}
        {agent.is_suspended && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border bg-rose-100 text-rose-700 border-rose-300 whitespace-nowrap shrink-0">
            <ShieldOff className="w-2.5 h-2.5" />
            Suspended
          </span>
        )}
      </div>
    </div>

    {/* Description */}
    <p className="text-xs text-[#596273] leading-relaxed line-clamp-2">{agent.description}</p>

    {/* Capabilities */}
    <div className="flex flex-wrap gap-1.5">
      {agent.capabilities.map(cap => (
        <span key={cap} className="px-2.5 py-0.5 rounded-md text-[10px] font-mono font-medium bg-slate-100 text-[#18202F] border border-slate-200">
          {cap}
        </span>
      ))}
    </div>

    {/* Metrics row */}
    <div className="grid grid-cols-3 gap-2 pt-3.5 border-t border-slate-100">
      <div className="text-center">
        <p className="text-xs font-black text-[#172554] font-mono">{agent.reputation_score}</p>
        <p className="text-[10px] text-[#87909F] flex items-center justify-center gap-0.5 mt-0.5"><Star className="w-3 h-3 text-amber-500" />Rep</p>
      </div>
      <div className="text-center">
        <p className="text-xs font-black text-emerald-700 font-mono">{agent.tasks_completed}</p>
        <p className="text-[10px] text-[#87909F] flex items-center justify-center gap-0.5 mt-0.5"><CheckCircle2 className="w-3 h-3 text-emerald-600" />Done</p>
      </div>
      <div className="text-center">
        <p className="text-xs font-black text-amber-800 font-mono">{agent.wallet_balance.toFixed(0)}</p>
        <p className="text-[10px] text-[#87909F] flex items-center justify-center gap-0.5 mt-0.5"><Wallet className="w-3 h-3 text-amber-600" />AP</p>
      </div>
    </div>

    {/* Separate Footer Actions */}
    <div className="flex items-center justify-between pt-2 border-t border-slate-100">
      <button
        onClick={e => { e.stopPropagation(); onToggle(); }}
        disabled={toggling}
        className={`text-[11px] font-semibold px-3 py-1 rounded-lg border transition-all flex items-center gap-1.5 ${
          agent.is_active
            ? 'border-rose-200 text-rose-700 bg-rose-50 hover:bg-rose-100'
            : 'border-emerald-200 text-emerald-700 bg-emerald-50 hover:bg-emerald-100'
        } disabled:opacity-50 cursor-pointer`}
      >
        {toggling ? (
          <>
            <RefreshCw className="w-3 h-3 animate-spin" />
            <span>Updating...</span>
          </>
        ) : (
          <span>{agent.is_active ? 'Deactivate' : 'Activate'}</span>
        )}
      </button>

      <span className="text-xs font-semibold text-[#3155D9] flex items-center gap-1 hover:underline">
        <span>Inspect Node</span>
        <ChevronRight className="w-3.5 h-3.5" />
      </span>
    </div>
  </Interactive3DCard>
);

export const AgentsPage: React.FC<AgentsPageProps> = ({ onNavigate, onSelectAgent }) => {
  const [agents, setAgents] = useState<ApiAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('All');
  const [filterStatus, setFilterStatus] = useState('All');
  const [togglingId, setTogglingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: AgentFilterParams = {};
      if (filterType !== 'All') params.agent_type = filterType;
      if (filterStatus !== 'All') params.status = filterStatus;
      const data = await fetchAgents(params);
      setAgents(data);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  }, [filterType, filterStatus]);

  useEffect(() => { load(); }, [load]);

  const handleToggle = async (agent: ApiAgent) => {
    setTogglingId(agent.id);
    setError(null);
    try {
      const updated = agent.is_active
        ? await deactivateAgent(agent.id)
        : await activateAgent(agent.id);
      setAgents(prev => prev.map(a => a.id === updated.id ? updated : a));
    } catch (e: any) {
      setError(`Failed to update agent: ${e.message}`);
    } finally {
      setTogglingId(null);
    }
  };

  const filtered = agents.filter(a =>
    search === '' ||
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    a.agent_code.toLowerCase().includes(search.toLowerCase()) ||
    a.capabilities.some(c => c.toLowerCase().includes(search.toLowerCase()))
  );

  const stats = {
    total: agents.length,
    available: agents.filter(a => a.status === 'available').length,
    workers: agents.filter(a => a.agent_type === 'worker').length,
    verifiers: agents.filter(a => a.agent_type === 'verifier').length,
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-[#172554]">Agent Network</h1>
          <p className="text-[#596273] text-sm mt-1">Autonomous agents available across the AgentPay economy.</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={load}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-white border border-slate-200 text-[#596273] hover:text-[#18202F] hover:border-slate-300 transition-all shadow-sm cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
          <button
            onClick={() => onNavigate('create-agent')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-[#172554] via-[#1E3A8A] to-[#3155D9] text-white hover:brightness-110 transition-all shadow-md cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" /> Register Agent
          </button>
        </div>
      </div>

      {/* Compact Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-5">
        {[
          { label: 'Total Agents', value: stats.total, icon: <Users className="w-4 h-4" />, color: 'text-[#172554]' },
          { label: 'Available', value: stats.available, icon: <CheckCircle2 className="w-4 h-4" />, color: 'text-emerald-700' },
          { label: 'Workers', value: stats.workers, icon: <Cpu className="w-4 h-4" />, color: 'text-[#3155D9]' },
          { label: 'Verifiers', value: stats.verifiers, icon: <Award className="w-4 h-4" />, color: 'text-[#6D5BD0]' },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
            <div className={`flex items-center gap-2 mb-1.5 ${s.color}`}>
              {s.icon}
              <span className="text-xs font-semibold text-[#87909F] uppercase tracking-wider">{s.label}</span>
            </div>
            <p className="text-2xl font-black font-mono text-[#18202F]">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="glass-panel rounded-2xl border border-slate-200 p-4 flex flex-col sm:flex-row gap-3 shadow-sm">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#87909F]" />
          <input
            type="text"
            placeholder="Search agents by name, code, or capability…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-slate-50/80 border border-slate-200 rounded-xl text-sm text-[#18202F] placeholder-[#87909F] focus:outline-none focus:border-[#3155D9] focus:bg-white transition-colors"
          />
        </div>
        <div className="flex gap-2">
          <div className="relative">
            <Filter className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#87909F]" />
            <select
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
              className="pl-8 pr-4 py-2.5 bg-slate-50/80 border border-slate-200 rounded-xl text-xs text-[#18202F] focus:outline-none focus:border-[#3155D9] focus:bg-white cursor-pointer"
            >
              {['All', 'worker', 'verifier', 'orchestrator'].map(t => (
                <option key={t} value={t}>{t === 'All' ? 'All Types' : t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>
          <div className="relative">
            <Zap className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#87909F]" />
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              className="pl-8 pr-4 py-2.5 bg-slate-50/80 border border-slate-200 rounded-xl text-xs text-[#18202F] focus:outline-none focus:border-[#3155D9] focus:bg-white cursor-pointer"
            >
              {['All', 'available', 'busy', 'offline', 'suspended'].map(s => (
                <option key={s} value={s}>{s === 'All' ? 'All Status' : s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="bg-white border border-slate-200 rounded-2xl p-6 animate-pulse space-y-4 shadow-sm">
              <div className="flex justify-between">
                <div className="h-5 bg-slate-200 rounded w-28" />
                <div className="h-4 bg-slate-200 rounded w-16" />
              </div>
              <div className="h-4 bg-slate-100 rounded w-full" />
              <div className="h-4 bg-slate-100 rounded w-2/3" />
              <div className="pt-3 border-t border-slate-100 flex justify-between">
                <div className="h-4 bg-slate-200 rounded w-16" />
                <div className="h-4 bg-slate-200 rounded w-16" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filtered.length === 0 && (
        <div className="text-center py-24 flex flex-col items-center gap-4 bg-white rounded-3xl border border-slate-200 shadow-sm p-12">
          <div className="w-16 h-16 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center">
            <Cpu className="w-7 h-7 text-slate-500" />
          </div>
          <div>
            <p className="text-[#18202F] font-bold text-base">No agents match these filters.</p>
            <p className="text-[#596273] text-sm mt-1">Try adjusting your search query or filters.</p>
          </div>
          <button
            onClick={() => onNavigate('create-agent')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-[#172554] to-[#3155D9] text-white hover:brightness-110 transition-all shadow-sm cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" /> Register New Agent
          </button>
        </div>
      )}

      {/* Agent Cards Grid */}
      {!loading && !error && filtered.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onSelect={() => onSelectAgent(agent.id)}
              onToggle={() => handleToggle(agent)}
              toggling={togglingId === agent.id}
            />
          ))}
        </div>
      )}

    </div>
  );
};

export default AgentsPage;
