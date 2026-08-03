"""Modal deployment for the GTM Outbound Agent backend.

This is a ready-to-run TEMPLATE — it is not yet deployed. Deploying needs your own
Modal account and a live LLM key; nothing here has been run against Modal.

Prereqs
-------
    pip install modal
    modal token new                      # one-time auth to your Modal account
    # Store keys as a Modal Secret named "gtm-outbound" (dashboard or CLI):
    modal secret create gtm-outbound \
        GROQ_API_KEY=... \
        ANTHROPIC_API_KEY=... \
        DATABASE_URL=postgresql://...neon.tech/db   # Neon Postgres (see docs/DEPLOY.md)
        # optional: LANGFUSE_PUBLIC_KEY=... LANGFUSE_SECRET_KEY=... TAVILY_API_KEY=...

Run once (ephemeral):
    modal run deploy/modal_app.py --domains "stripe.com,ramp.com"

Deploy the web endpoint (persistent):
    modal deploy deploy/modal_app.py
    # -> POST {"domains": ["stripe.com"]} to the printed URL

Written against the Modal 1.x API. Providers (Groq/Anthropic + tools) are constructed
inside `batch.main_run`, so this wrapper only needs to install deps, mount the package,
attach secrets, and persist `runs/` to a Volume.
"""

from __future__ import annotations

import modal

app = modal.App("gtm-outbound-agent")

# Install the same runtime deps declared in pyproject, then mount the source tree.
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "groq>=0.4.0",
        "anthropic>=0.28",
        "pydantic>=2.0",
        "sqlmodel>=0.0.14",
        "psycopg[binary]>=3.1",
        "chromadb>=0.5",
        "langfuse>=2.0",
        "fastapi[standard]",
    )
    # Mount the package source at /root/src (kept out of the image layers so code
    # changes don't rebuild deps).
    .add_local_dir("src", remote_path="/root/src")
)

# Keys live in a Modal Secret, never in this file.
secret = modal.Secret.from_name("gtm-outbound")

# Persist generated Account Briefs across runs.
runs_volume = modal.Volume.from_name("gtm-runs", create_if_missing=True)

RUNS_DIR = "/data/runs"


@app.function(
    image=image,
    secrets=[secret],
    volumes={"/data": runs_volume},
    timeout=1800,  # 30 min — batch of async company pipelines
)
async def run_batch(domains: list[str]) -> dict:
    """Run the full outbound pipeline for each domain; persist briefs to the Volume."""
    import sys
    from pathlib import Path

    sys.path.insert(0, "/root/src")
    from gtm_outbound.batch import main_run

    run_id = await main_run(domains=domains, output_dir=Path(RUNS_DIR))
    runs_volume.commit()  # flush new files so they survive the container
    return {"run_id": run_id, "domains": domains, "output": f"{RUNS_DIR}/{run_id}"}


@app.function(image=image, secrets=[secret], volumes={"/data": runs_volume})
@modal.fastapi_endpoint(method="POST")
async def api(payload: dict) -> dict:
    """HTTP entry point. Body: {"domains": ["stripe.com", ...]}."""
    domains = payload.get("domains") or []
    if not domains:
        return {"error": "provide a non-empty 'domains' list"}
    # Fan the batch out to the worker function above.
    return await run_batch.remote.aio(domains)


@app.local_entrypoint()
def main(domains: str = "stripe.com"):
    """`modal run deploy/modal_app.py --domains "a.com,b.com"`."""
    result = run_batch.remote([d.strip() for d in domains.split(",") if d.strip()])
    print(result)
