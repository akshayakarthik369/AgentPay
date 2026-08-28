import React from 'react';
import { ClientDashboard } from '../components/ClientDashboard';
import { NavTab } from '../components/Navbar';

interface ClientDashboardPageProps {
  onNavigate: (tab: NavTab) => void;
  onSelectTask?: (taskId: string) => void;
  onSelectSettlement?: (settlementId: number) => void;
}

export const ClientDashboardPage: React.FC<ClientDashboardPageProps> = ({
  onNavigate,
  onSelectTask,
  onSelectSettlement,
}) => {
  return (
    <ClientDashboard
      onNavigate={onNavigate}
      onSelectTask={onSelectTask}
      onSelectSettlement={onSelectSettlement}
    />
  );
};
