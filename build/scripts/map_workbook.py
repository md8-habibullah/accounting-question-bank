#!/usr/bin/env python3
"""Find, per ICAB workbook chapter, the pages with interactive questions (IQs) and the answers section.

Input : extracted/book_pages/pNNN.txt (OCR of the scanned workbook)
Output: build/data/workbook_map_draft.json  {chapter: {start, end, iq_pages, iq_numbers, selftest_pages, answers_start, answer_pages}}
Heuristics (OCR text is noisy, so everything is matched with spaces removed):
  - chapter opener: one of the first 6 lines is exactly "Chapter <n>"
  - IQ question: a line that starts with "Interactive question <n>"
  - the question continues onto the next page unless a "See Answer ..." line follows the header on the same page
  - "Self-test questions" section: from its heading page up to the first answers page
  - answers: from "Answers to Interactive questions" / "Answers to Self-test questions" to the end of the chapter
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "extracted" / "book_pages"
LAST_PDF_PAGE = 536   # page 537 is the back cover

def load():
    d = {}
    for f in sorted(PAGES.glob("p*.txt")):
        d[int(f.stem[1:])] = f.read_text(errors="ignore").splitlines()
    return d

def squash(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

def main():
    pg = load()
    if not pg:
        sys.exit("no OCR pages yet")
    maxp = max(pg)
    starts = {}
    for p in sorted(pg):
        for ln in pg[p][:6]:
            m = re.fullmatch(r"chapter(\d{1,2})", squash(ln))
            if m:
                n = int(m.group(1))
                if n not in starts and 1 <= n <= 15:
                    starts[n] = p
    out = {}
    order = sorted(starts)
    for i, n in enumerate(order):
        s = starts[n]
        e = (starts[order[i + 1]] - 1) if i + 1 < len(order) else LAST_PDF_PAGE
        complete = (i + 1 < len(order)) or maxp >= LAST_PDF_PAGE
        if not complete:
            out[n] = {"start": s, "end": None, "note": "OCR incomplete"}
            continue
        def heading(pattern, lo, hi):
            """first page in [lo, hi] with a line that is exactly this heading (the opener page lists headings too, so skip it)"""
            for p in range(lo, hi + 1):
                if any(re.fullmatch(pattern, squash(ln)) for ln in pg.get(p, [])[:6]):
                    return p
            return None

        ans_iq = heading(r"answers?to(the)?interactivequestions?", s + 1, e)
        ans_st = heading(r"answers?to(the)?self(test)?questions?", s + 1, e)
        st = heading(r"selftest(questions?)?", s + 1, e)
        first_answers = min([x for x in (ans_iq, ans_st) if x] or [None]) if (ans_iq or ans_st) else None
        # self-test questions sit between their heading and the first answers page
        st_end = (first_answers - 1) if (st and first_answers and first_answers > st) else None
        q_end = (st - 1) if st else ((first_answers - 1) if first_answers else e)
        iq_pages, nums = set(), []
        done = lambda txt: "seeanswer" in squash(txt) or "answerattheend" in squash(txt)

        def add_iq(p, k):
            cur = p
            iq_pages.add(cur)
            txt = " ".join(pg.get(p, [])[k:])
            while not done(txt) and cur + 1 <= q_end and cur - p < 2:
                cur += 1
                iq_pages.add(cur)
                txt = " ".join(pg.get(cur, []))

        for p in range(s, q_end + 1):
            lines = pg.get(p, [])
            for k, ln in enumerate(lines):
                m = re.match(r"^\W{0,3}[Il1]nteractive\s*[Qq]\w{3,9}\s*(\d+)\b", ln.strip())
                if m:
                    nums.append(int(m.group(1)))
                    add_iq(p, k)
        # fallback for headers the OCR merged into a longer line: use the numbering of the answers section
        ans_pages = range(first_answers, e + 1) if first_answers else []
        ans_nums = [int(x) for q in ans_pages for ln in pg.get(q, [])
                    for x in re.findall(r"(?i)interactive\s*question\s*(\d+)", ln)]
        top = max(ans_nums + nums, default=0)
        for need in [x for x in range(1, top + 1) if x not in nums]:
            for p in range(s, q_end + 1):
                hit = [k for k, ln in enumerate(pg.get(p, []))
                       if re.search(rf"(?i)interactive\s*q\w{{3,9}}\s*{need}(?!\d)", ln) and not re.search(r"(?i)see|answer", ln)]
                if hit:
                    nums.append(need)
                    add_iq(p, hit[0])
                    break
        out[n] = {"start": s, "end": e, "iq_numbers": sorted(set(nums)), "iq_pages": sorted(iq_pages),
                  "selftest_pages": list(range(st, st_end + 1)) if (st and st_end) else [],
                  "answers_start": first_answers, "answer_pages": list(range(first_answers, e + 1)) if first_answers else []}
    (ROOT / "build" / "data" / "workbook_map_draft.json").write_text(json.dumps(out, indent=1))
    for n in sorted(out):
        o = out[n]
        if o.get("end") is None:
            print(f"ch{n:>2}: starts p{o['start']} (OCR incomplete)"); continue
        print(f"ch{n:>2}: pp {o['start']}-{o['end']} | IQs {o['iq_numbers']} on {len(o['iq_pages'])} pp {o['iq_pages']} | self-test pp {o['selftest_pages']} | answers pp {o['answer_pages'][:1]}..{o['answer_pages'][-1:]}")

if __name__ == "__main__":
    main()
