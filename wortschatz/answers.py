"""Checking typed answers.

English answers are matched against every translation listed in the sheet ("to do / make" accepts
"do" and "make"), ignoring a leading "to"/"the"/"a", brackets, case and spacing.
German answers must be spelled exactly (nouns with their article), except that ae/oe/ue/ss are
accepted for ä/ö/ü/ß so nobody needs a German keyboard. A blank answer or a dash is never correct.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from . import config
from .german import edit_distance, fold, fold_translit

_BRACKETS = re.compile(r"\([^)]*\)")
_LEADING = re.compile(r"^(to|the|a|an)\s+(?=\S)")


@dataclass
class AnswerCheck:
    correct: bool
    expected: str
    given: str
    near_miss: bool = False
    message: str = ""
    parts: dict[str, bool] = field(default_factory=dict)


# ----------------------------------------------------------------------------- English
def normalize_english(text: object) -> str:
    cleaned = fold(_BRACKETS.sub(" ", str(text or "")))
    return _LEADING.sub("", cleaned).strip()


def english_variants(expected: str) -> list[str]:
    """Every accepted translation in an English cell: 'to do / make; create' -> do, make, create."""
    variants: list[str] = []
    for part in re.split(r"[/;,]", _BRACKETS.sub(" ", expected)):
        normalized = normalize_english(part)
        if normalized and normalized not in variants:
            variants.append(normalized)
    return variants


def check_english(given: str, expected: str) -> AnswerCheck:
    answer = normalize_english(given)
    variants = english_variants(expected)
    if answer and answer in variants:
        return AnswerCheck(True, expected, given)
    near = bool(answer) and any(len(v) >= 5 and edit_distance(answer, v) == 1 for v in variants)
    return AnswerCheck(False, expected, given, near_miss=near)


# ----------------------------------------------------------------------------- German
def split_article(text: str) -> tuple[str, str]:
    """'der Tisch' -> ('der', 'Tisch');  'Tisch' -> ('', 'Tisch')."""
    tokens = text.strip().split()
    if len(tokens) > 1 and tokens[0].casefold() in config.ARTICLES:
        return tokens[0].casefold(), " ".join(tokens[1:])
    return "", " ".join(tokens)


def same_text(a: str, b: str) -> bool:
    key = fold_translit(a)
    return key != "" and key == fold_translit(b)


def _near(a: str, b: str) -> bool:
    ka, kb = fold_translit(a), fold_translit(b)
    return len(kb) >= 4 and ka != kb and edit_distance(ka, kb) == 1


def has_forms(word: Mapping) -> bool:
    return word["word_class"] == "verb" and bool(word["past_tense"]) and bool(word["perfect_tense"])


def german_fields(word: Mapping) -> list[str]:
    """The boxes the learner has to fill in for English -> German."""
    return ["infinitive", "past", "perfect"] if has_forms(word) else ["answer"]


def german_display(word: Mapping) -> str:
    """The German side of a card: 'der Tisch' or 'gehen'."""
    return f'{word["article"]} {word["german"]}'.strip()


def expected_german(word: Mapping) -> str:
    if has_forms(word):
        return f'{word["german"]} · {word["past_tense"]} · {word["perfect_tense"]}'
    return german_display(word)


def check_german(word: Mapping, response) -> AnswerCheck:
    """`response` is a string, or (infinitive, past, perfect) for verbs that have forms."""
    if has_forms(word):
        given = list(response) if not isinstance(response, str) else [response]
        given = (given + ["", "", ""])[:3]
        wanted = [word["german"], word["past_tense"], word["perfect_tense"]]
        parts = dict(zip(("infinitive", "past", "perfect"), (same_text(g, w) for g, w in zip(given, wanted))))
        correct = all(parts.values())
        near = not correct and all(ok or _near(g, w) for ok, g, w in zip(parts.values(), given, wanted))
        return AnswerCheck(correct, expected_german(word), " · ".join(given).strip(" ·"), near_miss=near, parts=parts)

    text = response if isinstance(response, str) else str(response[0])
    if word["article"] in config.ARTICLES:
        article, noun = split_article(text)
        noun_ok, article_ok = same_text(noun, word["german"]), article == word["article"]
        message = ""
        if noun_ok and not article:
            message = "Nouns need their article."
        elif noun_ok and not article_ok:
            message = f"The article is “{word['article']}”."
        return AnswerCheck(noun_ok and article_ok, expected_german(word), text,
                           near_miss=not (noun_ok and article_ok) and _near(noun, word["german"]),
                           message=message, parts={"article": article_ok, "word": noun_ok})
    correct = same_text(text, word["german"])
    return AnswerCheck(correct, expected_german(word), text, near_miss=not correct and _near(text, word["german"]),
                       parts={"word": correct})


def check(word: Mapping, direction: str, response) -> AnswerCheck:
    """Grade one question: `direction` is 'de_en' (type the English) or 'en_de' (type the German)."""
    if direction == "de_en":
        return check_english(str(response), word["english"])
    return check_german(word, response)


def blank(response: str | Sequence[str]) -> bool:
    if isinstance(response, str):
        return response.strip(" -–—") == ""
    return all(blank(r) for r in response)
