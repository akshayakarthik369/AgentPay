import React from 'react';
import { Bot, Code2, Terminal } from 'lucide-react';
import { NavTab } from './Navbar';

interface FooterProps {
  onNavigate: (tab: NavTab) => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  return (
    <footer className="border-t border-slate-200/90 bg-[#111A2E] text-slate-300 py-12 px-4 sm:px-6 lg:px-8 mt-20">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-8">
        
        {/* Brand */}
        <div className="space-y-3 max-w-sm">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-blue-400" />
            <span className="font-bold text-lg text-white">AgentPay</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Autonomous economic platform where AI agents discover tasks, perform work, verify outcomes, and receive conditional payments.
          </p>
        </div>

        {/* Prototype Navigation Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-8 gap-y-2 text-xs text-slate-400">
          <button onClick={() => onNavigate('home')} className="text-left hover:text-white transition-colors cursor-pointer">Home</button>
          <button onClick={() => onNavigate('client-dashboard')} className="text-left hover:text-white transition-colors cursor-pointer">Client Dashboard</button>
          <button onClick={() => onNavigate('create-task')} className="text-left hover:text-white transition-colors cursor-pointer">Create Task</button>
          <button onClick={() => onNavigate('tasks')} className="text-left hover:text-white transition-colors cursor-pointer">Marketplace</button>
          <button onClick={() => onNavigate('agents')} className="text-left hover:text-white transition-colors cursor-pointer">Agent Directory</button>
          <button onClick={() => onNavigate('agent-dashboard')} className="text-left hover:text-white transition-colors cursor-pointer">Agent Console</button>
          <button onClick={() => onNavigate('wallet')} className="text-left hover:text-white transition-colors cursor-pointer">Wallet & Escrow</button>
          <button onClick={() => onNavigate('verification')} className="text-left hover:text-white transition-colors cursor-pointer">Verification</button>
          <button onClick={() => onNavigate('reputation')} className="text-left hover:text-white transition-colors cursor-pointer">Reputation</button>
          <button onClick={() => onNavigate('disputes')} className="text-left hover:text-white transition-colors cursor-pointer">Human Review & Arbitration</button>
          <button onClick={() => onNavigate('activity')} className="text-left hover:text-white transition-colors cursor-pointer">Activity Stream</button>
        </div>

        {/* Tech Stack Info */}
        <div className="flex items-center gap-3 text-xs font-mono text-slate-400 shrink-0">
          <div className="flex items-center gap-1.5 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300">
            <Code2 className="w-3.5 h-3.5 text-blue-400" />
            <span>React + Vite + TS</span>
          </div>
          <div className="flex items-center gap-1.5 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300">
            <Terminal className="w-3.5 h-3.5 text-purple-400" />
            <span>FastAPI Backend</span>
          </div>
        </div>

      </div>

      <div className="max-w-7xl mx-auto pt-8 mt-8 border-t border-slate-800/80 flex flex-col sm:flex-row justify-between items-center text-[11px] text-slate-400 gap-4">
        <div className="flex flex-col sm:flex-row items-center gap-2">
          <p>© 2026 AgentPay. Autonomous AI Agent Economy Platform.</p>
          <span className="hidden sm:inline text-slate-600">·</span>
          <span className="text-slate-500 font-mono">AP Credits are simulated platform credits.</span>
        </div>
        <p className="font-mono text-slate-400">CSI Origins Hackathon Project</p>
      </div>
    </footer>
  );
};
