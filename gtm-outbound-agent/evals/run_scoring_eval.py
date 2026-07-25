"""Day 10 scoring eval: does the agent rank companies like the ICP says it should?

Two metrics:

  spearman   Rank correlation between the agent's overall score and the hand-assigned
             band ordinal (none=0, weak=1, strong=2). Rank correlation, not exact-value
             error, because the labels are ordinal bands — we care that strong outranks
             weak outranks none, not that a "strong" hits some specific number. DoD gate: > 0.6.

  confusion  3x3 matrix of predicted band vs gold band, from thresholding the overall
             score. Shows *where* it fails (e.g. weak->strong optimism) which a single
             correlation number hides.

Both need live model scores, so both are gated: with no API key the run reports gold-set
readiness and emits `not measured`, never a fabricated correlation (same discipline as
the Day-9 enrichment eval).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from gtm_outbound.agents.scoring_agent import score  # noqa: E402
from scoring_gold import BAND_ORDINAL, GOLD  # noqa: E402

# Score thresholds that map an overall score to a band. Tunable; documented so a change
# is a decision, not a silent drift. Chosen to bracket the 0.5 midpoint asymmetrically:
# "strong" should require clearly-above-midpoint evidence.
STRONG_MIN = 0.65
WEAK_MIN = 0.40


def band_for_score(s: float) -> str:
    if s >= STRONG_MIN:
        return "strong"
    if s >= WEAK_MIN:
        return "weak"
    return "none"


def _rank(values: list[float]) -> list[float]:
    """Average ranks (ties share the mean of the ranks they span)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1  # 1-based average rank across the tie group
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(a: list[float], b: list[float]) -> Optional[float]:
    n = len(a)
    if n == 0:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    da = [x - ma for x in a]
    db = [y - mb for y in b]
    num = sum(x * y for x, y in zip(da, db))
    den = (sum(x * x for x in da) * sum(y * y for y in db)) ** 0.5
    if den == 0:
        return None  # a constant series has no correlation; don't fake one
    return num / den


def spearman(x: list[float], y: list[float]) -> Optional[float]:
    """Spearman rho = Pearson on the average-ranked series."""
    if len(x) != len(y) or not x:
        return None
    return _pearson(_rank(x), _rank(y))


def confusion(pred_bands: list[str], gold_bands: list[str]) -> dict[str, dict[str, int]]:
    bands = ["strong", "weak", "none"]
    m = {g: {p: 0 for p in bands} for g in bands}
    for p, g in zip(pred_bands, gold_bands):
        m[g][p] += 1
    return m


def run_eval(
    client: Any = None,
    icp_provider: Any = None,
    offline: bool = False,
) -> dict:
    counts = {"strong": 0, "weak": 0, "none": 0}
    for band, _ in GOLD:
        counts[band] += 1

    if offline or (client is None and not _has_key()):
        return {
            "mode": "offline",
            "total_rows": len(GOLD),
            "band_counts": counts,
            "spearman": None,
            "accuracy": None,
            "confusion": None,
            "note": (
                "Offline: no scoring executed. "
                f"{len(GOLD)} labeled companies ready "
                f"({counts['strong']} strong / {counts['weak']} weak / {counts['none']} none)."
            ),
        }

    if icp_provider is None:
        from gtm_outbound.icp import KBICPProvider

        icp_provider = KBICPProvider()

    scores: list[float] = []
    gold_ord: list[float] = []
    pred_bands: list[str] = []
    gold_bands: list[str] = []
    rows: list[dict] = []
    errors = 0

    for band, profile in GOLD:
        try:
            fit = score(profile, icp_provider=icp_provider, client=client)
        except Exception as e:
            errors += 1
            rows.append({"domain": profile.target.domain, "error": f"{type(e).__name__}: {e}"})
            continue
        pred = band_for_score(fit.score)
        scores.append(fit.score)
        gold_ord.append(float(BAND_ORDINAL[band]))
        pred_bands.append(pred)
        gold_bands.append(band)
        rows.append({
            "domain": profile.target.domain, "gold": band, "predicted": pred,
            "score": round(fit.score, 4), "cited_signals": fit.cited_signals,
        })

    rho = spearman(scores, gold_ord)
    acc = (
        sum(1 for p, g in zip(pred_bands, gold_bands) if p == g) / len(pred_bands)
        if pred_bands else None
    )
    return {
        "mode": "full",
        "total_rows": len(GOLD),
        "scored_rows": len(scores),
        "errored_rows": errors,
        "band_counts": counts,
        "spearman": round(rho, 4) if rho is not None else None,
        "accuracy": round(acc, 4) if acc is not None else None,
        "confusion": confusion(pred_bands, gold_bands) if pred_bands else None,
        "rows": rows,
    }


def _has_key() -> bool:
    import os

    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def format_report(r: dict) -> str:
    def fmt(v: Any) -> str:
        return "not measured" if v is None else str(v)

    lines = [
        "# Scoring Eval — ICP Fit Agent",
        "",
        f"**Mode:** `{r['mode']}`  ",
        f"**Labeled companies:** {r['total_rows']} "
        f"({r['band_counts']['strong']} strong / {r['band_counts']['weak']} weak / "
        f"{r['band_counts']['none']} none)",
        "",
    ]

    if r["spearman"] is None:
        lines += [
            "> **Not measured.** Scoring needs a live model call and no `ANTHROPIC_API_KEY`",
            "> was present, so no correlation is reported. The 15-company labeled set is",
            "> ready; set the key and re-run. Correlation/confusion below stay `not measured`",
            "> rather than showing a fabricated number.",
            "",
        ]

    gate = ""
    if r["spearman"] is not None:
        gate = "  ✅ (> 0.6)" if r["spearman"] > 0.6 else "  ❌ (DoD gate is > 0.6)"

    lines += [
        "| Metric | Value | DoD gate |",
        "|---|---|---|",
        f"| Spearman rank correlation | {fmt(r['spearman'])}{gate} | > 0.6 |",
        f"| 3-band accuracy | {fmt(r.get('accuracy'))} | — |",
        "",
    ]

    if r.get("confusion"):
        lines += ["## Confusion (rows = gold, cols = predicted)", "",
                  "| gold ↓ / pred → | strong | weak | none |", "|---|---|---|---|"]
        for g in ("strong", "weak", "none"):
            row = r["confusion"][g]
            lines.append(f"| {g} | {row['strong']} | {row['weak']} | {row['none']} |")
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate the scoring agent.")
    ap.add_argument("--offline", action="store_true",
                    help="report gold-set readiness only; run no scoring")
    args = ap.parse_args()

    results = run_eval(offline=args.offline)
    out = Path(__file__).parent
    (out / "scoring_report.md").write_text(format_report(results), encoding="utf-8")

    print(f"mode={results['mode']}  companies={results['total_rows']}")
    print(f"  spearman   {results['spearman'] if results['spearman'] is not None else 'not measured'}")
    print(f"  accuracy   {results.get('accuracy')}")
    print(f"\nreport -> {out / 'scoring_report.md'}")


if __name__ == "__main__":
    main()
