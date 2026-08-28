import React from 'react';
import { ClientDashboard } from '../components/ClientDashboard';
import { NavTab } from '../components/Navbar';

interface ClientDashboardPageProps {
  onNavigate: (tab: NavTab) => void;
}

export const ClientDashboardPage: React.FC<ClientDashboardPageProps> = ({ onNavigate }) => {
  return <ClientDashboard onNavigate={onNavigate} />;
};
