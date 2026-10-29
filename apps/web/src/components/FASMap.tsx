import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useSelection } from "../lib/selection";
import type { Station } from "../lib/types";

interface FASMapProps {
  stations: Station[];
  levels: Record<string, string | null>;
}

// Drought-level marker colors (the dark-theme ramp, bright enough over imagery).
const LEVEL_COLOR: Record<string, string> = {
  D0: "#c87600",
  D1: "#e0604e",
  D2: "#ff4fa3",
  D3: "#ff2d78",
  D4: "#ff1a4d",
};
const NORMAL_COLOR = "#00a2c8";

function colorFor(level: string | null): string {
  return level ? LEVEL_COLOR[level] ?? NORMAL_COLOR : NORMAL_COLOR;
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
            </Tooltip>
            <Popup>
              <strong>{s.name}</strong>
              <br />
              {s.countryName} · {s.geoId}
              <br />
              {level ? `Drought level: ${level}` : "No drought"}
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
