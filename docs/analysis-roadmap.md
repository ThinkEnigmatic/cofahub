# Analysis roadmap — what else would benefit COFA FORWARD

Deep-dive into the tool's remaining gaps, framed by its real job: **anticipatory
water security and climate-hazard early warning for atoll nations** (Palau, FSM,
RMI). Each item is scored for value, feasibility, and effort, with the honest
caveat. Data sources are named and their free/open status noted.

## The core insight

The tool's three structural weaknesses are, in order:

1. **No ground truth.** Every layer is model (ERA5, NMME) or satellite (CHIRPS,
   IMERG, Himawari). The FAS has airport weather stations — the only independent
   check on all of it — and they are not yet wired in.
2. **Precipitation-only drought.** Drought is a *water balance* (precip minus
   evapotranspiration), but the monitor only sees the precip side. The USGS
   release this app now mirrors actually ships an ET + water-budget component
   (SSEBop) that is missing here.
3. **The two biggest atoll hazards are under-served.** Sea-level rise / king-tide
   flooding and cyclone *wind/surge impact* — not just track proximity — are what
   actually damage atolls, and neither is modeled yet.

---

## Priority 1 — In-situ station ground truth (GHCNd)

* **What:** daily precipitation + temperature from the FAS airport WMO stations
  (Koror PTRO, Yap PTYA, Chuuk PTKK, Pohnpei PTPN, Kosrae PTSA, Majuro PKMR,
  Kwajalein PKWA).
* **Why:** the single highest-value addition. It lets the app (a) validate
  ERA5/CHIRPS/IMERG against reality, (b) show a "satellite vs gauge" bias, and
  (c) feed the forecast-verification loop. Today every "drought" call is an
  unverified satellite/model estimate.
* **Source:** NOAA NCEI GHCNd (free, public domain, daily, 1900s–present).
* **Effort:** moderate (adapter + bias comparison + provenance). **Feasibility: high.**

## Priority 2 — Evapotranspiration → true water balance (SSEBop)

* **What:** operational actual ET (SSEBop) + water-balance = precipitation − ET
  per island, giving a real water-deficit drought indicator instead of a rainfall
  one.
* **Why:** this is the "Water Budget components" child of the same USGS release
  (Senay et al. 2026) the app now mirrors for rainfall. It converts "is it dry?"
  into "is there actually a water deficit?"
* **Source:** USGS SSEBop (1 km, global, 2000–present, free, already used by the
  same USGS team).
* **Effort:** moderate. **Feasibility: high.**

## Priority 3 — Sea level + coastal flooding

* **What:** satellite-altimetry sea-level anomaly + (optionally) tide/king-tide
  forecasts per atoll.
* **Why:** ENSO moves western-Pacific sea level by ±20–30 cm; on a 2 m atoll that
  is the difference between dry and flooded. Sea level is arguably the most
  ENSO-coupled, atoll-critical variable the app does not track at all.
* **Source:** AVISO/CMEMS satellite altimetry (free); NOAA CO-OPS tide gauges
  (free, but sparse in the FAS); PEAC also publishes a seasonal sea-level
  forecast (same nav as the rainfall outlook the app already scrapes).
* **Effort:** moderate–high (gridded altimetry is heavy). **Feasibility: high** for
  the PEAC outlook + altimetry point extraction.

## Priority 4 — Cyclone impact (wind + surge), not just proximity

* **What:** wind-impact estimate from JTWC quadrant wind radii (already ingested)
  + a storm-surge/inundation estimate using GEBCO bathymetry.
* **Why:** the app explicitly says "proximity only, no wind impact." For atolls,
  the actual damage is wind + overwash, which a nearest-track distance cannot
  express.
* **Source:** JTWC radii (have it), GEBCO bathymetry (`planned` in sources.yaml),
  a simple parametric wind field + storm-surge model.
* **Effort:** high. **Feasibility: medium** (surge modeling is the hard part; wind
  field is tractable).

## Priority 5 — Forecast verification loop (closed)

* **What:** score the Open-Meteo/ECMWF forecasts against observed (gauge/IMERG)
  rainfall each cycle, surface the skill.
* **Why:** the verification framework (bias/MAE/RMSE/skill) exists and is tested
  but is not run against live data. An unverified forecast in a decision tool
  quietly overstates confidence.
* **Source:** none new — combines #1 (gauge) with existing forecast + archive.
* **Effort:** low. **Feasibility: high.**

## Priority 6 — ENSO → hazard coupling

* **What:** cyclone frequency, sea-level anomaly, and SST/bleaching by ENSO phase
  (the analog engine already exists but has nothing to feed it).
* **Why:** turns "what is ENSO doing" into "what does ENSO mean here" — the
  El Niño drought linkage is partially done; cyclone and sea-level linkages are not.
* **Source:** IBTrACS + ONI (have), altimetry + SST (have the tiles, need the series).
* **Effort:** moderate. **Feasibility: high.**

## Priority 7 — Alerting / decision support

* **What:** push (Telegram/iMessage) when a drought index crosses a threshold, a
  cyclone approaches a location, or the PEAC index flips to Red.
* **Why:** the app is a dashboard; the FAS use case is *early warning*. The
  household already has a Telegram front door (ai-dev) this could reuse.
* **Source:** none new — thresholds + the existing alert engine + a notifier.
* **Effort:** low–moderate. **Feasibility: high.**

---

## Suggested next three

1. **GHCNd stations** (ground truth — unlocks verification + trust).
2. **SSEBop ET + water balance** (completes the drought monitor's other half).
3. **Sea-level anomaly + PEAC sea-level outlook** (the biggest un-modeled atoll
   hazard, and directly ENSO-coupled).

## Honest non-starters (kept out)

* **Groundwater / freshwater-lens depth** — not satellite-observable; needs local
  wells. (Already documented as a missing input, never fabricated.)
* **Exact per-atoll storm surge** — needs high-res bathymetry + a hydrodynamic
  model; GEBCO (450 m) is too coarse for precise atoll overwash.
* **Palau-specific USGS drought data** — the USGS release does not include Palau.
