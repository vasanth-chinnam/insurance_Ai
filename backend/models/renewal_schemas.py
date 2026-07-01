from pydantic import BaseModel, Field


class CurrentPolicy(BaseModel):
    provider_name:   str
    annual_premium:  float
    sum_insured:     float
    coverage_type:   str
    years_with_provider: int = Field(0, description="Years with current provider")
    claim_free_years:    int = Field(0, description="Years without a claim")
    deductible:      float = Field(0)
    addons:          list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    name:            str
    age:             int
    city:            str
    insurance_type:  str   # motor | health | travel | crop
    risk_score:      int   = Field(0, description="From Phase 4 Risk Profiler (0-100)")


class ProviderQuote(BaseModel):
    provider_id:          str
    provider_name:        str
    rating:               float
    claim_settlement_ratio: float
    annual_premium:       float
    negotiated_premium:   float
    sum_insured:          float
    savings_vs_current:   float
    savings_pct:          float
    loyalty_discount:     float
    ncb_discount:         float
    total_discount:       float
    coverage_score:       int        # 0-100
    value_score:          float      # composite score
    strengths:            list[str]
    recommended:          bool


class RenewalRequest(BaseModel):
    current_policy:  CurrentPolicy
    user_profile:    UserProfile


class RenewalResponse(BaseModel):
    user_name:              str
    insurance_type:         str
    current_premium:        float
    best_deal:              ProviderQuote
    all_quotes:             list[ProviderQuote]
    savings_amount:         float
    savings_pct:            float
    negotiation_summary:    str
    recommendation:         str
    switch_recommended:     bool
    confidence:             str
    degraded:               bool
