import { DROUGHT_SEVERITY, USDM_IMPACT } from "../lib/drought";
import type { DroughtLevel } from "../lib/types";

function ordinal(n: number): string {
  const r10 = n % 10;
  const r100 = n % 100;
  if (r10 === 1 && r100 !== 11) return `${n}st`;
  if (r10 === 2 && r100 !== 12) return `${n}nd`;
  if (r10 === 3 && r100 !== 13) return `${n}rd`;
  return `${n}th`;
}

interface Props {
  /** Whether the official U.S. Drought Monitor ranks this island at all. */
  ranked: boolean;
  /** Official USDM level (null = no drought, when ranked). */
  usdmLevel: DroughtLevel | null;
  usdmImpact: string | null;
  usdmDate: string | null;
  /** The local precipitation-percentile estimate (separate indicator). */
  localLevel: DroughtLevel | null;
  /** Empirical percentile (0..1) of the latest month (local estimate). */
  percentile: number | null;
  latestMonth?: string | null;
}

/**
 * The prominent drought-level hero. The big D# is the official U.S. Drought
 * Monitor category (the source of truth); the local precipitation-percentile
 * estimate is shown beneath it as a separate, clearly-labelled indicator.
 */
export default function DroughtLevel({
  ranked,
  usdmLevel,
  usdmImpact,
  usdmDate,
  localLevel,
  percentile,
  latestMonth,
}: Props) {
  const label = ranked
    ? usdmLevel
      ? DROUGHT_SEVERITY[usdmLevel]
      : "No drought"
    : "Not ranked by USDM";

  const provenance = ranked
    ? `U.S. Drought Monitor · ${usdmDate ?? "n/a"}${
        usdmImpact ? ` · ${USDM_IMPACT[usdmImpact] ?? usdmImpact}` : ""
      }`
    : "no official USDM category for this island";

  return (
    <div className="drought-hero" data-level={usdmLevel ?? "none"}>
      <div className="drought-hero-level">{usdmLevel ?? "—"}</div>
      <div className="drought-hero-body">
        <div className="drought-hero-label">{label}</div>
        <div className="drought-hero-sub">{provenance}</div>
        <div className="drought-hero-local">
          Local estimate: {localLevel ?? "—"}
          {percentile != null ? ` (${ordinal(Math.round(percentile * 100))} percentile)` : ""}
          {latestMonth ? ` · ${latestMonth}` : ""} — precipitation percentile, not USDM
        </div>
      </div>
    </div>
  );
}
