/**
 * AgentPay API Client Service
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export interface HealthResponse {
  status: string;
}

export interface ClientDashboardMetrics {
  total_tasks: number;
  active_tasks: number;
  completed_tasks: number;
  total_spent: number;
}

export interface TaskCreatePayload {
  title: string;
  description: string;
  category: string;
  required_capability: string;
  reward: number;
  deadline: string; // ISO datetime string
  minimum_reputation: number;
  minimum_quality_score: number;
}

export interface ApiTask {
  id: number;
  task_code: string;
  title: string;
  description: string;
  category: string;
  required_capability: string;
  reward: number;
  deadline: string;
  minimum_reputation: number;
  minimum_quality_score: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedTaskResponse {
  items: ApiTask[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface TaskFilterParams {
  search?: string;
  category?: string;
  status?: string;
  required_capability?: string;
  min_reward?: number;
  max_reward?: number;
  min_reputation?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface MarketplaceStats {
  open_tasks: number;
  total_rewards: number;
  active_categories: number;
}

export async function checkBackendHealth(): Promise<HealthResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Backend health check failed:', error);
    throw error;
  }
}

export async function fetchClientDashboardMetrics(): Promise<ClientDashboardMetrics> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/client/dashboard`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Client dashboard metrics fetch failed:', error);
    throw error;
  }
}

export async function createTask(payload: TaskCreatePayload): Promise<ApiTask> {
  const response = await fetch(`${API_BASE_URL}/api/tasks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    let message = 'Unable to create task. Please check the entered details.';
    if (errorData?.detail) {
      if (typeof errorData.detail === 'string') {
        message = errorData.detail;
      } else if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
        message = errorData.detail.map((err: any) => err.msg || err.detail).join(', ');
      }
    }
    throw new Error(message);
  }

  return await response.json();
}

export async function fetchTasks(params?: TaskFilterParams): Promise<ApiTask[]> {
  const paginated = await fetchTasksFiltered(params || {});
  return paginated.items;
}

export async function fetchTasksFiltered(params: TaskFilterParams): Promise<PaginatedTaskResponse> {
  const query = new URLSearchParams();

  if (params.search && params.search.trim()) query.set('search', params.search.trim());
  if (params.category && params.category !== 'All') query.set('category', params.category);
  if (params.status && params.status !== 'All') query.set('status', params.status.toLowerCase());
  if (params.required_capability && params.required_capability !== 'All') query.set('required_capability', params.required_capability);
  if (params.min_reward !== undefined && params.min_reward !== null) query.set('min_reward', params.min_reward.toString());
  if (params.max_reward !== undefined && params.max_reward !== null) query.set('max_reward', params.max_reward.toString());
  if (params.min_reputation !== undefined && params.min_reputation !== null) query.set('min_reputation', params.min_reputation.toString());
  if (params.sort_by) query.set('sort_by', params.sort_by);
  if (params.sort_order) query.set('sort_order', params.sort_order);
  if (params.page) query.set('page', params.page.toString());
  if (params.page_size) query.set('page_size', params.page_size.toString());

  const queryString = query.toString();
  const url = `${API_BASE_URL}/api/tasks${queryString ? `?${queryString}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch tasks: ${response.statusText}`);
  }

  return await response.json();
}

export async function fetchTaskById(id: number): Promise<ApiTask> {
  const response = await fetch(`${API_BASE_URL}/api/tasks/${id}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Task not found');
    }
    throw new Error(`Failed to fetch task details: ${response.statusText}`);
  }

  return await response.json();
}

export async function fetchMarketplaceStats(): Promise<MarketplaceStats> {
  const response = await fetch(`${API_BASE_URL}/api/marketplace/stats`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch marketplace statistics: ${response.statusText}`);
  }

  return await response.json();
}

// ---------------------------------------------------------------------------
// Agent Types
// ---------------------------------------------------------------------------

export interface ApiAgent {
  id: number;
  agent_code: string;
  name: string;
  agent_type: 'worker' | 'verifier' | 'orchestrator';
  description: string;
  capabilities: string[];
  status: 'available' | 'busy' | 'offline' | 'suspended';
  is_active: boolean;
  reputation_score: number;
  wallet_balance: number;
  tasks_completed: number;
  tasks_failed: number;
  total_earned: number;
  success_rate?: number;
  average_verification_score?: number;
  created_at: string;
  updated_at: string;
}

export interface AgentCreatePayload {
  name: string;
  agent_type: 'worker' | 'verifier' | 'orchestrator';
  description: string;
  capabilities: string[];
  status?: 'available' | 'busy' | 'offline' | 'suspended';
}

export interface AgentUpdatePayload {
  name?: string;
  agent_type?: 'worker' | 'verifier' | 'orchestrator';
  description?: string;
  capabilities?: string[];
  status?: 'available' | 'busy' | 'offline' | 'suspended';
}

export interface AgentFilterParams {
  status?: string;
  agent_type?: string;
  capability?: string;
  is_active?: boolean;
}

export interface AgentSummaryForMatch {
  id: number;
  agent_code?: string;
  name: string;
  agent_type: string;
  capabilities: string[];
  status: string;
  is_active: boolean;
  reputation_score: number;
  wallet_balance: number;
}

export interface TaskSummaryForMatch {
  id: number;
  task_code?: string;
  title: string;
  category: string;
  required_capability: string;
  reward: number;
  deadline: string;
  minimum_reputation: number;
  minimum_quality_score: number;
  status: string;
}

export interface TaskMatchResult {
  task: TaskSummaryForMatch;
  overall_score: number;
  capability_score: number;
  reputation_score: number;
  quality_score: number;
  success_score: number;
  availability_score: number;
  eligible: boolean;
  match_level: 'excellent' | 'strong' | 'moderate' | 'weak' | 'poor';
  reasons: string[];
}

export interface AgentMatchResult {
  agent: AgentSummaryForMatch;
  overall_score: number;
  capability_score: number;
  reputation_score: number;
  quality_score: number;
  success_score: number;
  availability_score: number;
  eligible: boolean;
  match_level: 'excellent' | 'strong' | 'moderate' | 'weak' | 'poor';
  reasons: string[];
}

export interface SingleAgentTaskMatchResponse {
  agent: AgentSummaryForMatch;
  task: TaskSummaryForMatch;
  overall_score: number;
  capability_score: number;
  reputation_score: number;
  quality_score: number;
  success_score: number;
  availability_score: number;
  eligible: boolean;
  match_level: 'excellent' | 'strong' | 'moderate' | 'weak' | 'poor';
  reasons: string[];
}

export interface DiscoverableTaskMatchesResponse {
  agent: AgentSummaryForMatch;
  matches: TaskMatchResult[];
  total_matches: number;
}

export interface TaskMatchingAgentsResponse {
  task: TaskSummaryForMatch;
  agents: AgentMatchResult[];
  total_agents: number;
}

// ---------------------------------------------------------------------------
// Agent API Functions
// ---------------------------------------------------------------------------

export async function fetchAgents(params?: AgentFilterParams): Promise<ApiAgent[]> {
  const query = new URLSearchParams();
  if (params?.status && params.status !== 'All') query.set('status', params.status);
  if (params?.agent_type && params.agent_type !== 'All') query.set('agent_type', params.agent_type);
  if (params?.capability && params.capability !== 'All') query.set('capability', params.capability);
  if (params?.is_active !== undefined) query.set('is_active', String(params.is_active));

  const qs = query.toString();
  const url = `${API_BASE_URL}/api/agents${qs ? `?${qs}` : ''}`;
  const response = await fetch(url, { headers: { 'Accept': 'application/json' } });
  if (!response.ok) throw new Error(`Failed to fetch agents: ${response.statusText}`);
  return await response.json();
}

export async function fetchAgentById(id: number): Promise<ApiAgent> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${id}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    if (response.status === 404) throw new Error('Agent not found');
    throw new Error(`Failed to fetch agent: ${response.statusText}`);
  }
  return await response.json();
}

export async function createAgent(payload: AgentCreatePayload): Promise<ApiAgent> {
  const response = await fetch(`${API_BASE_URL}/api/agents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    let msg = 'Unable to register agent.';
    if (err?.detail) {
      msg = typeof err.detail === 'string' ? err.detail : err.detail.map((e: any) => e.msg).join(', ');
    }
    throw new Error(msg);
  }
  return await response.json();
}

export async function updateAgent(id: number, payload: AgentUpdatePayload): Promise<ApiAgent> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Failed to update agent: ${response.statusText}`);
  return await response.json();
}

export async function activateAgent(id: number): Promise<ApiAgent> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${id}/activate`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) throw new Error(`Failed to activate agent: ${response.statusText}`);
  return await response.json();
}

export async function deactivateAgent(id: number): Promise<ApiAgent> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${id}/deactivate`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) throw new Error(`Failed to deactivate agent: ${response.statusText}`);
  return await response.json();
}

export async function fetchDiscoverableTasks(
  agentId: number,
  params?: { min_score?: number; limit?: number }
): Promise<DiscoverableTaskMatchesResponse> {
  const query = new URLSearchParams();
  if (params?.min_score !== undefined) query.set('min_score', params.min_score.toString());
  if (params?.limit !== undefined) query.set('limit', params.limit.toString());

  const qs = query.toString();
  const url = `${API_BASE_URL}/api/agents/${agentId}/discoverable-tasks${qs ? `?${qs}` : ''}`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) throw new Error(`Failed to fetch discoverable tasks: ${response.statusText}`);
  return await response.json();
}

export async function fetchAgentTaskMatch(
  agentId: number,
  taskId: number
): Promise<SingleAgentTaskMatchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/match/${taskId}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) throw new Error(`Failed to calculate agent-task match: ${response.statusText}`);
  return await response.json();
}

export async function fetchMatchingAgentsForTask(
  taskId: number,
  params?: { min_score?: number; limit?: number }
): Promise<TaskMatchingAgentsResponse> {
  const query = new URLSearchParams();
  if (params?.min_score !== undefined) query.set('min_score', params.min_score.toString());
  if (params?.limit !== undefined) query.set('limit', params.limit.toString());

  const qs = query.toString();
  const url = `${API_BASE_URL}/api/tasks/${taskId}/matching-agents${qs ? `?${qs}` : ''}`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) throw new Error(`Failed to fetch matching agents: ${response.statusText}`);
  return await response.json();
}

// ---------------------------------------------------------------------------
// Phase 7 Bidding Types
// ---------------------------------------------------------------------------


export interface ApiBid {
  id: number;
  bid_code?: string;
  task_id: number;
  agent_id: number;
  bid_amount: number;
  estimated_completion_minutes: number;
  proposal: string;
  match_score_snapshot: number;
  reputation_snapshot: number;
  selection_score: number;
  status: 'pending' | 'accepted' | 'rejected' | 'withdrawn';
  created_at: string;
  updated_at: string;
  accepted_at?: string;
  rejected_at?: string;
  withdrawn_at?: string;
  agent?: {
    id: number;
    agent_code?: string;
    name: string;
    agent_type: string;
    reputation_score: number;
    status: string;
  };
  task?: {
    id: number;
    task_code?: string;
    title: string;
    category: string;
    required_capability: string;
    reward: number;
    status: string;
  };
}

export interface BidCreatePayload {
  task_id: number;
  agent_id: number;
  bid_amount: number;
  estimated_completion_minutes: number;
  proposal: string;
}

export interface BidUpdatePayload {
  bid_amount?: number;
  estimated_completion_minutes?: number;
  proposal?: string;
}

export interface RankedBidItem {
  id: number;
  bid_code?: string;
  task_id: number;
  agent_id: number;
  bid_amount: number;
  estimated_completion_minutes: number;
  proposal: string;
  match_score: number;
  price_score: number;
  speed_score: number;
  selection_score: number;
  status: 'pending' | 'accepted' | 'rejected' | 'withdrawn';
  created_at: string;
  updated_at: string;
  reasons: string[];
  agent: {
    id: number;
    agent_code?: string;
    name: string;
    agent_type: string;
    reputation_score: number;
    status: string;
  };
}

export interface TaskBidsListResponse {
  task_id: number;
  task_code?: string;
  task_status: string;
  reward: number;
  bids: RankedBidItem[];
  total_bids: number;
}

export interface AgentBidsListResponse {
  agent_id: number;
  agent_code?: string;
  bids: ApiBid[];
  total_bids: number;
}

export interface SelectBidResponse {
  message: string;
  task_id: number;
  task_code?: string;
  task_status: string;
  assigned_agent_id: number;
  assigned_agent_name: string;
  assigned_agent_code?: string;
  selected_bid_id: number;
  selected_bid_code?: string;
  selected_bid_amount: number;
  assigned_at: string;
}

// ---------------------------------------------------------------------------
// Bidding API Functions
// ---------------------------------------------------------------------------

export async function createBid(payload: BidCreatePayload): Promise<ApiBid> {
  const response = await fetch(`${API_BASE_URL}/api/bids`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    let msg = 'Failed to submit bid.';
    if (err?.detail) {
      msg = typeof err.detail === 'string' ? err.detail : err.detail.map((e: any) => e.msg).join(', ');
    }
    throw new Error(msg);
  }
  return await response.json();
}

export async function fetchTaskBids(taskId: number, status?: string): Promise<TaskBidsListResponse> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/bids${qs}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) throw new Error(`Failed to fetch bids for task: ${response.statusText}`);
  return await response.json();
}

export async function fetchAgentBids(agentId: number, status?: string): Promise<AgentBidsListResponse> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/bids${qs}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) throw new Error(`Failed to fetch agent bids: ${response.statusText}`);
  return await response.json();
}

export async function fetchBidById(bidId: number): Promise<ApiBid> {
  const response = await fetch(`${API_BASE_URL}/api/bids/${bidId}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) throw new Error(`Failed to fetch bid: ${response.statusText}`);
  return await response.json();
}

export async function updateBid(bidId: number, payload: BidUpdatePayload): Promise<ApiBid> {
  const response = await fetch(`${API_BASE_URL}/api/bids/${bidId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    let msg = 'Failed to update bid.';
    if (err?.detail) {
      msg = typeof err.detail === 'string' ? err.detail : err.detail.map((e: any) => e.msg).join(', ');
    }
    throw new Error(msg);
  }
  return await response.json();
}

export async function withdrawBid(bidId: number): Promise<ApiBid> {
  const response = await fetch(`${API_BASE_URL}/api/bids/${bidId}/withdraw`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to withdraw bid: ${response.statusText}`);
  }
  return await response.json();
}

export async function selectWinningBid(taskId: number, bidId: number): Promise<SelectBidResponse> {
  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/select-bid/${bidId}`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    let msg = 'Failed to select winning bid.';
    if (err?.detail) {
      msg = typeof err.detail === 'string' ? err.detail : err.detail.map((e: any) => e.msg).join(', ');
    }
    throw new Error(msg);
  }
  return await response.json();
}

// ============================================================
// PHASE 8 — Execution Engine Types & API Functions
// ============================================================

export interface ApiExecutionTaskSummary {
  id: number;
  task_code: string | null;
  title: string;
  description: string;
  category: string;
  required_capability: string;
  reward: number;
  status: string;
}

export interface ApiExecutionAgentSummary {
  id: number;
  agent_code: string | null;
  name: string;
  agent_type: string;
  reputation_score: number;
}

export interface ApiExecutionBidSummary {
  id: number;
  bid_code: string | null;
  bid_amount: number;
  estimated_completion_minutes: number;
  proposal: string;
  selection_score: number;
}

export interface ApiExecution {
  id: number;
  execution_code: string | null;
  task_id: number;
  agent_id: number;
  bid_id: number;
  status: string; // pending | running | completed | submitted | failed | cancelled
  progress: number;
  attempt_number: number;
  output_text: string | null;
  structured_output: string | null; // JSON string
  execution_metadata: string | null; // JSON string
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
  task?: ApiExecutionTaskSummary | null;
  agent?: ApiExecutionAgentSummary | null;
  bid?: ApiExecutionBidSummary | null;
}

export interface ApiExecutionLog {
  id: number;
  execution_id: number;
  level: string;
  step: string | null;
  message: string;
  created_at: string;
}

export interface ApiExecutionLogsResponse {
  execution_id: number;
  execution_code: string | null;
  logs: ApiExecutionLog[];
  total_logs: number;
}

export interface ApiExecutionStartResponse {
  id: number;
  execution_code: string | null;
  task_id: number;
  agent_id: number;
  bid_id: number;
  status: string;
  progress: number;
  started_at: string | null;
  created_at: string;
  message: string;
}

export interface ApiExecutionSubmitResponse {
  message: string;
  execution_id: number;
  execution_code: string | null;
  execution_status: string;
  task_id: number;
  task_code: string | null;
  task_status: string;
  submitted_at: string;
  submission_id?: number;
  submission_code?: string;
}

export interface ApiAgentAssignedTask {
  task_id: number;
  task_code: string | null;
  title: string;
  category: string;
  required_capability: string;
  reward: number;
  deadline: string;
  task_status: string;
  bid_id: number | null;
  bid_code: string | null;
  bid_amount: number | null;
  execution_id: number | null;
  execution_code: string | null;
  execution_status: string | null;
  execution_progress: number | null;
  assigned_at: string | null;
}

export interface ApiAgentAssignedTasksResponse {
  agent_id: number;
  agent_code: string | null;
  tasks: ApiAgentAssignedTask[];
  total: number;
}

/** POST /api/tasks/{taskId}/execution/start — create execution for an assigned task */
export async function startExecution(taskId: number): Promise<ApiExecutionStartResponse> {
  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/execution/start`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to start execution: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/tasks/{taskId}/execution — get current execution for a task */
export async function fetchTaskExecution(taskId: number): Promise<ApiExecution | null> {
  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/execution`, {
    headers: { 'Accept': 'application/json' },
  });
  if (response.status === 404) return null;
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch task execution: ${response.statusText}`);
  }
  return await response.json();
}

/** POST /api/executions/{id}/run — run the executor synchronously */
export async function runExecution(executionId: number): Promise<ApiExecution> {
  const response = await fetch(`${API_BASE_URL}/api/executions/${executionId}/run`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to run execution: ${response.statusText}`);
  }
  return await response.json();
}

/** POST /api/executions/{id}/submit — submit completed execution for verification */
export async function submitExecution(executionId: number): Promise<ApiExecutionSubmitResponse> {
  const response = await fetch(`${API_BASE_URL}/api/executions/${executionId}/submit`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to submit execution: ${response.statusText}`);
  }
  return await response.json();
}

/** POST /api/executions/{id}/retry — retry a failed execution */
export async function retryExecution(executionId: number): Promise<ApiExecution> {
  const response = await fetch(`${API_BASE_URL}/api/executions/${executionId}/retry`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to retry execution: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/executions/{id} — get full execution detail */
export async function fetchExecution(executionId: number): Promise<ApiExecution> {
  const response = await fetch(`${API_BASE_URL}/api/executions/${executionId}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch execution: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/executions/{id}/logs — get ordered execution logs */
export async function fetchExecutionLogs(executionId: number): Promise<ApiExecutionLogsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/executions/${executionId}/logs`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch execution logs: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/agents/{agentId}/assigned-tasks — get agent's active work list */
export async function fetchAgentAssignedTasks(agentId: number): Promise<ApiAgentAssignedTasksResponse> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/assigned-tasks`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch assigned tasks: ${response.statusText}`);
  }
  return await response.json();
}

// ---------------------------------------------------------------------------
// Phase 9 — Result Submission & Audit Types & API
// ---------------------------------------------------------------------------

export interface ApiSubmissionAuditLog {
  id: number;
  submission_id: number;
  action: string;
  actor_type: string;
  actor_id: string | null;
  message: string | null;
  created_at: string;
}

export interface ApiResultSubmission {
  id: number;
  submission_code: string | null;
  version: number;
  status: string;
  is_locked: boolean;
  verification_ready: boolean;
  task_id: number;
  execution_id: number;
  agent_id: number;
  bid_id: number;
  result_summary: string | null;
  confidence_score: number | null;
  integrity_hash: string | null;
  submitted_at: string | null;
  created_at: string;
}

export interface ApiResultSubmissionDetail {
  id: number;
  submission_code: string | null;
  version: number;
  status: string;
  is_locked: boolean;
  verification_ready: boolean;
  task_id: number;
  execution_id: number;
  agent_id: number;
  bid_id: number;
  output_text: string | null;
  structured_output: any;
  result_summary: string | null;
  content_type: string | null;
  confidence_score: number | null;
  evidence: any;
  provenance: any;
  task_snapshot: any;
  agent_snapshot: any;
  bid_snapshot: any;
  execution_snapshot: any;
  submission_metadata: any;
  self_assessment: any;
  limitations: string[] | null;
  integrity_hash: string | null;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiSubmissionIntegrityResponse {
  submission_code: string | null;
  submission_id: number;
  valid: boolean;
  algorithm: string;
  stored_hash: string | null;
  verification_ready: boolean;
  reason?: string | null;
}

export interface ApiPendingVerificationItem {
  id: number;
  submission_code: string | null;
  task_id: number;
  agent_id: number;
  status: string;
  result_summary?: string | null;
  verification_ready: boolean;
  integrity_hash: string | null;
  submitted_at: string | null;
}


/** GET /api/submissions/{id} — get full submission detail */
export async function fetchSubmission(submissionId: number): Promise<ApiResultSubmissionDetail> {
  const response = await fetch(`${API_BASE_URL}/api/submissions/${submissionId}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch submission: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/submissions/code/{code} — lookup submission by RS-code */
export async function fetchSubmissionByCode(submissionCode: string): Promise<ApiResultSubmissionDetail> {
  const response = await fetch(`${API_BASE_URL}/api/submissions/code/${encodeURIComponent(submissionCode)}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch submission by code: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/tasks/{taskId}/submission — get current submission for a task */
export async function fetchTaskSubmission(taskId: number): Promise<ApiResultSubmissionDetail | null> {
  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/submission`, {
    headers: { 'Accept': 'application/json' },
  });
  if (response.status === 404) return null;
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch task submission: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/agents/{agentId}/submissions — get agent's submissions */
export async function fetchAgentSubmissions(agentId: number): Promise<ApiResultSubmission[]> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/submissions`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch agent submissions: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/submissions/{id}/integrity — check SHA-256 fingerprint */
export async function fetchSubmissionIntegrity(submissionId: number): Promise<ApiSubmissionIntegrityResponse> {
  const response = await fetch(`${API_BASE_URL}/api/submissions/${submissionId}/integrity`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to verify submission integrity: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/submissions/{id}/audit — get ordered audit log entries */
export async function fetchSubmissionAudit(submissionId: number): Promise<ApiSubmissionAuditLog[]> {
  const response = await fetch(`${API_BASE_URL}/api/submissions/${submissionId}/audit`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch submission audit log: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/submissions/pending-verification — get pending submissions list */
export async function fetchPendingVerifications(): Promise<ApiPendingVerificationItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/submissions/pending-verification`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch pending verifications: ${response.statusText}`);
  }
  return await response.json();
}

// ---------------------------------------------------------------------------
// Phase 10: Independent Verification Engine Types & API
// ---------------------------------------------------------------------------

export interface ApiVerificationAuditLog {
  id: number;
  verification_id: number;
  action: string;
  actor_type: string;
  actor_id?: string | null;
  message?: string | null;
  created_at: string;
}

export interface ApiVerificationStartResponse {
  message: string;
  verification_id: number;
  verification_code?: string | null;
  status: string;
  submission_id: number;
  task_id: number;
  worker_agent_id: number;
  verifier_agent_id: number;
  verifier_name?: string | null;
  verifier_code?: string | null;
  started_at?: string | null;
}

export interface ApiVerificationSummary {
  id: number;
  verification_code?: string | null;
  submission_id: number;
  task_id: number;
  worker_agent_id: number;
  verifier_agent_id: number;
  status: string;
  decision?: 'PASS' | 'FAIL' | 'REVIEW' | null;
  integrity_valid: boolean;
  accuracy_score: number;
  completeness_score: number;
  format_compliance_score: number;
  quality_score: number;
  evidence_score: number;
  overall_score: number;
  required_score: number;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
}

export interface ApiVerificationDetail extends ApiVerificationSummary {
  reasons?: Record<string, string[]> | null;
  warnings?: string[] | null;
  verification_details?: Record<string, any> | null;
  verifier_snapshot?: {
    verifier_id: number;
    verifier_code: string;
    name: string;
    agent_type: string;
    capabilities: string[];
    reputation_score: number;
    status_at_verification: string;
  } | null;
  submission_hash_snapshot?: string | null;
  updated_at: string;
}

/** POST /api/submissions/{id}/verification/start — start verification pipeline */
export async function startVerification(submissionId: number): Promise<ApiVerificationStartResponse> {
  const response = await fetch(`${API_BASE_URL}/api/submissions/${submissionId}/verification/start`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail?.error || err?.detail || `Failed to start verification: ${response.statusText}`);
  }
  return await response.json();
}

/** POST /api/verifications/{id}/run — execute evaluation */
export async function runVerification(verificationId: number): Promise<ApiVerificationDetail> {
  const response = await fetch(`${API_BASE_URL}/api/verifications/${verificationId}/run`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to execute verification: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/verifications/{id} — get verification detail */
export async function fetchVerification(verificationId: number): Promise<ApiVerificationDetail> {
  const response = await fetch(`${API_BASE_URL}/api/verifications/${verificationId}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch verification: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/verifications/{id}/audit — get verification audit trail */
export async function fetchVerificationAudit(verificationId: number): Promise<ApiVerificationAuditLog[]> {
  const response = await fetch(`${API_BASE_URL}/api/verifications/${verificationId}/audit`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch verification audit: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/tasks/{taskId}/verification — get latest verification for task */
export async function fetchTaskVerification(taskId: number): Promise<ApiVerificationDetail | null> {
  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/verification`, {
    headers: { 'Accept': 'application/json' },
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch task verification: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/submissions/{subId}/verification — get verification for submission */
export async function fetchSubmissionVerification(submissionId: number): Promise<ApiVerificationDetail | null> {
  const response = await fetch(`${API_BASE_URL}/api/submissions/${submissionId}/verification`, {
    headers: { 'Accept': 'application/json' },
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch submission verification: ${response.statusText}`);
  }
  return await response.json();
}

/** GET /api/verifications — list historical verifications */
export async function fetchVerifications(limit = 50, offset = 0): Promise<ApiVerificationSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/verifications?limit=${limit}&offset=${offset}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || `Failed to fetch verifications: ${response.statusText}`);
  }
  return await response.json();
}





