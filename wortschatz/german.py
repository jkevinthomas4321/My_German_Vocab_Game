"""Small German-language helpers: noun-suffix patterns, text normalisation, edit distance."""
from __future__ import annotations

import unicodedata

# Ordered: the first matching suffix wins. Each group is a classic gender rule of thumb.
SUFFIX_GROUPS: list[tuple[str, tuple[str, ...]]] = [
    ("-ung", ("ung",)),
    ("-heit / -keit", ("heit", "keit")),
    ("-schaft", ("schaft",)),
    ("-ion", ("ion",)),
    ("-tät", ("tät",)),
    ("-ur", ("ur",)),
    ("-chen / -lein", ("chen", "lein")),
    ("-ment", ("ment",)),
    ("-um", ("um",)),
    ("-ismus", ("ismus",)),
    ("-ling", ("ling",)),
    ("-er", ("er",)),
    ("-e", ("e",)),
]
NO_SUFFIX_RULE = "other endings"

# The classic rule of thumb for each ending (shown next to the analysis; "mostly" = real exceptions exist).
SUFFIX_HINT = {
    "-ung": "always die", "-heit / -keit": "always die", "-schaft": "always die", "-ion": "always die",
    "-tät": "always die", "-ur": "mostly die", "-chen / -lein": "always das", "-ment": "mostly das",
    "-um": "mostly das", "-ismus": "always der", "-ling": "always der", "-er": "mostly der (but das Zimmer, die Mutter)",
    "-e": "mostly die (but der Junge, das Ende)", NO_SUFFIX_RULE: "no reliable rule: learn the article with the word",
}


def suffix_group(noun: str) -> str:
    """The suffix pattern a noun belongs to ('other endings' if none of the rules apply)."""
    lowered = noun.casefold().strip()
    for label, endings in SUFFIX_GROUPS:
        if lowered.endswith(endings):
            return label
    return NO_SUFFIX_RULE


def fold(text: object) -> str:
    """Comparison key: NFC, case-folded, single-spaced."""
    if text is None:
        return ""
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


_TRANSLIT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def fold_translit(text: object) -> str:
    """`fold` plus ä/ö/ü/ß -> ae/oe/ue/ss, so a learner without a German keyboard is not penalised."""
    return fold(text).translate(_TRANSLIT)


def edit_distance(a: str, b: str) -> int:
    """Edit distance counting insert, delete, substitute and swapping two adjacent letters as one step."""
    if a == b:
        return 0
    rows = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        rows[i][0] = i
    for j in range(len(b) + 1):
        rows[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = a[i - 1] != b[j - 1]
            rows[i][j] = min(rows[i - 1][j] + 1, rows[i][j - 1] + 1, rows[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                rows[i][j] = min(rows[i][j], rows[i - 2][j - 2] + 1)
    return rows[-1][-1]
