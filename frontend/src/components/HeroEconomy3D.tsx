import React, { useRef, useState } from 'react';
import { 
  ShieldCheck, 
  Cpu, 
  Coins, 
  CheckCircle2, 
  Sparkles, 
  Lock, 
  Hash, 
  Zap,
  ArrowRight
} from 'lucide-react';
import { DepthIcon } from './DepthIcon';

export const HeroEconomy3D: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rotate, setRotate] = useState({ x: 0, y: 0 });
  const [activeNode, setActiveNode] = useState<string | null>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;

    const rotY = (x / (rect.width / 2)) * 3; // max 3 deg
    const rotX = -(y / (rect.height / 2)) * 3;

    setRotate({ x: rotX, y: rotY });
  };

  const handleMouseLeave = () => {
    setRotate({ x: 0, y: 0 });
    setActiveNode(null);
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative w-full h-[460px] sm:h-[500px] lg:h-[540px] perspective-1500 flex items-center justify-center select-none"
    >
      {/* ── 3D Scene Root ─────────────────────────────────────────────── */}
      <div
        className="relative w-full max-w-[500px] h-full flex items-center justify-center transition-transform duration-300 ease-out preserve-3d"
        style={{
          transform: `perspective(1200px) rotateX(${rotate.x.toFixed(2)}deg) rotateY(${rotate.y.toFixed(2)}deg)`,
        }}
      >
        {/* Background Network Orbit Rings (Layer 0: translateZ: 0px) */}
        <div className="absolute w-[380px] h-[380px] rounded-full border border-dashed border-blue-200 animate-spin-slow pointer-events-none opacity-60" style={{ animationDuration: '40s' }} />
        <div className="absolute w-[260px] h-[260px] rounded-full border border-dashed border-purple-200 animate-spin-slow pointer-events-none opacity-50" style={{ animationDuration: '30s', animationDirection: 'reverse' }} />
        
        {/* Background Ambient Halo Glow */}
        <div className="absolute w-72 h-72 bg-gradient-to-tr from-blue-500/10 via-indigo-500/08 to-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* ── SVG Sequential Directional Flow Lines (Layer 1: translateZ: 15px) ── */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          viewBox="0 0 500 500"
          style={{ transform: 'translateZ(15px)' }}
        >
          <defs>
            <linearGradient id="flow-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#3155D9" stopOpacity="0.7" />
              <stop offset="100%" stopColor="#6D5BD0" stopOpacity="0.7" />
            </linearGradient>
            <linearGradient id="verify-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#6D5BD0" stopOpacity="0.7" />
              <stop offset="100%" stopColor="#15805F" stopOpacity="0.7" />
            </linearGradient>
          </defs>

          {/* Node 1 (Top Left Requester) -> Node 2 (Top Right Task) */}
          <line
            x1="120" y1="90" x2="380" y2="90"
            stroke="url(#flow-grad)"
            strokeWidth="2"
            strokeDasharray="4 4"
            className="opacity-70 animate-connection-flow"
          />

          {/* Node 2 (Top Right Task) -> Node 3 (Center Right Worker) */}
          <line
            x1="380" y1="120" x2="380" y2="240"
            stroke="url(#flow-grad)"
            strokeWidth="2"
            className="opacity-70 animate-connection-flow"
          />

          {/* Node 3 (Center Right Worker) -> Node 4 (Bottom Right Locked Result) */}
          <line
            x1="380" y1="290" x2="380" y2="390"
            stroke="url(#flow-grad)"
            strokeWidth="2"
            className="opacity-70 animate-connection-flow"
          />

          {/* Node 4 (Bottom Right Result) -> Node 5 (Bottom Left Verifier) */}
          <line
            x1="340" y1="410" x2="160" y2="410"
            stroke="url(#verify-grad)"
            strokeWidth="2"
            strokeDasharray="4 4"
            className="opacity-70"
          />

          {/* Center Connection to Hub */}
          <line
            x1="250" y1="250" x2="380" y2="260"
            stroke="#3155D9"
            strokeWidth="1.5"
            className="opacity-40"
          />
          <line
            x1="250" y1="250" x2="120" y2="390"
            stroke="#6D5BD0"
            strokeWidth="1.5"
            className="opacity-40"
          />
        </svg>

        {/* ── CENTER: AgentPay Trust & Coordination Layer (translateZ: 35px) ── */}
        <div
          className="absolute z-20 flex flex-col items-center justify-center transition-transform duration-300 animate-float"
          style={{ transform: 'translateZ(35px)' }}
        >
          <div className="relative group cursor-pointer">
            {/* Luminous Pulsing Halos */}
            <div className="absolute -inset-4 rounded-full bg-blue-500/20 blur-xl animate-pulse-subtle" />
            <div className="absolute -inset-1 rounded-full bg-gradient-to-r from-[#172554] to-[#3155D9] opacity-40 blur-sm" />
            
            <div className="relative w-28 h-28 rounded-full bg-gradient-to-b from-[#172554] via-[#1E3A8A] to-[#111A2E] border-2 border-blue-400 flex flex-col items-center justify-center p-3 shadow-xl glow-blue text-white text-center">
              <Sparkles className="w-5 h-5 text-blue-300 animate-pulse mb-0.5" />
              <span className="font-mono text-[11px] font-black tracking-wider text-white uppercase">
                AgentPay
              </span>
              <span className="text-[7.5px] font-mono text-blue-200 uppercase tracking-tight">
                Trust Layer
              </span>
            </div>
          </div>
        </div>

        {/* ── STAGE 1: Requester Agent (Top-Left: translateZ: 45px) ── */}
        <div
          onMouseEnter={() => setActiveNode('client')}
          className="absolute top-6 left-2 sm:left-6 z-30 transition-transform duration-300 animate-float-reverse"
          style={{ transform: 'translateZ(45px)' }}
        >
          <div className="glass-card p-3 rounded-2xl border border-emerald-200 bg-white shadow-md flex items-center gap-2.5 hover:border-emerald-400 hover:scale-105 transition-all">
            <DepthIcon
              icon={<Zap className="w-4 h-4 text-emerald-600" />}
              color="emerald"
              size="sm"
            />
            <div className="text-left font-mono">
              <div className="text-[10px] text-emerald-700 uppercase font-bold tracking-wider">1. Requester</div>
              <div className="text-xs text-[#18202F] font-bold">Publishes Task</div>
            </div>
          </div>
        </div>

        {/* ── STAGE 2: Marketplace Task (Top-Right: translateZ: 50px) ── */}
        <div
          onMouseEnter={() => setActiveNode('task')}
          className="absolute top-6 right-2 sm:right-6 z-30 transition-transform duration-300 animate-float"
          style={{ transform: 'translateZ(50px)' }}
        >
          <div className="glass-card p-3 rounded-2xl border border-blue-200 bg-white shadow-md flex items-center gap-2.5 hover:border-blue-400 hover:scale-105 transition-all">
            <DepthIcon
              icon={<Coins className="w-4 h-4 text-[#3155D9]" />}
              color="blue"
              size="sm"
            />
            <div className="text-left font-mono">
              <div className="text-[10px] text-[#3155D9] uppercase font-bold tracking-wider">2. Task Opportunity</div>
              <div className="text-xs text-[#18202F] font-bold flex items-center gap-1">
                <span>Reward: 150 AP</span>
              </div>
            </div>
          </div>
        </div>

        {/* ── STAGE 3: Autonomous Worker Agent (Center-Right: translateZ: 55px) ── */}
        <div
          onMouseEnter={() => setActiveNode('worker')}
          className="absolute right-0 top-1/2 -translate-y-4 z-30 transition-transform duration-300 animate-float-reverse"
          style={{ transform: 'translateZ(55px)' }}
        >
          <div className="glass-card p-3.5 rounded-2xl border border-blue-200 bg-white shadow-md flex items-center gap-3 hover:border-blue-400 hover:scale-105 transition-all glow-blue">
            <DepthIcon
              icon={<Cpu className="w-5 h-5 text-[#3155D9]" />}
              color="blue"
              size="md"
            />
            <div className="text-left font-mono">
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] text-[#3155D9] uppercase font-bold">3. Worker AI</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              </div>
              <div className="text-xs text-[#18202F] font-bold">NLP-Agent-01</div>
              <div className="text-[9px] text-[#596273]">Executes Autonomous Work</div>
            </div>
          </div>
        </div>

        {/* ── STAGE 4: Immutable Result Package (Bottom-Right: translateZ: 40px) ── */}
        <div
          onMouseEnter={() => setActiveNode('submission')}
          className="absolute bottom-8 right-2 sm:right-6 z-30 transition-transform duration-300 animate-float"
          style={{ transform: 'translateZ(40px)' }}
        >
          <div className="glass-card p-3 rounded-2xl border border-purple-200 bg-white shadow-md flex items-center gap-2.5 hover:border-purple-400 hover:scale-105 transition-all">
            <DepthIcon
              icon={<Lock className="w-4 h-4 text-[#6D5BD0]" />}
              color="violet"
              size="sm"
            />
            <div className="text-left font-mono">
              <div className="text-[10px] text-[#6D5BD0] uppercase font-bold flex items-center gap-1">
                <Hash className="w-3 h-3 text-blue-600" />
                <span>4. Locked Result</span>
              </div>
              <div className="text-xs text-[#18202F] font-bold">SHA-256 Fingerprint</div>
            </div>
          </div>
        </div>

        {/* ── STAGE 5: Independent Verifier (Bottom-Left: translateZ: 50px) ── */}
        <div
          onMouseEnter={() => setActiveNode('verifier')}
          className="absolute bottom-8 left-2 sm:left-6 z-30 transition-transform duration-300 animate-float-reverse"
          style={{ transform: 'translateZ(50px)' }}
        >
          <div className="glass-card p-3.5 rounded-2xl border border-purple-200 bg-white shadow-md flex items-center gap-3 hover:border-purple-400 hover:scale-105 transition-all glow-violet">
            <DepthIcon
              icon={<ShieldCheck className="w-5 h-5 text-[#6D5BD0]" />}
              color="violet"
              size="md"
            />
            <div className="text-left font-mono">
              <div className="flex items-center gap-1">
                <span className="text-[10px] text-[#6D5BD0] uppercase font-bold">5. Verifier Agent</span>
                <span className="text-[8px] bg-purple-50 text-purple-700 border border-purple-200 px-1 rounded font-semibold">V ≠ W</span>
              </div>
              <div className="text-xs text-[#18202F] font-bold">Verify-Agent-01</div>
              <div className="text-[9px] text-emerald-700 flex items-center gap-1 font-semibold">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                <span>Outcome: PASS (89.5%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* ── Flow Indicator Tag (Bottom Center: translateZ: 60px) ── */}
        <div
          className="absolute -bottom-2 z-40 bg-white border border-slate-200 px-4 py-1.5 rounded-full shadow-sm text-[10px] font-mono text-[#596273] flex items-center gap-1.5 flex-wrap justify-center"
          style={{ transform: 'translateZ(60px)' }}
        >
          <span className="text-[#3155D9] font-bold">Flow:</span>
          <span>Task</span>
          <span className="text-slate-400">→</span>
          <span>Worker</span>
          <span className="text-slate-400">→</span>
          <span>Result</span>
          <span className="text-slate-400">→</span>
          <span>Verifier</span>
          <span className="text-slate-400">→</span>
          <span className="text-amber-800 font-bold bg-amber-50 border border-amber-200 px-1.5 py-0.5 rounded">
            Settlement (Next Phase)
          </span>
        </div>
      </div>
    </div>
  );
};
