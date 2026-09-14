import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.flask_api import app

client = app.test_client()

genuine_payload = {
  "keystroke_features": {
    "avg_dwell_time": 92.45, 
    "avg_flight_time": 118.20
  },
  "mouse_features": {
    "mda": -15.42,
    "msd": 0.12,
    "total_distance": 1800.5,
    "avg_speed": 2.45
  }
}

impostor_payload = {
  "keystroke_features": {
    "avg_dwell_time": 150.0, 
    "avg_flight_time": 210.0
  },
  "mouse_features": {
    "mda": 120.0,
    "msd": 0.55,
    "total_distance": 4200.0,
    "avg_speed": 900.0
  }
}

print("Testing Genuine Payload:")
response1 = client.post('/api/v1/biometrics/score', json=genuine_payload)
print(response1.get_json())

print("\nTesting Impostor Payload:")
response2 = client.post('/api/v1/biometrics/score', json=impostor_payload)
print(response2.get_json())
