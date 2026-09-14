package com.frauddetection.gateway;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ScoredTransactionRepository extends JpaRepository<ScoredTransaction, Long> {

    Optional<ScoredTransaction> findByTransactionId(String transactionId);
}
