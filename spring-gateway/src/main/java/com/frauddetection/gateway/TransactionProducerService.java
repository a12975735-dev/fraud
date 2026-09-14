package com.frauddetection.gateway;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class TransactionProducerService {

    public static final String TOPIC = "transactions-stream";
    private static final Logger logger = LoggerFactory.getLogger(TransactionProducerService.class);
    private final KafkaTemplate<String, TransactionMessage> kafkaTemplate;

    public TransactionProducerService(KafkaTemplate<String, TransactionMessage> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void publish(TransactionMessage message) {
        kafkaTemplate.send(TOPIC, message.transactionId(), message)
                .whenComplete((result, error) -> {
                    if (error != null) {
                        logger.error("Kafka message publishing failed transactionId={}", message.transactionId(), error);
                    } else {
                        logger.info("Kafka message published transactionId={} topic={} partition={} offset={}",
                                message.transactionId(), TOPIC, result.getRecordMetadata().partition(),
                                result.getRecordMetadata().offset());
                    }
                });
    }
}
