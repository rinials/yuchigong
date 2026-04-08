#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert Markdown files to Word (.docx) documents with proper Chinese text support.

Key fixes for Chinese (CJK) text rendering in Word:

  Mistake 1 (seen in previous attempts): Chinese text was garbled because no
  Chinese font or language tag was set — Word fell back to the default English
  (en-US) rendering and a non-CJK font, producing mojibake / 乱码.

  Mistake 2 (seen in a follow-up attempt): Per-run font overrides were applied
  (w:rFonts on individual <w:r> elements) but the 'Normal' style's <w:rPr> was
  NOT touched.  Word resolves fonts top-down from style → run; per-run CJK font
  overrides are ignored when the inherited style still points to a non-CJK
  font at the East-Asian slot.

This script fixes both issues by:
  1. Setting the eastAsia font AND zh-CN language on the 'Normal' style's rPr
     (style-level fix — inherited by every paragraph automatically).
  2. Setting document-level defaults (docDefaults/rPrDefault) to SimSun + zh-CN
     (document-level safety net; all *Theme font attributes are also removed so
     they cannot override the explicit SimSun setting).
  3. Applying the same SimSun / zh-CN settings to every text run (belt-and-
     suspenders so per-paragraph overrides are also correct).
"""

import os
import re
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


# ─── Chinese-font helpers ──────────────────────────────────────────────────────

def _set_run_chinese_font(run, font_name="SimSun"):
    """Set Chinese font on a single run's rPr element."""
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"),    font_name)
    rFonts.set(qn("w:hAnsi"),    font_name)
    rFonts.set(qn("w:eastAsia"), font_name)
    # Remove theme-font attributes that override explicit fonts
    for attr in (qn("w:asciiTheme"), qn("w:hAnsiTheme"), qn("w:eastAsiaTheme")):
        if rFonts.get(attr) is not None:
            del rFonts.attrib[attr]

    lang = rPr.find(qn("w:lang"))
    if lang is None:
        lang = OxmlElement("w:lang")
        rPr.append(lang)
    lang.set(qn("w:val"),      "zh-CN")
    lang.set(qn("w:eastAsia"), "zh-CN")


def _set_style_chinese_font(doc, style_name="Normal", font_name="SimSun"):
    """
    Set Chinese font + language on a named style's rPr.

    This is the critical fix missed by PR4: per-run overrides are overridden by
    Word's style-level settings when CJK font fallback is resolved. We must set
    the font at the *style* level so every paragraph that uses that style
    inherits it automatically.
    """
    style = doc.styles[style_name]
    rPr = style.element.get_or_add_rPr()

    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"),    font_name)
    rFonts.set(qn("w:hAnsi"),    font_name)
    rFonts.set(qn("w:eastAsia"), font_name)
    for attr in (qn("w:asciiTheme"), qn("w:hAnsiTheme"), qn("w:eastAsiaTheme"),
                 qn("w:cstheme")):
        if rFonts.get(attr) is not None:
            del rFonts.attrib[attr]

    lang = rPr.find(qn("w:lang"))
    if lang is None:
        lang = OxmlElement("w:lang")
        rPr.append(lang)
    lang.set(qn("w:val"),      "zh-CN")
    lang.set(qn("w:eastAsia"), "zh-CN")


def _set_doc_defaults_chinese(doc, font_name="SimSun"):
    """
    Set document-level defaults (docDefaults/rPrDefault) to Chinese font + language.

    This is an additional safety net so even runs that inherit nothing from styles
    still display Chinese text correctly.

    IMPORTANT: Use doc.styles.element (the <w:styles> root in styles.xml), NOT
    doc.element (which is the <w:document> root in document.xml).  PR4 bug: the
    styles root was looked up on the wrong document part.
    """
    # doc.styles.element is the root <w:styles> element inside styles.xml
    styles_elem = doc.styles.element
    if styles_elem is None:
        return

    doc_defaults = styles_elem.find(qn("w:docDefaults"))
    if doc_defaults is None:
        doc_defaults = OxmlElement("w:docDefaults")
        styles_elem.insert(0, doc_defaults)

    rPr_default = doc_defaults.find(qn("w:rPrDefault"))
    if rPr_default is None:
        rPr_default = OxmlElement("w:rPrDefault")
        doc_defaults.append(rPr_default)

    rPr = rPr_default.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        rPr_default.append(rPr)

    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"),    font_name)
    rFonts.set(qn("w:hAnsi"),    font_name)
    rFonts.set(qn("w:eastAsia"), font_name)
    # Remove all theme-font attributes; they override explicit fonts in Word
    for attr in (qn("w:asciiTheme"), qn("w:hAnsiTheme"), qn("w:eastAsiaTheme"),
                 qn("w:cstheme")):
        if rFonts.get(attr) is not None:
            del rFonts.attrib[attr]

    lang = rPr.find(qn("w:lang"))
    if lang is None:
        lang = OxmlElement("w:lang")
        rPr.append(lang)
    lang.set(qn("w:val"),      "zh-CN")
    lang.set(qn("w:eastAsia"), "zh-CN")
    # Remove bidi language if set to Arabic (default template artifact)
    if lang.get(qn("w:bidi")) is not None:
        del lang.attrib[qn("w:bidi")]


# ─── Markdown → docx conversion ───────────────────────────────────────────────

def _add_run(para, text, bold=False, italic=False, font_name="SimSun", font_size=None):
    """Add a run to a paragraph with Chinese font settings."""
    run = para.add_run(text)
    run.bold = bold
    run.italic = italic
    if font_size:
        run.font.size = Pt(font_size)
    _set_run_chinese_font(run, font_name)
    return run


def _parse_inline(para, text, font_name="SimSun", font_size=None):
    """Parse inline bold/italic markdown and add runs to para."""
    # Pattern: **bold**, *italic*, ***bold+italic***
    pattern = re.compile(r'(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)')
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            _add_run(para, text[pos:m.start()], font_name=font_name, font_size=font_size)
        if m.group(1).startswith("***"):
            _add_run(para, m.group(2), bold=True, italic=True, font_name=font_name, font_size=font_size)
        elif m.group(1).startswith("**"):
            _add_run(para, m.group(3), bold=True, font_name=font_name, font_size=font_size)
        elif m.group(1).startswith("*"):
            _add_run(para, m.group(4), italic=True, font_name=font_name, font_size=font_size)
        elif m.group(1).startswith("`"):
            run = _add_run(para, m.group(5), font_name="Courier New", font_size=font_size)
            run.font.name = "Courier New"
        pos = m.end()
    if pos < len(text):
        _add_run(para, text[pos:], font_name=font_name, font_size=font_size)


def _strip_md_link(text):
    """Replace [label](url) with label."""
    return re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)


def md_to_docx(md_path: Path, docx_path: Path, font_name="SimSun"):
    """Convert a Markdown file to a .docx file with proper Chinese support."""
    doc = Document()

    # ── Step 1: fix Chinese at document-defaults level ──────────────────────
    _set_doc_defaults_chinese(doc, font_name)

    # ── Step 2: fix Chinese at Normal style level ────────────────────────────
    _set_style_chinese_font(doc, "Normal", font_name)

    # ── Step 3: also patch heading styles ────────────────────────────────────
    for heading_style in ["Heading 1", "Heading 2", "Heading 3", "Heading 4"]:
        try:
            _set_style_chinese_font(doc, heading_style, font_name)
        except KeyError:
            pass

    # ── Step 4: parse and render Markdown ────────────────────────────────────
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")

        # ── Blank line ────────────────────────────────────────────────────────
        if line.strip() == "":
            i += 1
            continue

        # ── ATX headings: # ## ### ####  ─────────────────────────────────────
        heading_match = re.match(r'^(#{1,4})\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            title = _strip_md_link(heading_match.group(2).strip())
            para = doc.add_heading(level=level)
            para.clear()
            _parse_inline(para, title, font_name=font_name,
                          font_size=[18, 16, 14, 13][level - 1])
            i += 1
            continue

        # ── Horizontal rule  ──────────────────────────────────────────────────
        if re.match(r'^[-*_]{3,}\s*$', line):
            doc.add_paragraph("─" * 40)
            i += 1
            continue

        # ── Blockquote  ───────────────────────────────────────────────────────
        if line.startswith(">"):
            text = line.lstrip("> ").strip()
            text = _strip_md_link(text)
            para = doc.add_paragraph(style="Normal")
            para.paragraph_format.left_indent = Pt(24)
            _parse_inline(para, text, font_name=font_name)
            i += 1
            continue

        # ── Fenced code block  ────────────────────────────────────────────────
        if line.startswith("```"):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].rstrip("\n").startswith("```"):
                code_lines.append(lines[i].rstrip("\n"))
                i += 1
            i += 1  # skip closing ```
            para = doc.add_paragraph("\n".join(code_lines), style="Normal")
            for run in para.runs:
                run.font.name = "Courier New"
            continue

        # ── Table  ────────────────────────────────────────────────────────────
        if "|" in line and line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].rstrip("\n"))
                i += 1
            # Filter out separator rows (---|---|---)
            data_rows = [r for r in table_lines
                         if not re.match(r'^\s*\|[\s\-:|]+\|\s*$', r)]
            if not data_rows:
                continue
            rows_data = []
            for row_line in data_rows:
                cells = [c.strip() for c in row_line.strip().strip("|").split("|")]
                rows_data.append(cells)
            if not rows_data:
                continue
            num_cols = max(len(r) for r in rows_data)
            table = doc.add_table(rows=len(rows_data), cols=num_cols)
            table.style = "Table Grid"
            for r_idx, row_data in enumerate(rows_data):
                for c_idx, cell_text in enumerate(row_data):
                    if c_idx >= num_cols:
                        break
                    cell = table.cell(r_idx, c_idx)
                    cell.text = ""
                    cell_text = _strip_md_link(cell_text)
                    para = cell.paragraphs[0]
                    is_header = r_idx == 0
                    _parse_inline(para, cell_text, font_name=font_name)
                    if is_header:
                        for run in para.runs:
                            run.bold = True
                            _set_run_chinese_font(run, font_name)
                # Fill empty cells
                for c_idx in range(len(row_data), num_cols):
                    pass
            continue

        # ── Unordered list  ───────────────────────────────────────────────────
        ul_match = re.match(r'^(\s*)[-*+]\s+(.*)', line)
        if ul_match:
            indent = len(ul_match.group(1)) // 2
            text = _strip_md_link(ul_match.group(2).strip())
            para = doc.add_paragraph(style="List Bullet")
            para.paragraph_format.left_indent = Pt(18 + indent * 18)
            _parse_inline(para, text, font_name=font_name)
            i += 1
            continue

        # ── Ordered list  ─────────────────────────────────────────────────────
        ol_match = re.match(r'^(\s*)\d+[.)]\s+(.*)', line)
        if ol_match:
            indent = len(ol_match.group(1)) // 2
            text = _strip_md_link(ol_match.group(2).strip())
            para = doc.add_paragraph(style="List Number")
            para.paragraph_format.left_indent = Pt(18 + indent * 18)
            _parse_inline(para, text, font_name=font_name)
            i += 1
            continue

        # ── Normal paragraph  ─────────────────────────────────────────────────
        text = _strip_md_link(line.strip())
        para = doc.add_paragraph(style="Normal")
        _parse_inline(para, text, font_name=font_name)
        i += 1

    doc.save(str(docx_path))
    print(f"  ✓  {docx_path.name}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    script_dir = Path(__file__).parent
    output_dir = script_dir / "word"
    output_dir.mkdir(exist_ok=True)

    # Collect all .md files except README
    md_files = sorted(
        p for p in script_dir.glob("*.md")
        if p.name.lower() != "readme.md"
    )

    if not md_files:
        print("No .md files found in", script_dir)
        return

    print(f"Converting {len(md_files)} Markdown files to Word …")
    docx_files = []
    for md_path in md_files:
        docx_name = md_path.stem + ".docx"
        docx_path = output_dir / docx_name
        md_to_docx(md_path, docx_path)
        docx_files.append(docx_path)

    # Create ZIP archive
    zip_path = script_dir / "3GPP_TR_22870_中文翻译.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for docx_path in docx_files:
            zf.write(docx_path, docx_path.name)
    print(f"\n✓  ZIP archive created: {zip_path}")
    print(f"   Contains {len(docx_files)} Word documents")
    print(f"   Total size: {zip_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
