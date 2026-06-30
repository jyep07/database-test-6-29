---
name: datasheet-publisher
description: >-
  Convert an uploaded PDF or Word document into a clean markdown transcription
  (via the datasheet-to-markdown skill) and then PUBLISH that markdown to a
  GitHub repository, a Google Drive folder, or both — asking the user which
  destination(s) they want when the request doesn't already say. Use this
  whenever someone uploads a spec, datasheet, ICD,
  report, or similar PDF/Word file and wants it not just converted but also
  pushed somewhere — e.g. "convert this and commit it to our repo", "transcribe
  this datasheet and put it in the team Drive folder", "turn this into markdown
  and publish it to GitHub and Drive". Trigger this (rather than
  datasheet-to-markdown on its own) whenever the request names a destination —
  a GitHub repo/owner/branch/path or a Google Drive folder — alongside the
  conversion. The repo and folder are supplied per run; GitHub uses existing
  git/gh credentials when present (e.g. in Claude Code) and falls back to a
  token only in a bare sandbox; Drive uses the connector.
---

# Datasheet Publisher

A pipeline: take one uploaded PDF/Word document, transcribe it to markdown, then
publish that single markdown file to wherever the user wants it — a GitHub repo,
a Google Drive folder, or both. The transcription itself is delegated to the
`datasheet-to-markdown` skill so this skill stays focused on the publishing half.

The mental model to keep: there is exactly **one** artifact — the `.md` file. It
is always created (conversion), then published to whichever destination(s) the
user chose — a GitHub commit, a Google Drive copy, or both. Always keep the local
copy in `/mnt/user-data/outputs/` too, so the user walks away with the file even
if a chosen destination fails.

## What the user provides each run

Collect these from the conversation; ask only for what's genuinely missing.

- **Which destination(s)** — GitHub, Google Drive, or both. If the request
  already says (e.g. "put it in my Drive folder" → Drive only; "commit to repo X
  *and* Drive folder Y" → both), honor that and don't re-ask. **If it isn't
  clear, ask before publishing** — one short question: "Where should this go —
  GitHub, Google Drive, or both?" Only gather the inputs below for the
  destination(s) actually chosen.
- **The source file** — a PDF or Word doc, usually in `/mnt/user-data/uploads/`.
- **The target repo** *(GitHub only)* — `owner/name`. Optionally a `branch`
  (default: the repo's default branch) and a `path` inside the repo (default: the
  markdown filename at the repo root; if they mention a folder like `docs/specs/`,
  put it there).
- **GitHub auth** *(GitHub only)* — usually nothing to ask for: if the
  environment already has `gh`/git credentials (the normal Claude Code case), use
  those. Only when there are none (a bare sandbox) do you need a token. See the
  GitHub step and "GitHub auth".
- **GitHub folder** - if user wants the file in GitHub repo, ask for where in the repo
  it should be placed (e.g. in a distinct folder).
- **The Google Drive folder** *(Drive only)* — a folder name, or a Drive link/ID.

If something's missing, ask for it plainly rather than guessing — committing to
the wrong repo or folder is worse than a one-line question. The exception is the
defaults above (branch, path, filename), which are safe to assume and mention.

Only PDF and Word are in scope, because that's what `datasheet-to-markdown`
handles. If the upload is a spreadsheet or anything else, say so and stop rather
than producing a low-quality transcription.

## Workflow

### 1. Decide the destination(s)

Before publishing, know where the file is going: **GitHub, Google Drive, or
both.** If the user's request already specifies it, honor that and don't re-ask.
If it's ambiguous, ask one short question — "Where should this go — GitHub,
Google Drive, or both?" — and wait for the answer before doing any publishing.
The conversion (next step) happens regardless of the choice; only the publish
steps are gated on it. Gather destination-specific inputs (repo/folder) only for
what was chosen.

### 2. Convert the document to markdown

Locate the uploaded file, then hand the conversion to the `datasheet-to-markdown`
skill: read its `SKILL.md` (typically under `/mnt/skills/.../datasheet-to-markdown/`)
and follow its workflow exactly. It writes the result to
`/mnt/user-data/outputs/<source-stem>.md` and that file is the artifact every
later step operates on.

Pass through the figure-summary preference: if the user asked for figure/diagram
summaries, run that skill with summaries ON; otherwise leave them off (its
default). Don't add anything to the markdown beyond what that skill produces —
the value of the transcription is that it's faithful and citable.

After conversion, note the exact output path and the stem (e.g.
`atlas-2-icd.md`); you'll reuse it as the default GitHub path and Drive title.

### 3. Commit the markdown to GitHub *(only if GitHub was chosen)*

Skip this entire step if the user chose Drive only. Otherwise: there are two ways
to authenticate, and the right one depends on the
environment. **Check for ambient credentials first** — when they exist (the
normal case in Claude Code on a developer's machine), you don't need a token at
all, and asking for one is needless friction.

**Path A — use existing git/`gh` credentials (preferred where available).**
Probe with `gh auth status` (and/or `git config --get remote.origin.url` if a
repo is already checked out). If `gh` is authenticated or the machine has git
credentials configured, just use plain git — no PAT:

```bash
# If the target repo is already the working directory, skip the clone.
gh repo clone <owner/name> /tmp/repo 2>/dev/null || git clone https://github.com/<owner/name>.git /tmp/repo
mkdir -p "$(dirname /tmp/repo/<in-repo path>)"
cp /mnt/user-data/outputs/<stem>.md /tmp/repo/<in-repo path>
cd /tmp/repo
git switch <branch> 2>/dev/null || true   # omit to stay on the default branch
git add <in-repo path>
git commit -m "<commit message>"
git push
```

`gh`/git inject auth for you, so nothing secret is passed around. This is what
the user means by "Claude Code connects to the repo" — it's leaning on `gh` and
the local credential helper, not a token baked into the skill.

**Path B — no git identity present (bare sandbox).** Some environments have no
`gh`, no SSH key, and no credential helper — only network access to
`api.github.com` (this is the case in the plain Claude.ai container). There, fall
back to the bundled script, which commits one file via the REST Contents API and
handles the fiddly part (an update needs the file's current SHA; a new file must
not send one):

```bash
python scripts/github_upload.py \
  --repo <owner/name> \
  --path <in-repo path, e.g. docs/specs/atlas-2-icd.md> \
  --file /mnt/user-data/outputs/<stem>.md \
  [--branch <branch>] \
  [--message "<commit message>"]
```

For Path B the script reads `GITHUB_TOKEN` from the environment (preferred) or
takes `--token`; either way it never echoes the token. See "GitHub auth (token
setup)" below for what that token needs.

A useful commit message names the source, e.g.
`Add atlas-2-icd.md (transcribed from ATLAS-2 ICD.pdf)`. After either path,
capture the committed file's URL to show the user. The script (Path B) prints
JSON: on success (`"ok": true`) read `html_url`; on failure (`"ok": false`) it
includes a `hint`; relay it. The common ones: a 401/403 means the token is
missing, unscoped, or (for org repos) pending approval; a 404 means the
repo/branch isn't visible to the token; a 422 usually means a protected branch or
a stale SHA
(re-running picks up the latest).

### 4. Place the markdown in the Google Drive folder *(only if Drive was chosen)*

Skip this entire step if the user chose GitHub only. Otherwise: this uses the
Google Drive connector. If its tools aren't already loaded, run
`tool_search` for "google drive create file folder" to load `create_file` and
`search_files`.

**Preflight — confirm the connector is alive before uploading.** Do one cheap
read first (e.g. `get_file_metadata` on the target folder, or a tiny
`list_recent_files`). If even that errors, the Drive connector isn't authorized
in this session — stop the Drive step and tell the user plainly: "Google Drive
isn't connected in this session; authorize it (or run this in an environment
where it's connected) and I'll retry the upload." Don't keep retrying the upload
against a dead connector, and don't reach for `copy_file` as a substitute — it
copies an existing Drive file by `fileId` and can't ingest local content, so it
fails the same way. The GitHub commit and local file still stand; report them.

First resolve the folder to an ID:
- If the user gave a Drive **link**, the ID is the segment after `/folders/`
  (e.g. `https://drive.google.com/drive/folders/ABC123` → `ABC123`).
- If they gave a raw **ID**, use it directly.
- If they gave a **name**, search for it: a folder query looks like
  `mimeType = 'application/vnd.google-apps.folder' and name = '<name>'`. If the
  search returns several matches, list them with their IDs and ask which one
  rather than picking arbitrarily.

Then create the file with `create_file`:
- `title`: `<stem>.md`
- `textContent`: the full markdown text (read it from the output file)
- `contentMimeType`: `text/markdown`
- `parentId`: the resolved folder ID
- `disableConversionToGoogleType`: `true` — this keeps it a real `.md` file. Omit
  this flag (and use `text/plain`) only if the user explicitly wants it as a
  Google Doc instead.

Capture the returned file's link to show the user.

### 5. Report back

Give a short summary listing the local markdown path in `/mnt/user-data/outputs/`
plus the link for each destination the user chose:
- the GitHub commit link (`html_url`) — if GitHub was chosen,
- the Google Drive file link — if Drive was chosen.

Don't report a destination that wasn't requested. If a chosen destination failed,
say which and why (with the script's hint or the connector's error), and make
clear the other outputs still succeeded. Don't abort the whole run over one
failed destination — the user would rather have what worked than nothing.

## GitHub auth (token setup — Path B fallback only)

Skip this entirely when git/`gh` credentials already exist (Path A). It applies
only in a bare sandbox with no git identity. The token proves who you are to the
API. Use a **fine-grained personal access token** scoped to just the target
repo:

1. GitHub → Settings → Developer settings → Personal access tokens →
   Fine-grained tokens → Generate new token.
2. Set an expiration; under Repository access choose "Only select repositories"
   and pick the target repo.
3. Under Repository permissions, set **Contents: Read and write** (Metadata:
   Read-only is required and included automatically). That's all this skill
   needs.
4. Generate and copy it immediately — GitHub shows it once.

Provide it as `GITHUB_TOKEN` in the environment (cleanest — never lands in a
command or chat), or by pasting when asked. For org-owned repos, the token may
need org admin approval before it works. Revoke it anytime from the same page.

## Quality bar (self-check before reporting)

- The markdown came from `datasheet-to-markdown`, unmodified by this skill.
- The local `.md` exists in `/mnt/user-data/outputs/`.
- A destination was confirmed (asked if the request didn't say), and only the
  chosen destination(s) were acted on.
- *If GitHub was chosen:* the commit landed and you captured its URL (or the
  failure was reported with the hint).
- *If Drive was chosen:* the file landed in the **named/linked** folder (right
  `parentId`), as a `.md` unless a Google Doc was requested.
- The final message lists the local file and each chosen destination (or names
  whichever failed).
