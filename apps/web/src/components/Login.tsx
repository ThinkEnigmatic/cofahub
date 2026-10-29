import { useState, type FormEvent } from "react";
import { useAuth } from "../lib/auth";
import ThemeToggle from "./ThemeToggle";

export default function Login() {
  const { login } = useAuth();
  const [user, setUser] = useState("COFAHUB");
  const [pass, setPass] = useState("");
  const [err, setErr] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const ok = await login(user, pass);
    if (!ok) setErr(true);
  }

  return (
    <div className="login">
      <div className="login-card">
        <div className="login-brand">
          COFAHUB<span className="brand-dot">.</span>
        </div>
        <div className="login-sub">FAS climate intelligence — analysis &amp; action</div>
        <div style={{ position: "absolute", top: "0.9rem", right: "0.9rem" }}>
          <ThemeToggle />
        </div>
        <form onSubmit={submit}>
          <input
            aria-label="Username"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            autoComplete="username"
          />
          <input
            aria-label="Password"
            type="password"
            value={pass}
            onChange={(e) => setPass(e.target.value)}
            autoComplete="current-password"
            placeholder="password"
          />
          {err && <div className="login-err">Invalid credentials.</div>}
          <button className="btn" type="submit">
            Enter
          </button>
        </form>
      </div>
    </div>
  );
}
