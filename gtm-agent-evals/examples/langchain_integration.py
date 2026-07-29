"""LangChain integration example using gtm-agent-evals rubrics.

Shows how to use the open-source rubrics as LangChain evaluators,
not tied to any specific GTM agent.
"""

from typing import Optional

from gtm_agent_evals import ICPRubric, EmailRubric, CritiqueRubric, PersonaRubric


class LangChainICPEvaluator:
    """Wraps ICPRubric as a LangChain-compatible evaluator."""

    def evaluate(
        self,
        company_profile: dict,
        rubric_weights: Optional[dict] = None,
    ) -> dict:
        """Evaluate ICP fit for any company profile.

        Args:
            company_profile: dict with keys: firmographic, technographic,
                           behavioral, timing (each 0-10)
            rubric_weights: optional override weights (default: ICPRubric.WEIGHTS)

        Returns:
            dict with keys: score, pass/fail, reasoning
        """
        # Compute score using rubric
        score = ICPRubric.compute_overall_score(company_profile)

        # Simple threshold gate (tune for your use case)
        threshold = 6.5
        passed = score >= threshold

        reasoning = {
            "score": score,
            "threshold": threshold,
            "passed": passed,
            "breakdown": {
                dim: company_profile.get(dim, 0)
                for dim in ICPRubric.WEIGHTS
            },
        }

        return reasoning


class LangChainEmailEvaluator:
    """Wraps EmailRubric as a LangChain-compatible evaluator."""

    def evaluate(
        self,
        email_scores: dict,
    ) -> dict:
        """Evaluate email quality based on 4 dimensions.

        Args:
            email_scores: dict with keys personalization, relevance, cta,
                         spam_risk (each 0-5)

        Returns:
            dict with would_send boolean and pass/fail status
        """
        criteria = EmailRubric.DIMENSIONS["would_send"]["pass_criteria"]

        would_send = (
            email_scores.get("personalization", 0) >= criteria["personalization"]
            and email_scores.get("relevance", 0) >= criteria["relevance"]
            and email_scores.get("cta", 0) >= criteria["cta"]
            and email_scores.get("spam_risk", 0) <= criteria["spam_risk"]
        )

        reasoning = {
            "scores": email_scores,
            "thresholds": criteria,
            "would_send": would_send,
            "failures": [
                f"personalization {email_scores.get('personalization', 0):.1f} < {criteria['personalization']}"
                for key in ["personalization"]
                if email_scores.get(key, 0) < criteria[key]
            ]
            + [
                f"relevance {email_scores.get('relevance', 0):.1f} < {criteria['relevance']}"
                for key in ["relevance"]
                if email_scores.get(key, 0) < criteria[key]
            ]
            + [
                f"cta {email_scores.get('cta', 0):.1f} < {criteria['cta']}"
                for key in ["cta"]
                if email_scores.get(key, 0) < criteria[key]
            ]
            + [
                f"spam_risk {email_scores.get('spam_risk', 0):.1f} > {criteria['spam_risk']}"
                for key in ["spam_risk"]
                if email_scores.get(key, 0) > criteria[key]
            ],
        }

        return reasoning


class LangChainPersonaEvaluator:
    """Wraps PersonaRubric as a LangChain-compatible evaluator."""

    def evaluate(self, persona: dict) -> dict:
        """Validate persona completeness.

        Args:
            persona: dict with required fields (see PersonaRubric.REQUIRED_FIELDS)

        Returns:
            dict with is_complete boolean and missing fields
        """
        is_complete = PersonaRubric.is_complete(persona)

        missing = [
            field
            for field in PersonaRubric.REQUIRED_FIELDS
            if field not in persona or not persona[field]
        ]

        reasoning = {
            "is_complete": is_complete,
            "missing_fields": missing,
            "required_fields": list(PersonaRubric.REQUIRED_FIELDS.keys()),
        }

        return reasoning


# Example usage
if __name__ == "__main__":
    # ICP Evaluator
    icp_eval = LangChainICPEvaluator()
    company = {
        "firmographic": 7.0,
        "technographic": 6.0,
        "behavioral": 9.0,
        "timing": 6.0,
    }
    print("ICP Evaluation:", icp_eval.evaluate(company))

    # Email Evaluator
    email_eval = LangChainEmailEvaluator()
    email_scores = {
        "personalization": 4.0,
        "relevance": 3.5,
        "cta": 3.0,
        "spam_risk": 1.0,
    }
    print("Email Evaluation:", email_eval.evaluate(email_scores))

    # Persona Evaluator
    persona_eval = LangChainPersonaEvaluator()
    persona = {
        "title": "VP Revenue Operations",
        "department": "RevOps",
        "seniority": "vp",
        "pain_points": ["forecast accuracy", "pipeline visibility"],
        "priorities": ["ROI tracking", "cycle time"],
        "objections": ["cost", "implementation"],
        "buying_influence": "high",
    }
    print("Persona Evaluation:", persona_eval.evaluate(persona))
