---
name: datasheet-to-markdown
description: >-
  Convert a partner, vendor, or supplier technical document (PDF or Word .docx/.dotx) —
  data sheet, interface control document (ICD), spec sheet, datasheet, hardware/component
  reference, user manual, or similar — into a clean markdown transcription that preserves
  the original's page numbers, document ID/version, and table/figure identifiers so every
  claim can be cited back to the source. Use this whenever the user wants to "extract",
  "transcribe", "convert to markdown", "pull the technical content out of", "make a
  referenceable version of", or "summarize for the team" a vendor/partner PDF or Word
  spec — even if they don't say the word "markdown". The output is a standalone markdown
  file someone can read later and still cite exact pages, tables, and figures from. By
  default it transcribes text and tables only and does NOT describe figures/diagrams;
  there is an opt-in flag to add brief text summaries of figures.
---

# Datasheet → Markdown

Turn a vendor/partner technical document into a markdown file that is a faithful,
**citable** transcription of the original. The guiding principle: a teammate who only
ever sees the markdown should still be able to write "per Table 3-1 on page 6 of
ICD-ATL-0001…" and have that reference resolve against the original document.

Two things make that possible and are non-negotiable: (1) preserve the source's own
identifiers (document ID, revision, page numbers, table/figure numbers), and (2) when
you ever shorten or omit something, leave a citation breadcrumb pointing to where the
full content lives in the source.

## What this skill does and does not do

- **Does:** transcribe body text, headings (with original section numbers), lists, and
  tables; anchor every chunk to its source page; preserve table/figure numbers and
  captions; carry over cross-references ("see Figure 4-4") verbatim.
- **Does NOT (by default):** interpret, describe, or summarize figures, diagrams,
  drawings, photos, or charts. Record that they exist and where, but not what they show.
- **Opt-in only:** brief text summaries of figures (see "Figure summary flag").

## When the user wants figure summaries (the flag)

Default = OFF. Turn it ON only if the user clearly asks, e.g. "include figure
summaries", "also describe the diagrams", "with short descriptions of the figures",
"summarize what each figure shows". If it's ambiguous, default OFF and mention they can
ask for figure summaries. Never let summaries leak into a default run.

When ON, summaries must be clearly marked as skill-generated interpretation, never
presented as if they were source text (see template below).

---

## Workflow

### 1. Locate and identify the source
Find the file (usually under `/mnt/user-data/uploads/`). Confirm the type:
- PDF → step 2A
- Word (`.docx`/`.dotx`) → step 2B

### 2A. Extract a PDF (page-faithful)
Get metadata and page count first, then the per-page content:
```bash
python scripts/extract_pdf.py SOURCE.pdf --info
python scripts/extract_pdf.py SOURCE.pdf            # all pages, text + detected tables
```
The script delimits pages with `===== PAGE N =====`. **These boundaries are
authoritative — they become your page anchors.** If a page's text is empty/garbled the
PDF is scanned; rasterize and transcribe visually:
```bash
python scripts/extract_pdf.py SOURCE.pdf --render 12 /tmp/p12.png   # then view the PNG
```
For dense or merged-cell tables the script's auto-detected tables are often imperfect —
render the page and transcribe the table by reading the image when in doubt.

### 2B. Extract a Word document
Word XML has no reliable rendered page numbers. Choose:
- **Preferred (page-accurate anchors):** convert to PDF, then use 2A.
  ```bash
  soffice --headless --convert-to pdf SOURCE.docx --outdir /tmp && \
  python scripts/extract_pdf.py /tmp/SOURCE.pdf
  ```
  Record in the header that page numbers come from a rendered conversion (they may
  differ from the authoring tool's pagination).
- **Fallback (no converter available):** 
  ```bash
  python scripts/extract_docx.py SOURCE.docx --info
  python scripts/extract_docx.py SOURCE.docx
  ```
  Anchor on **section/heading numbers** instead of pages, capture any "Page X of Y"
  text found in headers/footers, and state in the header that page anchors are
  unavailable / structural.

### 3. Mine the metadata
From the title page, header/footer band, or revision table, capture: document title,
document ID, current revision/version + its date, classification, and total pages.
Datasheets usually repeat ID/classification in a header on every page and carry a
revision history table — use the latest row. If a field genuinely isn't present, write
`(not specified)` rather than guessing.

### 4. Assemble the markdown
Walk the source front to back and apply the conventions below. Do not reorder content.
Preserve original section numbering exactly (e.g. `## 10.1 Electrical Specifications`).

### 5. Save and present
Write to `/mnt/user-data/outputs/<source-stem>.md` and present it. Default filename
mirrors the source stem.

---

## Output conventions (use exactly)

### Header block (top of file)
```markdown
# <Document Title>

> **Source document:** `<original filename>`
> **Document ID:** <id or (not specified)>
> **Revision:** <rev> (<date>)
> **Classification:** <e.g. Confidential, or (not specified)>
> **Total pages:** <N>
> **Page anchors:** PDF page numbers from the source.   <!-- or: rendered-conversion / structural -->
> **Figure summaries:** not included   <!-- or: included (skill-generated, see notes) -->
> **Transcribed by:** datasheet-to-markdown skill on <date>
>
> Throughout this file, `> **Source page N**` markers (and `<!-- page: N -->` comments)
> indicate where each section appears in the source document. Table and figure numbers
> are the source's own. Condensed or untranscribed items always cite their source page.
```
If the source carries a confidentiality/distribution notice, restate it once, here.

### Page anchors (both visible + hidden, at every page boundary)
Insert at the start of each page's content:
```markdown
<!-- page: 5 -->
> **Source page 5**
```
The HTML comment is for search/tooling; the blockquote line is the human-visible
marker. Put body content from that page after the marker. Keep markers even across a
page break that splits a paragraph or table (note "(continued)" if a table spans pages).

### Headings / sections
Reproduce the source's numbering and nesting. Map the document's top-level sections to
`##`, subsections to `###`, etc. Don't invent headings the source doesn't have.

### Tables — full by default, condense by judgement, always cite
Default: transcribe the table in full as a GitHub-flavored markdown table, with a
caption line that preserves the source's table number:
```markdown
**Table 3-1 — ATLAS-2 electrical power interfaces for 12 V and 5 V power lines** <!-- table: 3-1; page: 6 -->

| Mode | Min current [A] | Average current [A] | Peak current [A] (10 ms) | Typical duration |
|---|---|---|---|---|
| Start up | 0.5 | 0.6 | 3.0 | <5 min |
```
**Use judgement to condense** when a table is voluminous but not substantively critical
to the section's technical message (e.g. an exhaustive per-pin connector table that the
prose never leans on). When you condense, you MUST keep the table number, caption, and a
pointer to the source page, and convey the gist:
```markdown
**Table 10-7 — Connector J6 pinout** *(condensed — full 16-pin table on source page 27)* <!-- table: 10-7; page: 27; condensed -->

16-pin LPA-module interface (SPI chip-selects, ±12 V LDD power, differential LDD
SPI/disable lines). None of the pins connect to the bus. Full pin-by-pin listing on
source page 27.
```
Decide per table; when unsure whether a table is "critical", transcribe it in full.
Never silently drop a table — a condensed table still appears in place, with its
citation.

### Figures / diagrams / drawings — default: record, don't describe
Place a caption line where the figure occurs, preserving its number, with an explicit
not-transcribed note and a page citation:
```markdown
**Figure 4-4 — Technical drawing: ATLAS-2 FSO assembly space envelope** *(figure not transcribed; see source page 12)* <!-- figure: 4-4; page: 12; not-transcribed -->
```
If the figure has values called out in nearby body text (dimensions, ratings), those
live in the transcribed text as usual — but do not read new information off the figure
itself in a default run.

### Figures — with the summary flag ON
Add a short, clearly-labelled summary under the caption. Mark it as skill-generated so
no reader mistakes it for source text:
```markdown
**Figure 4-4 — Technical drawing: ATLAS-2 FSO assembly space envelope** <!-- figure: 4-4; page: 12; summary -->
> *Figure summary (skill-generated, not source text):* Multi-view mechanical drawing of
> the FSO module envelope (~127 × 92 × 104 mm) showing two circular front apertures and
> labelled mounting points; a thermal-interface surface is called out on one face.
Keep summaries to 1–3 sentences, factual, about what is depicted. Don't infer beyond
what's visibly shown; don't editorialize.

### Cross-references and footnotes
Carry over the source's internal references verbatim ("as per SDA OCT 4.0", "see
Figure 6-2", "described in [1]") so the markdown's references stay navigable. Reproduce
footnotes/endnotes near where they're marked, with their marker preserved.

### Things to leave alone
Don't fix the source's apparent typos or unit oddities silently — transcribe as-is. If
something is illegible, write `[illegible — source page N]`. Don't add analysis,
opinions, or recommendations; this is a transcription, not a review.

---

## Quality bar (self-check before presenting)
- Every page boundary has both a `<!-- page: N -->` comment and a `> **Source page N**` line.
- Header block is filled; missing fields say `(not specified)`, not blank.
- Every source table appears in place (full or condensed-with-citation); every figure has
  a caption + page citation. No silent drops.
- A default run contains zero figure descriptions; a flagged run marks every summary as
  skill-generated.
- Original section numbers and internal cross-references are intact.
- Spot-check 2–3 values against the source page they're anchored to.

## Examples of triggering phrases
- "Convert this supplier ICD to markdown so we can reference it." → default run
- "Pull the technical content out of this datasheet PDF." → default run
- "Make a referenceable markdown of the vendor spec, and include short summaries of the
  diagrams." → figure-summary flag ON
- "Transcribe this Word data sheet for the wiki." → 2B (convert-to-PDF preferred)
