import React from 'react';
import { Coins } from 'lucide-react';

export interface APTokenBadgeProps {
  amount: number | string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export const APTokenBadge: React.FC<APTokenBadgeProps> = ({
  amount,
  size = 'md',
  showLabel = true,
  className = '',
}) => {
  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'px-2 py-0.5 text-xs',
          coin: 'w-3.5 h-3.5 text-[9px]',
          amountText: 'text-xs font-bold',
        };
      case 'lg':
        return {
          container: 'px-4 py-2 text-xl',
          coin: 'w-6 h-6 text-xs',
          amountText: 'text-2xl font-black',
        };
      case 'md':
      default:
        return {
          container: 'px-2.5 py-1 text-sm',
          coin: 'w-4 h-4 text-[10px]',
          amountText: 'text-sm font-bold',
        };
    }
  };

  const { container, coin, amountText } = getSizeStyles();

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-xl font-mono bg-white border border-slate-200/90 text-[#18202F] shadow-sm ${container} ${className}`}
      title="Simulated AgentPay Credits (AP)"
    >
      {/* 3D Dimensional AP Coin Icon */}
      <span
        className={`relative inline-flex items-center justify-center rounded-full ap-coin-shimmer text-amber-300 font-bold shrink-0 border border-[#B89B5E]/40 ${coin}`}
      >
        <span className="relative z-10 leading-none">AP</span>
      </span>

      <span className={`text-[#18202F] tracking-tight ${amountText}`}>
        {typeof amount === 'number' ? amount.toLocaleString() : amount}
      </span>

      {showLabel && (
        <span className="text-[10px] uppercase font-bold text-[#596273] opacity-90">
          Credits
        </span>
      )}
    </span>
  );
};
