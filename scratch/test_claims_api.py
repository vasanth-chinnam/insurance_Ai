import httpx

url = "http://127.0.0.1:8000/claims/motor"
files = {
    "damage_photo": ("car_damage.png", open("D:/insurance/uploads/claims/car_damage.png", "rb"), "image/png")
}
data = {
    "claimant_name": "John Doe",
    "vehicle_number": "KA-01-MJ-1234",
    "vehicle_make": "Honda",
    "vehicle_model": "City",
    "year": "2020",
    "incident_date": "15-06-2025",
    "incident_description": "Front bumper collided with a low wall.",
    "policy_number": "DG-MOTOR-2025-042"
}

print("Sending request to Claim Estimator API...")
try:
    response = httpx.post(url, data=data, files=files, timeout=60.0)
    print("Status Code:", response.status_code)
    print("Response JSON:")
    import json
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("Failed to run claims test:", e)
