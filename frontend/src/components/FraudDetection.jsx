import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Search, AlertTriangle, CheckCircle, Shield, Clock, FileText } from "lucide-react"

const API_BASE = "http://127.0.0.1:8000"

const RISK_CONFIG = {
  High:   { color: "#DC2626", bg: "#FEE2E2", border: "#FCA5A5", icon: "🔴", gradient: "linear-gradient(135deg, #DC2626, #B91C1C)" },
  Medium: { color: "#D97706", bg: "#FEF3C3", border: "#FCD34D", icon: "🟡", gradient: "linear-gradient(135deg, #D97706, #B45309)" },
  Low:    { color: "#16A34A", bg: "#DCFCE7", border: "#86EFAC", icon: "🟢", gradient: "linear-gradient(135deg, #16A34A, #15803D)" },
}

const LOADING_STEPS = [
  { text: "Validating policy number...", icon: Shield },
  { text: "Running fraud rule engine...", icon: Search },
  { text: "Calculating risk score...", icon: AlertTriangle },
  { text: "Generating investigation report...", icon: FileText },
]

export default function FraudDetection({ showToast }) {
  const [form, setForm] = useState({
    claim_type: "motor",
    policy_number: "",
    claim_amount: "",
    days_after_incident: "",
    previous_claims: "",
    incident_date: "",
    description: "",
    flight_number: "",
    hospital_name: "",
    workshop_name: "",
  })
  const [result, setResult]       = useState(null)
  const [loading, setLoading]     = useState(false)
  const [loadingStep, setStep]    = useState(0)
  const [error, setError]         = useState(null)

  const runLoadingSteps = () => {
    LOADING_STEPS.forEach((_, i) => {
      setTimeout(() => setStep(i), i * 1000)
    })
  }

  const handleSubmit = async () => {
    if (!form.policy_number || !form.claim_amount || !form.incident_date || !form.description) {
      setError("Please fill in all required fields.")
      return
    }
    setLoading(true)
    setResult(null)
    setError(null)
    setStep(0)
    runLoadingSteps()
    try {
      const res = await fetch(`${API_BASE}/fraud/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          claim_amount:        parseFloat(form.claim_amount),
          days_after_incident: parseInt(form.days_after_incident || "0"),
          previous_claims:     parseInt(form.previous_claims || "0"),
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Server error" }))
        throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail))
      }
      const data = await res.json()
      setResult(data)
      showToast?.("Fraud analysis complete", "success")
    } catch (e) {
      const msg = e.message || "Analysis failed. Please check your inputs."
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const risk = result ? RISK_CONFIG[result.risk_level] : null

  return (
    <div className="claims-form-container">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div style={{ width: 44, height: 44, borderRadius: 14, background: "linear-gradient(135deg, #EF4444, #DC2626)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Search size={22} color="#fff" />
          </div>
          <div>
            <h1>Fraud Detection</h1>
            <span className="subtitle">AI-powered fraud risk analysis across all claim types</span>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, color: "#6B7280" }}>Fraud Engine</span>
          <span style={{ fontSize: 12, padding: "4px 10px", borderRadius: 99, background: "#DCFCE7", color: "#166534", fontWeight: 600 }}>Active</span>
        </div>
      </div>

      <div className="claims-content" style={{ paddingTop: "2rem" }}>
        {/* Form Card */}
        <div className="premium-form">
          <h3 style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>Claim Details</h3>
          <p style={{ color: "#6B7280", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
            Enter claim information for fraud analysis. Works for motor, health, travel, and crop insurance.
          </p>

          <div className="form-grid">
            <div className="form-group">
              <label>Claim Type</label>
              <select
                value={form.claim_type}
                onChange={e => setForm({...form, claim_type: e.target.value})}
                style={{
                  padding: "0.75rem 1rem",
                  border: "1.5px solid var(--border)",
                  borderRadius: 12,
                  fontSize: "0.95rem",
                  outline: "none",
                  background: "#f8fafc",
                  cursor: "pointer",
                }}
              >
                <option value="motor">🚗 Motor</option>
                <option value="health">🏥 Health</option>
                <option value="travel">✈️ Travel</option>
                <option value="crop">🌾 Crop</option>
              </select>
            </div>

            <div className="form-group">
              <label>Policy Number *</label>
              <input
                value={form.policy_number}
                onChange={e => setForm({...form, policy_number: e.target.value})}
                placeholder="DG-MOTOR-2025-042"
              />
            </div>

            <div className="form-group">
              <label>Claim Amount (₹) *</label>
              <input
                type="number"
                value={form.claim_amount}
                onChange={e => setForm({...form, claim_amount: e.target.value})}
                placeholder="25000"
              />
            </div>

            <div className="form-group">
              <label>Days After Incident</label>
              <input
                type="number"
                value={form.days_after_incident}
                onChange={e => setForm({...form, days_after_incident: e.target.value})}
                placeholder="3"
              />
            </div>

            <div className="form-group">
              <label>Previous Claims</label>
              <input
                type="number"
                value={form.previous_claims}
                onChange={e => setForm({...form, previous_claims: e.target.value})}
                placeholder="0"
              />
            </div>

            <div className="form-group">
              <label>Incident Date *</label>
              <input
                type="date"
                value={form.incident_date}
                onChange={e => setForm({...form, incident_date: e.target.value})}
              />
            </div>
            
            {/* Dynamic fields based on claim type */}
            <AnimatePresence mode="popLayout">
              {form.claim_type === 'travel' && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="form-group" style={{ overflow: "hidden" }}>
                  <label>Flight Number (Optional)</label>
                  <input
                    value={form.flight_number}
                    onChange={e => setForm({...form, flight_number: e.target.value})}
                    placeholder="e.g. AI-101"
                  />
                </motion.div>
              )}
              {form.claim_type === 'health' && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="form-group" style={{ overflow: "hidden" }}>
                  <label>Hospital Name (Optional)</label>
                  <input
                    value={form.hospital_name}
                    onChange={e => setForm({...form, hospital_name: e.target.value})}
                    placeholder="e.g. City General Hospital"
                  />
                </motion.div>
              )}
              {form.claim_type === 'motor' && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="form-group" style={{ overflow: "hidden" }}>
                  <label>Workshop Name (Optional)</label>
                  <input
                    value={form.workshop_name}
                    onChange={e => setForm({...form, workshop_name: e.target.value})}
                    placeholder="e.g. AutoFix Garage"
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="form-group" style={{ marginBottom: "1.5rem" }}>
            <label>Incident Description *</label>
            <textarea
              value={form.description}
              onChange={e => setForm({...form, description: e.target.value})}
              placeholder="Describe the incident in your own words..."
              rows={4}
            />
          </div>

          <button
            className="btn-submit"
            onClick={handleSubmit}
            disabled={loading}
            style={loading ? { background: "#93C5FD", boxShadow: "none" } : {}}
          >
            {loading ? "Analyzing..." : "🔍 Analyze for Fraud"}
          </button>
        </div>

        {/* Loading Animation */}
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="fraud-loading-card"
            >
              <div style={{ textAlign: "center", padding: "2rem" }}>
                <div className="fraud-loading-spinner" />
                <p style={{ fontWeight: 600, marginTop: 16, marginBottom: 8 }}>
                  Analyzing Claim...
                </p>
                <p style={{ color: "#6B7280", fontSize: 14, marginBottom: 20 }}>
                  {LOADING_STEPS[loadingStep].text}
                </p>
                <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
                  {LOADING_STEPS.map((step, i) => {
                    const Icon = step.icon
                    return (
                      <div
                        key={i}
                        style={{
                          width: 36, height: 36, borderRadius: 10,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          background: i <= loadingStep ? "#2563EB" : "#E5E7EB",
                          color: i <= loadingStep ? "#fff" : "#9CA3AF",
                          transition: "all 0.4s ease",
                          transform: i === loadingStep ? "scale(1.15)" : "scale(1)",
                        }}
                      >
                        <Icon size={16} />
                      </div>
                    )
                  })}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              padding: "1rem 1.25rem",
              background: "#FEE2E2",
              borderRadius: 12,
              color: "#DC2626",
              display: "flex",
              alignItems: "center",
              gap: 10,
              fontWeight: 500,
            }}
          >
            <AlertTriangle size={18} />
            {error}
          </motion.div>
        )}

        {/* Result */}
        <AnimatePresence>
          {result && risk && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            >
              {/* Verdict Banner */}
              <div className="fraud-verdict-banner" style={{ borderColor: risk.border, background: risk.bg }}>
                <div className="fraud-verdict-left">
                  <div style={{ fontSize: 13, color: risk.color, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Fraud Verdict
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 700, color: risk.color, marginTop: 4, display: "flex", alignItems: "center", gap: 10 }}>
                    {risk.icon} {result.verdict}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div className="fraud-score-big" style={{ color: risk.color }}>
                    {result.fraud_score}%
                  </div>
                  <div style={{ fontSize: 13, color: risk.color, fontWeight: 500 }}>
                    {result.risk_level} Risk
                  </div>
                </div>
              </div>

              {/* Score Bar */}
              <div className="fraud-score-bar-container">
                <div className="fraud-score-bar-bg">
                  <motion.div
                    className="fraud-score-bar-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${result.fraud_score}%` }}
                    transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
                    style={{
                      background: result.fraud_score >= 70 ? "#DC2626"
                                : result.fraud_score >= 40 ? "#D97706" : "#16A34A",
                    }}
                  />
                </div>
                <div className="fraud-score-labels">
                  <span>0 — Genuine</span>
                  <span>40 — Suspicious</span>
                  <span>70 — Fraudulent — 100</span>
                </div>
              </div>

              {/* Red Flags */}
              {result.reasons.length > 0 && (
                <div className="fraud-section-card">
                  <div className="fraud-section-title">
                    <AlertTriangle size={18} color="#DC2626" />
                    Red Flags Detected ({result.reasons.length})
                  </div>
                  {result.reasons.map((r, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -15 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + i * 0.1 }}
                      className="fraud-flag-item"
                    >
                      <span className="fraud-flag-icon">⚠</span>
                      <span>{r}</span>
                    </motion.div>
                  ))}
                </div>
              )}

              {/* Investigation Report */}
              <div className="fraud-section-card">
                <div className="fraud-section-title" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <FileText size={18} color="#2563EB" />
                    Investigation Report
                  </div>
                  <div style={{
                    fontSize: 11, fontWeight: 600, padding: "4px 10px", borderRadius: 8,
                    background: result.confidence === "High" ? "#DCFCE7" : result.confidence === "Medium" ? "#FEF3C3" : "#FEE2E2",
                    color: result.confidence === "High" ? "#166534" : result.confidence === "Medium" ? "#854D0E" : "#991B1B",
                    border: `1px solid ${result.confidence === "High" ? "#86EFAC" : result.confidence === "Medium" ? "#FCD34D" : "#FCA5A5"}`
                  }}>
                    Fraud Engine | Confidence: {result.confidence}
                  </div>
                </div>
                <p className="fraud-report-text">
                  {result.investigation_report}
                </p>
              </div>

              {/* Recommended Action */}
              <div
                className="fraud-action-banner"
                style={{
                  background: result.verdict === "Genuine" ? "#DCFCE7"
                            : result.verdict === "Suspicious" ? "#FEF3C3" : "#FEE2E2",
                  borderColor: result.verdict === "Genuine" ? "#86EFAC"
                             : result.verdict === "Suspicious" ? "#FCD34D" : "#FCA5A5",
                }}
              >
                <div>
                  <div style={{ fontSize: 12, color: "#6B7280", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 500 }}>
                    Recommended Action
                  </div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>
                    {result.verdict === "Genuine" && <CheckCircle size={16} style={{ marginRight: 6, verticalAlign: "text-bottom", color: "#16A34A" }} />}
                    {result.verdict === "Suspicious" && <Clock size={16} style={{ marginRight: 6, verticalAlign: "text-bottom", color: "#D97706" }} />}
                    {result.verdict === "Fraudulent" && <AlertTriangle size={16} style={{ marginRight: 6, verticalAlign: "text-bottom", color: "#DC2626" }} />}
                    {result.recommended_action}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 11, color: "#6B7280", marginBottom: 2 }}>Confidence</div>
                  <div style={{
                    fontSize: 13, fontWeight: 600,
                    color: result.confidence === "High" ? "#166534"
                         : result.confidence === "Medium" ? "#854D0E" : "#991B1B",
                  }}>
                    {result.confidence}
                  </div>
                </div>
              </div>

              {/* Timeline */}
              <div className="fraud-section-card">
                <div className="fraud-section-title">
                  <Clock size={18} color="#6B7280" />
                  Analysis Timeline
                </div>
                <div className="fraud-timeline">
                  {[
                    { label: "Data Received", status: "done" },
                    { label: "Rules Evaluated", status: "done" },
                    { label: "Risk Score Calculated", status: "done" },
                    { label: "Report Generated", status: "done" },
                  ].map((step, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.5 + i * 0.15 }}
                      className="fraud-timeline-step"
                    >
                      <div className="fraud-timeline-dot done" />
                      <span>{step.label}</span>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: "flex", gap: 12, marginTop: "1.5rem" }}>
                <button
                  onClick={() => showToast?.("Claim sent to specialized investigation team.", "success")}
                  style={{
                    flex: 1, padding: "0.85rem", borderRadius: 12, border: "1.5px solid #2563EB",
                    background: "#fff", color: "#2563EB", fontWeight: 600, fontSize: "0.9rem",
                    display: "flex", alignItems: "center", justifyContent: "center", gap: 8, cursor: "pointer",
                    transition: "all 0.2s"
                  }}
                  onMouseOver={e => e.currentTarget.style.background = "#EFF6FF"}
                  onMouseOut={e => e.currentTarget.style.background = "#fff"}
                >
                  🔍 Send to Investigator
                </button>
                <button
                  onClick={() => showToast?.("Generating PDF report...", "success")}
                  style={{
                    flex: 1, padding: "0.85rem", borderRadius: 12, border: "none",
                    background: "#2563EB", color: "#fff", fontWeight: 600, fontSize: "0.9rem",
                    display: "flex", alignItems: "center", justifyContent: "center", gap: 8, cursor: "pointer",
                    transition: "all 0.2s", boxShadow: "0 4px 12px rgba(37, 99, 235, 0.2)"
                  }}
                  onMouseOver={e => e.currentTarget.style.background = "#1D4ED8"}
                  onMouseOut={e => e.currentTarget.style.background = "#2563EB"}
                >
                  📄 Download PDF
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
