"""Saving and loading a profile: `progress.csv` (the diary and second-chance list) and `attempts.csv`
(one row per answered question, the source for all statistics). Plain CSV, so you can open both in Excel."""
from __future__ import annotations

import io
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd

from . import config
from .progress import PROGRESS_COLUMNS, Progress

ATTEMPT_COLUMNS = ["ts", "session_id", "phase", "word_id", "word_class", "english", "german", "direction",
                   "correct", "response_ms", "given", "expected"]
TS_FORMAT = "%Y-%m-%d %H:%M:%S"


def empty_attempts() -> pd.DataFrame:
    frame = pd.DataFrame({c: pd.Series(dtype="object") for c in ATTEMPT_COLUMNS})
    frame["ts"] = pd.to_datetime(frame["ts"])
    for column in ("correct", "response_ms"):
        frame[column] = frame[column].astype("int64")
    return frame


class Store:
    """One profile's files. The game state is held in memory and written after every completed word."""

    def __init__(self, profile: str = config.PROFILE_ME):
        self.profile = profile
        self.progress = self._load_progress()

    # ------------------------------------------------------------------ paths
    @property
    def progress_file(self) -> Path:
        return config.progress_path(self.profile)

    @property
    def attempts_file(self) -> Path:
        return config.attempts_path(self.profile)

    # ------------------------------------------------------------------ progress
    def _load_progress(self) -> Progress:
        if not self.progress_file.exists() or self.progress_file.stat().st_size == 0:
            return Progress()
        raw = pd.read_csv(self.progress_file, dtype=str, keep_default_na=False, encoding="utf-8")
        for column in PROGRESS_COLUMNS:
            if column not in raw.columns:
                raw[column] = ""
        for column in ("first_seen", "diary_since", "last_tested"):
            raw[column] = pd.to_datetime(raw[column].replace("", pd.NA), errors="coerce")
        for column in ("tests", "passes", "fails", "streak", "returns"):
            raw[column] = pd.to_numeric(raw[column], errors="coerce").fillna(0).astype("int64")
        raw["zipf"] = pd.to_numeric(raw["zipf"], errors="coerce")
        raw = raw[raw["status"].isin([config.STATUS_DIARY, config.STATUS_SECOND]) & (raw["word_id"] != "")]
        return Progress.from_frame(raw[PROGRESS_COLUMNS])

    def save_progress(self) -> None:
        """Atomic write (temp file + rename), so a crash can never leave a half-written diary."""
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        frame = self.progress.frame()
        for column in ("first_seen", "diary_since", "last_tested"):
            frame[column] = frame[column].dt.strftime(TS_FORMAT)
        temp = self.progress_file.with_suffix(".tmp")
        frame.to_csv(temp, index=False, encoding="utf-8")
        os.replace(temp, self.progress_file)

    # ------------------------------------------------------------------ attempts
    def append_attempts(self, rows: Iterable[Mapping]) -> None:
        rows = list(rows)
        if not rows:
            return
        self.attempts_file.parent.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame(rows).reindex(columns=ATTEMPT_COLUMNS)
        if pd.api.types.is_datetime64_any_dtype(frame["ts"]) or isinstance(frame["ts"].iloc[0], datetime):
            frame["ts"] = pd.to_datetime(frame["ts"]).dt.strftime(TS_FORMAT)
        header = not self.attempts_file.exists() or self.attempts_file.stat().st_size == 0
        frame.to_csv(self.attempts_file, mode="a", header=header, index=False, encoding="utf-8")

    def attempts(self) -> pd.DataFrame:
        if not self.attempts_file.exists() or self.attempts_file.stat().st_size == 0:
            return empty_attempts()
        raw = pd.read_csv(self.attempts_file, dtype=str, keep_default_na=False, on_bad_lines="skip", encoding="utf-8")
        for column in ATTEMPT_COLUMNS:
            if column not in raw.columns:
                raw[column] = ""
        raw["ts"] = pd.to_datetime(raw["ts"], errors="coerce")
        for column in ("correct", "response_ms"):
            raw[column] = pd.to_numeric(raw[column], errors="coerce")
        raw = raw.dropna(subset=["ts", "correct", "response_ms"])      # rows damaged by hand-editing are dropped
        raw = raw.astype({"correct": "int64", "response_ms": "int64"})
        return raw.sort_values("ts", kind="stable").reset_index(drop=True)[ATTEMPT_COLUMNS]

    # ------------------------------------------------------------------ editing
    def remove_word(self, word_id: str, when: datetime | None = None) -> bool:
        record = self.progress.records.get(word_id)
        if record is None or not self.progress.remove(word_id):
            return False
        self.save_progress()
        self.append_attempts([{
            "ts": when or datetime.now(), "session_id": "manual", "phase": config.PHASE_REMOVED, "word_id": word_id,
            "word_class": record["word_class"], "english": record["english"], "german": record["german"],
            "direction": "", "correct": 0, "response_ms": 0, "given": "", "expected": ""}])
        return True

    def backup_zip(self) -> bytes:
        """The profile's two files in one zip, so a reset can be undone by copying them back into the folder."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in (self.progress_file, self.attempts_file):
                if path.exists():
                    archive.write(path, path.name)
        return buffer.getvalue()

    def reset(self) -> None:
        for path in (self.progress_file, self.attempts_file):
            if path.exists():
                path.unlink()
        self.progress = Progress()
