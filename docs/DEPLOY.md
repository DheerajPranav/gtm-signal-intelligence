# Deployment guide

Status of the three deployable surfaces, and how to ship each. **Honest note:** the
portfolio is live; the flagship backend and dashboard configs below are ready-to-run
templates that need *your* accounts and a live LLM key — they have **not** been executed,
so no live backend URL is claimed.

| Surface | Target | Status |
|---|---|---|
| Portfolio site | GitHub Pages | ✅ **live** — https://dheerajpranav.github.io/gtm-signal-intelligence/ |
| Flagship backend | Modal | 🧩 config ready (`gtm-outbound-agent/deploy/modal_app.py`) — needs Modal account + keys |
| Dashboard | Streamlit Community Cloud | 🧩 steps below — needs Streamlit account + keys |
| Database | Neon (Postgres) | 🧩 connection string wired via `DATABASE_URL` |

---

## 0. Environment variables

The flagship reads these (only the first two are required for a live run):

| Var | Required | Used by |
|---|---|---|
| `GROQ_API_KEY` | ✅ primary LLM | `llm_provider.py` |
| `ANTHROPIC_API_KEY` | ✅ fallback LLM | `llm_provider.py` |
| `DATABASE_URL` | for Postgres (else SQLite) | `db.py` |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` | optional tracing | `observability.py` |

Keep keys in the platform's secret store (Modal Secret / Streamlit secrets / Neon dashboard) —
never in the repo. Budget guard from the sprint plan: stay under ~$50 total; prefer Groq/Haiku.

## 1. Database — Neon (Postgres)

1. Create a free project at neon.tech → copy the pooled connection string.
2. It looks like `postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname?sslmode=require`.
3. Set it as `DATABASE_URL` in your Modal Secret (and Streamlit secrets). With it unset the
   app falls back to local SQLite — fine for dev, not for a shared deploy.
4. Tables are created by the app's `db.py` on first use (SQLModel metadata).

## 2. Backend — Modal

Config: [`gtm-outbound-agent/deploy/modal_app.py`](../gtm-outbound-agent/deploy/modal_app.py).

```bash
pip install modal
modal token new                                   # auth to your account
modal secret create gtm-outbound \
    GROQ_API_KEY=... ANTHROPIC_API_KEY=... \
    DATABASE_URL=postgresql://...neon.tech/db

# one-off run:
modal run gtm-outbound-agent/deploy/modal_app.py --domains "stripe.com,ramp.com"

# persistent HTTP endpoint:
modal deploy gtm-outbound-agent/deploy/modal_app.py
# -> POST {"domains": ["stripe.com"]} to the printed *.modal.run URL
```

What it does: builds an image with the runtime deps, mounts `src/`, attaches the secret,
runs `batch.main_run` (which self-constructs the Groq/Anthropic providers and the async
company pipelines), and persists generated Account Briefs to a Modal Volume (`gtm-runs`).

## 3. Dashboard — Streamlit Community Cloud

The dashboard is `gtm-outbound-agent/dashboard.py` (run history, live progress, cost trends).

1. Push to GitHub (done).
2. share.streamlit.io → **New app** → repo `DheerajPranav/gtm-signal-intelligence`.
3. **Main file path:** `gtm-outbound-agent/dashboard.py`.
4. **Advanced → Secrets:** paste the same env vars (TOML form):
   ```toml
   GROQ_API_KEY = "..."
   ANTHROPIC_API_KEY = "..."
   DATABASE_URL = "postgresql://...neon.tech/db"
   ```
5. Deploy. Point it at the same `DATABASE_URL` as the Modal backend so it reads live runs.

> The dashboard reads from the database/volume the backend writes to. For a fully shared
> setup, both must use the same Neon `DATABASE_URL`; the Modal Volume is backend-local.

## 4. Verify after deploying

```bash
# backend (once the endpoint is deployed):
curl -X POST https://<your-app>.modal.run -H 'content-type: application/json' \
     -d '{"domains":["stripe.com"]}'
# -> {"run_id": "...", "output": "/data/runs/..."}
```

Then open the Streamlit dashboard and confirm the run appears. Only after a real run
returns non-`not measured` metrics should any live quality number be quoted anywhere —
per the project's honesty rule.
