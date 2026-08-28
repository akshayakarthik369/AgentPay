import React, { useEffect, useState } from 'react';
import { 
  LayoutDashboard, 
  PlusCircle, 
  ListOrdered, 
  Wallet, 
  Receipt, 
  ShieldAlert, 
  Settings, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  XCircle, 
  ArrowUpRight, 
  Bot, 
  Sparkles,
  TrendingUp,
  Activity,
  Layers
} from 'lucide-react';
import { fetchClientDashboardMetrics, fetchActivity, ClientDashboardMetrics, ActivityEvent } from '../services/api';
import { NavTab } from './Navbar';
import { Interactive3DCard } from './Interactive3DCard';
import { APTokenBadge } from './APTokenBadge';

interface ClientDashboardProps {
  onNavigate: (tab: NavTab) => void;
  onSelectTask?: (taskId: string) => void;
  onSelectSettlement?: (settlementId: number) => void;
}

export interface TaskItem {
  id: string;
  name: string;
  category: string;
  reward: string;
  status: 'Pending' | 'Active' | 'Completed' | 'Failed';
  agent: string;
  createdDate: string;
}

export const ClientDashboard: React.FC<ClientDashboardProps> = ({ onNavigate, onSelectTask }) => {
  const [metrics, setMetrics] = useState<ClientDashboardMetrics | null>(null);
  const [realActivities, setRealActivities] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeSidebarItem, setActiveSidebarItem] = useState<string>('Dashboard');

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        const [data, acts] = await Promise.all([
          fetchClientDashboardMetrics().catch(() => null),
          fetchActivity({ limit: 6 }).catch(() => []),
        ]);
        if (data) setMetrics(data);
        else {
          setMetrics({
            total_tasks: 12,
            active_tasks: 3,
            completed_tasks: 9,
            total_spent: 850
          });
        }
        setRealActivities(acts);
      } catch (err) {
        console.error("Failed to load dashboard metrics from backend:", err);
        setMetrics({
          total_tasks: 12,
          active_tasks: 3,
          completed_tasks: 9,
          total_spent: 850
        });
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  // Sidebar items
  const sidebarItems = [
    { name: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" />, targetTab: 'client-dashboard' as NavTab },
    { name: 'Create Task', icon: <PlusCircle className="w-4 h-4" />, targetTab: 'create-task' as NavTab },
    { name: 'My Tasks', icon: <ListOrdered className="w-4 h-4" />, targetTab: 'tasks' as NavTab },
    { name: 'Wallet', icon: <Wallet className="w-4 h-4" />, targetTab: 'wallet' as NavTab },
    { name: 'Transactions', icon: <Receipt className="w-4 h-4" />, targetTab: 'wallet' as NavTab },
    { name: 'Disputes', icon: <ShieldAlert className="w-4 h-4" />, targetTab: 'disputes' as NavTab },
    { name: 'Settings', icon: <Settings className="w-4 h-4" />, targetTab: 'client-dashboard' as NavTab },
  ];

  // Mock task data per specification
  const mockTasks: TaskItem[] = [
    {
      id: 'TASK-101',
      name: 'Customer Review Sentiment Analysis',
      category: 'NLP',
      reward: '100 AP',
      status: 'Completed',
      agent: 'NLP-Agent-01',
      createdDate: '2026-08-27'
    },
    {
      id: 'TASK-102',
      name: 'Summarize Research Document',
      category: 'Research',
      reward: '80 AP',
      status: 'Active',
      agent: 'Research-Agent-02',
      createdDate: '2026-08-28'
    },
    {
      id: 'TASK-103',
      name: 'Product Description Generation',
      category: 'Content',
      reward: '50 AP',
      status: 'Pending',
      agent: 'Not Assigned',
      createdDate: '2026-08-28'
    },
    {
      id: 'TASK-104',
      name: 'Code Vulnerability Audit',
      category: 'Security',
      reward: '250 AP',
      status: 'Failed',
      agent: 'Audit-Bot-X',
      createdDate: '2026-08-26'
    }
  ];

  // Mock activity feed per specification
  const recentActivities = [
    {
      id: 'act-1',
      title: 'NLP-Agent-01 completed "Customer Review Sentiment Analysis"',
      time: '10 mins ago',
      type: 'success',
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />
    },
    {
      id: 'act-2',
      title: 'Task verification completed successfully',
      time: '12 mins ago',
      type: 'info',
      icon: <Sparkles className="w-4 h-4 text-[#3155D9]" />
    },
    {
      id: 'act-3',
      title: '100 AP Credits verified and ready for settlement',
      time: '12 mins ago',
      type: 'payment',
      icon: <Wallet className="w-4 h-4 text-[#6D5BD0]" />
    },
    {
      id: 'act-4',
      title: 'Research-Agent-02 started assigned task workflow',
      time: '1 hour ago',
      type: 'active',
      icon: <Bot className="w-4 h-4 text-[#172033]" />
    }
  ];

  const renderStatusBadge = (status: TaskItem['status']) => {
    switch (status) {
      case 'Completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Completed
          </span>
        );
      case 'Active':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-[#172033] border border-blue-200">
            <Clock className="w-3.5 h-3.5 animate-pulse text-[#3155D9]" />
            Active
          </span>
        );
      case 'Pending':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-300">
            <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
            Pending
          </span>
        );
      case 'Failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-300">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            Failed
          </span>
        );
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      <div className="flex flex-col lg:flex-row gap-8">
        
        {/* Sidebar Navigation */}
        <aside className="w-full lg:w-64 shrink-0">
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm sticky top-24">
            <div className="px-3 py-2 text-[11px] font-mono text-[#5B6475] font-bold uppercase tracking-wider mb-2">
              Client Portal
            </div>
            <nav className="space-y-1">
              {sidebarItems.map((item) => {
                const isActive = activeSidebarItem === item.name;
                return (
                  <button
                    key={item.name}
                    onClick={() => {
                      setActiveSidebarItem(item.name);
                      if (item.name !== 'Dashboard') {
                        onNavigate(item.targetTab);
                      }
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-semibold transition-all duration-150 cursor-pointer ${
                      isActive
                        ? 'bg-blue-50 text-[#3155D9] border border-blue-200 font-bold'
                        : 'text-[#172033] hover:text-[#111827] hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className={isActive ? 'text-[#3155D9]' : 'text-[#5B6475]'}>
                        {item.icon}
                      </span>
                      <span>{item.name}</span>
                    </div>
                    {item.name !== 'Dashboard' && (
                      <span className="text-[10px] font-mono font-medium text-[#5B6475] bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                        Demo
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 space-y-8 min-w-0">
          
          {/* Header Section */}
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-blue-500/05 via-indigo-500/05 to-transparent blur-3xl pointer-events-none" />
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative z-10">
              <div>
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 text-[#3155D9] border border-blue-200 text-xs font-mono font-bold mb-3">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Phase 2 Operational</span>
                </div>
                <h1 className="text-3xl sm:text-4xl font-black text-[#172033] tracking-tight">
                  Welcome to AgentPay
                </h1>
                <p className="text-sm sm:text-base text-[#5B6475] mt-2 max-w-2xl leading-relaxed">
                  Manage tasks, monitor AI agent activity, and track your autonomous workflows in real time.
                </p>
              </div>

              {/* Quick Actions Buttons */}
              <div className="flex items-center gap-3 shrink-0">
                <button
                  onClick={() => onNavigate('create-task')}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#172033] via-[#1E3A8A] to-[#3155D9] hover:brightness-110 text-white font-semibold text-xs sm:text-sm shadow-md transition-all cursor-pointer"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Create New Task</span>
                </button>
                <button
                  onClick={() => onNavigate('tasks')}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-[#172033] font-semibold text-xs sm:text-sm border border-slate-200 shadow-sm transition-all cursor-pointer"
                >
                  <ListOrdered className="w-4 h-4 text-[#3155D9]" />
                  <span>View All Tasks</span>
                </button>
              </div>
            </div>
          </div>

          {/* 4 Summary Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            
            {/* Card 1: Total Tasks */}
            <Interactive3DCard level="interactive" glowColor="blue" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono font-bold text-[#5B6475] uppercase tracking-wider">Total Tasks</span>
                <div className="p-2 rounded-xl bg-blue-50 text-[#3155D9] border border-blue-200">
                  <Layers className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black font-mono text-[#172033]">
                {loading ? '...' : metrics?.total_tasks ?? 12}
              </div>
              <p className="text-xs text-[#5B6475] flex items-center gap-1 font-medium">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                <span>Across all categories</span>
              </p>
            </Interactive3DCard>

            {/* Card 2: Active Tasks */}
            <Interactive3DCard level="interactive" glowColor="blue" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono font-bold text-[#5B6475] uppercase tracking-wider">Active Tasks</span>
                <div className="p-2 rounded-xl bg-blue-50 text-[#3155D9] border border-blue-200">
                  <Clock className="w-4 h-4 animate-spin text-[#3155D9]" />
                </div>
              </div>
              <div className="text-3xl font-black font-mono text-[#3155D9]">
                {loading ? '...' : metrics?.active_tasks ?? 3}
              </div>
              <p className="text-xs text-[#5B6475] font-medium">Currently assigned to agents</p>
            </Interactive3DCard>

            {/* Card 3: Completed Tasks */}
            <Interactive3DCard level="interactive" glowColor="emerald" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono font-bold text-[#5B6475] uppercase tracking-wider">Completed Tasks</span>
                <div className="p-2 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black font-mono text-emerald-800">
                {loading ? '...' : metrics?.completed_tasks ?? 9}
              </div>
              <p className="text-xs text-[#5B6475] font-medium">Verified deliverable outcomes</p>
            </Interactive3DCard>

            {/* Card 4: Total Spent */}
            <Interactive3DCard level="interactive" glowColor="gold" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono font-bold text-[#5B6475] uppercase tracking-wider">Total Allocated</span>
                <div className="p-2 rounded-xl bg-amber-50 text-amber-700 border border-amber-200">
                  <Wallet className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black font-mono text-amber-800">
                {loading ? '...' : `${metrics?.total_spent ?? 850} AP`}
              </div>
              <p className="text-xs text-[#5B6475] font-medium">Task budget rewards</p>
            </Interactive3DCard>

          </div>

          {/* Recent Tasks Table Section */}
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
              <div>
                <h3 className="text-xl font-bold text-[#172033] flex items-center gap-2">
                  <ListOrdered className="w-5 h-5 text-[#3155D9]" />
                  <span>Recent Tasks</span>
                </h3>
                <p className="text-xs text-[#5B6475] mt-0.5">Overview of latest task assignments and execution state</p>
              </div>
              <button 
                onClick={() => onNavigate('tasks')} 
                className="text-xs font-bold text-[#3155D9] hover:text-blue-800 flex items-center gap-1 cursor-pointer transition-colors"
              >
                <span>View Full Market</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-[#172033] font-mono text-xs uppercase tracking-wider font-bold bg-slate-50/50">
                    <th className="py-3 px-3">Task Name</th>
                    <th className="py-3 px-3">Category</th>
                    <th className="py-3 px-3">Reward</th>
                    <th className="py-3 px-3">Status</th>
                    <th className="py-3 px-3">Assigned Agent</th>
                    <th className="py-3 px-3 text-right">Created Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {mockTasks.map((task) => (
                    <tr key={task.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-4 px-3">
                        <div className="font-bold text-[#172033] text-sm">{task.name}</div>
                        <div className="text-xs font-mono font-semibold text-[#3155D9] mt-0.5">{task.id}</div>
                      </td>
                      <td className="py-4 px-3">
                        <span className="px-2.5 py-1 rounded-md text-xs font-mono font-semibold bg-slate-100 text-[#172033] border border-slate-200">
                          {task.category}
                        </span>
                      </td>
                      <td className="py-4 px-3 font-mono font-bold text-[#172033]">
                        {task.reward}
                      </td>
                      <td className="py-4 px-3">
                        {renderStatusBadge(task.status)}
                      </td>
                      <td className="py-4 px-3 font-mono font-medium">
                        {task.agent === 'Not Assigned' ? (
                          <span className="text-[#87909F] italic">Not Assigned</span>
                        ) : (
                          <span className="flex items-center gap-1.5 text-[#172033] font-semibold">
                            <Bot className="w-4 h-4 text-[#3155D9]" />
                            {task.agent}
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-3 text-right font-mono text-[#5B6475] text-xs font-medium">
                        {task.createdDate}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Activity Section (Phase 17) */}
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-200">
              <div>
                <h3 className="text-xl font-bold text-[#172033] flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-600" />
                  <span>Recent Activity</span>
                </h3>
                <p className="text-xs text-[#5B6475] mt-0.5">Real-time log of agent operations, verifications, and workflow events</p>
              </div>

              <button
                onClick={() => onNavigate('activity')}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-xs transition-colors self-start sm:self-auto"
              >
                <span>View Full Audit Trail</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="space-y-3">
              {realActivities.length > 0 ? (
                realActivities.map((act, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-50/60 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-center gap-3.5">
                      <div className="p-2 rounded-xl bg-white border border-slate-200 shadow-xs text-blue-600 shrink-0">
                        <Activity className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs sm:text-sm font-semibold text-[#172033]">{act.title}</div>
                        <p className="text-xs text-slate-500 line-clamp-1">{act.description}</p>
                      </div>
                    </div>
                    <span className="text-xs font-mono font-medium text-[#5B6475] shrink-0 ml-0 sm:ml-4">
                      {act.created_at ? new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent'}
                    </span>
                  </div>
                ))
              ) : (
                recentActivities.map((act) => (
                  <div key={act.id} className="p-4 rounded-xl bg-slate-50/60 border border-slate-200/80 flex items-center justify-between hover:bg-slate-50 transition-colors">
                    <div className="flex items-center gap-3.5">
                      <div className="p-2 rounded-xl bg-white border border-slate-200 shadow-xs">
                        {act.icon}
                      </div>
                      <span className="text-xs sm:text-sm font-semibold text-[#172033]">{act.title}</span>
                    </div>
                    <span className="text-xs font-mono font-medium text-[#5B6475] shrink-0 ml-4">{act.time}</span>
                  </div>
                ))
              )}
            </div>
          </div>


        </main>

      </div>
    </div>
  );
};
