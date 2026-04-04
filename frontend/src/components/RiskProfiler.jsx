import { useState } from "react"

const RISK_COLORS = {
  Low:       { color: "#16A34A", bg: "#DCFCE7", border: "#86EFAC" },
  Medium:    { color: "#D97706", bg: "#FEF3C3", border: "#FCD34D" },
  High:      { color: "#EA580C", bg: "#FFEDD5", border: "#FDBA74" },
  "Very High": { color: "#DC2626", bg: "#FEE2E2", border: "#FCA5A5" },
}

const IMPACT_COLORS = {
  High:   "#DC2626",
  Medium: "#D97706",
  Low:    "#16A34A",
}

const INSURANCE_TYPES = [
  { value: "health",  label: "Health",  icon: "🏥" },
  { value: "motor",   label: "Motor",   icon: "🚗" },
  { value: "travel",  label: "Travel",  icon: "✈️" },
  { value: "crop",    label: "Crop",    icon: "🌾" },
]

const LOADING_STEPS = [
  "Collecting risk data...",
  "Running domain risk rules...",
  "Calculating risk score...",
  "Generating premium recommendation...",
]

// ── Domain forms ──────────────────────────────────────────────────────

function HealthForm({ data, onChange }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      {[
        { key: "age",               label: "Age",                  type: "number" },
        { key: "bmi",               label: "BMI",                  type: "number" },
        { key: "exercise_frequency",label: "Exercise days/week",   type: "number" },
        { key: "alcohol_units",     label: "Alcohol units/week",   type: "number" },
      ].map(f => (
        <div key={f.key}>
          <label style={{ fontSize: 12, color: "#6B7280" }}>{f.label.toUpperCase()}</label>
          <input type={f.type} value={data[f.key] ?? ""}
            onChange={e => {
              let val = e.target.value;
              if (f.type === "number") {
                val = val === "" ? "" : +val;
                if (f.key === "alcohol_units" && val !== "") val = Math.min(val, 100);
              }
              onChange({ ...data, [f.key]: val });
            }}
            style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
              border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
        </div>
      ))}
      {[
        { key: "smoker",          label: "Smoker" },
        { key: "diabetic",        label: "Diabetic" },
        { key: "hypertension",    label: "Hypertension" },
        { key: "heart_condition", label: "Heart condition" },
        { key: "family_history",  label: "Family history of illness" },
      ].map(f => (
        <label key={f.key} style={{ display: "flex", alignItems: "center",
          gap: 8, fontSize: 14, cursor: "pointer" }}>
          <input type="checkbox" checked={!!data[f.key]}
            onChange={e => onChange({ ...data, [f.key]: e.target.checked })}/>
          {f.label}
        </label>
      ))}
    </div>
  )
}

function MotorForm({ data, onChange }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      {[
        { key: "age",                label: "Driver age",          type: "number" },
        { key: "vehicle_age",        label: "Vehicle age (years)", type: "number" },
        { key: "accidents_last_5yr", label: "Accidents (5 years)", type: "number" },
        { key: "traffic_violations", label: "Violations (3 years)",type: "number" },
        { key: "annual_km",          label: "Annual km driven",    type: "number" },
      ].map(f => (
        <div key={f.key}>
          <label style={{ fontSize: 12, color: "#6B7280" }}>{f.label.toUpperCase()}</label>
          <input type="number" value={data[f.key] ?? ""}
            onChange={e => onChange({ ...data, [f.key]: e.target.value === "" ? "" : +e.target.value })}
            style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
              border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
        </div>
      ))}
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>VEHICLE TYPE</label>
        <select value={data.vehicle_type || "sedan"}
          onChange={e => onChange({ ...data, vehicle_type: e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4 }}>
          {["sedan","suv","bike","truck"].map(v => (
            <option key={v} value={v}>{v.charAt(0).toUpperCase() + v.slice(1)}</option>
          ))}
        </select>
      </div>
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>PARKING</label>
        <select value={data.parking || "street"}
          onChange={e => onChange({ ...data, parking: e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4 }}>
          {["garage","street","open"].map(v => (
            <option key={v} value={v}>{v.charAt(0).toUpperCase() + v.slice(1)}</option>
          ))}
        </select>
      </div>
      <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14, cursor: "pointer" }}>
        <input type="checkbox" checked={!!data.night_driving}
          onChange={e => onChange({ ...data, night_driving: e.target.checked })}/>
        Regular night driving
      </label>
    </div>
  )
}

function TravelForm({ data, onChange }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      {[
        { key: "age",               label: "Age",                type: "number" },
        { key: "trips_per_year",    label: "Trips per year",     type: "number" },
        { key: "avg_trip_duration", label: "Avg trip days",      type: "number" },
      ].map(f => (
        <div key={f.key}>
          <label style={{ fontSize: 12, color: "#6B7280" }}>{f.label.toUpperCase()}</label>
          <input type="number" value={data[f.key] ?? ""}
            onChange={e => onChange({ ...data, [f.key]: e.target.value === "" ? "" : +e.target.value })}
            style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
              border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
        </div>
      ))}
      <div style={{ gridColumn: "1 / -1" }}>
        <label style={{ fontSize: 12, color: "#6B7280" }}>DESTINATIONS (comma separated)</label>
        <input value={(data.destinations || []).join(", ")}
          onChange={e => onChange({
            ...data,
            destinations: e.target.value.split(",").map(d => d.trim()).filter(Boolean)
          })}
          placeholder="usa, uk, thailand"
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
      </div>
      {[
        { key: "adventure_sports", label: "Adventure sports" },
        { key: "pre_existing",     label: "Pre-existing conditions" },
        { key: "business_travel",  label: "Business travel" },
      ].map(f => (
        <label key={f.key} style={{ display: "flex", alignItems: "center",
          gap: 8, fontSize: 14, cursor: "pointer" }}>
          <input type="checkbox" checked={!!data[f.key]}
            onChange={e => onChange({ ...data, [f.key]: e.target.checked })}/>
          {f.label}
        </label>
      ))}
    </div>
  )
}

function CropForm({ data, onChange }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>CROP TYPE</label>
        <select value={data.crop_type || "wheat"}
          onChange={e => onChange({ ...data, crop_type: e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4 }}>
          {["wheat","rice","cotton","sugarcane","vegetables"].map(v => (
            <option key={v} value={v}>{v.charAt(0).toUpperCase() + v.slice(1)}</option>
          ))}
        </select>
      </div>
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>LAND AREA (ACRES)</label>
        <input type="number" value={data.land_area_acres ?? ""}
            onChange={e => onChange({ ...data, land_area_acres: e.target.value === "" ? "" : +e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
      </div>
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>STATE</label>
        <input value={data.location_state || ""}
          onChange={e => onChange({ ...data, location_state: e.target.value })}
          placeholder="Maharashtra"
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
      </div>
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>IRRIGATION</label>
        <select value={data.irrigation || "rainfed"}
          onChange={e => onChange({ ...data, irrigation: e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4 }}>
          {["rainfed","partial","full"].map(v => (
            <option key={v} value={v}>{v.charAt(0).toUpperCase() + v.slice(1)}</option>
          ))}
        </select>
      </div>
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>SEASON</label>
        <select value={data.season || "kharif"}
          onChange={e => onChange({ ...data, season: e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4 }}>
          {["kharif","rabi","zaid"].map(v => (
            <option key={v} value={v}>{v.charAt(0).toUpperCase() + v.slice(1)}</option>
          ))}
        </select>
      </div>
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>SOIL QUALITY</label>
        <select value={data.soil_quality || "medium"}
          onChange={e => onChange({ ...data, soil_quality: e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4 }}>
          {["poor","medium","good"].map(v => (
            <option key={v} value={v}>{v.charAt(0).toUpperCase() + v.slice(1)}</option>
          ))}
        </select>
      </div>
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>PAST CROP LOSSES (5 YEARS)</label>
        <input type="number" value={data.past_crop_losses ?? ""}
            onChange={e => onChange({ ...data, past_crop_losses: e.target.value === "" ? "" : +e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────

export default function RiskProfiler() {
  const [insuranceType, setInsuranceType] = useState("health")
  const [formData, setFormData]           = useState({})
  const [result, setResult]               = useState(null)
  const [loading, setLoading]             = useState(false)
  const [loadingStep, setStep]            = useState(0)
  const [error, setError]                 = useState(null)

  const runLoadingSteps = () => {
    LOADING_STEPS.forEach((_, i) => setTimeout(() => setStep(i), i * 900))
  }

  const handleTypeChange = (type) => {
    setInsuranceType(type)
    setFormData({})
    setResult(null)
    setError(null)
  }

  const handleSubmit = async () => {
    setLoading(true)
    setResult(null)
    setError(null)
    runLoadingSteps()
    try {
      const body = {
        insurance_type: insuranceType,
        [insuranceType]: formData,
      }
      const res = await fetch("http://localhost:8000/risk/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      setResult(await res.json())
    } catch (e) {
      setError(e.message || "Analysis failed.")
    } finally {
      setLoading(false)
    }
  }

  const rc = result ? RISK_COLORS[result.risk_category] || RISK_COLORS.Medium : null

  return (
    <div style={{ height: "100%", width: "100%", overflowY: "auto" }}>
      <div style={{ maxWidth: 700, margin: "0 auto", padding: "24px 16px" }}>
        <h2 style={{ fontWeight: 600, marginBottom: 4 }}>Risk Profiler</h2>
      <p style={{ color: "#6B7280", marginBottom: 20 }}>
        AI-powered risk scoring and premium recommendations
      </p>

      {/* Insurance type selector */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        {INSURANCE_TYPES.map(t => (
          <button key={t.value} onClick={() => handleTypeChange(t.value)}
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

      {/* Domain form */}
      <div style={{ background: "#F9FAFB", borderRadius: 12,
        padding: "20px 24px", marginBottom: 16 }}>
        <p style={{ fontWeight: 600, marginBottom: 16 }}>
          {INSURANCE_TYPES.find(t => t.value === insuranceType)?.icon}{" "}
          {insuranceType.charAt(0).toUpperCase() + insuranceType.slice(1)} Risk Factors
        </p>
        {insuranceType === "health"  && <HealthForm data={formData} onChange={setFormData}/>}
        {insuranceType === "motor"   && <MotorForm  data={formData} onChange={setFormData}/>}
        {insuranceType === "travel"  && <TravelForm data={formData} onChange={setFormData}/>}
        {insuranceType === "crop"    && <CropForm   data={formData} onChange={setFormData}/>}
      </div>

      <button onClick={handleSubmit} disabled={loading}
        style={{ width: "100%", padding: 12, borderRadius: 8,
          background: loading ? "#93C5FD" : "#2563EB", color: "#fff",
          fontWeight: 600, fontSize: 15, border: "none", cursor: "pointer",
          marginBottom: 16 }}>
        {loading ? "Analyzing..." : "Generate Risk Profile"}
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

      {/* Result */}
      {result && rc && (
        <div style={{ marginTop: 8 }}>

          {/* Score banner */}
          <div style={{ background: rc.bg, border: `1px solid ${rc.border}`,
            borderRadius: 12, padding: "20px 24px", marginBottom: 16,
            display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: 13, color: rc.color, fontWeight: 500 }}>
                RISK CATEGORY
              </div>
              <div style={{ fontSize: 22, fontWeight: 700, color: rc.color, marginTop: 4 }}>
                {result.risk_category} Risk
              </div>
              <div style={{ fontSize: 13, color: rc.color, marginTop: 4 }}>
                Premium adjustment: {result.premium_adjustment}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 40, fontWeight: 700, color: rc.color }}>
                {result.risk_score}
              </div>
              <div style={{ fontSize: 13, color: rc.color }}>out of 100</div>
            </div>
          </div>

          {/* Score bar */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ height: 8, background: "#E5E7EB",
              borderRadius: 4, overflow: "hidden" }}>
              <div style={{
                height: "100%", borderRadius: 4,
                width: `${result.risk_score}%`,
                background: result.risk_score >= 70 ? "#DC2626"
                          : result.risk_score >= 50 ? "#EA580C"
                          : result.risk_score >= 30 ? "#D97706" : "#16A34A",
                transition: "width 0.6s ease"
              }}/>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between",
              fontSize: 11, color: "#9CA3AF", marginTop: 4 }}>
              <span>0 — Low</span>
              <span>30 — Medium</span>
              <span>50 — High</span>
              <span>70 — Very High — 100</span>
            </div>
          </div>

          {/* Premium range */}
          <div style={{ background: "#F9FAFB", borderRadius: 10,
            padding: "14px 20px", marginBottom: 16,
            display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: 12, color: "#6B7280" }}>ESTIMATED PREMIUM RANGE</div>
              <div style={{ fontWeight: 600, fontSize: 16, marginTop: 2 }}>
                {result.base_premium_range}
              </div>
            </div>
            <div style={{ fontSize: 12, color: "#6B7280" }}>
              Confidence: {result.confidence}
            </div>
          </div>

          {/* Risk factors */}
          {result.risk_factors.length > 0 && (
            <div style={{ background: "#F9FAFB", borderRadius: 10,
              padding: "16px 20px", marginBottom: 16 }}>
              <div style={{ fontWeight: 600, marginBottom: 12 }}>
                Risk Factors ({result.risk_factors.length})
              </div>
              {result.risk_factors.map((f, i) => (
                <div key={i} style={{ marginBottom: 12, paddingBottom: 12,
                  borderBottom: i < result.risk_factors.length - 1
                    ? "1px solid #E5E7EB" : "none" }}>
                  <div style={{ display: "flex", justifyContent: "space-between",
                    alignItems: "center", marginBottom: 4 }}>
                    <span style={{ fontWeight: 500, fontSize: 14 }}>{f.factor}</span>
                    <span style={{
                      background: IMPACT_COLORS[f.impact] + "20",
                      color: IMPACT_COLORS[f.impact],
                      padding: "2px 10px", borderRadius: 999,
                      fontSize: 12, fontWeight: 500
                    }}>{f.impact} Impact</span>
                  </div>
                  <div style={{ fontSize: 13, color: "#6B7280" }}>
                    💡 {f.suggestion}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Recommendation */}
          <div style={{ background: "#F9FAFB", borderRadius: 10,
            padding: "16px 20px", marginBottom: 16 }}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>
              Recommendation
              {result.degraded && (
                <span style={{ marginLeft: 8, fontSize: 11,
                  background: "#FEF3C3", color: "#92400E",
                  padding: "2px 8px", borderRadius: 999 }}>Offline Mode</span>
              )}
            </div>
            <p style={{ fontSize: 14, color: "#374151",
              lineHeight: 1.6, margin: 0, whiteSpace: "pre-wrap" }}>
              {result.recommendation}
            </p>
          </div>

        </div>
      )}
      </div>
    </div>
  )
}
