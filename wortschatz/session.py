"""Choosing words, studying them as cards, and running a test.

A test asks every chosen word once per direction (German -> English, English -> German). A word is
finished when all of its questions are answered; at that moment it passes (every answer right) or fails,
the rules in `progress.py` move it, and the files are saved, so quitting half way loses nothing.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Mapping, Sequence

import pandas as pd

from . import answers, config
from .progress import Progress, Transition
from .storage import Store

NEW_ORDERS = {"frequency": "Most common first", "sheet": "Order of the sheet", "random": "Random"}
DIARY_ORDERS = {"stale": "Longest since last test", "random": "Random", "newest": "Newest first"}


# ----------------------------------------------------------------------------- choosing words
def new_words(words: pd.DataFrame, progress: Progress) -> pd.DataFrame:
    """Words of the loaded sheet the learner has not been tested on yet."""
    return words[~words["word_id"].isin(progress.ids())]


def class_counts(frame: pd.DataFrame) -> dict[str, int]:
    counts = frame["word_class"].value_counts()
    order = [c for c in config.WORD_CLASSES if c in counts.index] + [c for c in counts.index if c not in config.WORD_CLASSES]
    return {c: int(counts[c]) for c in order}


def _of_class(frame: pd.DataFrame, word_class: str | None) -> pd.DataFrame:
    return frame if not word_class or word_class == "all" else frame[frame["word_class"] == word_class]


def pick_new_words(words: pd.DataFrame, progress: Progress, word_class: str | None, count: int,
                   order: str = "frequency", rng: random.Random | None = None) -> list[dict]:
    pool = _of_class(new_words(words, progress), word_class)
    if order == "random":
        pool = pool.iloc[random_order(len(pool), rng)]
    elif order == "frequency" and pool["zipf"].notna().any():
        pool = pool.sort_values("zipf", ascending=False, na_position="last", kind="stable")
    return pool.head(count).to_dict("records")


def pick_second_chance(progress: Progress, count: int | None = None, word_class: str | None = None) -> list[dict]:
    """Second-chance words, those missed most often (then longest ago) first."""
    frame = _of_class(progress.frame(config.STATUS_SECOND), word_class)
    frame = frame.sort_values(["fails", "last_tested"], ascending=[False, True], kind="stable")
    return frame.head(count).to_dict("records") if count else frame.to_dict("records")


def pick_diary(progress: Progress, word_class: str | None, count: int, order: str = "stale",
               rng: random.Random | None = None) -> list[dict]:
    frame = _of_class(progress.frame(config.STATUS_DIARY), word_class)
    if order == "random":
        frame = frame.iloc[random_order(len(frame), rng)]
    elif order == "newest":
        frame = frame.sort_values("diary_since", ascending=False, kind="stable")
    else:                                               # stale: never revised first, then the longest ago
        frame = frame.sort_values("last_tested", ascending=True, kind="stable")
    return frame.head(count).to_dict("records")


def random_order(n: int, rng: random.Random | None) -> list[int]:
    order = list(range(n))
    (rng or random).shuffle(order)
    return order


# ----------------------------------------------------------------------------- studying cards
class CardDeck:
    """The words to study, one card at a time. `front` is which language is shown first."""

    def __init__(self, words: Sequence[Mapping], front: str = "de"):
        self.words = list(words)
        self.front = front
        self.index = 0

    @property
    def current(self) -> Mapping:
        return self.words[self.index]

    @property
    def last(self) -> bool:
        return self.index >= len(self.words) - 1

    def next(self) -> None:
        self.index = min(self.index + 1, len(self.words) - 1)

    def previous(self) -> None:
        self.index = max(self.index - 1, 0)


# ----------------------------------------------------------------------------- testing
@dataclass
class Item:
    word: dict
    direction: str


@dataclass
class Feedback:
    item: Item
    check: answers.AnswerCheck
    response_ms: int
    word_done: bool = False
    transition: Transition | None = None

    @property
    def correct(self) -> bool:
        return self.check.correct


def _interleave(items: list[Item], rng: random.Random | None) -> list[Item]:
    """Random order in which the same word is never asked twice in a row (while that is possible):
    always draw from the word with the most questions left, excluding the one just asked."""
    rng = rng or random
    pending: dict[str, list[Item]] = {}
    for item in items:
        pending.setdefault(item.word["word_id"], []).append(item)
    for group in pending.values():
        rng.shuffle(group)
    ordered: list[Item] = []
    last = None
    while pending:
        options = [w for w in pending if w != last] or list(pending)
        most = max(len(pending[w]) for w in options)
        word_id = rng.choice([w for w in options if len(pending[w]) == most])
        ordered.append(pending[word_id].pop())
        if not pending[word_id]:
            del pending[word_id]
        last = word_id
    return ordered


class TestRun:
    """One test over a list of words. `submit` grades an answer; `advance` moves to the next question."""

    __test__ = False      # not a pytest class

    def __init__(self, store: Store, words: Sequence[Mapping], directions: Sequence[str] = ("de_en", "en_de"),
                 session_id: str | None = None, rng: random.Random | None = None, shuffle: bool = True,
                 clock: Callable[[], datetime] = datetime.now):
        if not words:
            raise ValueError("A test needs at least one word.")
        if not directions or any(d not in config.DIRECTIONS for d in directions):
            raise ValueError(f"directions must be a non-empty subset of {list(config.DIRECTIONS)}")
        self.store = store
        self.words = [dict(w) for w in words]
        self.directions = list(directions)
        self.session_id = session_id or f"{int(time.time())}-{random.randrange(10**6):06d}"
        self.clock = clock
        self.phase = {w["word_id"]: _phase_for(store.progress.status(w["word_id"])) for w in self.words}
        items = [Item(w, d) for w in self.words for d in self.directions]
        if shuffle:
            items = _interleave(items, rng)
        self.items = items
        self.index = 0
        self.log: list[Feedback] = []
        self.outcomes: dict[str, Transition] = {}
        self._answers: dict[str, list[bool]] = {}
        self.feedback: Feedback | None = None       # set between submit() and advance()
        self._shown = time.monotonic()

    # ------------------------------------------------------------------ state
    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def finished(self) -> bool:
        return self.index >= len(self.items)

    @property
    def current(self) -> Item | None:
        return None if self.finished else self.items[self.index]

    @property
    def done_words(self) -> int:
        return len(self.outcomes)

    # ------------------------------------------------------------------ answering
    def submit(self, response, response_ms: int | None = None) -> Feedback:
        if self.finished or self.feedback is not None:
            raise RuntimeError("Call advance() before answering the next question.")
        item = self.current
        ms = response_ms if response_ms is not None else int((time.monotonic() - self._shown) * 1000)
        check = answers.check(item.word, item.direction, response)
        feedback = Feedback(item, check, ms)
        word_id = item.word["word_id"]
        self._answers.setdefault(word_id, []).append(check.correct)
        now = self.clock().replace(microsecond=0)         # whole seconds: what is saved equals what is in memory
        self.store.append_attempts([{
            "ts": now, "session_id": self.session_id, "phase": self.phase[word_id], "word_id": word_id,
            "word_class": item.word["word_class"], "english": item.word["english"], "german": item.word["german"],
            "direction": item.direction, "correct": int(check.correct), "response_ms": ms,
            "given": check.given, "expected": check.expected}])
        if len(self._answers[word_id]) == len(self.directions):
            transition = self.store.progress.apply(item.word, all(self._answers[word_id]), now)
            self.store.save_progress()
            self.outcomes[word_id] = transition
            feedback.word_done, feedback.transition = True, transition
        self.log.append(feedback)
        self.feedback = feedback
        return feedback

    def skip(self) -> Feedback:
        """'I don't know': counts as a wrong answer."""
        item = self.current
        blank = ("", "", "") if item.direction == "en_de" and answers.has_forms(item.word) else ""
        return self.submit(blank)

    def advance(self) -> None:
        self.feedback = None
        self.index += 1
        self._shown = time.monotonic()

    # ------------------------------------------------------------------ results
    def results(self) -> dict:
        """What happened to each word, for the results screen."""
        passed, failed = [], []
        for word in self.words:
            outcome = self.outcomes.get(word["word_id"])
            if outcome is None:
                continue
            wrong = [f for f in self.log if f.item.word["word_id"] == word["word_id"] and not f.correct]
            (passed if outcome.passed else failed).append({"word": word, "transition": outcome, "wrong": wrong})
        return {"passed": passed, "failed": failed, "answered": len(self.log),
                "correct": sum(f.correct for f in self.log)}


def _phase_for(status: str | None) -> str:
    return {config.STATUS_SECOND: config.PHASE_RETEST, config.STATUS_DIARY: config.PHASE_DIARY}.get(status, config.PHASE_LEARN)
