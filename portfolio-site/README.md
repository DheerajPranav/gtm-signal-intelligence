# Portfolio Site — Dheeraj Pranav

**Live:** https://dheerajpranav.github.io/gtm-signal-intelligence/

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

## Deploy — GitHub Pages (current)

Configured for static export as a **project page**, served under
`/gtm-signal-intelligence/` (see `next.config.ts`: `output: "export"` + `basePath`).
To redeploy after changing the site:

```bash
npm run build                     # -> ./out (static export, assets prefixed with basePath)
touch out/.nojekyll               # so Pages serves the _next/ folder
cd out && git init -q && git checkout -b gh-pages && git add -A \
  && git -c user.name="Dheeraj Pranav" -c user.email="krovvididheeraj@gmail.com" \
     commit -qm "deploy" \
  && git push -f https://github.com/DheerajPranav/gtm-signal-intelligence.git gh-pages
```

Pages is enabled from the `gh-pages` branch (root). First build takes ~1 min.

**Alternative — Vercel:** import the repo, set **Root Directory** = `portfolio-site`
(remove the `basePath` first, since Vercel serves at the domain root).

## Before sharing widely

- **Confirm the LinkedIn URL** in `src/app/page.tsx` (`LINKS.linkedin` is a `// TODO` placeholder), then redeploy.
- **Fill the CV placeholders** — Experience + Education in `public/cv.html`, regenerate `cv.pdf` (headless Chrome `--print-to-pdf`), and redeploy.
- Optional: add a screenshot/GIF of the dashboard.

All content numbers are computed from the actual test suites and eval artifacts — no live
quality metric is claimed, matching the sprint's honesty rule.
