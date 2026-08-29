import React from 'react';
import {
  ShieldCheck, ShieldOff, ShieldAlert, Clock, CheckCircle2, XCircle, Loader2
} from 'lucide-react';

const TRUST_CONFIGS: Record<string, {
  label: string;
  icon: React.ReactNode;
  bg: string;
  border: string;
  text: string;
  dot: string;
}> = {
  trusted: {
    label: 'Trusted',
    icon: <ShieldCheck className="w-3.5 h-3.5" />,
    bg: 'bg-emerald-50',
    border: 'border-emerald-300',
    text: 'text-emerald-800',
    dot: 'bg-emerald-500',
  },
  provisional: {
    label: 'Provisional',
    icon: <ShieldAlert className="w-3.5 h-3.5" />,
    bg: 'bg-amber-50',
    border: 'border-amber-300',
    text: 'text-amber-800',
    dot: 'bg-amber-500',
  },
  pending_canary: {
    label: 'Canary Required',
    icon: <Clock className="w-3.5 h-3.5" />,
    bg: 'bg-sky-50',
    border: 'border-sky-300',
    text: 'text-sky-800',
    dot: 'bg-sky-500',
  },
  canary_testing: {
    label: 'Canary Testing',
    icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
    bg: 'bg-violet-50',
    border: 'border-violet-300',
    text: 'text-violet-800',
    dot: 'bg-violet-500',
  },
  canary_failed: {
    label: 'Canary Failed',
    icon: <XCircle className="w-3.5 h-3.5" />,
    bg: 'bg-orange-50',
    border: 'border-orange-300',
    text: 'text-orange-800',
    dot: 'bg-orange-500',
  },
  suspended: {
    label: 'Suspended',
    icon: <ShieldOff className="w-3.5 h-3.5" />,
    bg: 'bg-rose-50',
    border: 'border-rose-300',
    text: 'text-rose-800',
    dot: 'bg-rose-500',
  },
};

interface TrustBadgeProps {
  trustStatus?: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const TrustBadge: React.FC<TrustBadgeProps> = ({
  trustStatus = 'trusted',
  size = 'md',
  showLabel = true,
}) => {
  const config = TRUST_CONFIGS[trustStatus] ?? TRUST_CONFIGS.trusted;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[10px] gap-1',
    md: 'px-2.5 py-1 text-xs gap-1.5',
    lg: 'px-3 py-1.5 text-sm gap-2',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-semibold rounded-full border font-mono ${config.bg} ${config.border} ${config.text} ${sizeClasses}`}
      title={`Trust Status: ${config.label}`}
    >
      {config.icon}
      {showLabel && <span>{config.label}</span>}
    </span>
  );
};

export { TRUST_CONFIGS };
