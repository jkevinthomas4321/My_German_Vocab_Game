"""Paths, schema and tunable constants. Nothing here imports Streamlit."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDLIST_DIR = ROOT / "data" / "wordlists"          # bundled, read-only word lists
# Everything the app writes lives here. Overridable so tests and CI never touch real progress.
USER_DIR = Path(os.environ.get("WORTSCHATZ_USER_DIR", ROOT / "user_data"))

PROFILE_ME = "me"
PROFILE_DEMO = "demo"
PROFILE_LABELS = {PROFILE_ME: "My progress", PROFILE_DEMO: "Demo data (synthetic)"}
DEFAULT_WORDLIST = "german_core"


def profile_dir(profile: str) -> Path:
    return Path(USER_DIR) / profile


def events_path(profile: str) -> Path:
    return profile_dir(profile) / "events.csv"


def uploads_dir() -> Path:
    return Path(USER_DIR) / "wordlists"


# ----------------------------------------------------------------------------- vocabulary schema
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

# ----------------------------------------------------------------------------- learning model
# Leitner boxes: a word in box b is due again INTERVAL_DAYS[b] days after it was last answered.
INTERVAL_DAYS = {1: 0.25, 2: 1.0, 3: 3.0, 4: 6.0, 5: 12.0}
MAX_BOX = 5
MASTERED_BOX = 5
WRONG_BOX_DROP = 2           # a wrong answer drops a word two boxes (never below box 1)
NEW_WORD_RATIO = 0.35        # share of a "smart" session reserved for unseen words
BACKLOG_NEW_WORD_RATIO = 0.1 # ...reduced to this while a full session's worth of reviews is already overdue

# ----------------------------------------------------------------------------- gamification
DEFAULT_DAILY_GOAL = 20      # answers per day
XP_CORRECT = 10
XP_FAST_BONUS = 5            # correct answer given within FAST_MS
FAST_MS = 4000
LEVEL_XP_STEP = 150          # level L is reached at LEVEL_XP_STEP * (L - 1)^2 XP
LEVEL_TITLES = ["Anfänger", "Entdecker", "Wortsammler", "Sprachschüler", "Wortschmied",
                "Satzbauer", "Redner", "Kenner", "Meister", "Wortzauberer"]

# ----------------------------------------------------------------------------- analytics thresholds
MIN_N_FOR_INSIGHT = 12       # smallest group an auto-generated insight may talk about
WEAK_ACCURACY = 0.7
