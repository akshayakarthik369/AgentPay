import { useState, useEffect, useCallback } from 'react';
import { Navbar, NavTab } from './components/Navbar';
import { Home } from './pages/Home';
import { ClientDashboardPage } from './pages/ClientDashboardPage';
import { CreateTaskPage } from './pages/CreateTaskPage';
import { MarketplacePage } from './pages/MarketplacePage';
import { TaskDetailsPage } from './pages/TaskDetailsPage';
import { AgentsPage } from './pages/AgentsPage';
import { CreateAgentPage } from './pages/CreateAgentPage';
import { AgentDetailsPage } from './pages/AgentDetailsPage';
import { AgentDashboardPage } from './pages/AgentDashboardPage';
import { ExecutionPage } from './pages/ExecutionPage';
import { SubmissionDetailsPage } from './pages/SubmissionDetailsPage';
import { VerificationPage } from './pages/VerificationPage';
import { VerificationDetailsPage } from './pages/VerificationDetailsPage';
import { WalletPage } from './pages/WalletPage';
import { ReputationPage } from './pages/ReputationPage';
import { DisputesPage } from './pages/DisputesPage';
import { Footer } from './components/Footer';
import { checkBackendHealth } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<NavTab>('home');
  const [selectedTaskId, setSelectedTaskId] = useState<string>('AP-1024');
  const [selectedAgentId, setSelectedAgentId] = useState<number>(0);
  const [selectedExecutionId, setSelectedExecutionId] = useState<number | null>(null);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<number | null>(null);
  const [selectedVerificationId, setSelectedVerificationId] = useState<number | null>(null);
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  const fetchHealth = useCallback(async () => {
    setBackendStatus('checking');
    try {
      const data = await checkBackendHealth();
      if (data.status === 'ok') {
        setBackendStatus('connected');
      } else {
        setBackendStatus('disconnected');
      }
    } catch {
      setBackendStatus('disconnected');
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  const handleSelectTask = (id: string) => {
    setSelectedTaskId(id);
    setActiveTab('task-details');
  };

  const handleSelectAgent = (id: number) => {
    setSelectedAgentId(id);
    setActiveTab('agent-details');
  };

  const handleSelectExecution = (id: number) => {
    setSelectedExecutionId(id);
    setActiveTab('execution');
  };

  const handleSelectSubmission = (id: number) => {
    setSelectedSubmissionId(id);
    setActiveTab('submission-details');
  };

  const handleSelectVerification = (id: number) => {
    setSelectedVerificationId(id);
    setActiveTab('verification-details');
  };

  const renderMainContent = () => {
    switch (activeTab) {
      case 'home':
        return <Home onNavigate={setActiveTab} backendStatus={backendStatus} />;
      case 'client-dashboard':
        return <ClientDashboardPage onNavigate={setActiveTab} />;
      case 'create-task':
        return <CreateTaskPage onNavigate={setActiveTab} />;
      case 'tasks':
        return <MarketplacePage onNavigate={setActiveTab} onSelectTask={handleSelectTask} />;
      case 'task-details':
        return (
          <TaskDetailsPage 
            taskId={selectedTaskId} 
            onNavigate={setActiveTab} 
            onSelectExecution={handleSelectExecution}
            onSelectSubmission={handleSelectSubmission}
            onSelectVerification={handleSelectVerification}
          />
        );
      case 'agents':
        return <AgentsPage onNavigate={setActiveTab} onSelectAgent={handleSelectAgent} />;
      case 'create-agent':
        return <CreateAgentPage onNavigate={setActiveTab} />;
      case 'agent-details':
        return <AgentDetailsPage agentId={selectedAgentId} onNavigate={setActiveTab} />;
      case 'agent-dashboard':
        return (
          <AgentDashboardPage 
            onNavigate={setActiveTab} 
            onSelectTask={handleSelectTask} 
            onSelectExecution={handleSelectExecution}
            onSelectSubmission={handleSelectSubmission}
          />
        );
      case 'execution':
        return (
          <ExecutionPage 
            onNavigate={setActiveTab} 
            executionId={selectedExecutionId}
            onSelectSubmission={handleSelectSubmission}
          />
        );
      case 'submission-details':
        return (
          <SubmissionDetailsPage 
            onNavigate={setActiveTab} 
            submissionId={selectedSubmissionId}
            onSelectTask={(tid) => handleSelectTask(String(tid))}
            onSelectAgent={handleSelectAgent}
            onSelectVerification={handleSelectVerification}
          />
        );
      case 'verification':
        return (
          <VerificationPage 
            onNavigate={setActiveTab}
            onSelectSubmission={handleSelectSubmission}
            onSelectVerification={handleSelectVerification}
          />
        );
      case 'verification-details':
        return (
          <VerificationDetailsPage
            verificationId={selectedVerificationId || 1}
            onBack={() => setActiveTab('verification')}
            onNavigateToSubmission={handleSelectSubmission}
            onNavigateToTask={(tid) => handleSelectTask(String(tid))}
          />
        );
      case 'wallet':
        return <WalletPage onNavigate={setActiveTab} />;
      case 'reputation':
        return <ReputationPage onNavigate={setActiveTab} />;
      case 'disputes':
        return <DisputesPage onNavigate={setActiveTab} />;
      default:
        return <Home onNavigate={setActiveTab} backendStatus={backendStatus} />;
    }
  };



  return (
    <div className="min-h-screen flex flex-col justify-between bg-[#F7F8FA] text-[#18202F] selection:bg-blue-500/20 selection:text-blue-950">
      <div>
        <Navbar 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          backendStatus={backendStatus}
          onRefreshHealth={fetchHealth}
        />

        <main className="transition-all duration-300">
          {renderMainContent()}
        </main>
      </div>

      <Footer onNavigate={setActiveTab} />
    </div>
  );
}

export default App;
