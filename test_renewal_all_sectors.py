"""Test renewal API for all 4 insurance sectors."""
import urllib.request
import json

API = "http://127.0.0.1:8000/renewal/negotiate"

TESTS = [
    {
        "label": "MOTOR",
        "payload": {
            "current_policy": {
                "provider_name": "ICICI Lombard",
                "annual_premium": 15000,
                "sum_insured": 500000,
                "coverage_type": "Comprehensive",
                "years_with_provider": 3,
                "claim_free_years": 2,
                "deductible": 0,
                "addons": [],
            },
            "user_profile": {
                "name": "Ramesh",
                "age": 35,
                "city": "Mumbai",
                "insurance_type": "motor",
                "risk_score": 0,
            },
        },
    },
    {
        "label": "HEALTH",
        "payload": {
            "current_policy": {
                "provider_name": "Star Health",
                "annual_premium": 20000,
                "sum_insured": 1000000,
                "coverage_type": "Family Floater",
                "years_with_provider": 2,
                "claim_free_years": 1,
                "deductible": 0,
                "addons": [],
            },
            "user_profile": {
                "name": "Priya",
                "age": 28,
                "city": "Bangalore",
                "insurance_type": "health",
                "risk_score": 0,
            },
        },
    },
    {
        "label": "TRAVEL",
        "payload": {
            "current_policy": {
                "provider_name": "Tata AIG",
                "annual_premium": 8000,
                "sum_insured": 2500000,
                "coverage_type": "Multi-trip",
                "years_with_provider": 1,
                "claim_free_years": 1,
                "deductible": 0,
                "addons": [],
            },
            "user_profile": {
                "name": "Anil",
                "age": 45,
                "city": "Delhi",
                "insurance_type": "travel",
                "risk_score": 0,
            },
        },
    },
    {
        "label": "CROP",
        "payload": {
            "current_policy": {
                "provider_name": "New India Assurance",
                "annual_premium": 5000,
                "sum_insured": 200000,
                "coverage_type": "PMFBY",
                "years_with_provider": 4,
                "claim_free_years": 3,
                "deductible": 0,
                "addons": [],
            },
            "user_profile": {
                "name": "Suresh",
                "age": 50,
                "city": "Nagpur",
                "insurance_type": "crop",
                "risk_score": 0,
            },
        },
    },
]


def test_sector(test):
    label = test["label"]
    data = json.dumps(test["payload"]).encode()
    req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        r = json.loads(resp.read())
        print(f"\n{'='*60}")
        print(f"  {label} INSURANCE")
        print(f"{'='*60}")
        print(f"  Status:    OK (200)")
        print(f"  Quotes:    {len(r['all_quotes'])}")
        print(f"  Best Deal: {r['best_deal']['provider_name']}")
        print(f"  Premium:   {r['best_deal']['negotiated_premium']}")
        print(f"  Cover:     {r['best_deal']['sum_insured']}")
        print(f"  Savings:   {r['savings_amount']} ({r['savings_pct']}%)")
        print(f"  Switch:    {r['switch_recommended']}")
        print(f"  Confidence:{r['confidence']}")
        print(f"  Degraded:  {r['degraded']}")
        print(f"  Providers: ", end="")
        for q in r["all_quotes"]:
            tag = " *" if q["recommended"] else ""
            print(f"{q['provider_name']}({q['negotiated_premium']}, cover={q['sum_insured']}){tag}", end=" | ")
        print()
        return True
    except Exception as e:
        print(f"\n  {label}: FAILED - {e}")
        return False


if __name__ == "__main__":
    print("Testing Renewal API for all 4 insurance sectors...\n")
    results = []
    for t in TESTS:
        results.append(test_sector(t))

    print(f"\n{'='*60}")
    print(f"  SUMMARY: {sum(results)}/4 sectors passed")
    print(f"{'='*60}")
