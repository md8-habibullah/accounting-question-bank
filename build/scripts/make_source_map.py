#!/usr/bin/env python3
"""Generate docs/SOURCE_MAP.md: chapter -> ICAB workbook pages and ICAEW question-bank pages.
Only page numbers and counts (facts); no copyrighted text. Needs build/data/icaew_map.json (+ workbook_map.json if present)."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
qb = {c["icaew_chapter"]: c for c in json.loads((ROOT / "build/data/icaew_map.json").read_text())}
wbp = ROOT / "build/data/workbook_map.json"
wb = json.loads(wbp.read_text()) if wbp.exists() else {}
# ICAB workbook contents page (printed page numbers)
icab = [("Introduction to accounting", 1), ("The accounting equation", 43), ("Recording financial transactions", 81),
        ("Ledger accounting and double entry", 103), ("Preparing basic financial statements", 143),
        ("Errors and corrections to accounting records and financial statements", 173), ("Cost of sales and inventories", 203),
        ("Irrecoverable debts and the allowance for receivables", 245), ("Accruals and prepayments", 273),
        ("Non-current assets, depreciation and impairment", 307), ("Company financial statements", 361),
        ("Company financial statements under IFRS Accounting Standards", 401), ("Statement of cash flows", 439),
        ("Sole trader financial statements under local GAAP", 475), ("Introduction to Public Financial Management", 489)]
icaew_of = {n: n for n in range(1, 14)}; icaew_of[14] = 15
rows = []
for i, (title, p0) in enumerate(icab, 1):
    p1 = icab[i][1] - 1 if i < len(icab) else None
    pages = f"{p0}-{p1}" if p1 else f"{p0}-end"
    e = icaew_of.get(i)
    if e:
        c = qb[e]
        qpg = f"{c['q_printed'][0]}-{c['q_printed'][1]}"; apg = f"{c['a_printed'][0]}-{c['a_printed'][1]}"; cnt = f"about {c['approx_question_count']}"
        ec = f"{e}"
    else:
        qpg = apg = cnt = "none"; ec = "none"
    w = wb.get(str(i), {})
    iq = (max(w["iq_numbers"]) if w.get("iq_numbers") else 0) if w else "?"
    st = len(w.get("selftest_pages", [])) if w else "?"
    rows.append(f"| {i} | {title} | {pages} | {iq} | {ec} | {qpg} | {apg} | {cnt} |")
pe, uk = qb[16], qb[14]
out = f"""# Source map

Which pages of the two source books belong to which chapter of this question bank. Page numbers are the
**printed** page numbers in each book. (The ICAEW bank has 16 chapters; ICAB chapter 14 corresponds to ICAEW chapter 15;
ICAB chapter 15 has no ICAEW counterpart.)

| Ch. | Chapter (ICAB workbook 2026) | ICAB workbook pages | Interactive questions in workbook | ICAEW chapter | ICAEW questions (pp.) | ICAEW answers (pp.) | ICAEW questions (count) |
|---:|---|---|---:|---|---|---|---|
""" + "\n".join(rows) + f"""

Also in the ICAEW Accounting Question Bank 2024 (used in the personal study edition as appendices):

| Part | Questions (pp.) | Answers (pp.) | Note |
|---|---|---|---|
| Chapter 16: Practice exam | {pe['q_printed'][0]}-{pe['q_printed'][1]} | {pe['a_printed'][0]}-{pe['a_printed'][1]} | ICAEW format (25 questions); useful as a mixed timed practice |
| Chapter 14: Company financial statements under UK GAAP | {uk['q_printed'][0]}-{uk['q_printed'][1]} | {uk['a_printed'][0]}-{uk['a_printed'][1]} | Not in the ICAB contents list; optional |
| Appendix: Mock exam guidance notes | 303-304 | | Maps ICAEW sample exams to chapters |

At the end of each ICAB workbook chapter there are self-test questions with answers ("Self-test questions", then
"Answers to Interactive questions" and "Answers to Self-test questions"); the personal study edition places those pages in each chapter.

To build the personal study edition you need the two original PDFs in `sources/`:
`Accounting_Question_Bank_2024_final.pdf` (ICAEW) and `Accounting_Book_CL26.pdf` (ICAB), plus the page maps in `build/data/`.
"""
(ROOT / "docs/SOURCE_MAP.md").write_text(out, encoding="utf-8")
print("wrote docs/SOURCE_MAP.md")
