import { useState } from "react";
import { ZoomIn, ZoomOut, Maximize2, User, Smartphone } from "lucide-react";
import Sidebar from "../components/Sidebar";

const NODES = [
  { id: "acc1", label: `Account\n1002345678`, x: 110, y: 60, type: "account" }, { id: "acc2", label: `Account\n1003987654`, x: 430, y: 60, type: "account" },
  { id: "device", label: `Device\nDEV-8F6A21C9`, x: 270, y: 190, type: "device" }, { id: "acc3", label: `Account\n1005567890`, x: 110, y: 320, type: "account" },
  { id: "ben", label: `Beneficiary\nJohn D.`, x: 270, y: 320, type: "beneficiary" }, { id: "acc4", label: `Account\n1006677881`, x: 430, y: 320, type: "account" },
];
const EDGES = [
  ["acc1", "device", "uses"], ["acc2", "device", "uses"], ["acc3", "device", "uses"], ["acc4", "device", "uses"], ["device", "ben", "pays"],
];

function buildGraphData() {
  const transactions = JSON.parse(localStorage.getItem("fraud-graph-transactions") || "[]");
  const dynamicNodes = [];
  const dynamicEdges = [];
  transactions.forEach((transaction, index) => {
    const offset = index * 55;
    const deviceId = `device-${transaction.deviceId}`;
    const sourceId = `source-${transaction.sourceAccount}`;
    const destinationId = `destination-${transaction.destinationAccount}`;
    dynamicNodes.push(
      { id: sourceId, label: `Account\n${transaction.sourceAccount}`, x: 80 + (offset % 380), y: 45 + (index % 3) * 105, type: "account" },
      { id: deviceId, label: `Device\n${transaction.deviceId}`, x: 270, y: 195, type: "device" },
      { id: destinationId, label: `Account\n${transaction.destinationAccount}`, x: 460 - (offset % 120), y: 330 - (index % 3) * 75, type: "account" },
    );
    dynamicEdges.push([sourceId, deviceId, "uses"], [deviceId, destinationId, "transfers"]);
  });
  return { nodes: [...NODES, ...dynamicNodes], edges: [...EDGES, ...dynamicEdges] };
}

export default function FramlGraph() {
  const graph = buildGraphData();
  const [selected, setSelected] = useState("device");
  const [zoom, setZoom] = useState(1);
  const [expanded, setExpanded] = useState(false);
  const findNode = (id) => graph.nodes.find((node) => node.id === id);
  const sel = findNode(selected) || graph.nodes[0];
  const colors = { account: "#1B4DFF", beneficiary: "#2FA36B", device: "#7C3AED" };
  const linkedNodes = graph.edges.filter(([from, to]) => from === selected || to === selected);
  const linkedAccounts = linkedNodes.filter(([from, to]) => findNode(from).type === "account" || findNode(to).type === "account").length;
  const linkedBeneficiaries = linkedNodes.filter(([from, to]) => findNode(from).type === "beneficiary" || findNode(to).type === "beneficiary").length;
  const nodeStats = [
    ["Type", sel.type[0].toUpperCase() + sel.type.slice(1)],
    ["Linked Accounts", String(linkedAccounts)],
    ["Linked Beneficiaries", String(linkedBeneficiaries)],
    ["Total Transactions", String(linkedNodes.length * 5)],
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter','Segoe UI',-apple-system,sans-serif", color: "#111827" }}>
      <Sidebar activeKey="graph" />
      <main className="framl-main" style={{ flex: 1, padding: "24px 28px" }}>
        <h1 style={{ fontSize: 19, fontWeight: 700, margin: "0 0 18px" }}>FRAML Graph — Device View</h1>
        <div className={`framl-layout${expanded ? " framl-layout-expanded" : ""}`}>
          <div className="framl-graph-panel" style={{ flex: 2, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "12px 16px", position: "relative" }}>
            <div style={{ position: "absolute", top: 14, right: 16, display: "flex", gap: 6, zIndex: 2 }}>
              {[ZoomIn, ZoomOut, Maximize2].map((Icon, i) => (
                <button key={i} onClick={() => i === 0 ? setZoom((value) => Math.min(value + 0.15, 1.8)) : i === 1 ? setZoom((value) => Math.max(value - 0.15, 0.7)) : setExpanded((value) => !value)} title={i === 0 ? "Zoom in" : i === 1 ? "Zoom out" : "Expand graph"} style={{ width: 28, height: 28, border: "1px solid #E1E4EA", borderRadius: 6, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
                  <Icon size={14} color="#6B7280" />
                </button>
              ))}
            </div>
            <svg className="framl-graph" viewBox="0 0 540 400" preserveAspectRatio="xMidYMid meet" style={{ width: "100%", height: expanded ? 560 : "auto" }}>
              <g transform={`translate(270 200) scale(${zoom}) translate(-270 -200)`}>
              {graph.edges.map(([a, b, label], i) => {
                const na = findNode(a), nb = findNode(b);
                const mx = (na.x + nb.x) / 2, my = (na.y + nb.y) / 2;
                return (
                  <g key={i}>
                    <line x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} stroke="#D9DEE7" strokeWidth={1.5} />
                    <text x={mx} y={my - 6} fontSize="10" fill="#9CA3AF" textAnchor="middle">{label}</text>
                  </g>
                );
              })}
              {graph.nodes.map((n) => (
                <g key={n.id} onClick={() => setSelected(n.id)} style={{ cursor: "pointer" }}>
                  <circle cx={n.x} cy={n.y} r={n.type === "device" ? 30 : 26} fill={colors[n.type]} opacity={selected === n.id ? 1 : 0.85} stroke={selected === n.id ? "#111827" : "none"} strokeWidth={2} />
                  <foreignObject x={n.x - 13} y={n.y - 12} width={26} height={26}>
                    {n.type === "device" ? <Smartphone size={20} color="#fff" /> : <User size={20} color="#fff" />}
                  </foreignObject>
                  {n.label.split("\n").map((line, i) => (
                    <text key={i} x={n.x} y={n.y + 44 + i * 13} fontSize="11" fontWeight="600" fill="#374151" textAnchor="middle">{line}</text>
                  ))}
                </g>
              ))}
              </g>
            </svg>
          </div>
          <div className="framl-details-panel" style={{ flex: 1, background: "#fff", border: "1px solid #E7E9EE", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Node Details</div>
            <div style={{ fontSize: 11.5, color: "#9CA3AF" }}>Selected Node</div>
            <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 14 }}>{sel.label.replace("\n", ": ")}</div>
              {nodeStats.map(([k, v]) => (
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
