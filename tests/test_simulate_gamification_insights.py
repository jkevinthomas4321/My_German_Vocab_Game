import random
from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

from tests.conftest import NOW
from wortschatz import analytics as A
from wortschatz import events, gamification, grading, insights, questions, simulate, srs


@pytest.fixture(scope="module")
def demo(core_words_module):
    ev = simulate.simulate_history(core_words_module, days=30, seed=2026, now=NOW)
    return ev, A.prepare(ev, core_words_module), srs.replay(ev)


@pytest.fixture(scope="module")
def core_words_module():
    from wortschatz import config, wordlist
    return wordlist.load_wordlist(config.WORDLIST_DIR / "german_core.csv")[0]


# ----------------------------------------------------------------------------- simulator
def test_simulation_is_reproducible_and_seed_dependent(core_words_module):
    a = simulate.simulate_history(core_words_module, days=10, seed=1, now=NOW)
    b = simulate.simulate_history(core_words_module, days=10, seed=1, now=NOW)
    c = simulate.simulate_history(core_words_module, days=10, seed=2, now=NOW)
    pd.testing.assert_frame_equal(a, b)
    assert not a.equals(c)


def test_simulated_log_is_a_valid_event_log(demo):
    ev, _, _ = demo
    assert list(ev.columns) == events.EVENT_COLUMNS and len(ev) > 300 and ev["session_id"].nunique() > 15
    assert ev["ts"].is_monotonic_increasing and ev["ts"].max() < pd.Timestamp(NOW) and ev["ts"].min() > pd.Timestamp(NOW) - timedelta(days=31)
    assert ev["correct"].isin([0, 1]).all() and ev["response_ms"].between(900, 70000).all() and (ev["retry"] == 0).all()
    assert 0.5 < ev["correct"].mean() < 0.9


def test_simulated_answers_agree_with_the_real_grader(demo, core_words_module):
    """The simulator must not invent outcomes the app's own grader would disagree with."""
    ev, _, _ = demo
    typed = ev[ev["qtype"] == "type_de"].head(40)
    for row in typed.itertuples():
        word = core_words_module[core_words_module["word_id"] == row.word_id].iloc[0].to_dict()
        q = questions.build_question(word, "type_de", core_words_module, random.Random(0))
        assert grading.grade(q, row.given).correct == bool(row.correct)


def test_simulated_learner_shows_the_effects_it_models(demo):
    ev, d, _ = demo
    lc = A.learning_curve(d, max_attempt=3).set_index("attempt")
    assert lc.loc[1, "acc"] + 0.15 < lc.loc[2, "acc"]                       # repetition helps
    fc = A.forgetting_curve(d).set_index("gap")
    assert fc.loc["1 day", "acc"] > fc.loc["8–14 days", "acc"]              # memory decays with time
    by_band = A.accuracy_by(d, "freq_band").set_index("freq_band")["acc"]
    assert by_band["Very common"] > by_band["Common"]                        # frequent words are known better
    verbs, nouns = (d[d["word_class"] == c]["correct"].mean() for c in ("verb", "noun"))
    assert verbs < nouns
    assert d[d["correct"] == 1]["response_s"].median() < d[d["correct"] == 0]["response_s"].median()


def test_simulated_history_has_streaks_and_a_gap(demo):
    _, d, _ = demo
    days = sorted(set(d["day"].dt.date))
    current, longest = A.practice_streaks(days, NOW.date())
    assert current >= 3 and len(days) < 30 and longest >= current


def test_simulation_uses_the_real_scheduler(demo):
    _, _, states = demo
    assert states["box"].between(1, 5).all() and (states["box"] == 5).sum() > 5 and states["lapses"].sum() > 0


# ----------------------------------------------------------------------------- gamification
@pytest.mark.parametrize("xp, level", [(0, 1), (149, 1), (150, 2), (599, 2), (600, 3), (1350, 4), (14000, 10)])
def test_level_thresholds(xp, level):
    assert gamification.level_for(xp).number == level


def test_level_progress_and_titles():
    lv = gamification.level_for(300)
    assert (lv.floor, lv.ceiling) == (150, 600) and lv.progress == pytest.approx(150 / 450)
    assert gamification.level_for(0).title == "Anfänger" and gamification.level_for(10**7).title == "Wortzauberer"


def test_badges_from_the_demo(demo):
    _, d, states = demo
    earned = {b.key for b in gamification.evaluate_badges(d, states) if b.earned}
    assert {"first", "seen100", "hundred"} <= earned and "thousand" not in earned


def test_no_badges_without_data():
    badges = gamification.evaluate_badges(A.prepare(events.empty_events()), srs.empty_states())
    assert len(badges) == 9 and not any(b.earned for b in badges)


def test_answers_today(demo):
    _, d, _ = demo
    assert gamification.answers_today(d, NOW.date()) == int((d["day"].dt.date == NOW.date()).sum())
    assert gamification.answers_today(A.prepare(events.empty_events())) == 0


# ----------------------------------------------------------------------------- insights
def test_insights_for_the_demo_are_specific_and_bounded(demo, core_words_module):
    _, d, states = demo
    found = insights.generate(d, states, core_words_module, NOW)
    titles = " ".join(i.title for i in found)
    assert 5 <= len(found) <= 14 and "Repetition pays off" in titles and found[0].title == "Overview"
    assert all(i.tone in ("good", "watch", "info") and i.text for i in found)


def test_insights_stay_quiet_without_enough_data(core_words_module):
    assert insights.generate(A.prepare(events.empty_events()), srs.empty_states(), core_words_module, NOW) == []
    tiny = simulate.simulate_history(core_words_module, days=2, seed=3, now=NOW).head(12)
    found = insights.generate(A.prepare(tiny, core_words_module), srs.replay(tiny), core_words_module, NOW)
    assert all(i.title not in ("Repetition pays off", "Forgetting shows up after a week", "You are getting faster") for i in found)
