"""A synthetic learner, used to generate the demo profile.

Anyone who clones the repo should be able to open the analytics dashboard immediately, without
first practising for weeks. The simulator therefore produces a realistic month of practice by
running the *real* application logic (question planner, grader, Leitner scheduler) against a
simple memory model:

  * recall probability decays exponentially with days since the last review:  R = exp(-t / S)
  * memory stability S grows after a success and shrinks after a miss (the spacing effect)
  * harder words (rarer, longer, verbs) start with lower stability
  * multiple choice is easier than typing (guessing floor); article accuracy depends on how
    regular the noun's ending is and improves with practice
  * response times are log-normal, slower for new/unsure words and faster with practice

It is seeded, so the demo is reproducible. It is clearly labelled as synthetic everywhere in the UI.
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

import pandas as pd

from . import config, events, grading, questions, srs
from .german import suffix_group

_CLASS_DIFFICULTY = {"noun": 0.0, "adjective": -0.1, "adverb": 0.1, "verb": 0.35,
                     "preposition": 0.3, "conjunction": 0.1, "interjection": -0.3, "other": 0.0}
_REGULAR_SUFFIXES = {"-ung", "-heit / -keit", "-schaft", "-ion", "-tät", "-chen / -lein", "-ismus", "-ling"}
_MEDIAN_SECONDS = {"choose_en": 3.4, "choose_de": 3.8, "article": 2.4, "type_de": 7.5, "forms": 12.0}
_MODE_WEIGHTS = {"smart": 0.6, "article": 0.16, "type": 0.1, "forms": 0.07, "weak": 0.07}
_START_HOURS = [7, 8, 9, 12, 13, 18, 19, 20, 21, 22]


class _Learner:
    """Hidden state of the simulated learner."""

    def __init__(self, words: pd.DataFrame, rng: random.Random, start: datetime):
        self.rng = rng
        zipf = words["zipf"].fillna(4.5)
        self.difficulty = {}
        self.stability: dict[str, float] = {}
        self.last_review: dict[str, datetime] = {}
        for row, z in zip(words.itertuples(index=False), zipf):
            d = _CLASS_DIFFICULTY.get(row.word_class, 0.0) - 0.45 * (z - 4.9) + 0.02 * len(row.german)
            self.difficulty[row.word_id] = d + rng.gauss(0, 0.35)
            # Prior knowledge: a learner already half-knows many very frequent words.
            p_known = 0.8 / (1 + math.exp(-1.6 * (z - 5.3)))
            if rng.random() < p_known:
                self.stability[row.word_id] = 22.0 * math.exp(-0.5 * self.difficulty[row.word_id])
                self.last_review[row.word_id] = start - timedelta(days=rng.uniform(3, 20))
        self.article_skill = 0.0                 # grows with every article question answered
        self.study_skill = 1.0                   # learning-to-learn: memory gets slightly stickier over the month

    def recall(self, word_id: str, now: datetime) -> float:
        if word_id not in self.stability:
            return 0.0
        days = (now - self.last_review[word_id]).total_seconds() / 86400
        return math.exp(-max(days, 0.0) / self.stability[word_id])

    def success_probability(self, q: questions.Question, now: datetime) -> float:
        r = self.recall(q.word_id, now)
        if q.qtype in ("choose_en", "choose_de"):
            floor = 1 / max(len(q.options), 2)
            p = floor + (1 - floor) * r
        elif q.qtype == "article":
            regular = suffix_group(q.german) in _REGULAR_SUFFIXES
            skill = min(1.0, self.article_skill / 150)
            known = 0.30 + 0.55 * skill + (0.12 if regular else -0.05) * skill
            p = 1 / 3 + (1 - 1 / 3) * min(0.97, max(0.0, known)) * (0.6 + 0.4 * r)
        elif q.qtype == "type_de":
            p = 0.93 * r
        else:
            p = 0.88 * r
        return max(0.01, min(0.99, p))

    def update(self, q: questions.Question, correct: bool, now: datetime) -> None:
        ease = math.exp(-0.5 * self.difficulty[q.word_id])
        if q.word_id not in self.stability:
            self.stability[q.word_id] = 6.0 * ease * (1.3 if correct else 1.0)
        elif correct:
            self.stability[q.word_id] *= self.rng.uniform(1.6, 2.4) * min(1.25, max(0.8, ease ** 0.3)) * self.study_skill
        else:
            self.stability[q.word_id] = max(0.25, self.stability[q.word_id] * 0.5)
        self.last_review[q.word_id] = now
        if q.qtype == "article":
            self.article_skill += 1.0

    def response_ms(self, q: questions.Question, correct: bool, recall: float, attempts: int) -> int:
        median = _MEDIAN_SECONDS[q.qtype] * (0.55 + 0.45 * (1.0 - recall) + 0.3)
        median *= max(0.62, 0.985 ** attempts)
        if not correct:
            median *= 1.35
        seconds = self.rng.lognormvariate(math.log(median), 0.38)
        return int(max(900, min(seconds * 1000, 55000)))


def _wrong_response(q: questions.Question, rng: random.Random):
    """A plausible wrong answer for question q."""
    if q.qtype in ("choose_en", "choose_de"):
        return rng.choice([o for o in q.options if o != q.answer])
    if q.qtype == "article":
        weights = {"der": {"die": 0.5, "das": 0.5}, "die": {"der": 0.6, "das": 0.4}, "das": {"der": 0.55, "die": 0.45}}[q.article]
        return rng.choices(list(weights), weights=list(weights.values()))[0]
    if q.qtype == "forms":
        return q.past_tense[:-1], q.perfect_tense
    if q.article and rng.random() < 0.4:
        return f"{rng.choice([a for a in config.ARTICLES if a != q.article])} {q.german}"
    return q.german[:-1] if len(q.german) > 3 else q.german + "e"


def _correct_response(q: questions.Question):
    if q.qtype in ("choose_en", "choose_de"):
        return q.answer
    if q.qtype == "article":
        return q.article
    if q.qtype == "forms":
        return q.past_tense, q.perfect_tense
    return q.answer


def _choose_mode(rng: random.Random, has_history: bool) -> str:
    modes, weights = zip(*_MODE_WEIGHTS.items())
    mode = rng.choices(modes, weights=weights)[0]
    return "smart" if mode == "weak" and not has_history else mode


def simulate_history(words: pd.DataFrame, days: int = 30, seed: int = 2026,
                     now: datetime | None = None) -> pd.DataFrame:
    """A month of practice ending at `now`. Returns an event log (see events.EVENT_COLUMNS)."""
    rng = random.Random(seed)
    now = (now or datetime.now()).replace(microsecond=0)
    first_day = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0)
    learner = _Learner(words, rng, first_day)
    rows: list[dict] = []
    attempts: dict[str, int] = {}

    break_start, break_len = rng.randint(7, 13), 4          # a short pause to make the streak chart interesting
    for offset in range(days):
        day = first_day + timedelta(days=offset)
        from_end = days - 1 - offset
        weekend = day.weekday() >= 5
        if break_start <= offset < break_start + break_len and from_end > 6:
            continue
        practice_probability = 0.97 if from_end <= 5 else (0.66 if weekend else 0.84)
        if rng.random() > practice_probability:
            continue
        learner.study_skill = 1.0 + 0.012 * offset
        for _ in range(1 if rng.random() < 0.6 else 2):
            start = day.replace(hour=rng.choice(_START_HOURS), minute=rng.randint(0, 59), second=rng.randint(0, 59))
            if start >= now - timedelta(minutes=20):
                continue
            states = srs.replay(pd.DataFrame(rows, columns=events.EVENT_COLUMNS).pipe(_as_events)) if rows else srs.empty_states()
            n = rng.randint(14, 20) + min(10, offset // 3)
            mode = _choose_mode(rng, has_history=len(states) > 5)
            plan = questions.plan_session(words, states, mode, n, start, rng)
            session_id = f"demo{len(rows):05d}"
            clock = start
            for q in plan:
                p = learner.success_probability(q, clock)
                recall = learner.recall(q.word_id, clock)
                correct = rng.random() < p
                response = _correct_response(q) if correct else _wrong_response(q, rng)
                grade = grading.grade(q, response)
                ms = learner.response_ms(q, grade.correct, recall, attempts.get(q.word_id, 0))
                rows.append(grading.to_event(q, grade, clock, session_id, ms))
                learner.update(q, grade.correct, clock)
                attempts[q.word_id] = attempts.get(q.word_id, 0) + 1
                clock += timedelta(milliseconds=ms + rng.randint(1200, 2600))
    return _as_events(pd.DataFrame(rows, columns=events.EVENT_COLUMNS)) if rows else events.empty_events()


def _as_events(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["ts"] = pd.to_datetime(out["ts"])
    for col in ("correct", "response_ms", "retry"):
        out[col] = out[col].astype("int64")
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
