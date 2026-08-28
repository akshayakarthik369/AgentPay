import { 
  Task, 
  AgentBid, 
  AgentProfile, 
  ExecutionStep, 
  VerificationMetrics, 
  Transaction, 
  ReputationEvent, 
  DisputeCase 
} from '../types';

export const mockTasks: Task[] = [
  {
    id: 'AP-1024',
    title: 'Customer Review Sentiment Analysis',
    category: 'NLP',
    description: 'Analyze 500 customer reviews and classify them into positive, neutral, and negative sentiment with confidence metrics.',
    capability: 'NLP / Sentiment Classification',
    reward: 100,
    deadline: '2026-08-30',
    minReputation: 80,
    minQualityScore: 85,
    agentsBiddingCount: 4,
    status: 'Open',
    client: 'Requester-Agent-01',
    createdDate: '2026-08-28'
  },
  {
    id: 'AP-1025',
    title: 'Summarize Research Document',
    category: 'Research',
    description: 'Extract key methodological insights, experimental results, and conclusion summaries from a 45-page arXiv preprint.',
    capability: 'Research / Text Summarization',
    reward: 80,
    deadline: '2026-08-29',
    minReputation: 75,
    minQualityScore: 80,
    agentsBiddingCount: 3,
    status: 'Executing',
    client: 'Requester-Agent-02',
    assignedAgent: 'Research-Agent-02',
    createdDate: '2026-08-28'
  },
  {
    id: 'AP-1026',
    title: 'Product Description Generation',
    category: 'Content',
    description: 'Generate 50 SEO-optimized e-commerce product descriptions tailored for consumer electronics.',
    capability: 'Content Generation',
    reward: 50,
    deadline: '2026-08-31',
    minReputation: 60,
    minQualityScore: 75,
    agentsBiddingCount: 2,
    status: 'Pending',
    client: 'Requester-Agent-03',
    createdDate: '2026-08-28'
  },
  {
    id: 'AP-1027',
    title: 'Code Vulnerability Audit',
    category: 'Security',
    description: 'Audit a Python FastAPI microservice repository for OWASP Top 10 vulnerabilities and dependency CVEs.',
    capability: 'Security / Static Analysis',
    reward: 250,
    deadline: '2026-08-27',
    minReputation: 90,
    minQualityScore: 90,
    agentsBiddingCount: 5,
    status: 'Failed',
    client: 'SecOps-Client-01',
    assignedAgent: 'Audit-Bot-X',
    createdDate: '2026-08-26'
  },
  {
    id: 'AP-1028',
    title: 'Financial Time-Series Anomaly Detection',
    category: 'Data Analysis',
    description: 'Detect volatility anomalies in 1-minute crypto orderbook trade streams and output alert triggers.',
    capability: 'Data Analysis / Time-Series ML',
    reward: 180,
    deadline: '2026-09-01',
    minReputation: 85,
    minQualityScore: 88,
    agentsBiddingCount: 6,
    status: 'Bidding',
    client: 'FinTech-Client-04',
    createdDate: '2026-08-28'
  },
  {
    id: 'AP-1029',
    title: 'LLM Response Quality Evaluation',
    category: 'Model Evaluation',
    description: 'Benchmark outputs from 3 LLM models across 100 reasoning prompts using G-Eval automated metrics.',
    capability: 'Model Evaluation / Benchmarking',
    reward: 120,
    deadline: '2026-08-29',
    minReputation: 80,
    minQualityScore: 85,
    agentsBiddingCount: 3,
    status: 'Verified',
    client: 'AI-Research-Lab',
    assignedAgent: 'Eval-Agent-09',
    createdDate: '2026-08-27'
  }
];

export const mockBids: AgentBid[] = [
  {
    id: 'BID-01',
    agentId: 'NLP-Agent-01',
    agentName: 'NLP-Agent-01',
    capabilityMatch: 96,
    reputation: 94,
    bidAmount: 85,
    successRate: 97,
    isSelected: true
  },
  {
    id: 'BID-02',
    agentId: 'NLP-Agent-02',
    agentName: 'NLP-Agent-02',
    capabilityMatch: 90,
    reputation: 88,
    bidAmount: 75,
    successRate: 91,
    isSelected: false
  },
  {
    id: 'BID-03',
    agentId: 'Linguist-Bot',
    agentName: 'Linguist-Bot-v2',
    capabilityMatch: 84,
    reputation: 82,
    bidAmount: 90,
    successRate: 89,
    isSelected: false
  },
  {
    id: 'BID-04',
    agentId: 'FastText-Agent',
    agentName: 'FastText-Agent-X',
    capabilityMatch: 78,
    reputation: 79,
    bidAmount: 65,
    successRate: 85,
    isSelected: false
  }
];

export const mockWorkerAgent: AgentProfile = {
  id: 'NLP-Agent-01',
  name: 'NLP-Agent-01',
  role: 'Specialized Sentiment & Text Processing Autonomous Agent',
  reputation: 94,
  walletBalance: 1250,
  completedTasks: 27,
  successRate: 96,
  avgVerificationScore: 93,
  activeTaskId: 'AP-1024',
  capabilities: ['NLP / Sentiment Classification', 'Text Summarization', 'Entity Extraction', 'Content Analysis']
};

export const mockExecutionSteps: ExecutionStep[] = [
  {
    title: 'Task Accepted & Escrow Locked',
    description: 'Accepted task AP-1024; 100 AP Credits locked in smart escrow contract.',
    status: 'completed',
    timestamp: '14:30:02'
  },
  {
    title: 'Input Received & Validated',
    description: 'Ingested 500 customer review dataset payload; Schema validation passed.',
    status: 'completed',
    timestamp: '14:30:15'
  },
  {
    title: 'Processing & Model Execution',
    description: 'Running transformer sentiment classification model across 500 batch items.',
    status: 'in_progress',
    timestamp: '14:31:00'
  },
  {
    title: 'Result Generated & Verified Locally',
    description: 'Structured JSON output compiled with 62% Positive, 18% Neutral, 20% Negative distribution.',
    status: 'pending'
  },
  {
    title: 'Result Submitted for AI Verification',
    description: 'Payload submitted to Verify-Agent-03 for automated quality audit.',
    status: 'pending'
  }
];

export const mockVerificationPassed: VerificationMetrics = {
  accuracy: 94,
  completeness: 96,
  formatCompliance: 100,
  qualityScore: 93,
  requiredQuality: 85,
  passed: true,
  verifierAgent: 'Verify-Agent-03',
  workerAgent: 'NLP-Agent-01'
};

export const mockVerificationFailed: VerificationMetrics = {
  accuracy: 68,
  completeness: 72,
  formatCompliance: 90,
  qualityScore: 74,
  requiredQuality: 85,
  passed: false,
  verifierAgent: 'Verify-Agent-04',
  workerAgent: 'Audit-Bot-X',
  failureReason: 'High false-negative rate on critical SQL injection test vectors. Completeness score failed 85% threshold requirement.'
};

export const mockTransactions: Transaction[] = [
  {
    id: 'TXN-901',
    taskId: 'AP-1024',
    taskTitle: 'Customer Review Sentiment Analysis',
    amount: 100,
    status: 'Released',
    from: 'Requester-Agent-01',
    to: 'NLP-Agent-01',
    condition: 'Verification Passed (Quality 93% >= 85%)',
    date: '2026-08-28 14:32'
  },
  {
    id: 'TXN-902',
    taskId: 'AP-1025',
    taskTitle: 'Summarize Research Document',
    amount: 80,
    status: 'Locked in Escrow',
    from: 'Requester-Agent-02',
    to: 'Escrow-Contract-02',
    condition: 'Awaiting Result Submission & Verification',
    date: '2026-08-28 12:10'
  },
  {
    id: 'TXN-903',
    taskId: 'AP-1029',
    taskTitle: 'LLM Response Quality Evaluation',
    amount: 120,
    status: 'Released',
    from: 'AI-Research-Lab',
    to: 'Eval-Agent-09',
    condition: 'Verification Passed (Quality 96% >= 85%)',
    date: '2026-08-27 18:45'
  },
  {
    id: 'TXN-904',
    taskId: 'AP-1027',
    taskTitle: 'Code Vulnerability Audit',
    amount: 250,
    status: 'Refunded',
    from: 'Escrow-Contract-04',
    to: 'SecOps-Client-01',
    condition: 'Verification Failed (Quality 74% < 90%)',
    date: '2026-08-26 21:00'
  }
];

export const mockReputationEvents: ReputationEvent[] = [
  {
    id: 'REP-01',
    taskId: 'AP-1024',
    taskTitle: 'Customer Review Sentiment Analysis',
    change: 2,
    reason: 'Task verified successfully with 93% Quality Score',
    date: '2026-08-28'
  },
  {
    id: 'REP-02',
    taskId: 'AP-1019',
    taskTitle: 'Automated Translation Verification',
    change: 1,
    reason: 'On-time delivery with 98% Format Compliance',
    date: '2026-08-25'
  },
  {
    id: 'REP-03',
    taskId: 'AP-1008',
    taskTitle: 'E-commerce Category Tagging',
    change: 2,
    reason: 'Perfect 100% Accuracy score verified',
    date: '2026-08-20'
  },
  {
    id: 'REP-04',
    taskId: 'AP-0982',
    taskTitle: 'Experimental Named Entity Recognition',
    change: -5,
    reason: 'Verification failed; precision threshold unmet',
    date: '2026-08-12'
  }
];

export const mockDisputes: DisputeCase[] = [
  {
    id: 'DSP-001',
    taskId: 'AP-1027',
    taskTitle: 'Code Vulnerability Audit',
    workerAgent: 'Audit-Bot-X',
    verifierAgent: 'Verify-Agent-04',
    arbitratorAgent: 'Judge-Agent-01',
    reason: 'Worker claims verifier benchmark test vectors contained outdated CVE signatures resulting in false failure.',
    status: 'Resolved - Payment Released',
    workerClaim: 'Audit-Bot-X submitted verified AST parse tree showing 100% static rule coverage. Verifier checked against deprecated 2024 test suite.',
    verifierDecision: 'Verify-Agent-04 flagged 74% quality score based on default test harness.',
    submittedEvidence: 'AST_Coverage_Report.json + Security_Ruleset_v3.2.pdf',
    verificationScore: 74,
    finalDecision: 'Arbitrator Judge-Agent-01 reviewed evidence. Worker claim accepted due to outdated test harness. 250 AP Released to Audit-Bot-X.',
    date: '2026-08-27'
  },
  {
    id: 'DSP-002',
    taskId: 'AP-1011',
    taskTitle: 'Financial Report Data Extraction',
    workerAgent: 'Data-Extractor-05',
    verifierAgent: 'Verify-Agent-02',
    arbitratorAgent: 'Judge-Agent-02',
    reason: 'Worker disputes 82% completeness score, claiming PDF tables were corrupted by client upload.',
    status: 'Under Review',
    workerClaim: 'Source PDF page 14 contained unparseable binary stream. Extracted all valid textual tables correctly.',
    verifierDecision: 'Completeness check flagged 3 missing financial statements.',
    submittedEvidence: 'PDF_Parse_Log.txt + Raw_Extraction_Output.csv',
    verificationScore: 82,
    date: '2026-08-28'
  }
];
