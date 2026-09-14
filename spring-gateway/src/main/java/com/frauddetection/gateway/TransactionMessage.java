package com.frauddetection.gateway;

/** JSON payload sent to Kafka; transactionId correlates the message with its database record. */
public record TransactionMessage(
        String transactionId,
        Double amount,
        Double oldbalanceDest,
        Double newbalanceDest,
        Integer step,
        Double transaction_velocity,
        Double amount_deviation,
        Double balance_discrepancy,
        String type,
        Double biometricRiskScore) {
}
