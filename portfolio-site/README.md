# Portfolio Site — Dheeraj Pranav

A single-page portfolio for the GTM AI engineering sprint, built with **Next.js 16
(App Router) + Tailwind v4 + TypeScript**. Statically prerendered — no server, no
database, no API keys. Fully mobile-responsive and dark-mode aware.

## Sections

- **Hero** — name, one-liner ("GTM AI Engineer building auditable agents"), links to GitHub, LinkedIn, email.
- **Stats** — 347 hermetic tests · $0.00 live spend · 4 capabilities · 0 fabricated metrics (all computed, honest numbers).
- **Featured work** — the four sprint projects (Outbound Agent, Knowledge Base, Agent Evals, CLI Warmup), each linking to its subfolder in the monorepo.
- **How I think about GTM AI** — short essay on grounding, computed gates, and `not measured` over fabrication.
- **Contact** — email + LinkedIn CTA.

## Develop

```bash
npm install
npm run dev      # http://localhost:3000
npm run build    # production build (verified passing)
```

## Deploy to Vercel

The repo is a monorepo, so point Vercel at this subdirectory:

1. Import `github.com/DheerajPranav/gtm-signal-intelligence` in Vercel.
2. Set **Root Directory** = `portfolio-site`.
3. Framework preset auto-detects **Next.js**; no env vars needed.
4. Deploy → attach a custom domain if desired.

## Before publishing

- **Confirm the LinkedIn URL** in `src/app/page.tsx` (`LINKS.linkedin` is a `// TODO` placeholder).
- Optional: add `public/cv.pdf` and a screenshot/GIF of the dashboard per the sprint plan.

All content numbers are computed from the actual test suites and eval artifacts — no live
quality metric is claimed, matching the sprint's honesty rule.
