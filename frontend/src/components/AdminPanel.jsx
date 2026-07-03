import { useState, useEffect } from "react"
import { apiFetch } from "../utils/api"
import { getRoleLabel, getRoleBadgeColor } from "../rbac"

export default function AdminPanel({ showToast }) {
  const [tab, setTab] = useState("users") // "users" | "requests"
  const [users, setUsers] = useState([])
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [updatingId, setUpdatingId] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      await Promise.all([fetchUsers(), fetchRequests()])
    } catch (err) {
      setError(err.message || "Failed to load admin dashboard data.")
    } finally {
      setLoading(false)
    }
  }

  const fetchUsers = async () => {
    const res = await apiFetch("/admin/users")
    if (!res.ok) throw new Error("Failed to fetch users")
    const data = await res.json()
    setUsers(data)
  }

  const fetchRequests = async () => {
    const res = await apiFetch("/admin/role-requests")
    if (!res.ok) throw new Error("Failed to fetch role requests")
    const data = await res.json()
    setRequests(data)
  }

  const handleRoleChange = async (userId, newRole) => {
    setUpdatingId(userId)
    try {
      const res = await apiFetch("/admin/users/role", {
        method: "PUT",
        body: JSON.stringify({ user_id: userId, role: newRole }),
      })
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || "Failed to update role")
      }
      showToast("User role updated successfully!", "success")
      
      // Update local state
      setUsers(prev => prev.map(u => u.user_id === userId ? { ...u, role: newRole } : u))
    } catch (err) {
      showToast(err.message, "error")
    } finally {
      setUpdatingId(null)
    }
  }

  const handleRequestAction = async (requestId, action) => {
    try {
      const res = await apiFetch(`/admin/role-requests/${requestId}/action`, {
        method: "POST",
        body: JSON.stringify({ action }),
      })
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || `Failed to ${action} request`)
      }
      showToast(`Request successfully ${action}ed!`, "success")
      
      // Update local requests list
      setRequests(prev => prev.map(r => r.request_id === requestId ? { ...r, status: action === "approve" ? "approved" : "rejected" } : r))
      
      // Re-fetch users to reflect role upgrade in users tab
      fetchUsers()
    } catch (err) {
      showToast(err.message, "error")
    }
  }

  return (
    <div style={{ padding: "30px 40px", maxWidth: 1100, margin: "0 auto" }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: "#1E293B", margin: 0 }}>
          Admin Panel & Role Management
        </h1>
        <p style={{ color: "#64748B", marginTop: 4, fontSize: 14 }}>
          Manage user permissions, security roles, and verify credential upgrade requests.
        </p>
      </header>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 16, borderBottom: "1px solid #E2E8F0", marginBottom: 20 }}>
        <button
          onClick={() => setTab("users")}
          style={{
            padding: "10px 16px",
            border: "none",
            background: "none",
            borderBottom: tab === "users" ? "2px solid #2563EB" : "none",
            color: tab === "users" ? "#2563EB" : "#64748B",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: 14,
            outline: "none"
          }}
        >
          Users List
        </button>
        <button
          onClick={() => setTab("requests")}
          style={{
            padding: "10px 16px",
            border: "none",
            background: "none",
            borderBottom: tab === "requests" ? "2px solid #2563EB" : "none",
            color: tab === "requests" ? "#2563EB" : "#64748B",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: 14,
            outline: "none",
            display: "flex",
            alignItems: "center",
            gap: 6
          }}
        >
          Role Requests
          {requests.filter(r => r.status === "pending").length > 0 && (
            <span style={{ background: "#EF4444", color: "#fff", fontSize: 11, padding: "1px 6px", borderRadius: 999, fontWeight: 700 }}>
              {requests.filter(r => r.status === "pending").length}
            </span>
          )}
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: "center", padding: "40px 0", color: "#64748B" }}>
          Loading dashboard data...
        </div>
      )}

      {error && (
        <div style={{ padding: 16, background: "#FEE2E2", color: "#DC2626", borderRadius: 8, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {!loading && !error && (
        <div style={{ background: "#fff", border: "1px solid #E2E8F0", borderRadius: 12, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
          {tab === "users" ? (
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ background: "#F8FAFC", borderBottom: "1px solid #E2E8F0" }}>
                  <th style={{ padding: "14px 18px", fontSize: 12, fontWeight: 600, color: "#475569" }}>NAME</th>
                  <th style={{ padding: "14px 18px", fontSize: 12, fontWeight: 600, color: "#475569" }}>EMAIL</th>
                  <th style={{ padding: "14px 18px", fontSize: 12, fontWeight: 600, color: "#475569" }}>ROLE</th>
                  <th style={{ padding: "14px 18px", fontSize: 12, fontWeight: 600, color: "#475569" }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => {
                  const badge = getRoleBadgeColor(u.role)
                  return (
                    <tr key={u.user_id} style={{ borderBottom: "1px solid #E2E8F0" }}>
                      <td style={{ padding: "14px 18px", fontSize: 14, color: "#1E293B", fontWeight: 500 }}>{u.name}</td>
                      <td style={{ padding: "14px 18px", fontSize: 14, color: "#64748B" }}>{u.email}</td>
                      <td style={{ padding: "14px 18px" }}>
                        <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 8px", borderRadius: 999, background: badge.bg, color: badge.color }}>
                          {getRoleLabel(u.role)}
                        </span>
                      </td>
                      <td style={{ padding: "14px 18px" }}>
                        <select
                          value={u.role}
                          disabled={updatingId === u.user_id}
                          onChange={e => handleRoleChange(u.user_id, e.target.value)}
                          style={{
                            padding: "6px 10px",
                            borderRadius: 6,
                            border: "1px solid #CBD5E1",
                            fontSize: 13,
                            outline: "none",
                            background: "#fff"
                          }}
                        >
                          <option value="customer">Customer</option>
                          <option value="agent">Agent</option>
                          <option value="fraud_investigator">Fraud Investigator</option>
                          <option value="manager">Manager</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                    </tr>
                  )
                })}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={4} style={{ padding: "30px 18px", textAlign: "center", color: "#64748B" }}>
                      No users registered in this tenant yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ background: "#F8FAFC", borderBottom: "1px solid #E2E8F0" }}>
                  <th style={{ padding: "14px 18px", fontSize: 12, fontWeight: 600, color: "#475569" }}>USER</th>
                  <th style={{ padding: "14px 18px", fontSize: 12, fontWeight: 600, color: "#475569" }}>REQUESTED ROLE</th>
                  <th style={{ padding: "14px 18px", fontSize: 12, fontWeight: 600, color: "#475569" }}>VERIFICATION DETAILS</th>
                  <th style={{ padding: "14px 18px", fontSize: 12, fontWeight: 600, color: "#475569" }}>STATUS</th>
                  <th style={{ padding: "14px 18px", fontSize: 12, fontWeight: 600, color: "#475569" }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {requests.map(r => {
                  const badge = getRoleBadgeColor(r.requested_role)
                  return (
                    <tr key={r.request_id} style={{ borderBottom: "1px solid #E2E8F0" }}>
                      <td style={{ padding: "14px 18px", fontSize: 14, color: "#1E293B" }}>
                        <div style={{ fontWeight: 500 }}>{r.user_name}</div>
                        <div style={{ fontSize: 12, color: "#64748B" }}>{r.user_email}</div>
                      </td>
                      <td style={{ padding: "14px 18px" }}>
                        <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 8px", borderRadius: 999, background: badge.bg, color: badge.color }}>
                          {getRoleLabel(r.requested_role)}
                        </span>
                      </td>
                      <td style={{ padding: "14px 18px", fontSize: 13, color: "#334155" }}>
                        {r.company_name && <div>🏢 <strong>Company/Agency:</strong> {r.company_name}</div>}
                        {r.employee_id && <div>🆔 <strong>Employee ID:</strong> {r.employee_id}</div>}
                        {r.license_number && <div>📜 <strong>License #:</strong> {r.license_number}</div>}
                        {!r.company_name && !r.employee_id && !r.license_number && <span style={{ color: "#94A3B8" }}>No credentials supplied</span>}
                      </td>
                      <td style={{ padding: "14px 18px" }}>
                        <span style={{
                          fontSize: 11,
                          fontWeight: 600,
                          padding: "3px 8px",
                          borderRadius: 6,
                          background: r.status === "pending" ? "#FEF3C7" : r.status === "approved" ? "#D1FAE5" : "#FEE2E2",
                          color: r.status === "pending" ? "#D97706" : r.status === "approved" ? "#065F46" : "#991B1B"
                        }}>
                          {r.status.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: "14px 18px" }}>
                        {r.status === "pending" ? (
                          <div style={{ display: "flex", gap: 8 }}>
                            <button
                              onClick={() => handleRequestAction(r.request_id, "approve")}
                              style={{
                                background: "#16A34A",
                                color: "#fff",
                                border: "none",
                                borderRadius: 6,
                                padding: "6px 12px",
                                fontSize: 12,
                                fontWeight: 600,
                                cursor: "pointer",
                                transition: "background 0.2s"
                              }}
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleRequestAction(r.request_id, "reject")}
                              style={{
                                background: "#DC2626",
                                color: "#fff",
                                border: "none",
                                borderRadius: 6,
                                padding: "6px 12px",
                                fontSize: 12,
                                fontWeight: 600,
                                cursor: "pointer",
                                transition: "background 0.2s"
                              }}
                            >
                              Reject
                            </button>
                          </div>
                        ) : (
                          <span style={{ fontSize: 12, color: "#94A3B8" }}>Processed</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {requests.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ padding: "30px 18px", textAlign: "center", color: "#64748B" }}>
                      No role requests submitted yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
