import { useEffect, useState } from "react";
import DroughtLevel from "../components/DroughtLevel";
import Readout from "../components/Readout";
import { getTrends, getVerification } from "../lib/data";
import { useSelection } from "../lib/selection";
import { useStation } from "../lib/useStation";
import type { Trend, Verification } from "../lib/types";

export default function Drought() {
  const { geoId } = useSelection();
  const { drought } = useStation(geoId);
  const [verification, setVerification] = useState<Verification | null>(null);
  const [trends, setTrends] = useState<{ rainfall?: Trend; tmax?: Trend } | null>(null);

  useEffect(() => {
    setVerification(null);
    setTrends(null);
    getVerification(geoId).then(setVerification).catch(() => {});
    getTrends(geoId).then((t) => setTrends(t.available ? t : null)).catch(() => {});
  }, [geoId]);

  return (
    <div className="section">
      <div className="section-head">
        <h1>Drought &amp; water</h1>
        <p className="deck">
          The four USGS western-Pacific indices — 1/3/6-month Rainfall Index and the PEAC
          4/8-inch traffic light — on ERA5, with forecast verification and the long-term
          station trend.
        </p>
      </div>

      {/* Drought level — the hero indicator. */}
      <DroughtLevel
        level={drought?.d0D4 ?? null}
        percentile={drought?.percentile ?? null}
        latestMonth={drought?.latestMonth ?? null}
      />

      <div className="readout-grid" style={{ marginTop: "1rem" }}>
        <Readout
          label="Rainfall Index · 1-mo"
          value={drought?.rainIndex1m ?? "—"}
          tone={drought?.rainIndex1m === "Drier" || drought?.rainIndex1m === "Dry" ? "warn" : "key"}
          provenance={drought?.latestMonth ? `as of ${drought.latestMonth}` : undefined}
        />
        <Readout
          label="Rainfall Index · 3-mo"
          value={drought?.rainIndex3m ?? "—"}
          tone={drought?.rainIndex3m === "Drier" || drought?.rainIndex3m === "Dry" ? "warn" : "key"}
        />
        <Readout
          label="Rainfall Index · 6-mo"
          value={drought?.rainIndex6m ?? "—"}
          tone={drought?.rainIndex6m === "Drier" || drought?.rainIndex6m === "Dry" ? "warn" : "key"}
        />
        <Readout
          label="PEAC 4/8-in index"
          value={drought?.peacIndex ?? "—"}
          tone={drought?.peacIndex === "Red" ? "warn" : drought?.peacIndex === "Dark Green" ? "key" : "default"}
          provenance="Red <101.6 · Yellow 101.6–203.2 · Dark Green >203.2 mm"
        />
      </div>

      <div className="panel" style={{ marginTop: "1.5rem" }}>
        <h2>Rolling totals</h2>
        <div className="panel-sub">right-aligned N-month precipitation sums</div>
        <div className="grid-3">
          <Readout label="1-month" value={drought?.rain1mMm != null ? drought.rain1mMm.toFixed(0) : "—"} unit="mm" />
          <Readout label="3-month" value={drought?.rain3mMm != null ? drought.rain3mMm.toFixed(0) : "—"} unit="mm" />
          <Readout label="6-month" value={drought?.rain6mMm != null ? drought.rain6mMm.toFixed(0) : "—"} unit="mm" />
        </div>
      </div>

      {verification?.available && (
        <div className="panel" style={{ marginTop: "1.5rem" }}>
          <h2>Forecast verification</h2>
          <div className="panel-sub">
            last {verification.nDays} days vs {verification.observedSource}
          </div>
          <div className="grid-3">
            <Readout label="Bias (fc − obs)" value={`${verification.biasMm >= 0 ? "+" : ""}${verification.biasMm.toFixed(1)}`} unit="mm" />
            <Readout label="MAE" value={verification.maeMm.toFixed(1)} unit="mm" />
            <Readout label="Correlation" value={verification.correlation.toFixed(2)} />
          </div>
        </div>
      )}

      {trends && (
        <div className="panel" style={{ marginTop: "1.5rem" }}>
          <h2>Climate trend</h2>
          <div className="panel-sub">station record, Mann-Kendall significance</div>
          <div className="grid-2">
            {trends.rainfall && (
              <div>
                <div className="readout-label">Annual rainfall</div>
                <div className="row">
                  <span className="readout-value" style={{ fontSize: "1.8rem" }}>
                    {trends.rainfall.slopePerDecade >= 0 ? "+" : ""}
                    {trends.rainfall.slopePerDecade.toFixed(1)}
                  </span>
                  <span className="readout-unit">mm/decade</span>
                </div>
                <div className="muted">
                  {trends.rainfall.verdict ?? "—"} (p={trends.rainfall.mannKendall.pValue.toFixed(2)}) ·{" "}
                  {trends.rainfall.start}–{trends.rainfall.end}
                </div>
              </div>
            )}
            {trends.tmax && (
              <div>
                <div className="readout-label">Mean Tmax</div>
                <div className="row">
                  <span className="readout-value" style={{ fontSize: "1.8rem" }}>
                    {trends.tmax.slopePerDecade >= 0 ? "+" : ""}
                    {trends.tmax.slopePerDecade.toFixed(2)}
                  </span>
                  <span className="readout-unit">°C/decade</span>
                </div>
                <div className="muted">
                  {trends.tmax.verdict ?? "—"} (p={trends.tmax.mannKendall.pValue.toFixed(2)})
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
