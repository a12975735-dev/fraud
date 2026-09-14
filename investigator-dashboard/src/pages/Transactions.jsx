import React, { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import TransactionForm from "../components/TransactionForm";
import { useNavigate } from "react-router-dom";
import { Search, Filter, Download } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const GATEWAY_URL = "http://127.0.0.1:8081";

function mapTransaction(transaction) {
  const risk = transaction.riskLevel ? transaction.riskLevel[0].toUpperCase() + transaction.riskLevel.slice(1) : "Unknown";
  const status = transaction.status === "COMPLETED" && risk === "High" ? "Flagged" : transaction.status[0] + transaction.status.slice(1).toLowerCase();
  return {
    ...transaction,
    id: transaction.transactionId,
    amount: `$${Number(transaction.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
    date: new Date(transaction.timestamp).toLocaleString(),
    status,
    risk,
  };
}

export default function Transactions() {
  const navigate = useNavigate();
  const { token, isDemoMode } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [showFlaggedOnly, setShowFlaggedOnly] = useState(false);
  const [createdTransactions, setCreatedTransactions] = useState([]);
  const mockTransactions = [
    { id: "TXN-100928", amount: "$1,250.00", date: "2023-10-25 14:32", status: "Completed", risk: "Low" },
    { id: "TXN-100929", amount: "$8,400.00", date: "2023-10-25 15:10", status: "Flagged", risk: "High" },
    { id: "TXN-100930", amount: "$125.50", date: "2023-10-25 16:05", status: "Completed", risk: "Low" },
    { id: "TXN-100931", amount: "$3,200.00", date: "2023-10-25 16:45", status: "Pending", risk: "Medium" },
    { id: "TXN-100932", amount: "$50.00", date: "2023-10-25 17:22", status: "Completed", risk: "Low" },
  ];
  const [liveTransactions, setLiveTransactions] = useState([]);

  useEffect(() => {
    if (isDemoMode || !token) {
      return undefined;
    }

    const loadTransactions = async () => {
      try {
        const response = await fetch(`${GATEWAY_URL}/api/transactions?page=0&size=100`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error(`Gateway returned HTTP ${response.status}`);
        const data = await response.json();
        setLiveTransactions((data.content || []).map(mapTransaction));
      } catch (error) {
        console.error('Unable to load transactions from the database:', error);
      }
    };

    loadTransactions();
    const interval = setInterval(loadTransactions, 3000);
    return () => clearInterval(interval);
  }, [isDemoMode, token]);

  const transactions = isDemoMode ? [...createdTransactions, ...mockTransactions] : liveTransactions;

  const query = searchTerm.trim().toLowerCase();
  const visibleTransactions = transactions.filter((transaction) => {
    const matchesSearch = !query || Object.values(transaction).some((value) => String(value).toLowerCase().includes(query));
    const matchesFilter = !showFlaggedOnly || transaction.status === 'Flagged';
    return matchesSearch && matchesFilter;
  });

  const exportTransactions = () => {
    const header = 'Transaction ID,Amount,Date & Time,Status,Risk Level';
    const rows = visibleTransactions.map((transaction) => [transaction.id, transaction.amount, transaction.date, transaction.status, transaction.risk].join(','));
    const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'fraud-transactions.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const addTransaction = (transaction) => {
    const graphTransaction = {
      transactionId: transaction.transactionId,
      deviceId: `DEV-${transaction.transactionId.slice(-6)}`,
      sourceAccount: `ACC-${transaction.transactionId.slice(-8)}`,
      destinationAccount: `DEST-${transaction.transactionId.slice(-6)}`,
      amount: transaction.amount,
    };
    const graphTransactions = JSON.parse(localStorage.getItem('fraud-graph-transactions') || '[]');
    localStorage.setItem('fraud-graph-transactions', JSON.stringify([
      ...graphTransactions.filter((item) => item.transactionId !== graphTransaction.transactionId),
      graphTransaction,
    ]));
    setCreatedTransactions((items) => [
      {
        id: transaction.transactionId,
        amount: `$${Number(transaction.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
        date: new Date(transaction.timestamp).toLocaleString(),
        status: transaction.status === 'FLAGGED' ? 'Flagged' : transaction.status === 'PENDING' ? 'Pending' : 'Completed',
        risk: transaction.riskLevel ? transaction.riskLevel[0].toUpperCase() + transaction.riskLevel.slice(1) : 'Unknown',
      },
      ...items,
    ]);
  };

  const investigateTransaction = (transaction) => {
    const graphTransactions = JSON.parse(localStorage.getItem('fraud-graph-transactions') || '[]');
    if (!graphTransactions.some((item) => item.transactionId === transaction.id)) {
      localStorage.setItem('fraud-graph-transactions', JSON.stringify([...graphTransactions, {
        transactionId: transaction.id,
        deviceId: `DEV-${transaction.id.slice(-6)}`,
        sourceAccount: `ACC-${transaction.id.slice(-8)}`,
        destinationAccount: `DEST-${transaction.id.slice(-6)}`,
        amount: transaction.amount,
      }]));
    }
    const caseId = `CASE-${transaction.id.replace(/[^A-Za-z0-9]/g, '').slice(-8)}`;
    localStorage.setItem('fraud-investigation-active-case', JSON.stringify({
      id: caseId,
      transactionId: transaction.id,
      suspects: 0,
      linkedEntities: 1,
      createdAt: new Date().toISOString(),
    }));
    navigate('/investigation');
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F5F6F8", fontFamily: "'Inter', sans-serif", color: "#111827" }}>
      <Sidebar activeKey="transactions" />
      <main style={{ flex: 1, padding: "24px 28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Transactions</h1>
          <div style={{ display: "flex", gap: 12 }}>
            <button onClick={() => setShowFlaggedOnly((value) => !value)} style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid #E7E9EE", background: showFlaggedOnly ? "#EEF2FF" : "#fff", display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontWeight: 500 }}>
              <Filter size={16} /> {showFlaggedOnly ? 'Showing Flagged' : 'Filter'}
            </button>
            <button onClick={exportTransactions} style={{ padding: "8px 16px", borderRadius: 8, border: "none", background: "#1B4DFF", color: "#fff", display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontWeight: 500 }}>
              <Download size={16} /> Export
            </button>
          </div>
        </div>

        <TransactionForm onTransactionSubmitted={addTransaction} />

        <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #E7E9EE", overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid #E7E9EE", display: "flex", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, background: "#F9FAFB", border: "1px solid #E7E9EE", borderRadius: 8, padding: "8px 12px", flex: 1 }}>
              <Search size={18} color="#6B7280" />
              <input value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} type="text" placeholder="Search transactions by ID, amount, or date..." style={{ border: "none", background: "transparent", outline: "none", width: "100%", fontSize: 14 }} />
            </div>
          </div>
          
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{ background: "#F9FAFB", color: "#6B7280", textAlign: "left", fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>
                <th style={{ padding: "12px 20px", fontWeight: 600 }}>Transaction ID</th>
                <th style={{ padding: "12px 20px", fontWeight: 600 }}>Amount</th>
                <th style={{ padding: "12px 20px", fontWeight: 600 }}>Date & Time</th>
                <th style={{ padding: "12px 20px", fontWeight: 600 }}>Status</th>
                <th style={{ padding: "12px 20px", fontWeight: 600 }}>Risk Level</th>
                <th style={{ padding: "12px 20px", fontWeight: 600 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {visibleTransactions.map((t) => (
                <tr key={t.id} style={{ borderTop: "1px solid #E7E9EE" }}>
                  <td style={{ padding: "16px 20px", fontWeight: 500, color: "#1B4DFF" }}>{t.id}</td>
                  <td style={{ padding: "16px 20px", fontWeight: 600 }}>{t.amount}</td>
                  <td style={{ padding: "16px 20px", color: "#6B7280" }}>{t.date}</td>
                  <td style={{ padding: "16px 20px" }}>
                    <span style={{ 
                      padding: "4px 10px", borderRadius: 100, fontSize: 12, fontWeight: 600,
                      background: t.status === "Completed" ? "#EAF6EE" : t.status === "Flagged" ? "#FDECEC" : "#FFF4E0",
                      color: t.status === "Completed" ? "#2C8A57" : t.status === "Flagged" ? "#C13B3B" : "#B4791E"
                    }}>
                      {t.status}
                    </span>
                  </td>
                  <td style={{ padding: "16px 20px" }}>
                    <span style={{ 
                      padding: "4px 10px", borderRadius: 100, fontSize: 12, fontWeight: 600,
                      background: t.risk === "Low" ? "#EAF6EE" : t.risk === "High" ? "#FDECEC" : "#FFF4E0",
                      color: t.risk === "Low" ? "#2C8A57" : t.risk === "High" ? "#C13B3B" : "#B4791E"
                    }}>
                      {t.risk}
                    </span>
                  </td>
                  <td style={{ padding: "16px 20px" }}>
                    <button onClick={() => investigateTransaction(t)} style={{ border: "1px solid #1B4DFF", borderRadius: 6, padding: "6px 10px", background: "#fff", color: "#1B4DFF", cursor: "pointer", fontWeight: 600, fontSize: 12 }}>
                      Investigate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
