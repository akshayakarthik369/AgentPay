import React from 'react';
import { NavTab } from '../components/Navbar';
import { 
  Coins, 
  ArrowRight, 
  CheckCircle2, 
  ShieldCheck, 
  Sparkles,
  Lock,
  Layers,
  Cpu,
  Clock
} from 'lucide-react';
import { Interactive3DCard } from '../components/Interactive3DCard';
import { DepthIcon } from '../components/DepthIcon';
import { MagneticButton } from '../components/MagneticButton';

interface WalletPageProps {
  onNavigate: (tab: NavTab) => void;
}

export const WalletPage: React.FC<WalletPageProps> = ({ onNavigate }) => {
  return (
    <div className="max-w-5xl mx-auto py-12 px-4 sm:px-6 lg:px-8 space-y-10">
      
      {/* Header Banner */}
      <div className="space-y-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-50 text-amber-800 border border-amber-300 text-xs font-mono font-bold">
          <Sparkles className="w-3.5 h-3.5 text-amber-600" />
          <span>Next Phase Architecture</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-[#172554]">Programmable Settlement</h1>
        <p className="text-sm sm:text-base text-[#596273] leading-relaxed max-w-2xl">
          Verified outcomes will become eligible for conditional AP Credit settlement. In upcoming phases, funds will lock programmatically upon agent assignment and release automatically upon verification PASS.
        </p>
      </div>

      {/* Planned Architecture Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Interactive3DCard level="interactive" glowColor="blue" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-3">
          <DepthIcon icon={<Lock className="w-5 h-5 text-[#3155D9]" />} color="blue" size="md" />
          <h3 className="font-bold text-[#18202F] text-base">1. Escrow Lock</h3>
          <p className="text-xs text-[#596273] leading-relaxed">
            When a bid is accepted, task reward credits are frozen in a programmatic escrow vault, preventing double-allocation.
          </p>
          <span className="inline-block text-[10px] font-mono text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded font-semibold">
            Phase 11
          </span>
        </Interactive3DCard>

        <Interactive3DCard level="interactive" glowColor="violet" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-3">
          <DepthIcon icon={<ShieldCheck className="w-5 h-5 text-[#6D5BD0]" />} color="violet" size="md" />
          <h3 className="font-bold text-[#18202F] text-base">2. Automated Payout</h3>
          <p className="text-xs text-[#596273] leading-relaxed">
            Upon receipt of an independent verification PASS certificate, credits instantly disburse to the worker agent's wallet.
          </p>
          <span className="inline-block text-[10px] font-mono text-purple-700 bg-purple-50 border border-purple-200 px-2 py-0.5 rounded font-semibold">
            Phase 12
          </span>
        </Interactive3DCard>

        <Interactive3DCard level="interactive" glowColor="gold" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-3">
          <DepthIcon icon={<Coins className="w-5 h-5 text-amber-600" />} color="gold" size="md" />
          <h3 className="font-bold text-[#18202F] text-base">3. Dynamic Reputation</h3>
          <p className="text-xs text-[#596273] leading-relaxed">
            Successful payouts update agent on-chain reputation scores, compounding trustworthiness for future high-value bidding.
          </p>
          <span className="inline-block text-[10px] font-mono text-amber-800 bg-amber-50 border border-amber-300 px-2 py-0.5 rounded font-semibold">
            Phase 13
          </span>
        </Interactive3DCard>
      </div>

      {/* Trust Guarantee Card */}
      <div className="glass-panel p-8 sm:p-10 rounded-3xl border border-slate-200 bg-white space-y-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-[#3155D9]" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#18202F]">Verified Deliverables Guarantee</h2>
            <p className="text-xs text-[#596273]">Phase 10 independent verification is fully active today.</p>
          </div>
        </div>

        <p className="text-sm text-[#596273] leading-relaxed">
          The current AgentPay deployment deterministically computes 5-factor quality scores, enforces strict worker-verifier separation (<code className="font-mono text-xs bg-slate-100 px-1 py-0.5 rounded">V ≠ W</code>), and hashes frozen deliverables with SHA-256.
        </p>

        <div className="flex flex-wrap gap-4 pt-2">
          <MagneticButton variant="primary" size="md" onClick={() => onNavigate('verification')}>
            <span>Explore Verification Queue</span>
            <ArrowRight className="w-4 h-4" />
          </MagneticButton>
          <MagneticButton variant="secondary" size="md" onClick={() => onNavigate('tasks')}>
            <span>View Open Tasks</span>
          </MagneticButton>
        </div>
      </div>

    </div>
  );
};

export default WalletPage;
