"""Shared fixtures. Every test runs against a throw-away user_data folder, never real progress."""
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from wortschatz import config, wordlist

ROOT = Path(__file__).resolve().parent.parent
NOW = datetime(2026, 10, 18, 15, 0, 0)


@pytest.fixture(autouse=True)
def isolated_user_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "USER_DIR", tmp_path / "user_data")
    return tmp_path / "user_data"


@pytest.fixture(scope="session")
def core_words() -> pd.DataFrame:
    """The bundled word list, loaded once."""
    return wordlist.load_wordlist(config.WORDLIST_DIR / "german_core.csv")[0]


@pytest.fixture
def mini_words() -> pd.DataFrame:
    """A small hand-made list covering every question type."""
    raw = pd.DataFrame({
        "word_class": ["noun", "noun", "noun", "noun", "verb", "verb", "adjective", "adjective", "adjective", "adverb"],
        "english": ["table", "city", "child", "door", "to write", "to go", "fast", "big", "new", "today"],
        "article": ["der", "die", "das", "die", "", "", "", "", "", ""],
        "german": ["Tisch", "Stadt", "Kind", "Tür", "schreiben", "gehen", "schnell", "groß", "neu", "heute"],
        "plural": ["Tische", "Städte", "Kinder", "Türen", "", "", "", "", "", ""],
        "past_tense": ["", "", "", "", "schrieb", "ging", "", "", "", ""],
        "perfect_tense": ["", "", "", "", "hat geschrieben", "ist gegangen", "", "", "", ""],
        "zipf": [4.8, 5.4, 5.6, 4.9, 5.0, 6.0, 5.3, 6.1, 5.9, 6.0],
    })
    return wordlist.standardize(raw)[0]
