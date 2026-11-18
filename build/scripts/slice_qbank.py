#!/usr/bin/env python3
"""Map the ICAEW Accounting Question Bank into chapters (PDF page ranges) and slice its text.

Printed page numbers from the QB's contents page; PDF page = printed + 8 (verified for every chapter).
Writes build/data/icaew_map.json and extracted/qbank_ch/chNN_{questions,answers}.txt.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
pages = (ROOT / "extracted" / "qbank.txt").read_text(encoding="utf-8").split("\f")[:312]
OFF = 8
Q = [1, 7, 11, 15, 19, 23, 33, 47, 55, 67, 81, 95, 125, 143, 145, 151]   # printed page where each chapter's questions start
A = [163, 167, 169, 171, 173, 175, 183, 191, 197, 205, 219, 231, 265, 285, 287, 291]
Q_END_LAST = 168   # pdf page before the "Answer Bank" divider (169)
A_END_LAST = 310   # last answers page before the mock-exam appendix (311)
TITLES = ["Introduction to accounting", "The accounting equation", "Recording financial transactions",
          "Ledger accounting and double entry", "Preparing basic financial statements",
          "Errors and corrections to accounting records and financial statements",
          "Cost of sales and inventories", "Irrecoverable debts and allowance for receivables",
          "Accruals and prepayments", "Non-current assets and depreciation", "Company financial statements",
          "Company financial statements under IFRS Accounting Standards", "Statement of cash flows",
          "Company financial statements under UK GAAP", "Sole trader financial statements under UK GAAP",
          "Practice exam"]

FOOT = re.compile(r"^\s*(?:\d+\s+Accounting\s+ICAEW 2024|ICAEW 2024\s+.*|Accounting\s+ICAEW 2024)\s*$|^\s*\d+\s*$")

def is_blank(txt):
    """Page carries nothing but a footer/page number (the QB's 'intentionally empty' separator pages)."""
    body = [l for l in txt.splitlines() if l.strip() and not FOOT.match(l.strip())]
    return len(" ".join(body)) < 25

def rng(a, b):
    return [p for p in range(a, b + 1)]

out = []
(ROOT / "extracted" / "qbank_ch").mkdir(parents=True, exist_ok=True)
for i in range(16):
    qa, qb = Q[i] + OFF, (Q[i + 1] + OFF - 1 if i < 15 else Q_END_LAST)
    aa, ab = A[i] + OFF, (A[i + 1] + OFF - 1 if i < 15 else A_END_LAST)
    qp = [p for p in rng(qa, qb) if not is_blank(pages[p - 1])]
    ap = [p for p in rng(aa, ab) if not is_blank(pages[p - 1])]
    qtxt = "\f".join(pages[p - 1] for p in qp)
    atxt = "\f".join(pages[p - 1] for p in ap)
    n = i + 1
    (ROOT / "extracted" / "qbank_ch" / f"ch{n:02d}_questions.txt").write_text(qtxt, encoding="utf-8")
    (ROOT / "extracted" / "qbank_ch" / f"ch{n:02d}_answers.txt").write_text(atxt, encoding="utf-8")
    # count questions: leading numbers 1,2,3... at line start, take the highest value in a sequential run
    nums = [int(m.group(1)) for m in re.finditer(r"(?m)^\s{0,3}(\d{1,2})\s+(?=[A-Za-z£])", qtxt)]
    cnt, expect = 0, 1
    for x in nums:
        if x == expect:
            cnt, expect = x, expect + 1
    out.append({"icaew_chapter": n, "title": TITLES[i],
                "q_printed": [Q[i], (Q[i + 1] - 1 if i < 15 else 161)], "a_printed": [A[i], (A[i + 1] - 1 if i < 15 else 302)],
                "q_pdf_pages": qp, "a_pdf_pages": ap, "approx_question_count": cnt})
(ROOT / "build" / "data" / "icaew_map.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
for c in out:
    print(f"ICAEW ch{c['icaew_chapter']:>2} {c['title'][:48]:<48} Q pdf {c['q_pdf_pages'][0]:>3}-{c['q_pdf_pages'][-1]:>3} ({len(c['q_pdf_pages']):>2} pp)  "
          f"A pdf {c['a_pdf_pages'][0]:>3}-{c['a_pdf_pages'][-1]:>3} ({len(c['a_pdf_pages']):>2} pp)  ~{c['approx_question_count']} questions")
print("total Q pages", sum(len(c['q_pdf_pages']) for c in out), "| total A pages", sum(len(c['a_pdf_pages']) for c in out))
