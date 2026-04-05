import { useState, useEffect } from "react"

const PAYOUT_COLORS = {
  "No Payout":      { color: "#16A34A", bg: "#DCFCE7", border: "#86EFAC" },
  "Partial Payout": { color: "#D97706", bg: "#FEF3C3", border: "#FCD34D" },
  "Full Payout":    { color: "#DC2626", bg: "#FEE2E2", border: "#FCA5A5" },
}

const SEVERITY_COLORS = {
  Mild:     "#D97706",
  Moderate: "#EA580C",
  Severe:   "#DC2626",
}

const LOADING_STEPS = [
  "Fetching weather data...",
  "Reading satellite imagery...",
  "Checking thresholds...",
  "Calculating yield loss...",
  "Processing payout decision...",
]

export default function CropInsurance() {
  const [farmers, setFarmers]          = useState([])
  const [farmerId, setFarmerId]        = useState("F001")
  const [location, setLocation]        = useState("")
  const [cropType, setCropType]        = useState("cotton")
  const [policyNo, setPolicyNo]        = useState("")
  const [season, setSeason]            = useState("kharif")
  const [simulateDrought, setSimulate] = useState(false)
  const [result, setResult]            = useState(null)
  const [loading, setLoading]          = useState(false)
  const [loadingStep, setStep]         = useState(0)
  const [error, setError]              = useState(null)

  // Load farmers on mount
  useEffect(() => {
    fetch("http://127.0.0.1:8000/crop/farmers")
      .then(r => r.json())
      .then(data => {
        setFarmers(data)
        if (data.length > 0) {
          setFarmerId(data[0].farmer_id)
          setLocation(data[0].location)
          setCropType(data[0].crop_type)
        }
      })
      .catch(() => {})
  }, [])

  const handleFarmerChange = (id) => {
    setFarmerId(id)
    const f = farmers.find(fa => fa.farmer_id === id)
    if (f) {
      setLocation(f.location)
      setCropType(f.crop_type)
    }
  }

  const runLoadingSteps = () => {
    LOADING_STEPS.forEach((_, i) => setTimeout(() => setStep(i), i * 900))
  }

  const handleSubmit = async () => {
    setLoading(true)
    setResult(null)
    setError(null)
    runLoadingSteps()
    try {
      const res = await fetch("http://127.0.0.1:8000/crop/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          farmer_id:        farmerId,
          location:         location,
          crop_type:        cropType,
          policy_number:    policyNo || `CROP-2025-${farmerId}`,
          season:           season,
          simulate_drought: simulateDrought,
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

  const pc = result ? PAYOUT_COLORS[result.payout_status] : null

  return (
    <div style={{ height: "100%", width: "100%", overflowY: "auto" }}>
      <div style={{ maxWidth: 720, margin: "0 auto", padding: "24px 16px" }}>
        <h2 style={{ fontWeight: 600, marginBottom: 4 }}>Crop Insurance Agent</h2>
        <p style={{ color: "#6B7280", marginBottom: 24 }}>
          Autonomous weather monitoring and payout trigger system
        </p>

        {/* Form */}
        <div style={{ background: "#F9FAFB", borderRadius: 12,
          padding: "20px 24px", marginBottom: 16 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>

            <div>
              <label style={{ fontSize: 12, color: "#6B7280" }}>FARMER</label>
              <select value={farmerId} onChange={e => handleFarmerChange(e.target.value)}
                style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
                  border: "1px solid #E5E7EB", marginTop: 4 }}>
                {farmers.map(f => (
                  <option key={f.farmer_id} value={f.farmer_id}>
                    {f.farmer_id} — {f.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: 12, color: "#6B7280" }}>SEASON</label>
              <select value={season} onChange={e => setSeason(e.target.value)}
                style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
                  border: "1px solid #E5E7EB", marginTop: 4 }}>
                {["kharif","rabi","zaid"].map(s => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: 12, color: "#6B7280" }}>LOCATION</label>
              <input value={location} onChange={e => setLocation(e.target.value)}
                style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
                  border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
            </div>

            <div>
              <label style={{ fontSize: 12, color: "#6B7280" }}>CROP TYPE</label>
              <input value={cropType} onChange={e => setCropType(e.target.value)}
                style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
                  border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
            </div>

          </div>

          {/* Drought simulation toggle */}
          <div style={{ marginTop: 16, padding: "12px 16px",
            background: simulateDrought ? "#FEE2E2" : "#F3F4F6",
            borderRadius: 8, display: "flex",
            justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 500, fontSize: 14 }}>
                Simulate Drought Conditions
              </div>
              <div style={{ fontSize: 12, color: "#6B7280" }}>
                Force drought data for demo purposes
              </div>
            </div>
            <label style={{ cursor: "pointer", display: "flex",
              alignItems: "center", gap: 8 }}>
              <input type="checkbox" checked={simulateDrought}
                onChange={e => setSimulate(e.target.checked)}
                style={{ width: 16, height: 16 }}/>
              <span style={{ fontSize: 14, fontWeight: 500,
                color: simulateDrought ? "#DC2626" : "#6B7280" }}>
                {simulateDrought ? "ON — Drought mode" : "OFF"}
              </span>
            </label>
          </div>
        </div>

        <button onClick={handleSubmit} disabled={loading}
          style={{ width: "100%", padding: 12, borderRadius: 8,
            background: loading ? "#93C5FD" : "#2563EB",
            color: "#fff", fontWeight: 600, fontSize: 15,
            border: "none", cursor: "pointer", marginBottom: 16 }}>
          {loading ? "Analyzing..." : "Run Crop Agent"}
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

        {/* Results */}
        {result && pc && (
          <div style={{ marginTop: 8 }}>

            {/* Payout verdict */}
            <div style={{ background: pc.bg, border: `1px solid ${pc.border}`,
              borderRadius: 12, padding: "20px 24px", marginBottom: 16,
              display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: 13, color: pc.color, fontWeight: 500 }}>
                  PAYOUT STATUS
                </div>
                <div style={{ fontSize: 22, fontWeight: 700, color: pc.color, marginTop: 4 }}>
                  {result.payout_status}
                </div>
                <div style={{ fontSize: 13, color: pc.color, marginTop: 4 }}>
                  {result.farmer_name} · {result.crop_type.toUpperCase()} · {result.location}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 32, fontWeight: 700, color: pc.color }}>
                  ₹{result.payout_amount.toLocaleString("en-IN")}
                </div>
                <div style={{ fontSize: 13, color: pc.color }}>
                  of ₹{result.sum_insured.toLocaleString("en-IN")} insured
                </div>
                <div style={{ fontSize: 12, color: pc.color, marginTop: 2 }}>
                  Yield loss: {result.yield_loss_pct}%
                </div>
              </div>
            </div>

            {/* Weather cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
              gap: 10, marginBottom: 16 }}>
              {[
                { label: "7-day Rainfall",  value: `${result.weather_data.rainfall_mm}mm`,       icon: "🌧" },
                { label: "Max Temp",       value: `${result.weather_data.temperature_max_c}°C`, icon: "🌡" },
                { label: "Humidity",       value: `${result.weather_data.humidity_pct}%`,        icon: "💧" },
                { label: "Wind Speed",     value: `${result.weather_data.wind_speed_kmh} km/h`, icon: "💨" },
                { label: "NDVI Index",     value: result.weather_data.ndvi_index.toFixed(2),     icon: "🛰" },
                { label: "Soil Moisture",  value: `${result.weather_data.soil_moisture_pct}%`,   icon: "🌱" },
              ].map((w, i) => (
                <div key={i} style={{ background: "#F9FAFB", borderRadius: 10,
                  padding: "14px 16px", textAlign: "center" }}>
                  <div style={{ fontSize: 20 }}>{w.icon}</div>
                  <div style={{ fontSize: 18, fontWeight: 600, margin: "4px 0" }}>
                    {w.value}
                  </div>
                  <div style={{ fontSize: 12, color: "#6B7280" }}>{w.label}</div>
                </div>
              ))}
            </div>

            {/* Threshold breaches */}
            {result.thresholds_breached.length > 0 ? (
              <div style={{ background: "#FFF7F0", border: "1px solid #FDBA74",
                borderRadius: 10, padding: "16px 20px", marginBottom: 16 }}>
                <div style={{ fontWeight: 600, marginBottom: 12 }}>
                  Threshold Breaches ({result.thresholds_breached.length})
                </div>
                {result.thresholds_breached.map((b, i) => (
                  <div key={i} style={{ display: "flex",
                    justifyContent: "space-between", alignItems: "center",
                    marginBottom: 10, paddingBottom: 10,
                    borderBottom: i < result.thresholds_breached.length - 1
                      ? "1px solid #FED7AA" : "none" }}>
                    <div>
                      <div style={{ fontWeight: 500, fontSize: 14 }}>
                        {b.parameter}
                      </div>
                      <div style={{ fontSize: 12, color: "#6B7280" }}>
                        {b.actual_value} — {b.threshold}
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <span style={{
                        background: SEVERITY_COLORS[b.severity] + "20",
                        color: SEVERITY_COLORS[b.severity],
                        padding: "2px 10px", borderRadius: 999,
                        fontSize: 12, fontWeight: 500
                      }}>{b.severity}</span>
                      <div style={{ fontSize: 12, color: "#6B7280", marginTop: 4 }}>
                        -{b.yield_impact}% yield
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ background: "#DCFCE7", border: "1px solid #86EFAC",
                borderRadius: 10, padding: "14px 20px", marginBottom: 16,
                color: "#16A34A", fontWeight: 500 }}>
                No threshold breaches detected — crops are healthy
              </div>
            )}

            {/* Assessment report */}
            <div style={{ background: "#F9FAFB", borderRadius: 10,
              padding: "16px 20px", marginBottom: 16 }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>
                Assessment Report
                <span style={{ marginLeft: 8, fontSize: 11,
                  background: result.weather_source.includes("Live") ? "#DBEAFE" : (result.weather_source.includes("Estimated") ? "#FEF3C3" : "#FEE2E2"),
                  color: result.weather_source.includes("Live") ? "#1E40AF" : (result.weather_source.includes("Estimated") ? "#92400E" : "#991B1B"),
                  padding: "2px 8px", borderRadius: 999 }}>
                  {result.weather_source}
                </span>
                {result.degraded && (
                  <span style={{ marginLeft: 6, fontSize: 11,
                    background: "#FEF3C3", color: "#92400E",
                    padding: "2px 8px", borderRadius: 999 }}>Offline Mode</span>
                )}
              </div>
              <p style={{ fontSize: 14, color: "#374151",
                lineHeight: 1.6, margin: 0, whiteSpace: "pre-wrap" }}>
                {result.assessment_report}
              </p>
            </div>

            {/* Farmer notification */}
            <div style={{ background: "#EFF6FF", border: "1px solid #BFDBFE",
              borderRadius: 10, padding: "16px 20px" }}>
              <div style={{ fontWeight: 600, marginBottom: 8, color: "#1E40AF" }}>
                Farmer Notification (SMS Preview)
              </div>
              <pre style={{ fontSize: 13, color: "#1E40AF",
                lineHeight: 1.6, margin: 0,
                whiteSpace: "pre-wrap", fontFamily: "monospace" }}>
                {result.farmer_notification}
              </pre>
            </div>

          </div>
        )}
      </div>
    </div>
  )
}
