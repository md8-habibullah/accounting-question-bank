#!/usr/bin/env python3
"""Read-only live monitor for the workbook OCR job and the chapter files (stdlib only, no network).

  python3 monitor.py          live view, refreshes every 2 s, press q to quit
  python3 monitor.py --once   print a single frame and exit

Reads:  chapters/*.md (word counts), build/ocr_progress.json, extracted/book_pages/*.txt, build/ocr.log, /proc (CPU/RAM of the job)
Writes: nothing.
The job itself READS sources/Accounting_Book_CL26.pdf and WRITES extracted/book_pages/pNNN.txt
(plus short-lived page images in build/ocr_tmp/).
"""
import json, os, sys, time, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROG = ROOT / "build" / "ocr_progress.json"
PAGES = ROOT / "extracted" / "book_pages"
LOG = ROOT / "build" / "ocr.log"
TOTAL_DEFAULT = 537


def job_pids():
    try:
        out = subprocess.run(["pgrep", "-f", "ocr_book.py"], capture_output=True, text=True).stdout.split()
        return [int(p) for p in out if int(p) != os.getpid()]
    except Exception:
        return []


def proc_stats(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            rss = next((int(l.split()[1]) for l in f if l.startswith("VmRSS")), 0)
        with open(f"/proc/{pid}/stat") as f:
            parts = f.read().rsplit(")", 1)[1].split()
        ticks = int(parts[11]) + int(parts[12])
        return rss / 1024, ticks
    except Exception:
        return 0, 0


def bar(frac, width=40):
    n = int(frac * width)
    return "[" + "#" * n + "-" * (width - n) + f"] {frac * 100:5.1f}%"


def fmt(sec):
    sec = int(sec)
    return f"{sec // 3600}h {sec % 3600 // 60:02d}m {sec % 60:02d}s" if sec >= 3600 else f"{sec // 60}m {sec % 60:02d}s"


def frame(prev=[None]):
    lines = []
    done_files = len(list(PAGES.glob("p*.txt"))) if PAGES.exists() else 0
    try:
        pr = json.loads(PROG.read_text())
    except Exception:
        pr = {}
    first, last = (pr.get("range") or [1, TOTAL_DEFAULT])
    total = last - first + 1
    done = pr.get("done", 0)
    spp = pr.get("s_per_page") or 0
    eta = (total - done) * spp if spp else 0
    pids = job_pids()
    state = "RUNNING" if pids else ("FINISHED" if done >= total and total else "IDLE / not running")
    lines.append("OCR of ICAB Accounting Workbook (scanned, 537 pages)   -   " + state)
    lines.append("")
    lines.append("progress  " + bar(done / total if total else 0))
    lines.append(f"pages     {done} / {total}   (range {first}-{last}, last page done: {pr.get('last_page', '-')})")
    lines.append(f"speed     {spp:.1f} s/page      elapsed {fmt(pr.get('elapsed_s', 0))}      ETA {fmt(eta) if eta else '-'}")
    lines.append(f"output    {done_files} page-text files in extracted/book_pages/")
    if pids:
        pids.sort(key=lambda p: proc_stats(p)[0], reverse=True)  # the python worker, not the nice/nohup wrapper
        rss, ticks = proc_stats(pids[0])
        now = time.time()
        cpu = 0.0
        if prev[0] and now > prev[0][0]:
            cpu = (ticks - prev[0][1]) / os.sysconf("SC_CLK_TCK") / (now - prev[0][0]) * 100
        prev[0] = (now, ticks)
        lines.append(f"job       pid {pids[0]}   CPU {cpu:4.0f}%   RAM {rss:,.0f} MB")
    try:
        la = open("/proc/loadavg").read().split()[:3]
        mem = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo") if l.split(":")[0] in ("MemAvailable", "SwapFree")}
        lines.append(f"system    load {' '.join(la)}   RAM available {mem['MemAvailable'] / 1048576:.1f} GB")
    except Exception:
        pass
    lines.append("")
    lines.append("reads:   sources/Accounting_Book_CL26.pdf (read-only)")
    lines.append("writes:  extracted/book_pages/pNNN.txt  (+ temp page image in build/ocr_tmp/)")
    lines.append("")
    lines.append("last OCR'd pages (first line):")
    recent = sorted(PAGES.glob("p*.txt"))[-4:] if PAGES.exists() else []
    for f in recent:
        try:
            first_line = next((l.strip() for l in f.read_text(errors="ignore").splitlines() if l.strip()), "")
        except Exception:
            first_line = ""
        lines.append(f"  {f.stem}: {first_line[:90]}")
    ch = sorted((ROOT / "chapters").glob("[0-9][0-9]-*.md"))
    ch = [f for f in ch if f.name[:2] != "00"]
    lines.append("")
    lines.append(f"chapters written (markdown): {len(ch)} / 15")
    for f in ch:
        words = len(f.read_text(errors="ignore").split())
        lines.append(f"  {f.name:<52} {words:>6,} words")
    mock = ROOT / "chapters" / "appendix-a-mock-exam.md"
    if mock.exists():
        t = mock.read_text(errors="ignore")
        import re as _re
        nq = len(_re.findall(r"(?m)^\*\*Q\d+\.\*\*", t)); na = len(_re.findall(r"(?m)^\*\*Q\d+\. Answer", t))
        lines.append(f"mock exam draft: {len(t.split()):,} words, {nq} questions, {na} answers (target 50 / 50)")
    ver = ROOT / "build" / "verify"
    reps = sorted(p.name[:-10] for p in ver.glob("*_report.md")) if ver.exists() else []
    lines.append("blind-check reports written: " + (", ".join(reps) if reps else "none"))
    if LOG.exists():
        lines.append("")
        lines.append("log tail:")
        for l in LOG.read_text(errors="ignore").splitlines()[-4:]:
            lines.append("  " + l[:100])
    return "\n".join(lines)


def main():
    if "--once" in sys.argv:
        print(frame())
        return
    import select, termios, tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            sys.stdout.write("\033[H\033[2J" + frame() + "\n\n(press q to quit)\n")
            sys.stdout.flush()
            r, _, _ = select.select([sys.stdin], [], [], 2)
            if r and sys.stdin.read(1).lower() == "q":
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


if __name__ == "__main__":
    main()
