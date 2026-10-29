import { useEffect, useState } from "react";
import {
  getCompound,
  getDrought,
  getEnso,
  getMarine,
  getRainfall,
  getSeaLevel,
  getStations,
  getTrends,
  getVerification,
} from "../lib/data";
import { useSelection } from "../lib/selection";
import { DROUGHT_SEVERITY } from "../lib/drought";
import type {
  CompoundFlag,
  DroughtStatus,
  EnsoState,
  MarineState,
  SeaLevelState,
  Station,
  Trend,
  Verification,
} from "../lib/types";

interface RainfallSeries {
  available: boolean;
  months: string[];
  values: number[];
  climatology: number[];
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function fmtMonth(ym: string): string {
  const [y, m] = ym.split("-");
  return `${MONTHS[Number(m) - 1]} ${y.slice(2)}`;
}

function num(v: number | null | undefined, digits = 0, suffix = ""): string {
  if (v == null || Number.isNaN(v)) return "—";
  return `${v.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits })}${suffix}`;
}

function signed(v: number | null | undefined, digits = 1): string {
  if (v == null || Number.isNaN(v)) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(digits)}`;
}

/** A single label/value row in a report section. */
function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="report-row">
      <span className="report-k">{k}</span>
      <span className="report-v">{v}</span>
    </div>
  );
}

/**
 * The print-only situation report for the selected atoll. Always mounted
 * (hidden on screen, shown by the @media print styles), so the "Print report"
 * button simply calls window.print(). Self-contained: fetches every available
 * indicator for the current selection, stamped with the generation date.
 */
export default function PrintReport() {
  const { geoId } = useSelection();
  const [station, setStation] = useState<Station | null>(null);
  const [enso, setEnso] = useState<EnsoState | null>(null);
  const [drought, setDrought] = useState<DroughtStatus | null>(null);
  const [marine, setMarine] = useState<MarineState | null>(null);
  const [seaLevel, setSeaLevel] = useState<SeaLevelState | null>(null);
  const [compound, setCompound] = useState<CompoundFlag[]>([]);
  const [rainfall, setRainfall] = useState<RainfallSeries | null>(null);
  const [verification, setVerification] = useState<Verification | null>(null);
  const [trends, setTrends] = useState<{ rainfall?: Trend; tmax?: Trend } | null>(null);
  const [stamp, setStamp] = useState("");

  useEffect(() => {
    setStamp(new Date().toLocaleString("en-US", { dateStyle: "full", timeStyle: "short" }));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setStation(null);
    setEnso(null);
    setDrought(null);
    setMarine(null);
    setSeaLevel(null);
    setCompound([]);
    setRainfall(null);
    setVerification(null);
    setTrends(null);

    (async () => {
      const results = await Promise.allSettled([
        getStations(),
        getEnso(),
        getDrought(geoId),
        getMarine(geoId),
        getSeaLevel(geoId),
        getCompound(geoId),
        getRainfall(geoId),
        getVerification(geoId),
        getTrends(geoId),
      ]);
      if (cancelled) return;

      const [stationsR, ensoR, droughtR, marineR, seaLevelR, compoundR, rainfallR, verifR, trendsR] = results;
      if (stationsR.status === "fulfilled") {
        setStation(stationsR.value.find((s) => s.geoId === geoId) ?? null);
      }
      if (ensoR.status === "fulfilled") setEnso(ensoR.value);
      if (droughtR.status === "fulfilled") setDrought(droughtR.value);
      if (marineR.status === "fulfilled") setMarine(marineR.value);
      if (seaLevelR.status === "fulfilled") setSeaLevel(seaLevelR.value);
      if (compoundR.status === "fulfilled") setCompound(compoundR.value);
      if (rainfallR.status === "fulfilled") setRainfall(rainfallR.value);
      if (verifR.status === "fulfilled") setVerification(verifR.value);
      if (trendsR.status === "fulfilled") {
        setTrends(trendsR.value.available ? trendsR.value : null);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [geoId]);

  const name = station?.name ?? geoId;
  const country = station?.countryName ?? "";
  const recentMonths = rainfall && rainfall.months.length ? rainfall.months.slice(-12) : [];

  return (
    <article className="print-report">
      <header className="report-head">
        <div className="report-kicker">COFAHUB · FAS climate intelligence</div>
        <h1 className="report-title">Situation report — {name}</h1>
        <div className="report-meta">
          {country} · {geoId} · generated {stamp}
        </div>
        {station && (
          <div className="report-meta report-meta-2">
            {station.entityType} · {station.lat.toFixed(2)}° N, {station.lon.toFixed(2)}° E
            {station.areaKm2 != null ? ` · ${station.areaKm2.toFixed(0)} km² land` : ""}
          </div>
        )}
      </header>

      {/* People & access */}
      <section className="report-section">
        <h2>People &amp; access</h2>
        <Row
          k="Population"
          v={
            station?.population != null
              ? `${station.population.toLocaleString()}  (${station.populationYear ?? "year unknown"} census)`
              : "not enumerated as a single unit"
          }
        />
        {station?.populationSource && <Row k="Source" v={station.populationSource} />}
        <Row k="Airport" v={station?.airport ?? "none"} />
        <Row k="Port" v={station?.port ?? "none"} />
        {station?.notes && <Row k="Note" v={station.notes} />}
      </section>

      {/* Drought & water */}
      <section className="report-section">
        <h2>Drought &amp; water{drought?.latestMonth ? `  (as of ${drought.latestMonth})` : ""}</h2>
        {!drought?.available ? (
          <Row k="Status" v="unavailable" />
        ) : (
          <>
            <Row
              k="Drought level"
              v={drought.d0D4 ? `${drought.d0D4} — ${DROUGHT_SEVERITY[drought.d0D4]}` : "no drought"}
            />
            <Row
              k="PEAC 4/8-inch index"
              v={drought.peacIndex ?? "—"}
            />
            <Row
              k="Monthly rainfall"
              v={
                drought.monthlyMm != null
                  ? `${num(drought.monthlyMm, 0)} mm  (median ${num(drought.climMedianMm, 0)} mm, ${drought.percentile != null ? `${(drought.percentile * 100).toFixed(0)}th` : "—"} percentile)`
                  : "—"
              }
            />
            <Row
              k="Rainfall index"
              v={`1-mo ${drought.rainIndex1m ?? "—"} · 3-mo ${drought.rainIndex3m ?? "—"} · 6-mo ${drought.rainIndex6m ?? "—"}`}
            />
            <Row
              k="Rolling totals"
              v={`1-mo ${num(drought.rain1mMm, 0)} mm · 3-mo ${num(drought.rain3mMm, 0)} mm · 6-mo ${num(drought.rain6mMm, 0)} mm`}
            />
          </>
        )}

        {recentMonths.length > 0 && (
          <table className="report-table">
            <thead>
              <tr>
                <th>Month</th>
                <th className="r">Rain (mm)</th>
                <th className="r">Climatology (mm)</th>
                <th className="r">Anomaly (mm)</th>
              </tr>
            </thead>
            <tbody>
              {recentMonths.map((m) => {
                const idx = rainfall!.months.indexOf(m);
                const v = rainfall!.values[idx];
                const c = rainfall!.climatology[idx];
                return (
                  <tr key={m}>
                    <td>{fmtMonth(m)}</td>
                    <td className="r">{num(v, 0)}</td>
                    <td className="r">{num(c, 0)}</td>
                    <td className="r">{signed(v - c, 0)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>

      {/* Marine */}
      <section className="report-section">
        <h2>Marine</h2>
        {!marine?.available ? (
          <Row k="Status" v="unavailable" />
        ) : (
          <>
            <Row
              k="Waves"
              v={`${num(marine.waveHeightM, 1)} m · ${num(marine.wavePeriodS, 0)} s · ${num(marine.waveDirectionDeg, 0)}°`}
            />
            <Row k="Sea-surface temperature" v={num(marine.sstC, 1, " °C")} />
            <Row
              k="Bleaching watch"
              v={
                marine.dhwCWeeks != null
                  ? `${num(marine.dhwCWeeks, 1, " °C-wk")}  (${marine.bleachingAlert ?? "n/a"})`
                  : marine.bleachingAlert ?? "—"
              }
            />
          </>
        )}
      </section>

      {/* Sea level */}
      <section className="report-section">
        <h2>Sea level</h2>
        {!seaLevel?.available ? (
          <Row k="Status" v="no UHSLC tide gauge for this location" />
        ) : (
          <>
            <Row
              k="Latest daily"
              v={`${num(seaLevel.latestMm, 0)} mm  (${seaLevel.station} · ${seaLevel.lastDate ?? ""})`}
            />
            <Row k="30-day mean" v={num(seaLevel.mean30Mm, 0, " mm")} />
          </>
        )}
      </section>

      {/* Hazard flags */}
      {compound.length > 0 && (
        <section className="report-section">
          <h2>Hazard flags</h2>
          {compound.map((f, i) => (
            <Row key={i} k={f.severity === "warning" ? "Warning" : "Watch"} v={f.text} />
          ))}
        </section>
      )}

      {/* ENSO context */}
      <section className="report-section">
        <h2>ENSO context</h2>
        {!enso?.available ? (
          <Row k="Status" v="unavailable" />
        ) : (
          <>
            <Row
              k="Phase"
              v={`${enso.phase.replace("_", " ")} · ONI ${signed(enso.anom, 2)} °C (${enso.season} ${enso.year})`}
            />
            {enso.analogs?.[0] && (
              <Row
                k="Closest analog"
                v={`${enso.analogs[0].episodeId} (peak ${signed(enso.analogs[0].peakOni, 1)} °C)`}
              />
            )}
          </>
        )}
      </section>

      {/* Verification */}
      <section className="report-section">
        <h2>Forecast verification</h2>
        {!verification?.available ? (
          <Row k="Status" v="unavailable" />
        ) : (
          <>
            <Row
              k="Window"
              v={`last ${verification.nDays} days vs ${verification.observedSource} (${verification.periodStart} → ${verification.periodEnd})`}
            />
            <Row
              k="Error"
              v={`bias ${signed(verification.biasMm, 1)} mm · MAE ${num(verification.maeMm, 1, " mm")} · RMSE ${num(verification.rmseMm, 1, " mm")} · r ${num(verification.correlation, 2)}`}
            />
          </>
        )}
      </section>

      {/* Climate trend */}
      {(trends?.rainfall || trends?.tmax) && (
        <section className="report-section">
          <h2>Climate trend (station record)</h2>
          {trends.rainfall && (
            <Row
              k="Annual rainfall"
              v={`${signed(trends.rainfall.slopePerDecade, 1)} mm/decade · ${trends.rainfall.verdict ?? "n/a"} (p=${trends.rainfall.mannKendall.pValue.toFixed(2)}) · ${trends.rainfall.start}–${trends.rainfall.end}`}
            />
          )}
          {trends.tmax && (
            <Row
              k="Mean Tmax"
              v={`${signed(trends.tmax.slopePerDecade, 2)} °C/decade · ${trends.tmax.verdict ?? "n/a"} (p=${trends.tmax.mannKendall.pValue.toFixed(2)})`}
            />
          )}
        </section>
      )}

      <footer className="report-foot">
        Sources: ERA5 (Open-Meteo) · UHSLC tide gauges · NOAA CPC ONI · GHCNd · simplified NOAA Coral
        Reef Watch · national censuses (RMI 2021, FSM 2023, Palau 2020). Figures reflect the most
        recent available data as of {stamp || "generation"}; missing data is shown as "—" and never
        estimated.
      </footer>
    </article>
  );
}
