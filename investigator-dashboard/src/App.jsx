import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

import Login from './components/Login';
import DashboardOverview from './pages/DashboardOverview';
import AlertDetail from './pages/AlertDetail';
import FramlGraph from './pages/FramlGraph';
import TransactionRiskScoring from './pages/TransactionRiskScoring';
import KafkaWorkflow from './pages/KafkaWorkflow';
import Transactions from './pages/Transactions';
import Alerts from './pages/Alerts';
import BiometricMonitor from './pages/BiometricMonitor';
import Investigation from './pages/Investigation';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

import './App.css';

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/dashboard" element={
            <ProtectedRoute><DashboardOverview /></ProtectedRoute>
          } />
          <Route path="/alerts/:id" element={
            <ProtectedRoute><AlertDetail /></ProtectedRoute>
          } />
          <Route path="/graph" element={
            <ProtectedRoute><FramlGraph /></ProtectedRoute>
          } />
          <Route path="/transactions/:id/score" element={
            <ProtectedRoute><TransactionRiskScoring /></ProtectedRoute>
          } />
          <Route path="/kafka" element={
            <ProtectedRoute><KafkaWorkflow /></ProtectedRoute>
          } />
          
          <Route path="/transactions" element={<ProtectedRoute><Transactions /></ProtectedRoute>} />
          <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
          <Route path="/biometric" element={<ProtectedRoute><BiometricMonitor /></ProtectedRoute>} />
          <Route path="/investigation" element={<ProtectedRoute><Investigation /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
