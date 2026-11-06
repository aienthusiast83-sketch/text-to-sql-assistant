# 🎵 Text-to-SQL Assistant

Ask business questions in plain English and get the answer straight from a database: the SQL, the result table, a chart, and a one-line summary. Built as a hands-on AI project by a BI engineer, using the Claude API and the Chinook music-store sample database.

> **"Top 5 artists by revenue by year"** → Claude writes the SQL → it runs read-only → you see a table, a line chart (one line per artist) and a plain-English answer. In this case the chart revealed that Iron Maiden, Metallica and Led Zeppelin all dipped sharply in 2011 while U2 stayed steady.

## What it does

- **Plain English in, SQL out**: no SQL knowledge needed to ask a question
- **Plain-English summary** written only from the numbers in the result (no guessing)
- **Smart charts**: line chart for trends over time (one line per category), bar chart for rankings, always in the order the query chose
- **Self-correction**: if a query fails, the error is sent back to Claude to fix it (up to 2 retries)
- **Refuses data changes**: "delete all customers" gets "I can only read data, not change or delete it."
- **Privacy mode**: a sidebar switch that keeps result rows on your computer; only the schema and the question are sent to the AI

## How it works

1. **Read the schema**: the app reads the table structure from the database so Claude knows the real tables and columns.
2. **Generate SQL**: the schema, a short set of rules and the question are sent to Claude (Haiku 5.5).
3. **Check safety**: only a single `SELECT` / `WITH` query is allowed.
4. **Run read-only**: the database is opened in read-only mode, then the result is shown with a summary and a chart.

**Two independent safety layers** (defence in depth): even if a harmful query slipped past the check in step 3, the read-only database refuses to change anything. Both layers are proven by `test_safety.py`.

## Data privacy

**What the AI sees:** when writing SQL, Claude gets only the table and column names plus the question, never the data. The SQL runs locally on a read-only connection; Claude never connects to the database.

**Where data could leave the system:** the plain-English summary sends up to 30 result rows to Claude, and self-correction sends database error messages. **Privacy mode** switches the summary off, so result rows never leave the computer.

**In a real company I would also add:** curated views without personal data (names, emails, salaries), a least-privilege read-only database user with row limits, aggregate-only summaries, running the model inside the company's own cloud (for example Claude on AWS Bedrock), masking, and audit logs of every question and query.

## Measuring accuracy

I wrote 20 test questions with verified answer SQL (from easy counts to window functions, ties and "never bought" questions). `evaluate.py` asks the assistant all 20, runs the answer key, compares the results and prints a score.

| Step | Score | What happened |
| --- | --- | --- |
| First run | 14/19 (74%) | 3 of the 5 failures were bugs in my own marking script (pandas 3 text type), not the AI |
| True baseline | 17/19 (89%) | Real mistakes: hid a tie (ROW_NUMBER), ignored "latest year" |
| Improved prompt | 18/19 (95%) | Two general rules added; tie fixed, nothing else broke |
| Answer-key review | 19/19 (100%) | On the last question the AI's reading (January vs the previous December) was the better business logic, so the answer key was updated |

Question 20 ("Who are our best customers?") is deliberately vague and is reviewed by hand rather than scored.

## Lessons learned

- **Grade the grader**: a low score can be a bug in your test, not the AI.
- **Fix with general rules, not test answers**: otherwise the score lies (overfitting).
- **Never trust AI formatting 100%**: the code cleans up the output itself.
- **Two correct-looking queries can disagree**: ties need `RANK()`, not `ROW_NUMBER()`.
- **An empty result can be the right answer**: verify before calling it wrong.
- **A chart can be correct and still misleading**: chart the measure that answers the question.

## Cost

About **₹0.03 per question** on Claude Haiku 5.5 (≈2,800 input + ≈170 output tokens). About 99% of the input is the database schema. A full 20-question evaluation costs about ₹0.75.

## Run it yourself

Requirements: Python 3, an Anthropic API key, and the Chinook SQLite file from [lerocha/chinook-database](https://github.com/lerocha/chinook-database) (Releases → `Chinook_Sqlite.sqlite`) placed in the project folder.

```bash
python3 -m venv venv
source venv/bin/activate
pip install streamlit pandas anthropic python-dotenv
```

Create a file named `.env` with your key (it is listed in `.gitignore`, so it never goes to GitHub):

```
ANTHROPIC_API_KEY=your-key-here
```

Then:

```bash
streamlit run app.py          # web app at http://localhost:8501
python text_to_sql.py         # terminal version
python test_safety.py         # prove both safety layers
python evaluate.py baseline   # run the 20-question evaluation
```

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit web page: question box, SQL, summary, table, smart chart |
| `text_to_sql.py` | The "brain": schema, prompt, safety check, read-only run, self-correction, summary |
| `test_cases.py` | 20 test questions with verified answer SQL |
| `evaluate.py` | Runs the evaluation and saves a CSV of results |
| `test_safety.py` | Tests both safety layers without calling the AI |
| `test_set.sql` | My original hand-written answers to the 20 questions |
| `check_db.py` | Checks the database tables and row counts |

## Built with

Python · Claude API (Haiku 5.5) · SQLite · pandas · Streamlit · Altair

AI helped me write the Python code. The test set, the answer key, the safety design and the evaluation judgements are mine, drawing on my SQL and BI experience.
