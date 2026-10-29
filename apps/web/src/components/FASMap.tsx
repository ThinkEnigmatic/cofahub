import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { DROUGHT_HEX, DROUGHT_SEVERITY } from "../lib/drought";
import { useSelection } from "../lib/selection";
import type { DroughtLevel, Station, UsdmStatus } from "../lib/types";

interface FASMapProps {
  stations: Station[];
  /** Local precipitation-percentile estimate (geoId -> D0-D4 or null). */
  levels: Record<string, string | null>;
  /** Official U.S. Drought Monitor status (source of truth for the D ranking). */
  usdm: UsdmStatus | null;
}

const NO_DROUGHT_COLOR = "#00a2c8"; // USDM-ranked, no drought
const UNRANKED_COLOR = "#8a8f98"; // not individually ranked by USDM

/** Marker color from the official USDM category (falls back to "not ranked"). */
function colorFor(geoId: string, usdm: UsdmStatus | null): string {
  const s = usdm?.stations?.[geoId];
  if (!s) return UNRANKED_COLOR;
  return s.level ? DROUGHT_HEX[s.level as DroughtLevel] : NO_DROUGHT_COLOR;
}

const ESRI_IMAGERY =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

/** The FAS satellite map — markers coloured by the official USDM drought level. */
export default function FASMap({ stations, levels, usdm }: FASMapProps) {
  const { geoId, setGeoId } = useSelection();
  const points = stations.filter((s) => s.entityType !== "country");

  return (
    <MapContainer
      center={[6.5, 152]}
      zoom={5}
      minZoom={3}
      maxZoom={12}
      scrollWheelZoom
      style={{ height: "100%", width: "100%", background: "#05050a" }}
      attributionControl
    >
      <TileLayer
        url={ESRI_IMAGERY}
        attribution="Esri, Maxar, Earthstar Geographics"
        maxZoom={19}
      />
      {points.map((s) => {
        const usdmStation = usdm?.stations?.[s.geoId];
        const level = usdmStation?.level ?? null;
        const local = levels[s.geoId] ?? null;
        const selected = s.geoId === geoId;
        return (
          <CircleMarker
            key={s.geoId}
            center={[s.lat, s.lon]}
            radius={selected ? 9 : 6}
            pathOptions={{
              color: selected ? "#ffffff" : colorFor(s.geoId, usdm),
              weight: selected ? 2.5 : 1.2,
              fillColor: colorFor(s.geoId, usdm),
              fillOpacity: selected ? 1 : 0.85,
            }}
            eventHandlers={{ click: () => setGeoId(s.geoId) }}
          >
            <Tooltip direction="top" offset={[0, -6]} opacity={1}>
              {s.name}
              {level ? ` · ${level}` : ""}
            </Tooltip>
            <Popup>
              <strong>{s.name}</strong>
              {level && (
                <>
                  <span className="map-d-level" data-level={level}>
                    {level}
                  </span>{" "}
                  <span className="map-d-label">{DROUGHT_SEVERITY[level as DroughtLevel]}</span>
                </>
              )}
              <br />
              {s.countryName} · {s.geoId}
              <br />
              {usdmStation ? (
                <span>
                  USDM: {level ? level : "no drought"}
                  {usdmStation.impact ? ` (${usdmStation.impact})` : ""}
                </span>
              ) : (
                <span>USDM: not ranked</span>
              )}
              <br />
              <span style={{ color: "var(--nn-ink-2)" }}>
                Local estimate: {local ?? "—"}
              </span>
              <br />
              {s.population != null && (
                <>
                  Pop: {s.population.toLocaleString()}
                  {s.populationYear ? ` (${s.populationYear})` : ""}
                  <br />
                </>
              )}
              <span style={{ color: "var(--nn-ink-2)" }}>
                ✈ {s.airport ?? "no airport"} · ⚓ {s.port ?? "no port"}
              </span>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
