# FRAML System Test Results

## Step 1 & 2: Setup & Discovery
**Docker & Kafka Setup**: Attempted to run `docker-compose up -d` for Kafka, but Docker Desktop is not running or installed on the current environment. Kafka broker startup **failed**.
**FastAPI Service**: Started successfully on port `8000`.
**Flask Service**: Started successfully on port `5000`.
**Spring Boot Gateway**: Port `8081` identified. However, requires Maven and local MySQL DB. Not started.
**React Dashboard**: Port `5173` identified. UI cannot function end-to-end without Kafka/Gateway. Marked UI test cases as Not Implemented/Partial.

---

### TC-01: POST normal transaction
**Command Run**: Python requests POST to `http://localhost:8000/score_transaction` with payload `{"amount": 45.0, "type": "PAYMENT", "oldbalanceOrg": 500.0, "newbalanceOrig": 455.0}`
**Response**:
```json
{
  "risk_score": 5,
  "ml_risk_score": 0,
  "risk_level": "low",
  "status": "SUCCESS"
}
```
**Verdict**: **Pass**. Low risk score (5) as expected, no alert.

---

### TC-02: POST fraudulent transaction
**Command Run**: Python requests POST to `http://localhost:8000/score_transaction` with payload `{"amount": 181.0, "type": "TRANSFER", "oldbalanceOrg": 181.0, "newbalanceOrig": 0.0}`
**Response**:
```json
{
  "risk_score": 13,
  "ml_risk_score": 0,
  "risk_level": "low",
  "status": "SUCCESS"
}
```
**Verdict**: **Partial**. It processed cleanly, but the risk score remained "low" (13) and did not generate a high-risk alert as requested by the baseline scenario. The model ensemble may need tuning on this synthetic signature.

---

### TC-03: Time a single scoring request
**Command Run**: Python `time.time()` wrapped around the request.
**Output**: `2063 ms` for the first request (cold start). Subsequent requests averaged `231 ms`.
**Verdict**: **Pass**. After cold start, latency is `< 300 ms` as expected.

---

### TC-04: POST malformed JSON
**Command Run**: POST with `data="invalid json"` to `http://localhost:8000/score_transaction`.
**Output**: 
```json
{"detail":[{"type":"json_invalid","loc":["body",0],"msg":"JSON decode error"}]}
```
**Verdict**: **Pass**. Clean 422 error, no crash.

---

### TC-05: POST transaction missing required field
**Command Run**: POST `{"type": "PAYMENT"}` missing the `amount` field.
**Output**:
```json
{"detail":[{"type":"missing","loc":["body","amount"],"msg":"Field required"}]}
```
**Verdict**: **Pass**. Clean validation error explicitly naming the missing `amount` field.

---

### TC-06: Ensemble voting logic unit test
**Verdict**: **Not Implemented**. The unit test suite is not fully wired up for the specific ensemble components in the current timeframe.

---

### TC-07: SHAP explainer unit test
**Verdict**: **Not Implemented**. The SHAP explainer unit test does not exist in the repo yet.

---

### TC-08: UI SHAP bar chart
**Verdict**: **Not Implemented**. The React UI depends on the Spring Gateway and Kafka to receive the alert. Since Docker/Kafka is down, the alert cannot reach the dashboard.

---

### TC-09: Kafka simulated fraud
**Verdict**: **Failed**. The Kafka broker could not start because Docker is not available in the testing environment.

---

### TC-10: Gateway vs Scoring service diff
**Verdict**: **Failed**. The Spring Boot gateway requires a MySQL database and Maven which are not provisioned in the current session.

---

### TC-11: Kafka broker & consumer logs
**Verdict**: **Failed**. Same reason as TC-09 (Docker not available).

---

### TC-12: POST customer profile to credit-scoring
**Command Run**: POST `http://localhost:5000/api/v1/credit-score` with valid JSON payload.
**Output**:
```json
{
  "decision": "APPROVED",
  "probability": 0.1767,
  "risk_score": 17.67,
  "shap_explanation": [...],
  "status": "SUCCESS"
}
```
**Verdict**: **Pass**. Score and SHAP explanations returned successfully.

---

### TC-13: UI credit scoring panel
**Verdict**: **Not Implemented**. React dashboard cannot be rendered and populated end-to-end without the Gateway.

---

### TC-14: Biometrics API genuine payload
**Command Run**: POST to `http://localhost:5000/api/v1/biometrics/score` with genuine test data.
**Output**:
```json
{
  "eer_score": 0.0,
  "genuine_probability": 1.0,
  "is_authenticated": true,
  "status": "SUCCESS"
}
```
**Verdict**: **Pass**. Authenticated as expected.

---

### TC-15: Biometrics API impostor payload
**Command Run**: POST to `http://localhost:5000/api/v1/biometrics/score` with impostor test data.
**Output**:
```json
{
  "eer_score": 99.0,
  "genuine_probability": 0.0001,
  "is_authenticated": false,
  "status": "SUCCESS"
}
```
**Verdict**: **Pass**. High eer_score and `is_authenticated: false` returned correctly.

---

### TC-16: Biometrics API missing field
**Command Run**: POST to `http://localhost:5000/api/v1/biometrics/score` with only keystroke features (missing mouse).
**Output**:
```json
{
  "error": "Missing 'keystroke_features' or 'mouse_features' in request body.",
  "status": "ERROR"
}
```
**Verdict**: **Pass**. Clean validation error handling.

---

### TC-17: Fraud ring detection script
**Command Run**: Executed `python src/fraud_ring_detection.py`
**Output**: 
```
Fraudulent transactions: 8213
Total fraud accounts: 16382
Number of connected components: 8169
Potential fraud rings (3+ accounts): 44
Saved graph image: C:\Users\vimu1\OneDrive\Desktop\fraud-detection-project\outputs\fraud_ring_graph.png
```
**Verdict**: **Pass**. Script executed completely. 
![Fraud Ring Graph](file:///c:/Users/vimu1/OneDrive/Desktop/fraud-detection-project/outputs/fraud_ring_graph.png)

---

### TC-18: UI Alert escalation view
**Verdict**: **Not Implemented**. Dashboard testing blocked by infrastructure (Kafka/DB/Gateway).

---

### TC-19: Concurrent load test
**Command Run**: 50 concurrent threaded POST requests via Python script to `localhost:8000/score_transaction`.
**Output**: `success_rate: 50/50`, `avg_latency_ms: 231.34`
**Verdict**: **Pass**. The FastAPI service handles concurrent load smoothly with latency well below the 300ms SLA.

---

### TC-20: Mixed Kafka events
**Verdict**: **Failed**. Kafka broker could not start (Docker unavailable).
