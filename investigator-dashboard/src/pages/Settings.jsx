import React from "react";
import Sidebar from "../components/Sidebar";
import { User, Bell, Shield, Database, Key } from "lucide-react";

export default function Settings() {
  const tabs = [
    { id: "profile", label: "My Profile", icon: User },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "security", label: "Security", icon: Shield },
    { id: "api", label: "API Keys", icon: Key },
    { id: "integrations", label: "Integrations", icon: Database },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter', sans-serif", color: "#111827" }}>
      <Sidebar activeKey="settings" />
      <main style={{ flex: 1, padding: "24px 28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>System Settings</h1>
        </div>

        <div style={{ display: "flex", gap: 24 }}>
          <div style={{ width: 250, display: "flex", flexDirection: "column", gap: 8 }}>
            {tabs.map((tab) => (
              <div key={tab.id} style={{ 
                padding: "10px 16px", borderRadius: 8, display: "flex", alignItems: "center", gap: 12, cursor: "pointer",
                background: tab.id === "profile" ? "#fff" : "transparent",
                border: tab.id === "profile" ? "1px solid #E7E9EE" : "1px solid transparent",
                fontWeight: tab.id === "profile" ? 600 : 500,
                color: tab.id === "profile" ? "#111827" : "#6B7280"
              }}>
                <tab.icon size={18} color={tab.id === "profile" ? "#1B4DFF" : "#9CA3AF"} />
                {tab.label}
              </div>
            ))}
          </div>
          
          <div style={{ flex: 1, background: "#fff", borderRadius: 12, border: "1px solid #E7E9EE", padding: 32 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, margin: "0 0 24px 0", borderBottom: "1px solid #E7E9EE", paddingBottom: 16 }}>Profile Information</h2>
            
            <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 400 }}>
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#4B5563", marginBottom: 8 }}>Full Name</label>
                <input type="text" defaultValue="Investigator User" style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #D1D5DB", outline: "none", fontSize: 14 }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#4B5563", marginBottom: 8 }}>Email Address</label>
                <input type="email" defaultValue="investigator@bank.local" style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #D1D5DB", outline: "none", fontSize: 14 }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#4B5563", marginBottom: 8 }}>Role</label>
                <input type="text" defaultValue="Senior Fraud Analyst" disabled style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #E5E7EB", background: "#F9FAFB", outline: "none", fontSize: 14, color: "#6B7280" }} />
              </div>
              
              <button style={{ marginTop: 12, padding: "10px 16px", borderRadius: 8, border: "none", background: "#1B4DFF", color: "#fff", fontWeight: 600, cursor: "pointer", alignSelf: "flex-start" }}>
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
