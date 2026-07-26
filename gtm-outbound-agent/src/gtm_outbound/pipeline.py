"""End-to-end pipeline: a domain in, a complete Account Brief out.

`run_company` chains all five agents — research → score → personas → write → critique —
then assembles and writes an `AccountBrief.md`. The sync agents (research/score/persona/
critique) run inline; writing fans out async; the 9 critiques run concurrently via
`asyncio.to_thread` so the sync critique client isn't a serial bottleneck.

Latency is real wall-clock. Cost is passed through (default 0.0): per-call token accounting
is not wired yet — it lands with the observability work — so the brief reports 0 rather than
a fabricated figure, and that limitation is stated in the docs.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .agents.critique_agent import critique
from .agents.persona_agent import build_personas
from .agents.research_agent import enrich
from .agents.scoring_agent import score
from .agents.writing_agent import draft_all
from .brief import assemble_brief, render_brief_md
from .models import AccountBrief
from .tools.web import ToolProvider


async def run_company(
    domain: str,
    tool_provider: ToolProvider,
    *,
    icp_provider: Any = None,
    positioning_provider: Any = None,
    peer_provider: Any = None,
    sync_client: Any = None,
    async_client: Any = None,
    name: Optional[str] = None,
    runs_dir: Optional[Path] = None,
    cost_usd: float = 0.0,
) -> tuple[AccountBrief, Path]:
    """Run the full pipeline for one domain and write `runs/<domain>.md`.

    Returns the assembled `AccountBrief` and the path it was written to.
    """
    started = time.perf_counter()

    # 1. Research (sync tool-use loop)
    profile, _trace = enrich(domain, tool_provider, client=sync_client, name=name)

    # 2. ICP fit (sync)
    fit = score(profile, icp_provider=icp_provider, client=sync_client)

    # 3. Personas (sync)
    personas = build_personas(profile, positioning_provider=positioning_provider,
                              client=sync_client)

    # 4. Writing (async fan-out)
    drafts = await draft_all(profile, personas, peer_provider=peer_provider,
                             client=async_client)

    # 5. Critique — 9 sync critiques run concurrently off the event loop
    persona_by_id = {p.id: p for p in personas}

    async def _critique(draft):
        ev, _decision = await asyncio.to_thread(
            critique, draft, persona_by_id[draft.persona_id], profile, sync_client
        )
        return draft.variant_id, ev

    evals = dict(await asyncio.gather(*[_critique(d) for d in drafts]))

    latency_ms = (time.perf_counter() - started) * 1000
    brief = assemble_brief(
        profile, fit, personas, drafts, evals,
        cost_usd=cost_usd, latency_ms=latency_ms,
        timestamp=datetime.now(timezone.utc),
    )

    runs_dir = runs_dir or Path("runs")
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{domain.replace('/', '_')}.md"
    path.write_text(render_brief_md(brief), encoding="utf-8")

    return brief, path
