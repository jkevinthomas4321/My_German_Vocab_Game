"""Learning analytics: pure pandas/numpy functions over the event log.

Nothing here touches Streamlit or the disk, so every function can be unit-tested and reused from a
notebook. Typical use:

    ev = events.load_events("me")
    d = analytics.prepare(ev, words)                  # graded events + derived columns
    analytics.accuracy_by(d, "word_class")            # accuracy with 95% Wilson intervals
    analytics.forgetting_curve(d)                     # recall of known words vs. days since last review

Rates are always reported with their sample size and a Wilson score interval, because a "100%"
over three answers is not the same evidence as a "100%" over three hundred.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

import numpy as np
import pandas as pd

from . import config, srs
from .events import graded
from .german import SUFFIX_GROUPS, suffix_group

GAP_LABELS = ["Same day", "1 day", "2–3 days", "4–7 days", "8–14 days", "15+ days"]
GAP_EDGES = [-np.inf, 0.5, 1.5, 3.5, 7.5, 14.5, np.inf]


# ----------------------------------------------------------------------------- statistics
def wilson(k, n, z: float = 1.96) -> tuple[np.ndarray, np.ndarray]:
    """95% Wilson score interval for k successes in n trials (vectorised; NaN where n == 0)."""
    k, n = np.asarray(k, dtype=float), np.asarray(n, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        p = k / n
        denom = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / denom
        half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def with_rates(frame: pd.DataFrame, k: str = "correct", n: str = "n") -> pd.DataFrame:
    """Add acc / lo / hi columns (a proportion with its Wilson interval)."""
    out = frame.copy()
    out["acc"] = out[k] / out[n].where(out[n] > 0)
    out["lo"], out["hi"] = wilson(out[k], out[n])
    return out


def rate_table(d: pd.DataFrame, by: str | list[str], outcome: str = "correct") -> pd.DataFrame:
    """Group `d` by `by`; count answers and successes of `outcome` and attach accuracy + interval."""
    grouped = d.groupby(by, observed=True, sort=True)[outcome].agg(n="size", correct="sum").reset_index()
    return with_rates(grouped)


# ----------------------------------------------------------------------------- preparing the data
def prepare(ev: pd.DataFrame, words: pd.DataFrame | None = None) -> pd.DataFrame:
    """Graded events plus the columns every analysis needs."""
    d = graded(ev).sort_values("ts", kind="stable").reset_index(drop=True)
    d["day"] = d["ts"].dt.normalize()
    d["hour"] = d["ts"].dt.hour
    d["weekday"] = d["ts"].dt.dayofweek
    d["response_s"] = d["response_ms"] / 1000.0

    by_word = d.groupby("word_id", sort=False)
    d["attempt_no"] = by_word.cumcount() + 1
    d["prev_correct"] = by_word["correct"].shift()
    d["gap_days"] = (d["ts"] - by_word["ts"].shift()).dt.total_seconds() / 86400.0

    fast = (d["correct"] == 1) & (d["response_ms"] <= config.FAST_MS)
    d["xp"] = d["correct"] * config.XP_CORRECT + fast * config.XP_FAST_BONUS
    d["suffix"] = [suffix_group(g) if wc == "noun" else "" for g, wc in zip(d["german"], d["word_class"])]
    has_article = d["article_given"] != ""
    d["article_ok"] = np.where(has_article, (d["article_given"] == d["article_expected"]).astype(float), np.nan)

    if words is not None and len(words):
        lookup = words.drop_duplicates("word_id")[["word_id", "zipf", "freq_band"]]
        d = d.merge(lookup, on="word_id", how="left")
    else:
        d["zipf"], d["freq_band"] = np.nan, np.nan
    d["freq_band"] = d["freq_band"].fillna("Unknown")
    return d


# ----------------------------------------------------------------------------- headline numbers
def practice_streaks(days: Iterable[date], today: date | None = None) -> tuple[int, int]:
    """(current, longest) run of consecutive practice days. A run stays alive through the day after."""
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


def kpis(d: pd.DataFrame, states: pd.DataFrame, today: date | None = None) -> dict:
    days = d["day"].dt.date.unique() if len(d) else []
    current, longest = practice_streaks(days, today)
    mastered = int((states["box"] >= config.MASTERED_BOX).sum()) if len(states) else 0
    return {
        "answers": len(d),
        "correct": int(d["correct"].sum()),
        "accuracy": float(d["correct"].mean()) if len(d) else float("nan"),
        "words_seen": int(len(states)),
        "words_mastered": mastered,
        "sessions": int(d["session_id"].nunique()),
        "active_days": int(len(days)),
        "streak": current,
        "best_streak": longest,
        "minutes": float(d["response_ms"].clip(upper=60000).sum() / 60000) if len(d) else 0.0,
        "median_rt": float(d.loc[d["correct"] == 1, "response_s"].median()) if len(d) else float("nan"),
    }


# ----------------------------------------------------------------------------- activity over time
def daily_activity(d: pd.DataFrame) -> pd.DataFrame:
    if d.empty:
        return pd.DataFrame(columns=["day", "answers", "correct", "wrong", "accuracy", "minutes"])
    out = d.groupby("day").agg(answers=("correct", "size"), correct=("correct", "sum"),
                               ms=("response_ms", lambda s: s.clip(upper=60000).sum())).reset_index()
    out["wrong"] = out["answers"] - out["correct"]
    out["accuracy"] = out["correct"] / out["answers"]
    out["minutes"] = out["ms"] / 60000
    return out.drop(columns="ms")


def calendar_grid(d: pd.DataFrame, weeks: int = 26, today: date | None = None) -> pd.DataFrame:
    """One row per calendar day of the last `weeks` weeks, for a GitHub-style activity heatmap."""
    end = pd.Timestamp(today or date.today()).normalize()
    start = (end - pd.Timedelta(weeks=weeks - 1))
    start = start - pd.Timedelta(days=start.dayofweek)            # back to a Monday
    grid = pd.DataFrame({"day": pd.date_range(start, end, freq="D")})
    counts = d.groupby("day").size().rename("answers") if len(d) else pd.Series(dtype="int64", name="answers")
    grid = grid.merge(counts, left_on="day", right_index=True, how="left").fillna({"answers": 0})
    grid["answers"] = grid["answers"].astype(int)
    grid["week"] = grid["day"] - pd.to_timedelta(grid["day"].dt.dayofweek, unit="D")
    grid["dow"] = grid["day"].dt.dayofweek
    return grid


def session_table(d: pd.DataFrame) -> pd.DataFrame:
    if d.empty:
        return pd.DataFrame(columns=["session_id", "start", "answers", "correct", "accuracy", "minutes", "xp"])
    out = d.groupby("session_id", sort=False).agg(
        start=("ts", "min"), answers=("correct", "size"), correct=("correct", "sum"),
        ms=("response_ms", "sum"), xp=("xp", "sum")).reset_index()
    out["accuracy"] = out["correct"] / out["answers"]
    out["minutes"] = out["ms"] / 60000
    return out.sort_values("start", kind="stable").reset_index(drop=True).drop(columns="ms")


def rolling_accuracy(d: pd.DataFrame, window: int = 50) -> pd.DataFrame:
    """Accuracy over the last `window` answers, indexed by answer number (needs a full window)."""
    out = pd.DataFrame({"answer_no": np.arange(1, len(d) + 1),
                        "accuracy": d["correct"].rolling(window).mean().to_numpy()})
    return out.dropna()


# ----------------------------------------------------------------------------- memory models
def learning_curve(d: pd.DataFrame, max_attempt: int = 8) -> pd.DataFrame:
    """Accuracy on the k-th time a word is asked (k = 1..max, last bucket 'max+')."""
    if d.empty:
        return pd.DataFrame(columns=["attempt", "label", "n", "correct", "acc", "lo", "hi"])
    capped = d.assign(attempt=d["attempt_no"].clip(upper=max_attempt))
    out = rate_table(capped, "attempt")
    out["label"] = [f"{a}+" if a == max_attempt else str(a) for a in out["attempt"]]
    return out


def forgetting_curve(d: pd.DataFrame) -> pd.DataFrame:
    """Recall of words that were answered correctly last time, by days since that answer.

    Conditioning on a previous success isolates *forgetting* from never having learned the word.
    """
    sub = d[(d["prev_correct"] == 1) & d["gap_days"].notna()]
    if sub.empty:
        return pd.DataFrame(columns=["gap", "n", "correct", "acc", "lo", "hi"])
    sub = sub.assign(gap=pd.cut(sub["gap_days"], bins=GAP_EDGES, labels=GAP_LABELS, right=False))
    out = rate_table(sub, "gap")
    out["gap"] = out["gap"].astype(str)
    return out


# ----------------------------------------------------------------------------- breakdowns
def accuracy_by(d: pd.DataFrame, column: str, order: list[str] | None = None) -> pd.DataFrame:
    if d.empty:
        return pd.DataFrame(columns=[column, "n", "correct", "acc", "lo", "hi"])
    out = rate_table(d, column)
    if order:
        out[column] = pd.Categorical(out[column], categories=order, ordered=True)
        out = out.sort_values(column).reset_index(drop=True)
        out[column] = out[column].astype(str)
    return out


def hour_profile(d: pd.DataFrame) -> pd.DataFrame:
    return accuracy_by(d, "hour") if len(d) else pd.DataFrame(columns=["hour", "n", "correct", "acc", "lo", "hi"])


def weekday_profile(d: pd.DataFrame) -> pd.DataFrame:
    if d.empty:
        return pd.DataFrame(columns=["weekday", "name", "n", "correct", "acc", "lo", "hi"])
    out = accuracy_by(d, "weekday")
    out["name"] = out["weekday"].map(lambda i: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i])
    return out


# ----------------------------------------------------------------------------- response time
def response_times(d: pd.DataFrame, cap_s: float = 20.0) -> pd.DataFrame:
    return pd.DataFrame({"response_s": d["response_s"].clip(upper=cap_s),
                         "result": np.where(d["correct"] == 1, "Correct", "Wrong")})


def rt_trend(d: pd.DataFrame) -> pd.DataFrame:
    """Median response time of correct answers per day: faster answers mean growing fluency."""
    right = d[d["correct"] == 1]
    if right.empty:
        return pd.DataFrame(columns=["day", "median_s", "n"])
    return right.groupby("day").agg(median_s=("response_s", "median"), n=("response_s", "size")).reset_index()


def rt_by_qtype(d: pd.DataFrame) -> pd.DataFrame:
    right = d[d["correct"] == 1]
    if right.empty:
        return pd.DataFrame(columns=["qtype", "median_s", "n"])
    return right.groupby("qtype").agg(median_s=("response_s", "median"), n=("response_s", "size")).reset_index()


# ----------------------------------------------------------------------------- articles (der / die / das)
def article_events(d: pd.DataFrame) -> pd.DataFrame:
    return d[(d["article_expected"] != "") & (d["article_given"] != "")]


def article_confusion(d: pd.DataFrame) -> pd.DataFrame:
    """Long table: how often each correct article (rows) was answered as each article (columns)."""
    a = article_events(d)
    arts = list(config.ARTICLES)
    counts = pd.crosstab(a["article_expected"], a["article_given"]).reindex(index=arts, columns=arts, fill_value=0)
    long = counts.stack().rename("n").reset_index()
    long.columns = ["expected", "given", "n"]
    totals = long.groupby("expected")["n"].transform("sum")
    long["pct"] = (long["n"] / totals.where(totals > 0)).fillna(0.0)
    return long


def article_by_suffix(d: pd.DataFrame) -> pd.DataFrame:
    """Article accuracy per noun-ending pattern (-ung, -heit, ...), with the article each pattern predicts."""
    a = article_events(d)
    a = a[a["suffix"] != ""]
    if a.empty:
        return pd.DataFrame(columns=["suffix", "n", "correct", "acc", "lo", "hi"])
    return rate_table(a, "suffix", outcome="article_ok").sort_values("acc").reset_index(drop=True)


def suffix_gender_table(words: pd.DataFrame) -> pd.DataFrame:
    """Dataset-level: for each noun ending, the distribution of articles in the word list and the
    share a 'suffix -> most common article' rule would get right."""
    nouns = words[(words["word_class"] == "noun") & words["article"].isin(config.ARTICLES)]
    if nouns.empty:
        return pd.DataFrame(columns=["suffix", "nouns", "der", "die", "das", "rule", "rule_accuracy"])
    table = pd.crosstab(nouns["german"].map(suffix_group), nouns["article"]).reindex(columns=list(config.ARTICLES), fill_value=0)
    table["nouns"] = table.sum(axis=1)
    table["rule"] = table[list(config.ARTICLES)].idxmax(axis=1)
    table["rule_accuracy"] = table[list(config.ARTICLES)].max(axis=1) / table["nouns"]
    order = [label for label, _ in SUFFIX_GROUPS] + ["other endings"]
    table = table.reindex([o for o in order if o in table.index])
    return table.reset_index().rename(columns={"german": "suffix", "index": "suffix"})


# ----------------------------------------------------------------------------- words
def word_table(d: pd.DataFrame, states: pd.DataFrame, words: pd.DataFrame | None = None,
               prior_strength: float = 3.0) -> pd.DataFrame:
    """One row per practised word with a *smoothed* difficulty.

    A raw error rate over two answers is noisy, so the error rate is shrunk toward the learner's
    overall error rate (a Beta prior worth `prior_strength` answers):
        difficulty = (errors + a * p_overall) / (answers + a)
    """
    cols = ["word_id", "english", "german", "word_class", "zipf", "attempts", "correct", "accuracy",
            "difficulty", "median_s", "last_seen", "box"]
    if d.empty:
        return pd.DataFrame(columns=cols)
    overall_error = 1 - d["correct"].mean()
    out = d.groupby("word_id").agg(
        english=("english", "first"), german=("german", "first"), word_class=("word_class", "first"),
        attempts=("correct", "size"), correct=("correct", "sum"),
        median_s=("response_s", "median"), last_seen=("ts", "max")).reset_index()
    out["accuracy"] = out["correct"] / out["attempts"]
    errors = out["attempts"] - out["correct"]
    out["difficulty"] = (errors + prior_strength * overall_error) / (out["attempts"] + prior_strength)
    out["box"] = out["word_id"].map(states["box"]).fillna(0).astype(int) if len(states) else 0
    zipf = words.drop_duplicates("word_id").set_index("word_id")["zipf"] if words is not None and len(words) else None
    out["zipf"] = out["word_id"].map(zipf) if zipf is not None else np.nan
    return out[cols]


def hardest_words(wt: pd.DataFrame, min_attempts: int = 3, top: int = 15) -> pd.DataFrame:
    sub = wt[wt["attempts"] >= min_attempts]
    return sub.sort_values(["difficulty", "attempts"], ascending=[False, False]).head(top).reset_index(drop=True)


def frequency_effect(wt: pd.DataFrame, min_attempts: int = 3) -> dict:
    """Spearman rank correlation between word frequency (Zipf) and accuracy."""
    sub = wt[(wt["attempts"] >= min_attempts)][["zipf", "accuracy"]].dropna()
    if len(sub) < 10 or sub["zipf"].nunique() < 3 or sub["accuracy"].nunique() < 3:
        return {"rho": float("nan"), "n": len(sub)}
    # Spearman = Pearson correlation of the ranks (computed directly so scipy is not a dependency)
    return {"rho": float(sub["zipf"].rank().corr(sub["accuracy"].rank())), "n": len(sub)}


# ----------------------------------------------------------------------------- scheduling views
def mastery_funnel(states: pd.DataFrame, word_ids: list[str]) -> pd.DataFrame:
    counts = srs.status_counts(states, word_ids)
    return pd.DataFrame({"status": srs.STATUS_ORDER, "words": [counts[s] for s in srs.STATUS_ORDER]})


def due_forecast(states: pd.DataFrame, now: datetime, days: int = 7, word_ids: list[str] | None = None) -> pd.DataFrame:
    """How many reviews fall due on each of the next `days` days (overdue words count as today)."""
    today = pd.Timestamp(now).normalize()
    labels = [today + pd.Timedelta(days=i) for i in range(days)]
    counts = pd.Series(0, index=labels, dtype="int64")
    if len(states):
        sub = states if word_ids is None else states.loc[states.index.intersection(word_ids)]
        offset = (sub["due"].dt.normalize() - today).dt.days.clip(lower=0)
        for k, v in offset[offset < days].value_counts().items():
            counts.iloc[int(k)] = int(v)
    return pd.DataFrame({"day": labels, "reviews": counts.to_numpy()})


def vocabulary_growth(states: pd.DataFrame) -> pd.DataFrame:
    """Cumulative number of words seen and mastered, by day."""
    if states.empty:
        return pd.DataFrame(columns=["day", "metric", "words"])
    seen = states["first_seen"].dt.normalize().value_counts().sort_index().cumsum().rename("Words seen")
    mastered = states["mastered_at"].dropna().dt.normalize().value_counts().sort_index().cumsum().rename("Words mastered")
    days = pd.date_range(seen.index.min(), max(seen.index.max(), mastered.index.max() if len(mastered) else seen.index.max()))
    table = pd.concat([seen.reindex(days).ffill().fillna(0), mastered.reindex(days).ffill().fillna(0)], axis=1).fillna(0)
    table.index.name = "day"
    return table.reset_index().melt("day", var_name="metric", value_name="words")
