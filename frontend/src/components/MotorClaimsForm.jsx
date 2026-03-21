import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadCloud, CheckCircle, AlertTriangle, FileText, Camera, ShieldCheck, Car } from 'lucide-react'
import confetti from 'canvas-confetti'
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

const LOADING_STEPS = [
  "Uploading damage photo...",
  "Analyzing image with Vision AI...",
  "Retrieving policy coverage...",
  "Estimating repair costs...",
  "Generating assessment report...",
]

export default function MotorClaimsForm({ API_BASE, showToast }) {
  const [loadingStep, setLoadingStep] = useState(0)
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
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const fileInputRef = useRef(null)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handlePhotoUpload = (e) => {
    const file = e.target.files[0]
    if (file && (file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'image/webp')) {
      setPhoto(file)
    } else {
      showToast('Please upload a valid image file (JPG, PNG)', 'error')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const yearError = validateYear(formData.year)
    if (yearError) {
      showToast(`Vehicle Year: ${yearError.replace('Year', '')}`, 'error')
      return
    }

    if (formData.incident_date) {
      const incidentYear = new Date(formData.incident_date).getFullYear()
      const incidentYearError = validateYear(incidentYear)
      if (incidentYearError) {
        showToast(`Incident Date: ${incidentYearError.replace('Year', '')}`, 'error')
        return
      }
    }

    if (!photo) {
      showToast('Please upload a damage photo', 'error')
      return
    }

    setLoading(true)
    setResult(null)
    setLoadingStep(0)
    
    LOADING_STEPS.forEach((_, i) => {
      setTimeout(() => setLoadingStep(i), i * 1200)
    })

    const payload = new FormData()
    Object.keys(formData).forEach(key => payload.append(key, formData[key]))
    payload.append('damage_photo', photo)

    try {
      // Note: Motor claims sits directly on /claims/motor, not /api/claims/motor
      const claimsEndpoint = API_BASE.replace('/api', '') + '/claims/motor'
      const res = await fetch(claimsEndpoint, {
        method: 'POST',
        body: payload
      })
      
      const data = await res.json()
      
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to process claim')
      }
      
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
  }

  return (
    <div className="claims-form-container">
      <header className="chat-header" style={{ marginBottom: '2rem' }}>
        <div>
          <h1>Motor Claims Estimator</h1>
          <div className="subtitle">Upload damage photos for instant AI repair cost breakdown</div>
        </div>
      </header>
      
      <div className="claims-content">
        <form onSubmit={handleSubmit} className="premium-form">
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

          {loading ? (
            <div style={{ textAlign: "center", padding: "24px", background: "#f8fafc", borderRadius: "8px", border: "1px dashed #cbd5e1", marginTop: "1rem" }}>
              <div className="spinner" style={{ margin: "0 auto", width: "32px", height: "32px", border: "3px solid #e2e8f0", borderTopColor: "#3b82f6", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
              <p style={{ marginTop: "14px", color: "#475569", fontWeight: 500 }}>
                {LOADING_STEPS[loadingStep]}
              </p>
              <div style={{ display: "flex", gap: "8px", justifyContent: "center", marginTop: "12px" }}>
                {LOADING_STEPS.map((_, i) => (
                  <div key={i} style={{
                    width: "8px", height: "8px", borderRadius: "50%",
                    background: i <= loadingStep ? "#3B82F6" : "#E2E8F0",
                    transition: "background 0.3s ease"
                  }}/>
                ))}
              </div>
            </div>
          ) : (
            <button type="submit" className="btn-submit" disabled={!photo}>
              Submit Claim Request
            </button>
          )}
        </form>

        <AnimatePresence>
          {result && (
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              className="claim-result"
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
                    {result.notes}
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

              <div className="receipt-details">
                <div className="receipt-row">
                  <span>Vehicle</span>
                  <strong>{result.vehicle}</strong>
                </div>
                <div className="receipt-row">
                  <span>Claimant</span>
                  <strong>{result.claimant_name}</strong>
                </div>

                {/* Image Analysis Banner */}
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
                    {/* Confidence badge */}
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
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
