"""Fraud-ring detection from the raw PaySim transaction network.

This module demonstrates fraud-ring detection using classical graph analysis
(connected components) as a lightweight, interpretable proxy for the Graph
Neural Network approach discussed in the literature review. A full GNN
implementation (e.g. GraphSAGE or GAT) would learn richer relational patterns
beyond simple connectivity, but requires substantially more training data and
time than available in this project's scope; this demonstrates the same
underlying concept — that fraud often occurs in coordinated clusters rather
than isolated transactions.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as functional
from torch import nn
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv

BASE_DIR = Path(__file__).resolve().parents[1]
REQUESTED_RAW_PATH = BASE_DIR / "data" / "PS_20174392719_1491204439457_log.csv"
FALLBACK_RAW_PATH = BASE_DIR / "PS_20174392719_1491204439457_log.csv"
OUTPUT_PATH = BASE_DIR / "outputs" / "fraud_ring_graph.png"


def raw_data_path():
    """Prefer the documented data/ location; support the existing project root file."""
    if REQUESTED_RAW_PATH.exists():
        return REQUESTED_RAW_PATH
    if FALLBACK_RAW_PATH.exists():
        print(f"Raw CSV not found at {REQUESTED_RAW_PATH}; using {FALLBACK_RAW_PATH}.")
        return FALLBACK_RAW_PATH
    raise FileNotFoundError(f"Raw PaySim CSV not found at {REQUESTED_RAW_PATH} or {FALLBACK_RAW_PATH}.")


def load_fraud_transactions(path):
    """Read only graph-relevant raw columns, then retain fraudulent transactions."""
    columns = ["nameOrig", "nameDest", "amount", "isFraud"]
    raw = pd.read_csv(path, usecols=columns)
    return raw.loc[raw["isFraud"] == 1, ["nameOrig", "nameDest", "amount"]].copy()


def build_fraud_graph(fraud_transactions):
    """Build a directed multigraph: every edge is one fraudulent transaction."""
    graph = nx.MultiDiGraph()
    for row in fraud_transactions.itertuples(index=False):
        graph.add_edge(row.nameOrig, row.nameDest, amount=float(row.amount))
    return graph


class FraudGraphSAGE(nn.Module):
    """Minimal two-layer GraphSAGE encoder with an activity reconstruction head."""

    def __init__(self, input_channels: int, hidden_channels: int = 16, embedding_channels: int = 8):
        super().__init__()
        self.layer_one = SAGEConv(input_channels, hidden_channels)
        self.layer_two = SAGEConv(hidden_channels, embedding_channels)
        self.activity_head = nn.Linear(embedding_channels, 1)

    def forward(self, node_features: torch.Tensor, edge_index: torch.Tensor):
        hidden = functional.relu(self.layer_one(node_features, edge_index))
        embeddings = self.layer_two(hidden, edge_index)
        activity_prediction = self.activity_head(embeddings).squeeze(-1)
        return embeddings, activity_prediction


def compute_gnn_node_embeddings(graph: nx.MultiDiGraph, epochs: int = 100) -> dict:
    """Train GraphSAGE to reconstruct node activity and return learned embeddings.

    This graph deliberately contains only known-fraud transactions, so it has no
    negative labels from which to learn a fraud probability. The auxiliary target
    is normalized log transaction activity; this creates non-trivial gradients
    while the returned embeddings represent graph structure and account activity.
    """
    if graph.number_of_nodes() == 0:
        return {}

    undirected = nx.Graph(graph)
    pagerank = nx.pagerank(undirected) if len(undirected) > 0 else {}
    centrality = nx.degree_centrality(undirected) if len(undirected) > 0 else {}

    nodes = list(graph.nodes())
    node_to_index = {node: index for index, node in enumerate(nodes)}
    incoming_amount = {node: 0.0 for node in nodes}
    outgoing_amount = {node: 0.0 for node in nodes}
    edges = []
    for source, destination, edge_data in graph.edges(data=True):
        amount = float(edge_data.get("amount", 0.0))
        outgoing_amount[source] += amount
        incoming_amount[destination] += amount
        # Make the message-passing graph bidirectional while retaining the same accounts/transfers.
        edges.extend([(node_to_index[source], node_to_index[destination]),
                      (node_to_index[destination], node_to_index[source])])

    activity = np.array([incoming_amount[node] + outgoing_amount[node] for node in nodes], dtype=np.float32)
    activity_log = np.log1p(activity)
    activity_scale = max(float(activity_log.max()), 1.0)
    targets = torch.tensor(activity_log / activity_scale, dtype=torch.float32)
    features = torch.tensor([
        [
            float(activity_log[index] / activity_scale),
            float(graph.in_degree(node)),
            float(graph.out_degree(node)),
            float(pagerank.get(node, 0.0)),
            float(centrality.get(node, 0.0)),
        ]
        for index, node in enumerate(nodes)
    ], dtype=torch.float32)
    # Standardize degree/centrality columns without discarding the activity target.
    features[:, 1:] = (features[:, 1:] - features[:, 1:].mean(dim=0)) / features[:, 1:].std(dim=0).clamp_min(1e-6)
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    data = Data(x=features, edge_index=edge_index, y=targets)

    torch.manual_seed(42)
    model = FraudGraphSAGE(input_channels=data.num_node_features)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=1e-4)
    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        _, prediction = model(data.x, data.edge_index)
        loss = functional.mse_loss(prediction, data.y)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        learned_embeddings, activity_prediction = model(data.x, data.edge_index)

    return {
        node: {
            "gnn_embedding": [round(float(value), 6) for value in learned_embeddings[index].tolist()],
            "gnn_activity_score": round(float(activity_prediction[index].clamp(0, 1)), 6),
            "pagerank": round(float(pagerank.get(node, 0.0)), 6),
            "degree_centrality": round(float(centrality.get(node, 0.0)), 6),
        }
        for index, node in enumerate(nodes)
    }



def draw_largest_ring(graph, accounts):
    """Save a labelled graph of the largest component with >=3 accounts."""
    ring = graph.subgraph(accounts).copy()

    # Aggregate parallel transfers only for drawing so labels remain readable;
    # the MultiDiGraph above retains each individual fraudulent transaction.
    plot_graph = nx.DiGraph()
    for source, destination, data in ring.edges(data=True):
        amount = data["amount"]
        if plot_graph.has_edge(source, destination):
            plot_graph[source][destination]["amount"] += amount
        else:
            plot_graph.add_edge(source, destination, amount=amount)

    figure_size = max(10, min(24, 0.45 * len(accounts)))
    plt.figure(figsize=(figure_size, figure_size * 0.75))
    positions = nx.spring_layout(plot_graph, seed=42, k=1.5 / max(len(accounts), 1) ** 0.5)
    nx.draw_networkx_nodes(plot_graph, positions, node_color="#d62728", node_size=700, alpha=0.9)
    nx.draw_networkx_edges(plot_graph, positions, edge_color="#555555", arrows=True, arrowsize=16)
    nx.draw_networkx_labels(plot_graph, positions, font_size=6, font_color="black")
    edge_labels = {(source, destination): f"${data['amount']:,.0f}" for source, destination, data in plot_graph.edges(data=True)}
    nx.draw_networkx_edge_labels(plot_graph, positions, edge_labels=edge_labels, font_size=6, rotate=False)
    plt.title(f"Largest suspected fraud ring ({len(accounts)} accounts)")
    plt.axis("off")
    plt.tight_layout()
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=180, bbox_inches="tight")
    plt.close()


def find_fraud_rings(graph, max_length=8):
    """Detect circular fraud rings using SCC pre-filtering and simple_cycles."""
    rings = []
    # 1. Strongly Connected Components (must be >= 2 nodes to contain a cycle)
    sccs = [scc for scc in nx.strongly_connected_components(graph) if len(scc) >= 2]
    
    # 2. Extract cycles within each SCC
    for scc in sccs:
        subgraph = graph.subgraph(scc)
        try:
            # simple_cycles supports length_bound in NetworkX >= 3.0
            cycles = list(nx.simple_cycles(subgraph, length_bound=max_length))
        except TypeError:
            # Fallback if length_bound is not supported
            cycles = [c for c in nx.simple_cycles(subgraph) if len(c) <= max_length]
            
        for cycle in cycles:
            if len(cycle) >= 3:
                # Store as frozenset to easily deduplicate rings 
                rings.append(frozenset(cycle))
                
    # Deduplicate
    unique_rings = list(set(rings))
    return sorted([set(r) for r in unique_rings], key=len, reverse=True)


def main():
    path = raw_data_path()
    print("Loading raw PaySim transactions...")
    fraud_transactions = load_fraud_transactions(path)
    print(f"Fraudulent transactions: {len(fraud_transactions)}")

    graph = build_fraud_graph(fraud_transactions)
    embeddings = compute_gnn_node_embeddings(graph)

    suspected_rings = find_fraud_rings(graph, max_length=8)

    print("\n--- Fraud-ring detection summary ---")
    print(f"Total fraud accounts: {graph.number_of_nodes()}")
    print(f"Computed GraphSAGE embeddings for: {len(embeddings)} account nodes")
    for account, embedding in list(embeddings.items())[:3]:
        print(f"  {account}: activity={embedding['gnn_activity_score']}, embedding={embedding['gnn_embedding']}")
    print(f"Number of connected components: {len(components)}")

    print(f"Largest 5 component sizes: {[len(component) for component in components[:5]]}")
    print(f"Potential fraud rings (3+ accounts): {len(suspected_rings)}")

    if not suspected_rings:
        print("No connected component contains three or more accounts; no fraud-ring graph was created.")
        return

    largest_ring = suspected_rings[0]
    print(f"\nLargest suspected fraud ring ({len(largest_ring)} accounts):")
    print(", ".join(sorted(largest_ring)))
    draw_largest_ring(graph, largest_ring)
    print(f"\nSaved graph image: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
