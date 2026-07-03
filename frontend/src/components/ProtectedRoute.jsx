import { getRoleLabel } from "../rbac"

export default function ProtectedRoute({ role, allowedRoles, children }) {
  if (allowedRoles && !allowedRoles.includes(role)) {
    return (
      <div style={{
        minHeight: "80vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px",
        textAlign: "center"
      }}>
        <div style={{ fontSize: 64, marginBottom: 16 }}>⚠️</div>
        <h2 style={{ fontSize: 24, fontWeight: 700, color: "#1E293B", margin: 0 }}>
          Access Denied
        </h2>
        <p style={{ color: "#64748B", marginTop: 8, fontSize: 15, maxWidth: 450 }}>
          Your security clearance level ({getRoleLabel(role)}) is insufficient to access this action or page. Please contact your administrator.
        </p>
      </div>
    )
  }
  return children
}
