import React, { useRef, useState, useEffect, ReactNode, CSSProperties } from 'react';

export interface Interactive3DCardProps {
  children: ReactNode;
  className?: string;
  /** normal = subtle tilt | interactive = card-level tilt | hero = full dynamics | static = no tilt */
  level?: 'static' | 'normal' | 'interactive' | 'hero';
  maxRotation?: number; // degrees — interactive default: 3, hero default: 6
  maxTranslation?: number; // px — interactive default: 4, hero default: 6
  glowColor?: 'cyan' | 'purple' | 'indigo' | 'emerald' | 'amber' | 'blue' | 'gold' | 'navy' | 'violet';
  enableSpotlight?: boolean;
  enableGlow?: boolean;
  onClick?: () => void;
  style?: CSSProperties;
}

export const Interactive3DCard: React.FC<Interactive3DCardProps> = ({
  children,
  className = '',
  level = 'interactive',
  maxRotation,
  maxTranslation,
  glowColor = 'blue',
  enableSpotlight = true,
  enableGlow = true,
  onClick,
  style = {},
}) => {
  // Level-based defaults: interactive = refined (3°/4px), hero = expressive (6°/6px)
  const effectiveRotation = maxRotation ?? (level === 'hero' ? 6 : 3);
  const effectiveTranslation = maxTranslation ?? (level === 'hero' ? 6 : 4);
  const cardRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [supportsHover, setSupportsHover] = useState(false);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    // Check if device supports fine pointer hover (e.g. desktop mouse vs touch)
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(hover: hover) and (pointer: fine)');
      setSupportsHover(mediaQuery.matches);
      const listener = (e: MediaQueryListEvent) => setSupportsHover(e.matches);
      mediaQuery.addEventListener('change', listener);
      return () => mediaQuery.removeEventListener('change', listener);
    }
  }, []);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!supportsHover || level === 'normal' || level === 'static' || !cardRef.current) return;

    const card = cardRef.current;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const percentX = (x - centerX) / centerX; // -1 to 1
    const percentY = (y - centerY) / centerY; // -1 to 1

    // Rotation: moving mouse right tilts card Y right (rotateY positive), mouse down tilts X down (rotateX negative)
    const rotateY = percentX * effectiveRotation;
    const rotateX = -percentY * effectiveRotation;

    // Magnetic Translation
    const translateX = percentX * effectiveTranslation;
    const translateY = percentY * effectiveTranslation;

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    animationFrameRef.current = requestAnimationFrame(() => {
      if (card) {
        card.style.setProperty('--mouse-x', `${x}px`);
        card.style.setProperty('--mouse-y', `${y}px`);
        card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translate3d(${translateX.toFixed(1)}px, ${translateY.toFixed(1)}px, 0px) scale(${level === 'hero' ? 1.012 : 1.006})`;
      }
    });
  };

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (cardRef.current) {
      cardRef.current.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translate3d(0px, 0px, 0px) scale(1)';
    }
  };

  const getGlowClasses = () => {
    switch (glowColor) {
      case 'gold':
        return 'from-amber-400/15 via-yellow-500/10 to-transparent';
      case 'violet':
      case 'purple':
        return 'from-purple-500/15 via-indigo-500/10 to-transparent';
      case 'navy':
      case 'indigo':
        return 'from-blue-900/10 via-indigo-600/10 to-transparent';
      case 'emerald':
        return 'from-emerald-500/15 via-teal-500/10 to-transparent';
      case 'amber':
        return 'from-amber-500/15 via-orange-500/10 to-transparent';
      case 'blue':
      case 'cyan':
      default:
        return 'from-blue-500/15 via-indigo-500/10 to-transparent';
    }
  };

  return (
    <div
      className="relative group perspective-1000"
      style={{ transformStyle: 'preserve-3d' }}
    >
      {/* ── Layer 1: Ambient Rear Halo Glow ─────────────────────────────── */}
      {enableGlow && level !== 'normal' && level !== 'static' && (
        <div
          className={`absolute -inset-2 rounded-3xl bg-gradient-to-tr ${getGlowClasses()} blur-2xl opacity-0 group-hover:opacity-50 transition-opacity duration-500 -z-10 pointer-events-none`}
        />
      )}

      {/* ── Layer 2: Main Interactive Card ─────────────────────────────── */}
      <div
        ref={cardRef}
        onClick={onClick}
        onMouseMove={handleMouseMove}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className={`${level !== 'static' ? 'card-spotlight card-border-glow' : ''} transition-all duration-300 ease-out will-change-transform ${
          level === 'hero' ? 'glass-card-elevated' : 'glass-card'
        } ${className}`}
        style={{
          transformStyle: 'preserve-3d',
          transition: isHovered
            ? 'box-shadow 0.3s ease, border-color 0.3s ease'
            : 'transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.4s ease, border-color 0.4s ease',
          ...style,
        }}
      >
        {children}
      </div>
    </div>
  );
};
