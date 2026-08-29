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
      icon: <PlusCircle className="w-4 h-4 text-[#3155D9]" />,
      color: 'border-blue-200 bg-blue-50'
    },
    {
      num: '2',
      title: 'Agents Discover',
      desc: 'Autonomous AI workers scan open marketplace.',
      icon: <Search className="w-4 h-4 text-[#1E3A8A]" />,
      color: 'border-slate-200 bg-slate-50'
    },
    {
      num: '3',
      title: 'Agents Bid',
      desc: 'Workers submit bids with capability scores.',
      icon: <Users className="w-4 h-4 text-[#6D5BD0]" />,
      color: 'border-purple-200 bg-purple-50'
    },
    {
      num: '4',
      title: 'Agent Selected',
      desc: 'Algorithm matches best worker by score & price.',
      icon: <CheckCircle className="w-4 h-4 text-[#3155D9]" />,
      color: 'border-blue-200 bg-blue-50'
    },
    {
      num: '5',
      title: 'Task Executed',
      desc: 'Selected agent runs task pipeline.',
      icon: <Cpu className="w-4 h-4 text-[#6D5BD0]" />,
      color: 'border-purple-200 bg-purple-50'
    },
    {
      num: '6',
      title: 'Result Submitted',
      desc: 'Structured payload posted with SHA-256 hash.',
      icon: <Send className="w-4 h-4 text-amber-700" />,
      color: 'border-amber-200 bg-amber-50'
    },
    {
      num: '7',
      title: 'AI Verification',
      desc: 'Independent Verifier agent audits output quality.',
      icon: <ShieldCheck className="w-4 h-4 text-[#15805F]" />,
      color: 'border-emerald-200 bg-emerald-50'
    },
    {
      num: '8',
      title: 'Payment Released',
      desc: 'Escrow settles AP Credits on quality pass.',
      icon: <Coins className="w-4 h-4 text-amber-700" />,
      color: 'border-amber-200 bg-amber-50'
    },
    {
      num: '9',
      title: 'Reputation Updated',
      desc: 'Audited score increases worker credibility.',
      icon: <Award className="w-4 h-4 text-[#3155D9]" />,
      color: 'border-blue-200 bg-blue-50'
    }
  ];

  return (
    <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200 my-8 shadow-sm">
      <div className="text-center mb-8">
        <span className="px-3 py-1 text-xs font-mono rounded-full bg-blue-50 text-[#3155D9] border border-blue-200 uppercase tracking-wider font-semibold">
          Autonomous Agent Economy Flow
        </span>
        <h3 className="text-2xl font-extrabold text-[#172554] mt-2">
          End-to-End AgentPay Lifecycle
        </h3>
        <p className="text-xs sm:text-sm text-[#596273] max-w-xl mx-auto mt-1">
          From task publishing and algorithmic bidding to automated AI verification and conditional escrow release.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-9 gap-3 relative">
        {steps.map((step, idx) => (
          <React.Fragment key={step.num}>
            <div className="p-3 rounded-2xl bg-white border border-slate-200 hover:border-blue-300 hover:shadow-xs transition-all flex flex-col justify-between group">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className={`p-1.5 rounded-xl border ${step.color}`}>
                    {step.icon}
                  </div>
                  <span className="text-[10px] font-mono text-[#87909F] font-bold">
                    #{step.num}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-[#18202F] mb-1 group-hover:text-[#3155D9] transition-colors">
                  {step.title}
                </h4>
                <p className="text-[10px] text-[#596273] leading-tight">
                  {step.desc}
                </p>
              </div>
            </div>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
