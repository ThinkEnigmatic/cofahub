const SOURCES = [
  ["U.S. Drought Monitor (USDM)", "official D0–D4 drought ranking (weekly, source of truth)"],
  ["NOAA CPC ONI", "live ENSO index + derived phase"],
  ["NOAA CPC ENSO Discussion", "official status statement"],
  ["PEAC rainfall outlook", "tercile seasonal outlook (freshness-flagged)"],
  ["Open-Meteo / ERA5", "forecast + archive (rain, temperature)"],
  ["GHCNd", "in-situ airport gauges (ground truth)"],
  ["CHIRPS v3 / IMERG", "satellite precipitation"],
  ["IBTrACS / JMA / JTWC / NWS Guam", "cyclone tracks + active storms"],
  ["Himawari-9", "geostationary imagery"],
  ["UHSLC", "tide-gauge sea level"],
  ["Open-Meteo marine", "waves + sea-surface temperature"],
  ["USGS SSEBop", "actual evapotranspiration (2003–2021)"],
  ["NMME", "multi-model seasonal outlook"],
  ["RMI 2021 · FSM 2023 · Palau 2020 censuses", "atoll/state population + infrastructure (airports, ports)"],
  ["WorldPop / HDX / geoBoundaries", "population grid + boundaries"],
];

export default function About() {
  return (
    <div className="section">
      <div className="section-head">
        <h1>About COFAHUB</h1>
        <p className="deck">
          Weather operations and anticipatory climate intelligence for the Freely Associated
          States — Palau, the Federated States of Micronesia, and the Marshall Islands. The
          intent is analysis and <em>action</em>: drought early warning, water security, and
          cyclone preparedness for atoll nations.
        </p>
      </div>

      <div className="panel">
        <h2>Scientific integrity</h2>
        <div className="panel-sub">the rules this tool never breaks</div>
        <ul className="stack" style={{ listStyle: "none", color: "var(--nn-ink-2)", fontSize: "0.9rem" }}>
          <li>— Missing data stays missing; nothing is fabricated.</li>
          <li>— Every number carries provenance (source + retrieved time).</li>
          <li>— The D0–D4 ranking is the official U.S. Drought Monitor (weekly); the precipitation-percentile figure is a separate, clearly-labelled local estimate.</li>
          <li>— Classification is deterministic and verified against the USGS R scripts.</li>
          <li>— Drought is a water balance (P − ET), not rainfall alone.</li>
          <li>— The AI layer is a read-only, sandboxed analyst over a data snapshot.</li>
        </ul>
      </div>

      <div className="panel" style={{ marginTop: "1.5rem" }}>
        <h2>Data sources</h2>
        <div className="panel-sub">all live, all public</div>
        <div className="stack" style={{ fontSize: "0.875rem" }}>
          {SOURCES.map(([name, note]) => (
            <div className="row" key={name} style={{ justifyContent: "space-between" }}>
              <span className="mono" style={{ color: "var(--nn-key-glow)", fontSize: "0.75rem" }}>
                {name}
              </span>
              <span className="muted">{note}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
