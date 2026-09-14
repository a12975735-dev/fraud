import os

base_dir = r"c:\fraud-detection-project\investigator-dashboard\src"
components_dir = os.path.join(base_dir, "components")
pages_dir = os.path.join(base_dir, "pages")
os.makedirs(pages_dir, exist_ok=True)

sidebar_code = """import {
  LayoutDashboard, Receipt, Bell, Fingerprint, Share2, Search,
  BarChart3, Settings, LogOut, ShieldCheck
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard, path: "/dashboard" },
  { key: "transactions", label: "Transactions", icon: Receipt, path: "/transactions" },
  { key: "alerts", label: "Alerts", icon: Bell, path: "/alerts" },
  { key: "biometric", label: "Biometric Monitor", icon: Fingerprint, path: "/biometric" },
  { key: "investigation", label: "Investigation", icon: Search, path: "/investigation" },
  { key: "graph", label: "Graph Network", icon: Share2, path: "/graph" },
  { key: "reports", label: "Reports", icon: BarChart3, path: "/reports" },
  { key: "settings", label: "Settings", icon: Settings, path: "/settings" },
];

export default function Sidebar({ activeKey }) {
  const navigate = useNavigate();
  const { logout } = useAuth();
  
  return (
    <aside style={{ width: 232, background: "#0B1526", color: "#C9D2E0", display: "flex", flexDirection: "column", flexShrink: 0, minHeight: '100vh' }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "22px 20px 20px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
        <div style={{ width: 32, height: 32, borderRadius: 8, background: "#1B4DFF", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <ShieldCheck size={18} color="#fff" />
        </div>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: "#fff", lineHeight: 1.2 }}>Smart Banking</div>
          <div style={{ fontSize: 10.5, color: "#7C8AA5" }}>Fraud Detection System</div>
        </div>
      </div>
      <nav style={{ padding: "14px 12px", flex: 1 }}>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = item.key === activeKey;
          return (
            <div key={item.key} onClick={() => navigate(item.path)} style={{
              display: "flex", alignItems: "center", gap: 11,
              padding: "9px 12px", borderRadius: 8, marginBottom: 2,
              background: isActive ? "#1B4DFF" : "transparent",
              color: isActive ? "#fff" : "#AEB9CC",
              fontSize: 13.5, fontWeight: isActive ? 600 : 500,
              cursor: "pointer",
            }}>
              <Icon size={16} />{item.label}
            </div>
          );
        })}
      </nav>
      <div onClick={logout} style={{
        padding: "12px 20px 20px", borderTop: "1px solid rgba(255,255,255,0.08)",
        display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: "#AEB9CC",
        cursor: "pointer",
      }}>
        <LogOut size={15} /> Logout
      </div>
    </aside>
  );
}
"""

dashboard_code = """import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Bell, ChevronDown } from "lucide-react";
import Sidebar from "../components/Sidebar";

const TREND_DATA = [
  { t: "00:00", all: 820, flagged: 22 }, { t: "04:00", all: 610, flagged: 14 }, { t: "08:00", all: 1450, flagged: 48 },
  { t: "12:00", all: 2380, flagged: 71 }, { t: "16:00", all: 3120, flagged: 96 }, { t: "20:00", all: 2260, flagged: 58 },
  { t: "24:00", all: 1180, flagged: 29 },
];
const RISK_DATA = [
  { name: "Low (0–40)", value: 18300, color: "#2FA36B" }, { name: "Medium (40–70)", value: 4123, color: "#E0A02A" }, { name: "High (70–100)", value: 2066, color: "#D64545" },
];
const RECENT_ALERTS = [
  { time: "14:35:28", id: "TXN-20250520-143528", type: "Transaction", score: 87, status: "New" },
  { time: "14:31:09", id: "TXN-20250520-143109", type: "Transaction", score: 76, status: "New" },
  { time: "14:28:47", id: "TXN-20250520-142647", type: "Login", score: 71, status: "In Review" },
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
              <span style={{ position: "absolute", top: -6, right: -6, background: "#D64545", color: "#fff", fontSize: 10, fontWeight: 700, borderRadius: 100, width: 16, height: 16, display: "flex", alignItems: "center", justifyContent: "center" }}>12</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
              <div style={{ width: 30, height: 30, borderRadius: "50%", background: "#1B4DFF", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 12.5, fontWeight: 700 }}>IN</div>
              <span style={{ fontSize: 13.5, fontWeight: 600 }}>Investigator</span>
              <ChevronDown size={14} color="#6B7280" />
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 14, marginBottom: 20, flexWrap: "wrap" }}>
          <StatCard label="Total Transactions" value="24,583" delta="+12.6%" />
          <StatCard label="Flagged Transactions" value="312" delta="+18.3%" positiveIsBad />
          <StatCard label="High Risk" value="87" delta="+9.7%" positiveIsBad />
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
                  <span style={{ fontWeight: 600 }}>{((d.value / totalRisk) * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 16 }}>
          <div style={{ flex: 1.4, background: "#fff", borderRadius: 10, border: "1px solid #E7E9EE", padding: "16px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Recent Alerts</div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
              <thead><tr style={{ color: "#9CA3AF", textAlign: "left" }}><th style={{ paddingBottom: 8, fontWeight: 600 }}>Time</th><th style={{ paddingBottom: 8, fontWeight: 600 }}>Transaction ID</th><th style={{ paddingBottom: 8, fontWeight: 600 }}>Type</th><th style={{ paddingBottom: 8, fontWeight: 600 }}>Risk Score</th><th style={{ paddingBottom: 8, fontWeight: 600 }}>Status</th></tr></thead>
              <tbody>
                {RECENT_ALERTS.map((a) => (
                  <tr key={a.id} style={{ borderTop: "1px solid #F1F2F5" }}>
                    <td style={{ padding: "9px 0", color: "#6B7280" }}>{a.time}</td>
                    <td style={{ padding: "9px 0", fontWeight: 500 }}>{a.id}</td>
                    <td style={{ padding: "9px 0", color: "#6B7280" }}>{a.type}</td>
                    <td style={{ padding: "9px 0", fontWeight: 700, color: a.score >= 80 ? "#D64545" : "#B4791E" }}>{a.score}</td>
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

alert_detail_code = """import { ChevronRight, CheckCircle2, AlertTriangle, Flag, Eye } from "lucide-react";
import Sidebar from "../components/Sidebar";

const SHAP_FEATURES = [
  { label: "Amount deviates from profile", value: 0.42 }, { label: "Unusual beneficiary", value: 0.31 },
  { label: "High risk country", value: 0.28 }, { label: "New device", value: 0.21 },
  { label: "Velocity (many txns)", value: 0.18 }, { label: "Consistent login behavior", value: -0.15 },
];
const maxAbs = Math.max(...SHAP_FEATURES.map((f) => Math.abs(f.value)));

function Field({ label, value }) {
  return <div><div style={{ fontSize: 11.5, color: "#9CA3AF" }}>{label}</div><div style={{ fontSize: 13.5, fontWeight: 600, marginTop: 2 }}>{value}</div></div>;
}

export default function AlertDetail() {
  const score = 87;
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
            <h1 style={{ fontSize: 19, fontWeight: 700, margin: 0 }}>Alert ALRT-2025-00125</h1>
          </div>
          <select style={{ fontSize: 13, border: "1px solid #E1E4EA", borderRadius: 7, padding: "7px 12px", background: "#fff" }}>
            <option>New</option><option>In Review</option><option>Closed</option>
          </select>
        </div>
        <div style={{ display: "flex", gap: 16, marginBottom: 16, alignItems: "stretch" }}>
          <div style={{ flex: 1.6, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Transaction Details</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px 24px" }}>
              <Field label="Transaction ID" value="TXN-20250520-143528" /><Field label="Date & Time" value="2025-05-20 15:25:38" />
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
          <div style={{ flex: 1.6, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>Feature Contribution (SHAP Explanation)</div>
            <div style={{ fontSize: 11.5, color: "#9CA3AF", marginBottom: 16 }}>Positive values push the prediction toward fraud</div>
            {SHAP_FEATURES.map((f) => {
              const isPos = f.value > 0;
              const widthPct = (Math.abs(f.value) / maxAbs) * 45;
              return (
                <div key={f.label} style={{ display: "flex", alignItems: "center", marginBottom: 10, fontSize: 12.5 }}>
                  <div style={{ width: "42%", textAlign: "right", paddingRight: 10, color: "#4B5563" }}>{f.label}</div>
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

framl_graph_code = """import { useState } from "react";
import { ZoomIn, ZoomOut, Maximize2, User, Smartphone } from "lucide-react";
import Sidebar from "../components/Sidebar";

const NODES = [
  { id: "acc1", label: "Account\n1002345678", x: 110, y: 60, type: "account" }, { id: "acc2", label: "Account\n1003987654", x: 430, y: 60, type: "account" },
  { id: "device", label: "Device\nDEV-8F6A21C9", x: 270, y: 190, type: "device" }, { id: "acc3", label: "Account\n1005567890", x: 110, y: 320, type: "account" },
  { id: "ben", label: "Beneficiary\nJohn D.", x: 270, y: 320, type: "beneficiary" }, { id: "acc4", label: "Account\n1006677881", x: 430, y: 320, type: "account" },
];
const EDGES = [
  ["acc1", "device", "uses"], ["acc2", "device", "uses"], ["acc3", "device", "uses"], ["acc4", "device", "uses"], ["device", "ben", "pays"],
];
function nodeById(id) { return NODES.find((n) => n.id === id); }

export default function FramlGraph() {
  const [selected, setSelected] = useState("device");
  const sel = nodeById(selected);
  const colors = { account: "#1B4DFF", beneficiary: "#2FA36B", device: "#7C3AED" };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter','Segoe UI',-apple-system,sans-serif", color: "#111827" }}>
      <Sidebar activeKey="graph" />
      <main style={{ flex: 1, padding: "24px 28px" }}>
        <h1 style={{ fontSize: 19, fontWeight: 700, margin: "0 0 18px" }}>FRAML Graph — Device View</h1>
        <div style={{ display: "flex", gap: 16 }}>
          <div style={{ flex: 2, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "12px 16px", position: "relative" }}>
            <div style={{ position: "absolute", top: 14, right: 16, display: "flex", gap: 6, zIndex: 2 }}>
              {[ZoomIn, ZoomOut, Maximize2].map((Icon, i) => (
                <button key={i} style={{ width: 28, height: 28, border: "1px solid #E1E4EA", borderRadius: 6, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
                  <Icon size={14} color="#6B7280" />
                </button>
              ))}
            </div>
            <svg viewBox="0 0 540 400" style={{ width: "100%", height: 420 }}>
              {EDGES.map(([a, b, label], i) => {
                const na = nodeById(a), nb = nodeById(b);
                const mx = (na.x + nb.x) / 2, my = (na.y + nb.y) / 2;
                return (
                  <g key={i}>
                    <line x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} stroke="#D9DEE7" strokeWidth={1.5} />
                    <text x={mx} y={my - 6} fontSize="10" fill="#9CA3AF" textAnchor="middle">{label}</text>
                  </g>
                );
              })}
              {NODES.map((n) => (
                <g key={n.id} onClick={() => setSelected(n.id)} style={{ cursor: "pointer" }}>
                  <circle cx={n.x} cy={n.y} r={n.type === "device" ? 30 : 26} fill={colors[n.type]} opacity={selected === n.id ? 1 : 0.85} stroke={selected === n.id ? "#111827" : "none"} strokeWidth={2} />
                  <foreignObject x={n.x - 13} y={n.y - 12} width={26} height={26}>
                    {n.type === "device" ? <Smartphone size={20} color="#fff" /> : <User size={20} color="#fff" />}
                  </foreignObject>
                  {n.label.split("\\n").map((line, i) => (
                    <text key={i} x={n.x} y={n.y + 44 + i * 13} fontSize="11" fontWeight="600" fill="#374151" textAnchor="middle">{line}</text>
                  ))}
                </g>
              ))}
            </svg>
          </div>
          <div style={{ flex: 1, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Node Details</div>
            <div style={{ fontSize: 11.5, color: "#9CA3AF" }}>Selected Node</div>
            <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 14 }}>{sel.label.replace("\\n", ": ")}</div>
            {[["Type", sel.type[0].toUpperCase() + sel.type.slice(1)], ["Linked Accounts", "4"], ["Linked Beneficiaries", "1"], ["Total Transactions", "23"]].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, padding: "7px 0", borderTop: "1px solid #F1F2F5" }}>
                <span style={{ color: "#9CA3AF" }}>{k}</span><span style={{ fontWeight: 600 }}>{v}</span>
              </div>
            ))}
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, padding: "7px 0", borderTop: "1px solid #F1F2F5" }}>
              <span style={{ color: "#9CA3AF" }}>Risk Level</span>
              <span style={{ background: "#FFF4E0", color: "#B4791E", fontWeight: 700, fontSize: 11, padding: "2px 8px", borderRadius: 6 }}>Medium</span>
            </div>
            <div style={{ fontSize: 13, fontWeight: 700, margin: "18px 0 8px" }}>Legend</div>
            {[["Account", colors.account], ["Beneficiary", colors.beneficiary], ["Device", colors.device]].map(([label, c]) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#4B5563", marginBottom: 6 }}>
                <span style={{ width: 10, height: 10, borderRadius: "50%", background: c, display: "inline-block" }} />{label}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
"""

txn_scoring_code = """import { AlertTriangle } from "lucide-react";
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
"""

kafka_workflow_code = """import { useState } from "react";
import { CheckCircle2 } from "lucide-react";
import Sidebar from "../components/Sidebar";

export default function KafkaWorkflow() {
  const [tab, setTab] = useState("topic");
  const tabs = [
    { key: "producer", label: "Producer" }, { key: "topic", label: "Kafka Topic" }, { key: "consumer", label: "Consumer (Scoring Service)" },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter','Segoe UI',-apple-system,sans-serif", color: "#111827" }}>
      <Sidebar activeKey="transactions" />
      <main style={{ flex: 1, padding: "24px 28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
          <h1 style={{ fontSize: 19, fontWeight: 700, margin: 0 }}>Kafka Transaction Workflow Monitor</h1>
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, color: "#6B7280" }}>
            Auto Refresh
            <span style={{ width: 34, height: 18, background: "#1B4DFF", borderRadius: 100, position: "relative", display: "inline-block" }}>
              <span style={{ position: "absolute", top: 2, right: 2, width: 14, height: 14, borderRadius: "50%", background: "#fff" }} />
            </span>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
          {tabs.map((t) => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid #E1E4EA", cursor: "pointer", fontSize: 12.5, fontWeight: 600, background: tab === t.key ? "#1B4DFF" : "#fff", color: tab === t.key ? "#fff" : "#374151" }}>{t.label}</button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 16 }}>
          <div style={{ flex: 1, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Kafka Topic Details</div>
            {[
              ["Topic Name", "txn-events"], ["Partition", "0"], ["Replication Factor", "1"],
              ["Status", "Active"], ["Messages in Topic", "1,254"], ["Earliest Offset", "0"], ["Latest Offset", "1,254"],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, padding: "7px 0", borderTop: "1px solid #F1F2F5" }}>
                <span style={{ color: "#9CA3AF" }}>{k}</span>
                {k === "Status" ? (
                  <span style={{ display: "flex", alignItems: "center", gap: 5, color: "#2FA36B", fontWeight: 600 }}>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#2FA36B" }} />Active
                  </span>
                ) : <span style={{ fontWeight: 600 }}>{v}</span>}
              </div>
            ))}
          </div>
          <div style={{ flex: 1.4, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Recent Messages (From Topic)</div>
            <pre style={{ background: "#0B1526", color: "#9EE6C7", fontSize: 11.5, borderRadius: 8, padding: 14, overflowX: "auto", lineHeight: 1.6, margin: 0 }}>{`{
  "transaction_id": "TXN-20260814-000567",
  "timestamp": "2026-08-14T10:24:35Z",
  "from_account": "1002345678",
  "to_account": "2098765432",
  "amount": 5200.00,
  "currency": "USD",
  "channel": "Online Banking",
  "device_id": "DEV-8F6A21C9",
  "location": "Lagos, Nigeria"
}`}</pre>
          </div>
          <div style={{ flex: 1, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Consumer Status</div>
            {[["Consumer Group", "scoring-service"], ["Last Consumed Offset", "1,254"], ["Last Consumed Time", "2026-08-14 10:25:01"]].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, padding: "7px 0", borderTop: "1px solid #F1F2F5" }}>
                <span style={{ color: "#9CA3AF" }}>{k}</span><span style={{ fontWeight: 600 }}>{v}</span>
              </div>
            ))}
            <div style={{ display: "flex", alignItems: "center", gap: 8, background: "#EAF6EE", color: "#2C8A57", borderRadius: 8, padding: "10px 12px", fontSize: 12, fontWeight: 600, marginTop: 14 }}>
              <CheckCircle2 size={16} /> Message received and processed by scoring service successfully.
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
"""

with open(os.path.join(components_dir, "Sidebar.jsx"), "w", encoding="utf-8") as f: f.write(sidebar_code)
with open(os.path.join(pages_dir, "DashboardOverview.jsx"), "w", encoding="utf-8") as f: f.write(dashboard_code)
with open(os.path.join(pages_dir, "AlertDetail.jsx"), "w", encoding="utf-8") as f: f.write(alert_detail_code)
with open(os.path.join(pages_dir, "FramlGraph.jsx"), "w", encoding="utf-8") as f: f.write(framl_graph_code)
with open(os.path.join(pages_dir, "TransactionRiskScoring.jsx"), "w", encoding="utf-8") as f: f.write(txn_scoring_code)
with open(os.path.join(pages_dir, "KafkaWorkflow.jsx"), "w", encoding="utf-8") as f: f.write(kafka_workflow_code)

print("Files successfully generated.")
