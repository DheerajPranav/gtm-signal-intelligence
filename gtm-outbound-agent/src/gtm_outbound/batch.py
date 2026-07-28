"""Batch runner: process multiple companies concurrently with failure isolation + resume.

Usage:
    python -m gtm_outbound.batch run --input companies.csv --output runs/
    python -m gtm_outbound.batch resume --run-id abc123 --output runs/
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine

from .db import init_db
from .pipeline import run_company


logger = logging.getLogger(__name__)


@dataclass
class BatchRun:
    """A batch of companies to process."""
    run_id: str
    created_at: str  # ISO format
    status: str  # "running", "completed", "paused", "failed"
    total_companies: int
    completed: int = 0
    failed: int = 0
    elapsed_seconds: float = 0.0
    total_cost: float = 0.0


@dataclass
class CompanyRun:
    """Result of processing a single company."""
    run_id: str
    domain: str
    status: str  # "pending", "running", "completed", "failed", "skipped"
    brief_path: Optional[str] = None
    error: Optional[str] = None
    elapsed_seconds: float = 0.0
    cost_usd: float = 0.0


class BatchRunner:
    """Orchestrates concurrent company processing with failure isolation."""

    def __init__(self, db_path: Path = Path("gtm_outbound.db"), max_concurrent: int = 3):
        self.db_path = db_path
        self.max_concurrent = max_concurrent
        self.engine = create_engine(f"sqlite:///{db_path}")
        # Ensure tables exist
        init_db(url=f"sqlite:///{db_path}")

    def create_batch(self, domains: list[str]) -> str:
        """Create a new batch run."""
        run_id = str(uuid.uuid4())[:8]
        batch = BatchRun(
            run_id=run_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="pending",
            total_companies=len(domains),
        )

        # Store batch metadata in a simple JSON file
        batch_file = Path("runs") / f"batch_{run_id}.json"
        batch_file.parent.mkdir(exist_ok=True)
        batch_file.write_text(json.dumps(asdict(batch), indent=2))

        # Store company list
        companies_file = batch_file.parent / f"batch_{run_id}_companies.jsonl"
        for domain in domains:
            company_run = CompanyRun(run_id=run_id, domain=domain, status="pending")
            with companies_file.open("a") as f:
                f.write(json.dumps(asdict(company_run)) + "\n")

        logger.info(f"Created batch {run_id} with {len(domains)} companies")
        return run_id

    async def run_batch(self, run_id: str, output_dir: Path = Path("runs")) -> BatchRun:
        """Run all companies in a batch concurrently (with semaphore limit)."""
        output_dir.mkdir(exist_ok=True)

        # Load batch metadata
        batch_file = Path("runs") / f"batch_{run_id}.json"
        batch_data = json.loads(batch_file.read_text())
        batch = BatchRun(**batch_data)
        batch.status = "running"

        # Load company list
        companies_file = batch_file.parent / f"batch_{run_id}_companies.jsonl"
        companies = [
            CompanyRun(**json.loads(line))
            for line in companies_file.read_text().strip().split("\n")
        ]

        # Filter out already-completed companies (for resume)
        pending = [c for c in companies if c.status == "pending"]
        logger.info(f"Processing {len(pending)} pending companies (skipping {len(companies) - len(pending)} completed)")

        # Run with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def run_single(company: CompanyRun) -> CompanyRun:
            async with semaphore:
                return await self._run_company_safe(company, output_dir, run_id)

        t0 = time.perf_counter()
        results = await asyncio.gather(*[run_single(c) for c in pending])
        elapsed = time.perf_counter() - t0

        # Update batch metadata
        batch.completed = sum(1 for r in results if r.status == "completed")
        batch.failed = sum(1 for r in results if r.status == "failed")
        batch.elapsed_seconds = elapsed
        batch.total_cost = sum(r.cost_usd for r in results)
        batch.status = "completed" if batch.failed == 0 else "partial"

        # Persist updated metadata
        batch_file.write_text(json.dumps(asdict(batch), indent=2))

        # Persist company results
        with companies_file.open("w") as f:
            for company in companies:
                # Merge results for this company
                result = next((r for r in results if r.domain == company.domain), company)
                f.write(json.dumps(asdict(result)) + "\n")

        logger.info(
            f"Batch {run_id} complete: {batch.completed}/{batch.total_companies} succeeded, "
            f"{batch.failed} failed in {elapsed:.1f}s (${batch.total_cost:.2f})"
        )

        return batch

    async def _run_company_safe(
        self, company: CompanyRun, output_dir: Path, run_id: str
    ) -> CompanyRun:
        """Run a single company with error isolation."""
        company.status = "running"
        t0 = time.perf_counter()

        try:
            logger.info(f"[{run_id}] Processing {company.domain}...")

            # Call the flagship pipeline
            brief_md = await run_company(company.domain)

            # Save the brief
            brief_path = output_dir / run_id / f"{company.domain}.md"
            brief_path.parent.mkdir(parents=True, exist_ok=True)
            brief_path.write_text(brief_md)

            company.brief_path = str(brief_path)
            company.status = "completed"
            logger.info(f"[{run_id}] ✓ {company.domain}")

        except Exception as e:
            # Capture error and continue
            company.error = f"{type(e).__name__}: {str(e)}"
            company.status = "failed"
            logger.error(f"[{run_id}] ✗ {company.domain}: {company.error}")

        finally:
            company.elapsed_seconds = time.perf_counter() - t0

        return company

    def load_batch(self, run_id: str) -> Optional[BatchRun]:
        """Load batch metadata from disk."""
        batch_file = Path("runs") / f"batch_{run_id}.json"
        if not batch_file.exists():
            return None
        return BatchRun(**json.loads(batch_file.read_text()))

    def list_batches(self) -> list[BatchRun]:
        """List all batch runs."""
        batches = []
        runs_dir = Path("runs")
        if not runs_dir.exists():
            return batches

        for batch_file in runs_dir.glob("batch_*.json"):
            try:
                batch = BatchRun(**json.loads(batch_file.read_text()))
                batches.append(batch)
            except Exception as e:
                logger.warning(f"Failed to load {batch_file}: {e}")

        return sorted(batches, key=lambda b: b.created_at, reverse=True)


async def main_run(
    input_csv: Optional[Path] = None,
    domains: Optional[list[str]] = None,
    output_dir: Path = Path("runs"),
):
    """Main entry point for `run_batch`."""
    if input_csv:
        domains = []
        with input_csv.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "domain" in row:
                    domains.append(row["domain"])
                elif "company" in row:
                    domains.append(row["company"])

    if not domains:
        raise ValueError("No domains provided via CSV or CLI")

    runner = BatchRunner()
    run_id = runner.create_batch(domains)
    batch = await runner.run_batch(run_id, output_dir)

    print(f"\n📊 Batch run {run_id} complete!")
    print(f"   Completed: {batch.completed}/{batch.total_companies}")
    print(f"   Failed: {batch.failed}")
    print(f"   Time: {batch.elapsed_seconds:.1f}s")
    print(f"   Cost: ${batch.total_cost:.2f}")
    print(f"   Output: {output_dir / run_id}/")

    return run_id


async def main_resume(run_id: str, output_dir: Path = Path("runs")):
    """Main entry point for `resume_batch`."""
    runner = BatchRunner()
    batch = runner.load_batch(run_id)

    if not batch:
        raise ValueError(f"Batch {run_id} not found")

    print(f"Resuming batch {run_id} ({batch.total_companies} companies)...")
    batch = await runner.run_batch(run_id, output_dir)

    print(f"\n📊 Batch run {run_id} complete!")
    print(f"   Completed: {batch.completed}/{batch.total_companies}")
    print(f"   Failed: {batch.failed}")
    print(f"   Time: {batch.elapsed_seconds:.1f}s")
    print(f"   Cost: ${batch.total_cost:.2f}")


async def main_list():
    """Main entry point for `list` command."""
    runner = BatchRunner()
    batches = runner.list_batches()

    if not batches:
        print("No batch runs found.")
        return

    print("\n📊 Recent batch runs:\n")
    for batch in batches[:10]:  # Show last 10
        status_icon = "✓" if batch.status == "completed" else "⏸" if batch.status == "paused" else "✗"
        print(f"{status_icon} {batch.run_id} | {batch.completed}/{batch.total_companies} | ${batch.total_cost:.2f} | {batch.created_at}")
