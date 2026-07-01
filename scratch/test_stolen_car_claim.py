import httpx
import json

url = "http://127.0.0.1:8000/automation/run"
payload = {
    "message": "My car was stolen and I want to claim \u20b93,00,000 on policy DG-MOTOR-2025-042"
}

print("Running stolen car claim automation query...")
try:
    response = httpx.post(url, json=payload, timeout=60.0)
    print("Status Code:", response.status_code)
    data = response.json()
    print("Full Response JSON:")
    print(json.dumps(data, indent=2))
except Exception as e:
    print("Failed to run test:", e)
