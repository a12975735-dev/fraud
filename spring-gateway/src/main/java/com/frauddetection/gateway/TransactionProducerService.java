package com.frauddetection.gateway;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class TransactionProducerService {

    public static final String TOPIC = "transactions-stream";
    private static final Logger logger = LoggerFactory.getLogger(TransactionProducerService.class);
    private final KafkaTemplate<String, TransactionMessage> kafkaTemplate;
    private final boolean kafkaEnabled;

    public TransactionProducerService(KafkaTemplate<String, TransactionMessage> kafkaTemplate,
                                      @Value("${kafka.enabled:false}") boolean kafkaEnabled) {
        this.kafkaTemplate = kafkaTemplate;
        this.kafkaEnabled = kafkaEnabled;
    }

    public boolean publish(TransactionMessage message) {
        if (!kafkaEnabled) {
            logger.info("Kafka disabled; transaction will use direct scoring transactionId={}", message.transactionId());
            return false;
        }
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
        return true;
    }
}
