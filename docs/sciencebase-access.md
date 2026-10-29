# ScienceBase external access — how to unlock the auth-gated files

The USGS western-Pacific release (DOI 10.5066/P1RXUMV3) has three components. The
R-code, metadata, site-selection, and GFS-forecast files are on the *public*
`catalog/file/get` endpoint and are already downloaded into `data/raw/usgs_drought/`.
But the **SSEBop actual-ET / water-balance spreadsheets** (`evapotranspiration_
SSEBop_2012_2025.xlsx`, `water balance.xlsx`, `precipitation_IMERG_*.xlsx`) and the
**drought-monitor charts** (195 MB) are stored on the newer S3-backed "manager"
storage, which requires a ScienceBase login. The S3 bucket
(`prod-is-usgs-sb-prod-content`) is not public (403), and the `catalog/file/get`
URL 404s for these objects.

## Why this needs a human

ScienceBase external access is a two-gate federal process:

1. **Login.gov account** (`https://secure.login.gov/`) — federal SSO. This must be
   *your* identity; it cannot be created on your behalf (may require identity
   proofing, and it is your personal federal credential).
2. **USGS sponsor approval** — the registration form at
   `https://sciencebase.gov/directory/signUp` requires a *USGS Sponsor Email
   Address*; a USGS employee must approve the request before access is granted.

## The two steps (for the owner)

1. Create a **login.gov** account using the household email
   (`hemingwayglobal77@gmail.com`) or `bhemingway@gmail.com`.
2. Fill the ScienceBase registration form with:
   - Email (the login.gov email),
   - First/Last name,
   - **USGS Sponsor Email** — the natural sponsor is the dataset's own contact.
     The release metadata lists the authors at USGS EROS: Gabriel Senay, Stefanie
     Kagone, Francis Dwomoh, Matthew E Andersen; the general data contact is
     `custserv@usgs.gov`. Request sponsorship from the data author (they published
     the data and are the appropriate vouching party).

## Draft sponsor-outreach email

> Subject: Request for ScienceBase sponsor approval — USGS western-Pacific
> drought release (DOI 10.5066/P1RXUMV3)
>
> Dear Dr. Andersen / USGS EROS data team,
>
> I am building a drought early-warning dashboard for the Freely Associated
> States (Palau, FSM, RMI). I have been able to download the public files of
> your release "Hydro-climatic datasets … western Pacific Island nations"
> (10.5066/P1RXUMV3), but the SSEBop actual-ET / water-budget spreadsheets and
> the drought-monitor charts are on the S3-backed ScienceBase "manager" storage,
> which requires sponsor-approved login.gov access.
>
> Would you be willing to sponsor my ScienceBase registration so I can download
> the evapotranspiration and water-balance spreadsheets? My login.gov account is
> registered to <EMAIL>.
>
> Thank you, Ben Hemingway

## What happens after approval

Once the account is sponsor-approved and signed in, the auth-gated files can be
downloaded through the browser session (the existing `scripts/cdp_download.mjs`
real-Chrome path), then:
* `evapotranspiration_SSEBop_2012_2025.xlsx` → actual ET through 2025 (replaces
  the FEWS NET portal, which ends Jun 2021).
* `water balance.xlsx` → the authoritative P−ET balance.
* `Drought_Monitor_Charts.zip` → the official monthly drought-monitor outputs.
