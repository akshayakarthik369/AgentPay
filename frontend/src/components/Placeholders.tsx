import React from 'react';
import { LayoutDashboard, Cpu, Briefcase, Wallet, ShieldAlert, Clock, Layers, ArrowLeft } from 'lucide-react';
import { NavTab } from './Navbar';

interface PlaceholderProps {
  tab: NavTab;
  onBackToHome: () => void;
}

export const Placeholders: React.FC<PlaceholderProps> = ({ tab, onBackToHome }) => {
  const getTabDetails = () => {
    switch (tab) {
      case 'client-dashboard':
        return {
          title: 'Client Dashboard',
          subtitle: 'Create tasks, set escrow funds, and monitor AI agent performance.',
          icon: <LayoutDashboard className="w-8 h-8 text-cyan-400" />,
          color: 'cyan',
          modules: ['Task Creation Wizard', 'Active Escrows Summary', 'Agent Ratings', 'Outcome Verification']
        };
      case 'agent-dashboard':
        return {
          title: 'Agent Dashboard',
          subtitle: 'Register autonomous agents, manage API keys, and monitor active jobs.',
          icon: <Cpu className="w-8 h-8 text-purple-400" />,
          color: 'purple',
          modules: ['Agent Identity Keys', 'Job Queue Poller', 'Performance Metrics', 'Payout History']
        };
      case 'tasks':
        return {
          title: 'Task Marketplace',
          subtitle: 'Browse and discover open micro-tasks available for AI agent execution.',
          icon: <Briefcase className="w-8 h-8 text-indigo-400" />,
          color: 'indigo',
          modules: ['Open Task Feed', 'Reward Filters', 'Execution Constraints', 'Submission Protocols']
        };
      case 'wallet':
        return {
          title: 'AgentPay Wallet',
          subtitle: 'Manage programmatic escrow balances, micro-transactions, and withdrawals.',
          icon: <Wallet className="w-8 h-8 text-emerald-400" />,
          color: 'emerald',
          modules: ['Escrow Balance', 'Pending Settlements', 'Transaction Ledger', 'Withdrawal Gateway']
        };
      case 'disputes':
        return {
          title: 'Dispute Resolution System',
          subtitle: 'Arbitrate contested work outcomes with multi-agent consensus verification.',
          icon: <ShieldAlert className="w-8 h-8 text-amber-400" />,
          color: 'amber',
          modules: ['Active Claims', 'Evidence Submission', 'Arbitration Panel', 'Refund Escrow']
        };
      default:
        return {
          title: 'Section Overview',
          subtitle: 'Module initialized.',
          icon: <Layers className="w-8 h-8 text-slate-400" />,
          color: 'slate',
          modules: ['Module Foundation']
        };
    }
  };

  const details = getTabDetails();

  return (
    <div className="max-w-5xl mx-auto py-10 px-4 sm:px-6">
      
      {/* Back button */}
      <button
        onClick={onBackToHome}
        className="flex items-center gap-2 text-xs font-mono text-slate-400 hover:text-cyan-400 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to Home</span>
      </button>

      {/* Main Container */}
      <div className="glass-panel p-8 sm:p-12 rounded-3xl border border-slate-800 relative overflow-hidden">
        
        {/* Decorative Badge */}
        <div className="flex items-center justify-between mb-8 pb-6 border-b border-slate-800/80">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800">
              {details.icon}
            </div>
            <div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white">{details.title}</h2>
              <p className="text-sm text-slate-400 mt-1">{details.subtitle}</p>
            </div>
          </div>
          <span className="px-3 py-1 text-xs font-mono rounded-full bg-slate-900 text-slate-400 border border-slate-800 flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>Placeholder View</span>
          </span>
        </div>

        {/* Info Grid */}
        <div className="mb-8">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-4">
            Upcoming Modules in Future Iterations:
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {details.modules.map((mod, idx) => (
              <div key={idx} className="glass-card p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                <span className="text-sm font-medium text-slate-200">{mod}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                  Planned
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Foundation Notice */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 text-xs text-slate-400 flex items-center gap-3">
          <Layers className="w-5 h-5 text-cyan-400 shrink-0" />
          <span>
            This page placeholder verifies routing and navigation structure for <strong>AgentPay</strong> baseline foundation.
          </span>
        </div>

      </div>
    </div>
  );
};
