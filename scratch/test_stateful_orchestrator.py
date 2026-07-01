import httpx
import json

url = "http://127.0.0.1:8000/automation/run"
payload = {"message": "I had an accident, policy DG-MOTOR-2025-042"}

def run_test():
    print("=== RUN 1 ===")
    try:
        r1 = httpx.post(url, json=payload, timeout=60.0)
        print("Status Code:", r1.status_code)
        if r1.status_code == 200:
            data = r1.json()
            fraud_agent = next((a for a in data["agents_run"] if a["agent_name"] == "Fraud Detector"), None)
            if fraud_agent:
                print("Fraud Detector Summary:", fraud_agent["summary"])
                print("Fraud Result Reasons:", fraud_agent["data"]["reasons"])
            else:
                print("Fraud Detector agent did not run.")
        else:
            print("Error:", r1.text)
    except Exception as e:
        print("Run 1 failed:", e)

    print("\n=== RUN 2 ===")
    try:
        r2 = httpx.post(url, json=payload, timeout=60.0)
        print("Status Code:", r2.status_code)
        if r2.status_code == 200:
            data = r2.json()
            fraud_agent = next((a for a in data["agents_run"] if a["agent_name"] == "Fraud Detector"), None)
            if fraud_agent:
                print("Fraud Detector Summary:", fraud_agent["summary"])
                print("Fraud Result Reasons:", fraud_agent["data"]["reasons"])
            else:
                print("Fraud Detector agent did not run.")
        else:
            print("Error:", r2.text)
    except Exception as e:
        print("Run 2 failed:", e)

if __name__ == "__main__":
    run_test()
