import { useEffect, useState } from "react";
import { getStations } from "../lib/data";
import { useSelection } from "../lib/selection";
import type { Station } from "../lib/types";

const COUNTRY_ORDER = ["PW", "FM", "MH"] as const;

/** The station rail: atolls grouped by country, each with a drought-level dot. */
export default function StationRail() {
  const { geoId, setGeoId } = useSelection();
  const [stations, setStations] = useState<Station[]>([]);
  const [levels, setLevels] = useState<Record<string, string | null>>({});

  useEffect(() => {
    getStations().then(setStations).catch(() => {});
  }, []);

  // Resolve each station's drought level for the dots (best-effort, lightweight).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const { getDrought } = await import("../lib/data");
      const next: Record<string, string | null> = {};
      for (const s of stations) {
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
    })();
    return () => {
      cancelled = true;
    };
  }, [stations]);

  return (
    <nav className="rail" aria-label="Stations">
      {COUNTRY_ORDER.map((cc) => {
        const group = stations.filter((s) => s.country === cc && s.entityType !== "country");
        if (!group.length) return null;
        const name = { PW: "Palau", FM: "Micronesia (FSM)", MH: "Marshall Islands" }[cc];
        return (
          <div className="rail-group" key={cc}>
            <div className="rail-group-title">{name}</div>
            {group.map((s) => (
              <button
                key={s.geoId}
                className="rail-item"
                aria-selected={s.geoId === geoId}
                onClick={() => setGeoId(s.geoId)}
              >
                <span className="rail-dot" data-level={levels[s.geoId] ?? undefined} />
                <span>{s.name}</span>
              </button>
            ))}
          </div>
        );
      })}
    </nav>
  );
}
