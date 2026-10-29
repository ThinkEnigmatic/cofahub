import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { DROUGHT_HEX, DROUGHT_SEVERITY } from "../lib/drought";
import { useSelection } from "../lib/selection";
import type { DroughtLevel, Station } from "../lib/types";

interface FASMapProps {
  stations: Station[];
  levels: Record<string, string | null>;
}

const NORMAL_COLOR = "#00a2c8";

function colorFor(level: string | null): string {
  return level ? DROUGHT_HEX[level as DroughtLevel] ?? NORMAL_COLOR : NORMAL_COLOR;
}

const ESRI_IMAGERY =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

/** The FAS satellite map — station markers coloured by current drought level. */
export default function FASMap({ stations, levels }: FASMapProps) {
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
        const level = levels[s.geoId] ?? null;
        const selected = s.geoId === geoId;
        return (
          <CircleMarker
            key={s.geoId}
            center={[s.lat, s.lon]}
            radius={selected ? 9 : 6}
            pathOptions={{
              color: selected ? "#ffffff" : colorFor(level),
              weight: selected ? 2.5 : 1.2,
              fillColor: colorFor(level),
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
              {level ? `Drought level: ${level}` : "No drought"}
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
