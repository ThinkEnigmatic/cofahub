import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type Theme = "light" | "dark";
type ThemePref = Theme | "system";

const STORAGE_KEY = "cofahub_theme";

interface ThemeState {
  pref: ThemePref;
  resolved: Theme;
  setPref: (p: ThemePref) => void;
}

const Ctx = createContext<ThemeState | null>(null);

function systemDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function resolve(pref: ThemePref): Theme {
  return pref === "system" ? (systemDark() ? "dark" : "light") : pref;
}

function apply(theme: Theme) {
  document.documentElement.dataset.theme = theme;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [pref, setPrefState] = useState<ThemePref>(() => {
    const s = localStorage.getItem(STORAGE_KEY);
    return s === "light" || s === "dark" || s === "system" ? s : "system";
  });

  const [resolved, setResolved] = useState<Theme>(() => resolve(pref));

  useEffect(() => {
    apply(resolved);
  }, [resolved]);

  // Follow the OS preference when in "system" mode.
  useEffect(() => {
    if (pref !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setResolved(mq.matches ? "dark" : "light");
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [pref]);

  const setPref = useCallback((p: ThemePref) => {
    localStorage.setItem(STORAGE_KEY, p);
    setPrefState(p);
    setResolved(resolve(p));
  }, []);

  const value = useMemo(() => ({ pref, resolved, setPref }), [pref, resolved, setPref]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTheme(): ThemeState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
