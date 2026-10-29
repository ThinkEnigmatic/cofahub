import { useEffect, useState } from "react";
import { getDrought, getStations } from "./data";
import type { Station } from "./types";

export interface StationLevels {
  stations: Station[];
  /** geoId -> drought level (D0-D4 or null). */
  levels: Record<string, string | null>;
  loading: boolean;
}

/** Fetch stations + their drought levels (shared by the rail and the map). */
export function useStations(): StationLevels {
  const [stations, setStations] = useState<Station[]>([]);
  const [levels, setLevels] = useState<Record<string, string | null>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const all = await getStations();
        if (cancelled) return;
        setStations(all);
        // Fetch drought levels sequentially (server rate-limits the archive).
        const next: Record<string, string | null> = {};
        for (const s of all) {
          if (s.entityType === "country") continue;
          try {
            const d = await getDrought(s.geoId);
            if (cancelled) return;
            next[s.geoId] = d.d0D4 ?? null;
          } catch {
            next[s.geoId] = null;
          }
        }
        if (!cancelled) setLevels(next);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { stations, levels, loading };
}
