"""Points and levels.

Points reward words you have *proven*, and nothing is ever taken away. They are calculated from the
attempts log (see stats.word_outcomes), so they can never disagree with what really happened:

    pass a new word on its first test ........ 10 points
    rescue a second-chance word (re-test) ....  6 points
    pass a diary revision ....................  4 points
    miss a word ..............................  0 points (and no penalty)

Levels need more points the higher you climb: level L starts at LEVEL_STEP * (L - 1)^2 points.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import pandas as pd

from . import config

POINTS_PER_PASS = {config.PHASE_LEARN: 10, config.PHASE_RETEST: 6, config.PHASE_DIARY: 4}
LEVEL_STEP = 60
LEVEL_TITLES = ["Anfänger", "Entdecker", "Wortsammler", "Sprachschüler", "Wortschmied",
                "Satzbauer", "Redner", "Kenner", "Meister", "Wortzauberer"]


def word_points(phase: str, passed: bool) -> int:
    return POINTS_PER_PASS.get(phase, 0) if passed else 0


def round_points(phase: str, passed_words: int) -> int:
    """Points for a finished round in which `passed_words` words passed."""
    return word_points(phase, True) * passed_words


def total_points(outcomes: pd.DataFrame) -> int:
    """Points of all word outcomes (the table from stats.word_outcomes)."""
    if outcomes.empty:
        return 0
    per_word = outcomes["phase"].map(POINTS_PER_PASS).fillna(0).astype(int) * outcomes["passed"].astype(int)
    return int(per_word.sum())


def points_on(outcomes: pd.DataFrame, day: date) -> int:
    if outcomes.empty:
        return 0
    return total_points(outcomes[outcomes["day"].dt.date == day])


@dataclass(frozen=True)
class Level:
    number: int
    title: str
    points: int
    floor: int          # points at which this level starts
    ceiling: int        # points at which the next level starts

    @property
    def progress(self) -> float:
        return (self.points - self.floor) / (self.ceiling - self.floor)

    @property
    def to_next(self) -> int:
        return self.ceiling - self.points


def level_for(points: int) -> Level:
    number = int(math.sqrt(max(points, 0) / LEVEL_STEP)) + 1
    title = LEVEL_TITLES[min(number - 1, len(LEVEL_TITLES) - 1)]
    return Level(number, title, max(points, 0), LEVEL_STEP * (number - 1) ** 2, LEVEL_STEP * number ** 2)


def level_table(levels: int = 6) -> list[Level]:
    """The first few levels with the points they start at (for the guide)."""
    return [level_for(LEVEL_STEP * (n - 1) ** 2) for n in range(1, levels + 1)]
