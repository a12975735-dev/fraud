import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';

function CustomTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="custom-tooltip">
        <div className="tooltip-header">
          <span>TX: {data.fullId.substring(0, 8)}...</span>
          <span className="tooltip-time">{data.time}</span>
        </div>
        <div className="tooltip-row"><span>Risk Score:</span><strong className={`risk-text-${data.riskLevel}`}>{data.riskScore} / 99</strong></div>
        <div className="tooltip-row"><span>Risk Level:</span><span className={`risk-pill risk-${data.riskLevel}`}>{data.riskLevel?.toUpperCase()}</span></div>
        <div className="tooltip-row"><span>Amount:</span><strong>${data.amount?.toLocaleString()}</strong></div>
      </div>
    );
  }
  return null;
}

/**
 * RiskTrendsChart Component
 * Displays temporal risk score trends using Recharts.
 * 
 * Note: A region-based breakdown (as in the original design) would require a region field to be added to the transaction schema — this chart shows the temporal trend available with current data.
 */
export default function RiskTrendsChart({ transactions }) {
  // Note: A region-based breakdown (as in the original design) would require a region field to be added to the transaction schema — this chart shows the temporal trend available with current data.

  const completedData = transactions
    .filter((tx) => tx.status === 'COMPLETED' && tx.riskScore !== null && tx.riskScore !== undefined)
    .map((tx) => {
      const parsedTime = new Date(tx.timestamp);
      const timeLabel = Number.isNaN(parsedTime.getTime())
        ? tx.timestamp || 'Now'
        : parsedTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      return {
        id: tx.transactionId.substring(0, 6),
        fullId: tx.transactionId,
        time: timeLabel,
        riskScore: tx.riskScore,
        riskLevel: tx.riskLevel,
        amount: tx.amount,
      };
    })
    .reverse(); // Display in chronological order for trend line

  return (
    <div className="card chart-card">
      <div className="card-header">
        <div className="card-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          <h3>Risk Score Trend Over Time</h3>
        </div>
        <div className="chart-subtitle">Session Evaluation Analytics</div>
      </div>

      {completedData.length === 0 ? (
        <div className="empty-chart">
          <p>No completed transaction data yet for trend rendering.</p>
          <small>Score transactions to build real-time trend line.</small>
        </div>
      ) : (
        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={completedData} margin={{ top: 15, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="time"
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
                tickLine={{ stroke: '#334155' }}
              />
              <YAxis
                domain={[0, 100]}
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
                tickLine={{ stroke: '#334155' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'High Risk (70+)', fill: '#ef4444', fontSize: 10, position: 'insideTopRight' }} />
              <ReferenceLine y={30} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'Medium Risk (30+)', fill: '#f59e0b', fontSize: 10, position: 'insideBottomRight' }} />
              <Line
                type="monotone"
                dataKey="riskScore"
                stroke="#06b6d4"
                strokeWidth={3}
                dot={{ fill: '#0891b2', r: 5, stroke: '#06b6d4', strokeWidth: 2 }}
                activeDot={{ r: 8, fill: '#38bdf8', stroke: '#ffffff', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
