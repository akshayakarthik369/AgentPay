import React, { useState } from 'react';
import { 
  X, 
  Sparkles, 
  Send, 
  Clock, 
  Wallet, 
  AlertCircle, 
  CheckCircle2, 
  Loader2,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { createBid, TaskSummaryForMatch, ApiAgent } from '../services/api';

interface SubmitBidModalProps {
  task: TaskSummaryForMatch;
  agent: ApiAgent;
  matchScore: number;
  onClose: () => void;
  onSuccess: () => void;
}

export const SubmitBidModal: React.FC<SubmitBidModalProps> = ({
  task,
  agent,
  matchScore,
  onClose,
  onSuccess,
}) => {
  const [bidAmount, setBidAmount] = useState<number>(Math.round(task.reward * 0.9));
  const [estimatedMinutes, setEstimatedMinutes] = useState<number>(45);
  const [proposal, setProposal] = useState<string>(
    `I can complete this ${task.category} task using my ${agent.capabilities.slice(0, 2).join(' and ')} capabilities within ${estimatedMinutes} minutes.`
  );
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const isEligibleToBid = matchScore >= 60 && agent.is_active && agent.status === 'available';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isEligibleToBid) return;

    if (bidAmount <= 0) {
      setError('Bid amount must be greater than 0 AP Credits.');
      return;
    }
    if (bidAmount > task.reward) {
      setError(`Bid amount (${bidAmount} AP) cannot exceed task reward (${task.reward} AP).`);
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
      await createBid({
        task_id: task.id,
        agent_id: agent.id,
        bid_amount: bidAmount,
        estimated_completion_minutes: estimatedMinutes,
        proposal: proposal.trim(),
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to submit bid.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-panel w-full max-w-lg rounded-3xl border border-slate-800 p-6 sm:p-8 bg-[#0A0D14]/95 shadow-2xl relative">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-800">
          <div className="w-10 h-10 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Submit Autonomous Bid</h3>
            <p className="text-xs text-slate-400 font-mono">
              {agent.name} ({agent.agent_code}) · {task.task_code}
            </p>
          </div>
        </div>

        {/* Match Gate Banner */}
        {!isEligibleToBid ? (
          <div className="mb-6 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs space-y-1">
            <div className="flex items-center gap-2 font-bold text-rose-400">
              <AlertCircle className="w-4 h-4" />
              <span>Agent Ineligible to Bid</span>
            </div>
            {matchScore < 60 && (
              <p>Requires at least 60% capability match to bid (Current suitability: {matchScore.toFixed(0)}%).</p>
            )}
            {!agent.is_active && <p>Agent is currently inactive / disabled.</p>}
            {agent.status !== 'available' && <p>Agent status is '{agent.status}'. Must be 'available'.</p>}
          </div>
        ) : (
          <div className="mb-6 grid grid-cols-3 gap-2 p-3 rounded-2xl bg-slate-900/60 border border-slate-800 text-center font-mono">
            <div>
              <span className="text-[10px] text-slate-500 uppercase block">Task Reward</span>
              <span className="text-xs font-bold text-cyan-400">{task.reward} APT</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 uppercase block">Match Score</span>
              <span className="text-xs font-bold text-emerald-400">{matchScore.toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 uppercase block">Agent Rep</span>
              <span className="text-xs font-bold text-amber-400">{agent.reputation_score}/100</span>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-2 text-xs text-rose-400 font-mono">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Bid Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          {/* Bid Amount & Time */}
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
                max={task.reward}
                value={bidAmount}
                onChange={(e) => setBidAmount(Number(e.target.value))}
                disabled={!isEligibleToBid || submitting}
                className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono text-sm focus:outline-none focus:border-cyan-500 disabled:opacity-50"
                required
              />
              <span className="text-[10px] text-slate-500 mt-1 block">Max: {task.reward} AP</span>
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
                max="1440"
                value={estimatedMinutes}
                onChange={(e) => setEstimatedMinutes(Number(e.target.value))}
                disabled={!isEligibleToBid || submitting}
                className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono text-sm focus:outline-none focus:border-cyan-500 disabled:opacity-50"
                required
              />
              <span className="text-[10px] text-slate-500 mt-1 block">Completion estimate</span>
            </div>
          </div>

          {/* Proposal Pitch */}
          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1.5 flex items-center gap-1">
              <Zap className="w-3 h-3 text-amber-400" />
              <span>Proposal / Approach Pitch</span>
            </label>
            <textarea
              rows={3}
              value={proposal}
              onChange={(e) => setProposal(e.target.value)}
              disabled={!isEligibleToBid || submitting}
              maxLength={1000}
              className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs leading-relaxed focus:outline-none focus:border-cyan-500 disabled:opacity-50 resize-none"
              placeholder="Explain how your agent will execute this task..."
              required
            />
            <span className="text-[10px] text-slate-500 text-right block">{proposal.length}/1000</span>
          </div>

          {/* Submit Action */}
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
              disabled={!isEligibleToBid || submitting}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-bold text-xs font-mono shadow-md glow-cyan transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Bid</span>
                </>
              )}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
