import { AlertTriangle } from "lucide-react";
import Sidebar from "../components/Sidebar";

function Field({ label, value }) {
  return <div><div style={{ fontSize: 11.5, color: "#9CA3AF" }}>{label}</div><div style={{ fontSize: 13.5, fontWeight: 600, marginTop: 2 }}>{value}</div></div>;
}

export default function TransactionRiskScoring() {
  const score = 88;
  const factors = [
    { label: "Transaction Amount (USD)", value: 1.96 }, { label: "New Beneficiary", value: 1.42 },
    { label: "High Risk Country", value: 1.08 }, { label: "High Velocity (txn/hour)", value: 0.82 }, { label: "Odd Transaction Time", value: 0.47 },
  ];
  const max = Math.max(...factors.map((f) => f.value));

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter','Segoe UI',-apple-system,sans-serif", color: "#111827" }}>
      <Sidebar activeKey="transactions" />
      <main style={{ flex: 1, padding: "24px 28px" }}>
        <h1 style={{ fontSize: 19, fontWeight: 700, margin: "0 0 18px" }}>Transaction Risk Scoring</h1>
        <div style={{ background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px", marginBottom: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Transaction Details</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "16px 24px" }}>
            <Field label="Transaction ID" value="TXN-20260814-000567" /><Field label="Amount (USD)" value="5,200.00" /><Field label="Channel" value="Online Banking" />
            <Field label="From Account" value="1002345678" /><Field label="Device ID" value="DEV-8F6A21C9" /><Field label="Time" value="2026-08-14 10:24:35" />
            <Field label="To Account" value="2098765432 (John D.)" /><Field label="Location" value="Lagos, Nigeria" />
          </div>
        </div>
        <div style={{ display: "flex", gap: 16 }}>
          <div style={{ flex: 1, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>Risk Assessment Result</div>
            <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
              <div style={{ position: "relative", width: 110, height: 110 }}>
                <svg viewBox="0 0 100 100" style={{ transform: "rotate(-90deg)" }}>
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#F0F1F4" strokeWidth="10" />
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#D64545" strokeWidth="10" strokeDasharray={`${(score / 100) * 264} 264`} strokeLinecap="round" />
                </svg>
                <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                  <div style={{ fontSize: 22, fontWeight: 700 }}>{score}</div><div style={{ fontSize: 10, color: "#9CA3AF" }}>/100</div>
                </div>
              </div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}><AlertTriangle size={16} color="#D64545" /><span style={{ fontSize: 14, fontWeight: 700, color: "#D64545" }}>SUSPICIOUS</span></div>
                <Field label="Model" value="Ensemble (XGBoost + LightGBM + CatBoost)" />
                <div style={{ marginTop: 10 }}><Field label="Processed At" value="2026-08-14 10:24:35" /></div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
              <button style={{ flex: 1, border: "1px solid #E1E4EA", borderRadius: 8, padding: "9px 0", fontSize: 12.5, fontWeight: 600, background: "#fff", cursor: "pointer" }}>View SHAP Explanation</button>
              <button style={{ flex: 1, border: "none", borderRadius: 8, padding: "9px 0", fontSize: 12.5, fontWeight: 600, background: "#1B4DFF", color: "#fff", cursor: "pointer" }}>Add to Investigation Queue</button>
            </div>
          </div>
          <div style={{ flex: 1, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Top Contributing Factors</div>
            {factors.map((f) => (
              <div key={f.label} style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#4B5563", marginBottom: 4 }}>
                  <span>{f.label}</span><span style={{ fontWeight: 700, color: "#D64545" }}>+{f.value.toFixed(2)}</span>
                </div>
                <div style={{ height: 7, borderRadius: 100, background: "#F0F1F4" }}>
                  <div style={{ width: `${(f.value / max) * 100}%`, height: "100%", borderRadius: 100, background: "#D64545" }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
