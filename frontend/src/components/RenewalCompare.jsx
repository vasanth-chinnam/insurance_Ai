import { useState } from "react"

const INSURANCE_TYPES = [
  { value: "motor",  label: "Motor",  icon: "🚗" },
  { value: "health", label: "Health", icon: "🏥" },
  { value: "travel", label: "Travel", icon: "✈️" },
  { value: "crop",   label: "Crop",   icon: "🌾" },
]

const LOADING_STEPS = [
  "Contacting insurance providers...",
  "Collecting quotes from 8 insurers...",
  "Applying negotiation discounts...",
  "Scoring and ranking all deals...",
  "Preparing your savings report...",
]

export default function RenewalCompare() {
  const [insuranceType, setType]   = useState("motor")
  const [form, setForm]            = useState({
    user_name:            "",
    user_age:             "",
    user_city:            "",
    provider_name:        "",
    annual_premium:       "",
    sum_insured:          "",
    coverage_type:        "Comprehensive",
    years_with_provider:  "",
    claim_free_years:     "",
  })
  const [result, setResult]        = useState(null)
  const [loading, setLoading]      = useState(false)
  const [loadingStep, setStep]     = useState(0)
  const [error, setError]          = useState(null)

  const runLoadingSteps = () => {
    LOADING_STEPS.forEach((_, i) => setTimeout(() => setStep(i), i * 900))
  }

  const handleSubmit = async () => {
    setLoading(true)
    setResult(null)
    setError(null)
    runLoadingSteps()
    try {
      const res = await fetch("/renewal/negotiate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_policy: {
            provider_name:          form.provider_name,
            annual_premium:         parseFloat(form.annual_premium),
            sum_insured:            parseFloat(form.sum_insured),
            coverage_type:          form.coverage_type,
            years_with_provider:    parseInt(form.years_with_provider || "0"),
            claim_free_years:       parseInt(form.claim_free_years || "0"),
            deductible:             0,
            addons:                 [],
          },
          user_profile: {
            name:           form.user_name,
            age:            parseInt(form.user_age),
            city:           form.user_city,
            insurance_type: insuranceType,
            risk_score:     0,
          },
        }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      setResult(await res.json())
    } catch (e) {
      setError(e.message || "Analysis failed.")
    } finally {
      setLoading(false)
    }
  }

  const inp = (field, placeholder, type = "text") => (
    <div>
      <label style={{ fontSize: 12, color: "#6B7280" }}>
        {field.replace(/_/g, " ").toUpperCase()}
      </label>
      <input
        type={type}
        value={form[field]}
        placeholder={placeholder}
        onChange={e => setForm({ ...form, [field]: e.target.value })}
        style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
          border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}
      />
    </div>
  )

  return (
    <div style={{ height: "100%", width: "100%", overflowY: "auto" }}>
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "24px 16px" }}>
      <h2 style={{ fontWeight: 600, marginBottom: 4 }}>Renewal Compare</h2>
      <p style={{ color: "#6B7280", marginBottom: 20 }}>
        AI agent negotiates with 8 insurers to find your best renewal deal
      </p>

      {/* Insurance type selector */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {INSURANCE_TYPES.map(t => (
          <button key={t.value} onClick={() => setType(t.value)}
            style={{
              padding: "8px 16px", borderRadius: 8, fontWeight: 500,
              border: insuranceType === t.value ? "2px solid #2563EB" : "1px solid #E5E7EB",
              background: insuranceType === t.value ? "#EFF6FF" : "#fff",
              color: insuranceType === t.value ? "#2563EB" : "#374151",
              cursor: "pointer"
            }}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Form */}
      <div style={{ background: "#F9FAFB", borderRadius: 12,
        padding: "20px 24px", marginBottom: 16 }}>
        <p style={{ fontWeight: 600, marginBottom: 16 }}>Your Details</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {inp("user_name",           "Vasanth Kumar")}
          {inp("user_age",            "30",          "number")}
          {inp("user_city",           "Hyderabad")}
          {inp("provider_name",       "Current Insurer")}
          {inp("annual_premium",      "12000",       "number")}
          {inp("sum_insured",         "500000",      "number")}
          {inp("years_with_provider", "2",           "number")}
          {inp("claim_free_years",    "1",           "number")}
        </div>
      </div>

      <button onClick={handleSubmit} disabled={loading}
        style={{ width: "100%", padding: 12, borderRadius: 8,
          background: loading ? "#93C5FD" : "#2563EB",
          color: "#fff", fontWeight: 600, fontSize: 15,
          border: "none", cursor: "pointer", marginBottom: 16 }}>
        {loading ? "Negotiating..." : "Find Best Deal 🔍"}
      </button>

      {/* Loading steps */}
      {loading && (
        <div style={{ textAlign: "center", padding: "16px 0" }}>
          <p style={{ color: "#6B7280", marginBottom: 10 }}>
            {LOADING_STEPS[loadingStep]}
          </p>
          <div style={{ display: "flex", gap: 6, justifyContent: "center" }}>
            {LOADING_STEPS.map((_, i) => (
              <div key={i} style={{
                width: 8, height: 8, borderRadius: "50%",
                background: i <= loadingStep ? "#2563EB" : "#E5E7EB",
                transition: "background 0.3s"
              }}/>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div style={{ padding: 12, background: "#FEE2E2",
          borderRadius: 8, color: "#DC2626", marginBottom: 12 }}>{error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 8 }}>

          {/* Savings banner */}
          <div style={{
            background: result.switch_recommended ? "#DCFCE7" : "#EFF6FF",
            border: `1px solid ${result.switch_recommended ? "#86EFAC" : "#BFDBFE"}`,
            borderRadius: 12, padding: "20px 24px", marginBottom: 16,
            display: "flex", justifyContent: "space-between", alignItems: "center",
            flexWrap: "wrap", gap: 12
          }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 500,
                color: result.switch_recommended ? "#16A34A" : "#1E40AF" }}>
                {result.switch_recommended ? "💰 BETTER DEAL FOUND" : "✅ CURRENT DEAL IS COMPETITIVE"}
              </div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4,
                color: result.switch_recommended ? "#16A34A" : "#1E40AF" }}>
                {result.recommendation}
              </div>
              <div style={{ fontSize: 13, marginTop: 4,
                color: result.switch_recommended ? "#16A34A" : "#1E40AF" }}>
                Compared {result.all_quotes.length} providers · Confidence: {result.confidence}
              </div>
            </div>
            {result.switch_recommended && (
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 36, fontWeight: 700, color: "#16A34A" }}>
                  ₹{result.savings_amount.toLocaleString("en-IN")}
                </div>
                <div style={{ fontSize: 13, color: "#16A34A" }}>
                  saved per year ({result.savings_pct}%)
                </div>
              </div>
            )}
          </div>

          {/* Best deal card */}
          <div style={{ background: "#F0FDF4", border: "2px solid #86EFAC",
            borderRadius: 12, padding: "16px 20px", marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between",
              alignItems: "flex-start", marginBottom: 12, flexWrap: "wrap", gap: 12 }}>
              <div>
                <span style={{ fontSize: 11, background: "#16A34A",
                  color: "#fff", padding: "2px 8px",
                  borderRadius: 999, fontWeight: 500 }}>
                  BEST DEAL
                </span>
                <div style={{ fontSize: 20, fontWeight: 700, marginTop: 6 }}>
                  {result.best_deal.provider_name}
                </div>
                <div style={{ fontSize: 13, color: "#6B7280", marginTop: 2 }}>
                  ⭐ {result.best_deal.rating}/5 · {result.best_deal.claim_settlement_ratio}% settlement · ₹{result.best_deal.sum_insured.toLocaleString("en-IN")} cover
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#16A34A" }}>
                  ₹{result.best_deal.negotiated_premium.toLocaleString("en-IN")}
                </div>
                <div style={{ fontSize: 12, color: "#6B7280" }}>/year (negotiated)</div>
                <div style={{ fontSize: 12, color: "#16A34A", marginTop: 2 }}>
                  ₹{result.best_deal.total_discount.toLocaleString("en-IN")} discount applied
                </div>
              </div>
            </div>

            {/* Discount breakdown */}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {result.best_deal.loyalty_discount > 0 && (
                <span style={{ fontSize: 12, background: "#DCFCE7",
                  color: "#16A34A", padding: "4px 10px", borderRadius: 999 }}>
                  Loyalty: -₹{result.best_deal.loyalty_discount.toLocaleString("en-IN")}
                </span>
              )}
              {result.best_deal.ncb_discount > 0 && (
                <span style={{ fontSize: 12, background: "#DCFCE7",
                  color: "#16A34A", padding: "4px 10px", borderRadius: 999 }}>
                  NCB: -₹{result.best_deal.ncb_discount.toLocaleString("en-IN")}
                </span>
              )}
              <span style={{ fontSize: 12, background: "#DCFCE7",
                color: "#16A34A", padding: "4px 10px", borderRadius: 999 }}>
                Negotiated: extra discount applied
              </span>
            </div>

            {/* Strengths */}
            <div style={{ marginTop: 12, display: "flex", gap: 6, flexWrap: "wrap" }}>
              {result.best_deal.strengths.map((s, i) => (
                <span key={i} style={{ fontSize: 12, background: "#F0FDF4",
                  border: "1px solid #86EFAC", color: "#166534",
                  padding: "3px 10px", borderRadius: 999 }}>
                  ✓ {s}
                </span>
              ))}
            </div>
          </div>

          {/* All providers table */}
          <div style={{ background: "#F9FAFB", borderRadius: 12,
            padding: "16px 20px", marginBottom: 16 }}>
            <div style={{ fontWeight: 600, marginBottom: 12 }}>
              All Providers Compared ({result.all_quotes.length})
            </div>

            {/* Header */}
            <div style={{ display: "grid",
              gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr",
              gap: 8, fontSize: 11, color: "#9CA3AF",
              fontWeight: 600, marginBottom: 8,
              padding: "0 8px" }}>
              <span>PROVIDER</span>
              <span style={{ textAlign: "right" }}>PREMIUM</span>
              <span style={{ textAlign: "right" }}>SAVINGS</span>
              <span style={{ textAlign: "center" }}>RATING</span>
              <span style={{ textAlign: "center" }}>SCORE</span>
            </div>

            {result.all_quotes.map((q, i) => (
              <div key={i} style={{
                display: "grid",
                gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr",
                gap: 8, alignItems: "center",
                padding: "10px 8px",
                background: q.recommended ? "#F0FDF4" : "transparent",
                borderRadius: 8,
                border: q.recommended ? "1px solid #86EFAC" : "none",
                marginBottom: 4,
              }}>
                <div style={{ fontWeight: q.recommended ? 600 : 400, fontSize: 14 }}>
                  {q.recommended && <span style={{ color: "#16A34A" }}>★ </span>}
                  {q.provider_name}
                  <div style={{ fontSize: 11, color: "#6B7280", marginTop: 2, fontWeight: 400 }}>
                    ₹{q.sum_insured.toLocaleString("en-IN")} cover
                  </div>
                </div>
                <div style={{ textAlign: "right", fontSize: 14, fontWeight: 500 }}>
                  ₹{q.negotiated_premium.toLocaleString("en-IN")}
                </div>
                <div style={{ textAlign: "right", fontSize: 13,
                  color: q.savings_vs_current > 0 ? "#16A34A" : "#DC2626" }}>
                  {q.savings_vs_current > 0 ? "-" : "+"}
                  ₹{Math.abs(q.savings_vs_current).toLocaleString("en-IN")}
                </div>
                <div style={{ textAlign: "center", fontSize: 13 }}>
                  ⭐ {q.rating}
                </div>
                <div style={{ textAlign: "center" }}>
                  <span style={{
                    fontSize: 12,
                    background: q.value_score >= 0.8 ? "#DCFCE7"
                              : q.value_score >= 0.6 ? "#FEF3C3" : "#FEE2E2",
                    color: q.value_score >= 0.8 ? "#16A34A"
                         : q.value_score >= 0.6 ? "#92400E" : "#DC2626",
                    padding: "2px 8px", borderRadius: 999
                  }}>
                    {Math.round(q.value_score * 100)}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Negotiation summary */}
          <div style={{ background: "#F9FAFB", borderRadius: 10,
            padding: "16px 20px", marginBottom: 16 }}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>
              Agent Negotiation Summary
              {result.degraded && (
                <span style={{ marginLeft: 8, fontSize: 11,
                  background: "#FEF3C3", color: "#92400E",
                  padding: "2px 8px", borderRadius: 999 }}>Offline Mode</span>
              )}
            </div>
            <p style={{ fontSize: 14, color: "#374151",
              lineHeight: 1.6, margin: 0, whiteSpace: "pre-wrap" }}>
              {result.negotiation_summary}
            </p>
          </div>

          {/* Accept deal button */}
          {result.switch_recommended && (
            <button
              onClick={() => alert(`Deal accepted! Switching to ${result.best_deal.provider_name}. Our agent will contact you within 24 hours.`)}
              style={{ width: "100%", padding: 14, borderRadius: 8,
                background: "#16A34A", color: "#fff",
                fontWeight: 600, fontSize: 15, border: "none", cursor: "pointer" }}>
              ✓ Accept Best Deal — Switch to {result.best_deal.provider_name}
            </button>
          )}

        </div>
      )}
    </div>
    </div>
  )
}
