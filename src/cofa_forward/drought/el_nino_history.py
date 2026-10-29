"""Documented El Niño drought crisis history for the Freely Associated States.

This module is **research data, not model output**: every fact below is quoted
from the sources gathered by the 2026-10-29 research swarm (see
``docs/el-nino-drought-research.md``). Each entry carries its source URL so the
UI can link the reader to the underlying reporting.

It is used by the "El Niño comparison" page to (a) place the current cycle in
the context of the last major emergency, and (b) surface the media/relief
reporting for each location. Facts are keyed by ``geo_id``; locations without a
specific entry fall back to their country/state entry (or a regional note).
"""

# ruff: noqa: E501  (long prose strings + source URLs are data, not code)

from __future__ import annotations

# --- The benchmark El Niño events (timing windows, from research) --- #
# windows are (onset_ym, peak_ym, recovery_ym) with month as YYYY-MM.
EL_NINO_EVENTS = [
    {
        "id": "1997-98",
        "label": "1997–98 (strongest in local memory)",
        "onset": "1997-10",
        "peak": "1998-01",
        "recovery": "1998-06",
        "strength": "ONI ~+2.4 °C",
    },
    {
        "id": "2015-16",
        "label": "2015–16 super El Niño (last major emergency)",
        "onset": "2015-10",
        "peak": "2016-01",
        "recovery": "2016-08",
        "strength": "ONI ~+2.6 °C (record)",
    },
    {
        "id": "2023-24",
        "label": "2023–24 (strong, weaker than the two above)",
        "onset": "2023-06",
        "peak": "2023-12",
        "recovery": "2024-06",
        "strength": "ONI ~+2.0 °C",
    },
]

# The event used for the "now vs last major emergency" default comparison.
LAST_MAJOR_EMERGENCY = "2015-16"

# --- Per-location crisis markers (documented, sourced) --- #
# Each: {event_id: {facts..., sources: [{name, url}]}}
CRISIS = {
    # ---- Republic of the Marshall Islands ----
    "RMI": {
        "2015-16": {
            "emergency": "State of Emergency 3 Feb 2016 → State of Disaster 8–10 Mar 2016 (extended twice); U.S. President (FEMA) disaster declaration 27 Apr 2016.",
            "rainfall": "Majuro 27% and Kwajalein 18% of normal rainfall in Jan–Mar 2016; 13 atolls ran out of catchment water.",
            "response": "~21,000 people affected; 55 reverse-osmosis units deployed across 33 communities; water filling stations in Majuro.",
            "sources": [
                {
                    "name": "GFDRR PDNA of the 2015–2016 drought (RMI)",
                    "url": "https://www.gfdrr.org/sites/default/files/publication/pda-2017-marshall-islands.pdf",
                },
                {
                    "name": "NOAA Climate.gov — Drought in the Pacific (2016)",
                    "url": "https://www.climate.gov/news-features/event-tracker/drought-pacific",
                },
                {
                    "name": "IOM El Niño Response Overview (2016)",
                    "url": "https://www.iom.int/sites/g/files/tmzbdl486/files/situation_reports/file/201606-El-Nino-Response-Overview-final.pdf",
                },
            ],
        },
        "1997-98": {
            "emergency": "Drought disaster declared Feb 1998.",
            "rainfall": "Majuro received only 8% of normal rainfall Jan–Apr 1998.",
            "response": "Reverse-osmosis units flown to Majuro; groundwater supplied 90% (Mar) → 64% (May) of Majuro's drinking water.",
            "sources": [
                {
                    "name": "USGS SIR 2005-5098 (Majuro lens, 1998 drought)",
                    "url": "https://pubs.usgs.gov/sir/2005/5098/",
                },
                {
                    "name": "World Bank CCKP — Marshall Islands profile",
                    "url": "https://climateknowledgeportal.worldbank.org/sites/default/files/country-profiles/15817-WB_Marshall%20Islands%20Country%20Profile-WEB_0.pdf",
                },
            ],
        },
        "2023-24": {
            "emergency": "Severe drought (~5,200 people / 15 atolls); Wotje reached D4 exceptional drought. No national disaster declaration.",
            "rainfall": "Majuro Feb 2024 = 5.11 in (2.5 in below normal); reservoir ~71%.",
            "response": "NDMO deployed RO units to 9 of 16 drought-affected atolls.",
            "sources": [
                {
                    "name": "IFRC/ReliefWeb — RMI Drought DREF Final Report (MDRMH004)",
                    "url": "https://reliefweb.int/report/marshall-islands/drought-republic-marshall-islands-2024-dref-final-report-mdrmh004",
                },
            ],
        },
    },
    "RMI-MAJ": {
        "2015-16": {
            "emergency": "Airport reservoir fell below half capacity; municipal filling stations opened.",
            "rainfall": "27% of normal in Jan–Mar 2016.",
            "response": "20,000-gpd RO unit at CMI trucked daily; 21 temporary collection points.",
            "sources": [
                {
                    "name": "Marshall Islands Journal — El Niño water struggles",
                    "url": "https://marshallislandsjournal.com/el-nino-water-struggles/",
                },
            ],
        },
    },
    "RMI-KWA": {
        "2015-16": {
            "emergency": "Severe drought; Kwajalein/Ebeye among hardest-hit.",
            "rainfall": "18% of normal in Jan–Mar 2016 (Kwajalein).",
            "response": "RO units deployed to outer islands incl. Kwajalein.",
            "sources": [
                {
                    "name": "NOAA Climate.gov — Drought in the Pacific (2016)",
                    "url": "https://www.climate.gov/news-features/event-tracker/drought-pacific",
                },
            ],
        },
    },
    "RMI-WOT": {
        "2015-16": {
            "emergency": "Northern atolls (incl. Wotje) driest and slowest to recover.",
            "rainfall": "Severe drought; northern-atoll catchments ran dry.",
            "response": "USDA FNS supplemental food to Wotje among 7 atolls (Oct–Nov 2016).",
            "sources": [
                {
                    "name": "NOAA Climate Resilience Toolkit — Recognizing & responding to drought",
                    "url": "https://prod-01-asg-toolkit-climate.woc.noaa.gov/case-study/recognizing-and-responding-drought-pacific-islands",
                },
            ],
        },
        "2023-24": {
            "emergency": "Wotje reached D4 exceptional drought (2024).",
            "rainfall": "Among the most affected northern atolls.",
            "response": "RO units prioritized for northern atolls.",
            "sources": [
                {
                    "name": "NWS Guam Drought Information Statement (10 May 2024)",
                    "url": "https://www.weather.gov/media/gum/DGT/DGT_GUM_05102024.pdf",
                },
            ],
        },
    },
    "RMI-UTR": {
        "2015-16": {
            "emergency": "Utrik among the driest northern atolls.",
            "rainfall": "Northern atolls incl. Utrik slowest to recover.",
            "response": "Part of the 15-atoll 2013/2016 drought relief area.",
            "sources": [
                {
                    "name": "IFRC Emergency Appeal (2013) / NOAA drought case study",
                    "url": "https://prod-01-asg-toolkit-climate.woc.noaa.gov/case-study/recognizing-and-responding-drought-pacific-islands",
                },
            ],
        },
    },
    # ---- Federated States of Micronesia ----
    "FSM": {
        "2015-16": {
            "emergency": "Presidential Emergency Declaration 18 Feb 2016 (all four states); ~100,000 people affected.",
            "rainfall": "Yap 35%, Kosrae 48%, Pohnpei 49%, Chuuk 71% of normal in Jan–Mar 2016.",
            "response": "$1.4M appropriation; water rationing; taro crops damaged.",
            "sources": [
                {
                    "name": "PEAC Pacific ENSO Update v22 (2016)",
                    "url": "https://www.weather.gov/media/peac/PEU/PEU_v22_n1.pdf",
                },
                {
                    "name": "OCHA Asia-Pacific snapshot (May 2016)",
                    "url": "https://www.unocha.org/publications/report/sri-lanka/asia-and-pacific-weekly-regional-humanitarian-snapshot-17-23-may-2016",
                },
            ],
        },
        "1997-98": {
            "emergency": "FSM + Pohnpei + Chuuk declared states of emergency; U.S. federal disaster assistance July 1998.",
            "rainfall": "Pohnpei/Kosrae at 4–9% of normal in Jan 1998; ~28,800 people (~30% of outer-island population) needed relief.",
            "response": "Bottled water, RO pumps, and rice delivered to every community; water rationing.",
            "sources": [
                {
                    "name": "OCHA FSM El Niño Drought SitRep No. 1 (27 Mar 1998)",
                    "url": "https://reliefweb.int/report/micronesia-federated-states/fsm-el-ni%C3%B1o-drought-ocha-situation-report-no-1",
                },
            ],
        },
        "2023-24": {
            "emergency": "National Emergency 11 Mar 2024 (~22,700 people, ~20% of population); Yap & Ulithi D4 exceptional drought.",
            "rainfall": "Yap's Mar–Apr 2024 = 2nd-driest in 73-year record.",
            "response": "US$1,288,824 Disaster Relief Fund; emergency extended to 30 Sep 2024.",
            "sources": [
                {
                    "name": "FSM Gov — President declares state of emergency (12 Mar 2024)",
                    "url": "https://gov.fm/president-simina-declares-state-of-emergency-amid-drought/",
                },
                {
                    "name": "UNICEF FSM & RMI Drought SitRep (Apr 2024)",
                    "url": "https://reliefweb.int/report/micronesia-federated-states/unicef-pacific-drought-emergency-response-north-pacific-federated-states-micronesia-and-republic-marshall-islands-april-2024",
                },
            ],
        },
    },
    "FSM-YAP": {
        "2015-16": {
            "emergency": "Record low 6-month rainfall (OND 2015 + JFM 2016 = 21.70 in).",
            "rainfall": "35% of normal Jan–Mar 2016.",
            "response": "Drought 'slowly tightened its grip' from end-2015; wildfires in Yap's savannas.",
            "sources": [
                {
                    "name": "PEAC Pacific ENSO Update v22 n3 (2016)",
                    "url": "https://www.weather.gov/media/peac/PEU/PEU_v22_n3.pdf",
                },
            ],
        },
        "2023-24": {
            "emergency": "Yap Proper & Ulithi at D4 exceptional drought (2024).",
            "rainfall": "Mar–Apr 2024 2nd-driest in 73 years.",
            "response": "Outer-island catchments (Ulithi, Woleai, Fais) low/near-empty.",
            "sources": [
                {
                    "name": "NWS Guam Drought Information Statement (10 May 2024)",
                    "url": "https://www.weather.gov/media/gum/DGT/DGT_GUM_05102024.pdf",
                },
            ],
        },
    },
    "FSM-YAP-ULI": {
        "2023-24": {
            "emergency": "Ulithi reached D4 exceptional drought (2024).",
            "rainfall": "Catchment low/near-empty.",
            "response": "RO/relief prioritized for outer islands.",
            "sources": [
                {
                    "name": "NWS Guam Drought Information Statement (10 May 2024)",
                    "url": "https://www.weather.gov/media/gum/DGT/DGT_GUM_05102024.pdf",
                },
                {
                    "name": "ABC Pacific — drought in Micronesian islands (2024)",
                    "url": "https://www.abc.net.au/pacific/drought-yap-micronesian-islands/104168996",
                },
            ],
        },
    },
    # ---- Palau ----
    "PAL": {
        "2015-16": {
            "emergency": "State of Emergency (EO-389) 21/22 Mar 2016; Koror/Airai on 3-hour-per-day rationing.",
            "rainfall": "Koror ~1/3 of normal from 1 Mar 2016; lowest 4-month rainfall since 1951.",
            "response": "Ngerimel Dam dried up; Japan emergency relief (jerry cans, tanks, purifiers) 1 Apr 2016.",
            "sources": [
                {
                    "name": "NOAA Climate.gov — Drought in the Pacific (2016)",
                    "url": "https://www.climate.gov/news-features/event-tracker/drought-pacific",
                },
                {
                    "name": "Gov. of Palau — El Niño Response Plan 2016",
                    "url": "http://palaugov.pw/wp-content/uploads/2017/06/EL-NINO-Response-Plan-2016.pdf",
                },
            ],
        },
    },
    "PAL-KOR": {
        "2015-16": {
            "emergency": "Ngerimel Dam dried up; Koror & Airai rationed to 3 h/day; schools on half-days.",
            "rainfall": "Koror ~1/3 of normal from 1 Mar 2016 (lowest in 65 years).",
            "response": "Emergency water rationing schedule.",
            "sources": [
                {
                    "name": "Straits Times/AFP — Palau could dry up (4 Apr 2016)",
                    "url": "https://www.straitstimes.com/world/drought-hit-pacific-island-nation-of-palau-could-dry-up-totally-this-month-appeals-for-aid",
                },
            ],
        },
    },
}

# Regional fallback when a location has no specific entry.
REGIONAL_NOTE = {
    "summary": (
        "El Niño suppresses western-Pacific rainfall by shifting the Walker "
        "circulation's rising branch east of the date line, imposing subsidence "
        "over the FAS warm pool. Drought peaks in the dry season the year *after* "
        "a strong El Niño."
    ),
    "sources": [
        {
            "name": "COFA FORWARD — El Niño drought research synthesis",
            "url": "https://github.com/cofa-forward/cofa-forward/blob/main/docs/el-nino-drought-research.md",
        },
        {
            "name": "NOAA Climate.gov — The Walker Circulation",
            "url": "https://www.climate.gov/news-features/blogs/enso/walker-circulation-ensos-atmospheric-buddy",
        },
    ],
}
