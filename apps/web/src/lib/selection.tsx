import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

interface Selection {
  geoId: string;
  setGeoId: (id: string) => void;
}

const Ctx = createContext<Selection | null>(null);

export function SelectionProvider({ children }: { children: ReactNode }) {
  const [geoId, setGeoId] = useState<string>("RMI-MAJ");
  const value = useMemo(() => ({ geoId, setGeoId }), [geoId]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSelection(): Selection {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useSelection must be used within SelectionProvider");
  return ctx;
}
