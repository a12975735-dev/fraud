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
    private Integer step;
    @Column(length = 32)
    private String type;
    private double oldBalanceDest;
    private double newBalanceDest;
    private double transactionVelocity;
    private double amountDeviation;
    private double balanceDiscrepancy;
    private Double biometricRiskScore;
    @Column(length = 64)
    private String sourceAccount;
    @Column(length = 64)
    private String destinationAccount;
    @Column(length = 64)
    private String deviceId;
    @Column(length = 64)
    private String region;
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

    public ScoredTransaction(String transactionId, Instant timestamp, double amount, Integer step, String type,
                             double oldBalanceDest, double newBalanceDest, double transactionVelocity,
                             double amountDeviation, double balanceDiscrepancy, Double biometricRiskScore,
                             String sourceAccount, String destinationAccount, String deviceId, String region) {
        this.transactionId = transactionId;
        this.timestamp = timestamp;
        this.amount = amount;
        this.step = step;
        this.type = type;
        this.oldBalanceDest = oldBalanceDest;
        this.newBalanceDest = newBalanceDest;
        this.transactionVelocity = transactionVelocity;
        this.amountDeviation = amountDeviation;
        this.balanceDiscrepancy = balanceDiscrepancy;
        this.biometricRiskScore = biometricRiskScore;
        this.sourceAccount = sourceAccount;
        this.destinationAccount = destinationAccount;
        this.deviceId = deviceId;
        this.region = region;
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
    public Integer getStep() { return step; }
    public String getType() { return type; }
    public double getOldBalanceDest() { return oldBalanceDest; }
    public double getNewBalanceDest() { return newBalanceDest; }
    public double getTransactionVelocity() { return transactionVelocity; }
    public double getAmountDeviation() { return amountDeviation; }
    public double getBalanceDiscrepancy() { return balanceDiscrepancy; }
    public Double getBiometricRiskScore() { return biometricRiskScore; }
    public String getSourceAccount() { return sourceAccount; }
    public String getDestinationAccount() { return destinationAccount; }
    public String getDeviceId() { return deviceId; }
    public String getRegion() { return region; }
    public Integer getRiskScore() { return riskScore; }
    public String getRiskLevel() { return riskLevel; }
    public String getStatus() { return status; }
    public String getTopReasonCodes() { return topReasonCodes; }
    public String getRawPythonResponse() { return rawPythonResponse; }
}
