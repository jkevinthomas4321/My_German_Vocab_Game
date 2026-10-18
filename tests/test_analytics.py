from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from tests.conftest import NOW
from wortschatz import analytics as A
from wortschatz import events, srs


def make_events(rows):
    """rows: dicts with at least word, days_ago (float) and correct. Everything else has a sensible default."""
    out = []
    for i, r in enumerate(rows):
        out.append({
            "ts": NOW - timedelta(days=r["days_ago"]), "session_id": r.get("session", f"s{int(r['days_ago'])}"),
            "word_id": r["word"], "word_class": r.get("cls", "noun"), "english": r["word"], "german": r.get("german", r["word"].capitalize()),
            "qtype": r.get("qtype", "choose_en"), "direction": "de→en", "correct": r["correct"], "response_ms": r.get("ms", 3000),
            "given": "", "expected": "", "article_expected": r.get("art_exp", ""), "article_given": r.get("art_giv", ""), "retry": r.get("retry", 0)})
    return pd.DataFrame(out, columns=events.EVENT_COLUMNS)


def prepared(rows, words=None):
    return A.prepare(make_events(rows), words)


# ----------------------------------------------------------------------------- statistics
def test_wilson_matches_textbook_values():
    lo, hi = A.wilson([5, 0, 10], [10, 10, 10])
    assert lo == pytest.approx([0.2366, 0.0, 0.7225], abs=1e-3)
    assert hi == pytest.approx([0.7634, 0.2775, 1.0], abs=1e-3)


def test_wilson_interval_narrows_with_more_data_and_handles_zero():
    narrow, wide = A.wilson(50, 100), A.wilson(5, 10)
    assert (narrow[1] - narrow[0]) < (wide[1] - wide[0])
    assert np.isnan(A.wilson(0, 0)[0])


def test_rate_table():
    d = prepared([dict(word="a", days_ago=3, correct=1), dict(word="b", days_ago=2, correct=0), dict(word="c", days_ago=1, correct=1, cls="verb")])
    t = A.rate_table(d, "word_class").set_index("word_class")
    assert t.loc["noun", ["n", "correct", "acc"]].tolist() == [2, 1, 0.5] and t.loc["verb", "acc"] == 1.0
    assert t.loc["noun", "lo"] < 0.5 < t.loc["noun", "hi"]


# ----------------------------------------------------------------------------- prepare
def test_prepare_derives_attempt_gap_and_previous_outcome():
    d = prepared([dict(word="a", days_ago=4, correct=1), dict(word="a", days_ago=2, correct=0), dict(word="a", days_ago=1, correct=1)])
    assert d["attempt_no"].tolist() == [1, 2, 3]
    assert d["prev_correct"].tolist()[1:] == [1, 0] and np.isnan(d["prev_correct"].iloc[0])
    assert d["gap_days"].tolist()[1:] == pytest.approx([2.0, 1.0]) and np.isnan(d["gap_days"].iloc[0])


def test_prepare_ignores_retries_and_computes_xp():
    d = prepared([dict(word="a", days_ago=2, correct=1, ms=2000), dict(word="b", days_ago=1, correct=1, ms=9000),
                  dict(word="c", days_ago=1, correct=0), dict(word="c", days_ago=1, correct=1, retry=1)])
    assert len(d) == 3 and d["xp"].tolist() == [15, 10, 0]


def test_prepare_joins_frequency_and_flags_unknown_words(mini_words):
    wid = mini_words.loc[mini_words["german"] == "Tisch", "word_id"].iloc[0]
    d = A.prepare(make_events([dict(word=wid, days_ago=1, correct=1), dict(word="orphan", days_ago=1, correct=1)]), mini_words)
    assert d["freq_band"].tolist() == ["Common", "Unknown"] and d["zipf"].iloc[0] == 4.8


def test_prepare_article_outcome_only_where_an_article_was_given():
    d = prepared([dict(word="a", days_ago=3, correct=0, art_exp="der", art_giv="die"), dict(word="b", days_ago=2, correct=1, art_exp="die", art_giv="die"),
                  dict(word="c", days_ago=1, correct=1)])
    assert d["article_ok"].iloc[:2].tolist() == [0.0, 1.0] and np.isnan(d["article_ok"].iloc[2])


# ----------------------------------------------------------------------------- headline numbers
def test_practice_streaks():
    days = [date(2026, 10, d) for d in (1, 2, 3, 10, 11)]
    assert A.practice_streaks(days, date(2026, 10, 11)) == (2, 3)
    assert A.practice_streaks(days, date(2026, 10, 12)) == (2, 3)         # yesterday keeps the streak alive
    assert A.practice_streaks(days, date(2026, 10, 13)) == (0, 3)
    assert A.practice_streaks([], date(2026, 10, 1)) == (0, 0)
    assert A.practice_streaks([date(2026, 10, 1)] * 4, date(2026, 10, 1)) == (1, 1)


def test_kpis():
    d = prepared([dict(word="a", days_ago=2, correct=1, ms=2000), dict(word="b", days_ago=1, correct=0, ms=4000),
                  dict(word="a", days_ago=1, correct=1, ms=3000)])
    k = A.kpis(d, srs.replay(make_events([dict(word="a", days_ago=2, correct=1)])), NOW.date())
    assert (k["answers"], k["correct"], k["sessions"], k["active_days"]) == (3, 2, 2, 2)
    assert k["accuracy"] == pytest.approx(2 / 3) and k["median_rt"] == 2.5 and k["streak"] == 2
    assert k["minutes"] == pytest.approx(9 / 60)


def test_daily_activity_and_sessions():
    d = prepared([dict(word="a", days_ago=2, correct=1), dict(word="b", days_ago=2, correct=0), dict(word="c", days_ago=1, correct=1)])
    daily = A.daily_activity(d)
    assert daily["answers"].tolist() == [2, 1] and daily["wrong"].tolist() == [1, 0]
    s = A.session_table(d)
    assert s["answers"].tolist() == [2, 1] and s["accuracy"].tolist() == [0.5, 1.0] and s["xp"].tolist() == [15, 15]


def test_calendar_grid_is_whole_weeks_ending_today():
    d = prepared([dict(word="a", days_ago=1, correct=1), dict(word="b", days_ago=1, correct=1)])
    grid = A.calendar_grid(d, weeks=3, today=NOW.date())
    assert grid["day"].iloc[0].dayofweek == 0 and grid["day"].iloc[-1] == pd.Timestamp(NOW.date())
    assert grid.loc[grid["day"] == pd.Timestamp(NOW.date() - timedelta(days=1)), "answers"].item() == 2
    assert (grid["week"].dt.dayofweek == 0).all() and grid["answers"].sum() == 2


def test_rolling_accuracy_needs_a_full_window():
    d = prepared([dict(word=f"w{i}", days_ago=10 - i, correct=int(i % 2 == 0)) for i in range(10)])
    r = A.rolling_accuracy(d, 4)
    assert len(r) == 7 and r["accuracy"].iloc[0] == 0.5


# ----------------------------------------------------------------------------- memory
def test_learning_curve_counts_the_kth_exposure():
    rows = [dict(word="a", days_ago=9, correct=0), dict(word="b", days_ago=9, correct=0), dict(word="a", days_ago=5, correct=1),
            dict(word="b", days_ago=5, correct=0), dict(word="a", days_ago=2, correct=1), dict(word="a", days_ago=1, correct=1)]
    lc = A.learning_curve(prepared(rows), max_attempt=3).set_index("label")
    assert lc.loc["1", ["n", "correct"]].tolist() == [2, 0] and lc.loc["2", "acc"] == 0.5 and lc.loc["3+", "n"] == 2


def test_forgetting_curve_conditions_on_a_previous_success():
    rows = [dict(word="a", days_ago=10, correct=1), dict(word="a", days_ago=9, correct=1),      # 1 day gap after success -> recalled
            dict(word="b", days_ago=10, correct=0), dict(word="b", days_ago=2, correct=1),      # previous wrong: excluded
            dict(word="c", days_ago=10, correct=1), dict(word="c", days_ago=0.5, correct=0)]    # 9.5 day gap after success -> forgotten
    fc = A.forgetting_curve(prepared(rows)).set_index("gap")
    assert fc.loc["1 day", ["n", "correct"]].tolist() == [1, 1] and fc.loc["8–14 days", ["n", "correct"]].tolist() == [1, 0]
    assert fc["n"].sum() == 2


# ----------------------------------------------------------------------------- articles
def test_article_confusion_is_complete_and_normalised():
    d = prepared([dict(word="a", days_ago=3, correct=1, art_exp="der", art_giv="der"), dict(word="b", days_ago=2, correct=0, art_exp="der", art_giv="die"),
                  dict(word="c", days_ago=1, correct=1, art_exp="der", art_giv="der")])
    conf = A.article_confusion(d)
    assert len(conf) == 9 and conf["n"].sum() == 3
    row = conf[(conf["expected"] == "der") & (conf["given"] == "die")].iloc[0]
    assert row["n"] == 1 and row["pct"] == pytest.approx(1 / 3)
    assert conf[conf["expected"] == "das"]["pct"].tolist() == [0, 0, 0]          # no data: zeros, not NaN


def test_article_accuracy_by_suffix_is_sorted_weakest_first():
    rows = [dict(word=f"u{i}", german="Zeitung", days_ago=5 - i, correct=1, art_exp="die", art_giv="die") for i in range(3)] + \
           [dict(word=f"e{i}", german="Zimmer", days_ago=5 - i, correct=0, art_exp="das", art_giv="der") for i in range(2)]
    t = A.article_by_suffix(prepared(rows))
    assert t["suffix"].tolist() == ["-er", "-ung"] and t["acc"].tolist() == [0.0, 1.0]


def test_suffix_gender_table(mini_words):
    # Tisch (der), Stadt (die), Kind (das), Tür (die): none has a rule ending, so one 'other' row
    t = A.suffix_gender_table(mini_words).set_index("suffix")
    assert t.loc["other endings", ["der", "die", "das", "nouns", "rule"]].tolist() == [1, 2, 1, 4, "die"]
    assert t.loc["other endings", "rule_accuracy"] == 0.5


# ----------------------------------------------------------------------------- words
def test_word_difficulty_is_shrunk_toward_the_overall_error_rate():
    rows = [dict(word="one_miss", days_ago=5, correct=0)] + [dict(word="five_misses", days_ago=5 - i * 0.1, correct=0) for i in range(5)] + \
           [dict(word="easy", days_ago=4 - i * 0.1, correct=1) for i in range(10)]
    wt = A.word_table(prepared(rows), srs.empty_states()).set_index("word_id")
    assert 0 < wt.loc["easy", "difficulty"] < wt.loc["one_miss", "difficulty"] < wt.loc["five_misses", "difficulty"] < 1
    assert wt.loc["one_miss", "accuracy"] == wt.loc["five_misses", "accuracy"] == 0       # raw rates tie; the smoothed score does not


def test_hardest_words_need_enough_answers():
    rows = [dict(word="few", days_ago=5, correct=0)] + [dict(word="many", days_ago=5 - i * 0.1, correct=0) for i in range(3)]
    hardest = A.hardest_words(A.word_table(prepared(rows), srs.empty_states()), min_attempts=3)
    assert hardest["word_id"].tolist() == ["many"]


def test_frequency_effect_detects_a_monotone_relationship():
    wt = pd.DataFrame({"zipf": np.linspace(3.5, 6.5, 20), "accuracy": np.linspace(0.3, 0.95, 20), "attempts": 5})
    assert A.frequency_effect(wt)["rho"] == pytest.approx(1.0)
    assert np.isnan(A.frequency_effect(wt.head(5))["rho"])


# ----------------------------------------------------------------------------- scheduling views
def test_due_forecast_counts_overdue_as_today():
    ev = make_events([dict(word="old", days_ago=10, correct=1), dict(word="now", days_ago=0.1, correct=1)])
    f = A.due_forecast(srs.replay(ev), NOW, days=3)
    assert f["reviews"].tolist() == [2, 0, 0] and f["day"].iloc[0] == pd.Timestamp(NOW.date())


def test_vocabulary_growth_is_cumulative():
    ev = make_events([dict(word="a", days_ago=5, correct=1), dict(word="b", days_ago=3, correct=1)])
    g = A.vocabulary_growth(srs.replay(ev))
    seen = g[g["metric"] == "Words seen"]["words"]
    assert seen.is_monotonic_increasing and seen.iloc[-1] == 2


def test_mastery_funnel(mini_words):
    funnel = A.mastery_funnel(srs.empty_states(), list(mini_words["word_id"]))
    assert funnel.set_index("status")["words"].to_dict() == {"Unseen": 10, "Learning": 0, "Reviewing": 0, "Mastered": 0}


# ----------------------------------------------------------------------------- no data
def test_every_function_survives_an_empty_log(mini_words):
    d = A.prepare(events.empty_events(), mini_words)
    s = srs.empty_states()
    assert d.empty and A.kpis(d, s)["answers"] == 0
    frames = [A.daily_activity(d), A.session_table(d), A.learning_curve(d), A.forgetting_curve(d), A.accuracy_by(d, "word_class"),
              A.hour_profile(d), A.weekday_profile(d), A.rt_trend(d), A.rt_by_qtype(d), A.article_by_suffix(d), A.word_table(d, s, mini_words),
              A.vocabulary_growth(s), A.rolling_accuracy(d, 5)]
    assert all(f.empty for f in frames)
    assert A.article_confusion(d)["n"].sum() == 0 and A.due_forecast(s, NOW)["reviews"].sum() == 0
    assert A.hardest_words(A.word_table(d, s, mini_words)).empty and np.isnan(A.frequency_effect(A.word_table(d, s))["rho"])
    assert len(A.calendar_grid(d, 4, NOW.date())) >= 22
