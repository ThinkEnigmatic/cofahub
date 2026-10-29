import { useEffect, useState } from "react";
import { getDrought, getMarine, getSeaLevel, getCompound, getRainfall } from "../lib/data";
import type { CompoundFlag, DroughtStatus, MarineState, SeaLevelState } from "../lib/types";

export interface RainfallSeries {
  available: boolean;
  months: string[];
  values: number[];
  climatology: number[];
}

/** Fetch the selected station's core indicators once. */
export function useStation(geoId: string) {
  const [drought, setDrought] = useState<DroughtStatus | null>(null);
  const [marine, setMarine] = useState<MarineState | null>(null);
  const [seaLevel, setSeaLevel] = useState<SeaLevelState | null>(null);
  const [compound, setCompound] = useState<CompoundFlag[]>([]);
  const [rainfall, setRainfall] = useState<RainfallSeries | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDrought(null);
    setMarine(null);
    setSeaLevel(null);
    setCompound([]);
    setRainfall(null);
    (async () => {
      try {
        const [d, m, s, c, r] = await Promise.all([
          getDrought(geoId),
          getMarine(geoId),
          getSeaLevel(geoId),
          getCompound(geoId),
          getRainfall(geoId),
        ]);
        if (cancelled) return;
        setDrought(d);
        setMarine(m);
        setSeaLevel(s);
        setCompound(c);
        setRainfall(r);
      } catch {
        /* noop — show "unavailable" */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [geoId]);

  return { drought, marine, seaLevel, compound, rainfall };
}
