import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * CreditScoringPanel — §6.3 of proposal:
 * "Predictive Risk Analytics and Credit Scoring — integrates alternative data sources
 *  such as utility payment records, social media activity metrics, and real-time cash
 *  flow trends to construct a dynamic credit risk profile."
 *
 * API routes via Spring Boot Gateway (port 8081) with JWT auth header — §5.1:
 * "Flask/FastAPI for model serving" behind the gateway.
 *
 * SHAP explainability per §4.4: "SHAP will allow us to determine which input features
 * have the most substantial impact upon an outcome produced by a prediction model."
 */

const GATEWAY_URL = 'http://localhost:8081';

const DEFAULT_FORM = {
  utility_payment_ratio: 0.82,
  avg_monthly_cashflow: 4500,
  cashflow_volatility: 0.21,
  social_engagement_score: 67,
  credit_inquiries_3m: 1,
};

const HIGH_RISK_PRESET = {
  utility_payment_ratio: 0.12,
  avg_monthly_cashflow: 620,
  cashflow_volatility: 0.91,
  social_engagement_score: 8,
  credit_inquiries_3m: 9,
};

const LOW_RISK_PRESET = {
  utility_payment_ratio: 0.97,
  avg_monthly_cashflow: 12400,
  cashflow_volatility: 0.05,
  social_engagement_score: 88,
  credit_inquiries_3m: 0,
};

/** Client-side synthetic fallback when gateway is offline (demo mode) */
function syntheticCreditResult(data) {
  const score =
    100 -
    Math.round(
      data.utility_payment_ratio * 20 +
        (1 - data.cashflow_volatility) * 20 +
        Math.min(data.avg_monthly_cashflow / 1000, 20) +
        data.social_engagement_score * 0.2 +
        (10 - data.credit_inquiries_3m) * 3
    );
  const clampedScore = Math.min(99, Math.max(0, score));
  return {
    risk_score: clampedScore,
    decision: clampedScore < 45 ? 'APPROVED' : 'REVIEW',
    probability: parseFloat((clampedScore / 100).toFixed(3)),
    shap_explanation: [
      { feature: 'utility_payment_ratio', impact: -(data.utility_payment_ratio * 0.4).toFixed(4) },
      { feature: 'avg_monthly_cashflow', impact: -(Math.min(data.avg_monthly_cashflow / 30000, 1) * 0.3).toFixed(4) },
      { feature: 'cashflow_volatility', impact: (data.cashflow_volatility * 0.5).toFixed(4) },
      { feature: 'social_engagement_score', impact: -(data.social_engagement_score / 300).toFixed(4) },
      { feature: 'credit_inquiries_3m', impact: (data.credit_inquiries_3m * 0.06).toFixed(4) },
    ],
    _demo: true,
  };
}

export default function CreditScoringPanel() {
  const { token, isDemoMode } = useAuth();
  const [form, setForm] = useState({ ...DEFAULT_FORM });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: parseFloat(value) }));
  };

  const handleEvaluate = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);

    const payload = {
      utility_payment_ratio: Number(form.utility_payment_ratio),
      avg_monthly_cashflow: Number(form.avg_monthly_cashflow),
      cashflow_volatility: Number(form.cashflow_volatility),
      social_engagement_score: Number(form.social_engagement_score),
      credit_inquiries_3m: Number(form.credit_inquiries_3m),
    };

    try {
      // Route through Spring Boot Gateway per enterprise microservice architecture
      const response = await fetch(`${GATEWAY_URL}/api/v1/credit-score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Gateway returned HTTP ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.warn('Gateway unreachable — falling back to synthetic demo result:', err.message);
      if (isDemoMode || !token || token === 'demo-jwt-token-investigator-dashboard') {
        // Generate deterministic synthetic result for demo/offline mode
        setResult(syntheticCreditResult(payload));
      } else {
        setError(
          `Unable to reach Spring Gateway at ${GATEWAY_URL}. Ensure the backend is running, or use Demo Mode for offline preview.`
        );
      }
    } finally {
      setLoading(false);
    }
  };

  // Determine max absolute SHAP value for proportional bar widths
  const shapData = result?.shap_explanation || [];
  const maxAbsImpact = shapData.length
    ? Math.max(...shapData.map((s) => Math.abs(parseFloat(s.impact))))
    : 1;

  const decisionApproved = result?.decision === 'APPROVED';
  const riskScore = result?.risk_score ?? null;

  return (
    <div className="card credit-scoring-card">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="card-header">
        <div className="card-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="5" width="20" height="14" rx="2" />
            <line x1="2" y1="10" x2="22" y2="10" />
            <line x1="6" y1="15" x2="10" y2="15" />
          </svg>
          <h3>Predictive Credit Scoring</h3>
        </div>
        <div className="credit-panel-badge">§6.3 Alternative Data Engine</div>
      </div>

      <p className="credit-panel-desc">
        Evaluates creditworthiness using alternative data sources per GDPR-compliant XAI governance.
        Request routes through the <code>Spring Boot Gateway :8081</code> with JWT authentication.
      </p>

      {/* ── Preset Buttons ─────────────────────────────────────────────────── */}
      <div className="credit-preset-row">
        <button type="button" className="btn-preset high" onClick={() => setForm({ ...HIGH_RISK_PRESET })}>
          ⚠ High Risk Sample
        </button>
        <button type="button" className="btn-preset low" onClick={() => setForm({ ...LOW_RISK_PRESET })}>
          ✓ Low Risk Sample
        </button>
        <button type="button" className="btn-preset neutral" onClick={() => setForm({ ...DEFAULT_FORM })}>
          Reset
        </button>
      </div>

      {/* ── Error Banner ───────────────────────────────────────────────────── */}
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

      {/* ── Input Form ─────────────────────────────────────────────────────── */}
      <form onSubmit={handleEvaluate} className="credit-form">
        <div className="credit-form-grid">

          {/* Utility Payment Ratio */}
          <div className="credit-form-group">
            <div className="credit-label-row">
              <label htmlFor="utility_payment_ratio">Utility Payment Ratio</label>
              <span className="credit-range-val">{Number(form.utility_payment_ratio).toFixed(2)}</span>
            </div>
            <input
              id="utility_payment_ratio"
              name="utility_payment_ratio"
              type="range"
              min="0" max="1" step="0.01"
              value={form.utility_payment_ratio}
              onChange={handleChange}
              className="credit-slider"
              disabled={loading}
            />
            <div className="credit-slider-labels"><span>0.00 (Poor)</span><span>1.00 (Perfect)</span></div>
          </div>

          {/* Cashflow Volatility */}
          <div className="credit-form-group">
            <div className="credit-label-row">
              <label htmlFor="cashflow_volatility">Cashflow Volatility</label>
              <span className="credit-range-val">{Number(form.cashflow_volatility).toFixed(2)}</span>
            </div>
            <input
              id="cashflow_volatility"
              name="cashflow_volatility"
              type="range"
              min="0" max="1" step="0.01"
              value={form.cashflow_volatility}
              onChange={handleChange}
              className="credit-slider credit-slider-danger"
              disabled={loading}
            />
            <div className="credit-slider-labels"><span>0.00 (Stable)</span><span>1.00 (Volatile)</span></div>
          </div>

          {/* Avg Monthly Cashflow */}
          <div className="credit-form-group">
            <label htmlFor="avg_monthly_cashflow" className="credit-label-plain">
              Avg Monthly Cashflow ($)
            </label>
            <input
              id="avg_monthly_cashflow"
              name="avg_monthly_cashflow"
              type="number"
              min="500" max="20000" step="50"
              value={form.avg_monthly_cashflow}
              onChange={handleChange}
              className="credit-number-input"
              disabled={loading}
            />
          </div>

          {/* Social Engagement Score */}
          <div className="credit-form-group">
            <div className="credit-label-row">
              <label htmlFor="social_engagement_score">Social Engagement Score</label>
              <span className="credit-range-val">{Math.round(form.social_engagement_score)}</span>
            </div>
            <input
              id="social_engagement_score"
              name="social_engagement_score"
              type="range"
              min="0" max="100" step="1"
              value={form.social_engagement_score}
              onChange={handleChange}
              className="credit-slider"
              disabled={loading}
            />
            <div className="credit-slider-labels"><span>0</span><span>100</span></div>
          </div>

          {/* Credit Inquiries 3m */}
          <div className="credit-form-group credit-form-group-full">
            <div className="credit-label-row">
              <label htmlFor="credit_inquiries_3m">Credit Inquiries (Last 3 Months)</label>
              <span className="credit-range-val">{Math.round(form.credit_inquiries_3m)}</span>
            </div>
            <input
              id="credit_inquiries_3m"
              name="credit_inquiries_3m"
              type="range"
              min="0" max="10" step="1"
              value={form.credit_inquiries_3m}
              onChange={handleChange}
              className={`credit-slider ${form.credit_inquiries_3m >= 6 ? 'credit-slider-danger' : ''}`}
              disabled={loading}
            />
            <div className="credit-slider-labels"><span>0 (None)</span><span>10 (High)</span></div>
          </div>

        </div>

        <button type="submit" className="credit-submit-btn" disabled={loading}>
          {loading ? (
            <span className="spinner-label">
              <span className="btn-spinner"></span> Evaluating via Gateway...
            </span>
          ) : (
            <>
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
              Evaluate Credit Risk →
            </>
          )}
        </button>
      </form>

      {/* ── Result Panel ───────────────────────────────────────────────────── */}
      {result && (
        <div className={`credit-result-card ${decisionApproved ? 'result-approved' : 'result-review'}`}>

          {/* Demo mode notice */}
          {result._demo && (
            <div className="demo-result-notice">
              ⚡ Synthetic result (gateway offline) — real SHAP values available when Flask + Gateway are running
            </div>
          )}

          {/* Score + Decision */}
          <div className="credit-result-header">
            <div className="credit-score-circle">
              <svg viewBox="0 0 80 80" className="credit-score-svg">
                <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="6" />
                <circle
                  cx="40" cy="40" r="34"
                  fill="none"
                  stroke={decisionApproved ? '#10b981' : '#f59e0b'}
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={`${(riskScore / 99) * 213.6} 213.6`}
                  transform="rotate(-90 40 40)"
                />
              </svg>
              <div className="credit-score-inner">
                <span className="credit-score-num">{riskScore}</span>
                <span className="credit-score-label">/99</span>
              </div>
            </div>

            <div className="credit-result-summary">
              <div className={`decision-badge ${decisionApproved ? 'decision-approved' : 'decision-review'}`}>
                {decisionApproved ? '✓ APPROVED' : '⚠ REVIEW'}
              </div>
              <div className="credit-prob-row">
                <span className="credit-prob-label">Default Probability:</span>
                <span className="credit-prob-val">
                  {(parseFloat(result.probability) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="credit-prob-row">
                <span className="credit-prob-label">Risk Score:</span>
                <span className={`credit-prob-val ${riskScore >= 70 ? 'text-error' : riskScore >= 35 ? 'text-amber' : 'text-emerald'}`}>
                  {riskScore} / 99
                </span>
              </div>
              <div className="credit-gateway-badge">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
                Scored via Spring Gateway :8081 · JWT Auth
              </div>
            </div>
          </div>

          {/* SHAP Explanation Bars — §4.4 Proposal */}
          {shapData.length > 0 && (
            <div className="shap-section">
              <div className="shap-section-title">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4" />
                </svg>
                SHAP Feature Contributions
                <span className="shap-subtitle">XGBoost Explainability — EU AI Act §4.4 compliant</span>
              </div>

              <div className="shap-legend">
                <span><span className="shap-legend-dot shap-risk"></span> Risk Increasing (+)</span>
                <span><span className="shap-legend-dot shap-safe"></span> Risk Reducing (−)</span>
              </div>

              <div className="shap-bars">
                {shapData.map((item, idx) => {
                  const impact = parseFloat(item.impact);
                  const isPositive = impact > 0;
                  const pct = Math.min(Math.abs(impact) / maxAbsImpact, 1) * 100;
                  return (
                    <div key={idx} className="shap-bar-row">
                      <div className="shap-feature-name">{item.feature}</div>
                      <div className="shap-bar-track">
                        <div
                          className={`shap-bar-fill ${isPositive ? 'shap-bar-risk' : 'shap-bar-safe'}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <div className={`shap-impact-val ${isPositive ? 'text-error' : 'text-emerald'}`}>
                        {impact > 0 ? `+${impact}` : impact}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
