# Contributing to gtm-agent-evals

Thanks for your interest in contributing! This is an open-source evaluation rubric kit built to be framework-agnostic and reusable across any GTM AI system.

## Design Principles

Before contributing, understand our core philosophy:

1. **Framework-agnostic**: No coupling to specific frameworks (LangChain, LlamaIndex, OpenAI SDK). Use only standard Python.
2. **Deterministic gates**: Thresholds are computed, not LLM-generated. No "ask Claude to score this" in rubric validation.
3. **Honest scoring**: A 3/5 email is "OK", not "good". No inflated metrics to make users feel better.
4. **Minimal dependencies**: Only `pydantic>=2.0` and `anthropic>=0.28` (optional for examples).

## How to Contribute

### Adding a New Rubric

New rubrics should follow the existing pattern:

```python
class MyRubric:
    """Description of what this rubric evaluates."""
    
    DIMENSIONS = {
        "dimension_name": {
            "description": "What this dimension measures",
            "max": 5,  # or None for boolean
            "scoring": {
                5: "Best case description",
                4: "...",
                3: "...",
                2: "...",
                1: "...",
                0: "Worst case or N/A",
            },
        },
        # ... more dimensions
    }
    
    @staticmethod
    def validate(item: dict) -> dict:
        """Validate item against this rubric."""
        return {
            "passed": bool,
            "reasoning": str,
            "scores": {"dimension": float},
        }
```

**Checklist:**
- [ ] All 5 dimensions have 0-5 scoring guides
- [ ] Descriptions are specific (not generic)
- [ ] No LLM calls in validation logic
- [ ] Tests verify scoring guide coverage
- [ ] Example usage in docstring
- [ ] A `examples/data/<rubric>.jsonl` fixture with **5 passing + 5 failing** records (`expected_*` labels) so `python -m gtm_agent_evals run --rubric <name>` reports agreement
- [ ] Calibration note in `docs/CALIBRATION.md` explaining any new weight/threshold/cutoff
- [ ] If it's a gate the runner should expose, wire it into `RUBRICS` in `cli.py`

### Adding an Integration Example

Examples show how to use rubrics in real systems:

```python
# examples/my_framework_integration.py

from gtm_agent_evals import ICPRubric, EmailRubric  # Only import rubrics

class MyFrameworkEvaluator:
    """Wraps rubrics for use with MyFramework."""
    
    def evaluate(self, item: dict) -> dict:
        """Evaluate item, return framework-native result."""
        # Use rubric logic
        # Never import from gtm-outbound-agent
        return {...}
```

**Checklist:**
- [ ] Only imports rubrics, no agent code
- [ ] Works with Pydantic models (if using them)
- [ ] Has docstring with usage example
- [ ] Included in README integrations section
- [ ] Covered by tests in test_integrations.py

### Writing Tests

Tests should verify:
1. **Rubric logic**: Dimensions, weights, thresholds
2. **Integration points**: Evaluators work with different input formats
3. **Edge cases**: Empty inputs, None values, boundary scores (0, 5)
4. **Reports**: Markdown output is valid, no None values

```python
def test_my_rubric_specific_case(self):
    """Test one specific scenario or edge case."""
    # Arrange: Set up test data
    dimensions = {"dim1": 5.0, "dim2": 0.0}
    
    # Act: Call rubric logic
    result = MyRubric.validate(dimensions)
    
    # Assert: Verify specific expectations
    assert result["passed"] is True
    assert "dim1" in result["scores"]
```

**Avoid:**
- Mocking internals (test public API only)
- Hardcoding company/email data (use fixtures)
- Testing Python stdlib (focus on rubric logic)
- Slow I/O (use temporary files, not network)

## Code Style

- **Format**: Black (implicit, not required)
- **Imports**: `from __future__ import annotations` at top
- **Type hints**: Use dataclass and Pydantic models
- **Docstrings**: One-liner for methods, examples for classes
- **Comments**: Only for non-obvious logic or workarounds

## Submitting Changes

1. **Fork** the repo
2. **Create a branch**: `git checkout -b feature/my-rubric`
3. **Make changes** following design principles above
4. **Test locally**: `PYTHONPATH=. pytest tests/`
5. **Commit**: Clear message describing what & why
6. **Push** and **open a PR** with:
   - Description of rubric/integration
   - Why it's valuable
   - Test coverage stats
   - Any dependencies added

## What We're NOT Looking For

- Framework-specific wrappers that couple to agent internals
- LLM-based gate logic (we compute, not delegate)
- Complex scoring algorithms (prefer simple weights)
- New rubrics without 3+ usage examples
- Dependencies on proprietary libraries

## What We ARE Looking For

- New rubric dimensions (based on production use)
- Framework integrations (LlamaIndex, Hugging Face, etc.)
- External dataset format examples (your gold labels)
- Scoring guide improvements (clarify edge cases)
- Better documentation and examples

## Questions?

Open an issue with:
- **[Rubric]** for new evaluation dimensions
- **[Integration]** for framework wrappers
- **[Docs]** for clarifications
- **[Bug]** for scoring/logic issues

## License

By contributing, you agree your code is released under MIT License.

---

**Repository:** https://github.com/DheerajPranav/gtm-signal-intelligence  
**Package:** `gtm-agent-evals` — Open-source LLM-judge rubric kit for GTM AI agents
