import { useEffect, useState } from "react";
import Readout from "../components/Readout";
import { getEnso } from "../lib/data";
import type { EnsoState } from "../lib/types";

export default function Enso() {
  const [enso, setEnso] = useState<EnsoState | null>(null);
  useEffect(() => {
    getEnso().then(setEnso).catch(() => {});
  }, []);

  return (
    <div className="section">
      <div className="section-head">
        <h1>ENSO &amp; climate</h1>
        <p className="deck">
          The Oceanic Niño Index drives drought and sea level across the FAS. Historical
          analogs by peak-ONI proximity are contextual evidence, not a forecast.
        </p>
      </div>

      <div className="readout-grid">
        <Readout
          label="ONI"
          value={enso ? `${enso.anom >= 0 ? "+" : ""}${enso.anom.toFixed(2)}` : "—"}
          unit="°C"
          tone={enso?.phase === "el_nino" ? "pink" : enso?.phase === "la_nina" ? "key" : "default"}
          provenance={enso ? `${enso.season} ${enso.year}` : undefined}
        />
        <Readout
          label="Phase"
          value={enso ? enso.phase.replace("_", " ") : "—"}
          tone={enso?.phase === "el_nino" ? "pink" : "default"}
        />
      </div>

      {enso?.analogs && enso.analogs.length > 0 && (
        <div className="panel" style={{ marginTop: "1.5rem" }}>
          <h2>Historical analogs</h2>
          <div className="panel-sub">closest episodes by peak |ONI| proximity</div>
          <div className="stack">
            {enso.analogs.map((a) => (
              <div className="row" key={a.episodeId} style={{ justifyContent: "space-between" }}>
                <span>
                  <strong style={{ fontFamily: "var(--font-display)", fontSize: "1.15rem" }}>
                    {a.episodeId}
                  </strong>{" "}
                  <span className="muted">({a.intensity})</span>
                </span>
                <span className="mono" style={{ fontSize: "0.75rem", color: "var(--nn-ink-2)" }}>
                  peak {a.peakOni >= 0 ? "+" : ""}
                  {a.peakOni.toFixed(1)} °C · similarity {a.similarity.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
