import React, { useState } from 'react';
import { X, Edit3, Loader2, AlertCircle, Wallet, Clock, Zap } from 'lucide-react';
import { updateBid, ApiBid } from '../services/api';

interface EditBidModalProps {
  bid: ApiBid;
  onClose: () => void;
  onSuccess: () => void;
}

export const EditBidModal: React.FC<EditBidModalProps> = ({ bid, onClose, onSuccess }) => {
  const [bidAmount, setBidAmount] = useState<number>(bid.bid_amount);
  const [estimatedMinutes, setEstimatedMinutes] = useState<number>(bid.estimated_completion_minutes);
  const [proposal, setProposal] = useState<string>(bid.proposal);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (bidAmount <= 0) {
      setError('Bid amount must be greater than 0 AP Credits.');
      return;
    }
    if (estimatedMinutes <= 0) {
      setError('Estimated completion time must be greater than 0 minutes.');
      return;
    }
    if (proposal.trim().length < 5) {
      setError('Proposal pitch must be at least 5 characters.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await updateBid(bid.id, {
        bid_amount: bidAmount,
        estimated_completion_minutes: estimatedMinutes,
        proposal: proposal.trim(),
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to update bid.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-panel w-full max-w-lg rounded-3xl border border-slate-800 p-6 sm:p-8 bg-[#0A0D14]/95 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-800">
          <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <Edit3 className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Edit Pending Bid</h3>
            <p className="text-xs text-slate-400 font-mono">{bid.bid_code} · {bid.task?.title || `Task #${bid.task_id}`}</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-2 text-xs text-rose-400 font-mono">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1.5 flex items-center gap-1">
                <Wallet className="w-3 h-3 text-cyan-400" />
                <span>Bid Amount (AP)</span>
              </label>
              <input
                type="number"
                step="1"
                min="1"
                value={bidAmount}
                onChange={(e) => setBidAmount(Number(e.target.value))}
                disabled={submitting}
                className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono text-sm focus:outline-none focus:border-cyan-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1.5 flex items-center gap-1">
                <Clock className="w-3 h-3 text-indigo-400" />
                <span>Est. Time (Mins)</span>
              </label>
              <input
                type="number"
                step="5"
                min="5"
                value={estimatedMinutes}
                onChange={(e) => setEstimatedMinutes(Number(e.target.value))}
                disabled={submitting}
                className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono text-sm focus:outline-none focus:border-cyan-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1.5 flex items-center gap-1">
              <Zap className="w-3 h-3 text-amber-400" />
              <span>Proposal / Approach Pitch</span>
            </label>
            <textarea
              rows={3}
              value={proposal}
              onChange={(e) => setProposal(e.target.value)}
              disabled={submitting}
              maxLength={1000}
              className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs leading-relaxed focus:outline-none focus:border-cyan-500 resize-none"
              required
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-300 hover:text-white text-xs font-mono transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-bold text-xs font-mono shadow-md glow-cyan transition-all"
            >
              {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <span>Update Bid</span>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
