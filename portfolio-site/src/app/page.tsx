// Portfolio — Dheeraj Pranav. Static Server Component (no client JS needed).
// Update LINKS.linkedin once the profile URL is confirmed.

const LINKS = {
  github: "https://github.com/DheerajPranav",
  repo: "https://github.com/DheerajPranav/gtm-signal-intelligence",
  linkedin: "https://www.linkedin.com/in/dheerajpranav", // TODO: confirm exact vanity URL
  email: "krovvididheeraj@gmail.com",
  cv: "/cv.pdf",
};

type Project = {
  name: string;
  tagline: string;
  bullets: string[];
  metric: string;
  href: string;
};

const PROJECTS: Project[] = [
  {
    name: "GTM Outbound Agent",
    tagline: "Flagship · five-agent, source-grounded outbound",
    bullets: [
      "Research → Score → Persona → Write → Critique, chained into a deterministic Account Brief",
      "Sourced profiles (every field carries its URL) + injection-fenced web content",
      "Async fan-out (3 angles × 3 personas) behind one shared semaphore; a skeptical Haiku judge",
    ],
    metric: "214 hermetic tests",
    href: `${LINKS.repo}/tree/main/gtm-outbound-agent`,
  },
  {
    name: "GTM Knowledge Base",
    tagline: "Hybrid RAG with cited answers + a golden eval set",
    bullets: [
      "BM25 + vector retrieval via Reciprocal Rank Fusion, Haiku reranker, Sonnet answers with inline citations",
      "30-doc internally-consistent corpus so every answer is groundable",
      "35-question golden eval set with a computed retrieval baseline",
    ],
    metric: "74% hit@5 · 61% recall@5 · 84 tests",
    href: `${LINKS.repo}/tree/main/gtm-knowledge-base`,
  },
  {
    name: "GTM Agent Evals",
    tagline: "Open-source, framework-agnostic rubric kit (MIT)",
    bullets: [
      "Reusable ICP / Persona / Email / Critique rubrics with deterministic gates",
      "LangChain, external-dataset, and Streamlit integration examples",
      "Zero framework coupling; works standalone or embedded in any LLM system",
    ],
    metric: "35 tests · MIT licensed",
    href: `${LINKS.repo}/tree/main/gtm-agent-evals`,
  },
  {
    name: "GTM CLI Warmup",
    tagline: "Structured-extraction primitives",
    bullets: [
      "Typed company/lead extraction via forced tool use — never string-parsing model text",
      "Recursively-closed strict schemas so the model can't invent fields",
      "Real cost / latency / token logging from the first LLM call",
    ],
    metric: "14 tests",
    href: `${LINKS.repo}/tree/main/gtm-cli-warmup`,
  },
];

const STATS = [
  { value: "347", label: "hermetic tests" },
  { value: "$0.00", label: "live API spend to date" },
  { value: "4", label: "shipped capabilities" },
  { value: "0", label: "fabricated metrics" },
];

function Icon({ path }: { path: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className="h-4 w-4"
      fill="currentColor"
    >
      <path d={path} />
    </svg>
  );
}

const ICONS = {
  github:
    "M12 .5C5.7.5.5 5.7.5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.3.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.8 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0C17 4.6 18 4.9 18 4.9c.6 1.6.2 2.8.1 3.1.8.8 1.2 1.8 1.2 3.1 0 4.5-2.7 5.5-5.3 5.8.4.3.8 1 .8 2.1v3.1c0 .3.2.7.8.6 4.6-1.5 7.9-5.8 7.9-10.9C23.5 5.7 18.3.5 12 .5z",
  linkedin:
    "M20.5 2h-17A1.5 1.5 0 0 0 2 3.5v17A1.5 1.5 0 0 0 3.5 22h17a1.5 1.5 0 0 0 1.5-1.5v-17A1.5 1.5 0 0 0 20.5 2zM8 19H5V9h3v10zM6.5 7.7a1.7 1.7 0 1 1 0-3.4 1.7 1.7 0 0 1 0 3.4zM19 19h-3v-5.3c0-1.3-.5-2.1-1.6-2.1-.9 0-1.4.6-1.6 1.2-.1.2-.1.5-.1.8V19h-3V9h3v1.4a3 3 0 0 1 2.7-1.5c2 0 3.4 1.3 3.4 4.1V19z",
  mail: "M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4-8 5-8-5V6l8 5 8-5v2z",
  doc: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm0 2 4.5 4.5H14V4zM8 13h8v1.5H8V13zm0 3h8v1.5H8V16zm0-6h4v1.5H8V10z",
};

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-16 sm:py-24">
      {/* Hero */}
      <section className="max-w-3xl">
        <p className="font-mono text-sm text-emerald-600 dark:text-emerald-400">
          GTM AI Engineer
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-6xl">
          Dheeraj Pranav
        </h1>
        <p className="mt-6 text-xl leading-relaxed text-black/70 dark:text-white/70 sm:text-2xl">
          I build <span className="text-foreground font-semibold">auditable</span> GTM
          AI — agents where every claim is sourced, every capability has a computed
          gate, and unmeasured stays unmeasured.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href={LINKS.repo}
            className="inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-2.5 text-sm font-medium text-background transition hover:opacity-90"
          >
            <Icon path={ICONS.github} /> View the code
          </a>
          <a
            href={LINKS.linkedin}
            className="inline-flex items-center gap-2 rounded-full border border-black/15 px-5 py-2.5 text-sm font-medium transition hover:bg-black/5 dark:border-white/20 dark:hover:bg-white/10"
          >
            <Icon path={ICONS.linkedin} /> LinkedIn
          </a>
          <a
            href={`mailto:${LINKS.email}`}
            className="inline-flex items-center gap-2 rounded-full border border-black/15 px-5 py-2.5 text-sm font-medium transition hover:bg-black/5 dark:border-white/20 dark:hover:bg-white/10"
          >
            <Icon path={ICONS.mail} /> Email
          </a>
          <a
            href={LINKS.cv}
            className="inline-flex items-center gap-2 rounded-full border border-black/15 px-5 py-2.5 text-sm font-medium transition hover:bg-black/5 dark:border-white/20 dark:hover:bg-white/10"
          >
            <Icon path={ICONS.doc} /> Résumé
          </a>
        </div>
      </section>

      {/* Stats */}
      <section className="mt-16 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-black/10 bg-black/10 dark:border-white/10 dark:bg-white/10 sm:grid-cols-4">
        {STATS.map((s) => (
          <div key={s.label} className="bg-background p-6 text-center">
            <div className="text-3xl font-bold tracking-tight sm:text-4xl">
              {s.value}
            </div>
            <div className="mt-1 text-xs text-black/60 dark:text-white/60">
              {s.label}
            </div>
          </div>
        ))}
      </section>

      {/* Projects */}
      <section className="mt-20">
        <h2 className="text-2xl font-bold tracking-tight">Featured work</h2>
        <p className="mt-2 text-black/60 dark:text-white/60">
          A 4-week applied-AI sprint, built against one fixed fictional world so every
          claim is groundable and every capability is measurable.
        </p>
        <div className="mt-8 grid gap-6 sm:grid-cols-2">
          {PROJECTS.map((p) => (
            <a
              key={p.name}
              href={p.href}
              className="group flex flex-col rounded-2xl border border-black/10 bg-black/[0.02] p-6 transition hover:border-emerald-500/50 hover:bg-black/[0.04] dark:border-white/10 dark:bg-white/[0.02] dark:hover:bg-white/[0.04]"
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-lg font-semibold">{p.name}</h3>
                <span
                  aria-hidden="true"
                  className="text-black/30 transition group-hover:translate-x-0.5 group-hover:text-emerald-500 dark:text-white/30"
                >
                  ↗
                </span>
              </div>
              <p className="mt-1 font-mono text-xs text-emerald-600 dark:text-emerald-400">
                {p.tagline}
              </p>
              <ul className="mt-4 flex-1 space-y-2 text-sm text-black/70 dark:text-white/70">
                {p.bullets.map((b, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-emerald-500" />
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-5 inline-flex w-fit rounded-full bg-emerald-500/10 px-3 py-1 font-mono text-xs text-emerald-700 dark:text-emerald-300">
                {p.metric}
              </div>
            </a>
          ))}
        </div>
      </section>

      {/* Essay */}
      <section className="mt-20 max-w-3xl">
        <h2 className="text-2xl font-bold tracking-tight">
          How I think about GTM AI
        </h2>
        <div className="mt-6 space-y-4 text-black/75 dark:text-white/75">
          <p>
            Most GTM AI demos fall apart on one question: <em>how do you know the
            output is any good before it reaches a customer?</em> The interesting
            engineering isn&apos;t the model call — it&apos;s the machinery that makes
            the answer trustworthy.
          </p>
          <p>
            So I build grounding in structurally, not through prompting. The research
            agent returns values that each carry the URL they came from, and a
            deterministic check fails any citation to a page it never actually fetched.
            Scores are computed in code from model-rated dimensions, so a headline
            number can never contradict its own breakdown. The judge that grades emails
            is skeptical by construction — a judge that says yes to everything measures
            nothing.
          </p>
          <p>
            And when there&apos;s no way to measure something honestly, the system says
            <span className="font-mono"> not measured</span> — never a placeholder
            number. Every capability here ships behind an offline, deterministic gate
            before a single live API call, which is why live spend to date is still
            $0.00. If it wasn&apos;t evaluated, it doesn&apos;t count.
          </p>
        </div>
      </section>

      {/* Contact */}
      <section className="mt-20 rounded-2xl border border-black/10 bg-black/[0.02] p-8 dark:border-white/10 dark:bg-white/[0.02] sm:p-12">
        <h2 className="text-2xl font-bold tracking-tight">Let&apos;s talk</h2>
        <p className="mt-3 max-w-xl text-black/70 dark:text-white/70">
          Open to GTM AI engineering and forward-deployed roles. The fastest way to
          reach me is email or LinkedIn.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <a
            href={`mailto:${LINKS.email}`}
            className="inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-2.5 text-sm font-medium text-background transition hover:opacity-90"
          >
            <Icon path={ICONS.mail} /> {LINKS.email}
          </a>
          <a
            href={LINKS.linkedin}
            className="inline-flex items-center gap-2 rounded-full border border-black/15 px-5 py-2.5 text-sm font-medium transition hover:bg-black/5 dark:border-white/20 dark:hover:bg-white/10"
          >
            <Icon path={ICONS.linkedin} /> Connect on LinkedIn
          </a>
        </div>
      </section>

      <footer className="mt-20 border-t border-black/10 pt-8 text-sm text-black/50 dark:border-white/10 dark:text-white/50">
        <p>
          Built by Dheeraj Pranav. Northstar Analytics — the world these systems are
          grounded in — is entirely fictional and labelled as such throughout.
        </p>
        <p className="mt-2 font-mono text-xs">Stay curious, stay disciplined.</p>
      </footer>
    </main>
  );
}
