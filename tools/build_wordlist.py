"""Build data/wordlists/german_core.csv from tools/seed_words.csv.

The seed file is hand-written (translations, articles, plurals, verb forms). This script
  1. validates it (articles, verb forms, duplicates),
  2. looks up each lemma's measured German frequency with the `wordfreq` package
     (Zipf scale: 7 = extremely common, 3 = rare), and
  3. writes the list sorted from most to least frequent.

Run from the repository root:  python tools/build_wordlist.py
Only needed when the seed changes; the generated CSV is committed, so `wordfreq` is not
a runtime dependency of the app.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from wordfreq import zipf_frequency

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "tools" / "seed_words.csv"
OUT = ROOT / "data" / "wordlists" / "german_core.csv"
ARTICLES = {"der", "die", "das"}


def validate(df: pd.DataFrame) -> list[str]:
    problems = []
    nouns = df[df.word_class == "noun"]
    verbs = df[df.word_class == "verb"]
    for row in nouns[~nouns.article.isin(ARTICLES)].itertuples():
        problems.append(f"noun without valid article: {row.german!r} ({row.article!r})")
    for row in verbs.itertuples():
        if not row.past_tense or not row.perfect_tense:
            problems.append(f"verb missing forms: {row.german!r}")
        elif row.perfect_tense.split()[0] not in {"hat", "ist"}:
            problems.append(f"perfect should start with hat/ist: {row.german!r} -> {row.perfect_tense!r}")
    for row in df[~df.word_class.isin(["noun"]) & (df.article != "")].itertuples():
        problems.append(f"article on non-noun: {row.german!r}")
    dup = df[df.duplicated(["word_class", "german"], keep=False)]
    problems += [f"duplicate German entry: {r.word_class}/{r.german}" for r in dup.itertuples()]
    dup_en = df[df.duplicated(["word_class", "english"], keep=False)]
    problems += [f"duplicate English label: {r.word_class}/{r.english}" for r in dup_en.itertuples()]
    return problems


def main() -> int:
    df = pd.read_csv(SEED, dtype=str, keep_default_na=False)
    problems = validate(df)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    df["zipf"] = [round(zipf_frequency(word, "de"), 2) for word in df.german]
    missing = df[df.zipf == 0]
    if len(missing):
        print("No frequency found for:", ", ".join(missing.german), file=sys.stderr)
    df = df.sort_values("zipf", ascending=False, kind="stable").reset_index(drop=True)
    df = df[["word_class", "english", "article", "german", "plural", "past_tense", "perfect_tense", "zipf"]]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"Wrote {len(df)} words to {OUT.relative_to(ROOT)}")
    print(df.word_class.value_counts().to_string())
    print(f"Zipf range {df.zipf.min()} - {df.zipf.max()}, median {df.zipf.median()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
