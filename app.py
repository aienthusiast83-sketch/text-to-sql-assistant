import re

import altair as alt
import streamlit as st
from text_to_sql import get_schema, answer, summarize, MODEL

st.set_page_config(page_title="Text-to-SQL Assistant", page_icon="🎵", layout="wide")
st.title("🎵 Text-to-SQL Assistant")
st.caption(f"Ask questions about the Chinook music store in plain English · Model: {MODEL}")

privacy_mode = st.sidebar.toggle(
    "🔒 Privacy mode",
    value=False,
    help="When on, result rows are never sent to the AI. Only the schema and your question are sent.",
)
st.sidebar.caption(
    "What the AI sees: the table and column names plus your question"
    + (". Result rows stay on this computer." if privacy_mode
       else ", and up to 30 result rows for the plain-English summary.")
)


@st.cache_data
def load_schema():
    return get_schema()


TIME_VALUE = re.compile(r"^(\d{4})(-\d{2})?(-\d{2})?$")  # 2013, 2013-01, 2013-01-31


def find_time_column(df):
    """Return the column that holds years/months/dates (e.g. 2013 or 2013-01), if any."""
    for c in df.columns:
        values = df[c].dropna().astype(str)
        if len(values) == 0:
            continue
        matches = values.str.extract(TIME_VALUE)[0]
        if matches.notna().all() and matches.astype(int).between(1900, 2100).all():
            return c
    return None


def show_chart(df):
    """Lines for trends over time (one line per category), bars for everything else."""
    if len(df) < 2:
        return
    time_col = find_time_column(df)
    num_cols = [c for c in df.select_dtypes("number").columns if c != time_col]
    txt_cols = [c for c in df.columns if c not in num_cols and c != time_col]
    if not num_cols:
        return
    value = num_cols[-1]

    if time_col:
        # Skip numbers that repeat on every row of a category (like an all-time total),
        # because they draw flat lines; prefer the number that changes over time.
        if txt_cols:
            varying = [c for c in num_cols
                       if df.groupby(txt_cols[0])[c].nunique().max() > 1]
            if varying:
                value = varying[0]
        enc = dict(
            x=alt.X(f"{time_col}:O", sort="ascending", title=time_col),
            y=alt.Y(f"{value}:Q"),
            tooltip=list(df.columns),
        )
        if txt_cols and df[txt_cols[0]].nunique() <= 10:
            enc["color"] = alt.Color(f"{txt_cols[0]}:N", sort=None)  # legend in SQL order
        chart = alt.Chart(df).mark_line(point=True).encode(**enc)
    elif txt_cols:
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(f"{txt_cols[0]}:N", sort=None),  # keep SQL's order
            y=alt.Y(f"{value}:Q"),
            tooltip=list(df.columns),
        )
    else:
        return

    st.subheader("Chart")
    st.altair_chart(chart)


schema = load_schema()

question = st.text_input("Your question", placeholder="e.g. Top 5 artists by revenue")

if st.button("Ask", type="primary") and question.strip():
    with st.spinner("Thinking..."):
        r = answer(question, schema)

    if r["status"] == "refused":
        st.warning(r["message"])
    else:
        st.subheader("Generated SQL")
        st.code(r["sql"], language="sql")

        if r["status"] == "ok":
            if r["attempts"] > 1:
                st.info(f"Fixed itself after {r['attempts']} attempts")
            df = r["df"]

            # Plain-English answer written from the result itself (skipped in privacy mode)
            if privacy_mode:
                st.info("🔒 Privacy mode: no result rows were sent to the AI, so there is "
                        "no summary. Only the schema and your question left this computer.")
            else:
                with st.spinner("Writing a summary..."):
                    summary, s_in, s_out = summarize(question, df)
                r["tokens_in"] += s_in
                r["tokens_out"] += s_out
                st.success(summary)

            st.subheader(f"Result ({len(df)} rows)")
            st.dataframe(df)

            show_chart(df)
        else:
            st.error(f"{r['status'].upper()}: {r['message']}")

    st.caption(f"Tokens: in={r['tokens_in']}, out={r['tokens_out']} · attempts: {r['attempts']}")