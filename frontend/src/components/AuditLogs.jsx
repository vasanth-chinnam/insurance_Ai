import { useState, useEffect } from "react"
import { apiFetch } from "../utils/api"

const ACTION_ICONS = {
  LOGIN:            "🔐",
  GOOGLE_AUTH:      "🔐",
  REGISTER:         "👤",
  UPLOAD_POLICY:    "📄",
  POLICY_QUERY:     "💬",
  CREATE_CLAIM:     "📋",
  APPROVE_CLAIM:    "✅",
  REJECT_CLAIM:     "❌",
  RUN_FRAUD_CHECK:  "🔍",
  FLAG_FRAUD:       "🚨",
  GENERATE_RISK:    "📊",
  RUN_CROP_AGENT:   "🌾",
  TRIGGER_PAYOUT:   "💰",
  RUN_RENEWAL:      "🔄",
  RUN_AUTOMATION:   "⚡",
  UPDATE_ROLE:      "👑",
  FAILED_LOGIN:     "⚠️",
  UNAUTHORIZED_ACCESS: "🚫",
}

const ACTION_COLORS = {
  LOGIN:            "#16A34A",
  GOOGLE_AUTH:      "#16A34A",
  REGISTER:         "#2563EB",
  CREATE_CLAIM:     "#D97706",
  APPROVE_CLAIM:    "#16A34A",
  REJECT_CLAIM:     "#DC2626",
  RUN_FRAUD_CHECK:  "#7C3AED",
  FLAG_FRAUD:       "#DC2626",
  FAILED_LOGIN:     "#DC2626",
  UNAUTHORIZED_ACCESS: "#DC2626",
}

const ACTIONS = [
  "All Actions",
  "LOGIN", "GOOGLE_AUTH", "REGISTER",
  "UPLOAD_POLICY", "POLICY_QUERY",
  "CREATE_CLAIM", "APPROVE_CLAIM", "REJECT_CLAIM",
  "RUN_FRAUD_CHECK", "FLAG_FRAUD",
  "GENERATE_RISK", "RUN_CROP_AGENT",
  "RUN_RENEWAL", "RUN_AUTOMATION",
  "UPDATE_ROLE", "FAILED_LOGIN",
]

export default function AuditLogs() {
  const [logs, setLogs]         = useState([])
  const [stats, setStats]       = useState(null)
  const [loading, setLoading]   = useState(true)
  const [filter, setFilter]     = useState("All Actions")
  const [search, setSearch]     = useState("")
  const [page, setPage]         = useState(0)
  const PAGE_SIZE = 20

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const action = filter === "All Actions" ? "" : `&action=${filter}`
      const res = await apiFetch(
        `/audit/logs?limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}${action}`
      )
      if (!res.ok) throw new Error("Failed to fetch logs")
      const data = await res.json()
      setLogs(data.logs || [])
    } catch (e) {
      console.error("Failed to fetch logs:", e)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await apiFetch("/audit/stats")
      if (!res.ok) throw new Error("Failed to fetch stats")
      setStats(await res.json())
    } catch (e) {
      console.error("Failed to fetch stats:", e)
    }
  }

  useEffect(() => {
    fetchLogs()
    fetchStats()
  }, [filter, page])

  const formatTime = (ts) => {
    if (!ts) return ""
    const d = new Date(ts)
    return d.toLocaleString("en-IN", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    })
  }

  const filteredLogs = logs.filter(log =>
    !search ||
    log.action?.includes(search.toUpperCase()) ||
    log.user_name?.toLowerCase().includes(search.toLowerCase()) ||
    log.user_email?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "24px 16px", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" }}>
      <h2 style={{ fontWeight: 700, marginBottom: 4, color: "#1E293B" }}>Audit Logs</h2>
      <p style={{ color: "#6B7280", marginBottom: 24, fontSize: 14 }}>
        Complete activity trail — every action recorded
      </p>

      {/* Stats cards */}
      {stats && (
        <div style={{ display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 12, marginBottom: 24 }}>
          <div style={{ background: "#DCFCE7", borderRadius: 12,
            padding: "16px 20px" }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#166534" }}>TODAY'S ACTIONS</div>
            <div style={{ fontSize: 28, fontWeight: 700,
              color: "#16A34A", marginTop: 4 }}>
              {stats.today_total}
            </div>
          </div>
          <div style={{ background: "#FEE2E2", borderRadius: 12,
            padding: "16px 20px" }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#991B1B" }}>FAILED ACTIONS</div>
            <div style={{ fontSize: 28, fontWeight: 700,
              color: "#DC2626", marginTop: 4 }}>
              {stats.today_failed}
            </div>
          </div>
          <div style={{ background: "#EFF6FF", borderRadius: 12,
            padding: "16px 20px" }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#1E40AF" }}>ACTIVE USERS TODAY</div>
            <div style={{ fontSize: 28, fontWeight: 700,
              color: "#2563EB", marginTop: 4 }}>
              {stats.active_users}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: 16,
        flexWrap: "wrap" }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search by user or action..."
          style={{ flex: 1, minWidth: 200, padding: "10px 14px",
            borderRadius: 8, border: "1px solid #E5E7EB", fontSize: 14, outline: "none", boxSizing: "border-box" }}
        />
        <select value={filter}
          onChange={e => { setFilter(e.target.value); setPage(0) }}
          style={{ padding: "10px 14px", borderRadius: 8,
            border: "1px solid #E5E7EB", fontSize: 14, minWidth: 160, background: "#fff", outline: "none" }}>
          {ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <button onClick={() => { fetchLogs(); fetchStats() }}
          style={{ padding: "10px 20px", borderRadius: 8,
            background: "#2563EB", color: "#fff",
            border: "none", cursor: "pointer", fontWeight: 500, fontSize: 14 }}>
          Refresh
        </button>
      </div>

      {/* Logs table */}
      <div style={{ background: "#fff", borderRadius: 12,
        border: "1px solid #E5E7EB", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>

        {/* Table header */}
        <div style={{ display: "grid",
          gridTemplateColumns: "48px 140px 1fr 140px 150px 100px",
          gap: 0, background: "#F9FAFB",
          padding: "12px 16px", borderBottom: "1px solid #E5E7EB" }}>
          {["", "ACTION", "USER", "DETAILS", "TIME", "STATUS"].map((h, idx) => (
            <div key={idx} style={{ fontSize: 11, fontWeight: 600,
              color: "#9CA3AF", letterSpacing: 0.5 }}>{h}</div>
          ))}
        </div>

        {/* Rows */}
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: "#9CA3AF", fontSize: 14 }}>
            Loading logs...
          </div>
        ) : filteredLogs.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: "#9CA3AF", fontSize: 14 }}>
            No audit logs found
          </div>
        ) : (
          filteredLogs.map((log, i) => {
            const color = ACTION_COLORS[log.action] || "#6B7280"
            const details = typeof log.details === "string"
              ? JSON.parse(log.details || "{}")
              : (log.details || {})

            return (
              <div key={log.id || i} style={{
                display: "grid",
                gridTemplateColumns: "48px 140px 1fr 140px 150px 100px",
                gap: 0, padding: "12px 16px", alignItems: "center",
                borderBottom: "1px solid #F3F4F6",
                background: log.status === "failed" ? "#FFF5F5" : "#fff",
                transition: "background 0.1s",
              }}>
                {/* Icon */}
                <div style={{ fontSize: 18, textAlign: "center" }}>
                  {ACTION_ICONS[log.action] || "📝"}
                </div>

                {/* Action */}
                <div>
                  <span style={{
                    fontSize: 11, fontWeight: 600,
                    padding: "3px 8px", borderRadius: 999,
                    background: color + "15", color,
                  }}>
                    {log.action}
                  </span>
                </div>

                {/* User */}
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: "#1E293B" }}>
                    {log.user_name || "System"}
                  </div>
                  <div style={{ fontSize: 11, color: "#9CA3AF" }}>
                    {log.user_email || ""}
                  </div>
                </div>

                {/* Details */}
                <div style={{ fontSize: 11, color: "#6B7280" }}>
                  {Object.entries(details).slice(0, 2).map(([k, v]) => (
                    <div key={k}>
                      <span style={{ color: "#9CA3AF" }}>{k}:</span>{" "}
                      {String(v).slice(0, 20)}
                    </div>
                  ))}
                </div>

                {/* Time */}
                <div style={{ fontSize: 11, color: "#9CA3AF" }}>
                  {formatTime(log.created_at)}
                </div>

                {/* Status */}
                <div>
                  <span style={{
                    fontSize: 11, fontWeight: 600,
                    padding: "2px 8px", borderRadius: 999,
                    background: log.status === "success" ? "#DCFCE7" : "#FEE2E2",
                    color: log.status === "success" ? "#16A34A" : "#DC2626",
                  }}>
                    {log.status || "success"}
                  </span>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Pagination */}
      <div style={{ display: "flex", justifyContent: "space-between",
        alignItems: "center", marginTop: 16 }}>
        <div style={{ fontSize: 13, color: "#6B7280" }}>
          Showing {page * PAGE_SIZE + 1}–{page * PAGE_SIZE + filteredLogs.length} logs
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            style={{ padding: "8px 16px", borderRadius: 8,
              border: "1px solid #E5E7EB", background: "#fff",
              cursor: page === 0 ? "not-allowed" : "pointer",
              color: page === 0 ? "#D1D5DB" : "#374151", fontSize: 13 }}>
            ← Previous
          </button>
          <button onClick={() => setPage(p => p + 1)}
            disabled={filteredLogs.length < PAGE_SIZE}
            style={{ padding: "8px 16px", borderRadius: 8,
              border: "1px solid #E5E7EB", background: "#fff",
              cursor: filteredLogs.length < PAGE_SIZE ? "not-allowed" : "pointer",
              color: filteredLogs.length < PAGE_SIZE ? "#D1D5DB" : "#374151", fontSize: 13 }}>
            Next →
          </button>
        </div>
      </div>
    </div>
  )
}
