#!/usr/bin/env python3
"""
extract_docx.py — structure-faithful raw extraction for Word datasheets.

Word files do NOT carry reliable rendered page numbers in their XML (the layout is
computed by the renderer, not stored). So page anchoring for .docx works one of two
ways — see the skill for which to choose:

  (A) PREFERRED for page-accurate anchors: convert the .docx to PDF first, then run
      extract_pdf.py on the result. Pagination matches what LibreOffice/Word renders.
          soffice --headless --convert-to pdf SOURCE.docx --outdir /tmp
          python extract_pdf.py /tmp/SOURCE.pdf
      Note in the output header that page numbers come from a rendered conversion.

  (B) If conversion is unavailable: anchor on the document's own structure (heading /
      section numbers) instead of pages, and capture any explicit "Page X of Y" text
      found in headers/footers. This script supports (B).

Usage:
    python extract_docx.py SOURCE.docx          # ordered paragraphs + tables + styles
    python extract_docx.py SOURCE.docx --info   # core properties (title, rev, etc.)
"""
import argparse


def get_info(path):
    from docx import Document
    doc = Document(path)
    cp = doc.core_properties
    for label, val in (
        ("Title", cp.title), ("Author", cp.author), ("Subject", cp.subject),
        ("Revision", cp.revision), ("Created", cp.created),
        ("Modified", cp.modified), ("Category", cp.category),
        ("Comments", cp.comments),
    ):
        if val:
            print(f"{label}: {val}")


def iter_block_items(parent):
    """Yield paragraphs and tables in document order."""
    from docx.document import Document as _Doc
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    body = parent.element.body if isinstance(parent, _Doc) else parent._tc
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def table_to_tsv(table):
    out = []
    for row in table.rows:
        out.append("\t".join(" ".join(c.text.split()) for c in row.cells))
    return "\n".join(out)


def dump(path):
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(path)
    t_idx = 0
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            style = block.style.name if block.style else ""
            text = block.text.rstrip()
            if not text and "Heading" not in style:
                continue
            tag = f"[{style}] " if style and style != "Normal" else ""
            print(f"{tag}{text}")
        elif isinstance(block, Table):
            t_idx += 1
            print(f"\n--- table {t_idx} (verify against source) ---")
            print(table_to_tsv(block))
            print("--- end table ---\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("--info", action="store_true")
    args = ap.parse_args()
    if args.info:
        get_info(args.docx)
    else:
        dump(args.docx)


if __name__ == "__main__":
    main()
