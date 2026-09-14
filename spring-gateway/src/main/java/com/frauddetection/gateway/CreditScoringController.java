package com.frauddetection.gateway;

import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

/** Proxies authenticated dashboard credit-score requests to the Flask model service. */
@RestController
@RequestMapping("/api/v1")
public class CreditScoringController {

    private final RestTemplate restTemplate;
    private final String creditScoringEndpoint;

    public CreditScoringController(RestTemplate restTemplate,
                                   @Value("${credit.scoring.endpoint}") String creditScoringEndpoint) {
        this.restTemplate = restTemplate;
        this.creditScoringEndpoint = creditScoringEndpoint;
    }

    @PostMapping(value = "/credit-score", consumes = MediaType.APPLICATION_JSON_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> creditScore(@RequestBody Map<String, Object> request) {
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(creditScoringEndpoint, request, Map.class);
            return ResponseEntity.status(response.getStatusCode()).body(response.getBody());
        } catch (RestClientException exception) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(Map.of(
                    "status", "ERROR",
                    "error", "Credit scoring service is unavailable."
            ));
        }
    }
}
