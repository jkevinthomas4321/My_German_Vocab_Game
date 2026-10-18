import streamlit as st

from ui import charts, components as C, context
from wortschatz import analytics as A
from wortschatz import config, events, insights
from wortschatz.questions import QTYPE_LABELS
from wortschatz.german import SUFFIX_HINT

context.init()
snap = context.snapshot()
d, states = snap.data, snap.states

st.title("Progress")
if snap.is_demo:
    st.info("Synthetic demo data: a simulated learner practised for a month so you can explore every chart. "
            "Switch to **My progress** in the sidebar to see your own.", icon="🧪")
if d.empty:
    st.info("No answers yet. Play a session and this page fills up, or open the demo profile from the sidebar.")
    st.stop()


def section(title: str, how_to_read: str) -> None:
    st.markdown(f"##### {title}")
    C.note(how_to_read)


overview, memory, articles, words_tab, habits = st.tabs(["Overview", "Memory", "Articles", "Words", "Habits"])
k = A.kpis(d, states, snap.now.date())

# ----------------------------------------------------------------------------- overview
with overview:
    C.tiles([
        ("Answers", f"{k['answers']:,}", f"{k['sessions']} sessions"),
        ("Accuracy", f"{100 * k['accuracy']:.0f}%", "all time"),
        ("Active days", str(k["active_days"]), f"streak {k['streak']} d · best {k['best_streak']} d"),
        ("Words mastered", str(k["words_mastered"]), f"of {k['words_seen']} met"),
        ("Answering time", f"{k['minutes']:.0f} min", f"median {k['median_rt']:.1f} s when correct"),
    ])
    st.write("")
    st.markdown("#### Findings")
    for item in insights.generate(d, states, snap.catalog_words, snap.now):
        C.insight_card(item)

    left, right = st.columns(2)
    with left:
        section("Session scores", "Each dot is one session; the line is the average of the last five.")
        C.show_chart(charts.session_trend(A.session_table(d)))
    with right:
        section("Daily activity", "Answers per day, split into correct and wrong.")
        C.show_chart(charts.activity_bars(A.daily_activity(d)))
    section("Rolling accuracy", "Accuracy over the last 50 answers, a smoother view of whether you are improving. "
                                "It dips whenever new words are introduced.")
    window = 50 if len(d) >= 80 else max(10, len(d) // 3)
    C.show_chart(charts.rolling_line(A.rolling_accuracy(d, window), window))
    st.download_button("⬇️ Export the event log (CSV)", events.load_events(snap.profile).to_csv(index=False).encode("utf-8"),
                       f"wortschatz_events_{snap.profile}.csv", "text/csv")

# ----------------------------------------------------------------------------- memory
with memory:
    left, right = st.columns(2)
    with left:
        section("Learning curve", "Accuracy the 1st, 2nd, 3rd... time a word is asked. The shaded band is the 95% "
                                  "confidence interval. The jump after the first exposure is the learning effect.")
        C.show_chart(charts.learning_curve_chart(A.learning_curve(d)))
    with right:
        fc = A.forgetting_curve(d)
        section("Forgetting curve", "Recall of words answered correctly last time, by time since that answer. "
                                    "A steady slope means reviews come too late; a flat line means the schedule fits your memory.")
        if fc.empty:
            C.note("Not enough repeated words yet.")
        else:
            C.show_chart(charts.forgetting_chart(fc))

    left, right = st.columns(2)
    with left:
        section("Where your words stand", "Learning = boxes 1-2, Reviewing = boxes 3-4, Mastered = box 5 "
                                          "(answered correctly five times in a row with growing gaps).")
        C.show_chart(charts.funnel_bars(A.mastery_funnel(states, list(snap.catalog_words["word_id"]))))
    with right:
        section("Review forecast", "Reviews falling due over the next week. Overdue words count as today.")
        C.show_chart(charts.forecast_bars(A.due_forecast(states, snap.now, 7)))
    section("Vocabulary growth", "Cumulative words met and words mastered.")
    growth = A.vocabulary_growth(states)
    if not growth.empty:
        C.show_chart(charts.growth_lines(growth))

# ----------------------------------------------------------------------------- articles
with articles:
    conf = A.article_confusion(d)
    if conf["n"].sum() == 0:
        st.info("No article answers yet. Try the Article trainer mode.")
    else:
        left, right = st.columns(2)
        with left:
            section("Which article do you mix up?", "Each row is the correct article; the cells show what you answered. "
                                                      "A bright diagonal is good; bright off-diagonal cells are your confusions.")
            C.show_chart(charts.confusion_heatmap(conf))
        with right:
            by_article = A.rate_table(A.article_events(d), "article_expected", outcome="article_ok")
            section("Accuracy per article", "How often you get der, die and das right (bars) with 95% intervals.")
            C.show_chart(charts.rate_bars(by_article, "article_expected", sort=["der", "die", "das"]))
        section("Accuracy by noun ending", "The classic rules of thumb: some endings give the article away. "
                                           "Short whiskers mean plenty of data; long ones mean treat the number with care.")
        by_suffix = A.article_by_suffix(d)
        by_suffix = by_suffix.assign(hint=by_suffix["suffix"].map(SUFFIX_HINT))
        C.show_chart(charts.rate_bars(by_suffix, "suffix", sort="x"))
        C.show_table(by_suffix.assign(acc=(100 * by_suffix["acc"]).round(0))[["suffix", "hint", "n", "acc"]].rename(
            columns={"suffix": "Ending", "hint": "Rule of thumb", "n": "Answers", "acc": "Accuracy %"}))

# ----------------------------------------------------------------------------- words
with words_tab:
    wt = A.word_table(d, states, snap.catalog_words)
    left, right = st.columns(2)
    with left:
        section("By word class", "Whiskers show the 95% interval; the label is the number of answers.")
        C.show_chart(charts.rate_bars(A.accuracy_by(d, "word_class"), "word_class"))
    with right:
        section("By question type", "Recognition (multiple choice) is easier than recall (typing).")
        qt = A.accuracy_by(d, "qtype")
        qt["qtype"] = qt["qtype"].map(lambda x: QTYPE_LABELS.get(x, x))
        C.show_chart(charts.rate_bars(qt, "qtype"))
    section("By word frequency", "Does a common word stick faster than a rare one? Bands are based on the measured Zipf frequency.")
    freq = A.accuracy_by(d[d["freq_band"] != "Unknown"], "freq_band", order=config.FREQ_BAND_ORDER[:-1])
    if len(freq):
        C.show_chart(charts.rate_bars(freq, "freq_band", sort=list(freq["freq_band"])))
    fe = A.frequency_effect(wt)
    if fe["n"] >= 10 and fe["rho"] == fe["rho"]:
        section("Frequency vs. accuracy per word", f"Each dot is a word asked at least 3 times (dot size = answers). "
                                                   f"Spearman ρ = {fe['rho']:.2f} over {fe['n']} words; the line is a linear fit.")
        C.show_chart(charts.scatter_frequency(wt[wt["attempts"] >= 3]))

    section("Hardest words", "Ranked by a smoothed error rate: with few answers it is pulled toward your overall "
                             "error rate, so one unlucky miss does not top the list.")
    hardest = A.hardest_words(wt, min_attempts=3, top=15)
    if hardest.empty:
        C.note("No word has been asked three times yet.")
    else:
        view = hardest.assign(accuracy=(100 * hardest["accuracy"]).round(0), difficulty=(100 * hardest["difficulty"]).round(0))
        st.dataframe(view[["english", "german", "word_class", "attempts", "accuracy", "difficulty"]], hide_index=True,
                     **C.stretch(st.dataframe), column_config={
                         "english": "English", "german": "German", "word_class": "Class", "attempts": "Answers",
                         "accuracy": st.column_config.NumberColumn("Accuracy %", format="%d"),
                         "difficulty": st.column_config.ProgressColumn("Difficulty", min_value=0, max_value=100, format="%d")})

# ----------------------------------------------------------------------------- habits
with habits:
    left, right = st.columns(2)
    with left:
        section("Time of day", "Bar height = answers; colour = accuracy.")
        C.show_chart(charts.hour_chart(A.hour_profile(d)))
    with right:
        section("Response time", "Dashed lines mark the medians. Hesitation predicts a miss.")
        C.show_chart(charts.rt_histogram(A.response_times(d)))
    left, right = st.columns(2)
    with left:
        section("Fluency over time", "Median time of correct answers per day. Falling means answers are becoming automatic.")
        trend = A.rt_trend(d)
        if len(trend) >= 2:
            C.show_chart(charts.rt_trend_chart(trend))
    with right:
        section("Speed by question type", "Median seconds for correct answers.")
        by_type = A.rt_by_qtype(d)
        C.show_table(by_type.assign(qtype=by_type["qtype"].map(QTYPE_LABELS), median_s=by_type["median_s"].round(1)).rename(
            columns={"qtype": "Question type", "median_s": "Median s", "n": "Answers"}))
    section("Weekday", "Accuracy and volume by day of the week.")
    wk = A.weekday_profile(d)
    C.show_chart(charts.rate_bars(wk, "name", sort=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))
