import { useState } from 'react'
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
import LoginPage from './LoginPage'
import RegisterPage from './RegisterPage'
import { useAuth } from './AuthContext'
import './App.css'

const API_BASE = '/api'

const NAV_ITEMS = [
  { id: 'policy_rag', icon: Stethoscope, label: 'Policy Q&A', badge: 'Live', phase: null },
  { id: 'motor_claim', icon: FileText, label: 'Claim Estimator', badge: 'Live', phase: 2 },
  { id: 'fraud_detection', icon: Search, label: 'Fraud Detection', badge: 'Live', phase: 3 },
  { id: 'risk_profiler', icon: BarChart3, label: 'Risk Profiler', badge: 'Live', phase: 4 },
  { id: 'crop_payout', icon: Leaf, label: 'Crop Insurance', badge: 'Live', phase: 5 },
  { id: 'renewal_agent', icon: RefreshCcw, label: 'Renewal Compare', badge: 'Live', phase: 6 },
  { id: 'agent_automation', icon: Sparkles, label: 'Agent Automation', badge: 'Live', phase: 7 },
]

function App() {
  const { user, loading, logout } = useAuth()
  const [authMode, setAuthMode] = useState("login")
  const [activeNav, setActiveNav] = useState('policy_rag')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [toast, setToast] = useState(null)
  
  // Lift chat messages state so history persists between tab switches
  const [messages, setMessages] = useState([])

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
          {NAV_ITEMS.map(item => {
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

        {activeNav === 'policy_rag' && (
          <PolicyChat 
            messages={messages} 
            setMessages={setMessages} 
            API_BASE={API_BASE} 
            showToast={showToast} 
          />
        )}

        {activeNav === 'motor_claim' && (
          <MotorClaimsForm 
            API_BASE={API_BASE} 
            showToast={showToast} 
          />
        )}

        {activeNav === 'fraud_detection' && (
          <FraudDetection
            showToast={showToast}
          />
        )}

        {activeNav === 'risk_profiler' && (
          <RiskProfiler />
        )}

        {activeNav === 'crop_payout' && (
          <CropInsurance />
        )}

        {activeNav === 'renewal_agent' && (
          <RenewalCompare />
        )}

        {activeNav === 'agent_automation' && (
          <AgentAutomation />
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
    </div>
  )
}

export default App
