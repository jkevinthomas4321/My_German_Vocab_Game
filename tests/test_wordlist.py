import io

import numpy as np
import pandas as pd
import pytest

from wortschatz import config, wordlist
from wortschatz.wordlist import WordListError, standardize


def raw(**columns):
    return pd.DataFrame(columns)


# ----------------------------------------------------------------------------- cleaning
def test_output_has_canonical_columns_and_types():
    df, _ = standardize(raw(english=["dog"], german=["Hund"]))
    assert list(df.columns) == wordlist.OUTPUT_COLUMNS
    assert df["zipf"].dtype == "float64" and np.isnan(df.loc[0, "zipf"])
    assert df.loc[0, "freq_band"] == "Unknown"


def test_header_aliases_and_case():
    df, report = standardize(raw(**{"English ": ["dog"], "Deutsch": ["Hund"], "Wortart": ["Noun"], "Artikel": ["DER"],
                                    "Plural": ["Hunde"], "Perfekt": [""]}))
    assert df.loc[0, ["english", "german", "word_class", "article", "plural"]].tolist() == ["dog", "Hund", "noun", "der", "Hunde"]
    assert report.unknown_columns == []


def test_missing_required_column_raises_with_the_columns_found():
    with pytest.raises(WordListError, match="german.*colour"):
        standardize(raw(english=["dog"], colour=["brown"]))


@pytest.mark.parametrize("marker", ["-", "–", "—", "n/a", "NaN", "  ", "None"])
def test_placeholder_markers_become_empty(marker):
    df, _ = standardize(raw(english=["dog"], german=["Hund"], plural=[marker]))
    assert df.loc[0, "plural"] == ""


def test_incomplete_and_empty_rows_are_dropped_and_counted():
    df, report = standardize(raw(english=["dog", "under", "cat", "", None], german=["Hund", "-", "", "", None]))
    assert df["english"].tolist() == ["dog"]
    assert (report.dropped_missing_required, report.dropped_empty) == (2, 2)
    assert report.rows_kept + report.rows_dropped == report.rows_read


def test_duplicates_ignore_case_and_whitespace_but_not_word_class():
    df, report = standardize(raw(word_class=["noun", "Noun", "verb"], english=["work", "Work ", "work"],
                                 german=["Arbeit", "arbeit", "arbeiten"]))
    assert df["german"].tolist() == ["Arbeit", "arbeiten"]
    assert report.dropped_duplicates == 1


def test_unicode_is_normalised_to_nfc():
    df, _ = standardize(raw(english=["door"], german=["Tür"]))
    assert df.loc[0, "german"] == "Tür" and len(df.loc[0, "german"]) == 3


def test_article_inside_the_german_cell_is_split_off():
    df, report = standardize(raw(english=["table", "dog"], german=["der Tisch", "Die Katze"], word_class=["", "noun"]))
    assert df[["word_class", "article", "german"]].values.tolist() == [["noun", "der", "Tisch"], ["noun", "die", "Katze"]]
    assert report.articles_split == 2


def test_article_prefix_is_not_split_for_a_verb():
    df, _ = standardize(raw(english=["to do"], german=["das tun"], word_class=["verb"]))
    assert df.loc[0, "german"] == "das tun" and df.loc[0, "article"] == ""


def test_zipf_accepts_decimal_commas_and_garbage():
    df, _ = standardize(raw(english=["a", "b", "c"], german=["A", "B", "C"], zipf=["4,83", "5.1", "very"]))
    assert df["zipf"].iloc[:2].tolist() == [4.83, 5.1] and np.isnan(df["zipf"].iloc[2])


@pytest.mark.parametrize("zipf, band", [(6.0, "Very common"), (5.0, "Common"), (4.5, "Less common"), (3.5, "Rare"), (np.nan, "Unknown")])
def test_frequency_bands(zipf, band):
    assert wordlist.freq_band(zipf) == band


def test_word_id_is_stable_and_content_based():
    a = wordlist.make_word_id("noun", "table", "Tisch")
    assert a == wordlist.make_word_id("Noun", " TABLE", "tisch") != wordlist.make_word_id("noun", "table", "Stuhl")
    df1, _ = standardize(raw(english=["a", "b"], german=["A", "B"]))
    df2, _ = standardize(raw(english=["b", "a"], german=["B", "A"]))
    assert set(df1["word_id"]) == set(df2["word_id"])


# ----------------------------------------------------------------------------- reading files
def test_reads_semicolon_csv_in_windows_1252(tmp_path):
    path = tmp_path / "words.csv"
    path.write_bytes("Englisch;Deutsch;Artikel\ndoor;Tür;die\n".encode("cp1252"))
    df, _ = wordlist.load_wordlist(path)
    assert df.loc[0, ["german", "article"]].tolist() == ["Tür", "die"]


def test_reads_csv_with_bom(tmp_path):
    path = tmp_path / "words.csv"
    path.write_bytes("﻿english,german\ndoor,Tür\n".encode("utf-8"))
    assert wordlist.load_wordlist(path)[0].loc[0, "german"] == "Tür"


def test_reads_excel_from_path_upload_and_sheet(tmp_path):
    path = tmp_path / "book.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"English": ["dog"], "German": ["Hund"]}).to_excel(writer, sheet_name="animals", index=False)
        pd.DataFrame({"English": ["door"], "German": ["Tür"]}).to_excel(writer, sheet_name="house", index=False)
    assert wordlist.list_sheets(path) == ["animals", "house"]
    assert wordlist.load_wordlist(path, sheet_name="house")[0].loc[0, "english"] == "door"
    upload, _ = wordlist.load_wordlist(io.BytesIO(path.read_bytes()), filename="book.xlsx")
    assert upload.loc[0, "english"] == "dog"


def test_excel_numbers_stay_text(tmp_path):
    path = tmp_path / "n.xlsx"
    pd.DataFrame({"english": ["one"], "german": [1]}).to_excel(path, index=False)
    assert wordlist.read_table(path).loc[0, "german"] == "1"


def test_unsupported_corrupt_and_empty_files_give_clear_errors(tmp_path):
    with pytest.raises(WordListError, match="Unsupported"):
        wordlist.read_table(tmp_path / "words.txt")
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"not a workbook")
    with pytest.raises(WordListError):
        wordlist.load_wordlist(bad)
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    with pytest.raises(WordListError, match="Missing required"):
        wordlist.load_wordlist(empty)


def test_export_import_round_trip(tmp_path, mini_words):
    path = tmp_path / "out.csv"
    wordlist.write_wordlist_csv(mini_words, path)
    assert not list(tmp_path.glob("*.tmp"))
    again, report = wordlist.load_wordlist(path)
    assert again.equals(mini_words) and report.messages == []
    from_excel, _ = wordlist.load_wordlist(io.BytesIO(wordlist.to_excel_bytes(mini_words)), filename="x.xlsx")
    assert from_excel.equals(mini_words)


# ----------------------------------------------------------------------------- the library
def test_upload_save_delete_and_discovery(mini_words):
    path = wordlist.save_upload(mini_words, "My Words!.csv")
    assert path.name == "My_Words.csv"
    available = wordlist.available_wordlists()
    assert "german_core" in available and "My_Words" in available
    assert not wordlist.is_bundled(available["My_Words"]) and wordlist.is_bundled(available["german_core"])
    assert wordlist.delete_upload("My_Words") and not wordlist.delete_upload("My_Words")


# ----------------------------------------------------------------------------- the bundled data
def test_bundled_list_passes_every_hard_quality_check(core_words):
    checks = wordlist.quality_checks(core_words)
    assert [c.name for c in checks if c.status == "fail"] == []


def test_bundled_list_content(core_words):
    assert len(core_words) >= 500
    assert core_words["zipf"].notna().all() and core_words["zipf"].is_monotonic_decreasing
    nouns = core_words[core_words["word_class"] == "noun"]
    assert nouns["article"].isin(config.ARTICLES).all()
    # spot checks of hand-written content against well-known facts
    row = core_words.set_index("german")
    assert row.loc["Tisch", ["article", "plural"]].tolist() == ["der", "Tische"]
    assert row.loc["gehen", ["past_tense", "perfect_tense"]].tolist() == ["ging", "ist gegangen"]
    assert row.loc["Mädchen", "article"] == "das"


def test_quality_checks_catch_problems(mini_words):
    bad = mini_words.copy()
    bad.loc[0, "article"] = "den"
    bad.loc[4, "perfect_tense"] = "geschrieben"
    bad.loc[6, "article"] = "der"
    failed = {c.name for c in wordlist.quality_checks(bad) if c.status == "fail"}
    assert {"Nouns have a valid article", "Perfect forms start with hat/ist", "Only nouns carry an article"} <= failed
