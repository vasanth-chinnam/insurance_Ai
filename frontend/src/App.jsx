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
  Stethoscope
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import PolicyChat from './components/PolicyChat'
import MotorClaimsForm from './components/MotorClaimsForm'
import FraudDetection from './components/FraudDetection'
import RiskProfiler from './components/RiskProfiler'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000/api'

const NAV_ITEMS = [
  { id: 'policy_rag', icon: Stethoscope, label: 'Policy Q&A', badge: 'Live', phase: null },
  { id: 'motor_claim', icon: FileText, label: 'Claim Estimator', badge: 'Live', phase: 2 },
  { id: 'fraud_detection', icon: Search, label: 'Fraud Detection', badge: 'Live', phase: 3 },
  { id: 'risk_profiler', icon: BarChart3, label: 'Risk Profiler', badge: 'Live', phase: 4 },
  { id: 'crop_payout', icon: Leaf, label: 'Crop Insurance', badge: 'Phase 5', phase: 5 },
  { id: 'renewal_agent', icon: RefreshCcw, label: 'Renewal Compare', badge: 'Phase 6', phase: 6 },
]

function App() {
  const [activeNav, setActiveNav] = useState('policy_rag')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [toast, setToast] = useState(null)
  
  // Lift chat messages state so history persists between tab switches
  const [messages, setMessages] = useState([])

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
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
                className={`nav-item ${activeNav === item.id ? 'active' : ''} ${item.phase && item.phase > 4 ? 'disabled' : ''}`}
                onClick={() => { 
                  if (!item.phase || item.phase <= 4) {
                    setActiveNav(item.id)
                    setSidebarOpen(false)
                  } else {
                    showToast(`Feature coming in Phase ${item.phase}!`, 'error')
                  }
                }}
              >
                <Icon className="icon" size={20} />
                <span className="label">{item.label}</span>
                {item.badge && <span className={`badge ${item.badge === 'Live' ? 'live' : ''}`}>{item.badge}</span>}
              </div>
            )
          })}
        </nav>

        <div className="sidebar-footer">
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
