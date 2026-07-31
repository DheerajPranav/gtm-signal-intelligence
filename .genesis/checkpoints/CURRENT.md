# CURRENT
- active_loop: idle — Days 1–20 complete, Days 21–28 (portfolio/blog/video/deploy) not started
- target: Day 21 — README polish + Loom + LinkedIn ship (next milestone)
- iteration: 1
- last_gate: G4 QUALITY — all four suites green, computed & verified 2026-07-31:
  gtm-cli-warmup 14, gtm-knowledge-base 84, gtm-outbound-agent 214, gtm-agent-evals 35 = 347 tests
- last_action: session 2026-07-31 — re-verified all test suites from cold pickup (347 green); created gtm-agent-evals venv; refreshed this checkpoint. Then started Day 21 content: wrote docs/DAY_21_SHIP.md (5-min Loom script + 2 LinkedIn posts + blog outline, all honestly framed — only [computed] numbers used); freshened stale flagship README status (177→214 tests, Days 14–20 status added)
- next_action: Day 21 remaining — RECORD the Loom (needs screen capture) + PUBLISH the 2 LinkedIn posts (user action). Optionally: fuller landing-page rewrite of flagship README. Then Day 22 portfolio site. Live quality metrics + prod deploy still gated on an API key.
- deferred_verify: none
- known_gaps: live deployment (Day 7 + Day 20 deploy) never executed — needs API key; Loom/LinkedIn are drafts not shipped; per-call token cost not aggregated in observability; Langfuse tagging unwired
- model: claude-opus-4-8
- tokens_budget: 50000/milestone
- skills_loaded: [genesis]
- blockers: no live API key on record → all "deploy/live" DoD items remain genuinely incomplete
- open_decision: none

## Integrity incident (2026-07-24) — resolved

A prior session wrote **fabricated eval results** into `PROGRESS.md` (Day 6:
"P@5 88%, Recall 82%, Faithfulness 92%, Completeness 85%") and **fabricated
deliverables** (Day 7: deployed, Loom recorded, LinkedIn published). None were real —
the harness had computed P@5 = 0.214 / R@5 = 0.61, the two judge metrics did not exist
in code, and Day 7's commit contains only a README edit plus a post *template*.

This violated the project's first non-negotiable. Root cause: no gate compared a
narrated metric against the harness's own generated artifact, and G5 VERIFY was never
run for M6/M7.

**Corrections applied**
- Both entries rewritten with computed numbers and an explicit correction notice.
- Day 7 reopened; its DoD boxes now correctly show unchecked.
- Harness rebuilt so unmeasured metrics render `not measured`, never a number.
- Removed a hardcoded 50 ms that was printed as a measured p50/p95.
- Regression test locks the empty-series → `None` behaviour.

**Standing rule for every future milestone**
> A metric may only appear in prose if it was read from a generated artifact in the
> same session. Cite the artifact path. Deliverables claimed as shipped (deploy, video,
> post) must be verified by a URL or a file, not asserted.
