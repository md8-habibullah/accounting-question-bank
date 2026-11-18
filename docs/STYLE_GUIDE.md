# Style guide for chapter files

Every chapter lives in `chapters/NN-short-title.md` (NN = two digits, ICAB workbook chapter number).
The PDF builder (`build/scripts/build_pdf.py`) reads these files, so the structure below is **strict**.
The model chapter to copy in quality, depth and format is **`chapters/09-accruals-and-prepayments.md`**. Read it fully first.

## Audience and tone

- A complete beginner preparing for the **ICAB Certificate Level "Accounting" exam** (1.5 hours, 50 questions x 2 marks, multiple choice and multiple response). English is a second language for many readers: short sentences, plain words, define every technical word the first time.
- Explain *why*, not only *what*. Use everyday comparisons (shop, tea stall, gym fee, school fees, rickshaw, mobile top-up) before the accounting version.
- UK spelling (organisation, recognise, practise as verb). Exam vocabulary of IFRS / the ICAB workbook: *statement of profit or loss*, *statement of financial position*, *trade receivables*, *trade payables*, *inventories*, *non-current assets*, *revenue*, *cost of sales*, *irrecoverable debts*, *allowance for receivables*. Say "balance sheet" in brackets the first time, because students know that name.
- Currency: **£** in all numerical questions (the ICAEW exam-standard bank uses £; the ICAB workbook uses "CU"; the arithmetic is identical). Years as 20X1, 20X2, ... Use varied names and small businesses (Bangladeshi, British and neutral names). No emoji. No decorative symbols.

## Required headings (exact numbering, in this order)

```
# Chapter N: Title                         <- title as in the ICAB workbook contents page
## N.1 Start here: the idea in plain English
## N.2 Key facts to remember
## N.3 Formulas and layouts
## N.4 Worked examples
## N.5 Exam traps
## N.6 Extra practice questions
## N.7 True or false
## N.8 Answers and explanations
```

Inside N.4 use `### Example 1: ...` headings. Inside N.6 use `**Q1.**` ... `**Q8.**` for exam-style questions and `### Q9. Scenario: ... (marks)` / `### Q10. Scenario: ...` for the two scenario questions. Inside N.8 use `### Answers: extra practice questions` and `### Answers: true or false`.

## What each section must contain

- **N.1** plain-English story (2 to 4 short paragraphs), a mini-table of new words if useful, and one `> **REMEMBER**` or `> **KEY FACT**` box.
- **N.2** bullet list of the facts the exam tests: definitions, rules, double entry (Dr/Cr) where relevant, statement presentation, effect on profit / assets / liabilities / cash.
- **N.3** every formula as its own `> **FORMULA** ...` line (one line each, plain text, no LaTeX). Add ledger / statement **layouts** as markdown tables (T-account, extract of statement of profit or loss, statement of financial position, cash-flow layout) where relevant.
- **N.4** 3 to 5 fully worked examples, step by step, numbers shown, ending with the answer in bold. At least one example in statement layout. Use `*Easy way to see it:*` lines for intuition.
- **N.5** 5 to 8 numbered exam traps (what students get wrong and why).
- **N.6** **exactly 10 extra questions**: Q1 to Q8 exam-style (single choice A to D, and at least two "(Select TWO.)" or "(Select THREE.)" multiple-response questions; most with a calculation; at least one tempting-wrong-answer "tricky" question) and **Q9, Q10 = two tricky scenario questions** (each a full business situation with several data items and a numbered **Required** list; one must be a *statement* style task (statement of financial position, statement of profit or loss or a reconciliation, as suits the chapter); the other should connect the topic to cash / the statement of cash flows or to the effect on profit and the balance sheet). Scenario questions end with `<!--space:N-->` (N = blank answer space in millimetres, 50 to 90). Give marks in the heading, e.g. `(12 marks)`.
- **N.7** **8 true/false** statements written as `**T/F 1.** Statement. *(True / False)*` (exactly that tail, it becomes two tick circles in the PDF). Mix true and false (about half each); make false ones plausible.
- **N.8** a full answer for every question and statement (see below).

For ICAB chapter 15 (Public Financial Management) there is no ICAEW material: write 12 objective questions (Q1 to Q10 objective, then two scenario / case questions as Q11 and Q12) and 10 true/false statements, and scale the learning sections to the workbook's content. For chapters that are mostly conceptual (1, 2) the two scenario questions can be classification / effect-on-the-statements cases, but should still include numbers and a simple statement.

## Answer format (N.8)

For each objective question:

```
**Q1. Answer: B (£1,800)**

- **Why:** one or two sentences, plain English.
- **Formula:** the working with numbers (omit if not numerical).
- **Easy example:** a daily-life comparison.
- **Why not the others:** one short clause for each wrong option (A, C, D).
```

For scenario questions: full worked answer with the **statement tables laid out properly** (workings table(s) then the statement), a short *marking tips* line naming the trap(s), and a check (a figure that must agree). True/false answers go in one table `| # | Answer | Reason and easy example |`.

## Markdown rules (the PDF builder depends on them)

- Callout boxes: a blockquote that starts with a bold label: `> **FORMULA**`, `> **KEY FACT**`, `> **REMEMBER**`, `> **EXAM TRAP**`, `> **EXAMPLE**`. One label per blockquote paragraph. Keep boxes short (1 to 3 lines).
- Multiple choice options are a bullet list, one option per line, starting `- A) `, `- B) `, `- C) `, `- D) `. A blank line between the question text and the list.
- **Nested bullets need 4 spaces of indentation** (2 spaces does not nest).
- Tables are normal GitHub tables. Right-align numbers with `---:`. Put totals in bold. Negative numbers in brackets: (500). Include a `£` column header or `£` in the heading, not in every cell.
- Minus sign `−` (U+2212), multiply `×`, divide `÷` are fine. No LaTeX, no HTML except the `<!--space:N-->` answer-space marker, no images, no emoji, no footnotes.
- Do not use `---` horizontal rules as separators (they are not needed).
- No front matter block. File must start with `# Chapter N: Title`.

## Content rules

1. **Original work only.** Do **not** copy or closely paraphrase any question, example, table or sentence from the ICAEW Question Bank or the ICAB workbook. Read them to learn the syllabus scope, terminology and exam style; then write new questions with new businesses and new numbers. Short standard definitions (for example the Conceptual Framework's definition of an asset) may be quoted briefly.
2. **Every number must be right.** Compute every figure with a Python snippet (Bash: `python3 -I -c '...'`) and re-check totals, balancing figures and "check" lines before writing them down. Statements must balance; T-accounts must balance. Each distractor in a multiple-choice question must be a *plausible mistake*, and you must be able to name the mistake in "Why not the others".
3. **Exam style.** ICAB questions are objective (multiple choice / multiple response). Questions should look like exam questions: a short business situation, clear numbers, one clear task.
4. **Aligned with the ICAB workbook.** Terminology, formats and methods (for example the layout of the statement of profit or loss, how the allowance for receivables is calculated) must match the ICAB workbook for that chapter. Where the workbook and general textbooks differ, follow the workbook.
5. **Cover the whole chapter scope** (all topics in the workbook chapter's contents and the ICAEW question-bank chapter), weighted by what an exam would test.
6. No claims about the exam that you cannot support from the sources (do not invent pass marks, dates, fees).
7. Length guide: N.1 to N.5 together about 1,800 to 2,800 words; the whole chapter about 3,800 to 7,000 words. Quality and correctness matter more than length.
