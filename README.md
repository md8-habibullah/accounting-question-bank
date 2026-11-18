# Accounting Question Bank for the CA Certificate Level (ICAB)

A topic-wise, beginner-friendly question bank for the **ICAB Certificate Level "Accounting" exam**
(1.5 hours, 50 questions x 2 marks, multiple choice and multiple response).
It follows the 15 chapters of the ICAB Accounting Workbook 2026 and adds the ICAEW Accounting
Question Bank 2024 chapter by chapter (the ICAEW bank is the exam-standard question set that the ICAB
workbook itself points students to).

Everything is written in plain Markdown so it can be read on GitHub, edited, and turned into a PDF.

## What is in each chapter

| Part | Content |
|---|---|
| Learn | Plain-English explanation, key facts, formulas and layouts, worked examples, exam traps |
| Extra practice | 10 original questions per chapter: 8 exam-style (multiple choice / multiple response) and 2 tricky scenario questions (statement of financial position, statement of profit or loss, cash flow links) with blank space for the answer |
| True or false | 8 statements per chapter, each with the reason |
| Answers | Every answer with *why*, the formula used, an easy example and why the other options are wrong |

`chapters/00-how-to-use.md` has the exam facts, the syllabus weightings, a 3/5/7-day study plan and exam technique.
`chapters/appendix-a-mock-exam.md` is an original 50-question mock exam (90 minutes, weighted like the real syllabus) with a full answer for every question and a score sheet that tells you which chapters to revise.
The generated PDF also contains an automatic formula sheet that collects every `> **FORMULA**` line.

## Chapters

See [docs/SOURCE_MAP.md](docs/SOURCE_MAP.md) for the full table (ICAB workbook pages and ICAEW question-bank pages for each chapter).

## Repository layout

| Path | What it is |
|---|---|
| `chapters/` | The content: one Markdown file per chapter (`01-...` to `15-...`), plus `00-how-to-use.md` and `appendix-a-mock-exam.md` |
| `docs/STYLE_GUIDE.md` | The strict structure every chapter follows (also the rules for adding or editing content) |
| `docs/SOURCE_MAP.md` | Which pages of the ICAB workbook and the ICAEW question bank belong to which chapter |
| `build/scripts/` | PDF builder, structure checker (`lint_chapters.py`), helpers |
| `output/Accounting_Question_Bank_original_only.pdf` | The PDF with the original content only (safe to share) |

## Copyright: what is NOT in this repository

The ICAEW Accounting Question Bank (copyright ICAEW) and the ICAB Accounting Workbook (copyright ICAB) are
copyrighted. This repository contains **only original text written for this project** (apart from short standard definitions, such as the Conceptual Framework's definitions of an asset and a liability, and the syllabus headings, which are quoted for orientation). The source PDFs, the
text extracted from them, and the personal-study PDF that includes copied pages are excluded by `.gitignore`
and must not be published or shared.

If you own the two source PDFs, you can build a **personal study edition** on your own computer that places
the ICAEW questions and answers (and the ICAB interactive and self-test question pages) inside each chapter.
Keep that file private.

## Building the PDF

Needs Python 3.11+ and the system libraries for WeasyPrint (Pango/Cairo). Fonts: Inter (falls back to DejaVu Sans).

```bash
python3 -m venv build/.venv-pdf
build/.venv-pdf/bin/pip install "weasyprint==70.0" "markdown==3.11.3" "pypdf==7.1.1" "reportlab==4.5.1"

# check the structure of every chapter
python3 -I build/scripts/lint_chapters.py

# original content only (no copied pages)
build/.venv-pdf/bin/python -I build/scripts/build_pdf.py --original-only

# personal study edition (needs the two source PDFs in sources/, see docs/SOURCE_MAP.md); do NOT share the result
build/.venv-pdf/bin/python -I build/scripts/build_pdf.py
```

## How the content was checked

Every number in the original questions was calculated with a script. Each of the 15 chapters and the mock exam was then
re-solved by an independent reviewer working only from the questions (answers hidden) and compared with the written
answers. Differences were investigated and fixed: mostly questions that did not state a convention they depended on, a few
explanation notes and some loose wording. No unresolved disagreement remained after the fixes. The reviewers' working
notes quote the source books, so they are kept on the author's computer and are not part of this repository.

Known limits:

- The ICAB workbook uses "CU" and some older words (stock, debtors, creditors, profit and loss account). This book uses
  pounds and the IFRS words, and gives a vocabulary table in Chapter 14.
- Chapter 14: the workbook never says what "local GAAP" means and has no partnership calculations, so this book does not
  claim more.
- Chapter 15 follows the workbook only (there is no ICAEW material). Where the workbook words something two ways, the
  chapter says so. One workbook page (printed page 504) is unreadable in the scan.
- The exam instructions on how wrong answers are marked are not in the sources, so this book gives no pass mark and
  no negative-marking rule. Read the instruction page of the real exam.
- If you find an error, please open an issue or correct the chapter file.

## Disclaimer

This is study material, not professional advice. Where it differs from your ICAB workbook, tutor or the
exam instructions, follow the ICAB workbook and your tutor.
