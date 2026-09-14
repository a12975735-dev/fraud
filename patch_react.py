import os

base_dir = r"c:\fraud-detection-project\investigator-dashboard\src\pages"

dashboard_code = """import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Bell, ChevronDown } from "lucide-react";
import Sidebar from "../components/Sidebar";
import { useNavigate } from "react-router-dom";

const TREND_DATA = [
  { t: "00:00", all: 820, flagged: 22 }, { t: "04:00", all: 610, flagged: 14 }, { t: "08:00", all: 1450, flagged: 48 },
  { t: "12:00", all: 2380, flagged: 71 }, { t: "16:00", all: 3120, flagged: 96 }, { t: "20:00", all: 2260, flagged: 58 },
  { t: "24:00", all: 1180, flagged: 29 },
];
const TOP_RISKY_ACCOUNTS = [
  { account: "1002345678", score: 92, txns: 23 }, { account: "2003456789", score: 89, txns: 17 }, { account: "1009876543", score: 85, txns: 19 },
];

function StatCard({ label, value, delta, positiveIsBad }) {
  const isUp = delta.startsWith("+");
  const badColor = positiveIsBad ? isUp : !isUp;
  const deltaColor = badColor ? "#D64545" : "#2FA36B";
  return (
    <div style={{ background: "#fff", borderRadius: 10, padding: "18px 20px", border: "1px solid #E7E9EE", flex: 1, minWidth: 180 }}>
      <div style={{ fontSize: 13, color: "#6B7280", marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: "#111827", letterSpacing: -0.5 }}>{value}</div>
      <div style={{ fontSize: 12.5, color: deltaColor, marginTop: 6, fontWeight: 600 }}>{isUp ? "↑" : "↓"} {delta.replace(/^[+-]/, "")} vs yesterday</div>
    </div>
  );
}

function StatusPill({ status }) {
  const map = { New: { bg: "#FDECEC", fg: "#C13B3B" }, "In Review": { bg: "#FFF4E0", fg: "#B4791E" }, Closed: { bg: "#EAF6EE", fg: "#2C8A57" } };
  const s = map[status] || map.New;
  return <span style={{ background: s.bg, color: s.fg, fontSize: 12, fontWeight: 600, padding: "3px 10px", borderRadius: 100 }}>{status}</span>;
}

export default function DashboardOverview() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_transactions: 0,
    flagged_transactions: 0,
    high_risk: 0,
    risk_distribution: { Low: 0, Medium: 0, High: 0 }
  });
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetch('http://localhost:5001/api/dashboard/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error(err));
      
    fetch('http://localhost:5001/api/alerts')
      .then(res => res.json())
      .then(data => setAlerts(data.alerts || []))
      .catch(err => console.error(err));
  }, []);

  const RISK_DATA = [
    { name: "Low (0–30)", value: stats.risk_distribution.Low, color: "#2FA36B" },
    { name: "Medium (30–70)", value: stats.risk_distribution.Medium, color: "#E0A02A" },
    { name: "High (70–100)", value: stats.risk_distribution.High, color: "#D64545" },
  ];
  const totalRisk = RISK_DATA.reduce((a, b) => a + b.value, 0);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter', 'Segoe UI', -apple-system, sans-serif", color: "#111827" }}>
      <Sidebar activeKey="dashboard" />
      <main style={{ flex: 1, padding: "24px 28px", overflowX: "hidden" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 22 }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Dashboard Overview</h1>
          <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
            <div style={{ position: "relative" }}>
              <Bell size={19} color="#4B5563" />
              <span style={{ position: "absolute", top: -6, right: -6, background: "#D64545", color: "#fff", fontSize: 10, fontWeight: 700, borderRadius: 100, width: 16, height: 16, display: "flex", alignItems: "center", justifyContent: "center" }}>{stats.high_risk}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
              <div style={{ width: 30, height: 30, borderRadius: "50%", background: "#1B4DFF", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 12.5, fontWeight: 700 }}>IN</div>
              <span style={{ fontSize: 13.5, fontWeight: 600 }}>Investigator</span>
              <ChevronDown size={14} color="#6B7280" />
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 14, marginBottom: 20, flexWrap: "wrap" }}>
          <StatCard label="Total Transactions" value={stats.total_transactions.toLocaleString()} delta="+12.6%" />
          <StatCard label="Flagged Transactions" value={stats.flagged_transactions.toLocaleString()} delta="+18.3%" positiveIsBad />
          <StatCard label="High Risk" value={stats.high_risk.toLocaleString()} delta="+9.7%" positiveIsBad />
          <StatCard label="Investigations" value="45" delta="+5.1%" positiveIsBad />
        </div>
        <div style={{ display: "flex", gap: 16, marginBottom: 16, alignItems: "stretch" }}>
          <div style={{ flex: 2, background: "#fff", borderRadius: 10, border: "1px solid #E7E9EE", padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Transactions Over Time</div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={TREND_DATA}>
                <CartesianGrid stroke="#EFF1F5" vertical={false} />
                <XAxis dataKey="t" tick={{ fontSize: 11, fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E7E9EE" }} />
                <Line type="monotone" dataKey="all" stroke="#1B4DFF" strokeWidth={2} dot={false} name="All Transactions" />
                <Line type="monotone" dataKey="flagged" stroke="#D64545" strokeWidth={2} dot={false} name="Flagged" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div style={{ flex: 1, background: "#fff", borderRadius: 10, border: "1px solid #E7E9EE", padding: "18px 20px", display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>Risk Distribution</div>
            <div style={{ position: "relative", flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={RISK_DATA} dataKey="value" innerRadius={48} outerRadius={68} paddingAngle={2}>
                    {RISK_DATA.map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div style={{ position: "absolute", textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 700 }}>{totalRisk.toLocaleString()}</div>
                <div style={{ fontSize: 10.5, color: "#9CA3AF" }}>Total</div>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
              {RISK_DATA.map((d) => (
                <div key={d.name} style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6, color: "#4B5563" }}><span style={{ width: 8, height: 8, borderRadius: "50%", background: d.color, display: "inline-block" }} />{d.name}</span>
                  <span style={{ fontWeight: 600 }}>{totalRisk > 0 ? ((d.value / totalRisk) * 100).toFixed(1) : 0}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 16 }}>
          <div style={{ flex: 1.4, background: "#fff", borderRadius: 10, border: "1px solid #E7E9EE", padding: "16px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Recent Alerts (Test Set)</div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
              <thead><tr style={{ color: "#9CA3AF", textAlign: "left" }}><th style={{ paddingBottom: 8, fontWeight: 600 }}>Time</th><th style={{ paddingBottom: 8, fontWeight: 600 }}>Transaction ID</th><th style={{ paddingBottom: 8, fontWeight: 600 }}>Type</th><th style={{ paddingBottom: 8, fontWeight: 600 }}>Risk Score</th><th style={{ paddingBottom: 8, fontWeight: 600 }}>Status</th></tr></thead>
              <tbody>
                {alerts.slice(0, 5).map((a) => (
                  <tr key={a.id} style={{ borderTop: "1px solid #F1F2F5", cursor: "pointer" }} onClick={() => navigate(`/alerts/${a.id}`)}>
                    <td style={{ padding: "9px 0", color: "#6B7280" }}>{a.time}</td>
                    <td style={{ padding: "9px 0", fontWeight: 500, color: "#1B4DFF" }}>{a.id}</td>
                    <td style={{ padding: "9px 0", color: "#6B7280" }}>{a.type}</td>
                    <td style={{ padding: "9px 0", fontWeight: 700, color: a.score >= 70 ? "#D64545" : "#B4791E" }}>{a.score.toFixed(2)}</td>
                    <td style={{ padding: "9px 0" }}><StatusPill status={a.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ flex: 1, background: "#fff", borderRadius: 10, border: "1px solid #E7E9EE", padding: "16px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Top Risky Accounts</div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
              <thead><tr style={{ color: "#9CA3AF", textAlign: "left" }}><th style={{ paddingBottom: 8, fontWeight: 600 }}>Account</th><th style={{ paddingBottom: 8, fontWeight: 600 }}>Risk Score</th><th style={{ paddingBottom: 8, fontWeight: 600 }}># Txns</th></tr></thead>
              <tbody>
                {TOP_RISKY_ACCOUNTS.map((r) => (
                  <tr key={r.account} style={{ borderTop: "1px solid #F1F2F5" }}>
                    <td style={{ padding: "9px 0", fontWeight: 500 }}>{r.account}</td>
                    <td style={{ padding: "9px 0", fontWeight: 700, color: "#D64545" }}>{r.score}</td>
                    <td style={{ padding: "9px 0", color: "#6B7280" }}>{r.txns}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
"""

alert_detail_code = """import { useState, useEffect } from "react";
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
"""

with open(os.path.join(base_dir, "DashboardOverview.jsx"), "w", encoding="utf-8") as f: f.write(dashboard_code)
with open(os.path.join(base_dir, "AlertDetail.jsx"), "w", encoding="utf-8") as f: f.write(alert_detail_code)

print("React components successfully patched to use API.")
