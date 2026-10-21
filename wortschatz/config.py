"""Paths, schema and constants. Nothing here imports a UI framework."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDLIST_DIR = ROOT / "data" / "wordlists"          # bundled, read-only word lists
# Everything the game writes lives here. Overridable so tests and CI never touch real progress.
USER_DIR = Path(os.environ.get("WORTSCHATZ_USER_DIR", ROOT / "user_data"))

PROFILE_ME = "me"
PROFILE_DEMO = "demo"
PROFILE_LABELS = {PROFILE_ME: "My diary", PROFILE_DEMO: "Demo data"}
DEFAULT_WORDLIST = "german_core"


def profile_dir(profile: str) -> Path:
    return Path(USER_DIR) / profile


def progress_path(profile: str) -> Path:
    return profile_dir(profile) / "progress.csv"


def attempts_path(profile: str) -> Path:
    return profile_dir(profile) / "attempts.csv"


def uploads_dir() -> Path:
    return Path(USER_DIR) / "wordlists"          # uploaded lists are shared by all profiles


# ----------------------------------------------------------------------------- word-list schema
SUPPORTED_EXTENSIONS = (".csv", ".xlsx")
TEXT_COLUMNS = ["word_class", "english", "article", "german", "plural", "past_tense", "perfect_tense"]
WORD_COLUMNS = TEXT_COLUMNS + ["zipf"]
REQUIRED_COLUMNS = ["english", "german"]
DEFAULT_WORD_CLASS = "other"
ARTICLES = ("der", "die", "das")
WORD_CLASSES = ["noun", "verb", "adjective", "adverb", "preposition", "conjunction", "interjection", "other"]

# Header spellings accepted on import (lower-cased, spaces/hyphens -> "_").
COLUMN_ALIASES = {
    "word_class": ["word_class", "wordclass", "class", "pos", "part_of_speech", "type", "wortart"],
    "english": ["english", "en", "eng", "englisch"],
    "article": ["article", "artikel", "gender", "genus"],
    "german": ["german", "de", "deutsch", "ger"],
    "plural": ["plural", "pl"],
    "past_tense": ["past_tense", "past", "preterite", "präteritum", "praeteritum", "simple_past"],
    "perfect_tense": ["perfect_tense", "perfect", "perfekt", "past_participle"],
    "zipf": ["zipf", "zipf_frequency", "frequency", "freq"],
}
MISSING_MARKERS = {"", "-", "–", "—", "nan", "none", "n/a", "null"}

# Frequency bands on the Zipf scale (log10 of occurrences per billion words; 7 = "the", 3 = rare).
FREQ_BANDS = [(5.4, "Very common"), (4.8, "Common"), (4.3, "Less common"), (-1.0, "Rare")]
FREQ_BAND_ORDER = ["Very common", "Common", "Less common", "Rare", "Unknown"]

# ----------------------------------------------------------------------------- game rules
STATUS_DIARY = "diary"
STATUS_SECOND = "second_chance"

DIRECTIONS = {"de_en": "German → English", "en_de": "English → German"}
DEFAULT_COUNT = 10
MIN_COUNT = 3
MAX_COUNT = 50

PHASE_LEARN = "learn"        # first test of a freshly learned word
PHASE_RETEST = "retest"      # test of a word from the second-chance list
PHASE_DIARY = "diary"        # revision test of a diary word
PHASE_REMOVED = "removed"    # a word deleted from the diary (logged so the history stays consistent)
