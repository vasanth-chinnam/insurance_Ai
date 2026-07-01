import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadCloud, CheckCircle, AlertTriangle, FileText, Camera, ShieldCheck, Car } from 'lucide-react'
import confetti from 'canvas-confetti'
import InsuranceTypeSelector from './InsuranceTypeSelector'

const severityStyles = {
  MINOR:    { background: "#FEF3C7", color: "#92400E" },
  MODERATE: { background: "#FFEDD5", color: "#9A3412" },
  SEVERE:   { background: "#FEE2E2", color: "#991B1B" },
}

const confidenceColors = {
  High:   "#16A34A",
  Medium: "#D97706",
  Low:    "#DC2626",
}

const validateYear = (year) => {
  const currentYear = new Date().getFullYear()
  if (year < 1900 || year > currentYear) {
    return `Year must be between 1900 and ${currentYear}`
  }
  return null
}

const getLocalToday = () => {
  const d = new Date()
  const offset = d.getTimezoneOffset()
  return new Date(d.getTime() - (offset * 60 * 1000)).toISOString().split('T')[0]
}

const MOTOR_LOADING_STEPS = [
  "Uploading damage photo...",
  "Analyzing image with Vision AI...",
  "Retrieving policy coverage...",
  "Estimating repair costs...",
  "Generating assessment report...",
]

function HealthClaimForm({ data, onChange }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      {[
        { key: "claimant_name",    label: "Claimant Name" },
        { key: "policy_number",    label: "Policy Number", ph: "e.g. HL-2025-001" },
        { key: "patient_name",     label: "Patient Name" },
        { key: "age",              label: "Age", type: "number" },
        { key: "diagnosis",        label: "Diagnosis" },
        { key: "hospital_name",    label: "Hospital Name" },
        { key: "admission_date",   label: "Admission Date", ph: "dd-mm-yyyy" },
        { key: "discharge_date",   label: "Discharge Date", ph: "dd-mm-yyyy" },
        { key: "total_bill_amount",label: "Total Bill Amount (₹)", type: "number" },
        { key: "sum_insured",      label: "Sum Insured (₹)", type: "number" },
      ].map(f => (
        <div key={f.key}>
          <label style={{ fontSize: 12, color: "#6B7280" }}>{f.label.toUpperCase()}</label>
          <input type={f.type || "text"} value={data[f.key] || ""}
            placeholder={f.ph}
            onChange={e => onChange({
              ...data,
              [f.key]: f.type === "number" ? (e.target.value === "" ? "" : +e.target.value) : e.target.value
            })}
            style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
              border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
        </div>
      ))}
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>TREATMENT TYPE</label>
        <select value={data.treatment_type || "IPD"}
          onChange={e => onChange({ ...data, treatment_type: e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4 }}>
          {["OPD","IPD","Daycare","Surgery"].map(v => <option key={v} value={v}>{v}</option>)}
        </select>
      </div>
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>ROOM TYPE</label>
        <select value={data.room_type || "General"}
          onChange={e => onChange({ ...data, room_type: e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4 }}>
          {["General","Semi-Private","Private","ICU"].map(v => <option key={v} value={v}>{v}</option>)}
        </select>
      </div>
    </div>
  )
}

function TravelClaimForm({ data, onChange }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      <div>
        <label style={{ fontSize: 12, color: "#6B7280" }}>CLAIM TYPE</label>
        <select value={data.claim_type || "flight_delay"}
          onChange={e => onChange({ ...data, claim_type: e.target.value })}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4 }}>
          <option value="flight_delay">Flight Delay</option>
          <option value="baggage_loss">Baggage Loss</option>
          <option value="trip_cancellation">Trip Cancellation</option>
          <option value="medical_emergency">Medical Emergency</option>
        </select>
      </div>
      {[
        { key: "claimant_name",  label: "Claimant Name" },
        { key: "policy_number",  label: "Policy Number", ph: "e.g. TR-2025-001" },
        { key: "origin",          label: "Origin" },
        { key: "destination",     label: "Destination" },
        { key: "departure_date",  label: "Departure Date", ph: "dd-mm-yyyy" },
        { key: "sum_insured",     label: "Sum Insured (₹)", type: "number" },
      ].map(f => (
        <div key={f.key}>
          <label style={{ fontSize: 12, color: "#6B7280" }}>{f.label.toUpperCase()}</label>
          <input type={f.type || "text"} value={data[f.key] || ""}
            placeholder={f.ph}
            onChange={e => onChange({
              ...data,
              [f.key]: f.type === "number" ? (e.target.value === "" ? "" : +e.target.value) : e.target.value
            })}
            style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
              border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
        </div>
      ))}
      {data.claim_type === "flight_delay" && (
        <div>
          <label style={{ fontSize: 12, color: "#6B7280" }}>DELAY HOURS</label>
          <input type="number" value={data.delay_hours || ""}
            onChange={e => onChange({ ...data, delay_hours: e.target.value === "" ? "" : +e.target.value })}
            style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
              border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
        </div>
      )}
      {data.claim_type === "baggage_loss" && (
        <div>
          <label style={{ fontSize: 12, color: "#6B7280" }}>BAGGAGE VALUE (₹)</label>
          <input type="number" value={data.baggage_value || ""}
            onChange={e => onChange({ ...data, baggage_value: e.target.value === "" ? "" : +e.target.value })}
            style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
              border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
        </div>
      )}
      {data.claim_type === "trip_cancellation" && (
        <div style={{ gridColumn: "1 / -1" }}>
          <label style={{ fontSize: 12, color: "#6B7280" }}>CANCELLATION REASON</label>
          <input value={data.cancellation_reason || ""}
            placeholder="e.g. illness, visa rejection"
            onChange={e => onChange({ ...data, cancellation_reason: e.target.value })}
            style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
              border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
        </div>
      )}
      <div style={{ gridColumn: "1 / -1" }}>
        <label style={{ fontSize: 12, color: "#6B7280" }}>DESCRIPTION</label>
        <textarea value={data.description || ""}
          onChange={e => onChange({ ...data, description: e.target.value })}
          rows={3}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8,
            border: "1px solid #E5E7EB", marginTop: 4, boxSizing: "border-box" }}/>
      </div>
    </div>
  )
}

export default function MotorClaimsForm({ API_BASE, showToast }) {
  const [loadingStep, setLoadingStep] = useState(0)
  const [insuranceType, setInsuranceType] = useState('motor')
  
  // Motor state
  const [formData, setFormData] = useState({
    claimant_name: '',
    vehicle_number: '',
    vehicle_make: '',
    vehicle_model: '',
    year: new Date().getFullYear(),
    incident_date: '',
    incident_description: '',
    policy_number: ''
  })
  const [photo, setPhoto] = useState(null)
  const fileInputRef = useRef(null)

  // Health state
  const [healthFormData, setHealthFormData] = useState({
    claimant_name: '',
    policy_number: '',
    patient_name: '',
    age: '',
    diagnosis: '',
    treatment_type: 'IPD',
    hospital_name: '',
    admission_date: '',
    discharge_date: '',
    room_type: 'General',
    total_bill_amount: '',
    sum_insured: '',
  })

  // Travel state
  const [travelFormData, setTravelFormData] = useState({
    claimant_name: '',
    policy_number: '',
    claim_type: 'flight_delay',
    origin: '',
    destination: '',
    departure_date: '',
    delay_hours: 0,
    baggage_value: 0,
    cancellation_reason: '',
    sum_insured: '',
    description: '',
  })

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handlePhotoUpload = (e) => {
    const file = e.target.files[0]
    if (file) {
      const type = file.type || ''
      const name = file.name || ''
      const isImg = type.startsWith('image/') || 
                    name.toLowerCase().endsWith('.png') || 
                    name.toLowerCase().endsWith('.jpg') || 
                    name.toLowerCase().endsWith('.jpeg') || 
                    name.toLowerCase().endsWith('.webp')
      if (isImg) {
        setPhoto(file)
      } else {
        showToast('Please upload a valid image file (JPG, PNG)', 'error')
      }
    }
  }

  const stepsList = insuranceType === 'motor' ? MOTOR_LOADING_STEPS : (
    insuranceType === 'health' ? [
      "Reviewing admission & discharge timeline...",
      "Applying policy room rent caps...",
      "Identifying excluded billing charges...",
      "Calculating eligible coverage & deductible...",
      "Generating medical assessment report...",
    ] : [
      "Verifying flight logs & departure details...",
      "Scoring delay & loss levels...",
      "Checking sum insured & policy caps...",
      "Processing travel claim payout verdict...",
      "Generating travel assessment report...",
    ]
  )

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (insuranceType === 'crop') {
      showToast(`Please use the Crop Insurance tab to file crop claims!`, 'error')
      return
    }

    setLoading(true)
    setResult(null)
    setLoadingStep(0)
    
    stepsList.forEach((_, i) => {
      setTimeout(() => setLoadingStep(i), i * 900)
    })

    if (insuranceType === 'motor') {
      const yearError = validateYear(formData.year)
      if (yearError) {
        showToast(`Vehicle Year: ${yearError.replace('Year', '')}`, 'error')
        setLoading(false)
        return
      }

      if (formData.incident_date) {
        const incidentYear = new Date(formData.incident_date).getFullYear()
        const incidentYearError = validateYear(incidentYear)
        if (incidentYearError) {
          showToast(`Incident Date: ${incidentYearError.replace('Year', '')}`, 'error')
          setLoading(false)
          return
        }
      }

      if (!photo) {
        showToast('Please upload a damage photo', 'error')
        setLoading(false)
        return
      }

      const payload = new FormData()
      Object.keys(formData).forEach(key => payload.append(key, formData[key]))
      payload.append('damage_photo', photo)

      try {
        const claimsEndpoint = API_BASE.replace('/api', '') + '/claims/motor'
        const res = await fetch(claimsEndpoint, {
          method: 'POST',
          body: payload
        })
        
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Failed to process claim')
        setResult(data)
        
        if (data.total_repair_estimate > 0) {
          confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#6366f1', '#4f46e5', '#10b981']
          })
          showToast('Claim assessed successfully!', 'success')
        } else {
          showToast('Claim partially assessed (AI degraded)', 'error')
        }
      } catch (err) {
        console.error(err)
        showToast(err.message || 'Server error connecting to claims endpoint', 'error')
      } finally {
        setLoading(false)
      }
    } else if (insuranceType === 'health') {
      try {
        const claimsEndpoint = API_BASE.replace('/api', '') + '/claims/health'
        const res = await fetch(claimsEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(healthFormData)
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Failed to process health claim')
        setResult(data)
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 }
        })
        showToast('Health claim assessed successfully!', 'success')
      } catch (err) {
        console.error(err)
        showToast(err.message || 'Server error processing health claim', 'error')
      } finally {
        setLoading(false)
      }
    } else if (insuranceType === 'travel') {
      try {
        const claimsEndpoint = API_BASE.replace('/api', '') + '/claims/travel'
        const res = await fetch(claimsEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(travelFormData)
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Failed to process travel claim')
        setResult(data)
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 }
        })
        showToast('Travel claim assessed successfully!', 'success')
      } catch (err) {
        console.error(err)
        showToast(err.message || 'Server error processing travel claim', 'error')
      } finally {
        setLoading(false)
      }
    }
  }

  return (
    <div className="claims-form-container">
      <header className="chat-header" style={{ marginBottom: '2rem' }}>
        <div>
          <h1>Claim Estimator</h1>
          <div className="subtitle">Submit health, travel, or motor policy claims for automated AI analysis</div>
        </div>
      </header>
      
      <div className="claims-content">
        <div style={{ marginBottom: 8 }}>
          <InsuranceTypeSelector value={insuranceType} onChange={(val) => {
            setInsuranceType(val)
            setResult(null)
          }} compact />
        </div>
        
        <form onSubmit={handleSubmit} className="premium-form">
          {insuranceType === 'motor' && (
            <div className="form-grid">
              <div className="form-group">
                <label>Policy Number</label>
                <input type="text" name="policy_number" value={formData.policy_number} onChange={handleInputChange} required placeholder="e.g. POL-2024-001" />
              </div>
              <div className="form-group">
                <label>Claimant Name</label>
                <input type="text" name="claimant_name" value={formData.claimant_name} onChange={handleInputChange} required placeholder="Your full name" />
              </div>
              <div className="form-group">
                <label>Vehicle Number</label>
                <input type="text" name="vehicle_number" value={formData.vehicle_number} onChange={handleInputChange} required placeholder="Registration plate" />
              </div>
              <div className="form-group">
                <label>Vehicle Make</label>
                <input type="text" name="vehicle_make" value={formData.vehicle_make} onChange={handleInputChange} required placeholder="e.g. Honda" />
              </div>
              <div className="form-group">
                <label>Vehicle Model</label>
                <input type="text" name="vehicle_model" value={formData.vehicle_model} onChange={handleInputChange} required placeholder="e.g. City" />
              </div>
              <div className="form-group">
                <label>Year</label>
                <input type="number" name="year" value={formData.year} onChange={handleInputChange} required max={new Date().getFullYear()} />
              </div>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>Incident Date</label>
                <input type="date" name="incident_date" value={formData.incident_date} onChange={handleInputChange} required max={getLocalToday()} />
              </div>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>Incident Description</label>
                <textarea name="incident_description" value={formData.incident_description} onChange={handleInputChange} required rows={3} placeholder="Describe how the accident happened..."></textarea>
              </div>
            </div>
          )}

          {insuranceType === 'health' && (
            <HealthClaimForm data={healthFormData} onChange={setHealthFormData} />
          )}

          {insuranceType === 'travel' && (
            <TravelClaimForm data={travelFormData} onChange={setTravelFormData} />
          )}

          {insuranceType === 'crop' && (
            <div style={{ padding: 24, textAlign: "center", background: "#F9FAFB", borderRadius: 12, border: "1px solid #E5E7EB" }}>
              <p style={{ color: "#4B5563" }}>🌾 Crop Insurance is managed autonomously by the Crop Agent tab. Please use that view to trigger satellite analysis.</p>
            </div>
          )}

          {insuranceType === 'motor' && (
            <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
              <input type="file" ref={fileInputRef} onChange={handlePhotoUpload} accept="image/*" style={{ display: 'none' }} />
              {photo ? (
                <div className="upload-success">
                  <CheckCircle size={32} className="text-primary" />
                  <p>{photo.name}</p>
                  <div className="image-preview" style={{ backgroundImage: `url(${URL.createObjectURL(photo)})` }}></div>
                </div>
              ) : (
                <div className="upload-prompt">
                  <Camera size={36} />
                  <p>Drag & drop or click to upload damage photo</p>
                  <span>Supports JPG, PNG</span>
                </div>
              )}
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: "center", padding: "24px", background: "#f8fafc", borderRadius: "8px", border: "1px dashed #cbd5e1", marginTop: "1rem" }}>
              <div className="spinner" style={{ margin: "0 auto", width: "32px", height: "32px", border: "3px solid #e2e8f0", borderTopColor: "#3b82f6", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
              <p style={{ marginTop: "14px", color: "#475569", fontWeight: 500 }}>
                {stepsList[loadingStep]}
              </p>
              <div style={{ display: "flex", gap: "8px", justifyContent: "center", marginTop: "12px" }}>
                {stepsList.map((_, i) => (
                  <div key={i} style={{
                    width: "8px", height: "8px", borderRadius: "50%",
                    background: i <= loadingStep ? "#3B82F6" : "#E2E8F0",
                    transition: "background 0.3s ease"
                  }}/>
                ))}
              </div>
            </div>
          ) : (
            insuranceType !== 'crop' && (
              <button type="submit" className="btn-submit" style={{ marginTop: 16 }} disabled={insuranceType === 'motor' && !photo}>
                Submit Claim Request
              </button>
            )
          )}
        </form>

        <AnimatePresence>
          {result && (
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              className="claim-result"
              style={{ marginTop: 24 }}
            >
              <h2>Assessment Receipt</h2>
              
              {result.degraded && (
                <div style={{ 
                  background: "#FEF9C3", 
                  border: "1px solid #FDE047",
                  borderRadius: "12px", 
                  padding: "16px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "2rem"
                }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#92400E', fontSize: '0.9rem', lineHeight: 1.4 }}>
                    <AlertTriangle size={20} style={{ flexShrink: 0 }} />
                    Claim processed with rule-based backup (AI models busy).
                  </span>
                  {result.confidence && (
                    <span style={{
                      background: confidenceColors[result.confidence] + "20",
                      color: confidenceColors[result.confidence],
                      padding: "4px 12px",
                      borderRadius: "999px",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                      marginLeft: "16px"
                    }}>
                      Confidence: {result.confidence}
                    </span>
                  )}
                </div>
              )}

              {/* Render Motor Result Receipt */}
              {insuranceType === 'motor' && (
                <div className="receipt-details">
                  <div className="receipt-row">
                    <span>Vehicle</span>
                    <strong>{result.vehicle}</strong>
                  </div>
                  <div className="receipt-row">
                    <span>Claimant</span>
                    <strong>{result.claimant_name}</strong>
                  </div>

                  {result.detected_area && (
                    <div style={{
                      background: "#EFF6FF",
                      border: "1px solid #BFDBFE",
                      borderRadius: "10px",
                      padding: "16px",
                      marginBottom: "24px",
                      marginTop: "16px",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      gap: "16px"
                    }}>
                      <div>
                        <p style={{ fontWeight: 600, color: "#1E40AF", marginBottom: "6px", fontSize: "0.95rem" }}>
                          Image Analysis: Detected {result.detected_area}
                        </p>
                        {result.image_analysis && (
                          <p style={{ fontSize: "0.85rem", color: "#2563EB", lineHeight: 1.5 }}>
                            {result.image_analysis}
                          </p>
                        )}
                      </div>
                      <span style={{
                        background: {High:"#DCFCE7",Medium:"#FEF9C3",Low:"#FEE2E2"}[result.confidence] || "#FEF9C3",
                        color: {High:"#166534",Medium:"#92400E",Low:"#991B1B"}[result.confidence] || "#92400E",
                        padding: "4px 12px",
                        borderRadius: "999px",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        whiteSpace: "nowrap"
                      }}>
                        AI Confidence: {result.confidence}
                      </span>
                    </div>
                  )}
                  
                  <h3 className="parts-header">Damaged Parts</h3>
                  {result.damaged_parts && result.damaged_parts.length > 0 ? (
                    <ul className="parts-list">
                      {result.damaged_parts.map((part, i) => (
                        <li key={i}>
                          <div className="part-info">
                            <span className="part-name">{part.part}</span>
                            <span 
                              className="severity-badge"
                              style={severityStyles[part.severity.toUpperCase()] || severityStyles.MINOR}
                            >
                              {part.severity}
                            </span>
                            <span className="repair-type">{part.repair_type}</span>
                          </div>
                          <strong className="part-cost">₹{part.estimated_cost.toLocaleString()}</strong>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="no-parts">No specific parts identified.</p>
                  )}
                  
                  <div className="receipt-totals">
                    <div className="receipt-row text-lg">
                      <span>Total Repair Estimate</span>
                      <strong>₹{result.total_repair_estimate.toLocaleString()}</strong>
                    </div>
                    <div className="receipt-row text-muted">
                      <span>Deductible (10%)</span>
                      <span>- ₹{result.deductible.toLocaleString()}</span>
                    </div>
                    <div className="receipt-row text-xl text-primary mt-2 pt-2 border-t">
                      <span>Covered Amount</span>
                      <strong>₹{result.covered_amount.toLocaleString()}</strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Render Health Result Receipt */}
              {insuranceType === 'health' && (
                <div className="receipt-details">
                  <div className="receipt-row">
                    <span>Patient Name</span>
                    <strong>{result.patient_name} (Age: {healthFormData.age})</strong>
                  </div>
                  <div className="receipt-row">
                    <span>Hospital</span>
                    <strong>{result.hospital_name}</strong>
                  </div>
                  <div className="receipt-row">
                    <span>Diagnosis</span>
                    <strong>{result.diagnosis}</strong>
                  </div>
                  <div className="receipt-row">
                    <span>Policy Number</span>
                    <strong>{result.policy_number}</strong>
                  </div>

                  <h3 className="parts-header">Bill Items Breakdown</h3>
                  {result.bill_breakdown && result.bill_breakdown.length > 0 ? (
                    <ul className="parts-list">
                      {result.bill_breakdown.map((item, i) => (
                        <li key={i}>
                          <div className="part-info">
                            <span className="part-name">{item.item}</span>
                            <span 
                              className="severity-badge"
                              style={
                                item.status === "Covered" ? { background: "#DCFCE7", color: "#166534" }
                                : item.status === "Capped" ? { background: "#FEF3C7", color: "#92400E" }
                                : { background: "#FEE2E2", color: "#991B1B" }
                              }
                            >
                              {item.status}
                            </span>
                            <span className="repair-type" style={{ maxWidth: '250px' }}>{item.reason}</span>
                          </div>
                          <div style={{ textAlign: "right" }}>
                            <strong className="part-cost">₹{item.eligible_amount.toLocaleString()}</strong>
                            <div style={{ fontSize: "11px", color: "#9CA3AF" }}>Billed: ₹{item.amount.toLocaleString()}</div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : null}

                  <div className="receipt-totals" style={{ marginTop: 24 }}>
                    <div className="receipt-row">
                      <span>Total Hospital Bill</span>
                      <strong>₹{result.total_bill_amount.toLocaleString()}</strong>
                    </div>
                    {result.room_rent_excess > 0 && (
                      <div className="receipt-row text-muted">
                        <span>Room Rent Excess (Capped at ₹{result.room_rent_cap.toLocaleString()})</span>
                        <span style={{ color: "#DC2626" }}>- ₹{result.room_rent_excess.toLocaleString()}</span>
                      </div>
                    )}
                    <div className="receipt-row text-muted">
                      <span>Exclusions & Capping Deductions</span>
                      <span>- ₹{result.total_deductions.toLocaleString()}</span>
                    </div>
                    <div className="receipt-row text-muted">
                      <span>Standard Deductible (5%)</span>
                      <span>- ₹{result.deductible.toLocaleString()}</span>
                    </div>
                    <div className="receipt-row text-xl text-primary mt-2 pt-2 border-t">
                      <span>Final Approved Payout</span>
                      <strong>₹{result.final_payout.toLocaleString()}</strong>
                    </div>
                  </div>

                  {result.explanation && (
                    <div style={{ marginTop: "24px", padding: "16px", background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "10px" }}>
                      <h4 style={{ fontWeight: 600, color: "#1E40AF", marginBottom: "8px", fontSize: "0.95rem" }}>Assessor Explanation</h4>
                      <p style={{ fontSize: "0.85rem", color: "#1E40AF", lineHeight: 1.5, margin: 0 }}>
                        {result.explanation}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Render Travel Result Receipt */}
              {insuranceType === 'travel' && (
                <div className="receipt-details">
                  <div className="receipt-row">
                    <span>Claimant</span>
                    <strong>{result.claimant_name}</strong>
                  </div>
                  <div className="receipt-row">
                    <span>Policy Number</span>
                    <strong>{result.policy_number}</strong>
                  </div>
                  <div className="receipt-row">
                    <span>Route</span>
                    <strong>{result.route}</strong>
                  </div>
                  <div className="receipt-row">
                    <span>Claim Type</span>
                    <strong>{result.claim_type.replace('_', ' ').toUpperCase()}</strong>
                  </div>
                  <div className="receipt-row">
                    <span>Applied Payout Tier</span>
                    <strong>{result.payout_tier}</strong>
                  </div>

                  <div className="receipt-totals" style={{ marginTop: "24px" }}>
                    <div className="receipt-row">
                      <span>Base Approved Payout</span>
                      <strong>₹{result.base_payout.toLocaleString()}</strong>
                    </div>
                    <div className="receipt-row text-muted">
                      <span>Deductions / Caps</span>
                      <span>- ₹{result.deductions.toLocaleString()}</span>
                    </div>
                    <div className="receipt-row text-xl text-primary mt-2 pt-2 border-t">
                      <span>Final Travel Payout</span>
                      <strong>₹{result.final_payout.toLocaleString()}</strong>
                    </div>
                  </div>

                  {result.explanation && (
                    <div style={{ marginTop: "24px", padding: "16px", background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "10px" }}>
                      <h4 style={{ fontWeight: 600, color: "#1E40AF", marginBottom: "8px", fontSize: "0.95rem" }}>Travel Assessor Explanation</h4>
                      <p style={{ fontSize: "0.85rem", color: "#1E40AF", lineHeight: 1.5, margin: 0 }}>
                        {result.explanation}
                      </p>
                    </div>
                  )}
                </div>
              )}

            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
