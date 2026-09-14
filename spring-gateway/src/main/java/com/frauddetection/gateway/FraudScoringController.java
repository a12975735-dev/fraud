package com.frauddetection.gateway;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

@RestController
@RequestMapping("/api")
public class FraudScoringController {

    private static final String FASTAPI_HEALTH_URL = "http://127.0.0.1:8000/";
    private static final Logger logger = LoggerFactory.getLogger(FraudScoringController.class);
    private final RestTemplate restTemplate;
    private final ScoredTransactionRepository transactionRepository;
    private final TransactionProducerService transactionProducerService;

    public FraudScoringController(RestTemplate restTemplate, ScoredTransactionRepository transactionRepository,
                                  TransactionProducerService transactionProducerService) {
        this.restTemplate = restTemplate;
        this.transactionRepository = transactionRepository;
        this.transactionProducerService = transactionProducerService;
    }

    @PostMapping(value = "/score_transaction", consumes = MediaType.APPLICATION_JSON_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, String>> scoreTransaction(@Valid @RequestBody TransactionRequest transaction) {
        String transactionId = UUID.randomUUID().toString();
        logger.info("Incoming async score request endpoint=/api/score_transaction transactionId={} timestamp={}",
                transactionId, Instant.now());

        transactionRepository.save(new ScoredTransaction(transactionId, Instant.now(), transaction.amount(),
            transaction.step(), transaction.type(), transaction.oldbalanceDest(), transaction.newbalanceDest(),
            transaction.transaction_velocity(), transaction.amount_deviation(), transaction.balance_discrepancy(),
            transaction.biometricRiskScore(), transaction.sourceAccount(), transaction.destinationAccount(),
            transaction.deviceId(), transaction.region()));
        transactionProducerService.publish(new TransactionMessage(
                transactionId, transaction.amount(), transaction.oldbalanceDest(), transaction.newbalanceDest(),
                transaction.step(), transaction.transaction_velocity(), transaction.amount_deviation(),
            transaction.balance_discrepancy(), transaction.type(), transaction.biometricRiskScore(),
            transaction.sourceAccount(), transaction.destinationAccount(), transaction.deviceId(), transaction.region()));

        logger.info("Response status=202 endpoint=/api/score_transaction transactionId={} status=PENDING", transactionId);
        return ResponseEntity.accepted().body(Map.of("transactionId", transactionId, "status", "PENDING"));
    }

    @GetMapping("/transactions")
    public Page<ScoredTransaction> getTransactions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        logger.info("Incoming request endpoint=/api/transactions timestamp={}", Instant.now());
        Page<ScoredTransaction> transactions = transactionRepository.findAll(
                PageRequest.of(page, Math.min(Math.max(size, 1), 100), Sort.by("timestamp").descending()));
        logger.info("Response status=200 endpoint=/api/transactions");
        return transactions;
    }

    @GetMapping("/transactions/{id}")
    public ResponseEntity<ScoredTransaction> getTransaction(@PathVariable Long id) {
        logger.info("Incoming request endpoint=/api/transactions/{} timestamp={}", id, Instant.now());
        ScoredTransaction transaction = transactionRepository.findById(id)
                .orElseThrow(() -> new TransactionNotFoundException(id));
        logger.info("Response status=200 endpoint=/api/transactions/{}", id);
        return ResponseEntity.ok(transaction);
    }

    @GetMapping("/transaction/{transactionId}/status")
    public ResponseEntity<ScoredTransaction> getTransactionStatus(@PathVariable String transactionId) {
        logger.info("Incoming request endpoint=/api/transaction/{}/status timestamp={}", transactionId, Instant.now());
        ScoredTransaction transaction = transactionRepository.findByTransactionId(transactionId)
                .orElseThrow(() -> new TransactionNotFoundException(transactionId));
        logger.info("Response status=200 endpoint=/api/transaction/{}/status transactionStatus={}",
                transactionId, transaction.getStatus());
        return ResponseEntity.ok(transaction);
    }

    @DeleteMapping("/transactions/{id}")
    public ResponseEntity<Void> deleteTransaction(@PathVariable Long id) {
        logger.info("Incoming request endpoint=/api/transactions/{} method=DELETE timestamp={}", id, Instant.now());
        if (!transactionRepository.existsById(id)) {
            logger.info("Response status=404 endpoint=/api/transactions/{} method=DELETE", id);
            throw new TransactionNotFoundException(id);
        }
        transactionRepository.deleteById(id);
        logger.info("Response status=204 endpoint=/api/transactions/{} method=DELETE", id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        logger.info("Incoming request endpoint=/api/health timestamp={}", Instant.now());
        Map<String, String> status = new LinkedHashMap<>();
        status.put("gateway", "ok");
        try {
            ResponseEntity<String> pythonResponse = restTemplate.getForEntity(FASTAPI_HEALTH_URL, String.class);
            status.put("python_api", pythonResponse.getStatusCode().is2xxSuccessful() ? "reachable" : "unavailable");
        } catch (RestClientException exception) {
            logger.error("Python API health check failed", exception);
            status.put("python_api", "unreachable");
        }
        logger.info("Response status=200 endpoint=/api/health");
        return status;
    }

    @GetMapping("/stats")
    public Map<String, Object> stats() {
        logger.info("Incoming request endpoint=/api/stats timestamp={}", Instant.now());
        Map<String, Long> riskLevels = new LinkedHashMap<>();
        for (String level : new String[]{"low", "medium", "high"}) {
            riskLevels.put(level, transactionRepository.findAll().stream()
                    .filter(transaction -> level.equalsIgnoreCase(transaction.getRiskLevel())).count());
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("totalTransactionsScored", transactionRepository.count());
        result.put("riskLevelCounts", riskLevels);
        logger.info("Response status=200 endpoint=/api/stats");
        return result;
    }

    public record TransactionRequest(
            @NotNull(message = "amount is required") @Positive(message = "amount must be greater than zero") Double amount,
            @PositiveOrZero(message = "oldbalanceDest cannot be negative") Double oldbalanceDest,
            @PositiveOrZero(message = "newbalanceDest cannot be negative") Double newbalanceDest,
            @PositiveOrZero(message = "step cannot be negative") Integer step,
            @PositiveOrZero(message = "transaction_velocity cannot be negative") Double transaction_velocity,
            @PositiveOrZero(message = "amount_deviation cannot be negative") Double amount_deviation,
            @PositiveOrZero(message = "balance_discrepancy cannot be negative") Double balance_discrepancy,
            String type,
            @PositiveOrZero(message = "biometricRiskScore cannot be negative") Double biometricRiskScore,
            String sourceAccount,
            String destinationAccount,
            String deviceId,
            String region) {
    }
}
