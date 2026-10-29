import { useEffect, useState } from "react";
import { getUsdm } from "./data";
import type { UsdmStatus } from "./types";

/** Fetch the official U.S. Drought Monitor status once (shared across the app). */
export function useUsdm(): UsdmStatus | null {
  const [usdm, setUsdm] = useState<UsdmStatus | null>(null);

  useEffect(() => {
    let cancelled = false;
    getUsdm()
      .then((d) => {
        if (!cancelled && d.ok) setUsdm(d);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return usdm;
}
