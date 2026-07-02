import { useState, useRef, useEffect } from "react"
import { apiFetch } from "../utils/api"
import { motion, AnimatePresence } from "framer-motion"
import {
  Sparkles, Zap, Clock, ChevronRight,
  CheckCircle2, XCircle, AlertTriangle,
  FileText, Car, Search, BarChart3, RefreshCcw,
  ArrowRight, History, Loader2
} from "lucide-react"

const AGENT_META = {
  "Policy RAG":       { icon: FileText,   color: "#6366F1", bg: "#EEF2FF", border: "#C7D2FE" },
  "Claims Estimator": { icon: Car,        color: "#EA580C", bg: "#FFF7ED", border: "#FDBA74" },
  "Fraud Detector":   { icon: Search,     color: "#DC2626", bg: "#FEF2F2", border: "#FECACA" },
  "Risk Profiler":    { icon: BarChart3,  color: "#0284C7", bg: "#F0F9FF", border: "#BAE6FD" },
  "Renewal Agent":    { icon: RefreshCcw, color: "#16A34A", bg: "#F0FDF4", border: "#BBF7D0" },
}

const STATUS_STYLE = {
  success: { icon: CheckCircle2,  color: "#16A34A", bg: "#DCFCE7", border: "#86EFAC" },
  failed:  { icon: XCircle,       color: "#DC2626", bg: "#FEE2E2", border: "#FCA5A5" },
  skipped: { icon: AlertTriangle, color: "#D97706", bg: "#FEF3C7", border: "#FDE68A" },
}

const EXAMPLE_QUERIES = [
  { text: "I had an accident with my car, policy DG-MOTOR-2025-042. What should I do?", emoji: "🚗" },
  { text: "What does my health insurance cover for hospitalization?", emoji: "🏥" },
  { text: "My crop was damaged by heavy rains. How do I file a claim?", emoji: "🌾" },
  { text: "I want to find a better deal for my motor insurance renewal.", emoji: "💰" },
  { text: "Check if my claim for ₹45,000 motor damage is valid.", emoji: "🔍" },
]

const LOADING_STEPS = [
  { text: "Analyzing your query...", icon: Sparkles },
  { text: "Classifying intent...", icon: Zap },
  { text: "Running AI agents...", icon: Loader2 },
  { text: "Aggregating results...", icon: BarChart3 },
  { text: "Generating unified report...", icon: FileText },
]

export default function AgentAutomation() {
  const [message, setMessage]       = useState("")
  const [result, setResult]         = useState(null)
  const [loading, setLoading]       = useState(false)
  const [loadingStep, setStep]      = useState(0)
  const [error, setError]           = useState(null)
  const [history, setHistory]       = useState([])
  const textareaRef = useRef(null)
  const resultRef   = useRef(null)

  useEffect(() => {
    if (result && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }, [result])

  const runLoadingSteps = () => {
    LOADING_STEPS.forEach((_, i) => setTimeout(() => setStep(i), i * 900))
  }

  const handleSubmit = async (msg) => {
    const query = msg || message
    if (!query.trim()) return

    setLoading(true)
    setResult(null)
    setError(null)
    setStep(0)
    runLoadingSteps()

    try {
      const res = await apiFetch("/automation/run", {
        method: "POST",
        body: JSON.stringify({ message: query }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()
      setResult(data)
      setHistory(prev => [{ query, result: data, ts: new Date() }, ...prev.slice(0, 4)])
    } catch (e) {
      setError(e.message || "Automation failed.")
    } finally {
      setLoading(false)
    }
  }

  const confidenceColor = (c) => {
    if (c === "High")   return { bg: "#DCFCE7", color: "#166534", border: "#86EFAC" }
    if (c === "Medium") return { bg: "#FEF9C3", color: "#854D0E", border: "#FDE68A" }
    return { bg: "#FEE2E2", color: "#991B1B", border: "#FECACA" }
  }

  return (
    <div className="claims-form-container">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="welcome-icon" style={{ width: 42, height: 42, borderRadius: 12, fontSize: "1.3rem" }}>
            <Sparkles size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: "1.15rem" }}>Agent Automation</h1>
            <span className="subtitle">Orchestrate all AI agents with a single message</span>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="badge live" style={{
            background: "linear-gradient(135deg, #6366F1, #8B5CF6)",
            color: "#fff", padding: "4px 12px", borderRadius: 999,
            fontSize: "0.75rem", fontWeight: 600
          }}>Phase 7</span>
        </div>
      </div>

      <div className="claims-content" style={{ paddingTop: "1.5rem" }}>

        {/* Example queries */}
        {!result && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div style={{ textAlign: "center", marginBottom: 24 }}>
              <h2 style={{ fontSize: "1.6rem", marginBottom: 8 }}>What can I help you with?</h2>
              <p style={{ color: "#6B7280", fontSize: "0.95rem" }}>
                Describe your insurance situation — AI agents will handle the rest automatically
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 10, marginBottom: 24 }}>
              {EXAMPLE_QUERIES.map((q, i) => (
                <motion.button
                  key={i}
                  whileHover={{ scale: 1.015, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => { setMessage(q.text); handleSubmit(q.text) }}
                  style={{
                    display: "flex", alignItems: "center", gap: 12,
                    padding: "14px 18px", borderRadius: 14,
                    border: "1px solid #E5E7EB", background: "#fff",
                    cursor: "pointer", textAlign: "left", fontSize: "0.9rem",
                    color: "#374151", transition: "all 0.2s",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.04)"
                  }}
                >
                  <span style={{ fontSize: "1.3rem", flexShrink: 0 }}>{q.emoji}</span>
                  <span style={{ flex: 1 }}>{q.text}</span>
                  <ArrowRight size={16} style={{ color: "#9CA3AF", flexShrink: 0 }} />
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}

        {/* Input area */}
        <div className="premium-form" style={{ padding: "1.25rem 1.5rem" }}>
          <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
            <textarea
              ref={textareaRef}
              value={message}
              onChange={e => setMessage(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
              placeholder="Describe your insurance situation in plain English..."
              rows={2}
              style={{
                flex: 1, padding: "12px 16px", borderRadius: 12,
                border: "1.5px solid #E5E7EB", fontSize: "0.95rem",
                resize: "none", outline: "none", background: "#F8FAFC",
                fontFamily: "Inter, sans-serif", transition: "all 0.2s"
              }}
              onFocus={e => {
                e.target.style.borderColor = "#6366F1"
                e.target.style.background = "#fff"
                e.target.style.boxShadow = "0 0 0 4px rgba(99,102,241,0.1)"
              }}
              onBlur={e => {
                e.target.style.borderColor = "#E5E7EB"
                e.target.style.background = "#F8FAFC"
                e.target.style.boxShadow = "none"
              }}
            />
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => handleSubmit()}
              disabled={loading || !message.trim()}
              style={{
                padding: "12px 24px", borderRadius: 12, border: "none",
                background: loading ? "#A5B4FC" : "linear-gradient(135deg, #6366F1, #8B5CF6)",
                color: "#fff", fontWeight: 600, fontSize: "0.95rem",
                cursor: loading ? "not-allowed" : "pointer",
                display: "flex", alignItems: "center", gap: 8,
                minWidth: 110, justifyContent: "center",
                boxShadow: "0 4px 15px rgba(99,102,241,0.3)"
              }}
            >
              {loading ? (
                <><Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} /> Running</>
              ) : (
                <><Sparkles size={18} /> Run AI</>
              )}
            </motion.button>
          </div>
        </div>

        {/* Loading state */}
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="premium-form"
              style={{ padding: "1.5rem", textAlign: "center" }}
            >
              <div style={{
                display: "flex", alignItems: "center", justifyContent: "center",
                gap: 10, marginBottom: 16, color: "#6366F1", fontWeight: 600
              }}>
                {(() => {
                  const StepIcon = LOADING_STEPS[loadingStep]?.icon || Sparkles
                  return <StepIcon size={20} style={{ animation: "spin 2s linear infinite" }} />
                })()}
                <span>{LOADING_STEPS[loadingStep]?.text}</span>
              </div>

              <div style={{ display: "flex", gap: 6, justifyContent: "center" }}>
                {LOADING_STEPS.map((_, i) => (
                  <motion.div
                    key={i}
                    animate={{
                      scale: i === loadingStep ? 1.3 : 1,
                      background: i <= loadingStep ? "#6366F1" : "#E5E7EB"
                    }}
                    transition={{ duration: 0.3 }}
                    style={{
                      width: 8, height: 8, borderRadius: "50%",
                      background: i <= loadingStep ? "#6366F1" : "#E5E7EB",
                    }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              padding: "14px 18px", background: "#FEE2E2",
              borderRadius: 12, color: "#DC2626", fontSize: "0.9rem",
              display: "flex", alignItems: "center", gap: 10,
              border: "1px solid #FECACA"
            }}
          >
            <XCircle size={18} />
            {error}
          </motion.div>
        )}

        {/* Results */}
        {result && (
          <motion.div
            ref={resultRef}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            style={{ display: "flex", flexDirection: "column", gap: 16 }}
          >
            {/* Intent banner */}
            <div style={{
              background: "linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%)",
              border: "1px solid #C7D2FE", borderRadius: 16,
              padding: "18px 22px",
              display: "flex", justifyContent: "space-between", alignItems: "center"
            }}>
              <div>
                <div style={{
                  fontSize: "0.7rem", color: "#6366F1", fontWeight: 600,
                  textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4
                }}>
                  Detected Intent
                </div>
                <div style={{
                  fontWeight: 700, fontSize: "1.1rem",
                  textTransform: "capitalize", color: "#312E81"
                }}>
                  {result.intent.replace(/_/g, " ")}
                </div>
                <div style={{
                  fontSize: "0.8rem", color: "#6366F1", marginTop: 2,
                  textTransform: "uppercase", fontWeight: 500
                }}>
                  {result.insurance_type} insurance
                </div>
              </div>
              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#4F46E5" }}>
                    {result.agents_run.length}
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "#6B7280" }}>Agents</div>
                </div>
                <div style={{
                  width: 1, height: 36, background: "#C7D2FE"
                }} />
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#4F46E5" }}>
                    {(result.total_time_ms / 1000).toFixed(1)}s
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "#6B7280" }}>Total</div>
                </div>
                <div style={{
                  width: 1, height: 36, background: "#C7D2FE"
                }} />
                <div style={{ textAlign: "center" }}>
                  {(() => {
                    const cc = confidenceColor(result.confidence)
                    return (
                      <span style={{
                        background: cc.bg, color: cc.color,
                        border: `1px solid ${cc.border}`,
                        padding: "4px 12px", borderRadius: 999,
                        fontSize: "0.75rem", fontWeight: 600
                      }}>
                        {result.confidence}
                      </span>
                    )
                  })()}
                  <div style={{ fontSize: "0.7rem", color: "#6B7280", marginTop: 4 }}>Confidence</div>
                </div>
              </div>
            </div>

            {/* Agent execution timeline */}
            <div className="premium-form" style={{ padding: "20px 24px" }}>
              <div style={{
                fontWeight: 700, marginBottom: 16, fontSize: "1rem",
                display: "flex", alignItems: "center", gap: 8
              }}>
                <Zap size={18} style={{ color: "#6366F1" }} />
                Agent Execution Pipeline
              </div>
              {result.agents_run.map((agent, i) => {
                const meta = AGENT_META[agent.agent_name] || { icon: Sparkles, color: "#6B7280", bg: "#F3F4F6", border: "#E5E7EB" }
                const ss   = STATUS_STYLE[agent.status]   || STATUS_STYLE.skipped
                const AgentIcon  = meta.icon
                const StatusIcon = ss.icon

                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    style={{
                      display: "flex", alignItems: "flex-start",
                      gap: 14, marginBottom: i < result.agents_run.length - 1 ? 12 : 0
                    }}
                  >
                    {/* Timeline connector */}
                    <div style={{
                      display: "flex", flexDirection: "column",
                      alignItems: "center", minWidth: 28
                    }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: "50%",
                        background: meta.bg, border: `2px solid ${meta.border}`,
                        display: "flex", alignItems: "center",
                        justifyContent: "center",
                      }}>
                        <AgentIcon size={14} style={{ color: meta.color }} />
                      </div>
                      {i < result.agents_run.length - 1 && (
                        <div style={{
                          width: 2, height: 20,
                          background: "linear-gradient(180deg, #C7D2FE, #E5E7EB)",
                          marginTop: 4
                        }}/>
                      )}
                    </div>

                    {/* Agent card */}
                    <div style={{
                      flex: 1, background: meta.bg,
                      border: `1px solid ${meta.border}`,
                      borderRadius: 12, padding: "12px 16px",
                    }}>
                      <div style={{
                        display: "flex",
                        justifyContent: "space-between", alignItems: "center"
                      }}>
                        <span style={{
                          fontWeight: 600, fontSize: "0.9rem", color: meta.color,
                          display: "flex", alignItems: "center", gap: 6
                        }}>
                          {agent.agent_name}
                          <StatusIcon size={14} style={{ color: ss.color }} />
                        </span>
                        <span style={{
                          fontSize: "0.75rem", color: "#9CA3AF",
                          display: "flex", alignItems: "center", gap: 4
                        }}>
                          <Clock size={12} />
                          {agent.duration_ms}ms
                        </span>
                      </div>
                      <div style={{
                        fontSize: "0.85rem", color: "#4B5563", marginTop: 6,
                        lineHeight: 1.4
                      }}>
                        {agent.summary}
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </div>

            {/* Key metrics */}
            {(result.claim_result || result.fraud_result || result.risk_result || result.renewal_result) && (
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: 12
              }}>
                {result.claim_result && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    style={{
                      background: "linear-gradient(135deg, #FFF7ED, #FFEDD5)",
                      border: "1px solid #FDBA74",
                      borderRadius: 14, padding: "16px 18px"
                    }}
                  >
                    <div style={{ fontSize: "0.7rem", color: "#9A3412", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      Claim Estimate
                    </div>
                    <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#EA580C", marginTop: 6 }}>
                      ₹{result.claim_result.covered_amount?.toLocaleString("en-IN")}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "#9A3412", marginTop: 2 }}>covered amount</div>
                  </motion.div>
                )}

                {result.fraud_result && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    style={{
                      background: result.fraud_result.fraud_score > 70
                        ? "linear-gradient(135deg, #FEE2E2, #FECACA)"
                        : result.fraud_result.fraud_score > 40
                          ? "linear-gradient(135deg, #FEF3C7, #FDE68A)"
                          : "linear-gradient(135deg, #DCFCE7, #BBF7D0)",
                      border: `1px solid ${result.fraud_result.fraud_score > 70 ? "#FCA5A5"
                        : result.fraud_result.fraud_score > 40 ? "#FCD34D" : "#86EFAC"}`,
                      borderRadius: 14, padding: "16px 18px"
                    }}
                  >
                    <div style={{ fontSize: "0.7rem", color: "#6B7280", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      Fraud Score
                    </div>
                    <div style={{
                      fontSize: "1.5rem", fontWeight: 800, marginTop: 6,
                      color: result.fraud_result.fraud_score > 70 ? "#DC2626"
                        : result.fraud_result.fraud_score > 40 ? "#D97706" : "#16A34A"
                    }}>
                      {result.fraud_result.fraud_score}/100
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "#6B7280", marginTop: 2 }}>
                      {result.fraud_result.verdict}
                    </div>
                  </motion.div>
                )}

                {result.risk_result && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    style={{
                      background: "linear-gradient(135deg, #F0F9FF, #E0F2FE)",
                      border: "1px solid #BAE6FD",
                      borderRadius: 14, padding: "16px 18px"
                    }}
                  >
                    <div style={{ fontSize: "0.7rem", color: "#0369A1", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      Risk Score
                    </div>
                    <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#0284C7", marginTop: 6 }}>
                      {result.risk_result.risk_score}/100
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "#0369A1", marginTop: 2 }}>
                      {result.risk_result.risk_category} risk
                    </div>
                  </motion.div>
                )}

                {result.renewal_result && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    style={{
                      background: "linear-gradient(135deg, #F0FDF4, #DCFCE7)",
                      border: "1px solid #86EFAC",
                      borderRadius: 14, padding: "16px 18px"
                    }}
                  >
                    <div style={{ fontSize: "0.7rem", color: "#166534", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      Best Renewal
                    </div>
                    <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "#16A34A", marginTop: 6 }}>
                      {result.renewal_result.best_deal?.provider_name}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "#166534", marginTop: 2 }}>
                      Save ₹{result.renewal_result.savings_amount?.toLocaleString("en-IN")}/yr
                    </div>
                  </motion.div>
                )}
              </div>
            )}

            {/* Unified report */}
            <div className="premium-form" style={{ padding: "20px 24px" }}>
              <div style={{
                fontWeight: 700, marginBottom: 12, fontSize: "1rem",
                display: "flex", alignItems: "center", gap: 8
              }}>
                <FileText size={18} style={{ color: "#6366F1" }} />
                Unified Report
                {result.degraded && (
                  <span style={{
                    marginLeft: 8, fontSize: "0.7rem",
                    background: "linear-gradient(135deg, #FEF3C7, #FDE68A)",
                    color: "#92400E", padding: "3px 10px", borderRadius: 999,
                    fontWeight: 600
                  }}>
                    Offline Mode
                  </span>
                )}
              </div>
              <p style={{
                fontSize: "0.9rem", color: "#374151",
                lineHeight: 1.7, margin: 0, whiteSpace: "pre-wrap"
              }}>
                {result.final_report}
              </p>
            </div>

            {/* Next steps */}
            <div style={{
              background: "linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%)",
              border: "1px solid #C7D2FE",
              borderRadius: 16, padding: "20px 24px"
            }}>
              <div style={{
                fontWeight: 700, color: "#312E81", marginBottom: 14,
                display: "flex", alignItems: "center", gap: 8, fontSize: "1rem"
              }}>
                <ChevronRight size={18} />
                Recommended Next Steps
              </div>
              {result.next_steps.map((step, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  style={{
                    display: "flex", alignItems: "flex-start",
                    gap: 12, marginBottom: i < result.next_steps.length - 1 ? 10 : 0
                  }}
                >
                  <span style={{
                    minWidth: 24, height: 24, borderRadius: "50%",
                    background: "linear-gradient(135deg, #6366F1, #8B5CF6)",
                    color: "#fff",
                    display: "flex", alignItems: "center",
                    justifyContent: "center", fontSize: "0.75rem", fontWeight: 700,
                    flexShrink: 0
                  }}>
                    {i + 1}
                  </span>
                  <span style={{
                    fontSize: "0.9rem", color: "#312E81", lineHeight: 1.5
                  }}>
                    {step}
                  </span>
                </motion.div>
              ))}
            </div>

            {/* Query history */}
            {history.length > 1 && (
              <div className="premium-form" style={{ padding: "16px 20px" }}>
                <div style={{
                  fontWeight: 600, marginBottom: 10, fontSize: "0.9rem",
                  display: "flex", alignItems: "center", gap: 8, color: "#6B7280"
                }}>
                  <History size={16} />
                  Recent Queries
                </div>
                {history.slice(1).map((h, i) => (
                  <div
                    key={i}
                    onClick={() => { setMessage(h.query); handleSubmit(h.query) }}
                    style={{
                      fontSize: "0.85rem", color: "#6B7280", padding: "8px 0",
                      borderBottom: i < history.length - 2 ? "1px solid #F3F4F6" : "none",
                      cursor: "pointer", transition: "color 0.2s",
                      display: "flex", alignItems: "center", gap: 8
                    }}
                    onMouseEnter={e => e.currentTarget.style.color = "#6366F1"}
                    onMouseLeave={e => e.currentTarget.style.color = "#6B7280"}
                  >
                    <ArrowRight size={14} style={{ flexShrink: 0 }} />
                    {h.query.length > 80 ? h.query.slice(0, 80) + "..." : h.query}
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Inline keyframe for spinner */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
