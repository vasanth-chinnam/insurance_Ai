import { createContext, useContext, useState, useEffect } from "react"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const savedUser = localStorage.getItem("insureai_user")
    const savedToken = localStorage.getItem("insureai_token")
    if (savedUser && savedToken) {
      setUser(JSON.parse(savedUser))
    }
    setLoading(false)
  }, [])

  const login = (token, userData) => {
    localStorage.setItem("insureai_token", token)
    localStorage.setItem("insureai_user", JSON.stringify(userData))
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem("insureai_token")
    localStorage.removeItem("insureai_user")
    setUser(null)
  }

  const updateRole = (newRole) => {
    if (user) {
      const updatedUser = { ...user, role: newRole }
      localStorage.setItem("insureai_user", JSON.stringify(updatedUser))
      const token = localStorage.getItem("insureai_token")
      if (token && token.startsWith("mock-")) {
        const parts = token.split("-")
        const userId = parts[parts.length - 1]
        localStorage.setItem("insureai_token", `mock-google-token-${newRole}-${userId}`)
      }
      setUser(updatedUser)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, updateRole }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
