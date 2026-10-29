import { useEffect, useState } from "react";
import RainChart from "../components/RainChart";
import Readout from "../components/Readout";
import { getEnso, getStations } from "../lib/data";
import { useSelection } from "../lib/selection";
import { useStation } from "../lib/useStation";
import type { EnsoState, Station } from "../lib/types";

const QUINTILE_TONE: Record<string, "default" | "key" | "pink" | "warn"> = {
  Drier: "warn",
  Dry: "warn",
  Typical: "key",
  Wet: "key",
  Wetter: "key",
};

export default function Console() {
  const { geoId } = useSelection();
  const { drought, marine, seaLevel, compound, rainfall } = useStation(geoId);
  const [enso, setEnso] = useState<EnsoState | null>(null);
  const [stations, setStations] = useState<Station[]>([]);

  useEffect(() => {
    getEnso().then(setEnso).catch(() => {});
    getStations().then(setStations).catch(() => {});
  }, []);

  const name = stations.find((s) => s.geoId === geoId)?.name ?? geoId;

  return (
    <div className="section">
      <div className="section-head">
        <h1>FAS situation</h1>
        <p className="deck">
          Drought, ENSO, sea level and marine conditions for {name} — with provenance on
          every number. This is the operations console, not a forecast.
        </p>
      </div>

      {/* ENSO strip */}
      <div className="row" style={{ gap: "1rem", marginBottom: "1.5rem" }}>
        {enso?.available ? (
          <>
            <span className="enso-chip">
              ENSO <strong>{enso.phase.replace("_", " ")}</strong> · ONI{" "}
              {enso.season} {enso.year} <strong>{enso.anom >= 0 ? "+" : ""}{enso.anom.toFixed(2)} °C</strong>
            </span>
            {enso.analogs?.[0] && (
              <span className="enso-chip">
                closest analog <strong>{enso.analogs[0].episodeId}</strong>
              </span>
            )}
          </>
        ) : (
          <span className="enso-chip">ENSO unavailable</span>
        )}
      </div>

      {/* Drought readouts */}
      <div className="readout-grid">
        <Readout
          label="Monthly rainfall"
          value={drought?.monthlyMm != null ? drought.monthlyMm.toFixed(0) : "—"}
          unit="mm"
          provenance={drought ? `${drought.latestMonth} · ERA5` : undefined}
        />
        <Readout
          label="Rainfall percentile"
          value={drought?.percentile != null ? (drought.percentile * 100).toFixed(0) : "—"}
          unit="%"
          tone={drought?.quintile ? QUINTILE_TONE[drought.quintile] : "default"}
          provenance={drought ? `quintile ${drought.quintile}` : undefined}
        />
        <Readout
          label="Drought level"
          value={drought?.d0D4 ?? "—"}
          tone={drought?.d0D4 ? "pink" : "default"}
          provenance={drought ? "precipitation percentile" : undefined}
        />
        <Readout
          label="PEAC 4/8-in index"
          value={drought?.peacIndex ?? "—"}
          tone={drought?.peacIndex === "Red" ? "warn" : drought?.peacIndex === "Dark Green" ? "key" : "default"}
          provenance={drought ? "latest month, absolute" : undefined}
        />
      </div>

      {/* Chart */}
      <div className="panel" style={{ marginTop: "1.5rem" }}>
        <h2>Rainfall vs climatology</h2>
        <div className="panel-sub">monthly precipitation (last 36 months) — the line draws on load</div>
        {rainfall ? <RainChart data={rainfall} /> : <div className="spinner">loading…</div>}
      </div>

      {/* Marine + sea level */}
      <div className="grid-2" style={{ marginTop: "1.5rem" }}>
        <div className="panel">
          <h2>Marine</h2>
          <div className="panel-sub">waves · sea-surface temperature · bleaching</div>
          <div className="grid-3">
            <Readout label="Wave height" value={marine?.waveHeightM != null ? marine.waveHeightM.toFixed(1) : "—"} unit="m" />
            <Readout label="SST" value={marine?.sstC != null ? marine.sstC.toFixed(1) : "—"} unit="°C" />
            <Readout
              label="Bleaching"
              value={marine?.bleachingAlert ?? "—"}
              tone={marine?.bleachingAlert && marine.bleachingAlert !== "No Stress" ? "warn" : "default"}
            />
          </div>
        </div>
        <div className="panel">
          <h2>Sea level</h2>
          <div className="panel-sub">tide gauge (UHSLC)</div>
          {seaLevel?.available ? (
            <Readout
              label="Latest"
              value={seaLevel.latestMm != null ? seaLevel.latestMm.toFixed(0) : "—"}
              unit="mm"
              provenance={`${seaLevel.station} · ${seaLevel.lastDate ?? ""}`}
            />
          ) : (
            <div className="muted">No tide gauge for this location.</div>
          )}
        </div>
      </div>

      {/* Hazard strip */}
      {compound.length > 0 && (
        <div className="stack" style={{ marginTop: "1.5rem" }}>
          {compound.map((f, i) => (
            <div className="hazard" data-severity={f.severity} key={i}>
              <span className="hazard-mark">{f.severity === "warning" ? "⚠" : "▲"}</span>
              <span className="hazard-text">{f.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
