import React, { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

const API_BASE_URL = 'http://127.0.0.1:8081';

export default function AlertsFeed({ transactions, setTransactions, onSelectTransaction, selectedTransactionId }) {
  const { token } = useAuth();

  // Auto-refresh poll every 3 seconds for any transaction still PENDING
  useEffect(() => {
    if (!token) return;

    const pendingTxs = transactions.filter((tx) => tx.status === 'PENDING');
    if (pendingTxs.length === 0) return;

    const pollPendingTransactions = async () => {
      for (const tx of pendingTxs) {
        try {
          const response = await fetch(`${API_BASE_URL}/api/transaction/${tx.transactionId}/status`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (response.ok) {
            const data = await response.json(); // ScoredTransaction entity
            if (data.status !== 'PENDING') {
              let parsedReasonCodes = data.topReasonCodes;
              if (typeof data.topReasonCodes === 'string') {
                try {
                  parsedReasonCodes = JSON.parse(data.topReasonCodes);
                } catch (e) {
                  console.warn('Failed to parse topReasonCodes string:', e);
                }
              }

              setTransactions((prevList) =>
                prevList.map((item) => {
                  if (item.transactionId === tx.transactionId) {
                    return {
                      ...item,
                      status: data.status,
                      riskScore: data.riskScore,
                      riskLevel: data.riskLevel,
                      topReasonCodes: parsedReasonCodes,
                      rawPythonResponse: data.rawPythonResponse,
                    };
                  }
                  return item;
                })
              );
            }
          }
        } catch (err) {
          console.error(`Polling error for tx ${tx.transactionId}:`, err);
        }
      }
    };

    // Execute immediately on mount/update, then poll every 3 seconds
    pollPendingTransactions();
    const interval = setInterval(pollPendingTransactions, 3000);

    return () => clearInterval(interval);
  }, [transactions, token, setTransactions]);

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val || 0);
  };

  const formatTime = (isoStr) => {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="card alerts-card">
      <div className="card-header">
        <div className="card-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <h3>Real-Time Alerts Feed</h3>
          <span className="live-pill">
            <span className="pulse-dot"></span> 3s Auto-Poll
          </span>
        </div>
        <div className="feed-count">{transactions.length} Scored Today</div>
      </div>

      {transactions.length === 0 ? (
        <div className="empty-feed">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <p>No transactions scored yet in this session.</p>
          <small>Use the form on the left to submit a new transaction.</small>
        </div>
      ) : (
        <div className="alerts-feed-list">
          {transactions.map((tx) => {
            const isHigh = tx.riskLevel === 'high';
            const isMedium = tx.riskLevel === 'medium';
            const isLow = tx.riskLevel === 'low';
            const isSelected = selectedTransactionId === tx.transactionId;

            let rowClass = 'alert-row';
            if (isHigh) rowClass += ' alert-row-high';
            else if (isMedium) rowClass += ' alert-row-medium';
            else if (isLow) rowClass += ' alert-row-low';
            if (isSelected) rowClass += ' selected';

            return (
              <div
                key={tx.transactionId}
                className={rowClass}
                onClick={() => onSelectTransaction(tx)}
                title="Click to view deep-dive SHAP risk breakdown"
              >
                <div className="alert-col col-id">
                  <span className="tx-id-badge">
                    <code>{tx.transactionId.substring(0, 8)}...</code>
                  </span>
                  <span className="tx-time">{formatTime(tx.timestamp)}</span>
                </div>

                <div className="alert-col col-amount">
                  <div className="amount-val">{formatCurrency(tx.amount)}</div>
                  <div className="step-val">Step: {tx.step}</div>
                </div>

                <div className="alert-col col-score">
                  {tx.status === 'COMPLETED' ? (
                    <div className={`score-box risk-${tx.riskLevel}`}>
                      <span className="score-num">{tx.riskScore}</span>
                      <span className="score-max">/99</span>
                    </div>
                  ) : tx.status === 'FAILED' ? (
                    <span className="badge badge-failed">FAILED</span>
                  ) : (
                    <span className="badge badge-pending">
                      <span className="status-dot pending pulse"></span> PENDING
                    </span>
                  )}
                </div>

                <div className="alert-col col-level">
                  {tx.status === 'COMPLETED' ? (
                    <span className={`risk-pill risk-${tx.riskLevel}`}>
                      {tx.riskLevel?.toUpperCase()}
                    </span>
                  ) : (
                    <span className="risk-pill pending">EVALUATING</span>
                  )}
                </div>

                <div className="alert-col col-action">
                  <button className="btn-deep-dive">
                    Dig Deep →
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
