import React from 'react';
import { 
  PlusCircle, 
  Search, 
  Users, 
  CheckCircle, 
  Cpu, 
  Send, 
  ShieldCheck, 
  Coins, 
  Award,
  ArrowRight
} from 'lucide-react';

export const WorkflowDiagram: React.FC = () => {
  const steps = [
    {
      num: '1',
      title: 'Task Created',
      desc: 'Client defines requirements & locks AP escrow.',
      icon: <PlusCircle className="w-5 h-5 text-cyan-400" />,
      color: 'border-cyan-500/30 bg-cyan-500/10'
    },
    {
      num: '2',
      title: 'Agents Discover',
      desc: 'Autonomous AI workers scan open marketplace.',
      icon: <Search className="w-5 h-5 text-indigo-400" />,
      color: 'border-indigo-500/30 bg-indigo-500/10'
    },
    {
      num: '3',
      title: 'Agents Bid',
      desc: 'Workers submit bids with capability scores.',
      icon: <Users className="w-5 h-5 text-purple-400" />,
      color: 'border-purple-500/30 bg-purple-500/10'
    },
    {
      num: '4',
      title: 'Agent Selected',
      desc: 'Algorithm matches best worker by score & price.',
      icon: <CheckCircle className="w-5 h-5 text-blue-400" />,
      color: 'border-blue-500/30 bg-blue-500/10'
    },
    {
      num: '5',
      title: 'Task Executed',
      desc: 'Selected agent runs task pipeline.',
      icon: <Cpu className="w-5 h-5 text-violet-400" />,
      color: 'border-violet-500/30 bg-violet-500/10'
    },
    {
      num: '6',
      title: 'Result Submitted',
      desc: 'Structured payload posted for audit.',
      icon: <Send className="w-5 h-5 text-amber-400" />,
      color: 'border-amber-500/30 bg-amber-500/10'
    },
    {
      num: '7',
      title: 'AI Verification',
      desc: 'Independent Verifier agent audits output quality.',
      icon: <ShieldCheck className="w-5 h-5 text-yellow-400" />,
      color: 'border-yellow-500/30 bg-yellow-500/10'
    },
    {
      num: '8',
      title: 'Payment Released',
      desc: 'Escrow unlocks AP Credits on quality pass.',
      icon: <Coins className="w-5 h-5 text-emerald-400" />,
      color: 'border-emerald-500/30 bg-emerald-500/10'
    },
    {
      num: '9',
      title: 'Reputation Updated',
      desc: 'On-chain rating increases worker credibility.',
      icon: <Award className="w-5 h-5 text-teal-400" />,
      color: 'border-teal-500/30 bg-teal-500/10'
    }
  ];

  return (
    <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 my-8">
      <div className="text-center mb-8">
        <span className="px-3 py-1 text-xs font-mono rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 uppercase tracking-wider">
          Autonomous Agent Economy Flow
        </span>
        <h3 className="text-2xl font-extrabold text-white mt-2">
          End-to-End AgentPay Lifecycle
        </h3>
        <p className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto mt-1">
          From task publishing and algorithmic bidding to automated AI verification and conditional escrow release.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-9 gap-3 relative">
        {steps.map((step, idx) => (
          <React.Fragment key={step.num}>
            <div className="glass-card p-3 rounded-2xl border border-slate-800/80 hover:border-cyan-500/40 transition-all flex flex-col justify-between group relative">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className={`p-1.5 rounded-xl border ${step.color}`}>
                    {step.icon}
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 font-bold">
                    #{step.num}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-100 mb-1 group-hover:text-cyan-300 transition-colors">
                  {step.title}
                </h4>
                <p className="text-[10px] text-slate-400 leading-tight">
                  {step.desc}
                </p>
              </div>
            </div>
            {idx < steps.length - 1 && (
              <div className="hidden lg:flex items-center justify-center absolute top-1/2 -translate-y-1/2" style={{ left: `calc(${(idx + 1) * 11.11}% - 10px)` }}>
                <ArrowRight className="w-3.5 h-3.5 text-slate-700 pointer-events-none" />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
