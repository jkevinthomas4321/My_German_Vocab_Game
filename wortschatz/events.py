"""The event log: one row per answered question. It is the single source of truth.

Spaced-repetition state, XP, streaks, badges and every chart are *derived* from this table, so
nothing can drift out of sync and there is no second file to corrupt.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd

from . import config

EVENT_COLUMNS = [
    "ts", "session_id", "word_id", "word_class", "english", "german", "qtype", "direction",
    "correct", "response_ms", "given", "expected", "article_expected", "article_given", "retry",
]
_TEXT = ["session_id", "word_id", "word_class", "english", "german", "qtype", "direction",
         "given", "expected", "article_expected", "article_given"]
_INT = ["correct", "response_ms", "retry"]
TS_FORMAT = "%Y-%m-%d %H:%M:%S"


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def empty_events() -> pd.DataFrame:
    frame = pd.DataFrame({c: pd.Series(dtype="object") for c in EVENT_COLUMNS})
    frame["ts"] = pd.to_datetime(frame["ts"])
    for col in _INT:
        frame[col] = frame[col].astype("int64")
    return frame


def _typed(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["ts"] = pd.to_datetime(frame["ts"], errors="coerce")
    for col in _INT:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in _TEXT:
        frame[col] = frame[col].fillna("").astype(str)
    # Rows damaged by hand-editing are dropped instead of crashing every page.
    frame = frame.dropna(subset=["ts", *_INT])
    frame = frame[frame["correct"].isin([0, 1]) & (frame["response_ms"] >= 0)]
    frame = frame.astype({c: "int64" for c in _INT})
    return frame.sort_values("ts", kind="stable").reset_index(drop=True)[EVENT_COLUMNS]


def load_events(profile: str = config.PROFILE_ME, path: Path | None = None) -> pd.DataFrame:
    path = Path(path or config.events_path(profile))
    if not path.exists() or path.stat().st_size == 0:
        return empty_events()
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, on_bad_lines="skip", encoding="utf-8")
    for col in EVENT_COLUMNS:
        if col not in raw.columns:
            raw[col] = "0" if col == "retry" else ""
    return _typed(raw)


def append_events(rows: Iterable[Mapping], profile: str = config.PROFILE_ME, path: Path | None = None) -> None:
    rows = list(rows)
    if not rows:
        return
    path = Path(path or config.events_path(profile))
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows).reindex(columns=EVENT_COLUMNS)
    if pd.api.types.is_datetime64_any_dtype(frame["ts"]):
        frame["ts"] = frame["ts"].dt.strftime(TS_FORMAT)
    write_header = not path.exists() or path.stat().st_size == 0
    frame.to_csv(path, mode="a", header=write_header, index=False, encoding="utf-8")


def write_events(frame: pd.DataFrame, profile: str, path: Path | None = None) -> None:
    """Replace a profile's log (used by the demo generator)."""
    path = Path(path or config.events_path(profile))
    path.parent.mkdir(parents=True, exist_ok=True)
    out = frame.reindex(columns=EVENT_COLUMNS).copy()
    out["ts"] = pd.to_datetime(out["ts"]).dt.strftime(TS_FORMAT)
    tmp = path.with_suffix(".tmp")
    out.to_csv(tmp, index=False, encoding="utf-8")
    tmp.replace(path)


def clear_events(profile: str) -> None:
    path = config.events_path(profile)
    if path.exists():
        path.unlink()


def graded(ev: pd.DataFrame) -> pd.DataFrame:
    """Events that count towards progress: answers that are not an immediate retry after a miss."""
    return ev[ev["retry"] == 0]
