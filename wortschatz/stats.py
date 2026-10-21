"""Statistics about the learning loop: pure pandas/NumPy over the attempts log (one row per answered question).

A *word outcome* is one test of one word: it passed when every question about it was answered correctly.
Everything below derives from the log, so the numbers can never disagree with what really happened.
Rates carry a 95% Wilson interval, because 100% over three tests is not the same evidence as over three hundred.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

import numpy as np
import pandas as pd

from . import config
from .progress import Progress

GAP_LABELS = ["1 day", "2–3 days", "4–7 days", "8–14 days", "15+ days"]
GAP_EDGES = [-np.inf, 1.5, 3.5, 7.5, 14.5, np.inf]
PHASE_LABELS = {config.PHASE_LEARN: "First test", config.PHASE_RETEST: "Second-chance re-test",
                config.PHASE_DIARY: "Diary revision"}


# ----------------------------------------------------------------------------- statistics helpers
def wilson(k, n, z: float = 1.96) -> tuple[np.ndarray, np.ndarray]:
    """95% Wilson score interval for k successes in n trials (NaN where n == 0)."""
    k, n = np.asarray(k, dtype=float), np.asarray(n, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        p = k / n
        denominator = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / denominator
        half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    return centre - half, centre + half


def rate_table(frame: pd.DataFrame, by: str, outcome: str = "passed") -> pd.DataFrame:
    """Group `frame` by `by`; count rows and successes of `outcome`, with rate and 95% interval."""
    table = frame.groupby(by, observed=True, sort=True)[outcome].agg(n="size", wins="sum").reset_index()
    table["rate"] = table["wins"] / table["n"].where(table["n"] > 0)
    table["lo"], table["hi"] = wilson(table["wins"], table["n"])
    return table


def practice_streaks(days: Iterable[date], today: date | None = None) -> tuple[int, int]:
    """(current, longest) run of consecutive days with at least one test. A run stays alive through the next day."""
    unique = sorted(set(days))
    if not unique:
        return 0, 0
    longest = run = 1
    for previous, current in zip(unique, unique[1:]):
        run = run + 1 if current - previous == timedelta(days=1) else 1
        longest = max(longest, run)
    today = today or date.today()
    current_run = 0
    if today - unique[-1] <= timedelta(days=1):
        current_run = 1
        for previous, current in zip(reversed(unique[:-1]), reversed(unique[1:])):
            if current - previous != timedelta(days=1):
                break
            current_run += 1
    return current_run, longest


# ----------------------------------------------------------------------------- word outcomes
OUTCOME_COLUMNS = ["ts", "day", "session_id", "phase", "word_id", "word_class", "english", "german", "passed"]


def word_outcomes(attempts: pd.DataFrame) -> pd.DataFrame:
    """One row per (test, word): passed = every question about the word was right. Removals are excluded."""
    tests = attempts[attempts["phase"] != config.PHASE_REMOVED]
    if tests.empty:
        empty = pd.DataFrame({c: pd.Series(dtype="object") for c in OUTCOME_COLUMNS})
        for column in ("ts", "day"):
            empty[column] = pd.to_datetime(empty[column])
        empty["passed"] = empty["passed"].astype("int64")
        return empty
    out = tests.groupby(["session_id", "phase", "word_id"], sort=False).agg(
        ts=("ts", "max"), word_class=("word_class", "first"), english=("english", "first"),
        german=("german", "first"), passed=("correct", "min")).reset_index()
    out["day"] = out["ts"].dt.normalize()
    return out.sort_values("ts", kind="stable").reset_index(drop=True)[OUTCOME_COLUMNS]


def kpis(progress: Progress, attempts: pd.DataFrame, today: date | None = None) -> dict:
    outcomes = word_outcomes(attempts)
    first = outcomes[outcomes["phase"] == config.PHASE_LEARN]
    current, longest = practice_streaks(outcomes["day"].dt.date, today)
    tests = attempts[attempts["phase"] != config.PHASE_REMOVED]
    today_ts = pd.Timestamp(today or date.today())
    return {
        "diary": progress.count(config.STATUS_DIARY),
        "second_chance": progress.count(config.STATUS_SECOND),
        "words_tested": len(progress.records),
        "tests": len(outcomes),
        "answers": len(tests),
        "first_try_rate": float(first["passed"].mean()) if len(first) else float("nan"),
        "streak": current,
        "best_streak": longest,
        "active_days": int(outcomes["day"].nunique()),
        "today_words": int((outcomes["day"] == today_ts).sum()),
        "minutes": float(tests["response_ms"].clip(upper=60000).sum() / 60000) if len(tests) else 0.0,
    }


# ----------------------------------------------------------------------------- over time
def daily_activity(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Word tests per day, split into passed and failed."""
    if outcomes.empty:
        return pd.DataFrame(columns=["day", "passed", "failed"])
    table = outcomes.groupby("day").agg(tests=("passed", "size"), passed=("passed", "sum")).reset_index()
    table["failed"] = table["tests"] - table["passed"]
    return table[["day", "passed", "failed"]]


def diary_growth(attempts: pd.DataFrame) -> pd.DataFrame:
    """Diary size at the end of each day: +1 when a word enters it, -1 when it falls back or is deleted."""
    outcomes = word_outcomes(attempts)
    removed = attempts[attempts["phase"] == config.PHASE_REMOVED]
    if outcomes.empty:
        return pd.DataFrame(columns=["day", "diary"])
    enters = outcomes["passed"].eq(1) & outcomes["phase"].isin([config.PHASE_LEARN, config.PHASE_RETEST])
    leaves = outcomes["passed"].eq(0) & outcomes["phase"].eq(config.PHASE_DIARY)
    delta = pd.concat([
        pd.DataFrame({"day": outcomes["day"], "delta": enters.astype(int) - leaves.astype(int)}),
        pd.DataFrame({"day": removed["ts"].dt.normalize(), "delta": -1}),
    ])
    daily = delta.groupby("day")["delta"].sum()
    days = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    return daily.reindex(days, fill_value=0).cumsum().rename_axis("day").rename("diary").reset_index()


def calendar_counts(outcomes: pd.DataFrame) -> pd.DataFrame:
    if outcomes.empty:
        return pd.DataFrame(columns=["day", "tests"])
    return outcomes.groupby("day").size().rename("tests").reset_index()


# ----------------------------------------------------------------------------- how well it goes
def pass_rate_by_phase(outcomes: pd.DataFrame) -> pd.DataFrame:
    if outcomes.empty:
        return pd.DataFrame(columns=["phase", "label", "n", "wins", "rate", "lo", "hi"])
    table = rate_table(outcomes, "phase")
    table["label"] = table["phase"].map(PHASE_LABELS)
    order = {p: i for i, p in enumerate(PHASE_LABELS)}
    return table.sort_values("phase", key=lambda s: s.map(order)).reset_index(drop=True)


def pass_rate_by_class(outcomes: pd.DataFrame) -> pd.DataFrame:
    if outcomes.empty:
        return pd.DataFrame(columns=["word_class", "n", "wins", "rate", "lo", "hi"])
    return rate_table(outcomes, "word_class").sort_values("rate").reset_index(drop=True)


def direction_accuracy(attempts: pd.DataFrame) -> pd.DataFrame:
    """Which direction is harder: German -> English or English -> German?"""
    tests = attempts[attempts["phase"] != config.PHASE_REMOVED]
    if tests.empty:
        return pd.DataFrame(columns=["direction", "label", "n", "wins", "rate", "lo", "hi", "median_s"])
    table = rate_table(tests.assign(passed=tests["correct"]), "direction")
    table["label"] = table["direction"].map(config.DIRECTIONS)
    table["median_s"] = table["direction"].map(tests.groupby("direction")["response_ms"].median() / 1000)
    return table


def second_chance_journey(outcomes: pd.DataFrame, progress: Progress) -> pd.DataFrame:
    """For words that ever failed their first test: how many re-tests did they need before reaching the diary?"""
    rows = []
    for _, group in outcomes.groupby("word_id"):
        group = group.sort_values("ts")
        if group.iloc[0]["phase"] != config.PHASE_LEARN or group.iloc[0]["passed"] == 1:
            continue
        retests = group[group["phase"] == config.PHASE_RETEST]["passed"].tolist()
        if 1 in retests:
            rows.append(retests.index(1) + 1)
        else:
            rows.append(0)                                              # still waiting in second chance
    if not rows:
        return pd.DataFrame(columns=["retests", "words"])
    labels = ["Not yet", "1 re-test", "2 re-tests", "3+ re-tests"]
    buckets = [labels[min(r, 3)] for r in rows]
    counts = pd.Series(buckets).value_counts().reindex(labels, fill_value=0)
    return counts.rename_axis("retests").reset_index(name="words")


def revision_by_gap(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Do diary words get forgotten? Pass rate of revision tests by days since the word was last tested."""
    if outcomes.empty:
        return pd.DataFrame(columns=["gap", "n", "wins", "rate", "lo", "hi"])
    ordered = outcomes.sort_values("ts", kind="stable")
    gap = (ordered["ts"] - ordered.groupby("word_id")["ts"].shift()).dt.total_seconds() / 86400
    revisions = ordered.assign(gap_days=gap)[ordered["phase"] == config.PHASE_DIARY]
    revisions = revisions[revisions["gap_days"].notna()]
    if revisions.empty:
        return pd.DataFrame(columns=["gap", "n", "wins", "rate", "lo", "hi"])
    revisions = revisions.assign(gap=pd.cut(revisions["gap_days"], bins=GAP_EDGES, labels=GAP_LABELS, right=False))
    table = rate_table(revisions, "gap")
    table["gap"] = table["gap"].astype(str)
    return table


def hardest_words(outcomes: pd.DataFrame, top: int = 12) -> pd.DataFrame:
    """Words that failed most often, with how often they were tested."""
    if outcomes.empty:
        return pd.DataFrame(columns=["german", "english", "word_class", "tests", "fails", "fail_rate"])
    table = outcomes.groupby("word_id").agg(german=("german", "first"), english=("english", "first"),
                                            word_class=("word_class", "first"), tests=("passed", "size"),
                                            wins=("passed", "sum")).reset_index()
    table["fails"] = table["tests"] - table["wins"]
    table["fail_rate"] = table["fails"] / table["tests"]
    table = table[table["fails"] > 0].sort_values(["fails", "fail_rate"], ascending=False)
    return table.head(top).reset_index(drop=True)[["german", "english", "word_class", "tests", "fails", "fail_rate"]]


def weekday_profile(outcomes: pd.DataFrame) -> pd.DataFrame:
    if outcomes.empty:
        return pd.DataFrame(columns=["name", "n", "wins", "rate", "lo", "hi"])
    table = rate_table(outcomes.assign(weekday=outcomes["ts"].dt.dayofweek), "weekday")
    table["name"] = table["weekday"].map(lambda i: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i])
    return table


# ----------------------------------------------------------------------------- plain-language findings
MIN_N = 10


def _pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def findings(progress: Progress, attempts: pd.DataFrame, today: date | None = None) -> list[dict]:
    """Short statements about the learner's data. Each rule stays silent when its sample is too small."""
    outcomes = word_outcomes(attempts)
    if outcomes.empty:
        return []
    out: list[dict] = []
    k = kpis(progress, attempts, today)
    first = outcomes[outcomes["phase"] == config.PHASE_LEARN]
    if len(first) >= MIN_N:
        out.append({"icon": "flag", "tone": "info", "title": "First-try pass rate",
                    "text": f"You pass {_pct(k['first_try_rate'])} of new words on their first test ({len(first)} words). "
                            f"{k['diary']} words are in your diary, {k['second_chance']} are in second chance."})

    by_class = pass_rate_by_class(first)
    by_class = by_class[by_class["n"] >= MIN_N]
    if len(by_class) >= 2 and by_class["rate"].iloc[-1] - by_class["rate"].iloc[0] >= 0.10:
        low, high = by_class.iloc[0], by_class.iloc[-1]
        out.append({"icon": "category", "tone": "watch", "title": f"{low['word_class'].capitalize()}s are hardest",
                    "text": f"{_pct(low['rate'])} of {low['word_class']}s pass first time (n={low['n']}) versus "
                            f"{_pct(high['rate'])} of {high['word_class']}s (n={high['n']})."})

    directions = direction_accuracy(attempts).set_index("direction")
    if {"de_en", "en_de"} <= set(directions.index) and directions["n"].min() >= 2 * MIN_N:
        easy, hard = directions.loc["de_en"], directions.loc["en_de"]
        if easy["rate"] - hard["rate"] >= 0.08:
            out.append({"icon": "translate", "tone": "watch", "title": "Writing German is harder than reading it",
                        "text": f"{_pct(hard['rate'])} correct English → German versus {_pct(easy['rate'])} German → English, "
                                f"and it takes about {hard['median_s'] / easy['median_s']:.1f}× as long."})

    journey = second_chance_journey(outcomes, progress)
    if len(journey) and journey["words"].sum() >= MIN_N:
        total = int(journey["words"].sum())
        once = int(journey.set_index("retests")["words"].get("1 re-test", 0))
        out.append({"icon": "replay", "tone": "good", "title": "Second chances work",
                    "text": f"Of {total} words that failed their first test, {once} ({_pct(once / total)}) reached the diary after a single re-test."})

    gaps = revision_by_gap(outcomes).set_index("gap")
    near, far = gaps.reindex(["1 day", "2–3 days"]).dropna(), gaps.reindex(["8–14 days", "15+ days"]).dropna()
    if near["n"].sum() >= MIN_N and far["n"].sum() >= MIN_N:
        a, b = near["wins"].sum() / near["n"].sum(), far["wins"].sum() / far["n"].sum()
        if a - b >= 0.10:
            out.append({"icon": "psychology", "tone": "watch", "title": "Diary words fade after a week",
                        "text": f"Revision tests pass {_pct(a)} within 3 days of the last test but {_pct(b)} after 8+ days. "
                                f"Revise your diary more often."})
        else:
            out.append({"icon": "psychology", "tone": "good", "title": "Your diary words are holding",
                        "text": f"Revision tests still pass {_pct(b)} after 8+ days (versus {_pct(a)} within 3 days)."})
    if k["streak"] >= 2:
        out.append({"icon": "local_fire_department", "tone": "good", "title": f"{k['streak']}-day streak",
                    "text": f"Your longest run so far is {k['best_streak']} days."})
    return out
