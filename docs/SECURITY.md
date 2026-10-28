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

## If deployed remotely (not yet supported)

Before any remote deployment, additional work is required: authentication and
authorization, TLS termination, access logging, rate limiting, secrets
management, a data-protection review (population/exposure data), and a formal
review of each data source's license for redistribution.
