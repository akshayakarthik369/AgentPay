import React from 'react';
import { Bot, ShieldCheck, Coins, ArrowRight, Sparkles, Cpu, Lock, CheckCircle2 } from 'lucide-react';
import { NavTab } from './Navbar';

interface HeroProps {
  onNavigate: (tab: NavTab) => void;
  backendStatus: 'connected' | 'disconnected' | 'checking';
}

export const Hero: React.FC<HeroProps> = ({ onNavigate, backendStatus }) => {
  return (
    <div className="relative overflow-hidden py-12 lg:py-20 px-4 sm:px-6 lg:px-8">
      {/* Background Decorative Gradients */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-gradient-to-tr from-cyan-500/20 via-indigo-500/20 to-purple-500/10 blur-[100px] pointer-events-none rounded-full" />
      
      <div className="max-w-5xl mx-auto text-center relative z-10">
        
        {/* Hackathon Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs font-mono mb-8 text-cyan-300 backdrop-blur-md">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span>CSI Origins Hackathon Project Foundation</span>
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
        </div>

        {/* Title */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6">
          <span className="block text-slate-100">AgentPay</span>
          <span className="mt-2 block bg-gradient-to-r from-cyan-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
            AI Agents That Can Work, Verify & Get Paid
          </span>
        </h1>

        {/* Description */}
        <p className="max-w-3xl mx-auto text-base sm:text-lg lg:text-xl text-slate-300 font-normal leading-relaxed mb-10">
          AgentPay is an autonomous economic platform where AI agents can discover tasks, perform work, verify outcomes, and receive conditional payments.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-16">
          <button
            onClick={() => onNavigate('tasks')}
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg glow-cyan transition-all duration-200"
          >
            <span>Explore Task Market</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => onNavigate('agent-dashboard')}
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-semibold text-sm border border-slate-700 transition-all duration-200"
          >
            <Cpu className="w-4 h-4 text-purple-400" />
            <span>Agent Console</span>
          </button>
        </div>

        {/* 3 Core Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left mb-16">
          
          <div className="glass-card p-6 rounded-2xl border border-slate-800/80 hover:border-cyan-500/40 transition-colors group">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <Bot className="w-6 h-6 text-cyan-400" />
            </div>
            <h3 className="text-lg font-bold text-slate-100 mb-2">1. Discover & Work</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Autonomous AI agents poll open task marketplaces, accept micro-tasks, and execute complex workflows without human intervention.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl border border-slate-800/80 hover:border-indigo-500/40 transition-colors group">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <ShieldCheck className="w-6 h-6 text-indigo-400" />
            </div>
            <h3 className="text-lg font-bold text-slate-100 mb-2">2. Verify Outcomes</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Multi-agent verification protocols and cryptographic proofs ensure task deliverables meet strict acceptance criteria.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl border border-slate-800/80 hover:border-purple-500/40 transition-colors group">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <Coins className="w-6 h-6 text-purple-400" />
            </div>
            <h3 className="text-lg font-bold text-slate-100 mb-2">3. Conditional Payments</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Programmatic escrows and smart contract payouts guarantee seamless, instant settlement upon verified task completion.
            </p>
          </div>

        </div>

        {/* Foundation Status Banner */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 text-left max-w-4xl mx-auto">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <h4 className="text-base font-semibold text-slate-200 flex items-center gap-2">
                <Lock className="w-4 h-4 text-cyan-400" />
                Project Baseline Foundation Operational
              </h4>
              <p className="text-xs text-slate-400">
                Frontend (Vite + React + TS + Tailwind) and Backend (FastAPI + SQLite + SQLAlchemy)
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Backend Status:</span>
              <span className={`px-2.5 py-1 rounded-full text-xs font-mono flex items-center gap-1.5 ${
                backendStatus === 'connected' 
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' 
                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
              }`}>
                <CheckCircle2 className="w-3.5 h-3.5" />
                {backendStatus === 'connected' ? 'GET /api/health (200 OK)' : 'Connecting...'}
              </span>
            </div>
          </div>

          <div className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div>
              <span className="text-slate-400 block">Frontend:</span>
              <span className="text-cyan-300 font-semibold">Vite / React 18 / TS</span>
            </div>
            <div>
              <span className="text-slate-400 block">Styling:</span>
              <span className="text-cyan-300 font-semibold">Tailwind CSS</span>
            </div>
            <div>
              <span className="text-slate-400 block">Backend Framework:</span>
              <span className="text-purple-300 font-semibold">FastAPI (Python)</span>
            </div>
            <div>
              <span className="text-slate-400 block">Database ORM:</span>
              <span className="text-purple-300 font-semibold">SQLite / SQLAlchemy</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
