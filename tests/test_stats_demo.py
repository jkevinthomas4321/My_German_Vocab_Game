from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from tests.conftest import NOW
from wortschatz import config, demo, stats
from wortschatz.progress import Progress
from wortschatz.storage import ATTEMPT_COLUMNS, Store, empty_attempts


def attempts(rows):
    """rows: dicts with word, phase, correct and days_ago; optional session, direction, ms, cls."""
    out = []
    for r in rows:
        out.append({"ts": NOW - timedelta(days=r["days_ago"]), "session_id": r.get("session", f'{r["phase"]}{int(r["days_ago"])}'),
                    "phase": r["phase"], "word_id": r["word"], "word_class": r.get("cls", "noun"), "english": r["word"],
                    "german": r["word"].capitalize(), "direction": r.get("direction", "de_en"), "correct": r["correct"],
                    "response_ms": r.get("ms", 3000), "given": "", "expected": ""})
    return pd.DataFrame(out, columns=ATTEMPT_COLUMNS).astype({"correct": "int64", "response_ms": "int64"})


def two_question_test(word, phase, ok_de_en, ok_en_de, days_ago, **kw):
    return [dict(word=word, phase=phase, correct=int(ok_de_en), days_ago=days_ago, direction="de_en", **kw),
            dict(word=word, phase=phase, correct=int(ok_en_de), days_ago=days_ago, direction="en_de", **kw)]


# ----------------------------------------------------------------------------- statistics helpers
def test_wilson_matches_textbook_values():
    lo, hi = stats.wilson([5, 0, 10], [10, 10, 10])
    assert lo == pytest.approx([0.2366, 0.0, 0.7225], abs=1e-3) and hi == pytest.approx([0.7634, 0.2775, 1.0], abs=1e-3)
    assert np.isnan(stats.wilson(0, 0)[0])


def test_practice_streaks():
    days = [date(2026, 10, d) for d in (1, 2, 3, 10, 11)]
    assert stats.practice_streaks(days, date(2026, 10, 11)) == (2, 3)
    assert stats.practice_streaks(days, date(2026, 10, 12)) == (2, 3)          # yesterday keeps it alive
    assert stats.practice_streaks(days, date(2026, 10, 14)) == (0, 3)
    assert stats.practice_streaks([], date(2026, 10, 1)) == (0, 0)


# ----------------------------------------------------------------------------- outcomes
def test_a_word_passes_only_if_every_question_was_right():
    rows = two_question_test("a", "learn", True, True, 5) + two_question_test("b", "learn", True, False, 5) + \
        [dict(word="c", phase="learn", correct=1, days_ago=5)]
    out = stats.word_outcomes(attempts(rows)).set_index("word_id")["passed"]
    assert out.to_dict() == {"a": 1, "b": 0, "c": 1}


def test_outcomes_are_per_test_and_ignore_removals():
    rows = two_question_test("a", "learn", True, False, 6) + two_question_test("a", "retest", True, True, 4) + \
        [dict(word="a", phase="removed", correct=0, days_ago=1)]
    out = stats.word_outcomes(attempts(rows))
    assert out["phase"].tolist() == ["learn", "retest"] and out["passed"].tolist() == [0, 1]


def test_kpis():
    rows = two_question_test("a", "learn", True, True, 2) + two_question_test("b", "learn", True, False, 2) + two_question_test("a", "diary", True, True, 0)
    p = Progress()
    p.apply({"word_id": "a", "word_class": "noun", "english": "a", "german": "A", "article": "", "plural": "", "past_tense": "", "perfect_tense": "", "zipf": 5.0}, True, NOW)
    k = stats.kpis(p, attempts(rows), NOW.date())
    assert (k["diary"], k["tests"], k["answers"], k["active_days"], k["today_words"]) == (1, 3, 6, 2, 1)
    assert k["first_try_rate"] == 0.5 and k["streak"] == 1 and k["minutes"] == pytest.approx(6 * 3 / 60)


def test_daily_activity_and_diary_growth():
    rows = (two_question_test("a", "learn", True, True, 3) + two_question_test("b", "learn", True, True, 3) + two_question_test("c", "learn", True, False, 3) +
            two_question_test("a", "diary", True, False, 1) + [dict(word="b", phase="removed", correct=0, days_ago=0)])
    att = attempts(rows)
    daily = stats.daily_activity(stats.word_outcomes(att)).set_index("day")
    assert daily.iloc[0].tolist() == [2, 1] and daily.iloc[1].tolist() == [0, 1]
    growth = stats.diary_growth(att).set_index("day")["diary"]
    # +2 on day -3 (a, b), +0 for failed c, -1 on day -1 (a fails revision), -1 on day 0 (b removed)
    assert growth.tolist() == [2, 2, 1, 0] and len(growth) == 4


def test_pass_rates_with_intervals():
    rows = []
    for i in range(10):
        rows += two_question_test(f"n{i}", "learn", True, i < 7, 3 + i * 0.1, cls="noun")
    rows += two_question_test("v", "learn", True, True, 3, cls="verb")
    out = stats.word_outcomes(attempts(rows))
    by_class = stats.pass_rate_by_class(out).set_index("word_class")
    assert by_class.loc["noun", ["n", "wins"]].tolist() == [10, 7] and by_class.loc["noun", "lo"] < 0.7 < by_class.loc["noun", "hi"]
    by_phase = stats.pass_rate_by_phase(out)
    assert by_phase["label"].tolist() == ["First test"] and by_phase["rate"].iloc[0] == pytest.approx(8 / 11)


def test_direction_accuracy_shows_the_harder_direction():
    rows = []
    for i in range(20):
        rows += two_question_test(f"w{i}", "learn", True, i % 2 == 0, 2, ms=2000)
    table = stats.direction_accuracy(attempts(rows)).set_index("direction")
    assert table.loc["de_en", "rate"] == 1.0 and table.loc["en_de", "rate"] == 0.5
    assert table.loc["en_de", "label"] == "English → German"


def test_second_chance_journey():
    rows = (two_question_test("quick", "learn", False, False, 9) + two_question_test("quick", "retest", True, True, 8) +
            two_question_test("slow", "learn", False, False, 9) + two_question_test("slow", "retest", False, False, 8) + two_question_test("slow", "retest", True, True, 7) +
            two_question_test("stuck", "learn", False, False, 9) + two_question_test("fine", "learn", True, True, 9))
    out = stats.word_outcomes(attempts(rows))
    journey = stats.second_chance_journey(out, Progress()).set_index("retests")["words"]
    assert journey.to_dict() == {"Not yet": 1, "1 re-test": 1, "2 re-tests": 1, "3+ re-tests": 0}


def test_revision_by_gap_and_forgetting():
    rows = []
    for i in range(12):                               # revised after 1 day: always right; after 10 days: mostly wrong
        rows += two_question_test(f"s{i}", "learn", True, True, 12)
        rows += two_question_test(f"s{i}", "diary", True, True, 11)
        rows += two_question_test(f"s{i}", "diary", i < 3, i < 3, 1)
    gaps = stats.revision_by_gap(stats.word_outcomes(attempts(rows))).set_index("gap")
    assert gaps.loc["1 day", "rate"] == 1.0 and gaps.loc["8–14 days", "rate"] == pytest.approx(3 / 12)


def test_hardest_words():
    rows = (two_question_test("tricky", "learn", False, False, 5) + two_question_test("tricky", "retest", False, False, 4) +
            two_question_test("tricky", "retest", True, True, 3) + two_question_test("easy", "learn", True, True, 5) +
            two_question_test("meh", "learn", False, False, 5))
    hardest = stats.hardest_words(stats.word_outcomes(attempts(rows)))
    assert hardest["german"].tolist() == ["Tricky", "Meh"] and hardest["fails"].tolist() == [2, 1] and "Easy" not in hardest["german"].tolist()


def test_findings_are_specific_and_stay_quiet_on_small_samples():
    assert stats.findings(Progress(), empty_attempts()) == []
    tiny = attempts(two_question_test("a", "learn", True, True, 1))
    assert stats.findings(Progress(), tiny, NOW.date()) == []
    rows = []
    for i in range(30):
        rows += two_question_test(f"n{i}", "learn", True, i % 3 != 0, 3 + i * 0.01, cls="noun", ms=2000)
        rows += two_question_test(f"v{i}", "learn", i % 3 == 0, i % 6 == 0, 3 + i * 0.01, cls="verb", ms=5000)
    found = stats.findings(Progress(), attempts(rows), NOW.date())
    titles = " ".join(f["title"] for f in found)
    assert "Verbs are hardest" in titles and "Writing German is harder" in titles
    assert all(f["tone"] in ("good", "watch", "info") and f["text"] for f in found)


def test_everything_survives_an_empty_log():
    empty = empty_attempts()
    out = stats.word_outcomes(empty)
    assert out.empty and stats.kpis(Progress(), empty)["tests"] == 0
    for frame in (stats.daily_activity(out), stats.diary_growth(empty), stats.calendar_counts(out), stats.pass_rate_by_phase(out),
                  stats.pass_rate_by_class(out), stats.direction_accuracy(empty), stats.second_chance_journey(out, Progress()),
                  stats.revision_by_gap(out), stats.hardest_words(out), stats.weekday_profile(out)):
        assert frame.empty


# ----------------------------------------------------------------------------- the demo learner
@pytest.fixture(scope="module")
def demo_store(core_words_module, tmp_path_factory):
    """The demo data, captured once (files are written to a temporary folder that only this fixture uses)."""
    from types import SimpleNamespace
    previous = config.USER_DIR
    config.USER_DIR = tmp_path_factory.mktemp("demo_user")
    try:
        store = demo.generate(core_words_module, days=30, seed=2026, now=NOW)
        return SimpleNamespace(progress=store.progress, att=store.attempts())
    finally:
        config.USER_DIR = previous


@pytest.fixture(scope="module")
def core_words_module():
    from wortschatz import wordlist
    return wordlist.load_wordlist(config.WORDLIST_DIR / "german_core.csv")[0]


def test_demo_is_reproducible(core_words_module, tmp_path, monkeypatch):
    runs = []
    for folder in ("a", "b"):
        monkeypatch.setattr(config, "USER_DIR", tmp_path / folder)
        store = demo.generate(core_words_module, days=12, seed=5, now=NOW)
        runs.append((store.attempts().drop(columns="session_id"), store.progress.frame()))
    pd.testing.assert_frame_equal(runs[0][0], runs[1][0])
    pd.testing.assert_frame_equal(runs[0][1], runs[1][1])


def test_demo_follows_the_rules_of_the_game(demo_store):
    p = demo_store.progress
    assert p.count(config.STATUS_DIARY) > 100 and p.count(config.STATUS_SECOND) >= 1
    assert p.ids(config.STATUS_DIARY).isdisjoint(p.ids(config.STATUS_SECOND))
    frame = p.frame()
    assert (frame["tests"] == frame["passes"] + frame["fails"]).all()
    assert frame.loc[frame["status"] == config.STATUS_DIARY, "diary_since"].notna().all()
    att = demo_store.att
    assert set(att["phase"]) == {"learn", "retest", "diary"} and att["ts"].max() < pd.Timestamp(NOW)


def test_demo_progress_equals_a_replay_of_the_log(demo_store):
    """The saved state must be exactly what the attempts log implies under the game's rules."""
    outcomes = stats.word_outcomes(demo_store.att).sort_values("ts", kind="stable")
    replay = Progress()
    words = {r["word_id"]: r for r in demo_store.progress.frame().to_dict("records")}
    for row in outcomes.itertuples():
        replay.apply(words[row.word_id], bool(row.passed), row.ts.to_pydatetime())
    assert {i: r["status"] for i, r in replay.records.items()} == {i: r["status"] for i, r in demo_store.progress.records.items()}


def test_demo_shows_the_effects_it_models(demo_store):
    out = stats.word_outcomes(demo_store.att)
    phases = stats.pass_rate_by_phase(out).set_index("phase")["rate"]
    assert 0.55 < phases["learn"] < 0.95 and phases["retest"] > phases["diary"] - 0.05
    gaps = stats.revision_by_gap(out).set_index("gap")
    near, far = gaps.reindex(["1 day", "2–3 days"]).dropna(), gaps.reindex(["8–14 days", "15+ days"]).dropna()
    assert near["wins"].sum() / near["n"].sum() > far["wins"].sum() / far["n"].sum()      # forgetting grows with time
    assert stats.direction_accuracy(demo_store.att).set_index("direction")["rate"].pipe(lambda s: s["de_en"] > s["en_de"])
    assert stats.kpis(demo_store.progress, demo_store.att, NOW.date())["streak"] >= 3
    assert len(stats.findings(demo_store.progress, demo_store.att, NOW.date())) >= 4


def test_demo_replaces_old_demo_data_but_never_touches_my_diary(core_words_module):
    mine = Store(config.PROFILE_ME)
    mine.progress.apply({"word_id": "x", "word_class": "noun", "english": "x", "german": "X", "article": "", "plural": "",
                         "past_tense": "", "perfect_tense": "", "zipf": 5.0}, True, NOW)
    mine.save_progress()
    demo.generate(core_words_module, days=5, seed=1, now=NOW)
    demo.generate(core_words_module, days=5, seed=1, now=NOW)
    assert Store(config.PROFILE_ME).progress.count(config.STATUS_DIARY) == 1
