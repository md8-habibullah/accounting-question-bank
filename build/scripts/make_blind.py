#!/usr/bin/env python3
"""Write build/verify/chNN_blind.md = a chapter's practice questions and true/false WITHOUT any answers
(sections N.6 and N.7 only), for independent blind re-solving.  Usage: make_blind.py 07 [08 ...]"""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
(ROOT / "build" / "verify").mkdir(parents=True, exist_ok=True)
for nn in sys.argv[1:]:
    f = next((ROOT / "chapters").glob(f"{nn}-*.md"))
    t = f.read_text(encoding="utf-8")
    secs = {int(m.group(2)): s for s in re.split(r"(?m)^(?=## )", t)[1:] if (m := re.match(r"## (\d+)\.(\d+) ", s))}
    out = f"# Blind question set for chapter {int(nn)}\n\n" + secs[6] + "\n" + secs[7]
    out = re.sub(r"(?m)^<!--space:\d+-->\n?", "", out)
    dst = ROOT / "build" / "verify" / f"ch{nn}_blind.md"
    dst.write_text(out, encoding="utf-8")
    print(dst, f"({len(out.split())} words)")
