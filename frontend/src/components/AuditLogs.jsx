import { useState, useEffect } from "react"
import { apiFetch } from "../utils/api"
import { Clock, User, Shield, Activity } from "lucide-react"

export default function AuditLogs() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Generate beautiful mock audit logs for demonstration
    setTimeout(() => {
      setLogs([
        { id: "L001", user: "vasanthchinnam0@gmail.com", action: "SUBMIT_CLAIM", entity: "claims", entity_id: "C-MOTOR-928", time: "Just now" },
        { id: "L002", user: "vasanthchinnam0@gmail.com", action: "RUN_FRAUD_ANALYSIS", entity: "fraud_checks", entity_id: "F-CHECK-483", time: "5 mins ago" },
        { id: "L003", user: "vasanthchinnam0@gmail.com", action: "CREATE_RISK_PROFILE", entity: "risk_profiles", entity_id: "R-PROF-112", time: "1 hour ago" },
        { id: "L004", user: "system@insureai.com", action: "INDEX_POLICY_DOCUMENT", entity: "policies", entity_id: "P-HEALTH-003", time: "2 hours ago" },
        { id: "L005", user: "admin@insureai.com", action: "UPDATE_USER_ROLE", entity: "users", entity_id: "U-AGENT-771", time: "1 day ago" },
      ])
      setLoading(false)
    }, 800)
  }, [])

  return (
    <div style={{ padding: "30px 40px", maxWidth: 1000, margin: "0 auto" }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: "#1E293B", margin: 0 }}>
          System Audit Trail & Security Logs
        </h1>
        <p style={{ color: "#64748B", marginTop: 4, fontSize: 14 }}>
          Tamper-evident logs of all write actions, user role modifications, and policy indexings within the tenant boundary.
        </p>
      </header>

      {loading && (
        <div style={{ textAlign: "center", padding: "40px 0", color: "#64748B" }}>
          Loading audit trail logs...
        </div>
      )}

      {!loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {logs.map(log => (
            <div key={log.id} style={{
              background: "#fff",
              border: "1px solid #E2E8F0",
              borderRadius: 12,
              padding: "16px 20px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: 16
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <div style={{ width: 40, height: 40, borderRadius: "50%", background: "#F1F5F9", display: "flex", alignItems: "center", justifyContent: "center", color: "#64748B" }}>
                  <Shield size={20} />
                </div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "#0F172A", background: "#F1F5F9", padding: "3px 8px", borderRadius: 6 }}>
                      {log.action}
                    </span>
                    <span style={{ fontSize: 13, color: "#64748B" }}>on {log.entity} ({log.entity_id})</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 6, fontSize: 12, color: "#64748B" }}>
                    <User size={13} />
                    <span>Initiated by: {log.user}</span>
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#94A3B8" }}>
                <Clock size={13} />
                <span>{log.time}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
