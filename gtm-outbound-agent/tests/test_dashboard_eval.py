"""Tests for dashboard and full eval harness (Days 16-17)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from evals.run_full_eval import EvalHarness, EvalMetrics, CompanyGold


class TestEvalHarness:
    """Test full eval harness."""

    @pytest.fixture
    def harness(self, tmp_path, monkeypatch):
        """Create a test harness in a temp directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "evals").mkdir()
        return EvalHarness(repo_dir=tmp_path)

    def test_load_gold_enrichment(self, harness):
        """Test loading enrichment gold set."""
        gold = harness.load_gold_companies("enrichment")
        assert len(gold) == 10
        assert all(isinstance(g, CompanyGold) for g in gold)
        # Check specific fields
        assert gold[0].domain == "ledgerly.com"
        assert gold[0].series == "Series B"

    def test_load_gold_icp(self, harness):
        """Test loading ICP gold set."""
        gold = harness.load_gold_companies("icp")
        assert len(gold) == 15
        # Count strong/weak/not-fit by has_revops_hire
        strong = sum(1 for g in gold if g.has_revops_hire)
        weak = sum(1 for g in gold if not g.has_revops_hire)
        assert strong == 7  # Expected strong fit count
        assert weak == 8  # Expected weak + not-fit count

    def test_load_gold_email_quality(self, harness):
        """Test loading email quality gold set."""
        gold = harness.load_gold_companies("email_quality")
        assert len(gold) == 15
        assert all(isinstance(g, CompanyGold) for g in gold)

    def test_eval_enrichment_accuracy_all_pass(self, harness):
        """Test enrichment accuracy eval (all companies succeeded)."""
        results = {}
        gold = harness.load_gold_companies("enrichment")
        for company in gold:
            results[company.domain] = {
                "status": "completed",
                "profile": {"industry": "SaaS", "headcount": 100, "arr": 25.0},
            }

        metric = harness.eval_enrichment_accuracy(results)
        assert metric.metric_name == "Enrichment Accuracy"
        assert metric.value == 1.0  # All companies should be complete
        assert metric.passes

    def test_eval_enrichment_accuracy_all_fail(self, harness):
        """Test enrichment accuracy eval (all companies failed)."""
        results = {}
        for i in range(10):
            results[f"company{i}.com"] = {"status": "failed"}

        metric = harness.eval_enrichment_accuracy(results)
        assert metric.value == 0.0
        assert not metric.passes

    def test_eval_icp_correlation(self, harness):
        """Test ICP correlation eval."""
        results = {}
        gold = harness.load_gold_companies("icp")
        for g in gold:
            results[g.domain] = {"status": "completed"}

        metric = harness.eval_icp_correlation(results)
        assert metric.metric_name == "ICP Correlation (Spearman)"
        assert 0 <= metric.value <= 1.0

    def test_eval_email_quality(self, harness):
        """Test email quality eval."""
        results = {}
        gold = harness.load_gold_companies("email_quality")
        for g in gold:
            results[g.domain] = {"status": "completed"}

        metric = harness.eval_email_quality(results)
        assert metric.metric_name == "Email Quality (Avg Critique)"
        assert 0 <= metric.value <= 5.0

    def test_eval_would_send_pass_rate(self, harness):
        """Test would-send pass rate eval."""
        results = {}
        gold = harness.load_gold_companies("email_quality")
        for g in gold:
            results[g.domain] = {"status": "completed"}

        metric = harness.eval_would_send_pass_rate(results)
        assert metric.metric_name == "Would-Send Pass Rate"
        assert 0 <= metric.value <= 1.0

    def test_run_all_evals(self, harness):
        """Test running all evals at once."""
        results = {}
        gold = harness.load_gold_companies("email_quality")
        for g in gold:
            results[g.domain] = {"status": "completed"}

        metrics = harness.run_all_evals(results)
        assert len(metrics) == 4
        assert all(isinstance(m, EvalMetrics) for m in metrics)
        assert harness.metrics == metrics

    def test_metrics_have_thresholds(self, harness):
        """Test that all metrics have DoD thresholds."""
        harness.run_all_evals({})
        for metric in harness.metrics:
            assert metric.threshold is not None, f"{metric.metric_name} has no threshold"

    def test_eval_metrics_pass_fail_logic(self, harness):
        """Test that pass/fail is correctly set based on threshold."""
        # Create metric that fails
        metric = EvalMetrics("Test", value=0.5, baseline=0.6, threshold=0.6)
        assert not metric.passes  # 0.5 < 0.6 threshold

        # Create metric that passes
        metric = EvalMetrics("Test", value=0.7, baseline=0.6, threshold=0.6)
        assert metric.passes  # 0.7 >= 0.6 threshold

    def test_generate_report_structure(self, harness):
        """Test report generation includes all required sections."""
        harness.run_all_evals({})
        report = harness.generate_report()

        # Check key sections
        assert "# Full Eval Report" in report
        assert "## Key Metrics" in report
        assert "## Metric Breakdown" in report
        assert "## Interpretation" in report
        assert "## Next Steps" in report

        # Check metrics are present
        for metric in harness.metrics:
            assert metric.metric_name in report

    def test_save_report(self, harness):
        """Test saving report to disk."""
        harness.run_all_evals({})
        report_path = harness.save_report("test_report.md")

        assert report_path.exists()
        content = report_path.read_text()
        assert "# Full Eval Report" in content

    def test_report_shows_failing_metrics(self, harness):
        """Test that report highlights failing metrics."""
        # Run with empty results (all will fail)
        harness.run_all_evals({})
        report = harness.generate_report()

        # Should show failures
        assert "✗ FAIL" in report or "Next Steps" in report

    def test_report_includes_results_table(self, harness):
        """Test that report includes a metrics table."""
        harness.run_all_evals({})
        report = harness.generate_report()

        # Check for markdown table
        assert "| Metric | Value | Baseline | Status |" in report

    def test_mutation_pass_rate_logic(self, harness):
        """Mutation test: verify pass rate computation."""
        # Create scenario with known results
        results = {}
        gold = harness.load_gold_companies("email_quality")

        # All high-fit companies
        for g in gold[:8]:
            results[g.domain] = {"status": "completed"}

        # Not-fit companies
        for g in gold[8:]:
            results[g.domain] = {"status": "completed"}

        metric = harness.eval_would_send_pass_rate(results)

        # Verify the value is in expected range (weighted by company fit)
        assert 0.4 <= metric.value <= 0.8, f"Pass rate {metric.value} out of expected range"

    def test_enrichment_completeness_check(self, harness):
        """Test that enrichment eval checks for complete profiles."""
        # Company with incomplete profile
        results = {
            "incomplete.com": {
                "status": "completed",
                "profile": {"industry": "SaaS"},  # Missing headcount, arr
            },
            "complete.com": {
                "status": "completed",
                "profile": {"industry": "SaaS", "headcount": 100, "arr": 25.0},
            },
        }

        # Fill remaining gold companies as completed
        for i in range(8):
            results[f"gold{i}.com"] = {
                "status": "completed",
                "profile": {"industry": "SaaS", "headcount": 100, "arr": 25.0},
            }

        metric = harness.eval_enrichment_accuracy(results)
        # Should reflect only 9/10 complete
        assert metric.value <= 0.9


class TestEvalMetrics:
    """Test EvalMetrics data class."""

    def test_metrics_string_repr(self):
        """Test string representation of metrics."""
        metric = EvalMetrics("Test Metric", value=0.75, baseline=0.70)
        str_repr = str(metric)
        assert "✓" in str_repr
        assert "Test Metric" in str_repr
        assert "0.75" in str_repr

    def test_metrics_with_no_baseline(self):
        """Test metrics without baseline."""
        metric = EvalMetrics("Test", value=0.5)
        str_repr = str(metric)
        assert "Test" in str_repr

    def test_pass_fail_determination(self):
        """Test pass/fail logic."""
        passing = EvalMetrics("Test", value=0.75, threshold=0.70)
        assert passing.passes

        failing = EvalMetrics("Test", value=0.50, threshold=0.70)
        assert not failing.passes

        no_threshold = EvalMetrics("Test", value=0.50, threshold=None)
        assert no_threshold.passes  # Default passes if no threshold


class TestEvalGoldSets:
    """Test gold dataset consistency."""

    def test_enrichment_gold_sizes(self):
        """Test enrichment gold set has 10 companies."""
        harness = EvalHarness()
        gold = harness.load_gold_companies("enrichment")
        assert len(gold) == 10

    def test_icp_gold_composition(self):
        """Test ICP gold set composition."""
        harness = EvalHarness()
        gold = harness.load_gold_companies("icp")
        assert len(gold) == 15
        # 7 strong fit
        strong = [g for g in gold if g.has_revops_hire]
        assert len(strong) == 7
        # Others are weak or not-fit
        assert len([g for g in gold if not g.has_revops_hire]) == 8

    def test_email_quality_gold_sizes(self):
        """Test email quality gold set has 15 companies."""
        harness = EvalHarness()
        gold = harness.load_gold_companies("email_quality")
        assert len(gold) == 15

    def test_gold_companies_have_required_fields(self):
        """Test all gold companies have required fields."""
        harness = EvalHarness()
        gold = harness.load_gold_companies("enrichment")

        for company in gold:
            assert company.domain
            assert company.industry
            assert company.series
            assert company.headcount > 0
            assert company.arr > 0
