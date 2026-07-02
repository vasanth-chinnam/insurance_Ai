import { useState, useEffect } from "react"
import { useAuth } from "./AuthContext"

export default function LoginPage({ onSwitch }) {
  const { login }             = useAuth()
  const [email, setEmail]     = useState("")
  const [password, setPass]   = useState("")
  const [showPass, setShow]   = useState(false)
  const [error, setError]     = useState(null)
  const [loading, setLoading] = useState(false)
  const [mode, setMode]       = useState("login") // "login" | "forgot"
  const [forgotSent, setForgotSent] = useState(false)

  // ── Google OAuth (Real Google Sign-In via accounts.google.com) ──
  const handleGoogleSuccess = async (credentialResponse) => {
    setError(null)
    setLoading(true)
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
        name:   data.name,
        email:  data.email,
        role:   data.role,
        avatar: data.avatar,
      })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
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
        const btnElem = document.getElementById("google-login-btn")
        if (btnElem) {
          window.google.accounts.id.renderButton(btnElem, {
            theme: "outline",
            size: "large",
            width: 336,
            shape: "rectangular",
            text: "continue_with"
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

  // ── Email/Password login ──────────────────────────────────────
  const handleEmailLogin = async () => {
    if (!email || !password) {
      setError("Please enter email and password")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const headers = { "Content-Type": "application/json" }
      const tid = localStorage.getItem("insureai_tenant_id")
      if (tid) {
        headers["X-Tenant-ID"] = tid
      }
      const res = await fetch("/auth/login", {
        method: "POST",
        headers,
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || "Login failed")
      const data = await res.json()
      login(data.token, {
        name:   data.name,
        email:  data.email,
        role:   data.role,
        avatar: data.avatar || "",
      })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Forgot password ───────────────────────────────────────────
  const handleForgotPassword = async () => {
    if (!email) {
      setError("Please enter your email address first")
      return
    }
    setLoading(true)
    setError(null)
    try {
      await new Promise(r => setTimeout(r, 1000))
      setForgotSent(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Shared input style ────────────────────────────────────────
  const inputStyle = {
    width: "100%",
    padding: "12px 16px",
    borderRadius: 8,
    border: "1px solid #E5E7EB",
    fontSize: 14,
    boxSizing: "border-box",
    outline: "none",
    transition: "border 0.2s",
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "#F3F4F6",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    }}>
      <div style={{
        background: "#fff",
        borderRadius: 16,
        padding: "36px 32px",
        width: 400,
        boxShadow: "0 8px 32px rgba(0,0,0,0.10)",
        position: "relative",
      }}>

        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>
            {mode === "forgot" ? "Reset Password" : "Log in"}
          </h2>
          {mode === "login" && (
            <div style={{ fontSize: 13, color: "#6B7280", marginTop: 6 }}>
              New user?{" "}
              <span onClick={onSwitch}
                style={{ color: "#2563EB", cursor: "pointer", fontWeight: 500 }}>
                Register Now
              </span>
            </div>
          )}
        </div>

        {/* Forgot password mode */}
        {mode === "forgot" ? (
          <div>
            {forgotSent ? (
              <div style={{ textAlign: "center", padding: "20px 0" }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>📧</div>
                <div style={{ fontWeight: 600, marginBottom: 8 }}>
                  Reset link sent!
                </div>
                <div style={{ fontSize: 13, color: "#6B7280", marginBottom: 24 }}>
                  Check your email at <strong>{email}</strong>
                </div>
                <button onClick={() => { setMode("login"); setForgotSent(false) }}
                  style={{ color: "#2563EB", background: "none",
                    border: "none", cursor: "pointer", fontSize: 14 }}>
                  ← Back to Login
                </button>
              </div>
            ) : (
              <>
                <p style={{ fontSize: 13, color: "#6B7280", marginBottom: 20 }}>
                  Enter your email and we'll send you a reset link.
                </p>
                <div style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: 13, fontWeight: 500,
                    display: "block", marginBottom: 6 }}>Email</label>
                  <input type="email" value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    style={inputStyle}/>
                </div>
                {error && (
                  <div style={{ color: "#DC2626", fontSize: 13,
                    marginBottom: 12 }}>{error}</div>
                )}
                <button onClick={handleForgotPassword} disabled={loading}
                  style={{ width: "100%", padding: "12px",
                    borderRadius: 8, background: "#16A34A",
                    color: "#fff", fontWeight: 600,
                    border: "none", cursor: "pointer",
                    fontSize: 14, marginBottom: 12 }}>
                  {loading ? "Sending..." : "Send Reset Link"}
                </button>
                <button onClick={() => { setMode("login"); setError(null) }}
                  style={{ width: "100%", color: "#6B7280",
                    background: "none", border: "none",
                    cursor: "pointer", fontSize: 13 }}>
                  ← Back to Login
                </button>
              </>
            )}
          </div>
        ) : (
          <>
            {/* Google OAuth button */}
            <div style={{ marginBottom: 20, display: "flex", justifyContent: "center" }}>
              <div id="google-login-btn" style={{ minHeight: 40 }}></div>
            </div>

            {/* Divider */}
            <div style={{ display: "flex", alignItems: "center",
              gap: 12, marginBottom: 20 }}>
              <div style={{ flex: 1, height: 1, background: "#E5E7EB" }}/>
              <span style={{ fontSize: 13, color: "#9CA3AF" }}>or</span>
              <div style={{ flex: 1, height: 1, background: "#E5E7EB" }}/>
            </div>

            {/* Email input */}
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 13, fontWeight: 500,
                display: "block", marginBottom: 6 }}>
                Username or Email
              </label>
              <input
                type="email" value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="Username or Email"
                onKeyDown={e => e.key === "Enter" && handleEmailLogin()}
                style={inputStyle}
              />
            </div>

            {/* Password input */}
            <div style={{ marginBottom: 8 }}>
              <label style={{ fontSize: 13, fontWeight: 500,
                display: "block", marginBottom: 6 }}>
                Password
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type={showPass ? "text" : "password"}
                  value={password}
                  onChange={e => setPass(e.target.value)}
                  placeholder="Enter password"
                  onKeyDown={e => e.key === "Enter" && handleEmailLogin()}
                  style={{ ...inputStyle, paddingRight: 44 }}
                />
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

            {/* Forgot password */}
            <div style={{ textAlign: "right", marginBottom: 20 }}>
              <span onClick={() => { setMode("forgot"); setError(null) }}
                style={{ fontSize: 13, color: "#2563EB",
                  cursor: "pointer", fontWeight: 500 }}>
                Forgot password?
              </span>
            </div>

            {/* Error */}
            {error && (
              <div style={{ color: "#DC2626", fontSize: 13,
                marginBottom: 14, padding: "10px 14px",
                background: "#FEE2E2", borderRadius: 8 }}>
                {error}
              </div>
            )}

            {/* Sign In button */}
            <button onClick={handleEmailLogin} disabled={loading}
              style={{ width: "100%", padding: "13px",
                borderRadius: 8, background: "#16A34A",
                color: "#fff", fontWeight: 600, fontSize: 15,
                border: "none", cursor: "pointer", marginBottom: 20 }}>
              {loading ? "Signing in..." : "Sign In"}
            </button>

            {/* Privacy */}
            <div style={{ textAlign: "center", fontSize: 12, color: "#9CA3AF" }}>
              By creating this account, you agree to our{" "}
              <span style={{ color: "#6B7280", cursor: "pointer",
                textDecoration: "underline" }}>
                Privacy Policy
              </span>
              {" & "}
              <span style={{ color: "#6B7280", cursor: "pointer",
                textDecoration: "underline" }}>
                Cookie Policy
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
