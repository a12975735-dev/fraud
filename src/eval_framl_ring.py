import os
import sys
import pandas as pd
import networkx as nx

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fraud_ring_detection import build_fraud_graph, compute_gnn_node_embeddings, find_fraud_rings

def main():
    print("Testing FRAML Graph Module with advanced network...")
    
    # 1. Create planted rings
    ring1 = [
        {"nameOrig": "R1_A", "nameDest": "R1_B", "amount": 1000.0, "isFraud": 1},
        {"nameOrig": "R1_B", "nameDest": "R1_C", "amount": 950.0,  "isFraud": 1},
        {"nameOrig": "R1_C", "nameDest": "R1_A", "amount": 900.0,  "isFraud": 1},
    ]
    ring2 = [
        {"nameOrig": "R2_A", "nameDest": "R2_B", "amount": 2000.0, "isFraud": 1},
        {"nameOrig": "R2_B", "nameDest": "R2_C", "amount": 1950.0, "isFraud": 1},
        {"nameOrig": "R2_C", "nameDest": "R2_D", "amount": 1900.0, "isFraud": 1},
        {"nameOrig": "R2_D", "nameDest": "R2_A", "amount": 1850.0, "isFraud": 1},
    ]
    
    # 2. Create legitimate multi-hop chains (NOT rings)
    legit_chains = []
    for i in range(20):
        legit_chains.extend([
            {"nameOrig": f"Legit_{i}_A", "nameDest": f"Legit_{i}_B", "amount": 500.0, "isFraud": 1},
            {"nameOrig": f"Legit_{i}_B", "nameDest": f"Legit_{i}_C", "amount": 500.0, "isFraud": 1},
        ])
    
    data = ring1 + ring2 + legit_chains
    df = pd.DataFrame(data)
    
    # Build Graph
    graph = build_fraud_graph(df)
    
    # Extract rings using proper cycle detection
    suspected_rings = find_fraud_rings(graph, max_length=8)
    
    # Evaluate Precision and Recall
    ground_truth_rings = [{"R1_A", "R1_B", "R1_C"}, {"R2_A", "R2_B", "R2_C", "R2_D"}]
    
    true_positives = 0
    false_positives = 0
    
    for suspected in suspected_rings:
        if suspected in ground_truth_rings:
            true_positives += 1
        else:
            false_positives += 1
            
    false_negatives = len(ground_truth_rings) - true_positives
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    
    print(f"\nTotal Nodes: {graph.number_of_nodes()}")
    print(f"Total Edges: {graph.number_of_edges()}")
    print(f"Found {len(suspected_rings)} suspected rings (3+ accounts).")
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")

if __name__ == "__main__":
    main()
