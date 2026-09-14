import React from "react";
import Sidebar from "../components/Sidebar";
import { Download, FileText, BarChart2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function Reports() {
  const data = [
    { name: "Jan", fraud: 40, normal: 2400 },
    { name: "Feb", fraud: 30, normal: 1398 },
    { name: "Mar", fraud: 20, normal: 9800 },
    { name: "Apr", fraud: 27, normal: 3908 },
    { name: "May", fraud: 18, normal: 4800 },
    { name: "Jun", fraud: 23, normal: 3800 },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter', sans-serif", color: "#111827" }}>
      <Sidebar activeKey="reports" />
      <main style={{ flex: 1, padding: "24px 28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Generated Reports</h1>
          <button style={{ padding: "10px 18px", borderRadius: 8, border: "none", background: "#1B4DFF", color: "#fff", display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontWeight: 600 }}>
            <FileText size={16} /> New Report
          </button>
        </div>

        <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
          <div style={{ flex: 1, background: "#fff", padding: 24, borderRadius: 12, border: "1px solid #E7E9EE" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
              <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>Fraud vs Normal Transactions (YTD)</h2>
              <button style={{ background: "transparent", border: "none", color: "#6B7280", cursor: "pointer" }}><Download size={18} /></button>
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E7E9EE" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#6B7280" }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#6B7280" }} />
                <Tooltip />
                <Bar dataKey="normal" fill="#1B4DFF" radius={[4, 4, 0, 0]} />
                <Bar dataKey="fraud" fill="#D64545" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Available Templates</h3>
        <div style={{ display: "flex", gap: 16 }}>
          {["Monthly Risk Summary", "Compliance Audit", "Analyst Performance", "Geographic Anomaly Report"].map((template, idx) => (
            <div key={idx} style={{ flex: 1, background: "#fff", padding: 20, borderRadius: 12, border: "1px solid #E7E9EE", display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 12 }}>
              <div style={{ background: "#F3F4F6", padding: 10, borderRadius: 8, color: "#4B5563" }}><BarChart2 size={20} /></div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{template}</div>
              <button style={{ marginTop: "auto", padding: "6px 12px", borderRadius: 6, border: "1px solid #E7E9EE", background: "#fff", fontSize: 12, fontWeight: 500, cursor: "pointer" }}>Generate</button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
