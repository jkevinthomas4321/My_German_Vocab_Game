"""A simulated learner, used to fill the demo profile.

Anyone who downloads the game can open the Stats page straight away. The simulated learner plays the
*real* game (learn words, take the test, work through the second-chance list, revise the diary) through
the same engine the app uses, so the demo data follows exactly the rules of the game. Its memory is a
simple model: harder words (rarer, longer, verbs) are learned less reliably, a word that is revised often
is remembered longer, and a diary word is forgotten with probability growing with the days since it was
last tested. It is seeded, so the demo is reproducible, and it is labelled as synthetic in the UI.
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

import pandas as pd

from . import config, session
from .storage import Store

_CLASS_PLAN = [("noun", 0.5), ("verb", 0.3), ("adjective", 0.2)]
_CLASS_DIFFICULTY = {"noun": 0.0, "adjective": -0.1, "adverb": 0.1, "verb": 0.35, "preposition": 0.3}


class _Learner:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.difficulty: dict[str, float] = {}
        self.stability: dict[str, float] = {}        # days a diary word is remembered
        self.last_test: dict[str, datetime] = {}

    def hardness(self, word: dict) -> float:
        key = word["word_id"]
        if key not in self.difficulty:
            zipf = word.get("zipf")
            zipf = 4.8 if zipf is None or pd.isna(zipf) else zipf
            self.difficulty[key] = (_CLASS_DIFFICULTY.get(word["word_class"], 0.0) - 0.4 * (zipf - 4.9)
                                    + 0.03 * len(word["german"]) + self.rng.gauss(0, 0.4))
        return self.difficulty[key]

    def p_word(self, word: dict, phase: str, now: datetime) -> float:
        """Chance of knowing the word right now."""
        if phase == config.PHASE_DIARY:
            days = max((now - self.last_test.get(word["word_id"], now)).total_seconds() / 86400, 0.0)
            return min(0.97, math.exp(-days / self.stability.get(word["word_id"], 8.0)))
        p = 0.90 - 0.13 * self.hardness(word)
        return min(0.95, max(0.3, p + (0.12 if phase == config.PHASE_RETEST else 0.0)))

    def slip(self, word: dict, direction: str) -> float:
        """Chance of answering correctly *given* that the word is known: typing German is harder than English."""
        if direction == "de_en":
            return 0.97
        return 0.82 if word["word_class"] == "verb" else 0.93

    def update(self, word: dict, passed: bool, now: datetime) -> None:
        key = word["word_id"]
        ease = math.exp(-0.5 * self.hardness(word))
        if passed:
            self.stability[key] = self.stability.get(key, 8.0 * ease) * self.rng.uniform(1.8, 2.6) + 1.0
        else:
            self.stability[key] = 3.0 * ease
        self.last_test[key] = now

    def response_ms(self, item: session.Item) -> int:
        median = 4.5 if item.direction == "de_en" else (13.0 if item.word["word_class"] == "verb" else 6.5)
        return int(max(900, min(self.rng.lognormvariate(math.log(median), 0.35) * 1000, 55000)))


def _response(item: session.Item, right: bool):
    word = item.word
    if item.direction == "de_en":
        return word["english"].split("/")[0].split("(")[0].strip() if right else "?"
    if word["word_class"] == "verb" and word["past_tense"] and word["perfect_tense"]:
        return (word["german"], word["past_tense"], word["perfect_tense"]) if right else (word["german"], word["past_tense"], "")
    return f'{word["article"]} {word["german"]}'.strip() if right else "?"


def _play(store: Store, words: list[dict], phase: str, learner: _Learner, rng: random.Random, start: datetime) -> None:
    clock = [start]
    run = session.TestRun(store, words, rng=rng, clock=lambda: clock[0], session_id=f"demo-{start:%Y%m%d%H%M}-{phase}")
    knows: dict[str, bool] = {}                      # decided once per word and test: it is known or it is not
    while not run.finished:
        item = run.current
        word_id = item.word["word_id"]
        if word_id not in knows:
            knows[word_id] = rng.random() < learner.p_word(item.word, run.phase[word_id], clock[0])
        right = rng.random() < (learner.slip(item.word, item.direction) if knows[word_id] else 0.05)
        ms = learner.response_ms(item)
        clock[0] += timedelta(milliseconds=ms)
        feedback = run.submit(_response(item, right), response_ms=ms)
        if feedback.word_done:
            learner.update(item.word, feedback.transition.passed, clock[0])
        run.advance()
        clock[0] += timedelta(seconds=rng.randint(1, 3))


def generate(words: pd.DataFrame, days: int = 30, seed: int = 2026, now: datetime | None = None) -> Store:
    """Replace the demo profile with `days` days of simulated play ending at `now`."""
    rng = random.Random(seed)
    now = (now or datetime.now()).replace(microsecond=0)
    store = Store(config.PROFILE_DEMO)
    store.reset()
    learner = _Learner(rng)
    first_day = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0)
    break_start = rng.randint(8, 13)
    for offset in range(days):
        day = first_day + timedelta(days=offset)
        from_end = days - 1 - offset
        if break_start <= offset < break_start + 3 and from_end > 6:
            continue                                                      # a short pause makes the streak chart interesting
        if rng.random() > (0.97 if from_end <= 5 else (0.62 if day.weekday() >= 5 else 0.85)):
            continue

        def at(hour_low: int, hour_high: int) -> datetime:
            return day.replace(hour=rng.randint(hour_low, hour_high), minute=rng.randint(0, 59), second=rng.randint(0, 59))

        start = at(7, 11)
        if start >= now - timedelta(minutes=30):
            continue
        word_class = rng.choices([c for c, _ in _CLASS_PLAN], weights=[w for _, w in _CLASS_PLAN])[0]
        fresh = session.pick_new_words(words, store.progress, word_class, rng.randint(7, 12), "frequency", rng)
        if fresh:
            _play(store, fresh, config.PHASE_LEARN, learner, rng, start)
        second = session.pick_second_chance(store.progress, rng.randint(8, 12))
        retest_start = at(17, 20)
        if second and from_end > 0 and retest_start < now - timedelta(minutes=30):
            _play(store, second, config.PHASE_RETEST, learner, rng, retest_start)
        revise_start = at(12, 14)
        if offset % 3 == 2 and store.progress.count(config.STATUS_DIARY) >= 8 and revise_start < now - timedelta(minutes=30):
            _play(store, session.pick_diary(store.progress, "all", rng.randint(10, 14), "stale"), config.PHASE_DIARY,
                  learner, rng, revise_start)
    return store
