#!/usr/bin/env python3
"""Write build/verify/mock_blind.md = the exam paper only (section A.2) of chapters/appendix-a-mock-exam.md,
so a reviewer can solve it without seeing any answer."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
text = (ROOT / "chapters" / "appendix-a-mock-exam.md").read_text(encoding="utf-8")
m = re.search(r"(?ms)^## A\.2 .*?(?=^## A\.3 )", text)
if not m:
    raise SystemExit("section A.2 not found")
out = ROOT / "build" / "verify" / "mock_blind.md"
out.write_text("# Mock exam paper (questions only)\n\n" + m.group(0), encoding="utf-8")
qs = re.findall(r"(?m)^\*\*Q(\d+)\.\*\*", m.group(0))
print(f"{out} ({len(qs)} questions: first {qs[:1]}, last {qs[-1:]}); words {len(m.group(0).split())}")
