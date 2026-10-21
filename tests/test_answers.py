import pytest

from wortschatz import answers


def noun(**kw):
    return {"word_class": "noun", "english": "table", "article": "der", "german": "Tisch", "plural": "Tische",
            "past_tense": "", "perfect_tense": "", **kw}


VERB = {"word_class": "verb", "english": "to go", "article": "", "german": "gehen", "plural": "",
        "past_tense": "ging", "perfect_tense": "ist gegangen"}
ADJ = {"word_class": "adjective", "english": "fast", "article": "", "german": "schnell", "plural": "",
       "past_tense": "", "perfect_tense": ""}


# ----------------------------------------------------------------------------- English
@pytest.mark.parametrize("given", ["table", "Table", "  TABLE ", "the table", "a table"])
def test_english_ignores_case_spacing_and_leading_articles(given):
    assert answers.check_english(given, "table").correct


@pytest.mark.parametrize("given", ["go", "to go", "To Go"])
def test_leading_to_is_optional(given):
    assert answers.check_english(given, "to go").correct


def test_every_listed_translation_is_accepted():
    for given in ("do", "make", "to do", "to make"):
        assert answers.check_english(given, "to do / make").correct
    assert answers.check_english("create", "to do; make, create").correct


def test_bracketed_hints_are_not_required_and_may_be_included():
    assert answers.check_english("friend", "friend (male)").correct
    assert answers.check_english("friend (male)", "friend (male)").correct
    assert answers.check_english("light", "light (not heavy)").correct
    assert answers.check_english("to", "to (a person or place)").correct


@pytest.mark.parametrize("given", ["", "   ", "-", "–", "chair", "tabl"])
def test_wrong_english(given):
    assert not answers.check_english(given, "table").correct


def test_a_one_letter_typo_is_flagged_not_credited():
    check = answers.check_english("tabel", "table")
    assert not check.correct and check.near_miss
    assert not answers.check_english("tabl", "tab").near_miss          # too short to call a near miss
    assert not answers.check_english("chair", "table").near_miss


def test_variants_helper():
    assert answers.english_variants("to do / make (something); create") == ["do", "make", "create"]


# ----------------------------------------------------------------------------- German nouns
@pytest.mark.parametrize("given", ["der Tisch", "Der  tisch", "  DER TISCH "])
def test_noun_needs_the_right_article_and_word(given):
    assert answers.check_german(noun(), given).correct


@pytest.mark.parametrize("given, hint", [("Tisch", "article"), ("die Tisch", "article"), ("der Tich", ""), ("", ""), ("-", "")])
def test_wrong_nouns(given, hint):
    check = answers.check_german(noun(), given)
    assert not check.correct and hint in check.message.lower()


def test_noun_near_miss_and_parts():
    check = answers.check_german(noun(), "der Tich")
    assert check.near_miss and check.parts == {"article": True, "word": False}
    assert answers.check_german(noun(), "die Tisch").parts == {"article": False, "word": True}


def test_umlauts_may_be_typed_as_ae_oe_ue_ss_but_not_dropped():
    tuer = noun(german="Tür", article="die")
    assert answers.check_german(tuer, "die Tuer").correct and answers.check_german(tuer, "die Tür").correct
    assert not answers.check_german(tuer, "die Tur").correct
    assert answers.check_german(noun(german="Straße", article="die"), "die Strasse").correct


# ----------------------------------------------------------------------------- German verbs and others
def test_verbs_need_all_three_forms():
    assert answers.german_fields(VERB) == ["infinitive", "past", "perfect"]
    assert answers.check_german(VERB, ("gehen", "ging", "ist gegangen")).correct
    assert answers.check_german(VERB, (" Gehen", "GING", "ist  gegangen")).correct
    partial = answers.check_german(VERB, ("gehen", "ging", "hat gegangen"))
    assert not partial.correct and partial.parts == {"infinitive": True, "past": True, "perfect": False}


def test_verb_without_forms_is_asked_like_a_plain_word():
    bare = {**VERB, "past_tense": "", "perfect_tense": ""}
    assert answers.german_fields(bare) == ["answer"] and answers.check_german(bare, "gehen").correct


def test_verb_near_miss():
    assert answers.check_german(VERB, ("gehen", "ging", "ist gegagnen")).near_miss


def test_plain_words():
    assert answers.check_german(ADJ, "schnell").correct and not answers.check_german(ADJ, "langsam").correct
    assert answers.german_fields(ADJ) == ["answer"]


def test_nothing_is_correct_when_blank_or_a_dash():
    for word, blank in [(noun(), "-"), (VERB, ("-", "-", "-")), (ADJ, " "), (VERB, ("", "", ""))]:
        assert not answers.check_german(word, blank).correct


def test_display_and_dispatch():
    assert answers.german_display(noun()) == "der Tisch" and answers.german_display(ADJ) == "schnell"
    assert answers.expected_german(VERB) == "gehen · ging · ist gegangen"
    assert answers.check(noun(), "de_en", "table").correct and answers.check(noun(), "en_de", "der Tisch").correct
    assert answers.blank("-") and answers.blank(("", " -")) and not answers.blank(("", "x"))
