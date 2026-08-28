import React, { useRef, useState, ReactNode, ButtonHTMLAttributes } from 'react';

export interface MagneticButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'glass' | 'emerald' | 'purple' | 'violet' | 'gold' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  magneticDistance?: number; // max px translation, default ~3px
  className?: string;
}

export const MagneticButton: React.FC<MagneticButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  magneticDistance = 3.0,
  className = '',
  onClick,
  disabled,
  ...rest
}) => {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled || !buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    const x = e.clientX - (rect.left + rect.width / 2);
    const y = e.clientY - (rect.top + rect.height / 2);

    const pullX = (x / (rect.width / 2)) * magneticDistance;
    const pullY = (y / (rect.height / 2)) * magneticDistance;

    setPosition({ x: pullX, y: pullY });
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'secondary':
        return 'bg-white hover:bg-slate-50 text-[#18202F] border border-slate-200/90 shadow-sm hover:border-slate-300 active:bg-slate-100';
      case 'glass':
        return 'bg-white/80 hover:bg-white text-[#18202F] border border-slate-200 shadow-sm hover:border-blue-500/30';
      case 'emerald':
        return 'bg-gradient-to-r from-[#15805F] to-[#0F766E] hover:brightness-110 text-white font-semibold shadow-sm';
      case 'violet':
      case 'purple':
        return 'bg-gradient-to-r from-[#6D5BD0] to-[#5845C7] hover:brightness-110 text-white font-semibold shadow-sm';
      case 'gold':
        return 'bg-gradient-to-r from-[#B89B5E] to-[#9E8246] hover:brightness-110 text-white font-semibold shadow-sm';
      case 'danger':
        return 'bg-gradient-to-r from-[#DC2626] to-[#B91C1C] hover:brightness-110 text-white font-semibold shadow-sm';
      case 'primary':
      default:
        return 'bg-gradient-to-r from-[#172554] via-[#1E3A8A] to-[#3155D9] hover:from-[#1E3A8A] hover:to-[#2546BD] text-white font-semibold shadow-md glow-blue';
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'px-3.5 py-1.5 text-xs rounded-xl';
      case 'lg':
        return 'px-7 py-3.5 text-base rounded-2xl';
      case 'md':
      default:
        return 'px-5 py-2.5 text-sm rounded-xl';
    }
  };

  return (
    <button
      ref={buttonRef}
      disabled={disabled}
      onClick={onClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative inline-flex items-center justify-center gap-2 font-semibold transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none disabled:transform-none select-none cursor-pointer ${getVariantStyles()} ${getSizeStyles()} ${className}`}
      style={{
        transform: `translate3d(${position.x.toFixed(1)}px, ${position.y.toFixed(1)}px, 0px)`,
        transition: position.x === 0 && position.y === 0 ? 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)' : 'transform 0.1s ease-out',
      }}
      {...rest}
    >
      {children}
    </button>
  );
};
