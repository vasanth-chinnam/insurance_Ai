from backend.db import init_db, create_user, create_policy

init_db()

# User 1
create_user("U001", "Vasanth Kumar", "vasanth@example.com", "9999999999")
create_policy(
    policy_id="DG-MOTOR-2025-042",
    user_id="U001",
    insurance_type="motor",
    provider="HDFC Ergo",
    sum_insured=500000,
    annual_premium=12000,
    years_with_provider=3,
    claim_free_years=2,
)
create_policy(
    policy_id="TR-2025-042",
    user_id="U001",
    insurance_type="travel",
    provider="TATA AIG",
    sum_insured=20000,
    annual_premium=1500,
    years_with_provider=2,
    claim_free_years=1,
)

# User 2
create_user("U002", "Priya Patel", "priya@example.com", "8888888888")
create_policy(
    policy_id="HL-2025-001",
    user_id="U002",
    insurance_type="health",
    provider="Star Health",
    sum_insured=500000,
    annual_premium=15000,
    years_with_provider=5,
    claim_free_years=5,
)
create_policy(
    policy_id="HL-2025-042",
    user_id="U002",
    insurance_type="health",
    provider="Star Health",
    sum_insured=500000,
    annual_premium=15000,
    years_with_provider=5,
    claim_free_years=5,
)
create_policy(
    policy_id="TR-2025-001",
    user_id="U002",
    insurance_type="travel",
    provider="TATA AIG",
    sum_insured=20000,
    annual_premium=1500,
    years_with_provider=2,
    claim_free_years=1,
)

print("Demo data seeded successfully")
