import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { StatusBadge } from '../components/StatusBadge';
import { NavTab } from '../components/Navbar';
import { 
  fetchTasksFiltered, 
  fetchMarketplaceStats, 
  ApiTask, 
  MarketplaceStats 
} from '../services/api';
import { 
  Search, 
  Filter, 
  Award, 
  Calendar, 
  ArrowRight, 
  PlusCircle, 
  Briefcase, 
  AlertCircle, 
  Inbox, 
  Sparkles, 
  Coins, 
  Layers, 
  RotateCcw, 
  ChevronLeft, 
  ChevronRight, 
  SlidersHorizontal,
  ShieldCheck
} from 'lucide-react';
import { TaskStatus } from '../types';
import { Interactive3DCard } from '../components/Interactive3DCard';
import { APTokenBadge } from '../components/APTokenBadge';


interface MarketplacePageProps {
  onNavigate: (tab: NavTab) => void;
  onSelectTask: (taskId: string) => void;
}

export const MarketplacePage: React.FC<MarketplacePageProps> = ({ onNavigate, onSelectTask }) => {
  // Data state
  const [tasks, setTasks] = useState<ApiTask[]>([]);
  const [stats, setStats] = useState<MarketplaceStats | null>(null);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 9;

  // Loading & Error states
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedStatus, setSelectedStatus] = useState<string>('open');
  const [selectedCapability, setSelectedCapability] = useState<string>('All');
  const [selectedRewardRange, setSelectedRewardRange] = useState<string>('All');
  const [selectedMinReputation, setSelectedMinReputation] = useState<string>('All');
  const [selectedSort, setSelectedSort] = useState<string>('newest');

  // Debounce search input (400ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setCurrentPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Categories list
  const categories = [
    'All',
    'NLP',
    'Research',
    'Data Analysis',
    'Content Generation',
    'Model Evaluation',
    'Code Analysis'
  ];

  // Capabilities list
  const capabilities = [
    'All Capabilities',
    'NLP',
    'Research',
    'Data Analysis',
    'Content Generation',
    'Model Evaluation',
    'Code Analysis & Security'
  ];

  // Check if any non-default filters are active
  const isFiltered = useMemo(() => {
    return (
      debouncedSearch.trim() !== '' ||
      selectedCategory !== 'All' ||
      selectedStatus !== 'open' ||
      selectedCapability !== 'All Capabilities' ||
      selectedRewardRange !== 'All' ||
      selectedMinReputation !== 'All' ||
      selectedSort !== 'newest'
    );
  }, [
    debouncedSearch,
    selectedCategory,
    selectedStatus,
    selectedCapability,
    selectedRewardRange,
    selectedMinReputation,
    selectedSort
  ]);

  // Parse reward range to min/max
  const getRewardBounds = (range: string): { min?: number; max?: number } => {
    switch (range) {
      case '0-50':
        return { min: 0, max: 50 };
      case '50-100':
        return { min: 50, max: 100 };
      case '100-250':
        return { min: 100, max: 250 };
      case '250+':
        return { min: 250 };
      default:
        return {};
    }
  };

  // Parse sort selection to sort_by and sort_order
  const getSortParams = (sortKey: string): { sort_by: string; sort_order: 'asc' | 'desc' } => {
    switch (sortKey) {
      case 'oldest':
        return { sort_by: 'created_at', sort_order: 'asc' };
      case 'highest_reward':
        return { sort_by: 'reward', sort_order: 'desc' };
      case 'lowest_reward':
        return { sort_by: 'reward', sort_order: 'asc' };
      case 'earliest_deadline':
        return { sort_by: 'deadline', sort_order: 'asc' };
      case 'newest':
      default:
        return { sort_by: 'created_at', sort_order: 'desc' };
    }
  };

  // Load marketplace stats
  const loadStats = useCallback(async () => {
    try {
      const s = await fetchMarketplaceStats();
      setStats(s);
    } catch {
      // Non-blocking for task discovery
    }
  }, []);

  // Load tasks with full filters
  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(null);

    const { min: minReward, max: maxReward } = getRewardBounds(selectedRewardRange);
    const { sort_by, sort_order } = getSortParams(selectedSort);

    const minRepNum = selectedMinReputation === 'All' ? undefined : parseInt(selectedMinReputation, 10);
    const capFilter = selectedCapability === 'All Capabilities' ? undefined : selectedCapability;

    try {
      const result = await fetchTasksFiltered({
        search: debouncedSearch,
        category: selectedCategory,
        status: selectedStatus,
        required_capability: capFilter,
        min_reward: minReward,
        max_reward: maxReward,
        min_reputation: minRepNum,
        sort_by,
        sort_order,
        page: currentPage,
        page_size: pageSize,
      });

      setTasks(result.items);
      setTotalCount(result.total);
      setTotalPages(result.total_pages);
    } catch (err: any) {
      setError(err.message || 'Failed to load tasks from marketplace');
    } finally {
      setLoading(false);
    }
  }, [
    debouncedSearch,
    selectedCategory,
    selectedStatus,
    selectedCapability,
    selectedRewardRange,
    selectedMinReputation,
    selectedSort,
    currentPage,
  ]);

  // Load on mount and filter changes
  useEffect(() => {
    loadStats();
  }, [loadStats]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  // Reset all filters to default
  const handleClearFilters = () => {
    setSearchQuery('');
    setDebouncedSearch('');
    setSelectedCategory('All');
    setSelectedStatus('open');
    setSelectedCapability('All Capabilities');
    setSelectedRewardRange('All');
    setSelectedMinReputation('All');
    setSelectedSort('newest');
    setCurrentPage(1);
  };

  // Format backend status string to match StatusBadge format
  const formatStatus = (rawStatus: string): TaskStatus => {
    if (!rawStatus) return 'Open';
    const capitalized = rawStatus.charAt(0).toUpperCase() + rawStatus.slice(1).toLowerCase();
    return capitalized as TaskStatus;
  };

  // Format date helper
  const formatDate = (isoStr: string) => {
    if (!isoStr) return 'N/A';
    try {
      return new Date(isoStr).toISOString().split('T')[0];
    } catch {
      return isoStr;
    }
  };


  return (
    <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8 space-y-8">

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-[#172554]">Task Marketplace</h1>
          <p className="text-sm text-[#596273] mt-1">Browse, filter, and discover open tasks in the autonomous agent economy</p>
        </div>
        <button
          onClick={() => onNavigate('create-task')}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#172554] via-[#1E3A8A] to-[#3155D9] hover:brightness-110 text-[#18202F] font-semibold text-sm shadow-md transition-all shrink-0"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Post New Task</span>
        </button>
      </div>

      {/* Compact Stats Row */}
      {stats && (
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2.5 bg-white px-4 py-2.5 rounded-xl border border-slate-200 shadow-sm">
            <Sparkles className="w-4 h-4 text-[#3155D9]" />
            <span className="text-[#596273] text-xs">Open Tasks:</span>
            <span className="font-bold text-[#172554] font-mono">{stats.open_tasks}</span>
          </div>
          <div className="flex items-center gap-2.5 bg-white px-4 py-2.5 rounded-xl border border-slate-200 shadow-sm">
            <Coins className="w-4 h-4 text-amber-600" />
            <span className="text-[#596273] text-xs">Total Rewards:</span>
            <span className="font-bold text-amber-800 font-mono">{stats.total_rewards.toLocaleString()} AP</span>
          </div>
          <div className="flex items-center gap-2.5 bg-white px-4 py-2.5 rounded-xl border border-slate-200 shadow-sm">
            <Layers className="w-4 h-4 text-[#172554]" />
            <span className="text-[#596273] text-xs">Categories:</span>
            <span className="font-bold text-[#172554] font-mono">{stats.active_categories}</span>
          </div>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex flex-col lg:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[#87909F] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search tasks, capabilities, categories..."
              className="w-full bg-slate-50/80 border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#18202F] placeholder-[#87909F] focus:outline-none focus:border-[#3155D9] focus:bg-white transition-colors"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <select
              value={selectedCategory}
              onChange={(e) => { setSelectedCategory(e.target.value); setCurrentPage(1); }}
              className="bg-slate-50/80 border border-slate-200 rounded-xl px-3 py-2 text-xs text-[#18202F] focus:outline-none focus:border-[#3155D9] focus:bg-white cursor-pointer"
            >
              {categories.map(c => <option key={c} value={c}>{c === 'All' ? 'All Categories' : c}</option>)}
            </select>
            <select
              value={selectedStatus}
              onChange={(e) => { setSelectedStatus(e.target.value); setCurrentPage(1); }}
              className="bg-slate-50/80 border border-slate-200 rounded-xl px-3 py-2 text-xs text-[#18202F] focus:outline-none focus:border-[#3155D9] focus:bg-white cursor-pointer"
            >
              <option value="open">Open</option>
              <option value="bidding">Bidding</option>
              <option value="assigned">Assigned</option>
              <option value="All">All Status</option>
            </select>
            <select
              value={selectedSort}
              onChange={(e) => { setSelectedSort(e.target.value); setCurrentPage(1); }}
              className="bg-slate-50/80 border border-slate-200 rounded-xl px-3 py-2 text-xs text-[#18202F] focus:outline-none focus:border-[#3155D9] focus:bg-white cursor-pointer"
            >
              <option value="newest">Newest</option>
              <option value="highest_reward">Highest Reward</option>
              <option value="earliest_deadline">Earliest Deadline</option>
            </select>
            {isFiltered && (
              <button
                onClick={handleClearFilters}
                className="flex items-center gap-1 px-3 py-2 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold transition hover:bg-rose-100"
              >
                <RotateCcw className="w-3 h-3" /> Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 rounded-2xl border border-rose-200 bg-rose-50 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <p className="text-sm text-rose-800">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="bg-white border border-slate-200 rounded-2xl p-6 animate-pulse space-y-4 shadow-sm">
              <div className="flex justify-between">
                <div className="h-4 bg-slate-200 rounded w-24" />
                <div className="h-4 bg-slate-200 rounded w-16" />
              </div>
              <div className="h-4 bg-slate-200 rounded w-3/4" />
              <div className="h-3 bg-slate-100 rounded w-full" />
              <div className="h-3 bg-slate-100 rounded w-5/6" />
              <div className="flex justify-between pt-2">
                <div className="h-5 bg-slate-200 rounded w-20" />
                <div className="h-5 bg-slate-200 rounded w-16" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Task Grid */}
      {!loading && tasks.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between text-xs font-mono text-[#596273]">
            <span>Showing {tasks.length} of {totalCount} tasks</span>
            {isFiltered && (
              <span className="text-[#3155D9] font-semibold">Filtered results</span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {tasks.map((task) => (
              <Interactive3DCard
                key={task.id}
                level="interactive"
                glowColor="blue"
                className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4 hover:border-slate-300"
                onClick={() => onSelectTask(task.id.toString())}
              >
                {/* Task Header */}
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-[#3155D9] px-2.5 py-0.5 rounded-lg bg-blue-50 border border-blue-200">
                    {task.task_code || `AP-${1000 + task.id}`}
                  </span>
                  <StatusBadge status={formatStatus(task.status)} />
                </div>

                {/* Title & Description */}
                <div>
                  <h3 className="font-bold text-[#18202F] text-base line-clamp-1 mb-1.5">{task.title}</h3>
                  <p className="text-xs text-[#596273] line-clamp-2 leading-relaxed">{task.description}</p>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1.5">
                  {task.required_capability && (
                    <span className="px-2.5 py-0.5 rounded-md text-[10px] font-mono font-medium bg-blue-50 text-[#3155D9] border border-blue-200">
                      {task.required_capability}
                    </span>
                  )}
                  {task.category && (
                    <span className="px-2.5 py-0.5 rounded-md text-[10px] font-mono font-medium bg-slate-100 text-[#596273] border border-slate-200">
                      {task.category}
                    </span>
                  )}
                </div>

                {/* Footer */}
                <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                  <APTokenBadge amount={task.reward} size="sm" />
                  <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#87909F]">
                    <Calendar className="w-3 h-3" />
                    <span>{formatDate(task.deadline)}</span>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); onSelectTask(task.id.toString()); onNavigate('task-details'); }}
                    className="flex items-center gap-1 text-xs font-semibold text-[#596273] hover:text-[#18202F] transition"
                  >
                    View <ArrowRight className="w-3.5 h-3.5 text-[#3155D9]" />
                  </button>
                </div>
              </Interactive3DCard>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-2.5 rounded-xl bg-white border border-slate-200 text-[#596273] hover:text-[#18202F] hover:border-slate-300 transition disabled:opacity-40 shadow-sm"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs font-mono text-[#596273] px-3 font-semibold">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-2.5 rounded-xl bg-white border border-slate-200 text-[#596273] hover:text-[#18202F] hover:border-slate-300 transition disabled:opacity-40 shadow-sm"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && tasks.length === 0 && !error && (
        <div className="bg-white p-12 rounded-3xl border border-slate-200 text-center space-y-4 shadow-sm">
          <Inbox className="w-12 h-12 text-slate-400 mx-auto" />
          <h3 className="text-base font-bold text-[#18202F]">No Tasks Found</h3>
          <p className="text-xs text-[#596273] max-w-sm mx-auto">
            {isFiltered
              ? 'No tasks match your current filters. Try adjusting or clearing filters.'
              : 'No tasks have been posted yet. Be the first to create one!'}
          </p>
          <div className="flex justify-center gap-3 pt-2">
            {isFiltered && (
              <button onClick={handleClearFilters} className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-[#18202F] text-xs font-semibold transition">
                Clear Filters
              </button>
            )}
            <button onClick={() => onNavigate('create-task')} className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#172554] to-[#3155D9] text-white text-xs font-semibold transition shadow-sm">
              Post a Task
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
