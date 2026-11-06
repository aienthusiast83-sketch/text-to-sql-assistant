"""Day 4: run every test question through the assistant and score it."""
import math
import re
import sqlite3
import sys
from datetime import datetime
from itertools import permutations

import pandas as pd

from test_cases import TEST_CASES
from text_to_sql import DB_PATH, MODEL, answer, get_schema

PRICE_IN, PRICE_OUT = 0.10, 0.50  # Haiku 5.5, $ per million tokens
NUMBER = re.compile(r"^-?\d+(\.\d+)?$")


def norm(v):
    """Make values comparable: round numbers to 2 decimals, tidy text, unify blanks."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    s = str(v).strip()
    if NUMBER.match(s):          # "2009" and 2009 count as the same
        return round(float(s), 2)
    return s


def column_values(series):
    """A column's values, normalised and sorted (so row order doesn't matter)."""
    return sorted((norm(v) for v in series), key=lambda x: (x is None, str(x)))


def candidate_columns(df):
    """Every AI column, plus text columns joined in pairs (FirstName + LastName)."""
    cols = [column_values(df[c]) for c in df.columns]
    text_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    for a, b in permutations(text_cols, 2):
        cols.append(column_values(df[a].astype(str) + " " + df[b].astype(str)))
    return cols


def results_match(expected, actual):
    """PASS if every expected column appears in the AI's result with the same values."""
    if actual is None:
        return False
    if expected.empty or actual.empty:
        return expected.empty and actual.empty
    if len(expected) != len(actual):
        return False
    candidates = candidate_columns(actual)
    return all(column_values(expected[c]) in candidates for c in expected.columns)


def run_expected(sql):
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    schema = get_schema()
    rows, passed, graded, tok_in, tok_out = [], 0, 0, 0, 0

    print(f"Evaluating {len(TEST_CASES)} questions with {MODEL} ...\n")
    for case in TEST_CASES:
        r = answer(case["question"], schema)
        tok_in += r["tokens_in"]
        tok_out += r["tokens_out"]

        if not case["grade"]:
            verdict = "REVIEW"
        else:
            graded += 1
            ok = r["status"] == "ok" and results_match(run_expected(case["expected_sql"]), r["df"])
            verdict = "PASS" if ok else "FAIL"
            passed += ok

        print(f"Q{case['id']:>2}  {verdict:6}  attempts={r['attempts']}  {case['question']}")
        if verdict != "PASS":
            print(f"       AI SQL: {' '.join(r['sql'].split())[:300]}")
            if r["status"] != "ok":
                print(f"       {r['status']}: {r['message']}")

        rows.append({"id": case["id"], "question": case["question"], "verdict": verdict,
                     "status": r["status"], "attempts": r["attempts"],
                     "tokens_in": r["tokens_in"], "tokens_out": r["tokens_out"],
                     "ai_sql": r["sql"]})

    cost = tok_in * PRICE_IN / 1e6 + tok_out * PRICE_OUT / 1e6
    print(f"\nAccuracy: {passed}/{graded} = {passed / graded:.0%}")
    print(f"Tokens: in={tok_in:,}  out={tok_out:,}  ·  cost ≈ ${cost:.4f}")

    out = f"eval_{label}_{datetime.now():%Y%m%d_%H%M}.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Saved details to {out}")


if __name__ == "__main__":
    main()