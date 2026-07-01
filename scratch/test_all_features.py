"""Full feature verification -- hits every endpoint to confirm no regressions."""
import httpx
import time
import sys

BASE = "http://127.0.0.1:8000"
PASS = 0
FAIL = 0

def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  -- {detail}")

def wait_for_server():
    for _ in range(15):
        try:
            r = httpx.get(f"{BASE}/", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False

def main():
    print("Waiting for backend...")
    if not wait_for_server():
        print("Backend not reachable. Aborting.")
        sys.exit(1)
    print("Backend is up.\n")

    # 1. Root health check
    r = httpx.get(f"{BASE}/")
    check("Root endpoint", r.status_code == 200)

    # 2. Policy Q&A (RAG) -- chat_router prefix="/api" + route="/chat"
    r = httpx.post(f"{BASE}/api/chat", json={"query": "What is the deductible for collision?", "insurance_type": "motor"}, timeout=60)
    check("RAG /api/chat", r.status_code == 200 and "answer" in r.json(), r.text[:120] if r.status_code != 200 else "")

    # 3. Fraud detection -- fraud_router prefix="/fraud" + route="/analyze"
    r = httpx.post(f"{BASE}/fraud/analyze", json={
        "insurance_type": "motor", "policy_number": "DG-MOTOR-2025-042",
        "claim_amount": 50000, "days_after_incident": 1,
        "previous_claims": 0, "incident_date": "01-06-2026",
        "description": "Minor fender bender"
    }, timeout=30)
    check("Fraud /fraud/analyze", r.status_code == 200 and "fraud_score" in r.json(), r.text[:120] if r.status_code != 200 else "")

    # 4. Risk profiler -- risk_router prefix="/risk" + route="/profile"
    #    Field is annual_km (not annual_mileage), needs vehicle_type
    r = httpx.post(f"{BASE}/risk/profile", json={
        "insurance_type": "motor",
        "motor": {"age": 30, "vehicle_age": 3, "annual_km": 12000,
                  "has_dashcam": True, "parking_type": "garage",
                  "traffic_violations": 0, "city_tier": "metro",
                  "vehicle_type": "sedan"}
    }, timeout=30)
    check("Risk /risk/profile", r.status_code == 200 and "risk_score" in r.json(), r.text[:120] if r.status_code != 200 else "")

    # 5. Renewal -- renewal_router prefix="/renewal" + route="/negotiate"
    r = httpx.post(f"{BASE}/renewal/negotiate", json={
        "current_policy": {
            "provider_name": "HDFC Ergo", "annual_premium": 12000,
            "sum_insured": 500000, "coverage_type": "Comprehensive",
            "years_with_provider": 3, "claim_free_years": 2
        },
        "user_profile": {
            "name": "Vasanth", "age": 30, "city": "Hyderabad",
            "insurance_type": "motor", "risk_score": 25
        }
    }, timeout=30)
    check("Renewal /renewal/negotiate", r.status_code == 200 and "best_deal" in r.json(), r.text[:120] if r.status_code != 200 else "")

    # 6. Health claim
    r = httpx.post(f"{BASE}/claims/health", json={
        "claimant_name": "Test User", "policy_number": "HL-2025-001",
        "patient_name": "Test User", "age": 40, "diagnosis": "Appendicitis",
        "treatment_type": "Surgery", "hospital_name": "Apollo",
        "admission_date": "10-06-2026", "discharge_date": "15-06-2026",
        "room_type": "General", "total_bill_amount": 100000, "sum_insured": 500000
    }, timeout=60)
    check("Health /claims/health", r.status_code == 200 and "final_payout" in r.json(), r.text[:120] if r.status_code != 200 else "")

    # 7. Travel claim
    r = httpx.post(f"{BASE}/claims/travel", json={
        "claimant_name": "Test User", "policy_number": "TR-2025-001",
        "claim_type": "flight_delay", "origin": "Delhi", "destination": "London",
        "departure_date": "20-06-2026", "delay_hours": 5, "baggage_value": 0,
        "cancellation_reason": "", "sum_insured": 10000,
        "description": "Flight delayed 5 hours"
    }, timeout=60)
    check("Travel /claims/travel", r.status_code == 200 and "final_payout" in r.json(), r.text[:120] if r.status_code != 200 else "")

    # 8. Orchestrator -- general query
    r = httpx.post(f"{BASE}/automation/run", json={
        "message": "What does my motor policy cover?"
    }, timeout=60)
    check("Orchestrator general query", r.status_code == 200 and "final_report" in r.json(), r.text[:120] if r.status_code != 200 else "")

    # 9. Orchestrator -- file claim (stateful)
    r = httpx.post(f"{BASE}/automation/run", json={
        "message": "I had an accident, policy DG-MOTOR-2025-042"
    }, timeout=60)
    if r.status_code == 200:
        data = r.json()
        fraud_agent = next((a for a in data.get("agents_run", []) if a["agent_name"] == "Fraud Detector"), None)
        check("Orchestrator file_claim + fraud", fraud_agent is not None and "previous claims" in fraud_agent.get("summary", ""), r.text[:120] if not fraud_agent else "")
    else:
        check("Orchestrator file_claim + fraud", False, r.text[:120])

    # 10. Orchestrator -- renewal with real DB context
    r = httpx.post(f"{BASE}/automation/run", json={
        "message": "I want to renew policy DG-MOTOR-2025-042"
    }, timeout=60)
    if r.status_code == 200:
        data = r.json()
        renewal_agent = next((a for a in data.get("agents_run", []) if a["agent_name"] == "Renewal Agent"), None)
        check("Orchestrator renewal (DB context)", renewal_agent is not None and renewal_agent.get("status") == "success", r.text[:120] if not renewal_agent else "")
    else:
        check("Orchestrator renewal (DB context)", False, r.text[:120])

    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed out of {PASS+FAIL} tests")
    if FAIL:
        sys.exit(1)

if __name__ == "__main__":
    main()
