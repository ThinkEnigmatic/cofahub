/** COFAHUB — FAS climate-intelligence data model (camelCase, matches the API). */

export type DroughtLevel = "D0" | "D1" | "D2" | "D3" | "D4";
export type Quintile = "Drier" | "Dry" | "Typical" | "Wet" | "Wetter";
export type PeacIndex = "Red" | "Yellow" | "Dark Green";

export interface Station {
  geoId: string;
  name: string;
  country: "PW" | "FM" | "MH";
  countryName: string;
  lat: number;
  lon: number;
  population: number | null;
  populationYear: number | null;
  populationSource: string | null;
  airport: string | null;
  port: string | null;
  areaKm2: number | null;
  entityType: string;
  notes: string | null;
}

export interface DroughtStatus {
  available: boolean;
  latestMonth: string | null;
  monthlyMm: number | null;
  climMedianMm: number | null;
  percentile: number | null;
  quintile: Quintile | null;
  d0D4: DroughtLevel | null;
  peacIndex: PeacIndex | null;
  rainIndex1m: Quintile | null;
  rainIndex3m: Quintile | null;
  rainIndex6m: Quintile | null;
  rain1mMm: number | null;
  rain3mMm: number | null;
  rain6mMm: number | null;
}

export interface EnsoAnalog {
  episodeId: string;
  intensity?: string;
  peakOni: number;
  similarity: number;
  start: string;
  end: string;
}

export interface EnsoState {
  available: boolean;
  phase: "el_nino" | "la_nina" | "neutral";
  season: string;
  year: number;
  anom: number;
  analogs: EnsoAnalog[];
}

export interface MarineState {
  available: boolean;
  waveHeightM: number | null;
  wavePeriodS: number | null;
  waveDirectionDeg: number | null;
  sstC: number | null;
  dhwCWeeks: number | null;
  bleachingAlert: string | null;
}

export interface SeaLevelState {
  available: boolean;
  station: string;
  latestMm: number | null;
  mean30Mm: number | null;
  lastDate: string | null;
}

export interface CompoundFlag {
  text: string;
  severity: "watch" | "warning";
}

export interface Verification {
  available: boolean;
  nDays: number;
  biasMm: number;
  maeMm: number;
  rmseMm: number;
  correlation: number;
  observedSource: string;
  periodStart: string;
  periodEnd: string;
}

export interface Trend {
  name: string;
  unit: string;
  nPoints: number;
  slopePerYear: number;
  slopePerDecade: number;
  verdict: "increasing" | "decreasing" | "no trend" | null;
  start: string;
  end: string;
  mannKendall: { tau: number; pValue: number; trend: string | null };
}

/** A single island's official USDM ranking. */
export interface UsdmStation {
  level: DroughtLevel | null;
  impact: "S" | "L" | "SL" | null;
  usdmName: string;
}

/** The official U.S. Drought Monitor status for the FAS (source of truth). */
export interface UsdmStatus {
  ok: boolean;
  date: string;
  sourceName: string;
  sourceUrl: string;
  stations: Record<string, UsdmStation>;
}
