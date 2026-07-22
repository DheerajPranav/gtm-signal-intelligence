"""Cost and latency tracking for LLM calls.

Every call goes through `CostTracker.record`, which appends one JSON object per
call to `runs.jsonl`. This is the observability floor for the whole sprint: if a
call isn't recorded here, it didn't happen.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .pricing import cost_usd

DEFAULT_LOG_PATH = Path(os.environ.get("GTM_RUNS_LOG", "runs.jsonl"))


@dataclass
class CallRecord:
    run_id: str
    operation: str
    model: str
    timestamp: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    cost_usd: float
    stop_reason: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_creation_tokens
            + self.cache_read_tokens
        )


class CostTracker:
    """Accumulates call records for one logical run and flushes them to JSONL."""

    def __init__(self, operation: str, log_path: Path | None = None) -> None:
        self.operation = operation
        self.run_id = uuid.uuid4().hex[:12]
        self.log_path = Path(log_path) if log_path else DEFAULT_LOG_PATH
        self.records: list[CallRecord] = []

    def record(
        self,
        response: Any,
        *,
        model: str,
        latency_ms: int,
        error: str | None = None,
        **metadata: Any,
    ) -> CallRecord:
        """Record one API response. `response` is an Anthropic `Message`."""
        usage = getattr(response, "usage", None)

        def u(name: str) -> int:
            return int(getattr(usage, name, 0) or 0) if usage else 0

        input_tokens = u("input_tokens")
        output_tokens = u("output_tokens")
        cache_creation = u("cache_creation_input_tokens")
        cache_read = u("cache_read_input_tokens")

        rec = CallRecord(
            run_id=self.run_id,
            operation=self.operation,
            model=model,
            timestamp=datetime.now(timezone.utc).isoformat(),
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_tokens=cache_creation,
            cache_read_tokens=cache_read,
            cost_usd=cost_usd(
                model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_creation_tokens=cache_creation,
                cache_read_tokens=cache_read,
            ),
            stop_reason=getattr(response, "stop_reason", None),
            error=error,
            metadata=metadata,
        )
        self.records.append(rec)
        return rec

    @property
    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.records)

    @property
    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self.records)

    @property
    def total_latency_ms(self) -> int:
        return sum(r.latency_ms for r in self.records)

    def flush(self) -> None:
        if not self.records:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            for rec in self.records:
                fh.write(json.dumps(asdict(rec)) + "\n")


@contextmanager
def cost_tracker(
    operation: str, log_path: Path | None = None
) -> Iterator[CostTracker]:
    """Track cost for a logical run; flush to JSONL even if the body raises."""
    tracker = CostTracker(operation, log_path)
    try:
        yield tracker
    finally:
        tracker.flush()


@contextmanager
def timed() -> Iterator[dict[str, int]]:
    """Measure wall-clock ms around a block. Result lands in `["ms"]`."""
    result: dict[str, int] = {"ms": 0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["ms"] = int((time.perf_counter() - start) * 1000)
