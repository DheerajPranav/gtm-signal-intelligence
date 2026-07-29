# Full Eval Report

Generated: "/Users/dheerajpranav/Desktop/DeskTrux/Projects/Dheeraj/gtm-signal-intelligence/gtm-outbound-agent"

## Key Metrics

| Metric | Value | Baseline | Status |
|--------|-------|----------|--------|
| Enrichment Accuracy | **0.000** | 0.800 | ✗ FAIL |
| ICP Correlation (Spearman) | **0.000** | 0.600 | ✗ FAIL |
| Email Quality (Avg Critique) | **0.000** | 3.500 | ✗ FAIL |
| Would-Send Pass Rate | **0.000** | 0.600 | ✗ FAIL |

**Result:** 0/4 metrics passing

## Metric Breakdown

### Enrichment Accuracy
- **Value:** 0.000
- **Baseline:** 0.8
- **Threshold:** 0.7
- **Status:** ✗ FAIL

### ICP Correlation (Spearman)
- **Value:** 0.000
- **Baseline:** 0.6
- **Threshold:** 0.6
- **Status:** ✗ FAIL

### Email Quality (Avg Critique)
- **Value:** 0.000
- **Baseline:** 3.5
- **Threshold:** 3.5
- **Status:** ✗ FAIL

### Would-Send Pass Rate
- **Value:** 0.000
- **Baseline:** 0.6
- **Threshold:** 0.6
- **Status:** ✗ FAIL

## Interpretation

- **Enrichment Accuracy:** % of companies where research agent produced complete profiles
- **ICP Correlation:** Spearman rank correlation between predicted and actual fit (DoD > 0.6)
- **Email Quality:** Average critique score (0-5) across all generated emails
- **Would-Send Rate:** % of emails passing the would-send bar (DoD > 60%)

## Next Steps

Weakest metrics:
- Enrichment Accuracy: 0.000 (threshold: 0.7)
- ICP Correlation (Spearman): 0.000 (threshold: 0.6)
- Email Quality (Avg Critique): 0.000 (threshold: 3.5)
- Would-Send Pass Rate: 0.000 (threshold: 0.6)

Recommended fixes (Day 18 iteration cycle):
1. Hypothesis-test prompt changes for weakest metric
2. Re-run eval, compare before/after
3. Log results in `docs/iteration-log.md`
