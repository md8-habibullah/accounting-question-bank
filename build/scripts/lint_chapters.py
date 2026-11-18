#!/usr/bin/env python3
"""Structure / style lint for chapters/NN-*.md (see docs/STYLE_GUIDE.md). Exit code 1 if any ERROR.

  python3 -I build/scripts/lint_chapters.py            # all chapters
  python3 -I build/scripts/lint_chapters.py 07 08      # selected chapters
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅❌]")
LABELS = {"FORMULA", "KEY FACT", "REMEMBER", "EXAM TRAP", "EXAMPLE", "WHY"}

def lint(f):
    errs, warns = [], []
    t = f.read_text(encoding="utf-8")
    n = int(f.name[:2])
    pfm = (n == 15)
    m = re.match(r"# Chapter (\d+): (.+)\n", t)
    if not m or int(m.group(1)) != n:
        errs.append("first line must be '# Chapter N: Title' with N = file number")
    secs = re.split(r"(?m)^(?=## )", t)[1:]
    heads = [re.match(r"## (\d+)\.(\d+) (.+)", s) for s in secs]
    if [ (int(h.group(1)), int(h.group(2))) if h else None for h in heads] != [(n, k) for k in range(1, 9)]:
        errs.append("headings must be exactly '## N.1' ... '## N.8' in order: found " + str([h.group(0)[:20] if h else '??' for h in heads]))
        return errs, warns, t
    S = {int(h.group(2)): s for h, s in zip(heads, secs)}
    # N.6 questions
    nobj = 10 if pfm else 8
    for q in range(1, nobj + 1):
        if not re.search(rf"(?m)^\*\*Q{q}\.\*\*", S[6]):
            errs.append(f"N.6: missing '**Q{q}.**'")
    scen = [11, 12] if pfm else [9, 10]
    for q in scen:
        if not re.search(rf"(?m)^### Q{q}\. Scenario", S[6]):
            errs.append(f"N.6: missing '### Q{q}. Scenario: ...'")
    if len(re.findall(r"<!--space:\d+-->", S[6])) < 2:
        errs.append("N.6: each scenario question needs a <!--space:N--> marker")
    opts = re.findall(r"(?m)^- ([A-D])\) ", S[6])
    if len(opts) < 4 * nobj - 4 or len(opts) > 4 * nobj + 8:
        warns.append(f"N.6: {len(opts)} option lines (expected about {4 * nobj})")
    if not re.search(r"\(Select (TWO|THREE)\.\)", S[6]):
        warns.append("N.6: no multiple-response question ('(Select TWO.)') found")
    # N.7
    tf = re.findall(r"(?m)^\*\*T/F (\d+)\.\*\* .+\*\(True / False\)\*\s*$", S[7])
    want_tf = 10 if pfm else 8
    if len(tf) != want_tf:
        errs.append(f"N.7: {len(tf)} well-formed T/F statements, expected {want_tf}")
    # N.8
    if "### Answers: extra practice questions" not in S[8]:
        errs.append("N.8: missing '### Answers: extra practice questions'")
    if "### Answers: true or false" not in S[8]:
        errs.append("N.8: missing '### Answers: true or false'")
    for q in list(range(1, nobj + 1)) + scen:
        if not re.search(rf"(?m)^\*\*Q{q}\. Answer", S[8]):
            errs.append(f"N.8: missing '**Q{q}. Answer ...**'")
    rows = re.findall(r"(?m)^\| (\d+) \| \*\*(True|False)\*\* \|", S[8])
    if len(rows) != want_tf:
        errs.append(f"N.8: {len(rows)} T/F answer rows, expected {want_tf}")
    # content / markdown rules
    if len(re.findall(r"(?m)^> \*\*FORMULA\*\*", S[3])) < 1:
        warns.append("N.3: no '> **FORMULA**' line")
    for lab in set(re.findall(r"(?m)^> \*\*([A-Z ]+)\*\*", t)):
        if lab not in LABELS:
            errs.append(f"unknown callout label '{lab}'")
    if EMOJI.search(t):
        errs.append("emoji found")
    if re.search(r"(?m)^\s*---+\s*$", t):
        errs.append("horizontal rule '---' found (not allowed)")
    if re.search(r"\$[^$\n]{1,40}\$", t) or "\\frac" in t or "\\times" in t:
        warns.append("possible LaTeX")
    tags = set(re.findall(r"</?([a-zA-Z][a-zA-Z0-9]*)", re.sub(r"<!--.*?-->", "", t)))
    if tags:
        errs.append(f"HTML tags present: {sorted(tags)}")
    if re.search(r"!\[", t):
        errs.append("image syntax found")
    if re.search(r"(?m)^  - ", t):
        errs.append("bullet indented 2 spaces: nested bullets need 4 spaces")
    if "<!--space" in t and not re.search(r"(?m)^<!--space:\d+-->$", t):
        errs.append("space marker must be alone on its line")
    for label in ("Why:", "Easy example:"):
        if len(re.findall(rf"\*\*{label}\*\*", S[8])) < 4:
            warns.append(f"N.8: fewer than 4 '**{label}**' bullets")
    words = len(t.split())
    if words < 3500:
        warns.append(f"short chapter: {words} words")
    return errs, warns, t

def main():
    want = set(sys.argv[1:])
    files = [f for f in sorted((ROOT / "chapters").glob("[0-9][0-9]-*.md")) if f.name[:2] != "00" and (not want or f.name[:2] in want)]
    bad = 0
    for f in files:
        e, w, t = lint(f)
        print(f"{f.name}: {len(t.split()):,} words | {len(e)} errors, {len(w)} warnings")
        for x in e: print("   ERROR  ", x)
        for x in w: print("   warning", x)
        bad += len(e)
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
