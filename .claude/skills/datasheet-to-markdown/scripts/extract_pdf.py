#!/usr/bin/env python3
"""
extract_pdf.py — page-faithful raw extraction for the datasheet-to-markdown skill.

This does NOT produce the final markdown. It produces clean, page-delimited raw
material (text + detected tables) that the agent then transforms into the final
markdown by applying the skill's conventions. Page boundaries are authoritative:
the agent must preserve the PAGE N markers as page anchors.

Usage:
    python extract_pdf.py SOURCE.pdf                 # all pages, text + tables
    python extract_pdf.py SOURCE.pdf --page 12       # one page only
    python extract_pdf.py SOURCE.pdf --info          # metadata + page count only
    python extract_pdf.py SOURCE.pdf --render 12 out.png   # rasterize a page for
                                                            # visual transcription
                                                            # of tough tables/figures

Notes:
- Table detection (pdfplumber) is imperfect on dense or merged-cell tables. Treat
  detected tables as a starting point and verify against the text or a rendered
  image before finalizing.
- If text comes back empty/garbled, the PDF is likely scanned: rasterize pages with
  --render and transcribe visually (OCR fallback).
"""
import argparse
import sys


def get_info(path):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        meta = pdf.metadata or {}
        print(f"PAGES: {len(pdf.pages)}")
        for k in ("Title", "Author", "Subject", "Creator", "Producer",
                  "CreationDate", "ModDate"):
            if meta.get(k):
                print(f"{k}: {meta[k]}")


def render_page(path, page_no, out_png):
    import fitz  # PyMuPDF
    doc = fitz.open(path)
    page = doc[page_no - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))  # ~180+ dpi
    pix.save(out_png)
    print(f"Rendered page {page_no} -> {out_png}")


def table_to_tsv(table):
    rows = []
    for row in table:
        cells = ["" if c is None else " ".join(str(c).split()) for c in row]
        rows.append("\t".join(cells))
    return "\n".join(rows)


def dump(path, only_page=None):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        pages = pdf.pages
        for i, page in enumerate(pages, start=1):
            if only_page and i != only_page:
                continue
            print(f"\n===== PAGE {i} =====")
            text = page.extract_text() or ""
            print(text.rstrip())
            try:
                tables = page.extract_tables()
            except Exception as e:  # noqa: BLE001
                tables = []
                print(f"[table extraction error: {e}]", file=sys.stderr)
            for t_idx, table in enumerate(tables, start=1):
                print(f"\n--- detected table {i}.{t_idx} (verify against text/image) ---")
                print(table_to_tsv(table))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--page", type=int, help="extract a single page")
    ap.add_argument("--info", action="store_true", help="print metadata + page count only")
    ap.add_argument("--render", nargs=2, metavar=("PAGE", "OUT_PNG"),
                    help="rasterize a page to PNG for visual transcription")
    args = ap.parse_args()

    if args.info:
        get_info(args.pdf)
    elif args.render:
        render_page(args.pdf, int(args.render[0]), args.render[1])
    else:
        dump(args.pdf, only_page=args.page)


if __name__ == "__main__":
    main()
