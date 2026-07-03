import { useState, useEffect } from "react"
import { useAuth } from "./AuthContext"

export default function RegisterPage({ onSwitch }) {
  const { login }           = useAuth()
  const [form, setForm]     = useState({
    name: "", email: "", phone: "", password: "", confirm: "",
    requested_role: "customer", company_name: "", employee_id: "", license_number: "", additional_info: ""
  })
  const [showPass, setShow] = useState(false)
  const [error, setError]   = useState(null)
  const [loading, setLoad]  = useState(false)

  // ── Google OAuth (Real Google Sign-In via accounts.google.com) ──
  const handleGoogleSuccess = async (credentialResponse) => {
    setError(null)
    setLoad(true)
    try {
      const headers = { "Content-Type": "application/json" }
      const tid = localStorage.getItem("insureai_tenant_id")
      if (tid) {
        headers["X-Tenant-ID"] = tid
      }
      const res = await fetch("/auth/google", {
        method: "POST",
        headers,
        body: JSON.stringify({ credential: credentialResponse.credential }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || "Google auth failed")
      const data = await res.json()
      login(data.token, {
        name: data.name, email: data.email,
        role: data.role, avatar: data.avatar,
      })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoad(false)
    }
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const tid = params.get("tenant_id")
    if (tid) {
      localStorage.setItem("insureai_tenant_id", tid)
    }

    let interval
    const initGoogle = () => {
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || "1065972828695-mockclientid.apps.googleusercontent.com",
          callback: handleGoogleSuccess,
        })
        const btnElem = document.getElementById("google-register-btn")
        if (btnElem) {
          window.google.accounts.id.renderButton(btnElem, {
            theme: "outline",
            size: "large",
            width: 336,
            shape: "rectangular",
            text: "signup_with"
          })
        }
      }
    }

    if (window.google) {
      initGoogle()
    } else {
      interval = setInterval(() => {
        if (window.google) {
          initGoogle()
          clearInterval(interval)
        }
      }, 500)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [])

  const handleRegister = async () => {
    if (!form.name || !form.email || !form.password) {
      setError("Please fill in all required fields")
      return
    }
    if (form.password !== form.confirm) {
      setError("Passwords do not match")
      return
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters")
      return
    }
    
    // Role-specific verification field checks
    if (form.requested_role !== "customer") {
      if (form.requested_role === "agent" && (!form.company_name || !form.license_number)) {
        setError("Please enter your Agency Name and Agent License Number")
        return
      }
      if (form.requested_role === "fraud_investigator" && (!form.company_name || !form.license_number)) {
        setError("Please enter your Company Name and Investigator License Number")
        return
      }
      if ((form.requested_role === "manager" || form.requested_role === "admin") && (!form.company_name || !form.employee_id)) {
        setError("Please enter your Company Name and Employee ID")
        return
      }
    }

    setLoad(true)
    setError(null)
    try {
      const headers = { "Content-Type": "application/json" }
      const tid = localStorage.getItem("insureai_tenant_id")
      if (tid) {
        headers["X-Tenant-ID"] = tid
      }
      const res = await fetch("/auth/register", {
        method: "POST",
        headers,
        body: JSON.stringify({
          name: form.name, email: form.email,
          phone: form.phone, password: form.password,
          requested_role: form.requested_role,
          company_name: form.company_name,
          employee_id: form.employee_id,
          license_number: form.license_number,
          additional_info: form.additional_info,
        }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || "Registration failed")
      const data = await res.json()
      login(data.token, {
        name: data.name, email: data.email,
        role: data.role, avatar: "",
      })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoad(false)
    }
  }

  const inputStyle = {
    width: "100%", padding: "12px 16px",
    borderRadius: 8, border: "1px solid #E5E7EB",
    fontSize: 14, boxSizing: "border-box",
  }

  const inp = (key, label, type = "text", placeholder = "") => (
    <div style={{ marginBottom: 14 }}>
      <label style={{ fontSize: 13, fontWeight: 500,
        display: "block", marginBottom: 6 }}>
        {label}
      </label>
      <input type={type} value={form[key]}
        placeholder={placeholder || label}
        onChange={e => setForm({ ...form, [key]: e.target.value })}
        style={inputStyle}/>
    </div>
  )

  return (
    <div style={{
      minHeight: "100vh", background: "#F3F4F6",
      display: "flex", alignItems: "center",
      justifyContent: "center",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    }}>
      <div style={{
        background: "#fff", borderRadius: 16,
        padding: "36px 32px", width: 400,
        boxShadow: "0 8px 32px rgba(0,0,0,0.10)",
      }}>

        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>
            Create Account
          </h2>
          <div style={{ fontSize: 13, color: "#6B7280", marginTop: 6 }}>
            Already have an account?{" "}
            <span onClick={onSwitch}
              style={{ color: "#2563EB", cursor: "pointer", fontWeight: 500 }}>
              Log in
            </span>
          </div>
        </div>

        {/* Google */}
        <div style={{ marginBottom: 20, display: "flex", justifyContent: "center" }}>
          <div id="google-register-btn" style={{ minHeight: 40 }}></div>
        </div>

        {/* Divider */}
        <div style={{ display: "flex", alignItems: "center",
          gap: 12, marginBottom: 20 }}>
          <div style={{ flex: 1, height: 1, background: "#E5E7EB" }}/>
          <span style={{ fontSize: 13, color: "#9CA3AF" }}>or</span>
          <div style={{ flex: 1, height: 1, background: "#E5E7EB" }}/>
        </div>

        {inp("name",  "Full Name *")}
        {inp("email", "Email *", "email")}
        {inp("phone", "Phone Number", "tel")}

        {/* Password with show/hide */}
        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 13, fontWeight: 500,
            display: "block", marginBottom: 6 }}>Password *</label>
          <div style={{ position: "relative" }}>
            <input type={showPass ? "text" : "password"}
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder="Min 8 characters"
              style={{ ...inputStyle, paddingRight: 44 }}/>
            <button onClick={() => setShow(!showPass)}
              style={{ position: "absolute", right: 12,
                top: "50%", transform: "translateY(-50%)",
                background: "none", border: "none",
                cursor: "pointer", color: "#9CA3AF",
                fontSize: 18, padding: 0 }}>
              {showPass ? "🙈" : "👁"}
            </button>
          </div>
        </div>

        {inp("confirm", "Confirm Password *", "password")}

        {/* Desired Role Selector */}
        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 6 }}>
            Desired Role
          </label>
          <select
            value={form.requested_role}
            onChange={e => setForm({ ...form, requested_role: e.target.value })}
            style={{ ...inputStyle, background: "#fff", cursor: "pointer" }}
          >
            <option value="customer">Customer (No Verification Needed)</option>
            <option value="agent">Agent</option>
            <option value="fraud_investigator">Fraud Investigator</option>
            <option value="manager">Manager</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        {/* Dynamic Verification Fields */}
        {form.requested_role === "agent" && (
          <div style={{ border: "1px solid #E5E7EB", borderRadius: 8, padding: 12, marginBottom: 14, background: "#F9FAFB" }}>
            <div style={{ fontSize: 12, color: "#4F46E5", fontWeight: 600, marginBottom: 10 }}>Agent Credentials Verification</div>
            {inp("company_name", "Agency/Company Name *")}
            {inp("license_number", "Agent License Number *")}
          </div>
        )}

        {form.requested_role === "fraud_investigator" && (
          <div style={{ border: "1px solid #E5E7EB", borderRadius: 8, padding: 12, marginBottom: 14, background: "#F9FAFB" }}>
            <div style={{ fontSize: 12, color: "#4F46E5", fontWeight: 600, marginBottom: 10 }}>Investigator Verification</div>
            {inp("company_name", "Investigator Agency/Company Name *")}
            {inp("license_number", "Investigator License Number *")}
          </div>
        )}

        {form.requested_role === "manager" && (
          <div style={{ border: "1px solid #E5E7EB", borderRadius: 8, padding: 12, marginBottom: 14, background: "#F9FAFB" }}>
            <div style={{ fontSize: 12, color: "#4F46E5", fontWeight: 600, marginBottom: 10 }}>Manager Verification</div>
            {inp("company_name", "Company Name *")}
            {inp("employee_id", "Employee ID *")}
          </div>
        )}

        {form.requested_role === "admin" && (
          <div style={{ border: "1px solid #E5E7EB", borderRadius: 8, padding: 12, marginBottom: 14, background: "#F9FAFB" }}>
            <div style={{ fontSize: 12, color: "#4F46E5", fontWeight: 600, marginBottom: 10 }}>Admin Verification</div>
            {inp("company_name", "Company Name *")}
            {inp("employee_id", "Employee ID *")}
          </div>
        )}

        {error && (
          <div style={{ color: "#DC2626", fontSize: 13,
            marginBottom: 14, padding: "10px 14px",
            background: "#FEE2E2", borderRadius: 8 }}>
            {error}
          </div>
        )}

        <button onClick={handleRegister} disabled={loading}
          style={{ width: "100%", padding: "13px",
            borderRadius: 8, background: "#16A34A",
            color: "#fff", fontWeight: 600, fontSize: 15,
            border: "none", cursor: "pointer", marginBottom: 20 }}>
          {loading ? "Creating account..." : "Create Account"}
        </button>

        <div style={{ textAlign: "center", fontSize: 12, color: "#9CA3AF" }}>
          By creating this account, you agree to our{" "}
          <span style={{ color: "#6B7280", cursor: "pointer",
            textDecoration: "underline" }}>Privacy Policy</span>
          {" & "}
          <span style={{ color: "#6B7280", cursor: "pointer",
            textDecoration: "underline" }}>Cookie Policy</span>
        </div>

      </div>
    </div>
  )
}
