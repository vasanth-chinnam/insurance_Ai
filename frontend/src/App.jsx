import { useState, useEffect } from 'react'
import { apiFetch } from './utils/api'
import { 
  FileText, 
  Search, 
  BarChart3, 
  Leaf, 
  RefreshCcw, 
  Menu, 
  X, 
  ShieldCheck, 
  AlertCircle,
  Stethoscope,
  Sparkles
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import PolicyChat from './components/PolicyChat'
import MotorClaimsForm from './components/MotorClaimsForm'
import FraudDetection from './components/FraudDetection'
import RiskProfiler from './components/RiskProfiler'
import CropInsurance from './components/CropInsurance'
import RenewalCompare from './components/RenewalCompare'
import AgentAutomation from './components/AgentAutomation'
import Analytics from './components/Analytics'
import AuditLogs from './components/AuditLogs'
import AdminPanel from './components/AdminPanel'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './LoginPage'
import RegisterPage from './RegisterPage'
import { useAuth } from './AuthContext'
import { canAccess, getRoleLabel, getRoleBadgeColor } from './rbac'
import './App.css'

const API_BASE = '/api'

const NAV_ITEMS = [
  { id: 'policy_qa', icon: Stethoscope, label: 'Policy Q&A', badge: 'Live', phase: null },
  { id: 'claim_estimator', icon: FileText, label: 'Claim Estimator', badge: 'Live', phase: 2 },
  { id: 'fraud_detection', icon: Search, label: 'Fraud Detection', badge: 'Live', phase: 3 },
  { id: 'risk_profiler', icon: BarChart3, label: 'Risk Profiler', badge: 'Live', phase: 4 },
  { id: 'crop_insurance', icon: Leaf, label: 'Crop Insurance', badge: 'Live', phase: 5 },
  { id: 'renewal_compare', icon: RefreshCcw, label: 'Renewal Compare', badge: 'Live', phase: 6 },
  { id: 'agent_automation', icon: Sparkles, label: 'Agent Automation', badge: 'Live', phase: 7 },
  { id: 'analytics', icon: BarChart3, label: 'Analytics', badge: 'New', phase: null },
  { id: 'audit_logs', icon: FileText, label: 'Audit Logs', badge: 'Admin', phase: null },
  { id: 'admin_panel', icon: ShieldCheck, label: 'Admin Panel', badge: 'Admin', phase: null },
]

function App() {
  const { user, loading, logout } = useAuth()
  const [authMode, setAuthMode] = useState("login")
  const [activeNav, setActiveNav] = useState('policy_qa')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [toast, setToast] = useState(null)
  const [pendingRequest, setPendingRequest] = useState(null)
  
  // Lift chat messages state so history persists between tab switches
  const [messages, setMessages] = useState([])

  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [upgradeForm, setUpgradeForm] = useState({
    requested_role: "agent",
    company_name: "",
    employee_id: "",
    license_number: "",
  })
  const [upgradeError, setUpgradeError] = useState(null)
  const [upgradeLoading, setUpgradeLoading] = useState(false)

  const handleUpgradeSubmit = async () => {
    setUpgradeError(null)
    if (upgradeForm.requested_role === "agent" && (!upgradeForm.company_name || !upgradeForm.license_number)) {
      setUpgradeError("Please enter your Agency Name and Agent License Number")
      return
    }
    if (upgradeForm.requested_role === "fraud_investigator" && (!upgradeForm.company_name || !upgradeForm.license_number)) {
      setUpgradeError("Please enter your Company Name and Investigator License Number")
      return
    }
    if ((upgradeForm.requested_role === "manager" || upgradeForm.requested_role === "admin") && (!upgradeForm.company_name || !upgradeForm.employee_id)) {
      setUpgradeError("Please enter your Company Name and Employee ID")
      return
    }

    setUpgradeLoading(true)
    try {
      const res = await apiFetch("/auth/role-request", {
        method: "POST",
        body: JSON.stringify(upgradeForm),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || "Submission failed")
      }
      showToast("Role upgrade request submitted successfully!", "success")
      setPendingRequest({
        requested_role: upgradeForm.requested_role,
        status: "pending"
      })
      setShowUpgradeModal(false)
    } catch (err) {
      setUpgradeError(err.message)
    } finally {
      setUpgradeLoading(false)
    }
  }

  useEffect(() => {
    if (user) {
      const fetchProfile = async () => {
        try {
          const res = await apiFetch("/auth/me")
          if (res.ok) {
            const data = await res.json()
            if (data.role !== user.role) {
              const updatedUser = { ...user, role: data.role }
              localStorage.setItem("insureai_user", JSON.stringify(updatedUser))
              window.location.reload()
            }
            if (data.pending_role_request) {
              setPendingRequest(data.pending_role_request)
            } else {
              setPendingRequest(null)
            }
          }
        } catch (err) {
          console.error("Failed to fetch user profile:", err)
        }
      }
      fetchProfile()
    }
  }, [user])

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 32, background: "#F3F4F6" }}>
        🛡️
      </div>
    )
  }

  if (!user) {
    return authMode === "login"
      ? <LoginPage onSwitch={() => setAuthMode("register")} />
      : <RegisterPage onSwitch={() => setAuthMode("login")} />
  }

  return (
    <div className="app-layout">
      {/* ── Sidebar ──────────────────────────────────── */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2><span>🛡️</span> InsureAI</h2>
          <p>Next-Gen Insurance Intelligence</p>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-label">Main Features</div>
          {NAV_ITEMS.filter(item => canAccess(user?.role || 'customer', item.id)).map(item => {
            const Icon = item.icon
            return (
              <div
                key={item.id}
                className={`nav-item ${activeNav === item.id ? 'active' : ''}`}
                onClick={() => { 
                  setActiveNav(item.id)
                  setSidebarOpen(false)
                }}
              >
                <Icon className="icon" size={20} />
                <span className="label">{item.label}</span>
                {item.badge && <span className={`badge ${item.badge === 'Live' ? 'live' : ''}`}>{item.badge}</span>}
              </div>
            )
          })}
        </nav>

        <div className="sidebar-footer" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 0", borderBottom: "1px solid #374151" }}>
            {user.avatar ? (
              <img src={user.avatar} alt={user.name} style={{ width: 32, height: 32, borderRadius: "50%", objectFit: "cover" }} />
            ) : (
              <div style={{ width: 32, height: 32, borderRadius: "50%", background: "#4F46E5", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 600 }}>
                {user.name.charAt(0).toUpperCase()}
              </div>
            )}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#fff", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>{user.name}</div>
              <div style={{ fontSize: 11, color: "#9CA3AF", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>{user.email}</div>
              
              {/* Role badge */}
              <div style={{ marginTop: 6 }}>
                <span style={{
                  fontSize: 10,
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: 999,
                  background: getRoleBadgeColor(user?.role || 'customer').bg,
                  color: getRoleBadgeColor(user?.role || 'customer').color,
                  display: "inline-block",
                  alignSelf: "flex-start"
                }}>
                  {getRoleLabel(user?.role || 'customer')}
                </span>
              </div>
              {user?.role === "customer" && !pendingRequest && (
                <div style={{ marginTop: 6 }}>
                  <span 
                    onClick={() => setShowUpgradeModal(true)}
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      padding: "2px 8px",
                      borderRadius: 999,
                      background: "#2563EB",
                      color: "#fff",
                      cursor: "pointer",
                      display: "inline-block",
                      boxShadow: "0 1px 3px rgba(0,0,0,0.2)"
                    }}
                  >
                    Upgrade Role 🚀
                  </span>
                </div>
              )}
            </div>
            <button onClick={logout} title="Log out" style={{ background: "none", border: "none", color: "#EF4444", cursor: "pointer", padding: 4, fontSize: "1.1rem" }}>
              🚪
            </button>
          </div>
          <div className="status">
            <span className="status-dot"></span>
            AI Engine Online
          </div>
        </div>
      </aside>

      {/* ── Main Area ─────────────────────────────────────── */}
      <main className="main-area relative">
        <button className="btn-icon btn-menu mobile-menu-btn" onClick={() => setSidebarOpen(s => !s)} style={{ position: 'absolute', top: '15px', left: '15px', zIndex: 10 }}>
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        {pendingRequest && (
          <div style={{
            background: "#EFF6FF",
            border: "1px solid #BFDBFE",
            borderRadius: 12,
            padding: "16px 20px",
            margin: "20px 40px 0 40px",
            display: "flex",
            alignItems: "center",
            gap: 12,
            boxShadow: "0 2px 4px rgba(0,0,0,0.02)"
          }}>
            <span style={{ fontSize: 20 }}>⏳</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#1E40AF" }}>
                Role Verification Request Pending
              </div>
              <div style={{ fontSize: 13, color: "#1E3A8A", marginTop: 2 }}>
                Your request to become a <strong>{getRoleLabel(pendingRequest.requested_role)}</strong> is currently under review by an administrator. You are currently viewing the platform with <strong>{getRoleLabel(user?.role)}</strong> privileges.
              </div>
            </div>
          </div>
        )}

        {activeNav === 'policy_qa' && (
          <ProtectedRoute role={user?.role} allowedRoles={['customer', 'agent', 'manager', 'admin']}>
            <PolicyChat 
              messages={messages} 
              setMessages={setMessages} 
              API_BASE={API_BASE} 
              showToast={showToast} 
            />
          </ProtectedRoute>
        )}

        {activeNav === 'claim_estimator' && (
          <ProtectedRoute role={user?.role} allowedRoles={['customer', 'agent', 'manager', 'admin']}>
            <MotorClaimsForm 
              API_BASE={API_BASE} 
              showToast={showToast} 
            />
          </ProtectedRoute>
        )}

        {activeNav === 'fraud_detection' && (
          <ProtectedRoute role={user?.role} allowedRoles={['fraud_investigator', 'manager', 'admin']}>
            <FraudDetection
              showToast={showToast}
            />
          </ProtectedRoute>
        )}

        {activeNav === 'risk_profiler' && (
          <ProtectedRoute role={user?.role} allowedRoles={['customer', 'agent', 'fraud_investigator', 'manager', 'admin']}>
            <RiskProfiler />
          </ProtectedRoute>
        )}

        {activeNav === 'crop_insurance' && (
          <ProtectedRoute role={user?.role} allowedRoles={['agent', 'manager', 'admin']}>
            <CropInsurance />
          </ProtectedRoute>
        )}

        {activeNav === 'renewal_compare' && (
          <ProtectedRoute role={user?.role} allowedRoles={['customer', 'agent', 'manager', 'admin']}>
            <RenewalCompare />
          </ProtectedRoute>
        )}

        {activeNav === 'agent_automation' && (
          <ProtectedRoute role={user?.role} allowedRoles={['agent', 'fraud_investigator', 'manager', 'admin']}>
            <AgentAutomation />
          </ProtectedRoute>
        )}

        {activeNav === 'analytics' && (
          <ProtectedRoute role={user?.role} allowedRoles={['manager', 'admin']}>
            <Analytics />
          </ProtectedRoute>
        )}

        {activeNav === 'audit_logs' && (
          <ProtectedRoute role={user?.role} allowedRoles={['admin']}>
            <AuditLogs />
          </ProtectedRoute>
        )}

        {activeNav === 'admin_panel' && (
          <ProtectedRoute role={user?.role} allowedRoles={['admin']}>
            <AdminPanel showToast={showToast} />
          </ProtectedRoute>
        )}
      </main>

      {/* ── Global Toast ──────────────────────────────────── */}
      <AnimatePresence>
        {toast && (
          <motion.div 
            initial={{ opacity: 0, y: 50, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 20, x: '-50%' }}
            className={`toast ${toast.type}`}
          >
            {toast.type === 'success' ? <ShieldCheck size={18} /> : <AlertCircle size={18} />}
            <span>{toast.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Upgrade Role Modal ───────────────────────────────── */}
      {showUpgradeModal && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(0,0,0,0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 9999
        }}>
          <div style={{
            background: "#fff",
            borderRadius: 16,
            padding: "28px 24px",
            width: 420,
            boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)",
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
          }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: "#1E293B" }}>Request Role Upgrade</h3>
            <p style={{ fontSize: 13, color: "#64748B", marginTop: 4, marginBottom: 20 }}>
              Request a security role upgrade. This will be sent to the System Administrator for verification.
            </p>

            {/* Role Select */}
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 6, color: "#334155" }}>
                Desired Role
              </label>
              <select
                value={upgradeForm.requested_role}
                onChange={e => setUpgradeForm({ ...upgradeForm, requested_role: e.target.value })}
                style={{
                  width: "100%", padding: "10px 14px",
                  borderRadius: 8, border: "1px solid #CBD5E1",
                  fontSize: 14, background: "#fff", outline: "none"
                }}
              >
                <option value="agent">Agent</option>
                <option value="fraud_investigator">Fraud Investigator</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            {/* Dynamic Inputs */}
            {upgradeForm.requested_role === "agent" && (
              <>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 6, color: "#475569" }}>Agency/Company Name *</label>
                  <input
                    type="text"
                    value={upgradeForm.company_name}
                    onChange={e => setUpgradeForm({ ...upgradeForm, company_name: e.target.value })}
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #CBD5E1", fontSize: 14, boxSizing: "border-box" }}
                  />
                </div>
                <div style={{ marginBottom: 20 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 6, color: "#475569" }}>Agent License Number *</label>
                  <input
                    type="text"
                    value={upgradeForm.license_number}
                    onChange={e => setUpgradeForm({ ...upgradeForm, license_number: e.target.value })}
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #CBD5E1", fontSize: 14, boxSizing: "border-box" }}
                  />
                </div>
              </>
            )}

            {upgradeForm.requested_role === "fraud_investigator" && (
              <>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 6, color: "#475569" }}>Investigator Agency/Company *</label>
                  <input
                    type="text"
                    value={upgradeForm.company_name}
                    onChange={e => setUpgradeForm({ ...upgradeForm, company_name: e.target.value })}
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #CBD5E1", fontSize: 14, boxSizing: "border-box" }}
                  />
                </div>
                <div style={{ marginBottom: 20 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 6, color: "#475569" }}>Investigator License Number *</label>
                  <input
                    type="text"
                    value={upgradeForm.license_number}
                    onChange={e => setUpgradeForm({ ...upgradeForm, license_number: e.target.value })}
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #CBD5E1", fontSize: 14, boxSizing: "border-box" }}
                  />
                </div>
              </>
            )}

            {upgradeForm.requested_role === "manager" && (
              <>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 6, color: "#475569" }}>Company Name *</label>
                  <input
                    type="text"
                    value={upgradeForm.company_name}
                    onChange={e => setUpgradeForm({ ...upgradeForm, company_name: e.target.value })}
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #CBD5E1", fontSize: 14, boxSizing: "border-box" }}
                  />
                </div>
                <div style={{ marginBottom: 20 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 6, color: "#475569" }}>Employee ID *</label>
                  <input
                    type="text"
                    value={upgradeForm.employee_id}
                    onChange={e => setUpgradeForm({ ...upgradeForm, employee_id: e.target.value })}
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #CBD5E1", fontSize: 14, boxSizing: "border-box" }}
                  />
                </div>
              </>
            )}

            {upgradeForm.requested_role === "admin" && (
              <>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 6, color: "#475569" }}>Company Name *</label>
                  <input
                    type="text"
                    value={upgradeForm.company_name}
                    onChange={e => setUpgradeForm({ ...upgradeForm, company_name: e.target.value })}
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #CBD5E1", fontSize: 14, boxSizing: "border-box" }}
                  />
                </div>
                <div style={{ marginBottom: 20 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 6, color: "#475569" }}>Employee ID *</label>
                  <input
                    type="text"
                    value={upgradeForm.employee_id}
                    onChange={e => setUpgradeForm({ ...upgradeForm, employee_id: e.target.value })}
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #CBD5E1", fontSize: 14, boxSizing: "border-box" }}
                  />
                </div>
              </>
            )}

            {upgradeError && (
              <div style={{ padding: 10, background: "#FEE2E2", color: "#DC2626", borderRadius: 8, fontSize: 13, marginBottom: 14 }}>
                {upgradeError}
              </div>
            )}

            {/* Actions */}
            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
              <button
                onClick={() => setShowUpgradeModal(false)}
                disabled={upgradeLoading}
                style={{
                  padding: "9px 16px", borderRadius: 8, border: "1px solid #CBD5E1",
                  background: "#fff", color: "#475569", fontSize: 14, fontWeight: 500, cursor: "pointer", outline: "none"
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleUpgradeSubmit}
                disabled={upgradeLoading}
                style={{
                  padding: "9px 16px", borderRadius: 8, border: "none",
                  background: "#2563EB", color: "#fff", fontSize: 14, fontWeight: 600, cursor: "pointer", outline: "none"
                }}
              >
                {upgradeLoading ? "Submitting..." : "Submit Request"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
