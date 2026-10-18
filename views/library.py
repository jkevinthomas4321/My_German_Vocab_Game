import io

import pandas as pd
import streamlit as st

from ui import components as C, context
from wortschatz import config, wordlist

context.init()
st.title("Word lists")
C.note("Learn from any CSV or Excel word list. Only two columns are required: english and german.")

SAMPLE = pd.DataFrame({
    "word_class": ["noun", "noun", "verb", "adjective"],
    "english": ["apple", "house", "to read", "big"],
    "article": ["der", "das", "", ""],
    "german": ["Apfel", "Haus", "lesen", "groß"],
    "plural": ["Äpfel", "Häuser", "", ""],
    "past_tense": ["", "", "las", ""],
    "perfect_tense": ["", "", "hat gelesen", ""],
})


def save_and_select(df: pd.DataFrame, name: str) -> None:
    path = wordlist.save_upload(df, name)
    st.session_state["wordlist"] = path.stem
    st.session_state["library_saved"] = f"Saved “{path.stem}” ({len(df)} words) and selected it as the active list."


def remove(name: str) -> None:
    wordlist.delete_upload(name)
    if st.session_state.get("wordlist") == name:
        st.session_state["wordlist"] = config.DEFAULT_WORDLIST


if message := st.session_state.pop("library_saved", None):
    st.success(message)

add, manage = st.tabs(["Add a list", "My lists"])

with add:
    upload = st.file_uploader("CSV or Excel file", type=["csv", "xlsx"])
    with st.expander("Which columns does the file need?"):
        st.markdown(
            "| Column | Required | Notes |\n|---|---|---|\n"
            "| `english`, `german` | yes | Header spellings like *Englisch*, *Deutsch* also work. |\n"
            "| `word_class` | no | noun, verb, adjective... (default *other*) |\n"
            "| `article` | no | der / die / das. `der Tisch` in the German cell is split automatically. |\n"
            "| `plural`, `past_tense`, `perfect_tense` | no | Enables plural and verb-form questions. |\n"
            "| `zipf` | no | Word frequency; enables the frequency analysis. |\n\n"
            "Semicolon-separated CSV from German Excel is detected automatically.")
        left, right = st.columns(2)
        left.download_button("⬇️ Template (CSV)", wordlist.to_csv_bytes(SAMPLE), "wortschatz_template.csv", "text/csv")
        right.download_button("⬇️ Template (Excel)", wordlist.to_excel_bytes(SAMPLE), "wortschatz_template.xlsx",
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if upload is not None:
        try:
            data, sheet = upload.getvalue(), 0
            if upload.name.lower().endswith(".xlsx"):
                sheets = wordlist.list_sheets(io.BytesIO(data))
                sheet = st.selectbox("Sheet", sheets) if len(sheets) > 1 else sheets[0]
            df, report = wordlist.load_wordlist(io.BytesIO(data), filename=upload.name, sheet_name=sheet)
        except wordlist.WordListError as error:
            st.error(str(error))
        else:
            if df.empty:
                st.warning("The file has no usable rows.")
            else:
                C.tiles([("Rows read", str(report.rows_read), ""), ("Words kept", str(report.rows_kept), ""),
                         ("Removed", str(report.rows_dropped), "empty, incomplete or duplicate")])
                for note in report.messages:
                    st.write(f"- {note}")
                C.show_table(df[config.WORD_COLUMNS].head(20))
                name = st.text_input("Name for this list", value=wordlist.safe_name(upload.name))
                st.button("💾 Save and use this list", type="primary", on_click=save_and_select, args=(df, name))

with manage:
    rows = []
    for name, path in context.catalog().items():
        df, _ = context.load_list(path)
        rows.append({"List": name, "Words": len(df), "Source": "bundled" if wordlist.is_bundled(path) else "uploaded"})
    C.show_table(pd.DataFrame(rows))
    uploaded = [r["List"] for r in rows if r["Source"] == "uploaded"]
    if uploaded:
        chosen = st.selectbox("Remove an uploaded list", uploaded)
        st.button("🗑️ Remove", on_click=remove, args=(chosen,))
    else:
        C.note("Lists you upload appear here.")
