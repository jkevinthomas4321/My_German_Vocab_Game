"""Grading answers. Tolerant of case, spacing and ä/ö/ü/ß typed as ae/oe/ue/ss; strict about everything else.

A blank answer or a dash is never correct (the first version of this project credited '-' cells).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from . import config
from .german import edit_distance, fold, fold_translit
from .questions import Question


@dataclass
class Grade:
    correct: bool
    given: str
    expected: str
    article_expected: str = ""
    article_given: str = ""
    near_miss: bool = False
    parts: dict[str, bool] = field(default_factory=dict)
    message: str = ""


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


def grade(q: Question, response) -> Grade:
    """`response` is the selected option / typed text, or (past, perfect) for 'forms'."""
    if q.qtype in ("choose_en", "choose_de", "article"):
        return _grade_choice(q, str(response))
    if q.qtype == "forms":
        return _grade_forms(q, response)
    return _grade_typed(q, str(response))


def _grade_choice(q: Question, selected: str) -> Grade:
    correct = fold(selected) == fold(q.answer)
    article_expected = q.article if q.qtype in ("article", "choose_de") and q.article in config.ARTICLES else ""
    article_given = ""
    if q.qtype == "article":
        article_given = selected.casefold()
    elif q.qtype == "choose_de" and article_expected:
        # Only the same noun with another article says something about this word's gender.
        article, noun = split_article(selected)
        article_given = article if noun and fold(noun) == fold(q.german) else ""
    return Grade(correct=correct, given=selected, expected=q.answer,
                 article_expected=article_expected, article_given=article_given)


def _grade_typed(q: Question, text: str) -> Grade:
    article, word = split_article(text)
    if q.article in config.ARTICLES:
        word_ok = same_text(word, q.german)
        article_ok = article == q.article
        correct = word_ok and article_ok
        message = ""
        if word_ok and not article:
            message = "Nouns need their article."
        elif word_ok and not article_ok:
            message = f"The article is “{q.article}”."
        return Grade(correct, text, q.german_display, q.article, article,
                     near_miss=not correct and _near(word, q.german),
                     parts={"article": article_ok, "word": word_ok}, message=message)
    plain = " ".join([article, word]).strip()
    correct = same_text(plain, q.german)
    return Grade(correct, text, q.german_display, near_miss=not correct and _near(plain, q.german),
                 parts={"word": correct})


def _grade_forms(q: Question, response) -> Grade:
    past, perfect = (list(response) + ["", ""])[:2]
    past_ok, perfect_ok = same_text(past, q.past_tense), same_text(perfect, q.perfect_tense)
    near = not (past_ok and perfect_ok) and (
        (past_ok or _near(past, q.past_tense)) and (perfect_ok or _near(perfect, q.perfect_tense)))
    return Grade(past_ok and perfect_ok, f"{past} | {perfect}", q.answer, near_miss=near,
                 parts={"past_tense": past_ok, "perfect_tense": perfect_ok})


def to_event(q: Question, g: Grade, ts: datetime, session_id: str, response_ms: int) -> dict:
    """The log row for one graded answer."""
    return {
        "ts": ts, "session_id": session_id, "word_id": q.word_id, "word_class": q.word_class,
        "english": q.english, "german": q.german, "qtype": q.qtype, "direction": q.direction,
        "correct": int(g.correct), "response_ms": int(response_ms), "given": g.given, "expected": g.expected,
        "article_expected": g.article_expected, "article_given": g.article_given, "retry": int(q.retry),
    }
