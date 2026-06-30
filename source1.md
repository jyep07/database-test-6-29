# Agent AI Markdown

> **Source document:** `source1.pdf`
> **Document ID:** (not specified)
> **Revision:** (not specified)
> **Classification:** (not specified)
> **Total pages:** 1
> **Page anchors:** PDF page numbers from the source.
> **Figure summaries:** not included
> **Transcribed by:** datasheet-publisher (datasheet-to-markdown skill) on 2026-06-30
>
> Throughout this file, `> **Source page N**` markers (and `<!-- page: N -->` comments)
> indicate where each section appears in the source document. The source page begins
> mid-sentence (the opening clause continues from material that precedes this page and
> is not part of the supplied file).

<!-- page: 1 -->
> **Source page 1**

…delegate, review, own — engineers move from writing code to orchestrating, reviewing,
and validating.

## 2. Deploying agents: local → cloud → hybrid, safely

**Lightweight starting points (intern can own):**

- **Local/terminal agents** (Claude Code, Codex CLI, Aider, Cline) run on the developer's
  machine, edit files, and run commands with permission gates. No infrastructure. This is
  where to start.
- **Hosted/async agents** (Codex cloud, Devin, Jules) run tasks in remote sandboxes and
  return PRs — good for parallel, well-defined tasks.

**Scheduling/triggering.** Cron-style scheduling is built into the personal-agent harnesses
(OpenClaw, NanoClaw, Hermes all ship schedulers), or use GitHub Actions for repo-triggered
agent runs, or a small cloud cron. Start with manual/triggered runs; add schedules once a
workflow is proven.

**Sandboxing & security (critical for autonomy).** Standard containers share the host kernel
and are **not** considered a sufficient isolation boundary for agent-executed code in 2026.
The consensus stack: **microVMs (Firecracker, Kata Containers)** for untrusted/regulated
code, **gVisor** for compute-heavy multi-tenant, plain containers only for trusted code. Per
the OWASP Top 10 for Agentic Applications (published December 9, 2025), item ASI05
(Unexpected Code Execution) requires: "Never execute agent-generated code without strict
sandboxing, input validation, and allowlisting," using "isolated containers with no network
access and minimal system privileges." Real CVEs in 2025-2026 (e.g., the Antigravity sandbox
escape) demonstrate the risk. Lightweight managed sandbox options: E2B (open-source,
Firecracker), Modal (gVisor), Vercel Sandbox, Cloudflare, Northflank, Daytona.

**Practical guardrails:** network egress allowlists; workspace write restrictions (especially
dotfiles/config dirs); per-task secrets (never bake credentials into prompts or skills);
least-privilege tool scoping; and **a registry/log of every agent and every action**.
NanoClaw's design (each agent in its own Linux container, credentials via a vault so the
agent never holds raw API keys, rate limits like "3 email deletions/hour") is a good model
for the mindset.

**Cost.** Agents bill like compute jobs, not seats — the number to watch is **cost per
accepted change**, not sticker price. Token efficiency varies widely: in developer Ian
Nuttall's widely-cited benchmark (via Builder.io, 2026), Claude Code (Opus) completed a
multi-file Next.js/Tailwind/shadcn task in ~33,000 tokens with zero errors, while Cursor's
agent (GPT-5) used ~188,000 tokens and hit errors along the way — a ~5.5x token gap.
CLI/direct-API tool calls can be dramatically cheaper than equivalent MCP calls in tokens,
so for high-volume production pipelines prefer direct calls; use MCP for convenience and
breadth.

## 3. Skills: giving and sharing reusable capabilities

*(Section heading appears at the foot of source page 1; its body content is not present on
this page of the supplied file.)*
