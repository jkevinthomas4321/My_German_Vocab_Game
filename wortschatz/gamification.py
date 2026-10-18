"""XP, levels, daily goals and badges. All derived from the event log; nothing is stored."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from . import config
from .analytics import practice_streaks


def xp_total(d: pd.DataFrame) -> int:
    """`d` is the output of analytics.prepare (graded events with an `xp` column)."""
    return int(d["xp"].sum()) if len(d) else 0


@dataclass(frozen=True)
class Level:
    number: int
    title: str
    xp: int
    floor: int
    ceiling: int

    @property
    def progress(self) -> float:
        return (self.xp - self.floor) / (self.ceiling - self.floor)


def level_for(xp: int) -> Level:
    number = int(math.sqrt(max(xp, 0) / config.LEVEL_XP_STEP)) + 1
    title = config.LEVEL_TITLES[min(number - 1, len(config.LEVEL_TITLES) - 1)]
    return Level(number, title, xp, config.LEVEL_XP_STEP * (number - 1) ** 2, config.LEVEL_XP_STEP * number**2)


def answers_today(d: pd.DataFrame, today: date | None = None) -> int:
    if d.empty:
        return 0
    return int((d["day"].dt.date == (today or date.today())).sum())


@dataclass(frozen=True)
class Badge:
    key: str
    icon: str
    title: str
    description: str
    earned_on: pd.Timestamp | None

    @property
    def earned(self) -> bool:
        return self.earned_on is not None and not pd.isna(self.earned_on)


def _nth(series: pd.Series, n: int):
    """Timestamp of the n-th entry (1-based) or None."""
    return series.iloc[n - 1] if len(series) >= n else None


def _first_true(mask: pd.Series, when: pd.Series):
    hit = when[mask.fillna(False).to_numpy()]
    return hit.iloc[0] if len(hit) else None


def evaluate_badges(d: pd.DataFrame, states: pd.DataFrame) -> list[Badge]:
    ts = d["ts"] if len(d) else pd.Series(dtype="datetime64[ns]")
    right = d[d["correct"] == 1] if len(d) else d

    first = _nth(ts, 1)
    hundred = _nth(right["ts"], 100) if len(d) else None
    thousand = _nth(ts, 1000)

    streak7 = None
    if len(d):
        days = sorted(set(d["day"].dt.date))
        run = 0
        for previous, current in zip([None] + days[:-1], days):
            run = run + 1 if previous is not None and (current - previous).days == 1 else 1
            if run >= 7:
                streak7 = pd.Timestamp(current)
                break

    article_pro = fast = perfect = None
    if len(d):
        art = d[d["article_ok"].notna()]
        if len(art) >= 50:
            rolled = art["article_ok"].rolling(50).mean()
            article_pro = _first_true(rolled >= 0.85, art["ts"])
        if len(right) >= 30:
            median = right["response_s"].rolling(30).median()
            fast = _first_true(median <= 2.5, right["ts"])
        sessions = d.groupby("session_id").agg(n=("correct", "size"), ok=("correct", "mean"), at=("ts", "max"))
        flawless = sessions[(sessions["n"] >= 10) & (sessions["ok"] == 1.0)].sort_values("at")
        perfect = flawless["at"].iloc[0] if len(flawless) else None

    seen100 = _nth(states["first_seen"].sort_values(), 100) if len(states) else None
    master25 = _nth(states["mastered_at"].dropna().sort_values(), 25) if len(states) else None

    return [
        Badge("first", "🌱", "Erste Schritte", "Answer your first question.", first),
        Badge("seen100", "📚", "Hundert Wörter", "Meet 100 different words.", seen100),
        Badge("hundred", "💯", "Hundertschaft", "Give 100 correct answers.", hundred),
        Badge("thousand", "🏔️", "Tausendsassa", "Answer 1,000 questions.", thousand),
        Badge("streak7", "🔥", "Wochenstreak", "Practise 7 days in a row.", streak7),
        Badge("article", "🎯", "Artikel-Profi", "85% article accuracy over 50 answers.", article_pro),
        Badge("fast", "⚡", "Blitzschnell", "Median correct-answer time of 2.5 s or less over 30 answers.", fast),
        Badge("perfect", "✨", "Perfektionist", "A flawless session of 10 or more questions.", perfect),
        Badge("master25", "👑", "Wortmeister", "Master 25 words.", master25),
    ]
