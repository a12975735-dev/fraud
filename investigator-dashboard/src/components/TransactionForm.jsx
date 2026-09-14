import React, { useState } from 'react';

const API_BASE_URL = 'http://127.0.0.1:8000';

export default function TransactionForm({ onTransactionSubmitted, biometricRiskScore }) {
  const [formData, setFormData] = useState({
    amount: 15420.50,
    step: 1,
    oldbalanceDest: 0.0,
    newbalanceDest: 0.0,
    transaction_velocity: 4.8,
    amount_deviation: 15.2,
    balance_discrepancy: 15420.50,
    type: 'TRANSFER',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastSubmittedId, setLastSubmittedId] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : parseFloat(value)) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const payload = {
      amount: Number(formData.amount),
      step: Number(formData.step),
      oldbalanceDest: Number(formData.oldbalanceDest || 0),
      newbalanceDest: Number(formData.newbalanceDest || 0),
      transaction_velocity: Number(formData.transaction_velocity || 0),
      amount_deviation: Number(formData.amount_deviation || 0),
      balance_discrepancy: Number(formData.balance_discrepancy || 0),
      type: formData.type || 'TRANSFER',
      biometricRiskScore: biometricRiskScore ?? undefined,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/score_transaction`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data = await response.json();
      const transactionId = `TXN-${Date.now().toString().slice(-8)}`;
      setLastSubmittedId(transactionId);

      const newTx = {
        transactionId,
        amount: payload.amount,
        step: payload.step,
        timestamp: new Date().toISOString(),
        status: data.risk_level === 'high' ? 'FLAGGED' : 'COMPLETED',
        riskScore: data.risk_score,
        riskLevel: data.risk_level,
        topReasonCodes: data.top_reason_codes || [],
        inputData: payload,
      };

      if (onTransactionSubmitted) {
        onTransactionSubmitted(newTx);
      }
    } catch (err) {
      console.error('Error submitting transaction:', err);
      setError(err.message || 'Failed to submit transaction for scoring.');
    } finally {
      setLoading(false);
    }
  };

  const fillHighRiskPreset = () => {
    setFormData({
      amount: 450000.00,
      step: 14,
      oldbalanceDest: 0.0,
      newbalanceDest: 0.0,
      transaction_velocity: 18.5,
      amount_deviation: 95.0,
      balance_discrepancy: 450000.00,
      type: 'TRANSFER',
    });
  };

  const fillLowRiskPreset = () => {
    setFormData({
      amount: 45.50,
      step: 1,
      oldbalanceDest: 1200.00,
      newbalanceDest: 1154.50,
      transaction_velocity: 0.5,
      amount_deviation: 0.1,
      balance_discrepancy: 0.0,
      type: 'PAYMENT',
    });
  };

  return (
    <div className="card form-card">
      <div className="card-header">
        <div className="card-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
          <h3>Score New Transaction</h3>
        </div>
        <div className="preset-buttons">
          <button type="button" className="btn-preset high" onClick={fillHighRiskPreset} title="Load high-risk sample data">
            High Risk Sample
          </button>
          <button type="button" className="btn-preset low" onClick={fillLowRiskPreset} title="Load low-risk sample data">
            Low Risk Sample
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {lastSubmittedId && (
        <div className="success-banner">
          <span className="status-dot pending pulse"></span>
          Scored! Transaction ID: <code>{lastSubmittedId}</code> · Risk: <strong>{onTransactionSubmitted ? 'See transaction table' : 'completed'}</strong>
        </div>
      )}

      <form onSubmit={handleSubmit} className="transaction-form">
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="amount">Amount ($) *</label>
            <input
              id="amount"
              name="amount"
              type="number"
              step="0.01"
              value={formData.amount}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="step">Step (Hour Index) *</label>
            <input
              id="step"
              name="step"
              type="number"
              value={formData.step}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="type">Transaction Type</label>
            <select id="type" name="type" value={formData.type} onChange={handleChange} disabled={loading}>
              <option value="TRANSFER">TRANSFER</option>
              <option value="CASH_OUT">CASH_OUT</option>
              <option value="PAYMENT">PAYMENT</option>
              <option value="DEPOSIT">DEPOSIT</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="transaction_velocity">Velocity Index</label>
            <input
              id="transaction_velocity"
              name="transaction_velocity"
              type="number"
              step="0.1"
              value={formData.transaction_velocity}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="amount_deviation">Amount Deviation</label>
            <input
              id="amount_deviation"
              name="amount_deviation"
              type="number"
              step="0.1"
              value={formData.amount_deviation}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="balance_discrepancy">Balance Discrepancy ($)</label>
            <input
              id="balance_discrepancy"
              name="balance_discrepancy"
              type="number"
              step="0.01"
              value={formData.balance_discrepancy}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="oldbalanceDest">Old Balance Dest ($)</label>
            <input
              id="oldbalanceDest"
              name="oldbalanceDest"
              type="number"
              step="0.01"
              value={formData.oldbalanceDest}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="newbalanceDest">New Balance Dest ($)</label>
            <input
              id="newbalanceDest"
              name="newbalanceDest"
              type="number"
              step="0.01"
              value={formData.newbalanceDest}
              onChange={handleChange}
              disabled={loading}
            />
          </div>
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? (
            <span className="spinner-label">
              <span className="btn-spinner"></span> Publishing to Kafka...
            </span>
          ) : (
            'Create Transaction & Run AI Scoring'
          )}
        </button>
      </form>
    </div>
  );
}
