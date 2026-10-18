"""Reading, cleaning, validating and discovering word lists (CSV or Excel).

Any input is turned into one canonical DataFrame: text columns where a missing value is always
the empty string, a numeric `zipf` frequency (NaN if unknown), a stable `word_id` and a `freq_band`.
Every cleaning step is counted in a ValidationReport so the user can see what was changed or dropped.
"""
from __future__ import annotations

import csv
import hashlib
import io
import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Union

import numpy as np
import pandas as pd

from . import config
from .german import fold

Source = Union[str, Path, BinaryIO]
OUTPUT_COLUMNS = config.WORD_COLUMNS + ["word_id", "freq_band"]
_ARTICLE_PREFIX = re.compile(r"^(der|die|das)\s+(\S.*)$", re.IGNORECASE)


class WordListError(ValueError):
    """The file could not be read or does not look like a word list."""


@dataclass
class ValidationReport:
    rows_read: int = 0
    rows_kept: int = 0
    dropped_empty: int = 0
    dropped_missing_required: int = 0
    dropped_duplicates: int = 0
    articles_split: int = 0
    unusual_articles: int = 0
    unknown_columns: list[str] = field(default_factory=list)
    defaulted_columns: list[str] = field(default_factory=list)

    @property
    def rows_dropped(self) -> int:
        return self.dropped_empty + self.dropped_missing_required + self.dropped_duplicates

    @property
    def messages(self) -> list[str]:
        notes = []
        if self.dropped_empty:
            notes.append(f"{self.dropped_empty} empty row(s) removed")
        if self.dropped_missing_required:
            notes.append(f"{self.dropped_missing_required} row(s) removed because English or German was missing")
        if self.dropped_duplicates:
            notes.append(f"{self.dropped_duplicates} duplicate row(s) removed")
        if self.articles_split:
            notes.append(f"{self.articles_split} noun(s) had the article inside the German cell; it was split off")
        if self.unusual_articles:
            notes.append(f"{self.unusual_articles} row(s) have an article other than der/die/das")
        if self.unknown_columns:
            notes.append("ignored unknown column(s): " + ", ".join(self.unknown_columns))
        if self.defaulted_columns:
            notes.append("column(s) not in the file, left empty: " + ", ".join(self.defaulted_columns))
        return notes


def make_word_id(word_class: str, english: str, german: str) -> str:
    """Content-based identity, so progress survives re-uploading or re-ordering a list."""
    key = "|".join(fold(part) for part in (word_class, english, german))
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def freq_band(zipf: float) -> str:
    if zipf is None or pd.isna(zipf):
        return "Unknown"
    for threshold, label in config.FREQ_BANDS:
        if zipf >= threshold:
            return label
    return "Rare"


def empty_words() -> pd.DataFrame:
    frame = pd.DataFrame({c: pd.Series(dtype="object") for c in config.TEXT_COLUMNS})
    frame["zipf"] = pd.Series(dtype="float64")
    frame["word_id"] = pd.Series(dtype="object")
    frame["freq_band"] = pd.Series(dtype="object")
    return frame[OUTPUT_COLUMNS]


# ----------------------------------------------------------------------------- reading
def _suffix(source: Source, filename: str | None) -> str:
    name = filename or (str(source) if isinstance(source, (str, Path)) else "")
    return Path(name).suffix.lower()


def _read_bytes(source: Source) -> bytes:
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes()
    data = source.read()
    return data.encode("utf-8") if isinstance(data, str) else data


def _read_csv_bytes(data: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "cp1252"):      # cp1252 = what German-locale Excel writes
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise WordListError("Could not decode the CSV file (expected UTF-8 or Windows-1252).")
    kwargs = dict(dtype=str, keep_default_na=False, on_bad_lines="skip")
    try:
        try:
            # sep=None sniffs the delimiter: German Excel exports use ';'
            return pd.read_csv(io.StringIO(text), sep=None, engine="python", **kwargs)
        except (pd.errors.ParserError, csv.Error):
            return pd.read_csv(io.StringIO(text), sep=",", **kwargs)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def list_sheets(source: Source) -> list[str]:
    try:
        return list(pd.ExcelFile(io.BytesIO(_read_bytes(source)), engine="openpyxl").sheet_names)
    except Exception as exc:
        raise WordListError(f"Could not read the Excel file: {exc}") from exc


def read_table(source: Source, filename: str | None = None, sheet_name: str | int = 0) -> pd.DataFrame:
    """Read a .csv or .xlsx file into a raw all-text DataFrame, without cleaning it."""
    suffix = _suffix(source, filename)
    if suffix not in config.SUPPORTED_EXTENSIONS:
        raise WordListError(f"Unsupported file type '{suffix or 'unknown'}'. "
                            f"Use one of: {', '.join(config.SUPPORTED_EXTENSIONS)}.")
    data = _read_bytes(source)
    if suffix == ".csv":
        return _read_csv_bytes(data)
    try:
        return pd.read_excel(io.BytesIO(data), sheet_name=sheet_name, dtype=str,
                             keep_default_na=False, engine="openpyxl")
    except Exception as exc:
        raise WordListError(f"Could not read the Excel file: {exc}") from exc


# ----------------------------------------------------------------------------- cleaning
def _header_key(name: object) -> str:
    return re.sub(r"[\s\-]+", "_", str(name).strip().casefold())


def _alias_lookup() -> dict[str, str]:
    return {alias: canonical for canonical, aliases in config.COLUMN_ALIASES.items() for alias in aliases}


def _clean_cell(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = " ".join(unicodedata.normalize("NFC", str(value)).split())
    return "" if text.casefold() in config.MISSING_MARKERS else text


def _parse_zipf(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(",", ".", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce").astype("float64")


def standardize(raw: pd.DataFrame) -> tuple[pd.DataFrame, ValidationReport]:
    """Turn any word table into the canonical schema. Raises WordListError without English + German."""
    report = ValidationReport(rows_read=len(raw))
    lookup = _alias_lookup()
    renamed = raw.rename(columns={c: lookup.get(_header_key(c), c) for c in raw.columns})
    renamed = renamed.loc[:, ~renamed.columns.duplicated()]

    missing = [c for c in config.REQUIRED_COLUMNS if c not in renamed.columns]
    if missing:
        found = ", ".join(str(c) for c in raw.columns) or "none"
        raise WordListError(f"Missing required column(s): {', '.join(missing)}. Columns found in the file: {found}.")

    report.unknown_columns = [str(c) for c in renamed.columns if c not in config.WORD_COLUMNS]
    report.defaulted_columns = [c for c in config.TEXT_COLUMNS if c not in renamed.columns]

    text = pd.DataFrame({c: renamed[c] if c in renamed.columns else "" for c in config.TEXT_COLUMNS},
                        index=renamed.index).apply(lambda col: col.map(_clean_cell))
    text["zipf"] = _parse_zipf(renamed["zipf"]) if "zipf" in renamed.columns else np.nan
    df = text

    empty = (df[config.TEXT_COLUMNS] == "").all(axis=1)
    report.dropped_empty = int(empty.sum())
    df = df[~empty]

    incomplete = (df["english"] == "") | (df["german"] == "")
    report.dropped_missing_required = int(incomplete.sum())
    df = df[~incomplete].copy()

    df["word_class"] = df["word_class"].str.casefold().replace("", config.DEFAULT_WORD_CLASS)
    df["article"] = df["article"].str.casefold()

    # "der Tisch" in the German cell -> article + noun (and a missing class becomes 'noun')
    parts = df["german"].str.extract(_ARTICLE_PREFIX)
    split = parts[0].notna() & (df["article"] == "") & df["word_class"].isin(["noun", config.DEFAULT_WORD_CLASS])
    df.loc[split, "article"] = parts.loc[split, 0].str.casefold()
    df.loc[split, "german"] = parts.loc[split, 1]
    df.loc[split & (df["word_class"] == config.DEFAULT_WORD_CLASS), "word_class"] = "noun"
    report.articles_split = int(split.sum())

    df["word_id"] = [make_word_id(c, e, g) for c, e, g in zip(df["word_class"], df["english"], df["german"])]
    duplicated = df["word_id"].duplicated()
    report.dropped_duplicates = int(duplicated.sum())
    df = df[~duplicated]

    report.unusual_articles = int(((df["article"] != "") & ~df["article"].isin(config.ARTICLES)).sum())
    df["freq_band"] = [freq_band(z) for z in df["zipf"]]
    df = df[OUTPUT_COLUMNS].reset_index(drop=True)
    report.rows_kept = len(df)
    return df, report


def load_wordlist(source: Source, filename: str | None = None,
                  sheet_name: str | int = 0) -> tuple[pd.DataFrame, ValidationReport]:
    return standardize(read_table(source, filename=filename, sheet_name=sheet_name))


# ----------------------------------------------------------------------------- the library
def available_wordlists() -> dict[str, Path]:
    """name -> path for bundled lists first, then the user's uploads."""
    found: dict[str, Path] = {}
    for folder in (config.WORDLIST_DIR, config.uploads_dir()):
        folder = Path(folder)
        if not folder.exists():
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() in config.SUPPORTED_EXTENSIONS and not path.name.startswith(("~$", ".")):
                found.setdefault(path.stem, path)
    return found


def is_bundled(path: Path) -> bool:
    return Path(path).resolve().parent == Path(config.WORDLIST_DIR).resolve()


def safe_name(name: str) -> str:
    stem = Path(name).stem
    cleaned = re.sub(r"[^\w\-]+", "_", stem, flags=re.UNICODE).strip("_")
    return cleaned or "my_words"


def write_wordlist_csv(df: pd.DataFrame, path: Path) -> None:
    """Atomic write (temp file + rename); utf-8-sig so Excel shows umlauts correctly."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.reindex(columns=config.WORD_COLUMNS).to_csv(tmp, index=False, encoding="utf-8-sig")
    os.replace(tmp, path)


def save_upload(df: pd.DataFrame, name: str) -> Path:
    path = Path(config.uploads_dir()) / f"{safe_name(name)}.csv"
    write_wordlist_csv(df, path)
    return path


def delete_upload(name: str) -> bool:
    path = Path(config.uploads_dir()) / f"{name}.csv"
    if path.exists():
        path.unlink()
        return True
    return False


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.reindex(columns=config.WORD_COLUMNS).to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df.reindex(columns=config.WORD_COLUMNS).to_excel(buffer, index=False, sheet_name="words", engine="openpyxl")
    return buffer.getvalue()


# ----------------------------------------------------------------------------- data-quality scorecard
@dataclass(frozen=True)
class Check:
    name: str
    status: str          # "pass" | "warn" | "fail"
    detail: str


def quality_checks(df: pd.DataFrame) -> list[Check]:
    """Automated checks a data engineer would run on a vocabulary table."""
    nouns = df[df["word_class"] == "noun"]
    verbs = df[df["word_class"] == "verb"]

    def check(name: str, bad: int, total: int, what: str, level: str = "fail") -> Check:
        if total == 0:
            return Check(name, "pass", "Not applicable (no such rows).")
        if bad == 0:
            return Check(name, "pass", f"All {total} {what} are fine.")
        return Check(name, level, f"{bad} of {total} {what} need attention.")

    perfect_ok = verbs["perfect_tense"].str.split().str[0].isin(["hat", "ist"])
    text = df[config.TEXT_COLUMNS]
    stray_space = int((text.apply(lambda col: col != col.str.strip()).any(axis=1)).sum())
    non_nfc = int(sum(unicodedata.normalize("NFC", v) != v for v in df["german"]))
    english_dupes = int(df.duplicated(["word_class", "english"]).sum())
    return [
        check("Unique words", int(df["word_id"].duplicated().sum()), len(df), "words"),
        check("Nouns have a valid article", int((~nouns["article"].isin(config.ARTICLES)).sum()), len(nouns), "nouns"),
        check("Only nouns carry an article", int((df[df["word_class"] != "noun"]["article"] != "").sum()),
              int((df["word_class"] != "noun").sum()), "non-nouns"),
        check("Verbs have past and perfect forms",
              int(((verbs["past_tense"] == "") | (verbs["perfect_tense"] == "")).sum()), len(verbs), "verbs"),
        check("Perfect forms start with hat/ist", int((~perfect_ok).sum()), len(verbs), "verbs"),
        check("English labels are unique per word class", english_dupes, len(df), "labels"),
        check("No stray whitespace", stray_space, len(df), "rows"),
        check("German text is Unicode-normalised (NFC)", non_nfc, len(df), "words"),
        check("Nouns have a plural", int((nouns["plural"] == "").sum()), len(nouns), "nouns", level="warn"),
        check("Frequency is known", int(df["zipf"].isna().sum()), len(df), "words", level="warn"),
    ]
