import random
from datetime import timedelta

import pandas as pd
import pytest

from tests.conftest import NOW
from wortschatz import config, events, grading, questions, srs
from wortschatz.german import edit_distance, fold_translit, suffix_group


def word(df, german):
    return df[df["german"] == german].iloc[0].to_dict()


def build(df, german, qtype, seed=1):
    return questions.build_question(word(df, german), qtype, df, random.Random(seed))


# ----------------------------------------------------------------------------- german helpers
@pytest.mark.parametrize("noun, group", [("Zeitung", "-ung"), ("Möglichkeit", "-heit / -keit"), ("Gesellschaft", "-schaft"),
                                         ("Information", "-ion"), ("Mädchen", "-chen / -lein"), ("Zimmer", "-er"),
                                         ("Tisch", "other endings"), ("Katze", "-e")])
def test_suffix_groups(noun, group):
    assert suffix_group(noun) == group


def test_edit_distance_counts_a_swap_as_one():
    assert (edit_distance("abc", "abc"), edit_distance("tisch", "tich"), edit_distance("schreiben", "schrieben")) == (0, 1, 1)
    assert edit_distance("kitten", "sitting") == 3


def test_transliteration_folds_umlauts():
    assert fold_translit("Größe") == fold_translit("GROESSE") == "groesse"


# ----------------------------------------------------------------------------- grading typed answers
@pytest.mark.parametrize("answer", ["der Tisch", "Der  tisch", "  DER TISCH "])
def test_noun_answers_forgive_case_and_spacing(mini_words, answer):
    assert grading.grade(build(mini_words, "Tisch", "type_de"), answer).correct


@pytest.mark.parametrize("answer, message", [("Tisch", "article"), ("die Tisch", "article"), ("der Tich", ""), ("", ""), ("-", ""), ("–", "")])
def test_wrong_noun_answers(mini_words, answer, message):
    g = grading.grade(build(mini_words, "Tisch", "type_de"), answer)
    assert not g.correct and message in g.message.lower()


def test_dash_and_blank_are_never_correct_for_any_question_type(mini_words):
    """Regression: the first version of this project credited '-' as a correct answer."""
    for german, qtype in [("Tisch", "type_de"), ("Tisch", "article"), ("schreiben", "forms"), ("Tisch", "choose_de"), ("schnell", "type_de")]:
        q = build(mini_words, german, qtype)
        response = ("-", "-") if qtype == "forms" else "-"
        assert not grading.grade(q, response).correct


def test_umlaut_transliteration_is_accepted_but_dropping_the_umlaut_is_not(mini_words):
    q = build(mini_words, "Tür", "type_de")
    assert grading.grade(q, "die Tuer").correct and grading.grade(q, "die Tür").correct
    assert not grading.grade(q, "die Tur").correct


def test_near_miss_is_flagged_but_not_credited(mini_words):
    g = grading.grade(build(mini_words, "Tisch", "type_de"), "der Tich")
    assert g.near_miss and not g.correct
    assert not grading.grade(build(mini_words, "Tisch", "type_de"), "der Stuhl").near_miss


def test_non_noun_typed_answer(mini_words):
    q = build(mini_words, "schnell", "type_de")
    assert grading.grade(q, "Schnell").correct and not grading.grade(q, "langsam").correct


def test_typed_answer_records_the_article_claim(mini_words):
    g = grading.grade(build(mini_words, "Tisch", "type_de"), "die Tisch")
    assert (g.article_expected, g.article_given) == ("der", "die")


def test_verb_forms(mini_words):
    q = build(mini_words, "schreiben", "forms")
    assert grading.grade(q, ("schrieb", "hat geschrieben")).correct
    assert grading.grade(q, ("Schrieb", " hat  geschrieben ")).correct
    partial = grading.grade(q, ("schrieb", "ist geschrieben"))
    assert not partial.correct and partial.parts == {"past_tense": True, "perfect_tense": False}
    assert grading.grade(q, ("schreib", "hat geschrieben")).near_miss


# ----------------------------------------------------------------------------- grading choices
def test_choose_questions(mini_words):
    q = build(mini_words, "Tisch", "choose_de")
    assert grading.grade(q, "der Tisch").correct
    wrong = grading.grade(q, next(o for o in q.options if o.endswith("Tisch") and o != "der Tisch"))
    assert not wrong.correct and wrong.article_given in ("die", "das") and wrong.article_expected == "der"


def test_picking_a_different_noun_says_nothing_about_this_nouns_gender(mini_words):
    q = build(mini_words, "Tisch", "choose_de")
    other = next(o for o in q.options if not o.endswith("Tisch"))
    assert grading.grade(q, other).article_given == ""


def test_article_question(mini_words):
    q = build(mini_words, "Stadt", "article")
    assert grading.grade(q, "die").correct
    g = grading.grade(q, "das")
    assert not g.correct and (g.article_expected, g.article_given) == ("die", "das")


def test_event_row_matches_the_grade(mini_words):
    q = build(mini_words, "Tisch", "article")
    row = grading.to_event(q, grading.grade(q, "die"), NOW, "s1", 1234)
    assert set(row) == set(events.EVENT_COLUMNS)
    assert (row["correct"], row["article_given"], row["response_ms"], row["retry"]) == (0, "die", 1234, 0)


# ----------------------------------------------------------------------------- building questions
def test_available_question_types(mini_words):
    assert set(questions.available_qtypes(word(mini_words, "Tisch"))) == {"choose_en", "choose_de", "type_de", "article"}
    assert "forms" in questions.available_qtypes(word(mini_words, "gehen"))
    assert questions.available_qtypes(word(mini_words, "heute")) == ["choose_en", "choose_de", "type_de"]


@pytest.mark.parametrize("qtype", ["choose_en", "choose_de"])
@pytest.mark.parametrize("german", ["Tisch", "schnell", "heute"])
def test_choice_options_are_unique_and_contain_the_answer(mini_words, qtype, german):
    for seed in range(20):
        q = build(mini_words, german, qtype, seed)
        assert q.answer in q.options and len(set(q.options)) == len(q.options) == 4


def test_noun_choices_include_a_same_noun_wrong_article_decoy(mini_words):
    for seed in range(20):
        q = build(mini_words, "Tisch", "choose_de", seed)
        decoys = [o for o in q.options if o.endswith(" Tisch") and o != "der Tisch"]
        assert len(decoys) == 1


def test_options_fall_back_to_other_classes_when_the_class_is_small(mini_words):
    assert len(set(build(mini_words, "heute", "choose_en").options)) == 4


def test_info_line_teaches_plural_and_forms(mini_words):
    assert questions.info_line(build(mini_words, "Kind", "type_de")) == "das Kind · plural: die Kinder"
    assert questions.info_line(build(mini_words, "gehen", "forms")) == "gehen · ging · ist gegangen"


# ----------------------------------------------------------------------------- planning
def test_first_session_spans_word_classes_in_frequency_order(core_words):
    plan = questions.plan_session(core_words, srs.empty_states(), "smart", 20, NOW, random.Random(0))
    classes = {q.word_class for q in plan}
    assert len(plan) == 20 and {"noun", "verb"} <= classes and len(classes) >= 3
    zipf = core_words.set_index("word_id")["zipf"]
    assert min(zipf[q.word_id] for q in plan) > core_words["zipf"].median()      # starts with the commoner half


def test_session_is_deterministic_for_a_seed_and_has_no_duplicate_words(core_words):
    first = questions.plan_session(core_words, srs.empty_states(), "smart", 25, NOW, random.Random(5))
    second = questions.plan_session(core_words, srs.empty_states(), "smart", 25, NOW, random.Random(5))
    assert [(q.word_id, q.qtype) for q in first] == [(q.word_id, q.qtype) for q in second]
    assert len({q.word_id for q in first}) == 25


def answered(df, german_words, correct, when):
    rows = []
    for german in german_words:
        w = word(df, german)
        rows.append({"ts": when, "session_id": "s", "word_id": w["word_id"], "word_class": w["word_class"], "english": w["english"],
                     "german": w["german"], "qtype": "choose_en", "direction": "de→en", "correct": int(correct), "response_ms": 2000,
                     "given": "", "expected": "", "article_expected": "", "article_given": "", "retry": 0})
    return pd.DataFrame(rows)


def test_due_words_come_before_new_words(mini_words):
    log = answered(mini_words, ["Tisch", "Stadt"], True, NOW - timedelta(days=2))
    plan = questions.plan_session(mini_words, srs.replay(log), "smart", 4, NOW, random.Random(0))
    assert {"Tisch", "Stadt"} <= {q.german for q in plan}


def test_words_not_yet_due_are_only_used_as_filler(mini_words):
    log = answered(mini_words, ["Tisch"], True, NOW - timedelta(minutes=5))        # box 1: due again in 6 hours
    states = srs.replay(log)
    enough_new = questions.plan_session(mini_words, states, "smart", 9, NOW, random.Random(0))
    assert "Tisch" not in {q.german for q in enough_new}                           # 9 unseen words are available
    everything = questions.plan_session(mini_words, states, "smart", 10, NOW, random.Random(0))
    assert "Tisch" in {q.german for q in everything}                               # only now is it needed to fill the session


def test_backlog_limits_new_words(core_words):
    ids = list(core_words["german"].iloc[:30])
    log = answered(core_words, ids, False, NOW - timedelta(days=3))
    plan = questions.plan_session(core_words, srs.replay(log), "smart", 20, NOW, random.Random(0))
    new = [q for q in plan if q.german not in ids]
    assert len(new) <= 2 and len(plan) == 20


@pytest.mark.parametrize("mode, check", [
    ("article", lambda q: q.qtype == "article" and q.word_class == "noun"),
    ("forms", lambda q: q.qtype == "forms" and q.word_class == "verb"),
    ("type", lambda q: q.qtype == "type_de"),
])
def test_dedicated_modes(core_words, mode, check):
    plan = questions.plan_session(core_words, srs.empty_states(), mode, 12, NOW, random.Random(1))
    assert len(plan) == 12 and all(check(q) for q in plan)


def test_weak_mode_picks_words_missed_more_than_once(mini_words):
    log = pd.concat([answered(mini_words, ["Tisch", "Stadt"], False, NOW - timedelta(days=3)),
                     answered(mini_words, ["Tisch"], False, NOW - timedelta(days=2)),
                     answered(mini_words, ["Stadt"], True, NOW - timedelta(days=2))])
    plan = questions.plan_session(mini_words, srs.replay(log), "weak", 5, NOW, random.Random(0))
    assert {q.german for q in plan} == {"Tisch", "Stadt"}
    assert not questions.plan_session(mini_words, srs.empty_states(), "weak", 5, NOW, random.Random(0))


def test_class_filter_and_word_id_filter(core_words):
    plan = questions.plan_session(core_words, srs.empty_states(), "smart", 10, NOW, random.Random(0), classes=["verb"])
    assert {q.word_class for q in plan} == {"verb"}
    ids = list(core_words["word_id"].iloc[:3])
    assert {q.word_id for q in questions.plan_session(core_words, srs.empty_states(), "smart", 10, NOW, random.Random(0), word_ids=ids)} == set(ids)


def test_harder_question_types_for_better_known_words(mini_words):
    rng = random.Random(0)
    w = word(mini_words, "Tisch")
    assert {questions.pick_qtype(w, 0, rng) for _ in range(60)} <= {"choose_en", "choose_de", "article"}
    assert "type_de" in {questions.pick_qtype(w, 4, rng) for _ in range(60)}


def test_retry_copy_is_marked(mini_words):
    q = build(mini_words, "Tisch", "article")
    assert questions.retry_of(q).retry and not q.retry
