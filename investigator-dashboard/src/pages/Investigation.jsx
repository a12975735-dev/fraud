import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import { Search, FolderOpen, UserPlus, Link as LinkIcon } from "lucide-react";

export default function Investigation() {
  const savedCase = JSON.parse(localStorage.getItem('fraud-investigation-active-case') || 'null');
  const [caseStarted, setCaseStarted] = useState(Boolean(savedCase));
  const [caseMessage, setCaseMessage] = useState(savedCase?.transactionId ? `Transaction ${savedCase.transactionId} added for investigation.` : '');
  const [caseId, setCaseId] = useState(savedCase?.id || '');
  const [suspectCount, setSuspectCount] = useState(savedCase?.suspects || 0);
  const [entityCount, setEntityCount] = useState(savedCase?.linkedEntities || 0);

  const startCase = () => {
    const newCaseId = `CASE-${Date.now().toString().slice(-6)}`;
    setCaseId(newCaseId);
    setCaseStarted(true);
    setSuspectCount(0);
    setEntityCount(0);
    setCaseMessage('Case created. Add suspects or link related entities.');
    localStorage.setItem('fraud-investigation-active-case', JSON.stringify({
      id: newCaseId,
      suspects: 0,
      linkedEntities: 0,
      createdAt: new Date().toISOString(),
    }));
  };

  const handleCaseAction = (action) => {
    if (!caseStarted) {
      startCase();
    }
    if (action === 'Suspect') {
      setSuspectCount((count) => count + 1);
      setEntityCount((count) => count + 1);
      setCaseMessage(`Suspect added to ${caseId || 'the new case'}.`);
      const storedCase = JSON.parse(localStorage.getItem('fraud-investigation-active-case') || '{}');
      localStorage.setItem('fraud-investigation-active-case', JSON.stringify({
        ...storedCase,
        suspects: (storedCase.suspects || 0) + 1,
        linkedEntities: (storedCase.linkedEntities || 0) + 1,
      }));
    } else {
      setEntityCount((count) => count + 1);
      setCaseMessage(`Entity link added to ${caseId || 'the new case'}.`);
      const storedCase = JSON.parse(localStorage.getItem('fraud-investigation-active-case') || '{}');
      localStorage.setItem('fraud-investigation-active-case', JSON.stringify({
        ...storedCase,
        linkedEntities: (storedCase.linkedEntities || 0) + 1,
      }));
    }
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter', sans-serif", color: "#111827" }}>
      <Sidebar activeKey="investigation" />
      <main style={{ flex: 1, padding: "24px 28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Investigation Workspace</h1>
          <button onClick={startCase} style={{ padding: "10px 18px", borderRadius: 8, border: "none", background: "#1B4DFF", color: "#fff", display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontWeight: 600 }}>
            <FolderOpen size={16} /> New Case
          </button>
        </div>

        <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #E7E9EE", padding: 32, minHeight: 400 }}>
          {!caseStarted ? (
            <div style={{ textAlign: "center", minHeight: 336, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
              <Search size={48} color="#9CA3AF" style={{ marginBottom: 16 }} />
              <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8, color: "#111827" }}>No Active Investigations</h2>
              <p style={{ color: "#6B7280", maxWidth: 400, lineHeight: 1.5, marginBottom: 24 }}>
                Start a new investigation to group related alerts, transactions, and entities into a single case file.
              </p>
              <div style={{ display: "flex", gap: 12 }}>
                <button onClick={() => handleCaseAction('Suspect')} style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid #E7E9EE", background: "#fff", display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontWeight: 500 }}>
                  <UserPlus size={16} /> Add Suspect
                </button>
                <button onClick={() => handleCaseAction('Entity link')} style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid #E7E9EE", background: "#fff", display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontWeight: 500 }}>
                  <LinkIcon size={16} /> Link Entities
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "1px solid #E7E9EE", paddingBottom: 20, marginBottom: 24 }}>
                <div>
                  <div style={{ color: "#6B7280", fontSize: 13, marginBottom: 6 }}>ACTIVE INVESTIGATION</div>
                  <h2 style={{ fontSize: 24, margin: 0, color: "#111827" }}>{caseId}</h2>
                  <p style={{ color: "#6B7280", margin: "8px 0 0" }}>{caseMessage}</p>
                </div>
                <span style={{ background: "#EAF6EE", color: "#2C8A57", borderRadius: 999, padding: "6px 12px", fontSize: 12, fontWeight: 700 }}>OPEN</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
                {[
                  ['Related alerts', 0],
                  ['Suspects', suspectCount],
                  ['Linked entities', entityCount],
                ].map(([label, count]) => (
                  <div key={label} style={{ border: "1px solid #E7E9EE", borderRadius: 8, padding: 18 }}>
                    <div style={{ color: "#6B7280", fontSize: 13 }}>{label}</div>
                    <strong style={{ display: "block", fontSize: 24, marginTop: 8 }}>{count}</strong>
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", gap: 12 }}>
                <button onClick={() => handleCaseAction('Suspect')} style={{ padding: "9px 16px", borderRadius: 8, border: "1px solid #E7E9EE", background: "#fff", display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontWeight: 600 }}><UserPlus size={16} /> Add Suspect</button>
                <button onClick={() => handleCaseAction('Entity link')} style={{ padding: "9px 16px", borderRadius: 8, border: "1px solid #E7E9EE", background: "#fff", display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontWeight: 600 }}><LinkIcon size={16} /> Link Entities</button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
