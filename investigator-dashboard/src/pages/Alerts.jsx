import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import { AlertTriangle, Clock, CheckCircle } from "lucide-react";

export default function Alerts() {
  const storedCase = JSON.parse(localStorage.getItem('fraud-investigation-active-case') || 'null');
  const caseAlert = storedCase ? {
    id: storedCase.id,
    type: "Investigation Case Created",
    entity: `${storedCase.suspects || 0} suspect(s), ${storedCase.linkedEntities || 0} linked entit(ies)`,
    severity: "Medium",
    time: "Just now",
  } : null;
  const resolvedAlertIds = JSON.parse(localStorage.getItem('fraud-resolved-alert-ids') || '[]');
  const [mockAlerts, setMockAlerts] = useState([
    ...(caseAlert ? [caseAlert] : []),
    { id: "ALT-9001", type: "Velocity Anomaly", entity: "Account 2003456789", severity: "Critical", time: "10 mins ago" },
    { id: "ALT-9002", type: "Location Impossible", entity: "Card ending 3921", severity: "High", time: "45 mins ago" },
    { id: "ALT-9003", type: "Large Transfer", entity: "Account 1009876543", severity: "Medium", time: "2 hours ago" },
    { id: "ALT-9004", type: "Login Failed Attempts", entity: "User ID 502", severity: "Low", time: "5 hours ago" },
  ].filter((alert) => !resolvedAlertIds.includes(alert.id)));
  const storedResolvedAlerts = JSON.parse(localStorage.getItem('fraud-resolved-alerts') || '[]');
  const [resolvedAlerts, setResolvedAlerts] = useState(storedResolvedAlerts);

  const resolveAlert = (id) => {
    const alert = mockAlerts.find((item) => item.id === id);
    if (!alert) return;
    const resolvedAlert = { ...alert, time: 'Just now' };
    const nextResolvedAlerts = [...resolvedAlerts, resolvedAlert];
    setResolvedAlerts(nextResolvedAlerts);
    setMockAlerts((alerts) => alerts.filter((item) => item.id !== id));
    localStorage.setItem('fraud-resolved-alerts', JSON.stringify(nextResolvedAlerts));
    localStorage.setItem('fraud-resolved-alert-ids', JSON.stringify([...resolvedAlertIds, id]));
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter', sans-serif", color: "#111827" }}>
      <Sidebar activeKey="alerts" />
      <main style={{ flex: 1, padding: "24px 28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Active Alerts</h1>
        </div>

        <div style={{ display: "flex", gap: 16, flexDirection: "column" }}>
          {mockAlerts.map((a) => (
            <div key={a.id} style={{ background: "#fff", borderRadius: 12, border: "1px solid #E7E9EE", padding: "20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
                <div style={{ 
                  width: 48, height: 48, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                  background: a.severity === "Critical" ? "#FDECEC" : a.severity === "High" ? "#FFF4E0" : "#F3F4F6",
                  color: a.severity === "Critical" ? "#C13B3B" : a.severity === "High" ? "#B4791E" : "#6B7280"
                }}>
                  <AlertTriangle size={24} />
                </div>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>{a.type}</div>
                  <div style={{ fontSize: 14, color: "#6B7280", display: "flex", gap: 12, alignItems: "center" }}>
                    <span>{a.id}</span>
                    <span style={{ width: 4, height: 4, borderRadius: "50%", background: "#D1D5DB" }} />
                    <span style={{ fontWeight: 500, color: "#111827" }}>{a.entity}</span>
                  </div>
                </div>
              </div>
              
              <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#6B7280", fontSize: 13 }}>
                  <Clock size={16} /> {a.time}
                </div>
                <button onClick={() => resolveAlert(a.id)} style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid #E7E9EE", background: "#fff", cursor: "pointer", fontWeight: 600, fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
                  <CheckCircle size={16} color="#2FA36B" /> Resolve
                </button>
              </div>
            </div>
          ))}
          {mockAlerts.length === 0 && (
            <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #E7E9EE", padding: 24, color: "#6B7280", textAlign: "center" }}>
              No active alerts.
            </div>
          )}
          {resolvedAlerts.length > 0 && (
            <div style={{ marginTop: 20 }}>
              <h2 style={{ fontSize: 18, margin: "0 0 12px" }}>Resolved Alerts</h2>
              {resolvedAlerts.map((a) => (
                <div key={`resolved-${a.id}`} style={{ background: "#F8FAFC", borderRadius: 12, border: "1px solid #E7E9EE", padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", color: "#64748B" }}>
                  <div><strong>{a.type}</strong><div style={{ fontSize: 13, marginTop: 4 }}>{a.id} · {a.entity}</div></div>
                  <span style={{ color: "#2FA36B", fontSize: 13, fontWeight: 700 }}>RESOLVED</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
