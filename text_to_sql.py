import re
import sqlite3

import anthropic
import pandas as pd
from dotenv import load_dotenv

DB_PATH = "Chinook_Sqlite.sqlite"
MODEL = "claude-haiku-5-5"
MAX_RETRIES = 2  # how many times Claude may fix a failing query

load_dotenv(override=True)
client = anthropic.Anthropic()


def get_schema():
    """Read CREATE TABLE statements so Claude knows the tables and columns."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ).fetchall()
    conn.close()
    return "\n\n".join(r[0] for r in rows)


def ask_claude(messages, schema):
    """Send the conversation to Claude and return its SQL (or CANNOT_MODIFY)."""
    system_prompt = (
        "You are an expert SQLite analyst. "
        "Write ONE SQLite SELECT query that answers the user's question, "
        "using only the tables and columns in this schema:\n\n"
        f"{schema}\n\n"
        "Rules:\n"
        "- Return only the SQL. No explanation, no markdown.\n"
        "- If a ranking or 'top per group' could have ties, use RANK() instead of ROW_NUMBER() so all tied rows are shown.\n"
        "- Apply every condition in the question. 'Latest year' or 'latest month' means the most recent one in the data (use MAX on the date column), not today's date.\n"
        "- If the user asks to change data (delete, update, insert, drop, etc.), "
        "do not write SQL. Reply with exactly: CANNOT_MODIFY"
    )
    msg = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=system_prompt,
        messages=messages,
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    text = re.sub(r"^```(?:sql)?\s*|\s*```$", "", text).strip()
    m = re.search(r"^\s*(WITH|SELECT)\b", text, re.IGNORECASE | re.MULTILINE)
    if m:
        text = text[m.start():].strip()

    return text, msg.usage          # ← always runs


BLOCKED = r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|VACUUM)\b"


def is_safe(sql):
    """Allow only a single SELECT (or WITH ... SELECT) query."""
    s = sql.strip().rstrip(";")
    if ";" in s:
        return False, "Only one statement allowed."
    if not re.match(r"^\s*(SELECT|WITH)\b", s, re.IGNORECASE):
        return False, "Only SELECT queries are allowed."
    if re.search(BLOCKED, s, re.IGNORECASE):
        return False, "Query contains a blocked keyword."
    return True, ""


def run_sql(sql):
    """Run the query in READ-ONLY mode and return a table."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


def answer(question, schema):
    """Full pipeline: generate SQL, check safety, run, self-correct on errors."""
    messages = [{"role": "user", "content": question}]
    result = {"status": "", "sql": "", "df": None, "message": "",
              "attempts": 0, "tokens_in": 0, "tokens_out": 0}

    for attempt in range(1, MAX_RETRIES + 2):
        sql, usage = ask_claude(messages, schema)
        result["attempts"] = attempt
        result["tokens_in"] += usage.input_tokens
        result["tokens_out"] += usage.output_tokens
        result["sql"] = sql

        if "CANNOT_MODIFY" in sql:
            result.update(status="refused",
                          message="I can only read data, not change or delete it.")
            return result

        ok, reason = is_safe(sql)
        if not ok:
            result.update(status="blocked", message=reason)
            return result

        try:
            result["df"] = run_sql(sql)
            result["status"] = "ok"
            return result
        except Exception as e:
            error = str(e)
            # Reflection: show Claude its own query and the error, ask for a fix
            messages += [
                {"role": "assistant", "content": sql},
                {"role": "user", "content":
                    f"That query failed with this SQLite error:\n{error}\n"
                    "Return a corrected query. Return only the SQL."},
            ]

    result.update(status="error", message=error)
    return result


def summarize(question, df):
    """Ask Claude for a short plain-English answer based only on the result table."""
    if df is None or df.empty:
        return "No rows matched this question (an empty result can still be the correct answer).", 0, 0
    preview = df.head(30).to_string(index=False)
    shown = "all rows" if len(df) <= 30 else f"first 30 of {len(df)} rows"
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=(
            "You explain query results to business users. In one or two short sentences, "
            "answer the user's question using only the numbers in the result. "
            "No SQL, no markdown, no guessing beyond the data."
        ),
        messages=[{"role": "user", "content":
                   f"Question: {question}\n\nResult ({shown}):\n{preview}"}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    return text, msg.usage.input_tokens, msg.usage.output_tokens


def main():
    schema = get_schema()
    print("Ask a question about the Chinook music store (type 'exit' to quit).")
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue

        r = answer(question, schema)

        if r["status"] == "refused":
            print(f"\n{r['message']}")
        else:
            print(f"\nGenerated SQL:\n{r['sql']}")
            if r["status"] == "ok":
                if r["attempts"] > 1:
                    print(f"(Fixed itself after {r['attempts']} attempts)")
                print("\nResult:")
                print(r["df"].head(20).to_string(index=False))
            else:
                print(f"\n{r['status'].upper()}: {r['message']}")

        print(f"\n(tokens: in={r['tokens_in']}, out={r['tokens_out']})")


if __name__ == "__main__":
    main()