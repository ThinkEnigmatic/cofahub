import { useEffect, useState } from "react";
import DroughtLevel from "../components/DroughtLevel";
import FASMap from "../components/FASMap";
import RainChart from "../components/RainChart";
import Readout from "../components/Readout";
import { getEnso } from "../lib/data";
import { useSelection } from "../lib/selection";
import { useStation } from "../lib/useStation";
import { useStations } from "../lib/useStations";
import type { EnsoState } from "../lib/types";

export default function Console() {
  const { geoId } = useSelection();
  const { drought, marine, seaLevel, compound, rainfall } = useStation(geoId);
  const { stations, levels } = useStations();
  const [enso, setEnso] = useState<EnsoState | null>(null);

  useEffect(() => {
    getEnso().then(setEnso).catch(() => {});
  }, []);

  const station = stations.find((s) => s.geoId === geoId);
  const name = station?.name ?? geoId;

  return (
    <div className="section">
      <div className="section-head head-row">
        <div>
          <h1>FAS situation</h1>
          <p className="deck">
            Drought, ENSO, sea level and marine conditions for {name} — with provenance on
            every number. This is the operations console, not a forecast.
          </p>
        </div>
        <button className="btn print-btn" onClick={() => window.print()}>
          Print report
        </button>
      </div>

      {/* ENSO strip */}
      <div className="row" style={{ gap: "1rem", marginBottom: "1.25rem" }}>
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

      {/* Satellite map — the regional situation. */}
      <div className="map-panel">
        <FASMap stations={stations} levels={levels} />
        <div className="map-legend">
          <span className="mono-label">Drought level</span>
          <span><i style={{ background: "#00a2c8" }} /> none</span>
          <span><i style={{ background: "#c87600" }} /> D0</span>
          <span><i style={{ background: "#e0604e" }} /> D1</span>
          <span><i style={{ background: "#ff4fa3" }} /> D2</span>
          <span><i style={{ background: "#ff2d78" }} /> D3</span>
          <span><i style={{ background: "#ff1a4d" }} /> D4</span>
        </div>
      </div>

      {/* People & access — socioeconomic profile (most recent census). */}
      <div className="panel" style={{ marginTop: "1.25rem" }}>
        <h2>People &amp; access</h2>
        <div className="panel-sub">
          population · airport · port — {station?.populationSource ?? "census"}
        </div>
        <div className="socio-grid">
          <div className="socio-card">
            <div className="readout-label">Population</div>
            <div className="readout-value">
              {station?.population != null ? station.population.toLocaleString() : "—"}
            </div>
            <div className="readout-prov">
              {station?.populationYear
                ? `${station.populationYear} census`
                : "not enumerated as a single unit"}
            </div>
          </div>
          <div className="socio-card">
            <div className="readout-label">Airport</div>
            <div className="socio-text">{station?.airport ?? <span className="na">none</span>}</div>
          </div>
          <div className="socio-card">
            <div className="readout-label">Port</div>
            <div className="socio-text">{station?.port ?? <span className="na">none</span>}</div>
          </div>
        </div>
        {station?.notes && (
          <p className="muted" style={{ marginTop: "0.6rem", fontSize: "0.8rem", maxWidth: "72ch" }}>
            {station.notes}
          </p>
        )}
      </div>

      {/* Drought level — the hero indicator for this atoll. */}
      <div style={{ marginTop: "1.25rem" }}>
        <DroughtLevel
          level={drought?.d0D4 ?? null}
          percentile={drought?.percentile ?? null}
          latestMonth={drought?.latestMonth ?? null}
        />
      </div>

      {/* Drought readouts */}
      <div className="readout-grid" style={{ marginTop: "1rem" }}>
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
          tone={drought?.d0D4 ? "pink" : "key"}
          provenance="vs 1991–2020 climatology"
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
