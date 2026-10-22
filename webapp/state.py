"""The game's state while the app runs. It is a single-user, local app, so one shared object is enough."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from wortschatz import config, demo, points, session, stats, wordlist
from wortschatz.session import CardDeck, TestRun
from wortschatz.storage import Store

DEMO_REFRESH_AFTER = pd.Timedelta(hours=36)


@dataclass
class Run:
    """One round of play: study some words as cards, take the test, see the results."""
    mode: str                          # config.PHASE_LEARN | PHASE_RETEST | PHASE_DIARY
    words: list[dict]
    directions: list[str]
    stage: str                         # "cards" | "test" | "results"
    deck: CardDeck | None = None
    test: TestRun | None = None
    flipped: bool = False
    front: str = "de"                  # which language is on the front of the cards: "de" or "en"

    def begin_test(self) -> None:
        self.test = TestRun(state.store, self.words, self.directions)
        self.stage = "test"


class AppState:
    def __init__(self) -> None:
        self.profile = config.PROFILE_ME
        self.store = Store(self.profile)
        self.wordlist = config.DEFAULT_WORDLIST
        self.run: Run | None = None
        self.points_before = 0
        self._lists: dict[tuple[str, float], pd.DataFrame] = {}

    # ------------------------------------------------------------------ word lists
    def catalog(self) -> dict[str, Path]:
        return wordlist.available_wordlists()

    def list_name(self) -> str | None:
        names = self.catalog()
        if self.wordlist in names:
            return self.wordlist
        return config.DEFAULT_WORDLIST if config.DEFAULT_WORDLIST in names else next(iter(names), None)

    def load_list(self, name: str) -> tuple[pd.DataFrame, wordlist.ValidationReport]:
        return wordlist.load_wordlist(self.catalog()[name])

    def words_of(self, name: str) -> pd.DataFrame:
        """The cleaned words of one list (cached until the file changes)."""
        path = self.catalog()[name]
        key = (str(path), path.stat().st_mtime)
        if key not in self._lists:
            self._lists[key] = wordlist.load_wordlist(path)[0]
        return self._lists[key]

    def words(self) -> pd.DataFrame:
        name = self.list_name()
        return self.words_of(name) if name else wordlist.empty_words()

    def list_ids(self, name: str | None) -> set[str] | None:
        """word_ids of a list; None means 'no restriction' (all my words)."""
        return None if name is None else set(self.words_of(name)["word_id"])

    # ------------------------------------------------------------------ profiles
    @property
    def is_demo(self) -> bool:
        return self.profile == config.PROFILE_DEMO

    def switch_profile(self, profile: str) -> None:
        self.run = None
        self.profile = profile
        if profile == config.PROFILE_DEMO:
            self.ensure_demo()
        self.store = Store(profile)

    def ensure_demo(self, force: bool = False) -> None:
        """Create the synthetic demo profile, or refresh it when it has gone stale."""
        attempts = Store(config.PROFILE_DEMO).attempts()
        fresh = len(attempts) and (pd.Timestamp.now() - attempts["ts"].max()) < DEMO_REFRESH_AFTER
        if fresh and not force:
            return
        core = self.catalog().get(config.DEFAULT_WORDLIST)
        words = wordlist.load_wordlist(core)[0] if core else self.words()
        demo.generate(words, days=30, seed=2026, now=datetime.now())
        if self.is_demo:
            self.store = Store(config.PROFILE_DEMO)

    # ------------------------------------------------------------------ playing
    def start(self, mode: str, words: list[dict], directions: list[str], cards: bool) -> Run:
        self.run = Run(mode=mode, words=words, directions=list(directions), stage="cards" if cards else "test",
                       deck=CardDeck(words) if cards else None)
        self.points_before = self.total_points()
        if not cards:
            self.run.begin_test()
        return self.run

    def end_run(self) -> None:
        self.run = None

    # ------------------------------------------------------------------ numbers for the sidebar, the house and the pages
    def counts(self) -> dict[str, int]:
        progress = self.store.progress
        return {"diary": progress.count(config.STATUS_DIARY), "second": progress.count(config.STATUS_SECOND),
                "new": len(session.new_words(self.words(), progress))}

    def total_points(self) -> int:
        return points.total_points(stats.word_outcomes(self.store.attempts()))

    def level(self) -> points.Level:
        return points.level_for(self.total_points())

    def points_today(self) -> int:
        return points.points_on(stats.word_outcomes(self.store.attempts()), date.today())


state = AppState()
