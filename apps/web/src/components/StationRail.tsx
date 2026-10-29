import { useSelection } from "../lib/selection";
import { useStations } from "../lib/useStations";

const COUNTRY_ORDER = ["PW", "FM", "MH"] as const;

/** The station rail: atolls grouped by country, each with a drought-level dot. */
export default function StationRail() {
  const { geoId, setGeoId } = useSelection();
  const { stations, levels } = useStations();

  return (
    <nav className="rail" aria-label="Stations">
      {COUNTRY_ORDER.map((cc) => {
        const group = stations.filter((s) => s.country === cc && s.entityType !== "country");
        if (!group.length) return null;
        const name = { PW: "Palau", FM: "Micronesia (FSM)", MH: "Marshall Islands" }[cc];
        return (
          <div className="rail-group" key={cc}>
            <div className="rail-group-title">{name}</div>
            {group.map((s) => (
              <button
                key={s.geoId}
                className="rail-item"
                aria-selected={s.geoId === geoId}
                onClick={() => setGeoId(s.geoId)}
              >
                <span className="rail-dot" data-level={levels[s.geoId] ?? undefined} />
                <span>{s.name}</span>
              </button>
            ))}
          </div>
        );
      })}
    </nav>
  );
}
