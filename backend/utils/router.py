def route_query(query: str) -> str:
    """Route the user query to the appropriate module based on keywords."""
    q = query.lower()

    # Motor claims — require more specific vehicle/accident keywords
    motor_keywords = ["vehicle damage", "car accident", "car damage", "motor claim",
                      "collision", "dent", "scratch", "repair cost", "fender"]
    if any(kw in q for kw in motor_keywords):
        return "motor_claim"

    # Fraud detection
    if any(kw in q for kw in ["fraud", "suspicious", "fake claim", "fraudulent"]):
        return "fraud_detection"

    # Risk profiler
    if any(kw in q for kw in ["risk score", "risk profile", "risk assess", "bmi",
                              "lifestyle risk", "health risk"]):
        return "risk_profiler"

    # Crop insurance
    if any(kw in q for kw in ["crop", "weather", "harvest", "agricultural",
                              "crop insurance", "rainfall"]):
        return "crop_payout"

    # Renewal comparison
    if any(kw in q for kw in ["renew", "renewal", "compare plans",
                              "switch policy", "better plan"]):
        return "renewal_agent"

    # Default: policy RAG — this covers all general insurance questions
    return "policy_rag"
