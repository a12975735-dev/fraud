package com.frauddetection.gateway;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "scored_transactions")
public class ScoredTransaction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, length = 36)
    private String transactionId;

    private Instant timestamp;
    private double amount;
    @Column(nullable = true)
    private Integer riskScore;

    @Column(nullable = true)
    private String riskLevel;

    private String status;

    @Column(columnDefinition = "TEXT", nullable = true)
    private String topReasonCodes;

    @Column(columnDefinition = "TEXT", nullable = true)
    private String rawPythonResponse;

    protected ScoredTransaction() {
        // Required by JPA.
    }

    public ScoredTransaction(String transactionId, Instant timestamp, double amount) {
        this.transactionId = transactionId;
        this.timestamp = timestamp;
        this.amount = amount;
        this.status = "PENDING";
    }

    public void markCompleted(int riskScore, String riskLevel, String topReasonCodes,
                              String rawPythonResponse) {
        this.riskScore = riskScore;
        this.riskLevel = riskLevel;
        this.topReasonCodes = topReasonCodes;
        this.rawPythonResponse = rawPythonResponse;
        this.status = "COMPLETED";
    }

    public void markFailed(String rawPythonResponse) {
        this.rawPythonResponse = rawPythonResponse;
        this.status = "FAILED";
    }

    public Long getId() { return id; }
    public String getTransactionId() { return transactionId; }
    public Instant getTimestamp() { return timestamp; }
    public double getAmount() { return amount; }
    public Integer getRiskScore() { return riskScore; }
    public String getRiskLevel() { return riskLevel; }
    public String getStatus() { return status; }
    public String getTopReasonCodes() { return topReasonCodes; }
    public String getRawPythonResponse() { return rawPythonResponse; }
}
