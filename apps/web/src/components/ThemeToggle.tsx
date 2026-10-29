import { useTheme } from "../lib/theme";

const OPTIONS: { key: "light" | "system" | "dark"; label: string; icon: string }[] = [
  { key: "light", label: "Light", icon: "☀" },
  { key: "system", label: "System", icon: "◐" },
  { key: "dark", label: "Dark", icon: "☾" },
];

/** A 3-way theme selector (light / system / dark). */
export default function ThemeToggle() {
  const { pref, setPref } = useTheme();
  return (
    <div
      className="theme-toggle"
      role="group"
      aria-label="Color theme"
      style={{ display: "flex", border: "1px solid var(--nn-line)", borderRadius: 4, overflow: "hidden" }}
    >
      {OPTIONS.map((o) => (
        <button
          key={o.key}
          onClick={() => setPref(o.key)}
          aria-pressed={pref === o.key}
          title={`${o.label} theme`}
          style={{
            border: "none",
            background: pref === o.key ? "rgba(0,162,200,0.14)" : "transparent",
            color: pref === o.key ? "var(--nn-key-glow)" : "var(--nn-ink-2)",
            padding: "0.32rem 0.6rem",
            cursor: "pointer",
            fontFamily: "var(--font-mono)",
            fontSize: "0.6875rem",
            letterSpacing: "0.04em",
          }}
        >
          <span aria-hidden="true">{o.icon}</span> {o.label}
        </button>
      ))}
    </div>
  );
}
