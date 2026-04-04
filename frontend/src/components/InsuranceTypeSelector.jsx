import { motion } from "framer-motion"

const TYPES = [
  { value: "motor",  label: "Motor",  icon: "🚗", desc: "Vehicle & Auto" },
  { value: "health", label: "Health", icon: "🏥", desc: "Medical & Hospital" },
  { value: "travel", label: "Travel", icon: "✈️", desc: "Flight & Trip" },
  { value: "crop",   label: "Crop",   icon: "🌾", desc: "Agriculture" },
]

export default function InsuranceTypeSelector({ value, onChange, compact = false }) {
  return (
    <div style={{
      display: "flex",
      gap: compact ? 6 : 8,
      marginBottom: compact ? 12 : 20,
      flexWrap: "wrap",
    }}>
      {TYPES.map(t => {
        const active = value === t.value
        return (
          <motion.button
            key={t.value}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onChange(t.value)}
            style={{
              padding: compact ? "6px 14px" : "10px 18px",
              borderRadius: 10,
              fontWeight: 600,
              fontSize: compact ? "0.8rem" : "0.85rem",
              border: active ? "2px solid #2563EB" : "1.5px solid #E5E7EB",
              background: active
                ? "linear-gradient(135deg, #EFF6FF, #DBEAFE)"
                : "#fff",
              color: active ? "#1D4ED8" : "#6B7280",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              transition: "all 0.2s ease",
              boxShadow: active
                ? "0 2px 8px rgba(37, 99, 235, 0.15)"
                : "0 1px 3px rgba(0,0,0,0.04)",
            }}
          >
            <span style={{ fontSize: compact ? "0.9rem" : "1.1rem" }}>{t.icon}</span>
            {t.label}
          </motion.button>
        )
      })}
    </div>
  )
}
