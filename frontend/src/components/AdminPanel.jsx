import { useState, useEffect } from "react"
import { apiFetch } from "../utils/api"
import { getRoleLabel, getRoleBadgeColor } from "../rbac"

export default function AdminPanel({ showToast }) {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [updatingId, setUpdatingId] = useState(null)

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch("/admin/users")
      if (!res.ok) throw new Error("Failed to fetch users")
      const data = await res.json()
      setUsers(data)
    } catch (err) {
      setError(err.message || "Failed to load users.")
    } finally {
      setLoading(false)
    }
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

  return (
    <div style={{ padding: "30px 40px", maxWidth: 1000, margin: "0 auto" }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: "#1E293B", margin: 0 }}>
          Admin Panel & Role Management
        </h1>
        <p style={{ color: "#64748B", marginTop: 4, fontSize: 14 }}>
          Manage user permissions and security roles for your tenant.
        </p>
      </header>

      {loading && (
        <div style={{ textAlign: "center", padding: "40px 0", color: "#64748B" }}>
          Loading users list...
        </div>
      )}

      {error && (
        <div style={{ padding: 16, background: "#FEE2E2", color: "#DC2626", borderRadius: 8, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {!loading && !error && (
        <div style={{ background: "#fff", border: "1px solid #E2E8F0", borderRadius: 12, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
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
        </div>
      )}
    </div>
  )
}
