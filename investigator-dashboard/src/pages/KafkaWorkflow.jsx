import { useState } from "react";
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
