package com.frauddetection.gateway;

public class TransactionNotFoundException extends RuntimeException {

    public TransactionNotFoundException(Long id) {
        super("Scored transaction with ID " + id + " was not found.");
    }

    public TransactionNotFoundException(String transactionId) {
        super("Scored transaction with transactionId " + transactionId + " was not found.");
    }
}
