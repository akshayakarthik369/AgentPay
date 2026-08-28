import React from 'react';
import { mockReputationEvents, mockWorkerAgent } from '../mock/demoData';
import { NavTab } from '../components/Navbar';
import { 
  Award, 
  ShieldCheck, 
  Bot, 
  TrendingUp, 
  TrendingDown, 
  CheckCircle2, 
  Clock, 
  Percent, 
  Sparkles 
} from 'lucide-react';

interface ReputationPageProps {
  onNavigate: (tab: NavTab) => void;
}

export const ReputationPage: React.FC<ReputationPageProps> = () => {
  const agent = mockWorkerAgent;

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6">
      
      {/* Header */}
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 text-xs font-mono mb-2">
          <Award className="w-3.5 h-3.5" />
          <span>Agent Credibility Protocol</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-[#172554]">Agent Reputation Score</h1>
        <p className="text-sm text-[#596273] mt-1">
          Cryptographically signed on-chain reputation history based on verified task quality outcomes.
        </p>
      </div>

      {/* Main Agent Profile & Score Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200 mb-8 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-yellow-500 via-amber-500 to-cyan-500 p-0.5 glow-cyan shrink-0">
              <div className="w-full h-full bg-[#F7F8FA] rounded-[14px] flex items-center justify-center">
                <Bot className="w-9 h-9 text-yellow-400" />
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-extrabold text-[#172554]">{agent.name}</h2>
              <p className="text-xs text-[#334155] mt-0.5">{agent.role}</p>

              {/* Trust Labels Badges */}
              <div className="flex flex-wrap items-center gap-2 mt-3">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 flex items-center gap-1">
                  <Award className="w-3 h-3" />
                  Trusted Agent
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-blue-50 text-[#3155D9] border border-blue-200 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" />
                  High Reliability
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Verified Worker
                </span>
              </div>
            </div>
          </div>

          {/* Large Score Display */}
          <div className="p-6 rounded-2xl bg-white border border-yellow-500/30 text-center shrink-0">
            <span className="text-xs font-mono uppercase text-[#596273] block mb-1">Overall Reputation</span>
            <div className="text-5xl font-extrabold text-yellow-400 font-mono">{agent.reputation}</div>
            <span className="text-xs font-mono text-[#596273] mt-1 block">out of 100 max</span>
          </div>
        </div>
      </div>

      {/* Metrics Breakdown Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-8">
        <div className="glass-card p-5 rounded-2xl border border-slate-200">
          <span className="text-[11px] font-mono text-[#596273] uppercase block mb-1">Success Rate</span>
          <div className="text-2xl font-extrabold text-emerald-700 font-mono">96%</div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-200">
          <span className="text-[11px] font-mono text-[#596273] uppercase block mb-1">Avg Quality</span>
          <div className="text-2xl font-extrabold text-[#3155D9] font-mono">93%</div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-200">
          <span className="text-[11px] font-mono text-[#596273] uppercase block mb-1">Reliability Score</span>
          <div className="text-2xl font-extrabold text-[#172554] font-mono">95%</div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-200">
          <span className="text-[11px] font-mono text-[#596273] uppercase block mb-1">Dispute Rate</span>
          <div className="text-2xl font-extrabold text-amber-700 font-mono">2%</div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-200 col-span-2 sm:col-span-1">
          <span className="text-[11px] font-mono text-[#596273] uppercase block mb-1">Tasks Completed</span>
          <div className="text-2xl font-extrabold text-[#6D5BD0] font-mono">27</div>
        </div>
      </div>

      {/* Reputation History Table */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200">
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200">
          <div>
            <h3 className="text-lg font-bold text-[#18202F] flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-yellow-400" />
              Reputation Change History
            </h3>
            <p className="text-xs text-[#596273] mt-0.5">Audit log of score adjustments from verified task executions</p>
          </div>
        </div>

        <div className="space-y-3">
          {mockReputationEvents.map((evt) => (
            <div key={evt.id} className="glass-card p-4 rounded-xl border border-slate-200 flex items-center justify-between font-mono text-xs">
              <div className="flex items-center gap-4">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-sm ${
                  evt.change > 0
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border border-rose-200'
                }`}>
                  {evt.change > 0 ? `+${evt.change}` : evt.change}
                </div>
                <div>
                  <h4 className="font-bold text-[#18202F] font-sans text-sm">{evt.taskTitle}</h4>
                  <p className="text-[11px] text-[#596273] font-sans">{evt.reason}</p>
                </div>
              </div>
              <span className="text-[#596273] text-xs shrink-0 ml-4">{evt.date}</span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
