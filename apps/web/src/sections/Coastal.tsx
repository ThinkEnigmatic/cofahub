import Readout from "../components/Readout";
import { useSelection } from "../lib/selection";
import { useStation } from "../lib/useStation";

export default function Coastal() {
  const { geoId } = useSelection();
  const { marine, seaLevel, compound } = useStation(geoId);

  return (
    <div className="section">
      <div className="section-head">
        <h1>Coastal &amp; marine</h1>
        <p className="deck">
          Waves, sea-surface temperature, coral-bleaching risk and tide-gauge sea level —
          the inundation side of the atoll hazard picture.
        </p>
      </div>

      <div className="readout-grid">
        <Readout
          label="Wave height"
          value={marine?.waveHeightM != null ? marine.waveHeightM.toFixed(1) : "—"}
          unit="m"
          provenance="significant wave height"
        />
        <Readout
          label="Wave period"
          value={marine?.wavePeriodS != null ? marine.wavePeriodS.toFixed(0) : "—"}
          unit="s"
        />
        <Readout
          label="Wave direction"
          value={marine?.waveDirectionDeg != null ? `${marine.waveDirectionDeg.toFixed(0)}°` : "—"}
        />
        <Readout
          label="Sea-surface temp"
          value={marine?.sstC != null ? marine.sstC.toFixed(1) : "—"}
          unit="°C"
        />
      </div>

      <div className="panel" style={{ marginTop: "1.5rem" }}>
        <h2>Coral bleaching watch</h2>
        <div className="panel-sub">Degree Heating Weeks (simplified NOAA Coral Reef Watch)</div>
        <div className="grid-2">
          <Readout
            label="Degree Heating Weeks"
            value={marine?.dhwCWeeks != null ? marine.dhwCWeeks.toFixed(1) : "—"}
            unit="°C-wk"
          />
          <Readout
            label="Bleaching alert"
            value={marine?.bleachingAlert ?? "—"}
            tone={marine?.bleachingAlert && marine.bleachingAlert !== "No Stress" ? "warn" : "default"}
            provenance="fixed western-Pacific MMM (not per-pixel)"
          />
        </div>
      </div>

      <div className="panel" style={{ marginTop: "1.5rem" }}>
        <h2>Sea level</h2>
        <div className="panel-sub">tide gauge (UHSLC Fast Delivery)</div>
        {seaLevel?.available ? (
          <div className="grid-2">
            <Readout
              label="Latest daily"
              value={seaLevel.latestMm != null ? seaLevel.latestMm.toFixed(0) : "—"}
              unit="mm"
              provenance={`${seaLevel.station} · ${seaLevel.lastDate ?? ""}`}
            />
            <Readout label="30-day mean" value={seaLevel.mean30Mm != null ? seaLevel.mean30Mm.toFixed(0) : "—"} unit="mm" />
          </div>
        ) : (
          <div className="muted">No UHSLC tide gauge for this location.</div>
        )}
      </div>

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
