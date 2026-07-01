import httpx
import json

base_url = "http://127.0.0.1:8000/claims"

# Test Health Claim
health_payload = {
    "claimant_name": "Aarav Sharma",
    "policy_number": "HL-2025-001",
    "patient_name": "Aarav Sharma",
    "age": 42,
    "diagnosis": "Acute Appendicitis",
    "treatment_type": "Surgery",
    "hospital_name": "Apollo Hospital, Delhi",
    "admission_date": "10-06-2026",
    "discharge_date": "15-06-2026",
    "room_type": "Private",
    "total_bill_amount": 180000.0,
    "sum_insured": 500000.0
}

# Test Travel Claim (Flight Delay)
travel_delay_payload = {
    "claimant_name": "Priya Patel",
    "policy_number": "TR-2025-001",
    "claim_type": "flight_delay",
    "origin": "Delhi",
    "destination": "London",
    "departure_date": "20-06-2026",
    "delay_hours": 6.5,
    "baggage_value": 0.0,
    "cancellation_reason": "",
    "sum_insured": 10000.0,
    "description": "Flight AI-111 delayed due to engine malfunction at Delhi Airport."
}

# Test Travel Claim (Baggage Loss)
travel_baggage_payload = {
    "claimant_name": "Priya Patel",
    "policy_number": "TR-2025-001",
    "claim_type": "baggage_loss",
    "origin": "Delhi",
    "destination": "London",
    "departure_date": "20-06-2026",
    "delay_hours": 0.0,
    "baggage_value": 8500.0,
    "cancellation_reason": "",
    "sum_insured": 10000.0,
    "description": "Checked baggage never arrived at London Heathrow. Airline issued PIR report."
}

def run_tests():
    print("Testing /claims/health endpoint...")
    try:
        r = httpx.post(f"{base_url}/health", json=health_payload, timeout=60.0)
        print("Health Status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Final Payout:", data["final_payout"])
            print("Room Rent Cap:", data["room_rent_cap"])
            print("Room Rent Excess:", data["room_rent_excess"])
            print("Total Deductions:", data["total_deductions"])
            print("Explanation Summary:", data["explanation"][:120] + "...")
        else:
            print("Error Response:", r.text)
    except Exception as e:
        print("Health claim request failed:", e)

    print("\nTesting /claims/travel (Flight Delay) endpoint...")
    try:
        r = httpx.post(f"{base_url}/travel", json=travel_delay_payload, timeout=60.0)
        print("Travel Delay Status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Final Payout:", data["final_payout"])
            print("Applied Payout Tier:", data["payout_tier"])
            print("Explanation Summary:", data["explanation"][:120] + "...")
        else:
            print("Error Response:", r.text)
    except Exception as e:
        print("Travel delay claim request failed:", e)

    print("\nTesting /claims/travel (Baggage Loss) endpoint...")
    try:
        r = httpx.post(f"{base_url}/travel", json=travel_baggage_payload, timeout=60.0)
        print("Travel Baggage Status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Final Payout:", data["final_payout"])
            print("Applied Payout Tier:", data["payout_tier"])
            print("Explanation Summary:", data["explanation"][:120] + "...")
        else:
            print("Error Response:", r.text)
    except Exception as e:
        print("Travel baggage claim request failed:", e)

if __name__ == "__main__":
    run_tests()
