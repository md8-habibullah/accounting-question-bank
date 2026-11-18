#!/usr/bin/env python3
"""OCR the scanned ICAB workbook, page by page, resumable.

Usage: ocr_book.py FIRST LAST        (1-based PDF page numbers, inclusive)
Writes extracted/book_pages/pNNN.txt (one file per page) and logs progress to build/ocr_progress.json.
Reads only; does not modify the source PDF. Light on RAM: one page at a time.
"""
import sys, os, json, time, subprocess, tempfile, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "sources" / "Accounting_Book_CL26.pdf"
OUT = ROOT / "extracted" / "book_pages"
PROG = ROOT / "build" / "ocr_progress.json"
OUT.mkdir(parents=True, exist_ok=True)

def main(first, last):
    from rapidocr_onnxruntime import RapidOCR
    eng = RapidOCR()
    todo = [p for p in range(first, last + 1) if not (OUT / f"p{p:03d}.txt").exists()]
    total = last - first + 1
    t0 = time.time(); done0 = total - len(todo)
    tmp = Path(tempfile.mkdtemp(prefix="ocr_", dir=ROOT / "build" / "ocr_tmp"))
    for i, p in enumerate(todo, 1):
        for f in glob.glob(str(tmp / "pg*")): os.remove(f)
        # render at 150 dpi (embedded scan is ~96 ppi; 150 gives the OCR a bit more to work with)
        subprocess.run(["pdftoppm", "-r", "150", "-jpeg", "-f", str(p), "-l", str(p),
                        str(SRC), str(tmp / "pg")], check=True)
        img = sorted(glob.glob(str(tmp / "pg*.jpg")))[0]
        res, _ = eng(img)
        lines = []
        if res:
            # res: [box, text, score]; sort top-to-bottom, then left-to-right, group rows
            items = [(sum(pt[1] for pt in b) / 4, min(pt[0] for pt in b), t) for b, t, s in res]
            items.sort()
            row, rows, ytol = [], [], 12
            for y, x, t in items:
                if row and abs(y - row[-1][0]) > ytol:
                    rows.append(row); row = []
                row.append((y, x, t))
            if row: rows.append(row)
            for r in rows:
                lines.append("   ".join(t for _, _, t in sorted(r, key=lambda z: z[1])))
        (OUT / f"p{p:03d}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        el = time.time() - t0
        PROG.write_text(json.dumps({"range": [first, last], "done": done0 + i, "total": total,
                                    "last_page": p, "elapsed_s": round(el), "s_per_page": round(el / i, 2)}))
    for f in glob.glob(str(tmp / "*")): os.remove(f)
    tmp.rmdir()

if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
