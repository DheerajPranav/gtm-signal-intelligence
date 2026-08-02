"""Tests for the standalone mini-eval runner and its rubric helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gtm_agent_evals.cli import (
    RUBRICS,
    _score_email,
    _score_icp,
    _score_persona,
    main,
    run,
)
from gtm_agent_evals.rubrics import EmailRubric, ICPRubric

DATA = Path(__file__).resolve().parent.parent / "examples" / "data"


# --- rubric helpers added for the runner -----------------------------------

class TestEmailWouldSend:
    def test_all_gates_met_sends(self):
        r = EmailRubric.evaluate_would_send(
            {"personalization": 4, "relevance": 4, "cta": 3.5, "spam_risk": 1}
        )
        assert r["would_send"] is True
        assert r["failures"] == []

    def test_exactly_at_thresholds_sends(self):
        r = EmailRubric.evaluate_would_send(
            {"personalization": 3.5, "relevance": 3.5, "cta": 3.0, "spam_risk": 1.5}
        )
        assert r["would_send"] is True

    def test_spam_over_limit_fails(self):
        r = EmailRubric.evaluate_would_send(
            {"personalization": 5, "relevance": 5, "cta": 5, "spam_risk": 2}
        )
        assert r["would_send"] is False
        assert any("spam_risk" in f for f in r["failures"])

    def test_missing_dimensions_cannot_pass_by_omission(self):
        r = EmailRubric.evaluate_would_send({})
        assert r["would_send"] is False
        # personalization/relevance/cta default to 0 (fail), spam_risk to 5 (fail)
        assert len(r["failures"]) == 4


class TestICPBand:
    def test_strong_weak_none_boundaries(self):
        assert ICPRubric.band(6.5) == "strong"
        assert ICPRubric.band(6.49) == "weak"
        assert ICPRubric.band(4.0) == "weak"
        assert ICPRubric.band(3.99) == "none"

    def test_band_uses_weighted_overall(self):
        overall = ICPRubric.compute_overall_score(
            {"firmographic": 7, "technographic": 6, "behavioral": 8, "timing": 7}
        )
        assert ICPRubric.band(overall) == "strong"


# --- scorer dispatch --------------------------------------------------------

class TestScorers:
    def test_email_scorer_reports_agreement(self):
        out = _score_email(
            {"scores": {"personalization": 2, "relevance": 4, "cta": 4, "spam_risk": 1},
             "expected_would_send": False}
        )
        assert out["prediction"] is False and out["agree"] is True

    def test_icp_scorer_band_and_overall(self):
        out = _score_icp(
            {"dimensions": {"firmographic": 2, "technographic": 2, "behavioral": 2, "timing": 2},
             "expected_band": "none"}
        )
        assert out["prediction"] == "none" and out["agree"] is True

    def test_persona_scorer_lists_missing(self):
        out = _score_persona({"persona": {"title": "X"}, "expected_complete": False})
        assert out["prediction"] is False
        assert "department" in out["detail"]["missing_fields"]

    def test_scorer_without_label_has_no_agree_key(self):
        out = _score_icp({"dimensions": {"behavioral": 9, "firmographic": 9, "technographic": 9, "timing": 9}})
        assert "agree" not in out


# --- end-to-end over the bundled fixtures -----------------------------------

@pytest.mark.parametrize("rubric", sorted(RUBRICS))
def test_fixtures_score_at_100pct_agreement(rubric, capsys):
    rc = run(rubric, str(DATA / f"{rubric}.jsonl"), as_json=True)
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["count"] == 10
    assert report["graded"] == 10
    assert report["agreement"] == 1.0


def test_main_list_command(capsys):
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    for name in RUBRICS:
        assert name in out


def test_main_run_command_text_output(capsys):
    rc = main(["run", "--rubric", "email_quality", "--input-file", str(DATA / "email_quality.jsonl")])
    assert rc == 0
    assert "Agreement vs labels: 10/10" in capsys.readouterr().out


def test_bad_json_exits_with_message(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{not json}\n")
    with pytest.raises(SystemExit):
        run("icp", str(bad), as_json=False)
