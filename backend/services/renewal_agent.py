import json
import logging
import random
from pathlib import Path

from backend.models.renewal_schemas import (
    RenewalRequest, RenewalResponse,
    ProviderQuote, CurrentPolicy, UserProfile
)
from backend.services.rag_service import _try_llm_chain
from backend.prompts.renewal_prompt import RENEWAL_PROMPT

logger = logging.getLogger(__name__)

PROVIDERS_DB_PATH = Path("data/mock_db/providers.json")


# ── Load providers ────────────────────────────────────────────────────

def _load_providers() -> list[dict]:
    try:
        with open(PROVIDERS_DB_PATH) as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not load providers DB: %s", e)
        return []


# ── Quote generation ──────────────────────────────────────────────────

def _generate_base_premium(
    provider: dict,
    current_policy: CurrentPolicy,
    user_profile: UserProfile,
    rng: random.Random,
) -> float:
    """
    Generate a highly realistic base premium for a provider based on sum insured and age,
    ensuring it matches real-world market rates (e.g. Star Health 25L sum insured at age 20 ≈ ₹10.5k).
    """
    insurance_type = user_profile.insurance_type.lower()
    sum_insured = current_policy.sum_insured
    age = user_profile.age

    # 1. Calculate standard market premium base for this policy type
    if insurance_type == "health":
        # Base factor starts at 0.35% of sum insured for age 20, scaling with age
        age_factor = 0.0035 + (max(age - 18, 0) / 100) * 0.005
        market_base = sum_insured * age_factor
    elif insurance_type == "motor":
        # Standard motor premium is roughly 2% of IDV (sum insured)
        market_base = sum_insured * 0.02
    elif insurance_type == "crop":
        # Standard crop premium is 2% of sum insured in India (PMFBY)
        market_base = sum_insured * 0.02
    else:
        # Travel is typically flat rate based on trip duration (simulated as low fraction)
        market_base = 1500.0

    # 2. Apply provider specific base multiplier and deterministic market variance (±8%)
    multiplier = provider["base_multipliers"].get(insurance_type, 1.0)
    market_factor = rng.uniform(0.92, 1.08)
    
    base = market_base * multiplier * market_factor
    return round(base, 2)


def _apply_discounts(
    base_premium: float,
    provider: dict,
    current_policy: CurrentPolicy,
    user_profile: UserProfile,
    rng: random.Random,
) -> tuple[float, float, float, float]:
    """
    Apply loyalty discount + NCB discount + negotiation discount using deterministic RNG.
    Returns (negotiated_premium, loyalty_disc, ncb_disc, total_disc)
    """
    loyalty_disc = 0.0
    ncb_disc     = 0.0

    # Loyalty discount — reward years with provider
    if current_policy.years_with_provider >= 3:
        loyalty_disc = (provider["loyalty_discount_pct"] / 100) * base_premium

    # No Claim Bonus — reward claim-free years
    if current_policy.claim_free_years >= 1:
        ncb_rate = min(current_policy.claim_free_years * 0.05, 0.50)
        ncb_disc = ncb_rate * base_premium * (provider["ncb_discount_pct"] / 100)

    # Negotiation discount — agent negotiates 2-5% extra deterministically
    negotiation_disc = rng.uniform(0.02, 0.05) * base_premium

    total_disc       = loyalty_disc + ncb_disc + negotiation_disc
    negotiated       = max(base_premium - total_disc, base_premium * 0.60)

    return (
        round(negotiated, 2),
        round(loyalty_disc, 2),
        round(ncb_disc, 2),
        round(total_disc, 2),
    )


def _calculate_coverage_score(
    provider: dict,
    insurance_type: str,
    current_policy: CurrentPolicy,
) -> int:
    """Score 0-100 based on coverage quality for this insurance type."""
    score = 50

    # Rating boost
    score += int((provider["rating"] - 3.0) * 15)

    # Settlement ratio boost
    if provider["claim_settlement_ratio"] >= 98:
        score += 20
    elif provider["claim_settlement_ratio"] >= 96:
        score += 10

    # Hospital network (health)
    if insurance_type == "health":
        if provider["network_hospitals"] >= 12000:
            score += 15
        elif provider["network_hospitals"] >= 8000:
            score += 8

    # Type-specific multiplier bonus
    mult = provider["base_multipliers"].get(insurance_type, 1.0)
    if mult <= 0.92:
        score += 10  # specialist in this type

    return min(max(score, 0), 100)


def _calculate_value_score(
    quote: dict,
    current_premium: float,
    current_sum_insured: float,
) -> float:
    """
    Composite value score balancing price, coverage, and savings.
    Higher is better.
    """
    savings_weight  = 0.35
    coverage_weight = 0.30
    rating_weight   = 0.20
    sum_insured_weight = 0.15

    savings_norm  = min((current_premium - quote["negotiated_premium"]) / current_premium, 0.5) * 2
    coverage_norm = quote["coverage_score"] / 100
    rating_norm   = (quote["rating"] - 3.5) / 1.5
    sum_insured_norm = min((quote["sum_insured"] - current_sum_insured) / current_sum_insured, 0.5) * 2

    score = (
        savings_norm  * savings_weight +
        coverage_norm * coverage_weight +
        rating_norm   * rating_weight +
        sum_insured_norm * sum_insured_weight
    )
    return round(score, 4)


# ── Quote builder ─────────────────────────────────────────────────────

def _build_quotes(
    request: RenewalRequest,
) -> list[ProviderQuote]:
    providers      = _load_providers()
    insurance_type = request.user_profile.insurance_type
    current        = request.current_policy

    # Setup stable seed string from input properties to remove random price fluctuations
    seed_str = f"{request.user_profile.name.lower().strip()}_{request.user_profile.age}_{request.user_profile.city.lower().strip()}_{request.current_policy.provider_name.lower().strip()}_{request.current_policy.annual_premium}_{request.current_policy.sum_insured}"
    
    import hashlib
    seed_bytes = hashlib.sha256(seed_str.encode('utf-8')).digest()
    seed_int = int.from_bytes(seed_bytes, byteorder='big')
    rng = random.Random(seed_int)

    quotes         = []

    for provider in providers:
        base_premium = _generate_base_premium(provider, current, request.user_profile, rng)

        negotiated, loyalty_disc, ncb_disc, total_disc = _apply_discounts(
            base_premium, provider, current, request.user_profile, rng
        )

        savings_vs_current = round(current.annual_premium - negotiated, 2)
        savings_pct        = round((savings_vs_current / current.annual_premium) * 100, 1)
        coverage_score     = _calculate_coverage_score(provider, insurance_type, current)

        # Add variation to sum insured (some providers offer a bonus to win the customer)
        bonus_factor = rng.choice([1.0, 1.0, 1.05, 1.10, 1.15])
        offered_sum_insured = int(current.sum_insured * bonus_factor)

        quote_dict = {
            "provider_id":             provider["provider_id"],
            "provider_name":           provider["name"],
            "rating":                  provider["rating"],
            "claim_settlement_ratio":  provider["claim_settlement_ratio"],
            "annual_premium":          base_premium,
            "negotiated_premium":      negotiated,
            "sum_insured":             offered_sum_insured,
            "savings_vs_current":      savings_vs_current,
            "savings_pct":             savings_pct,
            "loyalty_discount":        loyalty_disc,
            "ncb_discount":            ncb_disc,
            "total_discount":          total_disc,
            "coverage_score":          coverage_score,
            "value_score":             0.0,
            "strengths":               provider["strengths"],
            "recommended":             False,
        }

        quote_dict["value_score"] = _calculate_value_score(
            quote_dict, current.annual_premium, current.sum_insured
        )
        quotes.append(quote_dict)

    # Sort by value score descending
    quotes.sort(key=lambda q: q["value_score"], reverse=True)

    # Mark best deal
    if quotes:
        quotes[0]["recommended"] = True

    return [ProviderQuote(**q) for q in quotes]


# ── Negotiation summary ───────────────────────────────────────────────

def _generate_summary(
    request: RenewalRequest,
    quotes: list[ProviderQuote],
    best: ProviderQuote,
) -> tuple[str, bool]:

    context = f"""
User: {request.user_profile.name} | Age: {request.user_profile.age} | City: {request.user_profile.city}
Insurance Type: {request.user_profile.insurance_type.title()}
Current Provider: {request.current_policy.provider_name}
Current Annual Premium: ₹{request.current_policy.annual_premium:,.0f}
Years with Provider: {request.current_policy.years_with_provider}
Claim-free Years: {request.current_policy.claim_free_years}

Best Deal Found:
Provider: {best.provider_name}
Negotiated Premium: ₹{best.negotiated_premium:,.0f}
Savings: ₹{best.savings_vs_current:,.0f} ({best.savings_pct}%)
Rating: {best.rating}/5
Claim Settlement: {best.claim_settlement_ratio}%
Strengths: {', '.join(best.strengths)}
Coverage Score: {best.coverage_score}/100

All Providers Compared: {len(quotes)}
Premium Range: ₹{min(q.negotiated_premium for q in quotes):,.0f} – ₹{max(q.negotiated_premium for q in quotes):,.0f}
"""

    is_current_provider = best.provider_name.lower().strip() == request.current_policy.provider_name.lower().strip()

    if is_current_provider:
        question = (
            f"Should {request.user_profile.name} renew with {best.provider_name} "
            f"and save ₹{best.savings_vs_current:,.0f} via the negotiated discount?"
        )
    else:
        question = (
            f"Should {request.user_profile.name} switch to {best.provider_name} "
            f"and save ₹{best.savings_vs_current:,.0f}?"
        )

    answer = _try_llm_chain(
        context         = context,
        question        = question,
        prompt_template = RENEWAL_PROMPT,
    )

    if answer is None:
        switch = best.savings_vs_current > 0
        if switch:
            rec_action = "Renewing with your current provider is recommended." if is_current_provider else "Switching is recommended."
            return (
                f"Agent compared {len(quotes)} providers and found {best.provider_name} "
                f"offers the best value at ₹{best.negotiated_premium:,.0f}/year — "
                f"saving you ₹{best.savings_vs_current:,.0f} ({best.savings_pct}%) "
                f"vs your current premium. "
                f"Rating: {best.rating}/5 with {best.claim_settlement_ratio}% claim settlement ratio. "
                f"Strengths: {', '.join(best.strengths[:2])}. "
                f"{rec_action}"
            ), True
        else:
            return (
                f"After comparing {len(quotes)} providers, your current insurer "
                f"({request.current_policy.provider_name}) remains competitive. "
                f"Best alternative is {best.provider_name} at ₹{best.negotiated_premium:,.0f}/year. "
                f"Consider renewing with your current provider."
            ), True

    return answer, False


# ── Main entry point ──────────────────────────────────────────────────

def run_renewal_agent(request: RenewalRequest) -> RenewalResponse:
    """
    Renewal negotiation pipeline:
    1. Generate quotes from all providers
    2. Apply negotiation discounts
    3. Score and rank all quotes
    4. Pick best deal
    5. Generate LLM summary
    """

    # Step 1 + 2 + 3 — Quotes with negotiation
    quotes = _build_quotes(request)

    if not quotes:
        return RenewalResponse(
            user_name           = request.user_profile.name,
            insurance_type      = request.user_profile.insurance_type,
            current_premium     = request.current_policy.annual_premium,
            best_deal           = ProviderQuote(
                provider_id="N/A", provider_name="N/A",
                rating=0, claim_settlement_ratio=0,
                annual_premium=0, negotiated_premium=0,
                sum_insured=0, savings_vs_current=0,
                savings_pct=0, loyalty_discount=0,
                ncb_discount=0, total_discount=0,
                coverage_score=0, value_score=0,
                strengths=[], recommended=False,
            ),
            all_quotes          = [],
            savings_amount      = 0,
            savings_pct         = 0,
            negotiation_summary = "No providers available.",
            recommendation      = "Please try again later.",
            switch_recommended  = False,
            confidence          = "Low",
            degraded            = True,
        )

    # Step 4 — Best deal
    best = quotes[0]

    # Step 5 — LLM summary
    summary, degraded = _generate_summary(request, quotes, best)

    savings_amount = best.savings_vs_current
    savings_pct    = best.savings_pct
    switch         = savings_amount > 500  # switch only if saving > ₹500

    confidence = (
        "High"   if len(quotes) >= 6 else
        "Medium" if len(quotes) >= 3 else
        "Low"
    )

    is_current_provider = best.provider_name.lower().strip() == request.current_policy.provider_name.lower().strip()
    if switch:
        if is_current_provider:
            recommendation = f"Renew with {best.provider_name} and save ₹{savings_amount:,.0f}/year"
        else:
            recommendation = f"Switch to {best.provider_name} and save ₹{savings_amount:,.0f}/year"
    else:
        recommendation = f"Renew with {request.current_policy.provider_name} — current deal is competitive"

    return RenewalResponse(
        user_name           = request.user_profile.name,
        insurance_type      = request.user_profile.insurance_type,
        current_premium     = request.current_policy.annual_premium,
        best_deal           = best,
        all_quotes          = quotes,
        savings_amount      = round(savings_amount, 2),
        savings_pct         = round(savings_pct, 1),
        negotiation_summary = summary,
        recommendation      = recommendation,
        switch_recommended  = switch,
        confidence          = confidence,
        degraded            = degraded,
    )
