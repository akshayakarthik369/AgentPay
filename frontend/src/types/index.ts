export type TaskStatus = 
  | 'Open' 
  | 'Pending'
  | 'Bidding' 
  | 'Assigned' 
  | 'Executing' 
  | 'Submitted' 
  | 'Verifying' 
  | 'Verified' 
  | 'Payment Released' 
  | 'Failed' 
  | 'Disputed'
  | 'Review Required';


export interface Task {
  id: string;
  title: string;
  category: 'NLP' | 'Research' | 'Data Analysis' | 'Content' | 'Model Evaluation' | 'Security';
  description: string;
  capability: string;
  reward: number; // AP Credits
  deadline: string;
  minReputation: number;
  minQualityScore: number;
  agentsBiddingCount: number;
  status: TaskStatus;
  client: string;
  assignedAgent?: string;
  createdDate: string;
}

export interface AgentBid {
  id: string;
  agentId: string;
  agentName: string;
  capabilityMatch: number; // percentage (e.g., 96)
  reputation: number; // 0-100
  bidAmount: number; // AP Credits
  successRate: number; // percentage (e.g., 97)
  isSelected?: boolean;
}

export interface AgentProfile {
  id: string;
  name: string;
  role: string;
  reputation: number;
  walletBalance: number;
  completedTasks: number;
  successRate: number;
  avgVerificationScore: number;
  activeTaskId?: string;
  capabilities: string[];
}

export interface ExecutionStep {
  title: string;
  description: string;
  status: 'completed' | 'in_progress' | 'pending';
  timestamp?: string;
}

export interface VerificationMetrics {
  accuracy: number;
  completeness: number;
  formatCompliance: number;
  qualityScore: number;
  requiredQuality: number;
  passed: boolean;
  verifierAgent: string;
  workerAgent: string;
  failureReason?: string;
}

export interface Transaction {
  id: string;
  taskId: string;
  taskTitle: string;
  amount: number;
  status: 'Released' | 'Locked in Escrow' | 'Refunded';
  from: string;
  to: string;
  condition: string;
  date: string;
}

export interface ReputationEvent {
  id: string;
  taskId: string;
  taskTitle: string;
  change: number; // e.g. +2 or -5
  reason: string;
  date: string;
}

export interface DisputeCase {
  id: string;
  taskId: string;
  taskTitle: string;
  workerAgent: string;
  verifierAgent: string;
  arbitratorAgent: string;
  reason: string;
  status: 'Under Review' | 'Resolved - Payment Released' | 'Resolved - Refunded';
  workerClaim: string;
  verifierDecision: string;
  submittedEvidence: string;
  verificationScore: number;
  finalDecision?: string;
  date: string;
}
