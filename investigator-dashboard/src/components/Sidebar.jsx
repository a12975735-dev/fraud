import {
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
