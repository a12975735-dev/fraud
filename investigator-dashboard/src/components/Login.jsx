import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = 'http://127.0.0.1:8081';

/** 3 mock transactions pre-seeded when user signs in via Quick Demo mode */
export const DEMO_SEED_TRANSACTIONS = [
  {
    transactionId: 'DEMO-f3a91bc2-0001',
    amount: 450000.0,
    step: 14,
    timestamp: new Date(Date.now() - 65000).toISOString(),
    status: 'COMPLETED',
    riskScore: 94,
    riskLevel: 'high',
    topReasonCodes: [
      { feature: 'amount_deviation', impact: 0.621 },
      { feature: 'transaction_velocity', impact: 0.418 },
      { feature: 'balance_discrepancy', impact: 0.301 },
      { feature: 'oldbalanceDest', impact: -0.082 },
    ],
    inputData: { amount: 450000, step: 14, type: 'TRANSFER', transaction_velocity: 18.5, amount_deviation: 95.0, balance_discrepancy: 450000 },
  },
  {
    transactionId: 'DEMO-a77d2fe1-0002',
    amount: 8750.0,
    step: 3,
    timestamp: new Date(Date.now() - 32000).toISOString(),
    status: 'COMPLETED',
    riskScore: 48,
    riskLevel: 'medium',
    topReasonCodes: [
      { feature: 'transaction_velocity', impact: 0.215 },
      { feature: 'amount_deviation', impact: 0.174 },
      { feature: 'balance_discrepancy', impact: -0.091 },
      { feature: 'oldbalanceDest', impact: -0.043 },
    ],
    inputData: { amount: 8750, step: 3, type: 'CASH_OUT', transaction_velocity: 4.2, amount_deviation: 22.0, balance_discrepancy: 8750 },
  },
  {
    transactionId: 'DEMO-c1200d44-0003',
    amount: 45.5,
    step: 1,
    timestamp: new Date(Date.now() - 8000).toISOString(),
    status: 'COMPLETED',
    riskScore: 6,
    riskLevel: 'low',
    topReasonCodes: [
      { feature: 'balance_discrepancy', impact: -0.19 },
      { feature: 'oldbalanceDest', impact: -0.14 },
      { feature: 'transaction_velocity', impact: 0.031 },
      { feature: 'amount_deviation', impact: 0.012 },
    ],
    inputData: { amount: 45.5, step: 1, type: 'PAYMENT', transaction_velocity: 0.5, amount_deviation: 0.1, balance_discrepancy: 0 },
  },
];

export default function Login() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('demo-admin');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok && data.token) {
        login(data.token, username, data.role || 'INVESTIGATOR', false);
        navigate('/dashboard');
      } else {
        setError(data.error || `Authentication failed (HTTP ${response.status})`);
      }
    } catch (err) {
      console.warn('Spring Gateway unreachable:', err.message);
      setError(
        'Cannot reach Spring Boot Gateway at http://127.0.0.1:8081. ' +
          'Start the gateway, or use ⚡ Quick Demo Sign-In below for offline preview.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = () => {
    // demoMode=true → all components activate synthetic fallbacks
    login('demo-jwt-token-investigator-dashboard', 'demo_investigator', 'CHIEF_INVESTIGATOR', true);
    navigate('/dashboard');
  };

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Header */}
        <div className="login-header">
          <div className="shield-icon">
            <svg viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <polyline points="9 12 11 14 15 10" />
            </svg>
          </div>
          <h2>FRAUD SHIELD AI</h2>
          <p className="subtitle">Next-Gen Smart Banking · Real-Time Risk Analytics</p>
          <div className="login-pillars">
            <span>🔐 Behavioral Biometrics</span>
            <span>⚡ Real-Time Kafka</span>
            <span>🤖 XAI / SHAP</span>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="error-banner">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Live Login Form */}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
              disabled={loading}
            />
          </div>
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? (
              <span className="spinner-label">
                <span className="btn-spinner"></span> Authenticating via Gateway...
              </span>
            ) : (
              'Sign In via Spring Gateway'
            )}
          </button>
        </form>

        {/* Divider */}
        <div className="demo-login-divider">
          <span>OR</span>
        </div>

        {/* Demo Login */}
        <button type="button" id="demo-login-btn" className="demo-btn" onClick={handleDemoLogin}>
          ⚡ Quick Demo Sign-In
          <span className="demo-btn-sub">No backend required · Pre-seeded alerts + synthetic SHAP</span>
        </button>

        {/* Credentials hint */}
        <div className="credentials-hint">
          <p>Live Gateway credentials:</p>
          <code>
            Username: <strong>admin</strong> | Password: <strong>demo-admin</strong>
          </code>
        </div>
      </div>
    </div>
  );
}
