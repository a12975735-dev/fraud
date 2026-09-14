import React, { useState, useEffect } from 'react';

/**
 * Ghost-Execution Live Reasoning Trace Component
 * Section 6.4 of Proposal: "it shows the agent reasoning live, so investigators follow its logic step by step."
 */
export default function GhostExecutionTrace({ transaction }) {
  const [completedSteps, setCompletedSteps] = useState([1]); // Step 1 is immediate
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!transaction) return;

    // Reset step trace state when transaction changes
    setCompletedSteps([1]);
    setFailed(false);

    // Step 2 delay: "Awaiting ML model scoring..."
    const timer1 = setTimeout(() => {
      setCompletedSteps((prev) => (prev.includes(2) ? prev : [...prev, 2]));
    }, 500);

    return () => clearTimeout(timer1);
  }, [transaction?.transactionId]);

  useEffect(() => {
    if (!transaction) return;

    if (transaction.status === 'COMPLETED') {
      // Step 3 delay (after completion): "SHAP explanation generated"
      const timer2 = setTimeout(() => {
        setCompletedSteps((prev) => (prev.includes(3) ? prev : [...prev, 3]));

        // Step 4 delay (after Step 3): "Risk assessment complete"
        const timer3 = setTimeout(() => {
          setCompletedSteps((prev) => (prev.includes(4) ? prev : [...prev, 4]));
        }, 500);

        return () => clearTimeout(timer3);
      }, 500);

      return () => clearTimeout(timer2);
    } else if (transaction.status === 'FAILED') {
      const timerFail = setTimeout(() => {
        setFailed(true);
      }, 500);
      return () => clearTimeout(timerFail);
    }
  }, [transaction?.status]);

  if (!transaction) {
    return (
      <div className="card ghost-execution-card empty">
        <div className="ghost-header">
          <span className="ghost-badge">GHOST-EXECUTION</span>
          <h3>Live AI Agent Reasoning Trace</h3>
        </div>
        <p className="ghost-empty-text">Submit a transaction above to view live agent reasoning logic step-by-step.</p>
      </div>
    );
  }

  const stepsDef = [
    {
      id: 1,
      title: 'Step 1: Ingestion & Messaging',
      desc: 'Transaction published to Kafka stream',
      icon: 'kafka',
    },
    {
      id: 2,
      title: 'Step 2: Model Execution',
      desc: 'Awaiting ML model scoring...',
      icon: 'brain',
    },
    {
      id: 3,
      title: 'Step 3: Explainable AI Analysis',
      desc: 'SHAP explanation generated',
      icon: 'shap',
    },
    {
      id: 4,
      title: 'Step 4: Decision Finalization',
      desc: 'Risk assessment complete',
      icon: 'check',
    },
  ];

  return (
    <div className="card ghost-execution-card">
      <div className="ghost-header">
        <div className="ghost-title-group">
          <span className="ghost-badge pulse-badge">GHOST-EXECUTION LIVE</span>
          <h3>Agent Reasoning Trace</h3>
        </div>
        <div className="ghost-tx-id">
          TX: <code>{transaction.transactionId.substring(0, 8)}...</code>
        </div>
      </div>

      <div className="ghost-timeline">
        {stepsDef.map((step) => {
          const isDone = completedSteps.includes(step.id);
          const isCurrent = !isDone && !failed && step.id === Math.max(...completedSteps) + 1;

          return (
            <div
              key={step.id}
              className={`ghost-step ${isDone ? 'completed' : ''} ${isCurrent ? 'active' : ''} ${
                failed && step.id === 3 ? 'failed' : ''
              }`}
            >
              <div className="ghost-step-indicator">
                {isDone ? (
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : isCurrent ? (
                  <span className="step-spinner"></span>
                ) : (
                  <span>{step.id}</span>
                )}
              </div>

              <div className="ghost-step-content">
                <div className="ghost-step-title">{step.title}</div>
                <div className="ghost-step-desc">
                  {isCurrent ? (
                    <span className="typing-text">{step.desc}</span>
                  ) : isDone ? (
                    step.desc
                  ) : (
                    <span className="step-pending-text">Pending preceding step...</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {failed && (
          <div className="ghost-step failed">
            <div className="ghost-step-indicator error">✕</div>
            <div className="ghost-step-content">
              <div className="ghost-step-title text-error">Scoring Error</div>
              <div className="ghost-step-desc text-error">Scoring failed</div>
            </div>
          </div>
        )}
      </div>

      {transaction.riskScore !== null && transaction.riskScore !== undefined && (
        <div className={`ghost-footer-result risk-${transaction.riskLevel || 'low'}`}>
          <div className="ghost-result-label">Agent Conclusion:</div>
          <div className="ghost-result-value">
            Risk Score: <strong>{transaction.riskScore}/99</strong> | Level:{' '}
            <span className={`risk-tag ${transaction.riskLevel}`}>{transaction.riskLevel?.toUpperCase()}</span>
          </div>
        </div>
      )}
    </div>
  );
}
