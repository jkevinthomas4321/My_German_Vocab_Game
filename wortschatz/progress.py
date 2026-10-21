"""Where every word lives: the diary, the second-chance list, or neither (not learned yet).

The rules of the game are exactly these, and nothing else moves a word:

    not learned yet --pass the test--> DIARY
    not learned yet --fail the test--> SECOND CHANCE
    SECOND CHANCE   --pass the re-test--> DIARY
    SECOND CHANCE   --fail the re-test--> stays in SECOND CHANCE
    DIARY           --pass a revision test--> stays in the DIARY
    DIARY           --fail a revision test--> back to SECOND CHANCE

A word passes a test when *every* question about it was answered correctly.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

import pandas as pd

from . import config

TRACKING = ["status", "first_seen", "diary_since", "last_tested", "tests", "passes", "fails", "streak", "returns"]
PROGRESS_COLUMNS = config.WORD_COLUMNS + ["word_id"] + TRACKING
_TIME_COLUMNS = ["first_seen", "diary_since", "last_tested"]
_INT_COLUMNS = ["tests", "passes", "fails", "streak", "returns"]


@dataclass(frozen=True)
class Transition:
    before: str | None       # None = the word was not in the game yet
    after: str
    passed: bool

    @property
    def entered_diary(self) -> bool:
        return self.after == config.STATUS_DIARY and self.before != config.STATUS_DIARY

    @property
    def left_diary(self) -> bool:
        return self.before == config.STATUS_DIARY and self.after != config.STATUS_DIARY


class Progress:
    """All words the learner has been tested on, keyed by word_id."""

    def __init__(self, records: dict[str, dict] | None = None):
        self.records: dict[str, dict] = dict(records or {})

    # ------------------------------------------------------------------ queries
    def status(self, word_id: str) -> str | None:
        record = self.records.get(word_id)
        return record["status"] if record else None

    def ids(self, status: str | None = None) -> set[str]:
        return {i for i, r in self.records.items() if status is None or r["status"] == status}

    def count(self, status: str) -> int:
        return sum(r["status"] == status for r in self.records.values())

    def words(self, status: str) -> list[dict]:
        return [dict(r) for r in self.records.values() if r["status"] == status]

    # ------------------------------------------------------------------ the rules
    def apply(self, word: Mapping, passed: bool, when: datetime) -> Transition:
        """Record the result of a completed test of `word` and move it according to the rules."""
        word_id = word["word_id"]
        record = self.records.get(word_id)
        before = record["status"] if record else None
        if record is None:
            record = {c: word.get(c, "") for c in config.TEXT_COLUMNS}
            record["zipf"] = word.get("zipf", float("nan"))
            record.update(word_id=word_id, status=None, first_seen=when, diary_since=None, last_tested=None,
                          tests=0, passes=0, fails=0, streak=0, returns=0)
            self.records[word_id] = record

        record["tests"] += 1
        record["passes" if passed else "fails"] += 1
        record["last_tested"] = when
        if before == config.STATUS_DIARY:
            if passed:
                record["streak"] += 1
            else:
                record.update(status=config.STATUS_SECOND, streak=0, diary_since=None)
                record["returns"] += 1
        elif passed:                                    # a new word or a second-chance word
            record.update(status=config.STATUS_DIARY, diary_since=when, streak=1)
        else:
            record["status"] = config.STATUS_SECOND
        return Transition(before, record["status"], passed)

    def remove(self, word_id: str) -> bool:
        """Delete a word from the game entirely (it can be learned again later)."""
        return self.records.pop(word_id, None) is not None

    # ------------------------------------------------------------------ tables
    def frame(self, status: str | None = None) -> pd.DataFrame:
        rows = [r for r in self.records.values() if status is None or r["status"] == status]
        frame = pd.DataFrame(rows, columns=PROGRESS_COLUMNS)
        for column in _TIME_COLUMNS:
            frame[column] = pd.to_datetime(frame[column])
        for column in _INT_COLUMNS:
            frame[column] = frame[column].astype("int64")
        frame["zipf"] = pd.to_numeric(frame["zipf"], errors="coerce")
        return frame.reset_index(drop=True)

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> "Progress":
        records = {}
        for row in frame.to_dict("records"):
            for column in _TIME_COLUMNS:
                value = row.get(column)
                row[column] = None if value is None or pd.isna(value) else pd.Timestamp(value).to_pydatetime()
            for column in _INT_COLUMNS:
                row[column] = int(row[column]) if not pd.isna(row.get(column)) else 0
            records[row["word_id"]] = {c: row.get(c, "") for c in PROGRESS_COLUMNS}
        return cls(records)
