// Role → visible nav items
export const ROLE_NAV = {
  customer: [
    "policy_qa",
    "claim_estimator",
    "risk_profiler",
    "renewal_compare",
    "agent_automation",
  ],
  agent: [
    "policy_qa",
    "claim_estimator",
    "risk_profiler",
    "renewal_compare",
    "agent_automation",
    "crop_insurance",
  ],
  fraud_investigator: [
    "policy_qa",
    "fraud_detection",
    "risk_profiler",
    "agent_automation",
  ],
  manager: [
    "policy_qa",
    "claim_estimator",
    "fraud_detection",
    "risk_profiler",
    "crop_insurance",
    "renewal_compare",
    "agent_automation",
    "analytics",
  ],
  admin: [
    "policy_qa",
    "claim_estimator",
    "fraud_detection",
    "risk_profiler",
    "crop_insurance",
    "renewal_compare",
    "agent_automation",
    "analytics",
    "audit_logs",
    "admin_panel",
  ],
}

export const canAccess = (role, feature) => {
  const allowed = ROLE_NAV[role] || ROLE_NAV["customer"]
  return allowed.includes(feature)
}

export const getRoleLabel = (role) => ({
  customer:          "Customer",
  agent:             "Insurance Agent",
  fraud_investigator:"Fraud Investigator",
  manager:           "Manager",
  admin:             "Administrator",
}[role] || "Customer")

export const getRoleBadgeColor = (role) => ({
  customer:          { bg: "#EFF6FF", color: "#2563EB" },
  agent:             { bg: "#F0FDF4", color: "#16A34A" },
  fraud_investigator:{ bg: "#FEF3C3", color: "#D97706" },
  manager:           { bg: "#F5F3FF", color: "#7C3AED" },
  admin:             { bg: "#FEE2E2", color: "#DC2626" },
}[role] || { bg: "#EFF6FF", color: "#2563EB" })
