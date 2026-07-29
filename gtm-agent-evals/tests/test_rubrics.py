"""Tests for GTM evaluation rubrics."""

from __future__ import annotations

import pytest

from gtm_agent_evals.rubrics import (
    ICPRubric,
    PersonaRubric,
    EmailRubric,
    CritiqueRubric,
    Seniority,
)


class TestICPRubric:
    """Test ICP Scoring Rubric."""

    def test_weights_sum_to_one(self):
        """Verify dimension weights sum to 1.0."""
        total = sum(ICPRubric.WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_behavioral_weight_is_primary(self):
        """Verify behavioral signal gets highest weight (0.45)."""
        assert ICPRubric.WEIGHTS["behavioral"] == 0.45
        assert ICPRubric.WEIGHTS["behavioral"] > ICPRubric.WEIGHTS["firmographic"]
        assert ICPRubric.WEIGHTS["behavioral"] > ICPRubric.WEIGHTS["timing"]
        assert ICPRubric.WEIGHTS["behavioral"] > ICPRubric.WEIGHTS["technographic"]

    def test_compute_overall_score_all_perfect(self):
        """Test overall score when all dimensions are perfect (10.0)."""
        dimensions = {
            "firmographic": 10.0,
            "technographic": 10.0,
            "behavioral": 10.0,
            "timing": 10.0,
        }
        score = ICPRubric.compute_overall_score(dimensions)
        assert score == 10.0

    def test_compute_overall_score_all_zero(self):
        """Test overall score when all dimensions are zero."""
        dimensions = {
            "firmographic": 0.0,
            "technographic": 0.0,
            "behavioral": 0.0,
            "timing": 0.0,
        }
        score = ICPRubric.compute_overall_score(dimensions)
        assert score == 0.0

    def test_compute_overall_score_behavioral_driven(self):
        """Test that behavioral signal dominates overall score."""
        # High behavioral, low others
        dimensions = {
            "firmographic": 2.0,
            "technographic": 1.0,
            "behavioral": 10.0,  # Strong signal
            "timing": 2.0,
        }
        score = ICPRubric.compute_overall_score(dimensions)
        # Should be dominated by behavioral (0.45 * 10) + small from others
        # Calculation: 2*0.20 + 1*0.15 + 10*0.45 + 2*0.20 = 0.4 + 0.15 + 4.5 + 0.4 = 5.45
        assert score > 5.0  # Behavioral dominates, but not 6+

        # Reverse: low behavioral, high others
        dimensions = {
            "firmographic": 10.0,
            "technographic": 10.0,
            "behavioral": 1.0,  # Weak signal
            "timing": 10.0,
        }
        score2 = ICPRubric.compute_overall_score(dimensions)
        # Calculation: 10*0.20 + 10*0.15 + 1*0.45 + 10*0.20 = 2.0 + 1.5 + 0.45 + 2.0 = 5.95
        assert score2 < 6.0  # Less than all-high scenario

    def test_compute_overall_score_clamps_to_range(self):
        """Test that score is clamped to [0.0, 10.0]."""
        # Over 10
        dimensions = {"firmographic": 15.0, "technographic": 15.0, "behavioral": 15.0, "timing": 15.0}
        score = ICPRubric.compute_overall_score(dimensions)
        assert score == 10.0

        # Under 0
        dimensions = {"firmographic": -10.0, "technographic": -10.0, "behavioral": -10.0, "timing": -10.0}
        score = ICPRubric.compute_overall_score(dimensions)
        assert score == 0.0

    def test_dimension_descriptions_exist(self):
        """Verify all dimensions have descriptions."""
        expected_dims = {"firmographic", "technographic", "behavioral", "timing"}
        assert set(ICPRubric.DIMENSION_DESCRIPTIONS.keys()) == expected_dims


class TestPersonaRubric:
    """Test Persona Building Rubric."""

    def test_required_fields_defined(self):
        """Verify all required fields are documented."""
        expected = {"title", "department", "seniority", "pain_points", "priorities", "objections", "buying_influence"}
        assert set(PersonaRubric.REQUIRED_FIELDS.keys()) == expected

    def test_is_complete_with_all_fields(self):
        """Test that a complete persona passes validation."""
        persona = {
            "title": "VP Revenue Operations",
            "department": "RevOps",
            "seniority": Seniority.VP,
            "pain_points": ["forecast accuracy", "pipeline visibility"],
            "priorities": ["ROI tracking", "cycle time reduction"],
            "objections": ["cost concern", "implementation risk"],
            "buying_influence": "high",
        }
        assert PersonaRubric.is_complete(persona)

    def test_is_complete_with_missing_fields(self):
        """Test that incomplete personas fail validation."""
        incomplete_persona = {
            "title": "VP Revenue Operations",
            "department": "RevOps",
            # Missing seniority, pain_points, etc.
        }
        assert not PersonaRubric.is_complete(incomplete_persona)

    def test_grounding_terms_exist(self):
        """Verify grounding terms for major segments."""
        expected_segments = {"fintech", "devtools", "marketing", "enterprise"}
        assert set(PersonaRubric.GROUNDING_TERMS.keys()) == expected_segments
        # Each segment should have pain-point vocabulary
        for segment, terms in PersonaRubric.GROUNDING_TERMS.items():
            assert len(terms) > 0


class TestEmailRubric:
    """Test Email Writing Rubric."""

    def test_dimensions_defined(self):
        """Verify all 5 email dimensions are defined."""
        expected_dims = {"personalization", "relevance", "cta", "spam_risk", "would_send"}
        assert set(EmailRubric.DIMENSIONS.keys()) == expected_dims

    def test_dimensions_have_max_scores(self):
        """Verify scoring dimensions have max scores."""
        for dim, spec in EmailRubric.DIMENSIONS.items():
            if dim != "would_send":  # would_send is boolean
                assert spec["max"] == 5

    def test_would_send_is_boolean(self):
        """Verify would_send dimension has no numeric max."""
        assert EmailRubric.DIMENSIONS["would_send"]["max"] is None

    def test_pass_criteria_defined(self):
        """Verify would_send pass criteria are strict."""
        criteria = EmailRubric.DIMENSIONS["would_send"]["pass_criteria"]
        assert criteria["personalization"] == 3.5
        assert criteria["relevance"] == 3.5
        assert criteria["cta"] == 3.0
        assert criteria["spam_risk"] == 1.5  # LOWER is better

    def test_scoring_guides_exist(self):
        """Verify all dimensions have scoring guides."""
        for dim in ["personalization", "relevance", "cta", "spam_risk"]:
            assert "scoring" in EmailRubric.DIMENSIONS[dim]
            scoring = EmailRubric.DIMENSIONS[dim]["scoring"]
            # Should have 0-5 scores
            assert len(scoring) == 6


class TestCritiqueRubric:
    """Test Critique Rubric."""

    def test_critique_rubric_inherits_email_logic(self):
        """Verify critique uses same thresholds as email rubric."""
        # Critique thresholds should match email pass criteria
        assert CritiqueRubric.SHOULD_SEND_THRESHOLDS["personalization"] == 3.5
        assert CritiqueRubric.SHOULD_SEND_THRESHOLDS["relevance"] == 3.5
        assert CritiqueRubric.SHOULD_SEND_THRESHOLDS["cta"] == 3.0
        assert CritiqueRubric.SHOULD_SEND_THRESHOLDS["spam_risk"] == 1.5

    def test_system_prompt_exists(self):
        """Verify critique system prompt is defined."""
        prompt = CritiqueRubric.SYSTEM_PROMPT
        assert len(prompt) > 100
        assert "skeptical" in prompt.lower()
        assert "would_send" in prompt.lower()

    def test_system_prompt_mentions_thresholds(self):
        """Verify system prompt documents thresholds."""
        prompt = CritiqueRubric.SYSTEM_PROMPT
        assert "3.5" in prompt  # personalization/relevance
        assert "3.0" in prompt  # cta
        assert "1.5" in prompt  # spam_risk


class TestRubricConsistency:
    """Test consistency across rubrics."""

    def test_icp_behavioral_weight_matches_emphasis(self):
        """Verify behavioral weight reflects RevOps-first positioning."""
        behavioral_weight = ICPRubric.WEIGHTS["behavioral"]
        # Behavioral should be >2x firmographic for RevOps platform
        assert behavioral_weight / ICPRubric.WEIGHTS["firmographic"] >= 2.0

    def test_email_would_send_is_strict(self):
        """Verify email would_send thresholds are genuinely strict."""
        criteria = EmailRubric.DIMENSIONS["would_send"]["pass_criteria"]
        # All major dimensions require 3.0+/5
        assert criteria["personalization"] >= 3.5
        assert criteria["relevance"] >= 3.5
        assert criteria["cta"] >= 3.0

    def test_seniority_enum_covers_spectrum(self):
        """Verify seniority levels span IC to C-suite."""
        levels = [Seniority.IC, Seniority.MANAGER, Seniority.DIRECTOR, Seniority.VP, Seniority.C_SUITE]
        assert len(levels) == 5
