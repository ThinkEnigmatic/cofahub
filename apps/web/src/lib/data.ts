/** Typed data-fetch helpers over the COFAHUB API. */
import { api } from "./api";
import type {
  CompoundFlag,
  DroughtStatus,
  EnsoState,
  MarineState,
  SeaLevelState,
  Station,
  Trend,
  Verification,
} from "./types";

export const getStations = () => api<Station[]>("/stations");
export const getEnso = () => api<EnsoState>("/enso");
export const getDrought = (geoId: string) => api<DroughtStatus>("/drought/" + geoId);
export const getMarine = (geoId: string) => api<MarineState>("/marine/" + geoId);
export const getSeaLevel = (geoId: string) => api<SeaLevelState>("/sealevel/" + geoId);
export const getCompound = (geoId: string) => api<CompoundFlag[]>("/compound/" + geoId);
export const getVerification = (geoId: string) => api<Verification>("/verification/" + geoId);
export const getTrends = (geoId: string) =>
  api<{ available: boolean; stationId?: string; rainfall?: Trend; tmax?: Trend }>(
    "/trends/" + geoId,
  );
export const getRainfall = (geoId: string) =>
  api<{ available: boolean; months: string[]; values: number[]; climatology: number[] }>(
    "/rainfall/" + geoId,
  );
export const getPlans = () =>
  api<
    {
      title: string;
      country: string;
      docType: string;
      date: string | null;
      publisher: string;
      url: string;
      keyFacts: string[];
      summary: string;
    }[]
  >("/plans");

/** A station with its drought level resolved (for the rail dots). */
export type StationWithLevel = Station & { level: string | null };
