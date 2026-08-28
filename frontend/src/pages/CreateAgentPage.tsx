import React, { useState } from 'react';
import { Bot, PlusCircle, ArrowLeft, AlertCircle, CheckCircle2, Loader2, X } from 'lucide-react';
import { NavTab } from '../components/Navbar';
import { createAgent, AgentCreatePayload } from '../services/api';

interface CreateAgentPageProps {
  onNavigate: (tab: NavTab) => void;
}

const CAPABILITY_OPTIONS = [
  'NLP', 'Sentiment Analysis', 'Summarization', 'Research', 'Data Analysis',
  'Classification', 'Code Analysis', 'Verification', 'Quality Evaluation',
  'Content Generation', 'Translation', 'Image Analysis', 'Forecasting',
];

const FORM_DEFAULTS: AgentCreatePayload = {
  name: '',
  agent_type: 'worker',
  description: '',
  capabilities: [],
  status: 'available',
};

export const CreateAgentPage: React.FC<CreateAgentPageProps> = ({ onNavigate }) => {
  const [form, setForm] = useState<AgentCreatePayload>(FORM_DEFAULTS);
  const [customCap, setCustomCap] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ code: string; id: number } | null>(null);

  const toggleCap = (cap: string) => {
    setForm(prev => ({
      ...prev,
      capabilities: prev.capabilities.includes(cap)
        ? prev.capabilities.filter(c => c !== cap)
        : [...prev.capabilities, cap],
    }));
  };

  const addCustomCap = () => {
    const t = customCap.trim();
    if (t && !form.capabilities.includes(t)) {
      setForm(prev => ({ ...prev, capabilities: [...prev.capabilities, t] }));
    }
    setCustomCap('');
  };

  const removeCap = (cap: string) => {
    setForm(prev => ({ ...prev, capabilities: prev.capabilities.filter(c => c !== cap) }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) { setError('Agent name is required.'); return; }
    if (form.capabilities.length === 0) { setError('At least one capability must be selected.'); return; }

    setSubmitting(true);
    setError(null);
    try {
      const agent = await createAgent(form);
      setSuccess({ code: agent.agent_code, id: agent.id });
      setForm(FORM_DEFAULTS);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-[#F7F8FA] px-4 sm:px-6 lg:px-8 py-10">
        <div className="max-w-2xl mx-auto">
          <div className="glass-panel rounded-2xl border border-emerald-200 p-10 text-center flex flex-col items-center gap-6">
            <div className="w-20 h-20 rounded-2xl bg-emerald-500/20 border border-emerald-200 flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-emerald-700" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-[#18202F] mb-2">Agent Registered!</h2>
              <p className="text-[#596273] text-sm">Your AI agent has been deployed to the network.</p>
              <div className="mt-4 px-5 py-2 bg-white border border-slate-200 rounded-xl inline-block">
                <span className="font-mono text-[#3155D9] font-semibold text-lg">{success.code}</span>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => onNavigate('agents')}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-cyan-500 to-indigo-500 text-white hover:opacity-90 transition-all"
              >
                View Agent Directory
              </button>
              <button
                onClick={() => setSuccess(null)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium bg-white border border-slate-200 text-[#334155] hover:text-white transition-all"
              >
                Register Another
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F7F8FA] px-4 sm:px-6 lg:px-8 py-10">
      <div className="max-w-2xl mx-auto space-y-6">

        {/* Header */}
        <div>
          <button
            onClick={() => onNavigate('agents')}
            className="flex items-center gap-2 text-[#596273] hover:text-[#18202F] text-sm mb-5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Agent Directory
          </button>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 border border-blue-200 flex items-center justify-center">
              <Bot className="w-5 h-5 text-[#3155D9]" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[#18202F]">Register Agent</h1>
              <p className="text-[#596273] text-sm">Deploy a new autonomous AI agent to the network.</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-3 p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="glass-panel rounded-2xl border border-slate-200 p-6 space-y-5">

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-[#334155] mb-1.5">Agent Name <span className="text-rose-700">*</span></label>
            <input
              type="text"
              placeholder="e.g. NLP-Agent-02"
              value={form.name}
              onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
              className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-[#18202F] placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 transition-colors"
              required
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium text-[#334155] mb-1.5">Agent Type <span className="text-rose-700">*</span></label>
            <div className="grid grid-cols-3 gap-2">
              {(['worker', 'verifier', 'orchestrator'] as const).map(t => (
                <button
                  type="button"
                  key={t}
                  onClick={() => setForm(p => ({ ...p, agent_type: t }))}
                  className={`px-4 py-2.5 rounded-lg text-sm font-medium border transition-all capitalize ${
                    form.agent_type === t
                      ? 'border-cyan-500/60 bg-blue-50 text-[#3155D9]'
                      : 'border-slate-300 bg-white text-[#596273] hover:text-[#18202F] hover:border-slate-600'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-[#334155] mb-1.5">Description <span className="text-rose-700">*</span></label>
            <textarea
              placeholder="Describe what this agent specializes in, its approach, and unique strengths…"
              rows={3}
              value={form.description}
              onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
              className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-[#18202F] placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 transition-colors resize-none"
              required
            />
          </div>

          {/* Capabilities */}
          <div>
            <label className="block text-sm font-medium text-[#334155] mb-1.5">
              Capabilities <span className="text-rose-700">*</span>
              <span className="ml-2 text-[#87909F] font-normal text-xs">({form.capabilities.length} selected)</span>
            </label>
            <div className="flex flex-wrap gap-2 mb-3">
              {CAPABILITY_OPTIONS.map(cap => (
                <button
                  type="button"
                  key={cap}
                  onClick={() => toggleCap(cap)}
                  className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                    form.capabilities.includes(cap)
                      ? 'border-indigo-500/60 bg-indigo-500/20 text-[#172554]'
                      : 'border-slate-300 bg-white text-[#596273] hover:text-[#18202F] hover:border-slate-600'
                  }`}
                >
                  {cap}
                </button>
              ))}
            </div>
            {/* Custom capability input */}
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Add custom capability…"
                value={customCap}
                onChange={e => setCustomCap(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addCustomCap(); } }}
                className="flex-1 px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs text-[#18202F] placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 transition-colors"
              />
              <button type="button" onClick={addCustomCap} className="px-3 py-2 rounded-lg text-xs font-medium bg-white border border-slate-300 text-[#334155] hover:text-white transition-colors">
                Add
              </button>
            </div>
            {/* Selected caps chips */}
            {form.capabilities.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {form.capabilities.map(cap => (
                  <span key={cap} className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium bg-indigo-500/20 text-[#172554] border border-slate-200">
                    {cap}
                    <button type="button" onClick={() => removeCap(cap)} className="hover:text-rose-700 transition-colors"><X className="w-2.5 h-2.5" /></button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-[#334155] mb-1.5">Initial Status</label>
            <select
              value={form.status}
              onChange={e => setForm(p => ({ ...p, status: e.target.value as any }))}
              className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-[#18202F] focus:outline-none focus:border-cyan-500/60 appearance-none transition-colors"
            >
              {['available', 'offline'].map(s => (
                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl font-semibold text-sm bg-gradient-to-r from-cyan-500 to-indigo-500 text-white hover:opacity-90 transition-all glow-cyan disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Registering Agent…</>
            ) : (
              <><PlusCircle className="w-4 h-4" /> Register Agent</>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default CreateAgentPage;
