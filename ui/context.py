"""Per-run application context: which profile and word list are active, and the derived data frames."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from wortschatz import analytics, config, events, gamification, simulate, srs, wordlist

DEMO_REFRESH_AFTER = pd.Timedelta(hours=36)


def init() -> None:
    """Defaults that every view needs, whether it runs inside app.py or on its own (tests)."""
    if "profile" not in st.session_state:
        wanted = st.query_params.get("profile")             # e.g. http://localhost:8501/?profile=demo
        st.session_state["profile"] = wanted if wanted in config.PROFILE_LABELS else config.PROFILE_ME
    st.session_state.setdefault("wordlist", config.DEFAULT_WORDLIST)
    st.session_state.setdefault("daily_goal", config.DEFAULT_DAILY_GOAL)


@st.cache_data(show_spinner=False)
def _read_list(path: str, modified: float):
    return wordlist.load_wordlist(Path(path))


def load_list(path: Path):
    return _read_list(str(path), Path(path).stat().st_mtime)


def catalog() -> dict[str, Path]:
    return wordlist.available_wordlists()


def active_list_name() -> str | None:
    names = catalog()
    chosen = st.session_state.get("wordlist")
    if chosen in names:
        return chosen
    if config.DEFAULT_WORDLIST in names:
        return config.DEFAULT_WORDLIST
    return next(iter(names), None)


def all_words() -> pd.DataFrame:
    """Every known word across all lists, for joining frequency onto the event log."""
    frames = [load_list(path)[0] for path in catalog().values()]
    if not frames:
        return wordlist.empty_words()
    return pd.concat(frames, ignore_index=True).drop_duplicates("word_id")


def ensure_demo(now: datetime | None = None, force: bool = False) -> None:
    """Create (or refresh, when stale) the synthetic demo profile."""
    now = now or datetime.now()
    existing = events.load_events(config.PROFILE_DEMO)
    fresh = len(existing) and (pd.Timestamp(now) - existing["ts"].max()) < DEMO_REFRESH_AFTER
    if fresh and not force:
        return
    core = catalog().get(config.DEFAULT_WORDLIST)
    words = load_list(core)[0] if core else all_words()
    events.write_events(simulate.simulate_history(words, days=30, seed=2026, now=now), config.PROFILE_DEMO)


@dataclass
class Snapshot:
    profile: str
    now: datetime
    list_name: str | None
    words: pd.DataFrame          # the active word list
    catalog_words: pd.DataFrame  # union of all lists
    events: pd.DataFrame
    data: pd.DataFrame           # analytics.prepare(events)
    states: pd.DataFrame         # srs.replay(events)

    @property
    def is_demo(self) -> bool:
        return self.profile == config.PROFILE_DEMO

    @property
    def xp(self) -> int:
        return gamification.xp_total(self.data)

    @property
    def level(self) -> gamification.Level:
        return gamification.level_for(self.xp)


def snapshot() -> Snapshot:
    init()
    profile = st.session_state["profile"]
    now = datetime.now()
    if profile == config.PROFILE_DEMO:
        ensure_demo(now)
    name = active_list_name()
    words = load_list(catalog()[name])[0] if name else wordlist.empty_words()
    catalog_words = all_words()
    ev = events.load_events(profile)
    return Snapshot(profile, now, name, words, catalog_words, ev, analytics.prepare(ev, catalog_words), srs.replay(ev))


def list_label(name: str) -> str:
    return name.replace("_", " ").title()
