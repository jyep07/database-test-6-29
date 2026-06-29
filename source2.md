# Agent AI — Engineering Workflows, Roadmap & Caveats (excerpt)

> **Source document:** `source2.pdf` (internal PDF title: `Agent AI Markdown.pdf`)
> **Document ID:** (not specified)
> **Revision:** (not specified)
> **Classification:** (not specified)
> **Total pages:** 4
> **Page anchors:** PDF page numbers from the source.
> **Figure summaries:** not included
> **Transcribed by:** datasheet-to-markdown skill on 2026-06-29
>
> Throughout this file, `> **Source page N**` markers (and `<!-- page: N -->` comments)
> indicate where each section appears in the source document. The source contains no
> numbered tables or figures. **Note:** page 1 begins mid-sentence and mid-list — this
> PDF is an excerpt of a longer report; earlier pages/sections are not part of the source.

<!-- page: 1 -->
> **Source page 1**

*(continues a bulleted list from a preceding, not-included page — apparently covering Render hosting pricing)*

…hours/workspace/month, free Postgres deleted after 30 days. Always-on starts at **Starter $7/mo per service**; **Private Services** are reachable only within your Render network; implement app-level auth for dashboards. Professional workspace seats are ~$19/user/mo (verify).

- **Vercel** — **Do not use the Hobby (free) tier for company/internal tools — it is explicitly "for personal, non-commercial use only" per Vercel's own pricing/fair-use docs.** Use **Pro at $20/user/mo** for any business app (Viewer seats are free); Pro adds password protection, Enterprise adds SAML SSO.

**How an agent is empowered to deploy:** give the coding agent (a) the repo, (b) a deploy skill (`SKILL.md` capturing the exact build/deploy commands — there's a community `run-skill-generator` pattern that records a working recipe), and (c) scoped credentials via env/secret manager (never in the prompt). For Streamlit/HF/Render, deploy is a git push or CLI call the agent can run behind a permission gate. **Auth for internal-only:** prefer OIDC/SSO against your Google Workspace or Microsoft accounts (Streamlit st.login, or an auth proxy in front of Render/Vercel), or private Spaces under the org.

**Data/visualization for an engineering startup:** keep test/telemetry data in a real store (Postgres/Parquet/S3), not in the app; have the agent build read-only dashboards over it; log who viewed what for traceable engineering practice.

## 7. General productivity & engineering workflows

**What to automate first (highest ROI, lowest risk):**

1. **Documentation & knowledge capture** — agents drafting/maintaining the wiki, meeting notes, runbooks, onboarding guides. Text-heavy, low-risk, immediately useful.
2. **Test-data analysis** — Streamlit/Gradio dashboards over test campaigns; agents writing the analysis/visualization code (with engineers reviewing the analysis). This is the aerospace sweet spot: hot-fire/structural/avionics test data → quick, repeatable, shareable dashboards.
3. **Requirements & traceability** — LLMs are well-suited to requirements work (text-heavy): parsing unstructured docs into structured requirements, flagging ambiguous/untestable language, detecting broken trace links, and change-impact analysis. Industry guidance is explicit: **AI recommends, engineers approve** — route every suggestion through human review. (Tools like trace.space and Altium's requirements portal illustrate the pattern; NVIDIA's HEPH shows agentic test-case generation from requirements.)
4. **Code review & test generation** — agents draft tests and review PRs; humans gate merges.

**Hardware/software co-development specifics:** keep a single deployed source of truth (the wiki) linking requirements ↔ design ↔ test ↔ results; have agents help maintain the trace links and surface coverage gaps during normal work (MBSE-style "sense → reason → act" over the toolchain, engineer-supervised). For test/RL/data pipelines, run agent-generated code in **sandboxes** with coverage tracking.

<!-- page: 2 -->
> **Source page 2**

- Map each workflow step to AI-execution vs. human-decision based on the task (repetitive/data-intensive/measurable → AI; contextual/safety-critical/novel → human).
- Set explicit checkpoints requiring human approval before consequential actions. The Faros AI 2026 data (incidents/PR up 242.7%, unreviewed merges up 31.3% with AI adoption) is the cautionary baseline for why merge gates matter.
- **Instrument everything before optimizing anything:** capture agent traces, build regression datasets from real usage, run evals (LangSmith or similar). The fastest teams "close the loop from production trace to regression dataset."
- Pin model and spec versions; treat AGENTS.md/skills as code (reviewed, versioned); log every agent action; keep secrets out of prompts/skills.

**Move fast without breaking sound engineering:** the discipline that makes the loop work is the documentation architecture (AGENTS.md + skills + deployed wiki) and review gates — not the choice of framework. If/when you need orchestration code, **LangGraph** is the production-standard for stateful, auditable, human-in-the-loop graphs; **CrewAI** is the fastest prototyping path; the **Claude Agent SDK** is the Anthropic-native option (same architecture as Claude Code). But honestly, most "we need agents" tasks are really DAG workflows — don't reach for multi-agent frameworks until a single agent + good tools demonstrably falls short.

# Recommendations (phased summer roadmap)

**Phase 0 — Foundations (Week 1-2):**

- Adopt **AGENTS.md** in every active repo (symlink CLAUDE.md → AGENTS.md); keep each under ~150 lines. Seed with build/test commands, conventions, and gotchas.
- Stand up the **deployed source-of-truth wiki**. Pilot **Notion + Notion MCP** (zero-ops, best agent story) OR **Wiki.js with Git storage** (self-host, literal git versioning). Pick one; don't boil the ocean.
- Pick **one terminal coding agent** to standardize on (Claude Code or Codex) plus optionally a free BYO-key option (Aider/Cline) for cost-sensitive work. Establish the rule: **all agent output is a draft; humans review and merge.**

**Phase 1 — First useful agentic workflows (Week 3-5):**

- Author 3-5 **skills** for recurring tasks (e.g., "generate a test-data dashboard," "summarize uncommitted changes," "draft a requirements review"). Commit them to repos so the whole team gets them.
- Ship **one Streamlit (or Gradio) dashboard** over a real test dataset, deployed to a **private Hugging Face Space** (free, org-private) or **Render Starter ($7/mo)**. Have the coding agent write and deploy it behind a permission gate.
- Stand up the **most useful MCP servers** (GitHub + your wiki/Notion + Postgres) so agents…

<!-- page: 3 -->
> **Source page 3**

**Phase 2 — Expand & harden (Week 6-9):**

- Add **scheduling** (GitHub Actions or a small cron) for one proven workflow (e.g., nightly test-data digest posted to the wiki/Slack).
- Introduce **sandboxing** (E2B or Modal) for any agent that executes generated code; add network egress allowlists and per-task secrets.
- Add **observability/evals** (LangSmith or equivalent): trace agent runs, build a small regression set, gate changes on evals.
- Evaluate one **personal-agent harness** (NanoClaw for security-first, or Hermes for self-improving skills) on a *non-sensitive* always-on automation, in isolation, to learn the pattern.

**Phase 3 — Only if justified (Week 10+):**

- Graduate the best dashboards to production hosting (Dash/Next.js on Render/Vercel Pro) with SSO.
- Consider **multi-agent orchestration** (LangGraph) only for a workflow with proven parallelism/separation-of-duties needs.

**Benchmarks that should change your decisions:**

- If a single agent + good tools + skills reliably ships a class of work → don't add multi-agent complexity.
- If Streamlit's full-script rerun model causes performance/UX pain → move that app to Dash.
- If your free Streamlit private-app limit (one app) or HF/Render idle-sleep blocks real use → move to paid always-on tiers.
- If token/credit cost per accepted change climbs → switch models/tiers or route cheaper models for triage and reserve frontier models for hard tasks.
- If agents start missing earlier instructions → your AGENTS.md is too long; prune it.

# Caveats & things for the intern to validate

- **Pricing and product names change weekly in 2026.** Re-verify every price, tier, and limit against the official page before relying on it. Several tools moved to usage/credit billing (GitHub Copilot June 1 2026; Codex credits; Cursor Teams repricing), and some are in transition (Windsurf → Devin Desktop; Amazon Q Developer → Kiro with new signups blocked from May 15 2026; Gemini CLI legacy tiers retiring June 18 2026).
- **OpenClaw, NanoClaw, and Hermes Agent are fast-moving open-source projects.** Treat them as experimental; audit the code and security model before granting access to company data or systems. NanoClaw's container isolation and Hermes' self-hosting are points in their favor; OpenClaw's large application-level-security codebase is a point of caution.
- **"Hermes"** as a standalone coding tool could not be reliably distinguished from Nous Research's **Hermes Agent** (and the separate Hermes open-weight LLMs). Confirm which was [intended]. *[text continues on next page]*

<!-- page: 4 -->
> **Source page 4**

- **Material for MkDocs is in maintenance mode (Nov 2025).** If choosing docs-as-code, prefer Docusaurus or confirm MkDocs Material's status before standardizing.
- **Skills and MCP servers are prompt-injection / supply-chain vectors.** Only use skills and MCP servers from trusted sources; many community MCP servers lack auth and conformance testing.
- **MCP token overhead** can be large vs. direct CLI/API calls; for high-volume production pipelines benchmark before committing to MCP everywhere.
- **Claude Code does not natively read AGENTS.md** as of early 2026 — use the symlink workaround and re-check whether native support has shipped.
- The Streamlit "3 free apps per user" figure circulating in third-party blogs is **unverified against official docs**; the confirmed official constraint is one private (auth-configured) app per workspace. Verify current limits before standardizing.
- This report prioritizes breadth and starting points over deep implementation detail by design; the intern should write detailed step-by-step instructions for whichever 2-3 items the team commits to [text truncated at end of source page 4 — source page 4]
