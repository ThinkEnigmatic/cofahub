import { DROUGHT_SEVERITY } from "../lib/drought";
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
  level: DroughtLevel | null;
  /** Empirical percentile (0..1) of the latest month. */
  percentile: number | null;
  latestMonth?: string | null;
}

/**
 * The prominent drought-level hero — a big D0–D4 with its severity label and
 * percentile provenance. Used in the overview and the drought view.
 */
export default function DroughtLevel({ level, percentile, latestMonth }: Props) {
  return (
    <div className="drought-hero" data-level={level ?? "none"}>
      <div className="drought-hero-level">{level ?? "—"}</div>
      <div className="drought-hero-body">
        <div className="drought-hero-label">
          {level ? DROUGHT_SEVERITY[level] : "No drought"}
        </div>
        <div className="drought-hero-sub">
          {percentile != null
            ? `${ordinal(Math.round(percentile * 100))} percentile of 1991–2020${latestMonth ? ` · ${latestMonth}` : ""}`
            : "no current precipitation data"}
        </div>
      </div>
    </div>
  );
}
