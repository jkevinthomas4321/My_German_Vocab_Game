import random
from datetime import datetime, timedelta

import pandas as pd
import pytest

from tests.conftest import NOW
from wortschatz import config, session
from wortschatz.progress import Progress
from wortschatz.session import CardDeck, TestRun
from wortschatz.storage import Store

DIARY, SECOND = config.STATUS_DIARY, config.STATUS_SECOND


def word(df, german):
    return df[df["german"] == german].iloc[0].to_dict()


def answer_for(item, right=True):
    """A correct or deliberately wrong response for a question."""
    w = item.word
    if item.direction == "de_en":
        return w["english"] if right else "zzz"
    if w["word_class"] == "verb":
        return (w["german"], w["past_tense"], w["perfect_tense"]) if right else (w["german"], "xx", "yy")
    return f'{w["article"]} {w["german"]}'.strip() if right else "zzz"


def play(run, right_for=lambda item: True):
    while not run.finished:
        run.submit(answer_for(run.current, right_for(run.current)))
        run.advance()
    return run


# ----------------------------------------------------------------------------- the rules
@pytest.mark.parametrize("before, passed, after", [
    (None, True, DIARY), (None, False, SECOND), (SECOND, True, DIARY), (SECOND, False, SECOND),
    (DIARY, True, DIARY), (DIARY, False, SECOND)])
def test_the_six_transitions(mini_words, before, passed, after):
    p, w = Progress(), word(mini_words, "Tisch")
    if before == SECOND:
        p.apply(w, False, NOW)
    elif before == DIARY:
        p.apply(w, True, NOW)
    t = p.apply(w, passed, NOW + timedelta(days=1))
    assert (t.before, t.after, t.passed) == (before, after, passed) and p.status(w["word_id"]) == after


def test_counters_and_dates_follow_the_journey(mini_words):
    p, w = Progress(), word(mini_words, "Tisch")
    p.apply(w, False, NOW)                                  # learn -> second chance
    p.apply(w, True, NOW + timedelta(days=1))               # retest passed -> diary
    p.apply(w, True, NOW + timedelta(days=2))               # revision passed
    p.apply(w, True, NOW + timedelta(days=3))               # revision passed
    r = p.records[w["word_id"]]
    assert (r["tests"], r["passes"], r["fails"], r["streak"], r["returns"]) == (4, 3, 1, 3, 0)
    assert r["first_seen"] == NOW and r["diary_since"] == NOW + timedelta(days=1) and r["last_tested"] == NOW + timedelta(days=3)
    p.apply(w, False, NOW + timedelta(days=4))              # revision failed -> back to second chance
    r = p.records[w["word_id"]]
    assert (r["status"], r["streak"], r["returns"], r["diary_since"], r["fails"]) == (SECOND, 0, 1, None, 2)


def test_a_word_is_never_in_both_lists(mini_words):
    p = Progress()
    for german, passed in [("Tisch", True), ("Stadt", False), ("Kind", True)]:
        p.apply(word(mini_words, german), passed, NOW)
    assert p.ids(DIARY).isdisjoint(p.ids(SECOND)) and p.count(DIARY) == 2 and p.count(SECOND) == 1


def test_remove_lets_a_word_be_learned_again(mini_words):
    p, w = Progress(), word(mini_words, "Tisch")
    p.apply(w, True, NOW)
    assert p.remove(w["word_id"]) and not p.remove(w["word_id"]) and p.status(w["word_id"]) is None


def test_frame_round_trip(mini_words):
    p = Progress()
    p.apply(word(mini_words, "Tisch"), True, NOW)
    p.apply(word(mini_words, "Stadt"), False, NOW)
    frame = p.frame()
    assert frame["status"].tolist() == [DIARY, SECOND] and pd.api.types.is_datetime64_any_dtype(frame["last_tested"])
    again = Progress.from_frame(frame)
    pd.testing.assert_frame_equal(again.frame(), frame)


# ----------------------------------------------------------------------------- choosing words
def test_new_words_exclude_everything_already_in_the_game(mini_words):
    p = Progress()
    p.apply(word(mini_words, "Tisch"), True, NOW)
    p.apply(word(mini_words, "Stadt"), False, NOW)
    assert set(session.new_words(mini_words, p)["german"]) == set(mini_words["german"]) - {"Tisch", "Stadt"}
    assert session.class_counts(session.new_words(mini_words, p)) == {"noun": 2, "verb": 2, "adjective": 3, "adverb": 1}


def test_pick_new_words_by_class_count_and_order(core_words):
    p = Progress()
    by_freq = session.pick_new_words(core_words, p, "noun", 8)
    assert len(by_freq) == 8 and {w["word_class"] for w in by_freq} == {"noun"}
    assert [w["zipf"] for w in by_freq] == sorted((w["zipf"] for w in by_freq), reverse=True)
    sheet = session.pick_new_words(core_words, p, "verb", 5, order="sheet")
    assert [w["german"] for w in sheet] == list(core_words[core_words["word_class"] == "verb"]["german"].head(5))
    a = session.pick_new_words(core_words, p, "noun", 8, order="random", rng=random.Random(1))
    b = session.pick_new_words(core_words, p, "noun", 8, order="random", rng=random.Random(1))
    assert a == b and a != by_freq
    assert len(session.pick_new_words(core_words, p, "all", 5)) == 5 and len(session.pick_new_words(core_words, p, None, 5)) == 5


def test_pick_stops_when_the_class_runs_out(mini_words):
    assert len(session.pick_new_words(mini_words, Progress(), "adverb", 10)) == 1


def test_second_chance_picks_most_missed_first(mini_words):
    p = Progress()
    for german, fails in [("Tisch", 1), ("Stadt", 3), ("Kind", 2)]:
        for _ in range(fails):
            p.apply(word(mini_words, german), False, NOW)
    assert [w["german"] for w in session.pick_second_chance(p)] == ["Stadt", "Kind", "Tisch"]
    assert len(session.pick_second_chance(p, 2)) == 2


def test_diary_picking_orders(mini_words):
    p = Progress()
    for i, german in enumerate(["Tisch", "Stadt", "Kind"]):
        p.apply(word(mini_words, german), True, NOW + timedelta(days=i))
    p.apply(word(mini_words, "Tisch"), True, NOW + timedelta(days=10))               # Tisch revised most recently
    assert [w["german"] for w in session.pick_diary(p, "noun", 3, "stale")] == ["Stadt", "Kind", "Tisch"]
    assert [w["german"] for w in session.pick_diary(p, "noun", 3, "newest")] == ["Kind", "Stadt", "Tisch"]
    assert len(session.pick_diary(p, "verb", 3)) == 0 and len(session.pick_diary(p, "all", 2, "random", random.Random(0))) == 2


# ----------------------------------------------------------------------------- cards
def test_card_deck_navigation(mini_words):
    deck = CardDeck(mini_words.to_dict("records")[:3])
    assert deck.index == 0 and not deck.last
    deck.previous()
    assert deck.index == 0
    deck.next(); deck.next(); deck.next()
    assert deck.index == 2 and deck.last and deck.current["german"] == "Kind"


# ----------------------------------------------------------------------------- a test run
def new_store():
    return Store("me")


def test_a_perfect_test_moves_every_word_into_the_diary(mini_words):
    store = new_store()
    words = session.pick_new_words(mini_words, store.progress, "noun", 4, "sheet")
    run = play(TestRun(store, words, shuffle=False))
    assert run.total == 8 and run.finished and run.done_words == 4
    assert store.progress.ids(DIARY) == {w["word_id"] for w in words} and store.progress.count(SECOND) == 0
    assert all(t.entered_diary for t in run.outcomes.values())
    result = run.results()
    assert len(result["passed"]) == 4 and not result["failed"] and result["correct"] == result["answered"] == 8


def test_one_wrong_answer_sends_the_word_to_second_chance(mini_words):
    store = new_store()
    words = session.pick_new_words(mini_words, store.progress, "noun", 3, "sheet")
    target = words[0]["word_id"]
    run = play(TestRun(store, words, shuffle=False), lambda item: not (item.word["word_id"] == target and item.direction == "en_de"))
    assert store.progress.status(target) == SECOND and store.progress.count(DIARY) == 2
    failed = run.results()["failed"]
    assert len(failed) == 1 and failed[0]["wrong"][0].check.expected == "der Tisch"


def test_both_directions_are_tested_for_every_word(mini_words):
    store = new_store()
    run = TestRun(store, session.pick_new_words(mini_words, store.progress, "adjective", 3, "sheet"), shuffle=False)
    assert [(i.word["german"], i.direction) for i in run.items][:2] == [("schnell", "de_en"), ("schnell", "en_de")]
    only = TestRun(store, [word(mini_words, "Tisch")], directions=["en_de"])
    assert [i.direction for i in only.items] == ["en_de"]
    play(only)
    assert store.progress.status(word(mini_words, "Tisch")["word_id"]) == DIARY          # one direction is enough then


def test_verbs_are_tested_on_all_their_forms(mini_words):
    store = new_store()
    verbs = session.pick_new_words(mini_words, store.progress, "verb", 2, "sheet")
    run = play(TestRun(store, verbs, shuffle=False))
    assert store.progress.count(DIARY) == 2
    run2 = play(TestRun(new_store(), verbs, shuffle=False), lambda item: item.direction == "de_en")
    assert all(f.check.parts.get("past") is False for f in run2.log if f.item.direction == "en_de")


def test_the_two_questions_of_a_word_are_not_adjacent(core_words):
    words = session.pick_new_words(core_words, Progress(), "noun", 10)
    for seed in range(20):
        run = TestRun(new_store(), words, rng=random.Random(seed))
        ids = [i.word["word_id"] for i in run.items]
        assert all(a != b for a, b in zip(ids, ids[1:])) and len(ids) == 20


def test_second_chance_retest_and_diary_revision(mini_words):
    store = new_store()
    words = session.pick_new_words(mini_words, store.progress, "noun", 3, "sheet")
    play(TestRun(store, words, shuffle=False), lambda item: False)                   # everything failed
    assert store.progress.count(SECOND) == 3 and store.progress.count(DIARY) == 0
    # a failed re-test keeps them in second chance
    play(TestRun(store, session.pick_second_chance(store.progress), shuffle=False), lambda item: False)
    assert store.progress.count(SECOND) == 3
    # a passed re-test moves them to the diary
    retest = TestRun(store, session.pick_second_chance(store.progress), shuffle=False)
    assert set(retest.phase.values()) == {config.PHASE_RETEST}
    play(retest)
    assert store.progress.count(DIARY) == 3 and store.progress.count(SECOND) == 0
    # revision: one word fails and goes back, the others stay
    revise = TestRun(store, session.pick_diary(store.progress, "all", 10), shuffle=False)
    assert set(revise.phase.values()) == {config.PHASE_DIARY}
    bad = revise.words[0]["word_id"]
    play(revise, lambda item: item.word["word_id"] != bad)
    assert store.progress.status(bad) == SECOND and store.progress.count(DIARY) == 2
    assert revise.outcomes[bad].left_diary


def test_progress_is_saved_as_words_finish_not_only_at_the_end(mini_words):
    store = new_store()
    run = TestRun(store, session.pick_new_words(mini_words, store.progress, "noun", 2, "sheet"), shuffle=False)
    for _ in range(2):                                                                # both questions of the first word
        run.submit(answer_for(run.current)); run.advance()
    assert Store("me").progress.count(DIARY) == 1                                      # a fresh load sees it already


def test_every_answer_is_logged_with_its_phase(mini_words):
    store = new_store()
    words = session.pick_new_words(mini_words, store.progress, "noun", 2, "sheet")
    play(TestRun(store, words, shuffle=False, session_id="s1", clock=lambda: NOW))
    log = store.attempts()
    assert len(log) == 4 and set(log["phase"]) == {"learn"} and set(log["session_id"]) == {"s1"}
    assert set(log["direction"]) == {"de_en", "en_de"} and log["correct"].sum() == 4 and (log["ts"] == pd.Timestamp(NOW)).all()
    play(TestRun(store, session.pick_diary(store.progress, "all", 5), shuffle=False))
    assert set(store.attempts()["phase"]) == {"learn", "diary"}


def test_skip_counts_as_wrong_and_blank_or_dash_never_passes(mini_words):
    store = new_store()
    words = session.pick_new_words(mini_words, store.progress, "verb", 1, "sheet")
    run = TestRun(store, words, shuffle=False)
    run.submit("-"); run.advance()
    run.skip()
    run.advance()
    assert store.progress.count(SECOND) == 1 and store.progress.count(DIARY) == 0
    assert [f.correct for f in run.log] == [False, False]


def test_misuse_is_rejected(mini_words):
    store = new_store()
    with pytest.raises(ValueError):
        TestRun(store, [])
    with pytest.raises(ValueError):
        TestRun(store, [word(mini_words, "Tisch")], directions=["sideways"])
    run = TestRun(store, [word(mini_words, "Tisch")], shuffle=False)
    run.submit("table")
    with pytest.raises(RuntimeError):
        run.submit("again")                                                            # must advance() first


# ----------------------------------------------------------------------------- storage
def test_progress_survives_a_restart(mini_words):
    store = new_store()
    play(TestRun(store, session.pick_new_words(mini_words, store.progress, "noun", 3, "sheet"), shuffle=False),
         lambda item: item.word["german"] != "Tisch")
    again = Store("me")
    assert again.progress.ids(DIARY) == store.progress.ids(DIARY) and again.progress.ids(SECOND) == store.progress.ids(SECOND)
    pd.testing.assert_frame_equal(again.progress.frame(), store.progress.frame())


def test_profiles_are_separate(mini_words):
    play(TestRun(Store("me"), [word(mini_words, "Tisch")], shuffle=False))
    assert Store("demo").progress.count(DIARY) == 0 and Store("demo").attempts().empty


def test_remove_word_is_saved_and_logged(mini_words):
    store = new_store()
    w = word(mini_words, "Tisch")
    play(TestRun(store, [w], shuffle=False))
    assert store.remove_word(w["word_id"]) and not store.remove_word(w["word_id"])
    assert Store("me").progress.count(DIARY) == 0 and store.attempts()["phase"].iloc[-1] == config.PHASE_REMOVED


def test_a_damaged_attempts_row_is_skipped(mini_words):
    store = new_store()
    play(TestRun(store, [word(mini_words, "Tisch")], shuffle=False))
    with open(store.attempts_file, "a", encoding="utf-8") as handle:
        handle.write("not-a-date,s,learn,w,noun,x,X,de_en,maybe,5,,\n")
    assert len(store.attempts()) == 2
