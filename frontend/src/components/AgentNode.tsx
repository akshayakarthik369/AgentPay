import React from 'react';
import { Bot, ShieldCheck, Cpu, Zap, Activity } from 'lucide-react';
import { DepthIcon } from './DepthIcon';

export interface AgentNodeProps {
  name: string;
  code?: string;
  agentType?: 'worker' | 'verifier' | 'orchestrator' | 'client';
  status?: 'available' | 'busy' | 'offline' | 'suspended';
  reputation?: number;
  capabilities?: string[];
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
  className?: string;
  onClick?: () => void;
}

export const AgentNode: React.FC<AgentNodeProps> = ({
  name,
  code,
  agentType = 'worker',
  status = 'available',
  reputation,
  capabilities = [],
  size = 'md',
  showDetails = false,
  className = '',
  onClick,
}) => {
  const getTheme = () => {
    switch (agentType) {
      case 'verifier':
        return {
          color: 'violet' as const,
          icon: <ShieldCheck className="w-5 h-5 text-[#6D5BD0]" />,
          ringColor: 'border-purple-300',
          orbitColor: 'bg-[#6D5BD0]',
          badgeBg: 'bg-purple-50 text-purple-700 border-purple-200',
          titleColor: 'text-[#6D5BD0]',
        };
      case 'client':
        return {
          color: 'emerald' as const,
          icon: <Zap className="w-5 h-5 text-emerald-600" />,
          ringColor: 'border-emerald-300',
          orbitColor: 'bg-emerald-500',
          badgeBg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          titleColor: 'text-emerald-700',
        };
      case 'orchestrator':
        return {
          color: 'navy' as const,
          icon: <Activity className="w-5 h-5 text-[#172554]" />,
          ringColor: 'border-blue-300',
          orbitColor: 'bg-[#172554]',
          badgeBg: 'bg-blue-50 text-blue-800 border-blue-200',
          titleColor: 'text-[#172554]',
        };
      case 'worker':
      default:
        return {
          color: 'blue' as const,
          icon: <Cpu className="w-5 h-5 text-[#3155D9]" />,
          ringColor: 'border-blue-300',
          orbitColor: 'bg-[#3155D9]',
          badgeBg: 'bg-blue-50 text-blue-700 border-blue-200',
          titleColor: 'text-[#3155D9]',
        };
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'busy':
        return 'bg-amber-500 ring-amber-400/30';
      case 'offline':
        return 'bg-slate-400 ring-slate-300';
      case 'suspended':
        return 'bg-rose-500 ring-rose-300';
      case 'available':
      default:
        return 'bg-emerald-500 ring-emerald-400/30';
    }
  };

  const theme = getTheme();

  return (
    <div
      onClick={onClick}
      className={`inline-flex items-center gap-3 group/node min-w-0 ${onClick ? 'cursor-pointer' : ''} ${className}`}
    >
      {/* Node Core: Central 3D Icon + Outer Pulsing Ring */}
      <div className="relative flex items-center justify-center shrink-0">
        {/* Outer Orbit / Status Ring */}
        <div
          className={`absolute -inset-1.5 rounded-full border border-dashed ${theme.ringColor} animate-spin-slow opacity-60 group-hover/node:opacity-100 group-hover/node:scale-105 transition-all duration-300`}
          style={{ animationDuration: '20s' }}
        />

        {/* Orbiting Capability Satellite Dot */}
        <div
          className={`absolute -top-1 right-0 w-2 h-2 rounded-full ${theme.orbitColor} shadow-sm animate-pulse-subtle`}
        />

        {/* Depth Icon Core */}
        <DepthIcon
          icon={theme.icon}
          color={theme.color}
          size={size === 'lg' ? 'lg' : size === 'sm' ? 'sm' : 'md'}
          animateHover
        />

        {/* Status indicator dot */}
        <span
          className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white ring-2 ${getStatusColor()}`}
        />
      </div>

      {/* Node Meta Details */}
      {showDetails && (
        <div className="space-y-0.5 min-w-0 flex-1 overflow-hidden">
          <div className="flex items-center gap-1.5 flex-wrap min-w-0">
            <span className="font-bold text-[#18202F] text-sm truncate group-hover/node:text-blue-700 transition-colors">
              {name}
            </span>
            {code && (
              <span className="font-mono text-[10px] px-1.5 py-0.5 bg-slate-100 border border-slate-200 text-[#596273] rounded shrink-0">
                {code}
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5 text-[11px] font-mono text-[#596273] flex-wrap">
            <span className="capitalize">{agentType}</span>
            {reputation !== undefined && (
              <>
                <span className="text-slate-300">•</span>
                <span className="text-[#3155D9] font-semibold">Rep: {reputation}/100</span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
