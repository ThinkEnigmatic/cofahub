import type { DroughtLevel } from "./types";

/** USDM severity labels for the D0–D4 precipitation-drought scale. */
export const DROUGHT_SEVERITY: Record<DroughtLevel, string> = {
  D0: "Abnormally dry",
  D1: "Moderate drought",
  D2: "Severe drought",
  D3: "Extreme drought",
  D4: "Exceptional drought",
};

/** CSS variable for each drought level (matches the rail/map ramp). */
export const DROUGHT_VAR: Record<DroughtLevel, string> = {
  D0: "var(--d0)",
  D1: "var(--d1)",
  D2: "var(--d2)",
  D3: "var(--d3)",
  D4: "var(--d4)",
};

/** Hex color for Leaflet markers (bright enough over satellite imagery). */
export const DROUGHT_HEX: Record<DroughtLevel, string> = {
  D0: "#c87600",
  D1: "#e0604e",
  D2: "#ff4fa3",
  D3: "#ff2d78",
  D4: "#ff1a4d",
};
