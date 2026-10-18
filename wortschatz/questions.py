"""Turning word rows into questions, and planning which words a session practises.

Question types
  choose_en  German -> English, pick from 4          (recognition)
  choose_de  English -> German, pick from 4          (nouns carry an article; one distractor is the
                                                      same noun with a wrong article)
  type_de    English -> German, typed                (nouns need their article)
  article    German noun -> der / die / das          (gender drill)
  forms      verb -> typed Präteritum + Perfekt
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Mapping

import numpy as np
import pandas as pd

from . import config

QTYPE_LABELS = {
    "choose_en": "German → English", "choose_de": "English → German", "type_de": "Type the German",
    "article": "der / die / das", "forms": "Verb forms",
}
MODES = {
    "smart": "Smart review",
    "article": "Article trainer",
    "type": "Type it",
    "forms": "Verb forms",
    "weak": "Weak spots",
}
MODE_HELP = {
    "smart": "Due reviews first, then new words, with harder question types as a word is learned.",
    "article": "Drill der / die / das on nouns.",
    "type": "Recall the German word from the English prompt and type it.",
    "forms": "Type the Präteritum and Perfekt of verbs.",
    "weak": "Words you miss most often.",
}


@dataclass(frozen=True)
class Question:
    word_id: str
    word_class: str
    english: str
    german: str
    article: str
    plural: str
    past_tense: str
    perfect_tense: str
    qtype: str
    box: int
    prompt: str
    options: tuple[str, ...] = ()
    answer: str = ""
    retry: bool = False

    @property
    def direction(self) -> str:
        return {"choose_en": "de→en", "choose_de": "en→de", "type_de": "en→de",
                "article": "de→article", "forms": "de→forms"}[self.qtype]

    @property
    def german_display(self) -> str:
        return german_display(self.article, self.german)


def german_display(article: str, german: str) -> str:
    return f"{article} {german}" if article else german


def info_line(q: Question) -> str:
    """What to learn from this word, shown after every answer."""
    if q.word_class == "noun":
        plural = f"die {q.plural}" if q.plural else "no plural"
        return f"{q.german_display} · plural: {plural}"
    if q.word_class == "verb" and q.past_tense:
        return f"{q.german} · {q.past_tense} · {q.perfect_tense}"
    return q.german_display


def available_qtypes(word: Mapping) -> list[str]:
    types = ["choose_en", "choose_de", "type_de"]
    if word["word_class"] == "noun" and word["article"] in config.ARTICLES:
        types.append("article")
    if word["word_class"] == "verb" and word["past_tense"] and word["perfect_tense"]:
        types.append("forms")
    return types


# ----------------------------------------------------------------------------- building
def _distractors(word: Mapping, pool: pd.DataFrame, column: str, rng: random.Random, k: int) -> list[str]:
    """k texts from other words, preferring the same word class, never equal to the word itself."""
    same = pool[(pool["word_class"] == word["word_class"]) & (pool["word_id"] != word["word_id"])]
    other = pool[(pool["word_class"] != word["word_class"]) & (pool["word_id"] != word["word_id"])]
    out: list[str] = []
    for frame in (same, other):
        values = [v for v in frame[column].tolist() if v]
        rng.shuffle(values)
        for value in values:
            if value not in out:
                out.append(value)
            if len(out) >= k:
                return out
    return out


def build_question(word: Mapping, qtype: str, pool: pd.DataFrame, rng: random.Random, box: int = 0) -> Question:
    base = dict(
        word_id=word["word_id"], word_class=word["word_class"], english=word["english"], german=word["german"],
        article=word["article"], plural=word["plural"], past_tense=word["past_tense"],
        perfect_tense=word["perfect_tense"], qtype=qtype, box=box,
    )
    display = german_display(word["article"], word["german"])
    if qtype == "choose_en":
        wrong = _distractors(word, pool, "english", rng, 3)
        options = wrong + [word["english"]]
        rng.shuffle(options)
        return Question(prompt=display, options=tuple(options), answer=word["english"], **base)
    if qtype == "choose_de":
        wrong: list[str] = []
        if word["article"] in config.ARTICLES:
            wrong_article = rng.choice([a for a in config.ARTICLES if a != word["article"]])
            wrong.append(german_display(wrong_article, word["german"]))
        pool_display = pool.assign(_d=[german_display(a, g) for a, g in zip(pool["article"], pool["german"])])
        for text in _distractors(word, pool_display, "_d", rng, 3):
            if len(wrong) < 3 and text != display and text not in wrong:
                wrong.append(text)
        options = wrong + [display]
        rng.shuffle(options)
        return Question(prompt=word["english"], options=tuple(options), answer=display, **base)
    if qtype == "article":
        return Question(prompt=word["german"], options=config.ARTICLES, answer=word["article"], **base)
    if qtype == "forms":
        return Question(prompt=word["german"], answer=f'{word["past_tense"]} | {word["perfect_tense"]}', **base)
    return Question(prompt=word["english"], answer=display, **base)       # type_de


def retry_of(q: Question) -> Question:
    return replace(q, retry=True)


# ----------------------------------------------------------------------------- planning
_WEIGHTS = {
    0: {"choose_en": 3, "choose_de": 3, "article": 1},
    1: {"choose_en": 3, "choose_de": 3, "article": 1},
    2: {"choose_de": 3, "choose_en": 1, "article": 2, "type_de": 1, "forms": 1},
    3: {"type_de": 3, "article": 2, "choose_de": 1, "forms": 2},
    4: {"type_de": 4, "forms": 3, "article": 2},
    5: {"type_de": 4, "forms": 3, "article": 2},
}


def pick_qtype(word: Mapping, box: int, rng: random.Random) -> str:
    """Harder question types as a word moves up the boxes."""
    available = set(available_qtypes(word))
    weights = {t: w for t, w in _WEIGHTS[min(max(box, 0), 5)].items() if t in available}
    if not weights:
        return "choose_en"
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def _with_state(words: pd.DataFrame, states: pd.DataFrame) -> pd.DataFrame:
    df = words.copy()
    aligned = states.reindex(df["word_id"]) if len(states) else None
    df["box"] = aligned["box"].fillna(0).astype(int).to_numpy() if aligned is not None else 0
    df["attempts"] = aligned["attempts"].fillna(0).astype(int).to_numpy() if aligned is not None else 0
    df["wrong"] = aligned["wrong"].fillna(0).astype(int).to_numpy() if aligned is not None else 0
    df["due"] = aligned["due"].to_numpy() if aligned is not None else pd.NaT
    return df


def select_words(words: pd.DataFrame, states: pd.DataFrame, n: int, now: datetime,
                 rng: random.Random, new_ratio: float = config.NEW_WORD_RATIO) -> pd.DataFrame:
    """Due words (most overdue first), then new words in frequency order, then not-yet-due words."""
    df = _with_state(words, states)
    now_ts = pd.Timestamp(now)
    seen = df[df["attempts"] > 0]
    new = df[df["attempts"] == 0]
    # Most frequent first, but advance through every word class in proportion to its size, so the
    # first session is not made only of function words ("und", "zu", "von").
    by_class = new.groupby("word_class")["zipf"]
    new = new.assign(_progress=by_class.rank(ascending=False, method="first") / by_class.transform("size"))
    new = new.sort_values(["_progress", "zipf"], ascending=[True, False], na_position="last", kind="stable")
    due = seen[seen["due"] <= now_ts].sort_values("due", kind="stable")
    later = seen[seen["due"] > now_ts].sort_values("due", kind="stable")

    if len(due) >= n:                       # backlog: finish reviews before piling on new words
        new_ratio = min(new_ratio, config.BACKLOG_NEW_WORD_RATIO)
    new_target = min(len(new), math.ceil(n * new_ratio))
    parts = [due.head(max(n - new_target, 0))]
    remaining = n - len(parts[0])
    parts.append(new.head(remaining))
    remaining -= len(parts[1])
    if remaining > 0:
        parts.append(later.head(remaining))
    chosen = pd.concat(parts)
    order = list(range(len(chosen)))
    rng.shuffle(order)
    return chosen.iloc[order]


def select_weak(words: pd.DataFrame, states: pd.DataFrame, n: int, rng: random.Random) -> pd.DataFrame:
    df = _with_state(words, states)
    df = df[(df["attempts"] >= 2) & (df["wrong"] > 0)]
    df = df.assign(_err=(df["wrong"] + 1) / (df["attempts"] + 2)).sort_values("_err", ascending=False, kind="stable")
    chosen = df.head(n)
    order = list(range(len(chosen)))
    rng.shuffle(order)
    return chosen.iloc[order]


def plan_session(words: pd.DataFrame, states: pd.DataFrame, mode: str, n: int, now: datetime,
                 rng: random.Random, classes: list[str] | None = None,
                 word_ids: list[str] | None = None) -> list[Question]:
    """The questions for one session. `words` is the active word list."""
    pool = words
    if classes:
        pool = pool[pool["word_class"].isin(classes)]
    if word_ids is not None:
        pool = pool[pool["word_id"].isin(word_ids)]
    if mode == "article":
        pool = pool[(pool["word_class"] == "noun") & pool["article"].isin(config.ARTICLES)]
    elif mode == "forms":
        pool = pool[(pool["word_class"] == "verb") & (pool["past_tense"] != "") & (pool["perfect_tense"] != "")]
    if pool.empty:
        return []
    n = min(n, len(pool))
    chosen = select_weak(pool, states, n, rng) if mode == "weak" else select_words(pool, states, n, now, rng)

    questions = []
    for word in chosen.to_dict("records"):
        box = int(word["box"])
        qtype = {"article": "article", "forms": "forms", "type": "type_de"}.get(mode) or pick_qtype(word, box, rng)
        questions.append(build_question(word, qtype, words, rng, box))
    return questions
