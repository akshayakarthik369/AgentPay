import React, { useState } from 'react';
import { 
  Bot, 
  LayoutDashboard, 
  PlusCircle, 
  Briefcase, 
  Cpu, 
  Wallet, 
  ShieldCheck, 
  Award, 
  ShieldAlert, 
  Menu, 
  X, 
  CheckCircle2, 
  XCircle, 
  RefreshCw,
  Users
} from 'lucide-react';

import { DepthIcon } from './DepthIcon';

export type NavTab = 
  | 'home' 
  | 'client-dashboard' 
  | 'create-task' 
  | 'tasks' 
  | 'task-details'
  | 'agents'
  | 'create-agent'
  | 'agent-details'
  | 'agent-dashboard' 
  | 'execution'
  | 'submission-details'
  | 'verification' 
  | 'verification-details'
  | 'settlement-details'
  | 'wallet' 
  | 'reputation' 
  | 'disputes';

interface NavbarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  backendStatus: 'connected' | 'disconnected' | 'checking';
  onRefreshHealth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  backendStatus,
  onRefreshHealth
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'home',             label: 'Home',          icon: <Bot className="w-3.5 h-3.5" /> },
    { id: 'client-dashboard', label: 'Dashboard',     icon: <LayoutDashboard className="w-3.5 h-3.5" /> },
    { id: 'create-task',      label: 'Create Task',   icon: <PlusCircle className="w-3.5 h-3.5" /> },
    { id: 'tasks',            label: 'Marketplace',   icon: <Briefcase className="w-3.5 h-3.5" /> },
    { id: 'agents',           label: 'Agents',        icon: <Users className="w-3.5 h-3.5" /> },
    { id: 'agent-dashboard',  label: 'Agent Console', icon: <Cpu className="w-3.5 h-3.5" /> },
    { id: 'wallet',           label: 'Wallet',        icon: <Wallet className="w-3.5 h-3.5" /> },
    { id: 'verification',     label: 'Verification',  icon: <ShieldCheck className="w-3.5 h-3.5" /> },
    { id: 'reputation',       label: 'Reputation',    icon: <Award className="w-3.5 h-3.5" /> },
    { id: 'disputes',         label: 'Disputes',      icon: <ShieldAlert className="w-3.5 h-3.5" /> },
  ];

  const handleNavClick = (tab: NavTab) => {
    setActiveTab(tab);
    setMobileMenuOpen(false);
  };

  const isActiveTab = (id: NavTab) =>
    activeTab === id ||
    (activeTab === 'task-details'         && id === 'tasks') ||
    (activeTab === 'create-agent'         && id === 'agents') ||
    (activeTab === 'agent-details'        && id === 'agents') ||
    ((activeTab === 'execution' || activeTab === 'submission-details') && id === 'agent-dashboard') ||
    (activeTab === 'verification-details' && id === 'verification');

  return (
    <header className="sticky top-0 z-50 bg-[#111A2E] text-slate-100 border-b border-slate-800/80 px-4 lg:px-8 py-0 shadow-md">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 h-16">
        
        {/* Brand Logo with Subtitle */}
        <div
          className="flex items-center gap-3 cursor-pointer shrink-0 group"
          onClick={() => handleNavClick('home')}
        >
          <DepthIcon
            icon={<Bot className="w-4 h-4 text-blue-400" />}
            color="blue"
            size="sm"
          />
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-tight text-white group-hover:text-blue-300 transition">
                AgentPay
              </span>
              <span className="px-1.5 py-0.2 text-[9px] font-mono tracking-wider font-semibold uppercase bg-blue-500/20 text-blue-300 border border-blue-500/30 rounded">
                PROT
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono tracking-tight hidden sm:inline">
              Agent Economy Infrastructure
            </span>
          </div>
        </div>

        {/* Desktop Navigation — refined midnight navbar */}
        <nav className="hidden lg:flex items-center h-full gap-0.5">
          {navItems.map((item) => {
            const active = isActiveTab(item.id);
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`relative flex items-center gap-1.5 px-3 h-full text-xs font-medium transition-all duration-200 whitespace-nowrap ${
                  active
                    ? 'text-white bg-slate-800/60 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`}
              >
                <span className={active ? 'text-blue-400' : 'text-slate-400'}>{item.icon}</span>
                <span>{item.label}</span>
                {active && (
                  <span className="absolute bottom-0 left-2 right-2 h-[2px] bg-[#3155D9] rounded-t-full" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Section */}
        <div className="flex items-center gap-3 shrink-0">
          <div
            onClick={onRefreshHealth}
            title="FastAPI Backend Health"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono bg-slate-900 border border-slate-800 cursor-pointer hover:border-slate-700 transition-colors"
          >
            <span className="text-slate-400 hidden sm:inline text-[10px]">API</span>
            {backendStatus === 'connected' && (
              <div className="flex items-center gap-1 text-emerald-400 font-semibold">
                <CheckCircle2 className="w-3 h-3" />
                <span className="text-[10px]">OK</span>
              </div>
            )}
            {backendStatus === 'disconnected' && (
              <div className="flex items-center gap-1 text-rose-400 font-semibold">
                <XCircle className="w-3 h-3" />
                <span className="text-[10px]">Off</span>
              </div>
            )}
            {backendStatus === 'checking' && (
              <div className="flex items-center gap-1 text-amber-400">
                <RefreshCw className="w-3 h-3 animate-spin" />
              </div>
            )}
          </div>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
            aria-label="Toggle navigation"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-800 py-2 px-2 space-y-0.5 bg-[#0F172A]">
          {navItems.map((item) => {
            const active = isActiveTab(item.id);
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? 'bg-slate-800 text-blue-400 border-l-2 border-blue-500 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};
