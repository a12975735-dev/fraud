import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';

function CustomBarTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const isPositive = data.impact > 0;
    return (
      <div className="custom-tooltip">
        <strong>{data.feature}</strong>
        <div className="tooltip-row">
          <span>SHAP Impact Value:</span>
          <strong style={{ color: isPositive ? '#ef4444' : '#3b82f6' }}>
            {data.impact > 0 ? `+${data.impact.toFixed(4)}` : data.impact.toFixed(4)}
          </strong>
        </div>
        <div className="tooltip-row">
          <span>Effect:</span>
          <span className={isPositive ? 'text-error' : 'text-primary'}>
            {isPositive ? 'Risk Increasing (+)' : 'Risk Reducing (-)'}
          </span>
        </div>
      </div>
    );
  }
  return null;
}

/**
 * TransactionDetailModal Component
 * Section 6.4: "dig deep into any flagged transaction to find out exactly why the AI flagged it."
 * Section 5 Requirement: Horizontal bar chart of topReasonCodes clearly labeled "Why this was flagged".
 */
export default function TransactionDetailModal({ transaction, onClose }) {
  if (!transaction) return null;

  // Format topReasonCodes array for Recharts horizontal bar chart
  let reasonCodesData = [];

  if (Array.isArray(transaction.topReasonCodes)) {
    reasonCodesData = transaction.topReasonCodes;
  } else if (typeof transaction.topReasonCodes === 'string') {
    try {
      reasonCodesData = JSON.parse(transaction.topReasonCodes);
    } catch (e) {
      console.warn('Failed to parse topReasonCodes string:', e);
    }
  }

  const chartData = (reasonCodesData || []).map((item) => ({
    feature: item.feature || item.feature_name || 'Unknown Feature',
    impact: typeof item.impact === 'number' ? item.impact : parseFloat(item.impact || 0),
  }));

  const getRiskBadge = (score, level) => {
    if (level === 'high' || score >= 70) return <span className="risk-tag high">HIGH RISK</span>;
    if (level === 'medium' || score >= 30) return <span className="risk-tag medium">MEDIUM RISK</span>;
    return <span className="risk-tag low">LOW RISK</span>;
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="modal-icon">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
                <line x1="11" y1="8" x2="11" y2="14" />
                <line x1="8" y1="11" x2="14" y2="11" />
              </svg>
            </span>
            <div>
              <h2>Transaction Deep-Dive Audit</h2>
              <div className="modal-tx-id">
                ID: <code>{transaction.transactionId}</code>
              </div>
            </div>
          </div>
          <button className="close-btn" onClick={onClose} title="Close Modal">
            ✕
          </button>
        </div>

        <div className="modal-body">
          {/* Risk Summary Header Cards */}
          <div className="modal-summary-grid">
            <div className={`summary-box risk-${transaction.riskLevel}`}>
              <div className="summary-label">Risk Score</div>
              <div className="summary-val">{transaction.riskScore !== null ? transaction.riskScore : 'N/A'} <small>/ 99</small></div>
            </div>

            <div className="summary-box">
              <div className="summary-label">Risk Level Classification</div>
              <div className="summary-val">
                {getRiskBadge(transaction.riskScore, transaction.riskLevel)}
              </div>
            </div>

            <div className="summary-box">
              <div className="summary-label">Transaction Amount</div>
              <div className="summary-val">${transaction.amount?.toLocaleString()}</div>
            </div>

            <div className="summary-box">
              <div className="summary-label">Evaluation Status</div>
              <div className="summary-val">
                <span className={`status-badge ${transaction.status}`}>{transaction.status}</span>
              </div>
            </div>
          </div>

          {/* Section 5: Why this was flagged - Horizontal Bar Chart */}
          <div className="why-flagged-section">
            <div className="section-header-bar">
              <div className="section-title">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
                <h3>Why this was flagged</h3>
              </div>
              <div className="chart-legend">
                <span className="legend-item"><span className="legend-box red"></span> Risk Increasing (+)</span>
                <span className="legend-item"><span className="legend-box blue"></span> Risk Reducing (-)</span>
              </div>
            </div>
            <p className="section-desc">
              SHAP feature contribution values calculated by XGBoost/LightGBM Ensemble model explaining AI risk decision:
            </p>

            {chartData.length === 0 ? (
              <div className="empty-chart">
                <p>No SHAP reason code breakdown available for this transaction.</p>
              </div>
            ) : (
              <div className="horizontal-chart-container">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart
                    layout="vertical"
                    data={chartData}
                    margin={{ top: 10, right: 30, left: 130, bottom: 10 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                    <XAxis
                      type="number"
                      stroke="#64748b"
                      tick={{ fill: '#94a3b8', fontSize: 11 }}
                    />
                    <YAxis
                      dataKey="feature"
                      type="category"
                      stroke="#64748b"
                      tick={{ fill: '#e2e8f0', fontSize: 12, fontWeight: 500 }}
                      width={120}
                    />
                    <Tooltip content={<CustomBarTooltip />} />
                    <ReferenceLine x={0} stroke="#475569" strokeWidth={2} />
                    <Bar dataKey="impact" radius={[0, 4, 4, 0]} barSize={24}>
                      {chartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.impact > 0 ? '#ef4444' : '#3b82f6'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Raw Payload Features */}
          {transaction.inputData && (
            <div className="features-section">
              <h4>Evaluated Transaction Input Attributes</h4>
              <div className="features-grid">
                {Object.entries(transaction.inputData).map(([key, val]) => (
                  <div key={key} className="feature-item">
                    <span className="feature-key">{key}:</span>
                    <span className="feature-val">{typeof val === 'number' ? val.toLocaleString() : String(val)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="close-modal-btn" onClick={onClose}>
            Close Audit View
          </button>
        </div>
      </div>
    </div>
  );
}
