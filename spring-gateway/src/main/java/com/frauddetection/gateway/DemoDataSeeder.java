package com.frauddetection.gateway;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class DemoDataSeeder implements CommandLineRunner {

    private final ScoredTransactionRepository transactionRepository;

    public DemoDataSeeder(ScoredTransactionRepository transactionRepository) {
        this.transactionRepository = transactionRepository;
    }

    @Override
    public void run(String... args) {
        if (transactionRepository.count() > 0) {
            return;
        }

        Instant now = Instant.now();
        transactionRepository.saveAll(List.of(
                completed("LIVE-100001", now.minus(3, ChronoUnit.HOURS), 450000.00, 14, "TRANSFER",
                        0, 0, 18.5, 95, 450000, 82.0,
                        "ACC-100234", "DEST-900001", "DEV-8F6A21C9", "New York",
                        94, "high", "amount_deviation"),
                completed("LIVE-100002", now.minus(2, ChronoUnit.HOURS), 8750.00, 3, "CASH_OUT",
                        12000, 3250, 4.2, 22, 8750, 35.0,
                        "ACC-100234", "DEST-900002", "DEV-8F6A21C9", "New York",
                        48, "medium", "transaction_velocity"),
                completed("LIVE-100003", now.minus(1, ChronoUnit.HOURS), 45.50, 1, "PAYMENT",
                        1200, 1154.50, 0.5, 0.1, 0, 8.0,
                        "ACC-100556", "DEST-900003", "DEV-572418", "Boston",
                        6, "low", "balance_discrepancy"),
                completed("LIVE-100004", now.minus(35, ChronoUnit.MINUTES), 3200.00, 8, "TRANSFER",
                        7000, 3800, 7.1, 58, 3200, 64.0,
                        "ACC-100789", "DEST-900002", "DEV-572418", "Boston",
                        76, "high", "amount_deviation"),
                completed("LIVE-100005", now.minus(12, ChronoUnit.MINUTES), 125.50, 2, "PAYMENT",
                        850, 724.50, 0.8, 2.4, 0, 5.0,
                        "ACC-100556", "DEST-900004", "DEV-572418", "Boston",
                        12, "low", "transaction_velocity")
        ));
    }

    private ScoredTransaction completed(String id, Instant timestamp, double amount, int step, String type,
                                        double oldBalanceDest, double newBalanceDest, double velocity,
                                        double deviation, double discrepancy, Double biometricScore,
                                        String sourceAccount, String destinationAccount, String deviceId,
                                        String region, int riskScore, String riskLevel, String reasonFeature) {
        ScoredTransaction transaction = new ScoredTransaction(id, timestamp, amount, step, type,
                oldBalanceDest, newBalanceDest, velocity, deviation, discrepancy, biometricScore,
                sourceAccount, destinationAccount, deviceId, region);
        transaction.markCompleted(riskScore, riskLevel,
                "[{\"feature\":\"" + reasonFeature + "\",\"impact\":0.42}]",
                "{\"seeded\":true,\"risk_score\":" + riskScore + "}");
        return transaction;
    }
}
