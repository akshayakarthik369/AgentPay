import React, { useState } from 'react';
import { PlusCircle, CheckCircle2, ArrowRight, Shield, Award, AlertCircle, Loader2 } from 'lucide-react';
import { NavTab } from '../components/Navbar';
import { createTask } from '../services/api';

interface CreateTaskPageProps {
  onNavigate: (tab: NavTab) => void;
}

export const CreateTaskPage: React.FC<CreateTaskPageProps> = ({ onNavigate }) => {
  const [submitted, setSubmitted] = useState(false);
  const [createdTaskCode, setCreatedTaskCode] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Set default deadline to 7 days from today
  const defaultDeadline = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  const [formData, setFormData] = useState({
    title: 'Customer Review Sentiment Analysis',
    description: 'Analyze 500 customer reviews and classify them into positive, neutral, and negative sentiment with confidence metrics.',
    category: 'NLP',
    capability: 'NLP / Sentiment Classification',
    reward: '100',
    deadline: defaultDeadline,
    minReputation: '80',
    minQualityScore: '85'
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    setErrorMessage(null);

    // Basic frontend validation
    const rewardNum = parseFloat(formData.reward);
    const minRepNum = parseInt(formData.minReputation, 10);
    const minQualNum = parseInt(formData.minQualityScore, 10);

    if (!formData.title.trim()) {
      setErrorMessage('Task Title is required.');
      return;
    }
    if (!formData.description.trim()) {
      setErrorMessage('Task Description is required.');
      return;
    }
    if (isNaN(rewardNum) || rewardNum <= 0) {
      setErrorMessage('Reward must be greater than 0 AP Credits.');
      return;
    }
    if (isNaN(minRepNum) || minRepNum < 0 || minRepNum > 100) {
      setErrorMessage('Minimum Reputation Score must be between 0 and 100.');
      return;
    }
    if (isNaN(minQualNum) || minQualNum < 0 || minQualNum > 100) {
      setErrorMessage('Minimum Quality Score must be between 0 and 100.');
      return;
    }

    setIsSubmitting(true);

    try {
      // Format deadline date as ISO string at end of day
      const deadlineIso = new Date(`${formData.deadline}T23:59:59`).toISOString();

      const created = await createTask({
        title: formData.title.trim(),
        description: formData.description.trim(),
        category: formData.category,
        required_capability: formData.capability.trim(),
        reward: rewardNum,
        deadline: deadlineIso,
        minimum_reputation: minRepNum,
        minimum_quality_score: minQualNum,
      });

      setCreatedTaskCode(created.task_code || `AP-${created.id}`);
      setSubmitted(true);

      // Auto navigate after brief delay or let user click
      setTimeout(() => {
        onNavigate('tasks');
      }, 2000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Unable to create task. Please check the entered details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-10 px-4 sm:px-6">
      
      {/* Header */}
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-[#3155D9] border border-blue-200 text-xs font-mono mb-3">
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Task Publishing Wizard</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-[#172554]">Create New Task</h1>
        <p className="text-sm text-[#596273] mt-1">
          Specify task requirements, set AP Credit escrows, and define minimum AI agent verification thresholds.
        </p>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="glass-panel p-4 rounded-2xl border border-rose-500/40 bg-rose-50 mb-6 flex items-center gap-3 text-rose-800 text-xs font-semibold animate-fadeIn">
          <AlertCircle className="w-5 h-5 text-rose-700 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Success Notification Banner */}
      {submitted && (
        <div className="glass-panel p-6 rounded-2xl border border-emerald-500/40 bg-emerald-50 mb-8 animate-fadeIn">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-700">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-base font-bold text-emerald-800">
                  Task {createdTaskCode} published successfully!
                </h4>
                <p className="text-xs text-[#334155]">
                  Escrow locked: {formData.reward} AP Credits. Autonomous AI agents can now discover and bid on this task. Redirecting to Marketplace...
                </p>
              </div>
            </div>
            <button
              onClick={() => onNavigate('tasks')}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition-colors cursor-pointer"
            >
              <span>View in Marketplace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Form Container */}
      <form onSubmit={handleSubmit} className="glass-panel p-6 sm:p-10 rounded-3xl border border-slate-200 space-y-6">
        
        {/* Task Title */}
        <div>
          <label className="block text-xs font-mono uppercase text-[#334155] font-semibold mb-2">
            Task Title *
          </label>
          <input
            type="text"
            required
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            disabled={isSubmitting}
            className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm text-[#18202F] focus:outline-none focus:border-cyan-500/50 transition-colors disabled:opacity-50"
            placeholder="e.g. Customer Review Sentiment Analysis"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-mono uppercase text-[#334155] font-semibold mb-2">
            Task Description *
          </label>
          <textarea
            required
            rows={4}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            disabled={isSubmitting}
            className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm text-[#18202F] focus:outline-none focus:border-cyan-500/50 transition-colors disabled:opacity-50"
            placeholder="Describe the problem, input data structure, and required deliverable output..."
          />
        </div>

        {/* Grid: Category & Required Capability */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-mono uppercase text-[#334155] font-semibold mb-2">
              Category *
            </label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              disabled={isSubmitting}
              className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm text-[#18202F] focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
            >
              <option value="NLP">NLP</option>
              <option value="Research">Research</option>
              <option value="Data Analysis">Data Analysis</option>
              <option value="Content">Content Generation</option>
              <option value="Model Evaluation">Model Evaluation</option>
              <option value="Security">Code Analysis & Security</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-[#334155] font-semibold mb-2">
              Required Capability *
            </label>
            <input
              type="text"
              required
              value={formData.capability}
              onChange={(e) => setFormData({ ...formData, capability: e.target.value })}
              disabled={isSubmitting}
              className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm text-[#18202F] focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
              placeholder="e.g. NLP / Sentiment Classification"
            />
          </div>
        </div>

        {/* Grid: Reward & Deadline */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-mono uppercase text-[#334155] font-semibold mb-2 flex items-center justify-between">
              <span>Reward (AP Credits) *</span>
              <span className="text-[#6D5BD0] font-mono text-[10px]">Escrow Deposit</span>
            </label>
            <div className="relative">
              <input
                type="number"
                required
                min="1"
                step="any"
                value={formData.reward}
                onChange={(e) => setFormData({ ...formData, reward: e.target.value })}
                disabled={isSubmitting}
                className="w-full bg-white border border-slate-200 rounded-xl pl-4 pr-16 py-3 text-sm text-[#6D5BD0] font-mono font-bold focus:outline-none focus:border-purple-500/50 disabled:opacity-50"
                placeholder="100"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-mono text-[#596273]">
                AP Credits
              </span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-[#334155] font-semibold mb-2">
              Deadline *
            </label>
            <input
              type="date"
              required
              value={formData.deadline}
              onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
              disabled={isSubmitting}
              className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm text-[#18202F] focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
            />
          </div>
        </div>

        {/* Grid: Quality Thresholds */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 p-4 rounded-2xl bg-white border border-slate-200">
          <div>
            <label className="block text-xs font-mono uppercase text-[#334155] font-semibold mb-2 flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5 text-[#3155D9]" />
              <span>Minimum Reputation Score</span>
            </label>
            <input
              type="number"
              min="0"
              max="100"
              value={formData.minReputation}
              onChange={(e) => setFormData({ ...formData, minReputation: e.target.value })}
              disabled={isSubmitting}
              className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-[#18202F] font-mono focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
            />
            <p className="text-[11px] text-[#596273] mt-1">Min agent reputation score (0-100)</p>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-[#334155] font-semibold mb-2 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-yellow-400" />
              <span>Minimum Quality Score (%)</span>
            </label>
            <input
              type="number"
              min="0"
              max="100"
              value={formData.minQualityScore}
              onChange={(e) => setFormData({ ...formData, minQualityScore: e.target.value })}
              disabled={isSubmitting}
              className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-[#18202F] font-mono focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
            />
            <p className="text-[11px] text-[#596273] mt-1">Verifier pass threshold requirement</p>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-4 flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 disabled:from-slate-700 disabled:to-slate-800 text-[#18202F] font-bold text-sm shadow-lg glow-cyan transition-all disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin text-[#172554]" />
                <span>Publishing...</span>
              </>
            ) : (
              <>
                <PlusCircle className="w-5 h-5" />
                <span>Publish Task</span>
              </>
            )}
          </button>
        </div>

      </form>

    </div>
  );
};
