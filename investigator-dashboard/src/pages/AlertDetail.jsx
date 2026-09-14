import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { ChevronRight, CheckCircle2, AlertTriangle, Flag, Eye } from "lucide-react";
import Sidebar from "../components/Sidebar";

function Field({ label, value }) {
  return <div><div style={{ fontSize: 11.5, color: "#9CA3AF" }}>{label}</div><div style={{ fontSize: 13.5, fontWeight: 600, marginTop: 2 }}>{value}</div></div>;
}

export default function AlertDetail() {
  const { id } = useParams();
  const txIndex = id ? id.replace("TXN-", "") : "0";
  
  const [shapFeatures, setShapFeatures] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:5001/api/alerts/${txIndex}/shap`)
      .then(res => res.json())
      .then(data => {
        setShapFeatures(data.shap_features || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [txIndex]);

  const maxAbs = shapFeatures.length > 0 ? Math.max(...shapFeatures.map((f) => Math.abs(f.value))) : 1;
  const score = 87; // We could fetch the specific alert to get its score

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter','Segoe UI',-apple-system,sans-serif", color: "#111827" }}>
      <Sidebar activeKey="alerts" />
      <main style={{ flex: 1, padding: "24px 28px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, color: "#9CA3AF", marginBottom: 10 }}>
          Alerts <ChevronRight size={13} /> <span style={{ color: "#111827" }}>Alert Detail</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ background: "#FDECEC", color: "#C13B3B", fontSize: 11.5, fontWeight: 700, padding: "4px 10px", borderRadius: 6 }}>HIGH RISK</span>
            <h1 style={{ fontSize: 19, fontWeight: 700, margin: 0 }}>Alert ALRT-2025-{txIndex.padStart(5, '0')}</h1>
          </div>
          <select style={{ fontSize: 13, border: "1px solid #E1E4EA", borderRadius: 7, padding: "7px 12px", background: "#fff" }}>
            <option>New</option><option>In Review</option><option>Closed</option>
          </select>
        </div>
        <div style={{ display: "flex", gap: 16, marginBottom: 16, alignItems: "stretch" }}>
          <div style={{ flex: 1.6, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Transaction Details</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px 24px" }}>
              <Field label="Transaction ID" value={`TXN-${txIndex}`} /><Field label="Date & Time" value="2025-05-20 15:25:38" />
              <Field label="Account Number" value="1002345678" /><Field label="Channel" value="Online Banking" />
              <Field label="Amount (USD)" value="5,200.00" /><Field label="Merchant" value="Global Electronics Ltd." />
              <Field label="Location" value="Lagos, Nigeria" /><Field label="Device" value="Chrome / Windows" />
              <Field label="IP Address" value="197.12.22.45" />
            </div>
          </div>
          <div style={{ flex: 1, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 6 }}>Model Prediction</div>
            <div style={{ fontSize: 12, color: "#9CA3AF", marginBottom: 4 }}>Prediction</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: "#D64545", marginBottom: 14 }}>FRAUDULENT</div>
            <div style={{ fontSize: 12, color: "#9CA3AF", marginBottom: 4 }}>Risk Score</div>
            <div style={{ fontSize: 30, fontWeight: 700, marginBottom: 8 }}>{score}<span style={{ fontSize: 14, color: "#9CA3AF" }}>/100</span></div>
            <div style={{ height: 6, borderRadius: 100, background: "#F0F1F4", position: "relative" }}>
              <div style={{ width: `${score}%`, height: "100%", borderRadius: 100, background: "linear-gradient(90deg,#E0A02A,#D64545)" }} />
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 16 }}>
          <div style={{ flex: 1.6, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px", maxHeight: 500, overflowY: "auto" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>Feature Contribution (SHAP Explanation)</div>
            <div style={{ fontSize: 11.5, color: "#9CA3AF", marginBottom: 16 }}>Positive values push the prediction toward fraud</div>
            {loading ? <div style={{padding: 20, textAlign: "center", color: "#6B7280"}}>Loading SHAP values...</div> : 
              shapFeatures.slice(0, 15).map((f) => {
              const isPos = f.value > 0;
              const widthPct = (Math.abs(f.value) / maxAbs) * 45;
              return (
                <div key={f.label} style={{ display: "flex", alignItems: "center", marginBottom: 10, fontSize: 12.5 }}>
                  <div style={{ width: "42%", textAlign: "right", paddingRight: 10, color: "#4B5563", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} title={f.label}>{f.label}</div>
                  <div style={{ width: "58%", position: "relative", height: 18 }}>
                    <div style={{ position: "absolute", left: "0%", width: 1, height: "100%", background: "#E1E4EA" }} />
                    <div style={{ position: "absolute", height: "100%", borderRadius: 3, left: isPos ? "0%" : `${45 - widthPct}%`, width: `${widthPct}%`, background: isPos ? "#D64545" : "#2FA36B" }} />
                    <span style={{ position: "absolute", left: isPos ? `${widthPct + 2}%` : undefined, right: isPos ? undefined : `${45 - (45 - widthPct) + 2}%`, fontSize: 11, fontWeight: 700, color: isPos ? "#D64545" : "#2FA36B", top: 0 }}>{isPos ? "+" : ""}{f.value.toFixed(2)}</span>
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "16px 18px" }}>
              <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 10 }}>Investigation Notes</div>
              <textarea placeholder="Add your notes here..." style={{ width: "100%", minHeight: 70, border: "1px solid #E1E4EA", borderRadius: 8, padding: 10, fontSize: 12.5, fontFamily: "inherit", resize: "none", outline: "none" }} />
            </div>
            <div style={{ background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "16px 18px" }}>
              <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Investigation Actions</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {[
                  { label: "Mark Legitimate", icon: CheckCircle2, color: "#2FA36B" }, { label: "Confirm Fraud", icon: AlertTriangle, color: "#D64545" },
                  { label: "Escalate Case", icon: Flag, color: "#B4791E" }, { label: "Add to Watchlist", icon: Eye, color: "#1B4DFF" },
                ].map((b) => {
                  const Icon = b.icon;
                  return (
                    <button key={b.label} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, border: "1px solid #E1E4EA", borderRadius: 8, padding: "9px 4px", fontSize: 11.5, fontWeight: 600, color: b.color, background: "#fff", cursor: "pointer" }}>
                      <Icon size={14} />{b.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
