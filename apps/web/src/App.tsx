import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import Login from "./components/Login";
import PrintReport from "./components/PrintReport";
import StationRail from "./components/StationRail";
import ThemeToggle from "./components/ThemeToggle";
import { useAuth } from "./lib/auth";
import { SelectionProvider } from "./lib/selection";
import About from "./sections/About";
import Ask from "./sections/Ask";
import Coastal from "./sections/Coastal";
import Console from "./sections/Console";
import Drought from "./sections/Drought";
import Enso from "./sections/Enso";
import Plans from "./sections/Plans";

const NAV = [
  { to: "/", label: "Console", end: true },
  { to: "/drought", label: "Drought" },
  { to: "/coastal", label: "Coastal" },
  { to: "/enso", label: "ENSO" },
  { to: "/plans", label: "Plans" },
  { to: "/ask", label: "Ask" },
  { to: "/about", label: "About" },
];

export default function App() {
  const { authed, logout } = useAuth();

  if (!authed) {
    return <Login />;
  }

  return (
    <SelectionProvider>
      <div className="app">
        <header className="header">
          <NavLink to="/" className="brand" style={{ textDecoration: "none" }}>
            COFAHUB<span className="brand-dot">.</span>
          </NavLink>
          <nav style={{ display: "flex", gap: "0.25rem" }} aria-label="Primary">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) => "rail-item" + (isActive ? " active" : "")}
                style={{
                  width: "auto",
                  padding: "0.4rem 0.7rem",
                  borderRadius: 3,
                  textDecoration: "none",
                }}
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
          <div className="spacer" />
          <ThemeToggle />
          <button
            className="rail-item"
            onClick={logout}
            style={{ width: "auto", padding: "0.4rem 0.7rem", textDecoration: "none" }}
          >
            Sign out
          </button>
        </header>

        <StationRail />

        <main className="main">
          <Routes>
            <Route path="/" element={<Console />} />
            <Route path="/drought" element={<Drought />} />
            <Route path="/coastal" element={<Coastal />} />
            <Route path="/enso" element={<Enso />} />
            <Route path="/plans" element={<Plans />} />
            <Route path="/ask" element={<Ask />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        {/* Print-only situation report for the selected atoll (hidden on screen). */}
        <PrintReport />
      </div>
    </SelectionProvider>
  );
}
