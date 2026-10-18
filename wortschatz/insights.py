"""Plain-language findings generated from the analytics.

Every rule states the numbers it is based on and stays silent when the sample is too small
(config.MIN_N_FOR_INSIGHT), so the dashboard never claims more than the data supports.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from . import analytics as A
from . import config
from .german import SUFFIX_HINT

MIN_N = config.MIN_N_FOR_INSIGHT
DAYPARTS = [("morning (5-11)", range(5, 12)), ("afternoon (12-17)", range(12, 18)),
            ("evening (18-22)", range(18, 23)), ("night (23-4)", [23, 0, 1, 2, 3, 4])]


@dataclass(frozen=True)
class Insight:
    icon: str
    title: str
    text: str
    tone: str = "info"          # "good" | "watch" | "info"


def _pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def generate(d: pd.DataFrame, states: pd.DataFrame, words: pd.DataFrame, now: datetime) -> list[Insight]:
    """Findings for the prepared events `d` (see analytics.prepare)."""
    if d.empty:
        return []
    out: list[Insight] = []
    k = A.kpis(d, states, now.date())

    out.append(Insight("📊", "Overview",
                       f"{k['answers']} answers over {k['active_days']} active day(s), {_pct(k['accuracy'])} correct, "
                       f"about {k['minutes']:.0f} minutes of answering time. {k['words_seen']} words met, "
                       f"{k['words_mastered']} mastered."))

    # --- repetition works?
    lc = A.learning_curve(d, max_attempt=2)
    first, later = lc[lc["attempt"] == 1], d[d["attempt_no"] > 1]
    if len(first) and first["n"].iloc[0] >= MIN_N and len(later) >= MIN_N:
        a1, a2 = first["acc"].iloc[0], later["correct"].mean()
        out.append(Insight("🔁", "Repetition pays off",
                           f"On first sight of a word you are right {_pct(a1)} of the time (n={first['n'].iloc[0]}); "
                           f"on repeats it is {_pct(a2)} (n={len(later)}), a gain of {100 * (a2 - a1):.0f} points.",
                           "good" if a2 > a1 else "info"))

    # --- word classes
    by_class = A.accuracy_by(d, "word_class")
    by_class = by_class[by_class["n"] >= MIN_N]
    if len(by_class) >= 2:
        low, high = by_class.loc[by_class["acc"].idxmin()], by_class.loc[by_class["acc"].idxmax()]
        if high["acc"] - low["acc"] >= 0.10:
            out.append(Insight("🧩", f"{low['word_class'].capitalize()}s are your hardest class",
                               f"{_pct(low['acc'])} correct (n={low['n']}) versus {_pct(high['acc'])} for "
                               f"{high['word_class']}s (n={high['n']}). A weak-spots session targets them.", "watch"))

    # --- articles
    by_suffix = A.article_by_suffix(d)
    by_suffix = by_suffix[by_suffix["n"] >= MIN_N // 2]
    if len(by_suffix):
        worst = by_suffix.iloc[0]
        if worst["acc"] < 0.7:
            out.append(Insight("🎯", f"Article trap: nouns ending in {worst['suffix']}",
                               f"Only {_pct(worst['acc'])} correct (n={worst['n']}). Rule of thumb: "
                               f"{SUFFIX_HINT.get(worst['suffix'], 'no simple rule')}.", "watch"))
        best = by_suffix.iloc[-1]
        if best["acc"] >= 0.85 and best["suffix"] != worst["suffix"]:
            out.append(Insight("✅", f"You have {best['suffix']} nouns down",
                               f"{_pct(best['acc'])} article accuracy (n={best['n']}).", "good"))
    conf = A.article_confusion(d)
    off = conf[(conf["expected"] != conf["given"]) & (conf["n"] >= 6)]
    if len(off):
        top = off.loc[off["n"].idxmax()]
        out.append(Insight("🔀", "Most common article mix-up",
                           f"For “{top['expected']}” words you answered “{top['given']}” {_pct(top['pct'])} of the time "
                           f"({top['n']} times).", "watch"))

    # --- memory
    fc = A.forgetting_curve(d).set_index("gap")
    near = fc.reindex(["1 day", "2–3 days"]).dropna()
    far = fc.reindex(["8–14 days", "15+ days"]).dropna()
    if near["n"].sum() >= MIN_N and far["n"].sum() >= MIN_N:
        a_near, a_far = near["correct"].sum() / near["n"].sum(), far["correct"].sum() / far["n"].sum()
        if a_near - a_far >= 0.08:
            out.append(Insight("🧠", "Forgetting shows up after a week",
                               f"Recall of previously known words is {_pct(a_near)} within 3 days but {_pct(a_far)} "
                               f"after 8+ days. Short, regular reviews will beat long gaps.", "watch"))
        else:
            out.append(Insight("🧠", "Memory is holding",
                               f"Recall stays at {_pct(a_far)} after 8+ days versus {_pct(a_near)} within 3 days, "
                               f"so the review schedule is well matched to your memory.", "good"))

    # --- speed
    right, wrong = d[d["correct"] == 1]["response_s"], d[d["correct"] == 0]["response_s"]
    if len(right) >= MIN_N and len(wrong) >= MIN_N:
        out.append(Insight("⏱️", "Speed signals knowledge",
                           f"Correct answers take a median {right.median():.1f} s versus {wrong.median():.1f} s for wrong "
                           f"ones: hesitation is a good predictor of a miss."))
    ordered = d[d["correct"] == 1]
    if len(ordered) >= 3 * MIN_N:
        third = len(ordered) // 3
        early, late = ordered["response_s"].iloc[:third].median(), ordered["response_s"].iloc[-third:].median()
        if late <= 0.9 * early:
            out.append(Insight("⚡", "You are getting faster",
                               f"Median time for a correct answer fell from {early:.1f} s to {late:.1f} s "
                               f"({100 * (1 - late / early):.0f}% faster).", "good"))

    # --- frequency
    wt = A.word_table(d, states, words)
    fe = A.frequency_effect(wt)
    if fe["n"] >= 30 and abs(fe["rho"]) >= 0.15:
        direction = "Common words are easier for you" if fe["rho"] > 0 else "Rare words are easier for you"
        out.append(Insight("📚", direction, f"Spearman ρ = {fe['rho']:.2f} between word frequency and accuracy "
                                            f"over {fe['n']} words.", "info"))

    # --- time of day
    rows = []
    for label, hours in DAYPARTS:
        part = d[d["hour"].isin(list(hours))]
        if len(part) >= MIN_N:
            rows.append((label, part["correct"].mean(), len(part)))
    if len(rows) >= 2:
        best, worst = max(rows, key=lambda r: r[1]), min(rows, key=lambda r: r[1])
        if best[1] - worst[1] >= 0.08:
            out.append(Insight("🕒", f"You score best in the {best[0]}",
                               f"{_pct(best[1])} (n={best[2]}) versus {_pct(worst[1])} in the {worst[0]} (n={worst[2]}).", "info"))

    # --- workload and streak
    forecast = A.due_forecast(states, now, days=3)
    if len(states):
        out.append(Insight("🗓️", "Review workload",
                           f"{forecast['reviews'].iloc[0]} word(s) due today and {int(forecast['reviews'].iloc[1:].sum())} more "
                           f"in the next two days."))
    if k["streak"] >= 2:
        out.append(Insight("🔥", f"{k['streak']}-day streak", f"Your longest run so far is {k['best_streak']} days.", "good"))
    return out
