package com.frauddetection.gateway;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class TransactionConsumerService {

    private static final String FASTAPI_SCORE_URL = "http://127.0.0.1:8000/score_transaction";
    private static final Logger logger = LoggerFactory.getLogger(TransactionConsumerService.class);

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final ScoredTransactionRepository transactionRepository;

    public TransactionConsumerService(RestTemplate restTemplate, ObjectMapper objectMapper,
                                      ScoredTransactionRepository transactionRepository) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
        this.transactionRepository = transactionRepository;
    }

    @KafkaListener(topics = TransactionProducerService.TOPIC)
    public void consume(TransactionMessage message) {
        logger.info("Kafka message consumed transactionId={}", message.transactionId());
        ScoredTransaction transaction = transactionRepository.findByTransactionId(message.transactionId())
                .orElseThrow(() -> new IllegalStateException(
                        "No database record exists for transactionId=" + message.transactionId()));

        try {
            logger.info("Calling FastAPI for transactionId={}", message.transactionId());
            var response = restTemplate.postForEntity(FASTAPI_SCORE_URL, message, String.class);
            JsonNode scoredResponse = objectMapper.readTree(response.getBody());
            String topReasonCodes = objectMapper.writeValueAsString(scoredResponse.path("top_reason_codes"));

            transaction.markCompleted(
                    scoredResponse.path("risk_score").asInt(),
                    scoredResponse.path("risk_level").asText(),
                    topReasonCodes,
                    response.getBody());
            transactionRepository.save(transaction);
            logger.info("Database record updated to COMPLETED transactionId={}", message.transactionId());
        } catch (Exception exception) {
            logger.error("Asynchronous FastAPI scoring failed transactionId={}", message.transactionId(), exception);
            transaction.markFailed("{\"error\":\"FastAPI scoring failed.\"}");
            transactionRepository.save(transaction);
            logger.info("Database record updated to FAILED transactionId={}", message.transactionId());
        }
    }
}
