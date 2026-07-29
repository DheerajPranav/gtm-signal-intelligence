"""External dataset evaluation harness for gtm-agent-evals rubrics.

Demonstrates how to evaluate the rubrics on external datasets
without depending on the gtm-outbound-agent.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json

from gtm_agent_evals import ICPRubric, EmailRubric, CritiqueRubric, PersonaRubric, Seniority


@dataclass
class EvalResult:
    """One result from an eval run."""

    item_id: str
    rubric_name: str
    metric: str
    value: float
    reasoning: str


class ExternalDatasetEvaluator:
    """Framework-agnostic evaluation harness for external datasets."""

    def __init__(self):
        self.results: list[EvalResult] = []

    def eval_icp_dataset(self, dataset_path: Path) -> dict:
        """Evaluate companies on ICP fit against a gold dataset.

        Dataset format (JSONL):
            {"company": "Acme", "expected_score": 7.5, "dimensions": {...}}
        """
        correct = 0
        total = 0
        diffs = []

        with open(dataset_path) as f:
            for line in f:
                item = json.loads(line)
                total += 1

                predicted = ICPRubric.compute_overall_score(item["dimensions"])
                expected = item["expected_score"]
                diff = abs(predicted - expected)
                diffs.append(diff)

                if diff < 1.0:  # Allow 1-point tolerance
                    correct += 1

                # Use inverse of MAE as metric (lower MAE = higher value)
                # So perfectly matching gets 1.0, 1-point error gets 0.0
                metric_value = max(0.0, 1.0 - diff)

                self.results.append(
                    EvalResult(
                        item_id=item.get("company", f"item_{total}"),
                        rubric_name="ICPRubric",
                        metric="accuracy",
                        value=metric_value,
                        reasoning=f"predicted={predicted:.2f}, expected={expected:.2f}, mae={diff:.2f}",
                    )
                )

        mae = sum(diffs) / len(diffs) if diffs else 0.0
        accuracy = correct / total if total > 0 else 0.0

        return {
            "rubric": "ICPRubric",
            "total": total,
            "accuracy": accuracy,
            "mae": mae,
        }

    def eval_email_dataset(self, dataset_path: Path) -> dict:
        """Evaluate emails against a gold dataset.

        Dataset format (JSONL):
            {
                "email_id": "123",
                "scores": {
                    "personalization": 4.0,
                    "relevance": 3.5,
                    "cta": 3.0,
                    "spam_risk": 1.0
                },
                "expected_would_send": true
            }
        """
        correct = 0
        total = 0
        criteria = EmailRubric.DIMENSIONS["would_send"]["pass_criteria"]

        with open(dataset_path) as f:
            for line in f:
                item = json.loads(line)
                total += 1

                scores = item["scores"]
                predicted_would_send = (
                    scores.get("personalization", 0) >= criteria["personalization"]
                    and scores.get("relevance", 0) >= criteria["relevance"]
                    and scores.get("cta", 0) >= criteria["cta"]
                    and scores.get("spam_risk", 0) <= criteria["spam_risk"]
                )
                expected_would_send = item.get("expected_would_send", False)

                if predicted_would_send == expected_would_send:
                    correct += 1

                self.results.append(
                    EvalResult(
                        item_id=item.get("email_id", f"email_{total}"),
                        rubric_name="EmailRubric",
                        metric="would_send_match",
                        value=1.0 if predicted_would_send == expected_would_send else 0.0,
                        reasoning=f"predicted={predicted_would_send}, expected={expected_would_send}",
                    )
                )

        accuracy = correct / total if total > 0 else 0.0

        return {
            "rubric": "EmailRubric",
            "total": total,
            "would_send_accuracy": accuracy,
        }

    def eval_persona_dataset(self, dataset_path: Path) -> dict:
        """Evaluate personas for completeness.

        Dataset format (JSONL):
            {
                "persona_id": "123",
                "persona": {...},
                "expected_complete": true
            }
        """
        correct = 0
        total = 0

        with open(dataset_path) as f:
            for line in f:
                item = json.loads(line)
                total += 1

                persona = item["persona"]
                predicted_complete = PersonaRubric.is_complete(persona)
                expected_complete = item.get("expected_complete", False)

                if predicted_complete == expected_complete:
                    correct += 1

                missing = [
                    f for f in PersonaRubric.REQUIRED_FIELDS if f not in persona
                ]

                self.results.append(
                    EvalResult(
                        item_id=item.get("persona_id", f"persona_{total}"),
                        rubric_name="PersonaRubric",
                        metric="completeness_match",
                        value=1.0 if predicted_complete == expected_complete else 0.0,
                        reasoning=f"predicted={predicted_complete}, expected={expected_complete}, missing={missing}",
                    )
                )

        accuracy = correct / total if total > 0 else 0.0

        return {
            "rubric": "PersonaRubric",
            "total": total,
            "completeness_accuracy": accuracy,
        }

    def generate_report(self) -> str:
        """Generate a summary report of all evals."""
        if not self.results:
            return "No results to report."

        by_rubric = {}
        for result in self.results:
            if result.rubric_name not in by_rubric:
                by_rubric[result.rubric_name] = []
            by_rubric[result.rubric_name].append(result)

        report = "# External Dataset Evaluation Report\n\n"

        for rubric_name, results in sorted(by_rubric.items()):
            report += f"## {rubric_name}\n\n"
            report += f"- Total items: {len(results)}\n"

            # Calculate average metric
            values = [r.value for r in results]
            avg_value = sum(values) / len(values) if values else 0.0
            report += f"- Average metric: {avg_value:.3f}\n"

            # Failure count
            failures = [r for r in results if r.value < 1.0]
            if failures:
                report += f"- Failures: {len(failures)}\n"
                for fail in failures[:5]:  # Show first 5
                    report += f"  - {fail.item_id}: {fail.reasoning}\n"

            report += "\n"

        return report


# Example: Generate synthetic datasets for testing
def create_sample_icp_dataset(path: Path, n: int = 20):
    """Create a sample ICP dataset for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for i in range(n):
            dimensions = {
                "firmographic": 5.0 + (i % 3),
                "technographic": 4.0 + (i % 2),
                "behavioral": 6.0 + (i % 4),
                "timing": 5.0 + (i % 3),
            }
            expected_score = ICPRubric.compute_overall_score(dimensions)
            f.write(
                json.dumps(
                    {
                        "company": f"Company{i}",
                        "dimensions": dimensions,
                        "expected_score": expected_score,
                    }
                )
                + "\n"
            )


def create_sample_email_dataset(path: Path, n: int = 20):
    """Create a sample email dataset for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for i in range(n):
            scores = {
                "personalization": 3.0 + (i % 2),
                "relevance": 3.0 + (i % 2),
                "cta": 3.0,
                "spam_risk": 1.0,
            }
            criteria = EmailRubric.DIMENSIONS["would_send"]["pass_criteria"]
            expected_would_send = (
                scores.get("personalization", 0) >= criteria["personalization"]
                and scores.get("relevance", 0) >= criteria["relevance"]
                and scores.get("cta", 0) >= criteria["cta"]
                and scores.get("spam_risk", 0) <= criteria["spam_risk"]
            )
            f.write(
                json.dumps(
                    {
                        "email_id": f"email_{i}",
                        "scores": scores,
                        "expected_would_send": expected_would_send,
                    }
                )
                + "\n"
            )


# Example usage
if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create and evaluate sample datasets
        evaluator = ExternalDatasetEvaluator()

        icp_path = tmpdir / "icp_gold.jsonl"
        create_sample_icp_dataset(icp_path)
        icp_result = evaluator.eval_icp_dataset(icp_path)
        print("ICP Result:", icp_result)

        email_path = tmpdir / "email_gold.jsonl"
        create_sample_email_dataset(email_path)
        email_result = evaluator.eval_email_dataset(email_path)
        print("Email Result:", email_result)

        # Generate report
        print("\n" + evaluator.generate_report())
