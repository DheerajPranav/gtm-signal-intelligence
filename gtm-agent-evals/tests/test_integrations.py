"""Tests for gtm-agent-evals integration examples."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from gtm_agent_evals import ICPRubric, EmailRubric, PersonaRubric, Seniority

# Import examples (requires examples to be in PYTHONPATH or installed)
try:
    from examples.langchain_integration import (
        LangChainICPEvaluator,
        LangChainEmailEvaluator,
        LangChainPersonaEvaluator,
    )
    from examples.external_dataset_evals import (
        ExternalDatasetEvaluator,
        create_sample_icp_dataset,
        create_sample_email_dataset,
    )

    HAS_EXAMPLES = True
except ImportError:
    HAS_EXAMPLES = False


@pytest.mark.skipif(not HAS_EXAMPLES, reason="Examples not available")
class TestLangChainICPEvaluator:
    """Test LangChain ICP evaluator wrapper."""

    def test_icp_evaluator_high_score(self):
        """Test that high-scoring company passes."""
        evaluator = LangChainICPEvaluator()
        company = {
            "firmographic": 8.0,
            "technographic": 7.0,
            "behavioral": 9.0,
            "timing": 8.0,
        }
        result = evaluator.evaluate(company)

        assert result["passed"] is True
        assert result["score"] > 6.5

    def test_icp_evaluator_low_score(self):
        """Test that low-scoring company fails."""
        evaluator = LangChainICPEvaluator()
        company = {
            "firmographic": 2.0,
            "technographic": 1.0,
            "behavioral": 2.0,
            "timing": 1.0,
        }
        result = evaluator.evaluate(company)

        assert result["passed"] is False
        assert result["score"] < 6.5

    def test_icp_evaluator_behavioral_dominance(self):
        """Test behavioral weight dominates in scoring."""
        evaluator = LangChainICPEvaluator()

        # High behavioral, low others
        high_behavioral = {
            "firmographic": 2.0,
            "technographic": 1.0,
            "behavioral": 10.0,
            "timing": 1.0,
        }

        # Low behavioral, high others
        low_behavioral = {
            "firmographic": 10.0,
            "technographic": 10.0,
            "behavioral": 1.0,
            "timing": 10.0,
        }

        high_result = evaluator.evaluate(high_behavioral)
        low_result = evaluator.evaluate(low_behavioral)

        # Behavioral-driven should score higher
        assert high_result["score"] > low_result["score"] or abs(
            high_result["score"] - low_result["score"]
        ) < 1.0


@pytest.mark.skipif(not HAS_EXAMPLES, reason="Examples not available")
class TestLangChainEmailEvaluator:
    """Test LangChain email evaluator wrapper."""

    def test_email_evaluator_passes(self):
        """Test that high-quality email passes."""
        evaluator = LangChainEmailEvaluator()
        scores = {
            "personalization": 4.0,
            "relevance": 4.0,
            "cta": 3.5,
            "spam_risk": 1.0,
        }
        result = evaluator.evaluate(scores)

        assert result["would_send"] is True
        assert len(result["failures"]) == 0

    def test_email_evaluator_fails_low_personalization(self):
        """Test that low personalization fails."""
        evaluator = LangChainEmailEvaluator()
        scores = {
            "personalization": 2.0,  # Below threshold 3.5
            "relevance": 4.0,
            "cta": 3.5,
            "spam_risk": 1.0,
        }
        result = evaluator.evaluate(scores)

        assert result["would_send"] is False
        assert len(result["failures"]) > 0

    def test_email_evaluator_fails_high_spam_risk(self):
        """Test that high spam risk fails."""
        evaluator = LangChainEmailEvaluator()
        scores = {
            "personalization": 4.0,
            "relevance": 4.0,
            "cta": 3.5,
            "spam_risk": 2.0,  # Above threshold 1.5
        }
        result = evaluator.evaluate(scores)

        assert result["would_send"] is False
        assert len(result["failures"]) > 0


@pytest.mark.skipif(not HAS_EXAMPLES, reason="Examples not available")
class TestLangChainPersonaEvaluator:
    """Test LangChain persona evaluator wrapper."""

    def test_persona_evaluator_complete(self):
        """Test that complete persona passes."""
        evaluator = LangChainPersonaEvaluator()
        persona = {
            "title": "VP Revenue Operations",
            "department": "RevOps",
            "seniority": Seniority.VP,
            "pain_points": ["forecast accuracy"],
            "priorities": ["ROI tracking"],
            "objections": ["cost"],
            "buying_influence": "high",
        }
        result = evaluator.evaluate(persona)

        assert result["is_complete"] is True
        assert len(result["missing_fields"]) == 0

    def test_persona_evaluator_incomplete(self):
        """Test that incomplete persona fails."""
        evaluator = LangChainPersonaEvaluator()
        persona = {
            "title": "VP Revenue Operations",
            "department": "RevOps",
            # Missing other fields
        }
        result = evaluator.evaluate(persona)

        assert result["is_complete"] is False
        assert len(result["missing_fields"]) > 0


@pytest.mark.skipif(not HAS_EXAMPLES, reason="Examples not available")
class TestExternalDatasetEvaluator:
    """Test external dataset evaluation harness."""

    def test_icp_dataset_eval(self):
        """Test ICP dataset evaluation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            dataset_path = tmpdir / "icp_gold.jsonl"

            # Create test data
            create_sample_icp_dataset(dataset_path, n=10)

            # Evaluate
            evaluator = ExternalDatasetEvaluator()
            result = evaluator.eval_icp_dataset(dataset_path)

            assert result["total"] == 10
            assert result["accuracy"] == 1.0  # Perfect match
            assert result["mae"] == 0.0

    def test_email_dataset_eval(self):
        """Test email dataset evaluation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            dataset_path = tmpdir / "email_gold.jsonl"

            # Create test data
            create_sample_email_dataset(dataset_path, n=10)

            # Evaluate
            evaluator = ExternalDatasetEvaluator()
            result = evaluator.eval_email_dataset(dataset_path)

            assert result["total"] == 10
            assert result["would_send_accuracy"] == 1.0

    def test_eval_report_generation(self):
        """Test report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create datasets
            icp_path = tmpdir / "icp_gold.jsonl"
            email_path = tmpdir / "email_gold.jsonl"
            create_sample_icp_dataset(icp_path, n=5)
            create_sample_email_dataset(email_path, n=5)

            # Evaluate
            evaluator = ExternalDatasetEvaluator()
            evaluator.eval_icp_dataset(icp_path)
            evaluator.eval_email_dataset(email_path)

            # Generate report
            report = evaluator.generate_report()

            assert "External Dataset Evaluation Report" in report
            assert "ICPRubric" in report
            assert "EmailRubric" in report
            assert "Total items" in report

    def test_dataset_format_icp(self):
        """Test ICP dataset format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            dataset_path = tmpdir / "icp.jsonl"

            # Write custom ICP data
            with open(dataset_path, "w") as f:
                f.write(
                    json.dumps(
                        {
                            "company": "TestCo",
                            "dimensions": {
                                "firmographic": 7.0,
                                "technographic": 6.0,
                                "behavioral": 8.0,
                                "timing": 7.0,
                            },
                            "expected_score": 7.2,
                        }
                    )
                    + "\n"
                )

            evaluator = ExternalDatasetEvaluator()
            result = evaluator.eval_icp_dataset(dataset_path)

            assert result["total"] == 1
            assert result["mae"] < 0.5  # Should be close to expected

    def test_dataset_format_email(self):
        """Test email dataset format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            dataset_path = tmpdir / "email.jsonl"

            # Write custom email data
            with open(dataset_path, "w") as f:
                f.write(
                    json.dumps(
                        {
                            "email_id": "test1",
                            "scores": {
                                "personalization": 4.0,
                                "relevance": 4.0,
                                "cta": 3.0,
                                "spam_risk": 1.0,
                            },
                            "expected_would_send": True,
                        }
                    )
                    + "\n"
                )

            evaluator = ExternalDatasetEvaluator()
            result = evaluator.eval_email_dataset(dataset_path)

            assert result["total"] == 1
            assert result["would_send_accuracy"] == 1.0
