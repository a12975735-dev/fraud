import requests
import time
import json
import concurrent.futures

FASTAPI_URL = "http://localhost:8000"
FLASK_URL = "http://localhost:5000"

results = {}

def run_tc01():
    print("Running TC-01: POST normal transaction")
    payload = {"amount": 45.00, "type": "PAYMENT", "oldbalanceOrg": 500.00, "newbalanceOrig": 455.00}
    try:
        r = requests.post(f"{FASTAPI_URL}/score_transaction", json=payload)
        return {"status": r.status_code, "response": r.json()}
    except Exception as e:
        return {"error": str(e)}

def run_tc02():
    print("Running TC-02: POST fraudulent transaction")
    payload = {"amount": 181.00, "type": "TRANSFER", "oldbalanceOrg": 181.00, "newbalanceOrig": 0.00}
    try:
        r = requests.post(f"{FASTAPI_URL}/score_transaction", json=payload)
        return {"status": r.status_code, "response": r.json()}
    except Exception as e:
        return {"error": str(e)}

def run_tc03():
    print("Running TC-03: Latency timing")
    payload = {"amount": 45.00, "type": "PAYMENT", "oldbalanceOrg": 500.00, "newbalanceOrig": 455.00}
    start = time.time()
    try:
        r = requests.post(f"{FASTAPI_URL}/score_transaction", json=payload)
        latency = (time.time() - start) * 1000
        return {"latency_ms": latency}
    except Exception as e:
        return {"error": str(e)}

def run_tc04():
    print("Running TC-04: Malformed JSON")
    try:
        r = requests.post(f"{FASTAPI_URL}/score_transaction", data="invalid json", headers={"Content-Type": "application/json"})
        return {"status": r.status_code, "response": r.text}
    except Exception as e:
        return {"error": str(e)}

def run_tc05():
    print("Running TC-05: Missing required field")
    payload = {"type": "PAYMENT"} # missing amount
    try:
        r = requests.post(f"{FASTAPI_URL}/score_transaction", json=payload)
        return {"status": r.status_code, "response": r.json()}
    except Exception as e:
        return {"error": str(e)}

def run_tc12():
    print("Running TC-12: POST credit scoring")
    payload = {
        "utility_payment_ratio": 0.9,
        "avg_monthly_cashflow": 1200.0,
        "cashflow_volatility": 0.1,
        "social_engagement_score": 8.0,
        "credit_inquiries_3m": 1
    }
    try:
        r = requests.post(f"{FLASK_URL}/api/v1/credit-score", json=payload)
        return {"status": r.status_code, "response": r.json()}
    except Exception as e:
        return {"error": str(e)}

def run_tc14():
    print("Running TC-14: Biometrics genuine payload")
    payload = {
        "keystroke_features": {"avg_dwell_time": 92.45, "avg_flight_time": 118.20},
        "mouse_features": {"mda": -15.42, "msd": 0.12, "total_distance": 1800.5, "avg_speed": 2.45}
    }
    try:
        r = requests.post(f"{FLASK_URL}/api/v1/biometrics/score", json=payload)
        return {"status": r.status_code, "response": r.json()}
    except Exception as e:
        return {"error": str(e)}

def run_tc15():
    print("Running TC-15: Biometrics impostor payload")
    payload = {
        "keystroke_features": {"avg_dwell_time": 150.0, "avg_flight_time": 210.0},
        "mouse_features": {"mda": 120.0, "msd": 0.55, "total_distance": 4200.0, "avg_speed": 900.0}
    }
    try:
        r = requests.post(f"{FLASK_URL}/api/v1/biometrics/score", json=payload)
        return {"status": r.status_code, "response": r.json()}
    except Exception as e:
        return {"error": str(e)}

def run_tc16():
    print("Running TC-16: Biometrics missing field")
    payload = {
        "keystroke_features": {"avg_dwell_time": 92.45}
    }
    try:
        r = requests.post(f"{FLASK_URL}/api/v1/biometrics/score", json=payload)
        return {"status": r.status_code, "response": r.json()}
    except Exception as e:
        return {"error": str(e)}

def run_tc19():
    print("Running TC-19: Concurrent load test")
    payload = {"amount": 45.00, "type": "PAYMENT"}
    def req():
        return requests.post(f"{FASTAPI_URL}/score_transaction", json=payload)
    
    start = time.time()
    success = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(req) for _ in range(50)]
        for f in concurrent.futures.as_completed(futures):
            if f.result().status_code == 200:
                success += 1
    latency = (time.time() - start) * 1000 / 50
    return {"success_rate": f"{success}/50", "avg_latency_ms": latency}

if __name__ == "__main__":
    results["TC-01"] = run_tc01()
    results["TC-02"] = run_tc02()
    results["TC-03"] = run_tc03()
    results["TC-04"] = run_tc04()
    results["TC-05"] = run_tc05()
    results["TC-12"] = run_tc12()
    results["TC-14"] = run_tc14()
    results["TC-15"] = run_tc15()
    results["TC-16"] = run_tc16()
    results["TC-19"] = run_tc19()
    
    with open("api_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Finished API tests.")
