import React from "react";
import Sidebar from "../components/Sidebar";
import { Fingerprint, Activity } from "lucide-react";

export default function BiometricMonitor() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter', sans-serif", color: "#111827" }}>
      <Sidebar activeKey="biometric" />
      <main style={{ flex: 1, padding: "24px 28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Biometric & Behavioral Monitor</h1>
        </div>

        <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
          <div style={{ flex: 1, background: "#fff", padding: 24, borderRadius: 12, border: "1px solid #E7E9EE" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
              <div style={{ background: "#EAF6EE", padding: 10, borderRadius: 8, color: "#2C8A57" }}><Fingerprint size={24} /></div>
              <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Device Fingerprinting</h2>
            </div>
            <p style={{ color: "#6B7280", fontSize: 14, lineHeight: 1.5 }}>Analysis of device hardware anomalies, IP reputation, and browser characteristics.</p>
            <div style={{ marginTop: 24, fontSize: 32, fontWeight: 700, color: "#111827" }}>98.2% <span style={{ fontSize: 14, color: "#2FA36B", fontWeight: 500 }}>Trusted Devices</span></div>
          </div>
          
          <div style={{ flex: 1, background: "#fff", padding: 24, borderRadius: 12, border: "1px solid #E7E9EE" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
              <div style={{ background: "#FDECEC", padding: 10, borderRadius: 8, color: "#C13B3B" }}><Activity size={24} /></div>
              <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Behavioral Profiling</h2>
            </div>
            <p style={{ color: "#6B7280", fontSize: 14, lineHeight: 1.5 }}>Keystroke dynamics, mouse movement anomalies, and navigation velocity.</p>
            <div style={{ marginTop: 24, fontSize: 32, fontWeight: 700, color: "#111827" }}>124 <span style={{ fontSize: 14, color: "#D64545", fontWeight: 500 }}>Anomalous Sessions (24h)</span></div>
          </div>
        </div>
      </main>
    </div>
  );
}
