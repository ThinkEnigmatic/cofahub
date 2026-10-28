# User Guide

## Launch

```bash
cd cofa-forward
uv sync
uv run streamlit run src/cofa_forward/ui/app.py
# → open http://127.0.0.1:8501
```

## Navigation (left sidebar)

* **Units** — metric (default) / imperial. Scientific calculations are always
  metric; imperial is presentation only.
* **Overview** — regional situation picture (map, ENSO status, cyclone activity,
  flagged locations, data freshness, evidence-linked summary).
* **Weather Operations** — pick a location; **Fetch live forecast (Open-Meteo)**
  for real current + hourly + daily data; otherwise a clearly labeled sample
  forecast is shown.
* **ENSO & Climate** — ENSO status/outlook, episode catalog, analog comparison,
  rainfall-anomaly map.
* **Drought & Water** — monthly rainfall vs climatology, rolling totals,
  percentile category, alert thresholds, freshwater framework, SPI note.
* **Tropical Cyclones** — sample tracks, seasonal climatology, closest-approach,
  exposure, ENSO-conditioned note.
* **Historical Impacts** — impact catalog (sample), summaries.
* **Island Profiles** — per-entity geography, conditions, rainfall, drought
  indicators, cyclone exposure, impacts.
* **Reports** — generate and download the Markdown daily brief.
* **Data Sources & System Health** — provider status, ingestion history,
  provenance.

## Scheduling

Bulletin monitoring and ingestion are explicit scripts — run them on a schedule
rather than on page load (no page load triggers a large download).

**cron (every 15 minutes):**
```
*/15 * * * *  cd /Users/ben/cofa-forward && /Users/ben/cofa-forward/.venv/bin/python scripts/monitor_bulletins.py >> logs/monitor.log 2>&1
```

**launchd (macOS)** — create `~/Library/LaunchAgents/com.ben.cofa-bulletins.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.ben.cofa-bulletins</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/ben/cofa-forward/.venv/bin/python</string>
    <string>/Users/ben/cofa-forward/scripts/monitor_bulletins.py</string>
  </array>
  <key>StartInterval</key><integer>900</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>/Users/ben/cofa-forward/logs/monitor.log</string>
  <key>StandardErrorPath</key><string>/Users/ben/cofa-forward/logs/monitor.err.log</string>
</dict></plist>
```
Load with `launchctl load ~/Library/LaunchAgents/com.ben.cofa-bulletins.plist`.

## CLI

```bash
uv run python scripts/initialize_data.py            # generate sample datasets
uv run python scripts/ingest_weather.py --geo PAL-KOR   # fetch live forecast
uv run python scripts/ingest_rainfall.py --geo PAL-KOR --start 1991-01-01 --end 2020-12-31
uv run python scripts/build_climatology.py          # build climatology tables
uv run python scripts/ingest_enso.py                # fetch CPC ONI
uv run python scripts/ingest_ibtracs.py             # fetch IBTrACS FAS tracks
uv run python scripts/ingest_jma.py                 # fetch JMA active storms
uv run python scripts/monitor_bulletins.py          # poll bulletins, record updates
uv run python scripts/generate_report.py            # print the daily brief
uv run python scripts/check_sources.py              # adapter availability
```

## Important conventions

* **Sample data is always labeled.** Live data is only shown after a real fetch
  and always carries its source, valid time, and resolution.
* **No fabricated outputs.** Missing data stays missing; ENSO phase is not
  assumed; no storms, warnings, forecasts, probabilities, or impact counts are
  invented.
* **Evidence tags** (🔵 observed / 🟡 forecast / 🟢 official / 🟣 historical /
  🟠 modeled / ⚪ analyst) distinguish the nature of each statement.
