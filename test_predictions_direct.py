import json
from src.api.routers.predictions import get_prediction
from src.api.schemas.event import EventRequest

payload1 = EventRequest(**{
  "event_type": "Political Rally",
  "start_datetime": "2024-10-25 15:00:00",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "zone": "Jayanagara",
  "expected_attendance": 15000
})

payload2 = EventRequest(**{
  "event_type": "potholes",
  "start_datetime": "2025-02-12 03:15:00",
  "latitude": 13.0400,
  "longitude": 77.5180,
  "zone": "Peenya",
  "expected_attendance": 0
})

print("Testing Payload 1 (High Risk):")
try:
    response = get_prediction(payload1)
    print(json.dumps(response, indent=2))
except Exception as e:
    print(e)

print("\nTesting Payload 2 (Low Risk):")
try:
    response = get_prediction(payload2)
    print(json.dumps(response, indent=2))
except Exception as e:
    print(e)
