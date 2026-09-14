import { useState, useEffect } from "react";
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
