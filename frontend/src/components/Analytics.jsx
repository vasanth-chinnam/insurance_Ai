import { BarChart3, TrendingUp, ShieldAlert, Award } from "lucide-react"

export default function Analytics() {
  const stats = [
    { label: "Active Policies", value: "1,248", change: "+12.3%", icon: Award, color: "#2563EB", bg: "#EFF6FF" },
    { label: "Pending Claims", value: "48", change: "-4.2%", icon: BarChart3, color: "#16A34A", bg: "#F0FDF4" },
    { label: "Fraud Savings", value: "₹4.2L", change: "+18.9%", icon: TrendingUp, color: "#7C3AED", bg: "#F5F3FF" },
    { label: "Flagged Risks", value: "12", change: "0.0%", icon: ShieldAlert, color: "#DC2626", bg: "#FEE2E2" },
  ]

  return (
    <div style={{ padding: "30px 40px", maxWidth: 1000, margin: "0 auto" }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: "#1E293B", margin: 0 }}>
          SaaS Operations & Metrics Analytics
        </h1>
        <p style={{ color: "#64748B", marginTop: 4, fontSize: 14 }}>
          Executive dashboard tracking claims throughput, underwriting risk ratios, and loss prevention margins.
        </p>
      </header>

      {/* Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 20, marginBottom: 30 }}>
        {stats.map((s, idx) => {
          const Icon = s.icon
          return (
            <div key={idx} style={{
              background: "#fff",
              border: "1px solid #E2E8F0",
              borderRadius: 12,
              padding: 20,
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between"
            }}>
              <div>
                <div style={{ fontSize: 13, color: "#64748B", fontWeight: 500 }}>{s.label}</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: "#1E293B", marginTop: 6 }}>{s.value}</div>
                <div style={{ fontSize: 12, color: s.change.startsWith("+") ? "#16A34A" : "#DC2626", fontWeight: 600, marginTop: 4 }}>
                  {s.change} vs last month
                </div>
              </div>
              <div style={{ width: 48, height: 48, borderRadius: "50%", background: s.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Icon style={{ color: s.color }} size={24} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Main Graph mock */}
      <div style={{
        background: "#fff",
        border: "1px solid #E2E8F0",
        borderRadius: 12,
        padding: 24,
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
        marginBottom: 30
      }}>
        <div style={{ fontWeight: 600, fontSize: 16, color: "#1E293B", marginBottom: 16 }}>Claims Submission History</div>
        <div style={{ height: 200, display: "flex", alignItems: "flex-end", gap: 16, borderBottom: "2px solid #E2E8F0", paddingBottom: 10 }}>
          {[40, 65, 30, 85, 50, 95, 75].map((h, i) => (
            <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
              <div style={{ width: "100%", height: `${h}%`, background: "linear-gradient(180deg, #3B82F6 0%, #2563EB 100%)", borderRadius: "4px 4px 0 0" }} />
              <div style={{ fontSize: 11, color: "#64748B", marginTop: 4 }}>
                {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i]}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
