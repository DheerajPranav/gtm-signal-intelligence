"""Tests for pricing and the cost tracker. No API calls."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

import pytest

from gtm_cli_warmup.cost import cost_tracker
from gtm_cli_warmup.pricing import cost_usd, rates_for


@dataclass
class FakeUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class FakeResponse:
    usage: FakeUsage
    stop_reason: str = "tool_use"


def test_intro_rates_apply_before_expiry():
    assert rates_for("claude-sonnet-5", on=date(2026, 7, 20)).input == 2.00


def test_standard_rates_apply_after_expiry():
    assert rates_for("claude-sonnet-5", on=date(2026, 9, 1)).input == 3.00


def test_unknown_model_raises_rather_than_reporting_zero():
    with pytest.raises(KeyError):
        cost_usd("claude-imaginary-9", 100, 100)


def test_cost_includes_cache_tokens():
    # 1M in, 1M out, 1M cache-write, 1M cache-read at standard Sonnet rates.
    cost = cost_usd(
        "claude-sonnet-5",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_creation_tokens=1_000_000,
        cache_read_tokens=1_000_000,
        on=date(2026, 9, 1),
    )
    assert cost == pytest.approx(3.00 + 15.00 + 3.75 + 0.30)


def test_tracker_writes_one_jsonl_line_per_call(tmp_path):
    log = tmp_path / "runs.jsonl"
    response = FakeResponse(FakeUsage(input_tokens=500, output_tokens=120))

    with cost_tracker("describe", log_path=log) as tracker:
        tracker.record(response, model="claude-sonnet-5", latency_ms=900, company="Notion")
        tracker.record(response, model="claude-sonnet-5", latency_ms=850, company="Linear")
        assert tracker.total_tokens == 1240

    lines = log.read_text().strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["operation"] == "describe"
    assert first["metadata"]["company"] == "Notion"
    assert first["cost_usd"] > 0


def test_tracker_flushes_even_when_body_raises(tmp_path):
    log = tmp_path / "runs.jsonl"
    response = FakeResponse(FakeUsage(input_tokens=10, output_tokens=10))

    with pytest.raises(ValueError):
        with cost_tracker("describe", log_path=log) as tracker:
            tracker.record(response, model="claude-sonnet-5", latency_ms=100)
            raise ValueError("boom")

    # The call was billed, so it must be logged even though the run failed.
    assert len(log.read_text().strip().splitlines()) == 1
