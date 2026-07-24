"""Persistence tests: migrations actually create tables, and domain<->row round-trips."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa
from sqlmodel import Session, select

from gtm_outbound.db import init_db
from gtm_outbound.models import (
    Department,
    EpisodicEntry,
    FactType,
    PlaybookRule,
    SemanticFact,
    Seniority,
    VariantAngle,
)
from gtm_outbound.tables import EpisodicEntryRow, PlaybookRuleRow, SemanticFactRow

NOW = datetime(2026, 7, 24, 12, 0, 0)


@pytest.fixture
def engine():
    """In-memory database, migrated fresh for each test."""
    return init_db(url="sqlite://")


def _fact(fact_id: str = "f1", **kw) -> SemanticFact:
    defaults = dict(
        fact_id=fact_id,
        account_id="acme.com",
        fact_type=FactType.FUNDING_EVENT,
        value="Series C, $40M",
        source_url="https://example.test/news",
        confidence=0.9,
        observed_at=NOW,
    )
    return SemanticFact(**{**defaults, **kw})


def _episode(episode_id: str = "e1", **kw) -> EpisodicEntry:
    defaults = dict(
        episode_id=episode_id,
        variant_id="p1__trigger",
        account_domain="acme.com",
        persona_department=Department.OPERATIONS,
        persona_seniority=Seniority.VP,
        variant_angle=VariantAngle.TRIGGER_EVENT_LED,
        email_subject="Congrats on the raise",
        email_body="Body.",
        personalization_score=4.5,
        relevance_score=4.5,
        cta_score=4.0,
        spam_risk=1.0,
        would_send=True,
        embedding_id="emb-1",
        cost_usd=0.02,
        timestamp=NOW,
        industry="fintech",
        sub_industry="payments",
        size_band="200-500",
        funding_stage="Series C",
    )
    return EpisodicEntry(**{**defaults, **kw})


def _rule(rule_id: str = "r1", **kw) -> PlaybookRule:
    defaults = dict(
        rule_id=rule_id,
        segment_key="fintech_operations_vp",
        rule_text="Trigger-event openers outperform pain-led for fintech VPs.",
        variant_angle=VariantAngle.TRIGGER_EVENT_LED,
        support_n=42,
        effect_size=0.34,
        confidence=0.71,
        created_at=NOW,
        last_verified_at=NOW,
    )
    return PlaybookRule(**{**defaults, **kw})


# ── migrations ────────────────────────────────────────────────────────────────
def test_init_db_registers_tables_without_help_from_the_caller():
    """Regression: init_db() used to run cleanly and create zero tables, because the
    models were plain BaseModel and no SQLModel table was ever registered.

    Runs in a subprocess that imports ONLY `db`. Asserting this in-process would be
    worthless: this test module imports `gtm_outbound.tables` at the top, which
    registers the tables itself and masks the very defect being tested.
    """
    import subprocess
    import sys
    import textwrap

    script = textwrap.dedent(
        """
        import sqlalchemy as sa
        from gtm_outbound.db import init_db   # deliberately NOT importing .tables
        engine = init_db(url="sqlite://")
        print(",".join(sorted(sa.inspect(engine).get_table_names())))
        """
    )
    out = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    created = set(out.stdout.strip().split(","))
    assert {"semantic_fact", "playbook_rule", "episodic_entry"} <= created


def test_init_db_creates_every_memory_table(engine):
    names = set(sa.inspect(engine).get_table_names())
    assert {"semantic_fact", "playbook_rule", "episodic_entry"} <= names


def test_consolidation_grouping_columns_are_indexed(engine):
    """The nightly job groups by this triple; unindexed it degrades as memory grows."""
    indexed = {
        i["column_names"][0] for i in sa.inspect(engine).get_indexes("episodic_entry")
    }
    assert {"industry", "persona_department", "variant_angle"} <= indexed


def test_init_db_is_idempotent(engine):
    init_db(engine=engine)  # second run must not raise
    assert "semantic_fact" in sa.inspect(engine).get_table_names()


# ── round-trips ───────────────────────────────────────────────────────────────
def test_semantic_fact_round_trips_through_storage(engine):
    with Session(engine) as s:
        s.add(SemanticFactRow.from_domain(_fact()))
        s.commit()

    with Session(engine) as s:
        row = s.exec(select(SemanticFactRow)).one()
        restored = row.to_domain()

    assert restored == _fact()
    assert restored.fact_type is FactType.FUNDING_EVENT  # enum survives the trip


def test_episodic_entry_round_trips_with_enums(engine):
    with Session(engine) as s:
        s.add(EpisodicEntryRow.from_domain(_episode()))
        s.commit()

    with Session(engine) as s:
        restored = s.exec(select(EpisodicEntryRow)).one().to_domain()

    assert restored == _episode()
    assert restored.variant_angle is VariantAngle.TRIGGER_EVENT_LED


def test_playbook_rule_round_trips(engine):
    with Session(engine) as s:
        s.add(PlaybookRuleRow.from_domain(_rule()))
        s.commit()

    with Session(engine) as s:
        restored = s.exec(select(PlaybookRuleRow)).one().to_domain()

    assert restored == _rule()
    assert restored.is_active


# ── memory semantics ──────────────────────────────────────────────────────────
def test_supersession_preserves_history_instead_of_overwriting(engine):
    """Facts are append-only: the old row stays, flagged, so history is auditable."""
    with Session(engine) as s:
        s.add(SemanticFactRow.from_domain(_fact("f1", superseded_by="f2")))
        s.add(SemanticFactRow.from_domain(_fact("f2", value="Series D, $90M")))
        s.commit()

    with Session(engine) as s:
        rows = s.exec(select(SemanticFactRow)).all()
        current = [r for r in rows if r.superseded_by is None]

    assert len(rows) == 2, "the superseded fact must not be deleted"
    assert len(current) == 1
    assert current[0].value == "Series D, $90M"


def test_stale_facts_are_queryable_by_age(engine):
    """Backs the >60-day staleness flag the v2 eval requires."""
    with Session(engine) as s:
        s.add(SemanticFactRow.from_domain(_fact("fresh", observed_at=NOW - timedelta(days=5))))
        s.add(SemanticFactRow.from_domain(_fact("stale", observed_at=NOW - timedelta(days=90))))
        s.commit()

    cutoff = NOW - timedelta(days=60)
    with Session(engine) as s:
        stale = s.exec(
            select(SemanticFactRow).where(SemanticFactRow.observed_at < cutoff)
        ).all()

    assert [r.fact_id for r in stale] == ["stale"]
    assert stale[0].to_domain().age_days(now=NOW) > 60


def test_consolidation_can_aggregate_episodes_by_segment(engine):
    """The query shape the nightly job depends on: GROUP BY segment, count, mean."""
    with Session(engine) as s:
        for i in range(3):
            s.add(EpisodicEntryRow.from_domain(_episode(f"e{i}", personalization_score=4.0 + i * 0.5)))
        s.add(
            EpisodicEntryRow.from_domain(
                _episode("other", variant_angle=VariantAngle.PAIN_LED, personalization_score=2.0)
            )
        )
        s.commit()

    with Session(engine) as s:
        rows = s.exec(
            select(
                EpisodicEntryRow.variant_angle,
                sa.func.count().label("n"),
                sa.func.avg(EpisodicEntryRow.personalization_score).label("mean_pers"),
            ).group_by(EpisodicEntryRow.variant_angle)
        ).all()

    stats = {r[0]: (r[1], r[2]) for r in rows}
    assert stats[VariantAngle.TRIGGER_EVENT_LED][0] == 3
    assert stats[VariantAngle.TRIGGER_EVENT_LED][1] == pytest.approx(4.5)
    assert stats[VariantAngle.PAIN_LED][0] == 1


def test_retired_rules_are_excluded_from_active_lookups(engine):
    with Session(engine) as s:
        s.add(PlaybookRuleRow.from_domain(_rule("active")))
        s.add(PlaybookRuleRow.from_domain(_rule("dead", retired_at=NOW)))
        s.commit()

    with Session(engine) as s:
        active = s.exec(
            select(PlaybookRuleRow).where(PlaybookRuleRow.retired_at.is_(None))
        ).all()

    assert [r.rule_id for r in active] == ["active"]
