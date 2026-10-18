"""Spaced repetition (Leitner boxes), computed by replaying the event log.

A word starts in box 0 (unseen). Every graded answer moves it: correct -> one box up (max 5),
wrong -> two boxes down (min 1). A word in box b is due again INTERVAL_DAYS[b] days after its last
answer. Because the state is a pure function of the log, it can be recomputed at any point in
time, which is also how the demo-data simulator uses the exact same scheduler as the real app.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from . import config
from .events import graded

STATE_COLUMNS = ["box", "attempts", "correct", "wrong", "lapses", "first_seen", "last_seen", "due", "mastered_at"]
STATUS_ORDER = ["Unseen", "Learning", "Reviewing", "Mastered"]


def next_box(box: int, correct: bool) -> int:
    if correct:
        return min(config.MAX_BOX, box + 1)
    return max(1, box - config.WRONG_BOX_DROP)


def status_of(box: int) -> str:
    if box <= 0:
        return "Unseen"
    if box <= 2:
        return "Learning"
    if box < config.MASTERED_BOX:
        return "Reviewing"
    return "Mastered"


def empty_states() -> pd.DataFrame:
    frame = pd.DataFrame({
        "box": pd.Series(dtype="int64"), "attempts": pd.Series(dtype="int64"),
        "correct": pd.Series(dtype="int64"), "wrong": pd.Series(dtype="int64"),
        "lapses": pd.Series(dtype="int64"),
        "first_seen": pd.Series(dtype="datetime64[ns]"), "last_seen": pd.Series(dtype="datetime64[ns]"),
        "due": pd.Series(dtype="datetime64[ns]"), "mastered_at": pd.Series(dtype="datetime64[ns]"),
    })
    frame.index.name = "word_id"
    return frame


def replay(events: pd.DataFrame) -> pd.DataFrame:
    """Per-word scheduling state, indexed by word_id."""
    ev = graded(events)
    if ev.empty:
        return empty_states()
    rows: dict[str, dict] = {}
    for word_id, ts, correct in ev.sort_values("ts", kind="stable")[["word_id", "ts", "correct"]].itertuples(index=False):
        s = rows.get(word_id)
        if s is None:
            s = rows[word_id] = {"box": 0, "attempts": 0, "correct": 0, "wrong": 0, "lapses": 0,
                                 "first_seen": ts, "last_seen": ts, "mastered_at": pd.NaT}
        new_box = next_box(s["box"], bool(correct))
        if not correct and s["box"] > 1:
            s["lapses"] += 1
        s["attempts"] += 1
        s["correct" if correct else "wrong"] += 1
        s["box"] = new_box
        s["last_seen"] = ts
        if new_box >= config.MASTERED_BOX and pd.isna(s["mastered_at"]):
            s["mastered_at"] = ts
    states = pd.DataFrame.from_dict(rows, orient="index")
    states.index.name = "word_id"
    states["due"] = states["last_seen"] + states["box"].map(config.INTERVAL_DAYS).map(lambda d: pd.Timedelta(days=d))
    for col in ("first_seen", "last_seen", "mastered_at"):
        states[col] = pd.to_datetime(states[col])
    return states[STATE_COLUMNS].astype({c: "int64" for c in ("box", "attempts", "correct", "wrong", "lapses")})


def due_ids(states: pd.DataFrame, now: datetime | pd.Timestamp) -> list[str]:
    """Seen words that are due for review, most overdue first."""
    if states.empty:
        return []
    due = states[states["due"] <= pd.Timestamp(now)]
    return list(due.sort_values("due").index)


def status_counts(states: pd.DataFrame, word_ids: list[str]) -> dict[str, int]:
    """How many of the given words are unseen / learning / reviewing / mastered."""
    boxes = states["box"].reindex(word_ids).fillna(0).astype(int) if len(states) else pd.Series(0, index=word_ids)
    counts = {label: 0 for label in STATUS_ORDER}
    for box in boxes:
        counts[status_of(int(box))] += 1
    return counts
