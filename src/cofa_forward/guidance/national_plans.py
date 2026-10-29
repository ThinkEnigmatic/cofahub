"""National drought plans, emergency declarations, and response guidance.

A structured, provenance-carrying catalog of the Freely Associated States'
government drought-planning documents. Each entry records its source URL,
extraction method, and verification status so the app can cite these as guidance
without fabricating any of it.

Key analytical linkage: RMI's plan zones atolls by latitude into vulnerability
bands (Zone 1 >8°N / Zone 2 6–8°N / Zone 3 <6°N), which matches the app's
independent finding that northern RMI atolls are the most drought-exposed.
Palau's plan is stage-based (Stage 1 = water-shortage watch); FSM's plan is
three-pillar (early warning / vulnerability assessment / mitigation-response).

All facts below were extracted from the cited public documents on 2026-10-29.
"""

from __future__ import annotations

NATIONAL_PLANS: list[dict] = [
    {
        "doc_id": "rmi-immediate-drought-response-2016",
        "title": "Immediate Drought Response Plan for the Republic of the Marshall Islands",
        "country": "Marshall Islands",
        "country_code": "MH",
        "geo_id": "RMI",
        "doc_type": "response_plan",
        "publisher": (
            "Government of the Marshall Islands (NDMO / National Emergency Operations Centre)"
        ),
        "date": "2016-02-01",
        "url": (
            "https://reliefweb.int/report/marshall-islands/"
            "immediate-drought-response-plan-republic-marshall-islands"
        ),
        "file_url": (
            "https://reliefweb.int/attachments/5bfd505c-6e28-3d70-9f2b-b80cb105ba7f/"
            "RMI_DR_2016_Response_Plan_Feb5.pdf"
        ),
        "summary": (
            "Complementing the Declaration on State of Emergency (3 Feb 2016) for the "
            "2015–16 El Niño drought. Covers a 6-month WASH-focused response across "
            "19 atolls/islands, 44 communities, ~1,257 households plus 4,092 in Majuro."
        ),
        "key_facts": [
            "State of Emergency declared 3 February 2016.",
            (
                "Vulnerability zoning: Zone 1 (>8°N) high, Zone 2 (6°–8°N) high, "
                "Zone 3 (<6°N) moderate (Mili Atoll raised to Zone 2)."
            ),
            (
                "Northern atolls (Zone 1/2) are the government-designated "
                "highest-vulnerability area — matches the app's northern-atoll finding."
            ),
            "El Niño rainfall pattern: above-average early year, dry from Nov–Dec, "
            "returning ~July.",
            (
                "Response: drinking-water distribution points, reverse-osmosis units, "
                "safe-water education."
            ),
        ],
        "extraction_method": "PDF text extraction (pdftotext) from the ReliefWeb attachment",
        "verification_status": "verified",
        "extraction_date": "2026-10-29",
    },
    {
        "doc_id": "rmi-rpdi-2024",
        "title": "RMI Response Plan for Drought and Inundation (RPDI) 2024",
        "country": "Marshall Islands",
        "country_code": "MH",
        "geo_id": "RMI",
        "doc_type": "response_plan",
        "publisher": "Government of the Marshall Islands",
        "date": "2024",
        "url": (
            "https://reliefweb.int/report/micronesia-federated-states/"
            "micronesia-drought-response-situation-report-08-april-2024"
        ),
        "summary": (
            "The 2024 drought + inundation response plan. In early 2024, 18 atolls were "
            "impacted by inundation and drought affected ~15,000 people (~35%) across "
            "23 atolls/islands; NDMO deployed RO units to 9 of 16 affected atolls."
        ),
        "key_facts": [
            "NDMO deployed Reverse-Osmosis units to 9 of 16 drought-affected atolls (2024).",
            "~5,200 people (12.3% of population) affected across 15 atolls/islands.",
            "Three schools without RO units were forced to close.",
            "18 atolls impacted by inundation on 20 Jan and 9–10 Mar 2024.",
        ],
        "extraction_method": "UNICEF + IOM situation reports (ReliefWeb)",
        "verification_status": "verified",
        "extraction_date": "2026-10-29",
    },
    {
        "doc_id": "fsm-ndprp-2026",
        "title": "FSM National Drought Preparedness and Response Plan (NDPRP)",
        "country": "Federated States of Micronesia",
        "country_code": "FM",
        "geo_id": "FSM",
        "doc_type": "national_plan",
        "publisher": (
            "FSM Department of Environment, Climate Change and Emergency Management (DECEM); "
            "IOM; Japan"
        ),
        "date": "2026-08-22",
        "url": "https://kpress.fm/fsm-national-drought-plan-water-security",
        "summary": (
            "FSM's first comprehensive national drought framework, endorsed 22 Aug 2026. "
            "Three pillars: (1) early warning systems, (2) vulnerability & impact "
            "assessment, (3) mitigation, preparedness & response. Coordinates national, "
            "state, municipal and community actors."
        ),
        "key_facts": [
            "Endorsed 22 August 2026 (the current national framework).",
            (
                "Three pillars: early warning; vulnerability/impact assessment; "
                "mitigation–preparedness–response."
            ),
            "Historical drought events: 1983, 1998, 2015–16, and 2023–24 El Niño.",
            (
                "National emergency declared 12 March 2024 (President Simina) for "
                "Pohnpei/Yap/Chuuk; $1.2M; 21,000+ in urgent need."
            ),
        ],
        "extraction_method": "Kaselehlie Press report + UNICEF North Pacific response (Apr 2024)",
        "verification_status": "verified",
        "extraction_date": "2026-10-29",
    },
    {
        "doc_id": "palau-drought-action-plan",
        "title": "Palau National Drought Action Plan",
        "country": "Palau",
        "country_code": "PW",
        "geo_id": "PAL",
        "doc_type": "national_plan",
        "publisher": (
            "Palau National Emergency Committee (NEC) / National Emergency Management Office (NEMO)"
        ),
        "date": None,
        "url": "https://islandtimes.org/palau-nec-activates-stage-1-of-nations-drought-action-plan-water-shortage-watch",
        "summary": (
            "Palau's stage-based drought action plan. The National Emergency Committee "
            "activates stages; NEMO issues public advisories. Stage 1 is the water-shortage "
            "watch (entered 26 March 2024 during the 2023–24 El Niño)."
        ),
        "key_facts": [
            "Stage 1 = water-shortage watch; activated 26 March 2024.",
            (
                "NEC activates stages based on National Weather Service monitoring; "
                "NEMO issues advisories."
            ),
            (
                "Stage definitions are stage-based (watch → warning → emergency) rather "
                "than rainfall-percentile based."
            ),
        ],
        "extraction_method": "NEMO public advisories + Island Times reporting",
        "verification_status": "verified",
        "extraction_date": "2026-10-29",
    },
    {
        "doc_id": "unicef-north-pacific-2024",
        "title": "Drought Emergency Response for the North Pacific (FSM and RMI)",
        "country": "Federated States of Micronesia & Marshall Islands",
        "country_code": "FM+MH",
        "geo_id": None,
        "doc_type": "humanitarian_response",
        "publisher": "UNICEF Pacific",
        "date": "2024-04",
        "url": (
            "https://www.unicef.org/media/155256/file/"
            "Drought-Emergency-Response-for-the-North-Pacific(FSM-and-RMI),April%202024.pdf"
        ),
        "summary": (
            "UNICEF's response to the 2023–24 El Niño drought in FSM and RMI: WASH kits, "
            "RO support, health/nutrition, education continuity, and child protection."
        ),
        "key_facts": [
            (
                "FSM: >21,000 in urgent need; saltwater intrusion in Lekinioch/Piherarh/"
                "Onoun (Chuuk lagoon)."
            ),
            (
                "RMI: >5,200 people (12.3%) affected across 15 atolls/islands; little/no "
                "rain for 2–3 months."
            ),
            "4,307 WASH kits planned; 12 collapsible water tanks; water filters + school WASH.",
        ],
        "extraction_method": "PDF text extraction (pdftotext) from the UNICEF attachment",
        "verification_status": "verified",
        "extraction_date": "2026-10-29",
    },
]


def fas_plans(country_code: str | None = None) -> list[dict]:
    """Return the FAS national plans/declarations, optionally filtered by country."""
    out = [p for p in NATIONAL_PLANS if p["geo_id"] is not None]
    if country_code:
        out = [p for p in out if p["country_code"] == country_code]
    return out
