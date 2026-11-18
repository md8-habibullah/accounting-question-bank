#!/usr/bin/env python3
"""Build the Accounting Question Bank PDF from the Markdown chapters.

Run with the project's venv:   build/.venv-pdf/bin/python -I build/scripts/build_pdf.py [options]

  --original-only   only the original written content (no pages copied from the ICAEW / ICAB PDFs).
                    Safe to share. Default output: output/Accounting_Question_Bank_original_only.pdf
  (default)         FULL private study edition: original content + the ICAEW question-bank pages (and the
                    ICAB workbook interactive-question pages when build/data/workbook_map.json exists),
                    placed chapter by chapter. For personal study only - do not share or publish.
  --chapters 9,10   build only these chapters (quick test)
  --out PATH        output file

Pipeline: Markdown -> HTML (python-markdown) -> PDF (WeasyPrint) per part -> assemble with pypdf
(copied pages are scaled slightly onto A4 so every page gets the same header/footer band) -> stamp
header/footer + page numbers (reportlab) -> PDF bookmarks.
"""
import argparse, io, json, re, sys
from pathlib import Path

import markdown
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.pdfgen import canvas
from weasyprint import HTML, CSS

ROOT = Path(__file__).resolve().parents[2]
CH_DIR = ROOT / "chapters"
OUT_DIR = ROOT / "output"
WORK = ROOT / "build" / "work"
DATA = ROOT / "build" / "data"
CSS_FILE = Path(__file__).with_name("style.css")
SRC_QB = ROOT / "sources" / "Accounting_Question_Bank_2024_final.pdf"
SRC_WB = ROOT / "sources" / "Accounting_Book_CL26.pdf"

A4W, A4H = 595.276, 841.89
SCALE = 0.925          # copied pages are shrunk a little so the stamp bands fit

# ICAB chapter -> ICAEW question-bank chapter (ICAB 14 = ICAEW 15; ICAEW 14 and 16 become appendices)
ICAEW_OF = {n: n for n in range(1, 14)}
ICAEW_OF[14] = 15

TITLE_SHORT = "Accounting Question Bank"

# ---------------------------------------------------------------- markdown -> html
MD_EXT = ["tables", "sane_lists", "attr_list"]
CALLOUTS = {"FORMULA": "formula", "KEY FACT": "keyfact", "REMEMBER": "remember", "EXAM TRAP": "trap",
            "EXAMPLE": "example", "WHY": "keyfact"}


def md_to_html(text):
    html = markdown.markdown(text, extensions=MD_EXT, output_format="html")

    labels = "|".join(re.escape(k) for k in CALLOUTS)

    def callout(m):
        # one blockquote may hold several labelled paragraphs ("> **FORMULA** ..." lines separated by blank lines)
        out = []
        for chunk in re.split(rf"(?=<p><strong>(?:{labels})</strong>)", m.group(1)):
            mm = re.match(rf"\s*<p><strong>({labels})</strong>\s*(.*)", chunk, re.S)
            if mm:
                out.append(f'<div class="callout {CALLOUTS[mm.group(1)]}"><p><span class="callout-label">{mm.group(1)}</span>{mm.group(2)}</div>')
            elif chunk.strip():
                out.append(f"<blockquote>{chunk}</blockquote>")
        return "".join(out)

    html = re.sub(r"<blockquote>(.*?)</blockquote>", callout, html, flags=re.S)
    # long tables may split across pages (their header row repeats); short ones are kept together
    html = re.sub(r"<table>(.*?)</table>", lambda m: ('<table class="long">' if m.group(1).count("<tr>") > 8 else "<table>") + m.group(1) + "</table>", html, flags=re.S)
    # a caption paragraph directly before a table stays on the same page as the table
    html = re.sub(r"<p>((?:(?!</p>).){0,200})</p>(\s*<table)", r'<p class="cap">\1</p>\2', html, flags=re.S)
    html = re.sub(r"<!--space:(\d+)-->", lambda m: f'<div class="answer-space" style="height:{m.group(1)}mm"></div>', html)
    html = html.replace("<ul>\n<li>A)", '<ul class="options">\n<li>A)')
    html = re.sub(r"<em>\(True / False\)</em>", '<span class="tf"><span>True</span><span>False</span></span>', html)
    # keep a question and its options on the same page
    html = re.sub(r'(<p>(?:(?!</p>).)*</p>)\s*(<ul class="options">.*?</ul>)', r'<div class="mcq">\1\2</div>', html, flags=re.S)
    return html


def wrap(body, extra_css=""):
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{extra_css}</style></head><body>{body}</body></html>'


CSS_TEXT = CSS_FILE.read_text(encoding="utf-8")


def render(html_body, name):
    """Render HTML to a PDF in WORK; return (path, page_count)."""
    WORK.mkdir(parents=True, exist_ok=True)
    path = WORK / f"{name}.pdf"
    doc = HTML(string=wrap(html_body), base_url=str(ROOT)).render(stylesheets=[CSS(string=CSS_TEXT)])
    doc.write_pdf(str(path))
    return path, len(doc.pages)


# ---------------------------------------------------------------- content loading
def load_chapters():
    chapters = {}
    for f in sorted(CH_DIR.glob("[0-9][0-9]-*.md")):
        n = int(f.name[:2])
        if n == 0:
            continue
        text = f.read_text(encoding="utf-8")
        title = re.match(r"# Chapter (\d+): (.+)", text)
        if not title:
            sys.exit(f"{f.name}: first line must be '# Chapter N: Title'")
        parts = re.split(r"(?m)^(?=## )", text)
        h1 = parts[0]
        secs = {}
        for p in parts[1:]:
            m = re.match(r"## (\d+)\.(\d+) ", p)
            if not m or int(m.group(1)) != n:
                sys.exit(f"{f.name}: unexpected heading: {p.splitlines()[0]}")
            secs[int(m.group(2))] = p
        missing = [k for k in range(1, 9) if k not in secs]
        if missing:
            sys.exit(f"{f.name}: missing sections {missing}")
        chapters[n] = {"n": n, "title": title.group(2).strip(), "file": f.name, "h1": h1, "secs": secs, "text": text}
    return chapters


def count_questions(ch):
    t = ch["text"]
    extra = len(set(re.findall(r"(?m)^(?:\*\*|### )Q(\d+)[.\s]", ch["secs"][6])))
    tf = len(re.findall(r"(?m)^\*\*T/F \d+\.", ch["secs"][7]))
    return extra, tf


# ---------------------------------------------------------------- segments
def build_segments(chapters, include_foreign, only):
    qb_map = {c["icaew_chapter"]: c for c in json.loads((DATA / "icaew_map.json").read_text())}
    wb_path = DATA / "workbook_map.json"
    wb_map = json.loads(wb_path.read_text()) if wb_path.exists() else {}
    segs = []

    def own(kind_label, right, chapter, pdf, npages, title):
        segs.append({"src": "own", "pdf": pdf, "pages": list(range(npages)), "label": right, "chapter": chapter, "title": title})

    for n, ch in chapters.items():
        if only and n not in only:
            continue
        head = f'<h1>Chapter {n}: {ch["title"]}</h1>'
        learn_html = md_to_html(head + "".join(ch["secs"][k] for k in range(1, 6)))
        p, c = render(learn_html, f"ch{n:02d}_learn")
        own("learn", "Learn", n, p, c, "Learn: notes, formulas, examples")

        wb = wb_map.get(str(n), {}) if include_foreign else {}
        if wb.get("iq_pages"):
            segs.append({"src": "wb", "pages": wb["iq_pages"], "label": "ICAB workbook: interactive questions",
                         "chapter": n, "title": "ICAB workbook: interactive questions (pages that contain them)"})
        if wb.get("selftest_pages"):
            segs.append({"src": "wb", "pages": wb["selftest_pages"], "label": "ICAB workbook: self-test questions",
                         "chapter": n, "title": "ICAB workbook: self-test questions"})
        e = ICAEW_OF.get(n)
        if include_foreign and e:
            segs.append({"src": "qb", "pages": qb_map[e]["q_pdf_pages"], "label": "ICAEW question bank: questions",
                         "chapter": n, "title": f"ICAEW question bank: questions (about {qb_map[e]['approx_question_count']})"})
        prac_html = md_to_html("".join(ch["secs"][k] for k in (6, 7)).replace("## ", "## ", 1))
        prac_html = prac_html.replace("<h2>", '<h2 class="new-page">', 1)
        p, c = render(prac_html, f"ch{n:02d}_practice")
        own("practice", "Extra practice", n, p, c, "Extra practice questions and true/false")

        ans_html = md_to_html(ch["secs"][8]).replace("<h2>", '<h2 class="new-page">', 1)
        p, c = render(ans_html, f"ch{n:02d}_answers")
        own("answers", "Answers: extra practice", n, p, c, "Answers and explanations (extra practice)")
        if include_foreign and e:
            segs.append({"src": "qb", "pages": qb_map[e]["a_pdf_pages"], "label": "ICAEW question bank: answers",
                         "chapter": n, "title": "ICAEW question bank: answers"})
        if wb.get("answer_pages"):
            segs.append({"src": "wb", "pages": wb["answer_pages"], "label": "ICAB workbook: answers",
                         "chapter": n, "title": "ICAB workbook: answers (interactive and self-test)"})
    return segs, qb_map


MOCK_FILE = CH_DIR / "appendix-a-mock-exam.md"
MOCK_GROUP = "Appendix A: Mock exam (50 questions, 90 minutes)"


def hdr(t, limit=64):
    """running-header text: cut long chapter titles at a word boundary"""
    if len(t) <= limit:
        return t
    return t[:limit].rsplit(" ", 1)[0].rstrip(" ,:;") + "..."


def mock_segments():
    """Original mock exam (chapters/appendix-a-mock-exam.md): instructions, paper, answers, score sheet."""
    if not MOCK_FILE.exists():
        return []
    parts = re.split(r"(?m)^(?=## )", MOCK_FILE.read_text(encoding="utf-8"))
    head, secs = parts[0], {}
    for p in parts[1:]:
        m = re.match(r"## A\.(\d+) ", p)
        if not m:
            sys.exit(f"{MOCK_FILE.name}: unexpected heading: {p.splitlines()[0]}")
        secs[int(m.group(1))] = p
    missing = [k for k in range(1, 5) if k not in secs]
    if missing:
        sys.exit(f"{MOCK_FILE.name}: missing sections {missing}")
    segs = []
    plan = [("mock1", head + secs[1], "Instructions", False),
            ("mock2", secs[2], "Questions", True),
            ("mock3", secs[3], "Answers and explanations", True),
            ("mock4", secs[4], "Score sheet and what to revise", True)]
    for name, md, label, newpage in plan:
        html = md_to_html(md)
        if newpage:
            html = html.replace("<h2>", '<h2 class="new-page">', 1)
        p, c = render(html, name)
        segs.append({"src": "own", "pdf": p, "pages": list(range(c)), "label": "Mock exam: " + label.lower(),
                     "chapter": None, "group": MOCK_GROUP,
                     "title": {"Instructions": "Instructions", "Questions": "Exam paper: questions 1 to 50",
                               "Answers and explanations": "Answers and explanations",
                               "Score sheet and what to revise": "Answer key, score sheet and what to revise"}[label]})
    return segs


def appendix_segments(include_foreign, qb_map, only):
    if only:
        return []
    segs = mock_segments()
    if not include_foreign:
        return segs
    pe, uk = qb_map[16], qb_map[14]
    segs.append({"src": "qb", "pages": pe["q_pdf_pages"], "label": "Appendix B: ICAEW practice exam", "chapter": None,
                 "group": "Appendix B: ICAEW practice exam", "title": "Practice exam: questions"})
    segs.append({"src": "qb", "pages": pe["a_pdf_pages"] + [311, 312], "label": "Appendix B: practice exam answers", "chapter": None,
                 "group": "Appendix B: ICAEW practice exam", "title": "Practice exam: answers and mock-exam guidance"})
    segs.append({"src": "qb", "pages": uk["q_pdf_pages"] + uk["a_pdf_pages"], "label": "Appendix C: UK GAAP company accounts (optional)",
                 "chapter": None, "group": "Appendix C: UK GAAP company accounts (only if your tutor says it is examined)",
                 "title": "Questions and answers"})
    return segs


# ---------------------------------------------------------------- front matter
def cover_html(chapters, qb_map, include_foreign, n_extra, n_tf):
    qb_total = sum(c["approx_question_count"] for c in qb_map.values())
    rows = [("Exam", "ICAB Certificate Level: Accounting (1.5 hours, 50 questions x 2 marks, multiple choice / multiple response)"),
            ("Chapters", f"{len(chapters)} chapter{'s' if len(chapters) != 1 else ''} in the same order as the ICAB Accounting Workbook 2026"),
            ("Original content", f"Plain-English notes, key facts, formulas, worked examples, {n_extra} extra practice questions "
                                 f"(each chapter ends with 2 scenario questions), {n_tf} true/false questions, full answers with reasons")]
    if include_foreign:
        rows.append(("Included pages", f"ICAEW Accounting Question Bank 2024 (about {qb_total} exam-standard questions, with answers), "
                                       "placed chapter by chapter" + ("; ICAB workbook interactive questions" if (DATA / "workbook_map.json").exists() else "")))
        note = ("Personal study edition. It contains pages reproduced from the ICAEW Accounting Question Bank (&copy; ICAEW 2023) and the ICAB Accounting "
                "Workbook (&copy; ICAB 2026). Do not share or publish this file. The original notes, questions and answers were written for this book "
                "and checked, but if anything differs from your ICAB workbook or tutor, follow the workbook.")
    else:
        rows.append(("Edition", "Original content only (no copied pages). Use it together with the ICAB workbook and the ICAEW Accounting Question Bank."))
        note = ("This edition contains only original notes, questions and answers written for this book. They were checked, but if anything differs "
                "from your ICAB workbook or tutor, follow the workbook.")
    tr = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in rows)
    return (f'<div class="cover"><div class="band"><div class="kicker">CA Certificate Level &middot; Topic-wise practice</div>'
            f'<h1>Accounting<br>Question Bank</h1><div class="sub">Learn the idea, see the formula, practise exam-style questions, '
            f'and check every answer with the reason why.</div></div><div class="facts"><table>{tr}</table></div>'
            f'<div class="note">{note}</div></div>')


def formula_sheet_html(chapters):
    parts = ['<h1>Formula sheet</h1><p>Every formula from the chapters in one place. Cover a formula with your hand and try to write it from memory.</p><div class="fsheet">']
    for n, ch in chapters.items():
        fs = re.findall(r"(?m)^> \*\*FORMULA\*\*\s*(.+)$", ch["text"])
        if not fs:
            continue
        parts.append(f"<h3>Chapter {n}: {ch['title']}</h3><ul>")
        for f in fs:
            parts.append("<li>" + markdown.markdown(f, output_format="html").replace("<p>", "").replace("</p>", "") + "</li>")
        parts.append("</ul>")
    parts.append("</div>")
    return "".join(parts)


def toc_html(entries):
    """entries: list of (level, title, page); level 0 = group, 1 = chapter / item, 2 = sub-item"""
    rows = []
    for lvl, t, pg in entries:
        cls = {0: "group", 1: "ch", 2: "sub"}[lvl]
        rows.append(f'<tr class="{cls}"><td class="t">{t}</td><td class="p">{pg}</td></tr>')
    return '<div class="toc"><h1>Contents</h1><table>' + "".join(rows) + "</table></div>"


# ---------------------------------------------------------------- assembly
def stamp_overlay(specs):
    """specs: list of (top_left, top_right, bottom_text) -> in-memory PDF with one page per spec."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(A4W, A4H))
    for tl, tr, bt in specs:
        if tl or tr:
            c.setFont("Helvetica-Bold", 7.6); c.setFillGray(0.38)
            c.drawString(51, A4H - 24, tl)
            c.setFont("Helvetica", 7.6); c.drawRightString(A4W - 51, A4H - 24, tr)
            c.setStrokeGray(0.8); c.setLineWidth(0.4); c.line(51, A4H - 29, A4W - 51, A4H - 29)
        if bt:
            c.setFont("Helvetica", 8); c.setFillGray(0.38); c.drawCentredString(A4W / 2, 17, bt)
        c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--original-only", action="store_true")
    ap.add_argument("--chapters", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    include_foreign = not a.original_only
    only = {int(x) for x in a.chapters.split(",") if x.strip()}
    if include_foreign and not (SRC_QB.exists() and SRC_WB.exists()):
        sys.exit("source PDFs missing in sources/ - cannot build the full edition")

    chapters = load_chapters()
    if not chapters:
        sys.exit("no chapters found in chapters/")
    segs, qb_map = build_segments(chapters, include_foreign, only)
    segs += appendix_segments(include_foreign, qb_map, only)

    n_extra = sum(count_questions(c)[0] for c in chapters.values())
    n_tf = sum(count_questions(c)[1] for c in chapters.values())

    # front matter (own pages, rendered once)
    front = []
    cover_p, cover_n = render(cover_html(chapters, qb_map, include_foreign, n_extra, n_tf), "front_cover")
    front.append(("cover", cover_p, cover_n, "", "Cover"))
    howto_f = CH_DIR / "00-how-to-use.md"
    if howto_f.exists():
        h_p, h_n = render(md_to_html(howto_f.read_text(encoding="utf-8")), "front_howto")
        front.append(("howto", h_p, h_n, "How to use this book", "How to use this book, exam facts and study plan"))
    fs_p, fs_n = render(formula_sheet_html(chapters), "front_formulas")
    front.append(("formulas", fs_p, fs_n, "Formula sheet", "Formula sheet"))

    # page numbering and table of contents
    def paginate(toc_pages):
        pos, starts = 1, {}
        starts["cover"] = pos; pos += front[0][2]
        starts["toc"] = pos; pos += toc_pages
        for key, _, npg, _, _ in front[1:]:
            starts[key] = pos; pos += npg
        for i, s in enumerate(segs):
            s["start"] = pos; pos += len(s["pages"])
        return starts, pos - 1

    def make_toc(starts, placeholder=False):
        ents = []
        for key, _, _, _, title in front[1:]:
            ents.append((1, title, "000" if placeholder else starts[key]))
        last = object()
        for s in segs:
            grp = f"Chapter {s['chapter']}: {chapters[s['chapter']]['title']}" if s["chapter"] else s.get("group")
            if grp != last:
                ents.append((0 if s["chapter"] is None else 1, grp, "000" if placeholder else s["start"]))
                last = grp
            ents.append((2, s["title"], "000" if placeholder else s["start"]))
        return ents

    starts, total = paginate(1)
    _, toc_n = render(toc_html(make_toc(starts, True)), "front_toc_probe")
    starts, total = paginate(toc_n)
    toc_p, toc_n2 = render(toc_html(make_toc(starts)), "front_toc")
    assert toc_n2 == toc_n, "contents length changed between passes"

    # assemble
    w = PdfWriter()
    specs, outline = [], []
    readers = {}

    def rd(path):
        if path not in readers:
            readers[path] = PdfReader(str(path))
        return readers[path]

    def add_own(path, label_tl, label_tr, idxs):
        r = rd(path)
        for i in idxs:
            w.add_page(r.pages[i])
            specs.append((label_tl, label_tr, f"page {len(specs) + 1} of {{N}}"))

    def add_foreign(src, pages, label_tl, label_tr):
        r = rd(SRC_QB if src == "qb" else SRC_WB)
        for p in pages:
            sp = r.pages[p - 1]
            sw, sh = float(sp.mediabox.width), float(sp.mediabox.height)
            s = min(SCALE * A4W / sw, SCALE * A4H / sh)
            blank = PageObject.create_blank_page(width=A4W, height=A4H)
            tx, ty = (A4W - sw * s) / 2, (A4H - sh * s) / 2
            blank.merge_transformed_page(sp, Transformation().scale(s, s).translate(tx, ty))
            w.add_page(blank)
            specs.append((label_tl, label_tr, f"page {len(specs) + 1} of {{N}}"))

    add_own(cover_p, "", "", range(front[0][2]))
    for i in range(front[0][2]):
        specs[i] = ("", "", "")      # no header/footer stamp on the cover
    outline.append((0, "Cover", 0))
    toc_start = len(specs)
    add_own(toc_p, TITLE_SHORT, "Contents", range(toc_n))
    outline.append((0, "Contents", toc_start))
    for key, path, npg, tr, title in front[1:]:
        st = len(specs)
        add_own(path, TITLE_SHORT, tr, range(npg))
        outline.append((0, title, st))

    cur_ch, cur_grp = None, None
    for s in segs:
        st = len(specs)
        if s["chapter"]:
            tl = f"Chapter {s['chapter']}: {chapters[s['chapter']]['title']}"
            grp = tl
        else:
            tl = s.get("group", "Appendix"); grp = tl
        if grp != cur_grp:
            outline.append((0, grp, st)); cur_grp = grp
        outline.append((1, s["title"], st))
        if s["src"] == "own":
            add_own(s["pdf"], hdr(tl), s["label"], s["pages"])
        else:
            add_foreign(s["src"], s["pages"], hdr(tl), s["label"])

    n_total = len(specs)
    specs = [(a, b, c.replace("{N}", str(n_total))) for a, b, c in specs]
    ov = stamp_overlay(specs)
    for i, pg in enumerate(w.pages):
        pg.merge_page(ov.pages[i])

    parent = None
    for lvl, title, pg in outline:
        if lvl == 0:
            parent = w.add_outline_item(title=title, page_number=pg)
        else:
            w.add_outline_item(title=title, page_number=pg, parent=parent)
    w.add_metadata({"/Title": "Accounting Question Bank - CA Certificate Level",
                    "/Subject": "Topic-wise Accounting question bank (ICAB Certificate Level)"})
    w.compress_identical_objects()

    OUT_DIR.mkdir(exist_ok=True)
    out = Path(a.out) if a.out else OUT_DIR / ("Accounting_Question_Bank_original_only.pdf" if a.original_only else "Accounting_Question_Bank_FULL_private.pdf")
    with open(out, "wb") as fh:
        w.write(fh)
    print(f"wrote {out}  ({n_total} pages, {out.stat().st_size / 1e6:.1f} MB)")
    print(f"own content: extra Qs {n_extra}, T/F {n_tf}")


if __name__ == "__main__":
    main()
