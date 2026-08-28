import React from 'react';
import { TaskStatus } from '../types';
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  XCircle, 
  Cpu, 
  Send, 
  ShieldCheck, 
  Coins, 
  ShieldAlert, 
  Users,
  Gavel
} from 'lucide-react';

interface StatusBadgeProps {
  status: TaskStatus;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'px-2 py-0.5 text-[10px] gap-1';
      case 'lg':
        return 'px-3.5 py-1.5 text-sm gap-2 font-semibold';
      case 'md':
      default:
        return 'px-2.5 py-1 text-xs gap-1.5 font-medium';
    }
  };

  const getStatusConfig = () => {
    switch (status) {
      case 'Open':
        return {
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          icon: <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-600" />
        };
      case 'Bidding':
        return {
          bg: 'bg-blue-50 text-blue-700 border-blue-200',
          icon: <Users className="w-3.5 h-3.5 shrink-0 text-blue-600" />
        };
      case 'Assigned':
        return {
          bg: 'bg-indigo-50 text-indigo-700 border-indigo-200',
          icon: <Cpu className="w-3.5 h-3.5 shrink-0 text-indigo-600" />
        };
      case 'Executing':
        return {
          bg: 'bg-purple-50 text-purple-700 border-purple-200',
          icon: <Clock className="w-3.5 h-3.5 shrink-0 animate-spin text-purple-600" />
        };
      case 'Submitted':
        return {
          bg: 'bg-sky-50 text-sky-700 border-sky-200',
          icon: <Send className="w-3.5 h-3.5 shrink-0 text-sky-600" />
        };
      case 'Verifying':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          icon: <ShieldCheck className="w-3.5 h-3.5 shrink-0 animate-pulse text-amber-600" />
        };
      case 'Verified':
      case 'Payment Released':
        return {
          bg: 'bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold',
          icon: <Coins className="w-3.5 h-3.5 shrink-0 text-emerald-600" />
        };
      case 'Failed':
        return {
          bg: 'bg-rose-50 text-rose-700 border-rose-200',
          icon: <XCircle className="w-3.5 h-3.5 shrink-0 text-rose-600" />
        };
      case 'Disputed':
        return {
          bg: 'bg-orange-50 text-orange-700 border-orange-200',
          icon: <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-orange-600" />
        };
      case 'Review Required':
        return {
          bg: 'bg-amber-50 text-amber-800 border-amber-400 font-semibold',
          icon: <Gavel className="w-3.5 h-3.5 shrink-0 text-amber-700 animate-pulse" />
        };
      default:
        return {
          bg: 'bg-slate-100 text-slate-700 border-slate-200',
          icon: <AlertCircle className="w-3.5 h-3.5 shrink-0 text-slate-500" />
        };
    }
  };

  const config = getStatusConfig();

  return (
    <span className={`inline-flex items-center rounded-full font-mono border ${config.bg} ${getSizeClasses()}`}>
      {config.icon}
      <span>{status}</span>
    </span>
  );
};
