import pandas as pd
import streamlit as st

from ui import charts, components as C, context
from wortschatz import analytics as A
from wortschatz import config, wordlist
from wortschatz.german import SUFFIX_HINT

context.init()
snap = context.snapshot()
words = snap.words

st.title("Data lab")
C.note("Exploratory analysis of the active word list, the dataset the whole app is built on. "
       "The same checks run on every list you upload.")
if words.empty:
    st.warning("No word list loaded.")
    st.stop()

profile_tab, quality_tab, frequency_tab, browse_tab = st.tabs(["Dataset profile", "Quality checks", "Frequency", "Browse"])

# ----------------------------------------------------------------------------- profile
with profile_tab:
    nouns = words[words["word_class"] == "noun"]
    C.tiles([
        ("Words", f"{len(words):,}", context.list_label(snap.list_name or "")),
        ("Nouns", str(len(nouns)), f"{100 * len(nouns) / len(words):.0f}% of the list"),
        ("Verbs", str((words["word_class"] == "verb").sum()), "with Präteritum + Perfekt"),
        ("Median frequency", f"{words['zipf'].median():.2f}" if words["zipf"].notna().any() else "–", "Zipf scale"),
    ])
    st.write("")
    left, right = st.columns(2)
    with left:
        st.markdown("##### Words by class")
        C.show_chart(charts.class_mix(words))
    with right:
        st.markdown("##### Noun genders")
        genders = nouns["article"].value_counts().reindex(list(config.ARTICLES), fill_value=0)
        C.tiles([(a, str(int(genders[a])), f"{100 * genders[a] / max(len(nouns), 1):.0f}% of nouns") for a in config.ARTICLES])
        C.note("German has no gender rule that always works, but endings are strong predictors. See below.")

    st.markdown("##### Can the ending predict the article?")
    table = A.suffix_gender_table(words)
    if not table.empty:
        covered = table[table["suffix"] != "other endings"]
        total_nouns = int(table["nouns"].sum())
        rule_hits = int((table["rule_accuracy"] * table["nouns"]).sum().round())
        always_most_common = int(nouns["article"].value_counts().iloc[0])
        st.markdown(
            f"A rule that predicts each noun's article from its ending (the most common article for that ending) is right for "
            f"**{rule_hits} of {total_nouns} nouns ({100 * rule_hits / total_nouns:.0f}%)**, versus "
            f"{100 * always_most_common / total_nouns:.0f}% if you always guessed the most common article. "
            f"The reliable endings (-ung, -heit/-keit, -schaft, -ion, -tät) cover {int(covered[covered['rule_accuracy'] == 1]['nouns'].sum())} "
            f"nouns with no exceptions in this list.")
        C.show_chart(charts.suffix_gender_chart(table))
        C.show_table(table.assign(rule_accuracy=(100 * table["rule_accuracy"]).round(0), hint=table["suffix"].map(SUFFIX_HINT))[
            ["suffix", "nouns", "der", "die", "das", "rule_accuracy", "hint"]].rename(columns={
                "suffix": "Ending", "nouns": "Nouns", "rule_accuracy": "Rule accuracy %", "hint": "Rule of thumb"}))

    st.markdown("##### How complete is each field?")
    filled = words[["article", "plural", "past_tense", "perfect_tense"]].ne("")
    completeness = (filled.groupby(words["word_class"]).mean() * 100).round(0).astype(int).reset_index()
    C.show_table(completeness.rename(columns={"word_class": "Class", "article": "Article %", "plural": "Plural %",
                                               "past_tense": "Past %", "perfect_tense": "Perfect %"}))
    C.note("Fields that do not apply to a class (articles on verbs...) are correctly empty, "
           "so low numbers only matter where the field is expected.")

# ----------------------------------------------------------------------------- quality
with quality_tab:
    st.markdown("##### Automated checks")
    checks = wordlist.quality_checks(words)
    icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
    C.show_table(pd.DataFrame({
        "": [icon[c.status] for c in checks], "Check": [c.name for c in checks], "Result": [c.detail for c in checks]}))
    failed = sum(c.status == "fail" for c in checks)
    warned = sum(c.status == "warn" for c in checks)
    if failed:
        st.error(f"{failed} check(s) failed.")
    elif warned:
        st.warning(f"All hard checks pass; {warned} warning(s). A noun without a plural is usually uncountable "
                   f"(die Butter, das Geld), so the warning is expected.")
    else:
        st.success("All checks pass.")

    st.markdown("##### What the loader changed")
    report = context.load_list(context.catalog()[snap.list_name])[1]
    st.write(f"Rows read **{report.rows_read}** → kept **{report.rows_kept}**")
    for message in report.messages or ["Nothing: the file was already clean."]:
        st.write(f"- {message}")

# ----------------------------------------------------------------------------- frequency
with frequency_tab:
    if words["zipf"].isna().all():
        st.info("This list has no frequency column. Add a `zipf` column (see the About page) to unlock this analysis.")
    else:
        st.markdown("##### Distribution")
        C.note("Zipf frequency is a log scale: 7 is a word like “und”, 5 appears about once in 10,000 words, 3 is rare. "
               "The list is ordered most common first, so new words are introduced in that order.")
        C.show_chart(charts.zipf_histogram(words))
        left, right = st.columns(2)
        shown = words.dropna(subset=["zipf"]).sort_values("zipf", ascending=False)
        cols = ["german", "english", "word_class", "zipf"]
        names = {"german": "German", "english": "English", "word_class": "Class", "zipf": "Zipf"}
        with left:
            st.markdown("##### Most common")
            C.show_table(shown.head(10)[cols].rename(columns=names))
        with right:
            st.markdown("##### Least common")
            C.show_table(shown.tail(10).iloc[::-1][cols].rename(columns=names))
        st.markdown("##### Words per frequency band")
        bands = words["freq_band"].value_counts().reindex(config.FREQ_BAND_ORDER, fill_value=0).rename_axis("Band").reset_index(name="Words")
        C.show_table(bands[bands["Words"] > 0])

# ----------------------------------------------------------------------------- browse
with browse_tab:
    left, right = st.columns([2, 1])
    query = left.text_input("Search German or English", "")
    classes = right.multiselect("Class", sorted(words["word_class"].unique()))
    view = words
    if query:
        needle = query.casefold()
        view = view[view["german"].str.casefold().str.contains(needle, regex=False) |
                    view["english"].str.casefold().str.contains(needle, regex=False)]
    if classes:
        view = view[view["word_class"].isin(classes)]
    C.show_table(view[config.WORD_COLUMNS])
    st.caption(f"{len(view)} of {len(words)} words")
    st.download_button("⬇️ Download this list (CSV)", wordlist.to_csv_bytes(view), f"{snap.list_name}.csv", "text/csv")
