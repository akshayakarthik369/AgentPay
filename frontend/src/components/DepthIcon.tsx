import React, { ReactNode } from 'react';

export interface DepthIconProps {
  icon: ReactNode;
  color?: 'cyan' | 'purple' | 'indigo' | 'emerald' | 'amber' | 'blue' | 'rose' | 'gold' | 'violet' | 'navy';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  animateHover?: boolean;
}

export const DepthIcon: React.FC<DepthIconProps> = ({
  icon,
  color = 'blue',
  size = 'md',
  className = '',
  animateHover = true,
}) => {
  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'w-8 h-8 rounded-xl',
          iconSize: 'text-xs',
        };
      case 'lg':
        return {
          container: 'w-14 h-14 rounded-2xl',
          iconSize: 'text-xl',
        };
      case 'xl':
        return {
          container: 'w-18 h-18 rounded-3xl p-4',
          iconSize: 'text-2xl',
        };
      case 'md':
      default:
        return {
          container: 'w-11 h-11 rounded-2xl',
          iconSize: 'text-base',
        };
    }
  };

  const getColorStyles = () => {
    switch (color) {
      case 'gold':
        return {
          glow: 'bg-amber-400/20',
          shell: 'bg-gradient-to-br from-amber-50 to-orange-100/80 border-amber-200 text-amber-700 shadow-sm',
          highlight: 'from-amber-200/40 to-transparent',
        };
      case 'violet':
      case 'purple':
        return {
          glow: 'bg-purple-500/20',
          shell: 'bg-gradient-to-br from-purple-50 to-indigo-100/80 border-purple-200 text-purple-700 shadow-sm',
          highlight: 'from-purple-200/40 to-transparent',
        };
      case 'navy':
      case 'indigo':
        return {
          glow: 'bg-blue-900/15',
          shell: 'bg-gradient-to-br from-slate-50 to-blue-100/80 border-blue-200 text-[#172554] shadow-sm',
          highlight: 'from-blue-200/40 to-transparent',
        };
      case 'emerald':
        return {
          glow: 'bg-emerald-500/20',
          shell: 'bg-gradient-to-br from-emerald-50 to-teal-100/80 border-emerald-200 text-emerald-700 shadow-sm',
          highlight: 'from-emerald-200/40 to-transparent',
        };
      case 'amber':
        return {
          glow: 'bg-amber-500/20',
          shell: 'bg-gradient-to-br from-amber-50 to-orange-100/80 border-amber-200 text-amber-700 shadow-sm',
          highlight: 'from-amber-200/40 to-transparent',
        };
      case 'rose':
        return {
          glow: 'bg-rose-500/20',
          shell: 'bg-gradient-to-br from-rose-50 to-red-100/80 border-rose-200 text-rose-700 shadow-sm',
          highlight: 'from-rose-200/40 to-transparent',
        };
      case 'blue':
      case 'cyan':
      default:
        return {
          glow: 'bg-blue-500/20',
          shell: 'bg-gradient-to-br from-blue-50 to-indigo-100/80 border-blue-200 text-[#3155D9] shadow-sm',
          highlight: 'from-blue-200/40 to-transparent',
        };
    }
  };

  const { container } = getSizeStyles();
  const { glow, shell, highlight } = getColorStyles();

  return (
    <div
      className={`relative group/icon inline-flex items-center justify-center shrink-0 perspective-1000 ${container} ${className}`}
      style={{ transformStyle: 'preserve-3d' }}
    >
      {/* Layer 1: Ambient Rear Halo Glow */}
      <div
        className={`absolute inset-0 rounded-[inherit] ${glow} blur-md opacity-40 group-hover/icon:opacity-80 transition-opacity duration-300 pointer-events-none -z-10`}
      />

      {/* Layer 2: Glass/Gradient Outer Shell */}
      <div
        className={`w-full h-full rounded-[inherit] border backdrop-blur-md flex items-center justify-center relative overflow-hidden shadow-lg ${shell} ${
          animateHover ? 'group-hover/icon:scale-105 group-hover/icon:rotate-3 transition-transform duration-300 cubic-bezier(0.34, 1.56, 0.64, 1)' : ''
        }`}
        style={{ transformStyle: 'preserve-3d' }}
      >
        {/* Layer 3: Top-left Specular Glass Reflection */}
        <div
          className={`absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b ${highlight} opacity-40 pointer-events-none`}
        />

        {/* Layer 4: Foreground Depth Icon */}
        <div
          className="relative z-10 drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)] transition-transform duration-300 group-hover/icon:translate-z-20"
          style={{ transform: 'translateZ(8px)' }}
        >
          {icon}
        </div>
      </div>
    </div>
  );
};
