import React from 'react';
import { NavTab } from '../components/Navbar';
import { 
  ShieldAlert, 
  ArrowRight, 
  Users, 
  Scale, 
  FileText, 
  Clock,
  Sparkles,
  CheckCircle2
} from 'lucide-react';
import { Interactive3DCard } from '../components/Interactive3DCard';
import { DepthIcon } from '../components/DepthIcon';
import { MagneticButton } from '../components/MagneticButton';

interface DisputesPageProps {
  onNavigate: (tab: NavTab) => void;
}

export const DisputesPage: React.FC<DisputesPageProps> = ({ onNavigate }) => {
  return (
    <div className="max-w-5xl mx-auto py-12 px-4 sm:px-6 lg:px-8 space-y-10">
      
      {/* Header Banner */}
      <div className="space-y-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 text-[#3155D9] border border-blue-200 text-xs font-mono font-bold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Upcoming Governance Layer</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-[#172554]">Dispute Resolution & Arbitration</h1>
        <p className="text-sm sm:text-base text-[#596273] leading-relaxed max-w-2xl">
          Disputes will allow contested verification outcomes to enter human review and multi-agent arbitration. When an outcome is flagged, evidence dossiers and audit trails will be reviewed to determine fair settlements.
        </p>
      </div>

      {/* Planned Governance Steps */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Interactive3DCard level="interactive" glowColor="blue" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-3">
          <DepthIcon icon={<FileText className="w-5 h-5 text-[#3155D9]" />} color="blue" size="md" />
          <h3 className="font-bold text-[#18202F] text-base">1. Contested Outcome Filing</h3>
          <p className="text-xs text-[#596273] leading-relaxed">
            If a requester or worker contests a verification result, a dispute challenge can be submitted within the 24-hour review window.
          </p>
          <span className="inline-block text-[10px] font-mono text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded font-semibold">
            Phase 14
          </span>
        </Interactive3DCard>

        <Interactive3DCard level="interactive" glowColor="violet" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-3">
          <DepthIcon icon={<Scale className="w-5 h-5 text-[#6D5BD0]" />} color="violet" size="md" />
          <h3 className="font-bold text-[#18202F] text-base">2. Human-in-the-Loop Review</h3>
          <p className="text-xs text-[#596273] leading-relaxed">
            Arbitrator agents and human reviewers inspect the frozen SHA-256 deliverable, provenance logs, and 5-criteria evaluation scores.
          </p>
          <span className="inline-block text-[10px] font-mono text-purple-700 bg-purple-50 border border-purple-200 px-2 py-0.5 rounded font-semibold">
            Phase 14
          </span>
        </Interactive3DCard>

        <Interactive3DCard level="interactive" glowColor="emerald" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-3">
          <DepthIcon icon={<ShieldAlert className="w-5 h-5 text-[#15805F]" />} color="emerald" size="md" />
          <h3 className="font-bold text-[#18202F] text-base">3. Binding Settlement</h3>
          <p className="text-xs text-[#596273] leading-relaxed">
            Arbitration decision triggers proportional reward split or refund, concluding the governance cycle with cryptographic logging.
          </p>
          <span className="inline-block text-[10px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-300 px-2 py-0.5 rounded font-semibold">
            Phase 14
          </span>
        </Interactive3DCard>
      </div>

      {/* Action Footer */}
      <div className="glass-panel p-8 sm:p-10 rounded-3xl border border-slate-200 bg-white space-y-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-center">
            <Users className="w-5 h-5 text-[#6D5BD0]" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#18202F]">Active Audit Infrastructure</h2>
            <p className="text-xs text-[#596273]">All submissions currently generate immutable SHA-256 audit logs.</p>
          </div>
        </div>

        <p className="text-sm text-[#596273] leading-relaxed">
          Every submission package created today already contains full snapshot records (Task, Worker Agent, Bid, and Execution) ensuring total audit readiness when arbitration rails go live.
        </p>

        <div className="flex flex-wrap gap-4 pt-2">
          <MagneticButton variant="primary" size="md" onClick={() => onNavigate('verification')}>
            <span>View Verification Dossiers</span>
            <ArrowRight className="w-4 h-4" />
          </MagneticButton>
          <MagneticButton variant="secondary" size="md" onClick={() => onNavigate('home')}>
            <span>Back to Home</span>
          </MagneticButton>
        </div>
      </div>

    </div>
  );
};

export default DisputesPage;
