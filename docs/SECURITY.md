# Security

The initial release is a **local, single-user** application. Sensible defaults
are in place and documented so a remote deployment is not accidentally exposed.

## In place

* Binds to `127.0.0.1` by default (never public).
* No credentials required to launch; `data/`, `data/cache/`, `.env`, and secrets
  are git-ignored.
* Secrets are read only from environment variables / `~/.config`-style files, and
  are **never** written to logs, reports, or the UI.
* External data is validated before processing (normalization + pydantic schemas);
  network fetches use timeouts and bounded retries with backoff.
* No arbitrary shell execution from UI controls.
* Retrieved documents and any future LLM output are treated as **untrusted data**:
  they can never override system behavior, execute code, or trigger tools.
* Errors are logged without secrets.
* Source data (`raw`) is kept separate from derived data (`processed`).

## Deployment (2026-10-28)

Deployed at **https://cofaforward.benigmatic.com** via a Cloudflare Tunnel:

* **App service** — `com.ben.cofaforward-dashboard` runs Streamlit bound to
  `127.0.0.1:8501` (never a public bind).
* **Tunnel** — `cofaforward.benigmatic.com` → `http://127.0.0.1:8501` on the
  existing `benigmatic.yml` tunnel (`com.ben.benigmatic-tunnel`). DNS CNAME is
  auto-managed by Cloudflare.
* **TLS** — terminated by Cloudflare (HTTPS).
* **Secrets** — the Earthdata token lives at `~/.config/cofa-forward/earthdata_token`
  (0600) and is read only via `EARTHDATA_TOKEN`; it is **not** in the app image or
  the repository.

### ⚠️ Not yet authenticated

The app is currently **public** (no Cloudflare Access). It is read-only weather
data with no admin actions or credentials exposed, but to restrict it to the
operator, apply a **Cloudflare Access** policy for `cofaforward.benigmatic.com`
(allowed identity: `bhemingway@gmail.com`), mirroring `ben.benigmatic.com`.
This requires a valid Cloudflare API token with Access:Edit + Zone:Edit (the one
at `~/.config/benigmatic/cloudflare_api_token` was invalid/expired at last check).

### Manage

```bash
launchctl kickstart -k gui/$(id -u)/com.ben.cofaforward-dashboard   # restart app
launchctl kickstart -k gui/$(id -u)/com.ben.benigmatic-tunnel        # reload tunnel (after config edits)
tail -f ~/cofa-forward/logs/streamlit.log                            # app logs
```

## If deployed remotely (not yet supported)

Before any remote deployment, additional work is required: authentication and
authorization, TLS termination, access logging, rate limiting, secrets
management, a data-protection review (population/exposure data), and a formal
review of each data source's license for redistribution.
