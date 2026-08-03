# CURRENT
- active_loop: idle — Days 1–20 complete, Days 21–28 (portfolio/blog/video/deploy) not started
- target: Days 21–26 done (ship content, portfolio LIVE, blog, CV, eval-kit runner + comparison + launch thread) → Days 27–28 next (launch + cold outreach + live backend deploy)
- iteration: 1
- last_gate: G4 QUALITY — all four suites green: gtm-cli-warmup 14, gtm-knowledge-base 84,
  gtm-outbound-agent 214, gtm-agent-evals 55 (+16 runner Day 25, +4 comparison Day 26) = 367 tests
- last_action: session 2026-07-31 — re-verified all test suites from cold pickup (347 green); created gtm-agent-evals venv; refreshed this checkpoint. Then started Day 21 content: wrote docs/DAY_21_SHIP.md (5-min Loom script + 2 LinkedIn posts + blog outline, all honestly framed — only [computed] numbers used); freshened stale flagship README status (177→214 tests, Days 14–20 status added)
- next_action: Days 27–28 MATERIALS drafted (code work done): docs/launch/LAUNCH_CHECKLIST.md (LinkedIn long-form, community posts, DM + 4-line cold-outreach templates, target buckets), docs/launch/outreach-tracker.csv, docs/DEPLOY.md (Modal + Neon + Streamlit guide), gtm-outbound-agent/deploy/modal_app.py (syntax-checked template). Execution is USER-only: post thread/LinkedIn/communities, send DMs + 20+ outreaches, record Loom, publish blog, run the live Modal/Neon deploy (needs their accounts + API key), write retrospective. Sprint code work is effectively COMPLETE (Days 1–26 shipped + 27–28 drafted). PRIOR: Day 26 done — eval-kit polish: great-vs-templated email comparison (examples/email_comparison.py + .ipynb, key-aware LLM scorer w/ offline illustrative fallback; rubric separates 5/5 great vs 0/5 templated, spam-gap +2.1), +4 tests (55 total); Twitter launch thread in docs/launch/twitter-thread.md; CONTRIBUTING extended (fixtures/calibration checklist). Next dev-able: Days 27–28 are launch/outreach/deploy — mostly USER actions (post thread + LinkedIn, cold outreach) or gated on API key/hosting (live backend deploy). PRIOR: Day 25 done — eval-kit differentiator: deterministic `gtm-evals run` CLI (cli.py + __main__.py + console script), 5-good/5-bad JSONL fixtures per rubric (examples/data/), calibration notes (docs/CALIBRATION.md), +16 tests (51 total), version 0.2.0. Next dev task: Day 26 — comparison notebook + Twitter/X launch thread (docs/launch/twitter-thread.md). Prior: Days 21–24 content all done & committed. Day 24: one-page CV generated as portfolio-site/public/cv.pdf (via headless Chrome from cv.html; honest metrics, personal-history sections are marked placeholders), linked from the portfolio (Résumé button, build re-verified); LinkedIn overhaul copy in docs/DAY_24_LINKEDIN.md. All progress docs refreshed (README 24/28, STATUS addendum). USER actions pending: record Loom, publish 2 LinkedIn posts + blog, deploy portfolio to Vercel, confirm LinkedIn URL, fill CV Experience/Education placeholders. Next dev task: Day 25 (eval-kit polish — the differentiator package).
- deferred_verify: none
- known_gaps: PORTFOLIO now LIVE on GitHub Pages (https://dheerajpranav.github.io/gtm-signal-intelligence/, gh-pages branch, redeploy steps in portfolio-site/README). Still gated on API key: flagship live quality metrics + backend deploy (Modal). Loom/LinkedIn/blog are drafts not yet published; CV Experience/Education are placeholders; per-call token cost not aggregated; Langfuse tagging unwired
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
