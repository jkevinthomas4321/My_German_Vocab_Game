"""Altair chart builders. Each takes a small DataFrame produced by wortschatz.analytics.

Conventions: one palette (see theme.py), blue = correct / primary, orange = wrong, percentages on a
0-100% axis, 95% intervals drawn as whiskers, and the sample size always available in the tooltip.
"""
from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd

from wortschatz import analytics as A
from wortschatz import config

from .theme import ARTICLE_COLORS, BLUE, CLASS_COLORS, GOLD, GREEN, GREY, INK, LINE, MUTED, ORANGE, STATUS_COLORS

PCT = alt.Axis(format="%", title=None)
ARTICLES = list(config.ARTICLES)


def finish(chart, height: int = 260):
    """Shared look: quiet grid, muted labels, no frame."""
    return (chart.properties(height=height)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#EDE7DC", domainColor=LINE, tickColor=LINE,
                            labelFontSize=11, titleFontSize=11, titleFontWeight="normal")
            .configure_view(strokeWidth=0)
            .configure_legend(labelColor=INK, labelFontSize=11, orient="top", direction="horizontal", padding=4)
            .configure_title(color=INK, fontSize=13, anchor="start"))


def _tip(*pairs: tuple[str, str, str]):
    return [alt.Tooltip(field, title=title, format=fmt) if fmt else alt.Tooltip(field, title=title)
            for field, title, fmt in pairs]


# ----------------------------------------------------------------------------- activity
def activity_bars(daily: pd.DataFrame):
    full = daily.set_index("day")[["correct", "wrong"]]
    full = full.reindex(pd.date_range(full.index.min(), full.index.max(), freq="D"), fill_value=0)
    long = full.rename_axis("day").reset_index().melt("day", var_name="result", value_name="answers")
    long["result"] = long["result"].str.capitalize()
    chart = alt.Chart(long).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("day:T", title=None, axis=alt.Axis(format="%d %b", labelOverlap=True)),
        y=alt.Y("answers:Q", title="Answers"),
        color=alt.Color("result:N", title=None, scale=alt.Scale(domain=["Correct", "Wrong"], range=[BLUE, ORANGE])),
        order=alt.Order("result:N", sort="descending"),
        tooltip=_tip(("day", "Day", "%a %d %b"), ("result", "Result", ""), ("answers", "Answers", "d")))
    return finish(chart, 230)


def calendar_heatmap(grid: pd.DataFrame):
    top = max(1, int(grid["answers"].max()))
    chart = alt.Chart(grid).mark_rect(cornerRadius=3, stroke="#FBF8F3", strokeWidth=3).encode(
        x=alt.X("yearmonthdate(week):O", title=None, axis=alt.Axis(format="%b %d", labelAngle=0, labelOverlap=True, ticks=False, domain=False)),
        y=alt.Y("dow:O", title=None, sort=list(range(7)),
                axis=alt.Axis(labelExpr="['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][datum.value]", ticks=False, domain=False)),
        color=alt.Color("answers:Q", title="Answers", scale=alt.Scale(domain=[0, top], range=["#EFE8DC", "#9CC3DA", BLUE, "#14425E"]),
                        legend=alt.Legend(orient="right", gradientLength=90, titleFontSize=11)),
        tooltip=_tip(("day", "Day", "%a %d %b %Y"), ("answers", "Answers", "d")))
    return finish(chart, 210)


def session_trend(sessions: pd.DataFrame, window: int = 5):
    df = sessions.assign(n=np.arange(1, len(sessions) + 1))
    df["rolling"] = df["accuracy"].rolling(window, min_periods=1).mean()
    x = alt.X("n:Q", title="Session", axis=alt.Axis(tickMinStep=1, format="d"))
    dots = alt.Chart(df).mark_circle(size=70, opacity=0.4, color=BLUE).encode(
        x=x, y=alt.Y("accuracy:Q", axis=PCT, scale=alt.Scale(domain=[0, 1])),
        tooltip=_tip(("start", "Started", "%d %b %H:%M"), ("answers", "Answers", "d"), ("accuracy", "Accuracy", ".0%")))
    line = alt.Chart(df).mark_line(color=BLUE, strokeWidth=3).encode(
        x=x, y=alt.Y("rolling:Q", axis=PCT), tooltip=_tip(("rolling", f"{window}-session average", ".0%")))
    return finish(dots + line, 240)


def rolling_line(frame: pd.DataFrame, window: int):
    chart = alt.Chart(frame).mark_line(color=BLUE, strokeWidth=3).encode(
        x=alt.X("answer_no:Q", title="Answer number", axis=alt.Axis(format="d")),
        y=alt.Y("accuracy:Q", axis=PCT, scale=alt.Scale(domain=[0, 1])),
        tooltip=_tip(("answer_no", "Answer #", "d"), ("accuracy", f"Last {window} answers", ".0%")))
    return finish(chart, 220)


# ----------------------------------------------------------------------------- generic rate chart
def rate_bars(df: pd.DataFrame, label: str, sort: list[str] | str | None = "-x", color: str = BLUE):
    """Horizontal bars of accuracy with 95% Wilson whiskers; the right-hand text is the sample size."""
    data = df.assign(n_label=[f"n={n}" for n in df["n"]])
    y = alt.Y(f"{label}:N", title=None, sort=sort)
    base = alt.Chart(data).encode(y=y)
    bars = base.mark_bar(cornerRadiusEnd=4, color=color, size=18).encode(
        x=alt.X("acc:Q", axis=PCT, scale=alt.Scale(domain=[0, 1])),
        tooltip=_tip((label, "Group", ""), ("n", "Answers", "d"), ("acc", "Accuracy", ".0%"), ("lo", "95% low", ".0%"), ("hi", "95% high", ".0%")))
    whiskers = base.mark_rule(color=INK, strokeWidth=1.6).encode(x="lo:Q", x2="hi:Q")
    caps = base.mark_tick(color=INK, thickness=1.6, size=10, orient="vertical").encode(x="lo:Q") + \
        base.mark_tick(color=INK, thickness=1.6, size=10, orient="vertical").encode(x="hi:Q")
    text = base.mark_text(align="left", dx=8, color=MUTED, fontSize=11).encode(x="hi:Q", text="n_label:N")
    return finish(bars + whiskers + caps + text, max(110, 34 * len(data) + 46))


def curve_with_band(df: pd.DataFrame, x_field: str, x_title: str, order: list[str]):
    x = alt.X(f"{x_field}:O", sort=order, title=x_title, axis=alt.Axis(labelAngle=0))
    band = alt.Chart(df).mark_area(opacity=0.14, color=BLUE).encode(x=x, y=alt.Y("lo:Q", axis=PCT, scale=alt.Scale(domain=[0, 1])), y2="hi:Q")
    line = alt.Chart(df).mark_line(color=BLUE, strokeWidth=3, point=alt.OverlayMarkDef(filled=True, size=90, color=BLUE)).encode(
        x=x, y=alt.Y("acc:Q", axis=PCT),
        tooltip=_tip((x_field, x_title, ""), ("n", "Answers", "d"), ("acc", "Accuracy", ".0%"), ("lo", "95% low", ".0%"), ("hi", "95% high", ".0%")))
    return finish(band + line, 250)


def learning_curve_chart(lc: pd.DataFrame):
    return curve_with_band(lc, "label", "k-th time a word is asked", list(lc["label"]))


def forgetting_chart(fc: pd.DataFrame):
    order = [g for g in A.GAP_LABELS if g in set(fc["gap"])]
    return curve_with_band(fc, "gap", "Time since the word was last answered correctly", order)


# ----------------------------------------------------------------------------- articles
def confusion_heatmap(conf: pd.DataFrame):
    data = conf.assign(label=[f"{p:.0%}  ({n})" for p, n in zip(conf["pct"], conf["n"])])
    heat = alt.Chart(data).mark_rect(cornerRadius=6, stroke="#FBF8F3", strokeWidth=3).encode(
        x=alt.X("given:N", sort=ARTICLES, title="You answered", axis=alt.Axis(labelAngle=0, orient="top")),
        y=alt.Y("expected:N", sort=ARTICLES, title="Correct article"),
        color=alt.Color("pct:Q", legend=None, scale=alt.Scale(domain=[0, 1], range=["#F3EDE3", BLUE])),
        tooltip=_tip(("expected", "Correct", ""), ("given", "Answered", ""), ("n", "Times", "d"), ("pct", "Share of that article", ".0%")))
    text = alt.Chart(data).mark_text(fontSize=15, fontWeight="bold").encode(
        x=alt.X("given:N", sort=ARTICLES), y=alt.Y("expected:N", sort=ARTICLES), text="label:N",
        color=alt.condition(alt.datum.pct > 0.5, alt.value("white"), alt.value(INK)))
    return finish(heat + text, 230)


def suffix_gender_chart(table: pd.DataFrame):
    long = table.melt(id_vars=["suffix", "nouns"], value_vars=ARTICLES, var_name="article", value_name="count")
    order = list(table["suffix"])
    chart = alt.Chart(long).mark_bar().encode(
        y=alt.Y("suffix:N", sort=order, title=None),
        x=alt.X("count:Q", stack="normalize", axis=alt.Axis(format="%", title="Share of nouns with this ending")),
        color=alt.Color("article:N", title=None, scale=alt.Scale(domain=ARTICLES, range=[ARTICLE_COLORS[a] for a in ARTICLES])),
        tooltip=_tip(("suffix", "Ending", ""), ("article", "Article", ""), ("count", "Nouns", "d"), ("nouns", "Total with ending", "d")))
    return finish(chart, max(160, 30 * len(table) + 50))


# ----------------------------------------------------------------------------- vocabulary state
def funnel_bars(funnel: pd.DataFrame):
    chart = alt.Chart(funnel).mark_bar(cornerRadiusEnd=5, size=26).encode(
        y=alt.Y("status:N", sort=list(funnel["status"]), title=None),
        x=alt.X("words:Q", title="Words"),
        color=alt.Color("status:N", legend=None, scale=alt.Scale(domain=list(STATUS_COLORS), range=list(STATUS_COLORS.values()))),
        tooltip=_tip(("status", "Status", ""), ("words", "Words", "d")))
    labels = alt.Chart(funnel).mark_text(align="left", dx=6, color=INK, fontWeight="bold").encode(
        y=alt.Y("status:N", sort=list(funnel["status"])), x="words:Q", text="words:Q")
    return finish(chart + labels, 190)


def forecast_bars(forecast: pd.DataFrame):
    data = forecast.assign(label=[("Today" if i == 0 else d.strftime("%a %d")) for i, d in enumerate(forecast["day"])])
    chart = alt.Chart(data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=GOLD).encode(
        x=alt.X("label:N", sort=list(data["label"]), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("reviews:Q", title="Reviews due", axis=alt.Axis(tickMinStep=1, format="d")),
        tooltip=_tip(("day", "Day", "%a %d %b"), ("reviews", "Reviews due", "d")))
    labels = alt.Chart(data).mark_text(dy=-8, color=INK, fontWeight="bold").encode(
        x=alt.X("label:N", sort=list(data["label"])), y="reviews:Q", text="reviews:Q")
    return finish(chart + labels, 200)


def growth_lines(growth: pd.DataFrame):
    chart = alt.Chart(growth).mark_line(strokeWidth=3, interpolate="step-after").encode(
        x=alt.X("day:T", title=None, axis=alt.Axis(format="%d %b", labelOverlap=True)),
        y=alt.Y("words:Q", title="Words"),
        color=alt.Color("metric:N", title=None, scale=alt.Scale(domain=["Words seen", "Words mastered"], range=[BLUE, GREEN])),
        tooltip=_tip(("day", "Day", "%d %b"), ("metric", "Metric", ""), ("words", "Words", "d")))
    return finish(chart, 230)


# ----------------------------------------------------------------------------- speed and habits
def rt_histogram(times: pd.DataFrame):
    colors = alt.Scale(domain=["Correct", "Wrong"], range=[BLUE, ORANGE])
    hist = alt.Chart(times).mark_bar(opacity=0.6, binSpacing=1).encode(
        x=alt.X("response_s:Q", bin=alt.Bin(maxbins=28), title="Response time (seconds, capped at 20)"),
        y=alt.Y("count():Q", stack=None, title="Answers"),
        color=alt.Color("result:N", title=None, scale=colors))
    medians = alt.Chart(times).mark_rule(strokeWidth=2.5, strokeDash=[5, 3]).encode(
        x="median(response_s):Q", color=alt.Color("result:N", legend=None, scale=colors))
    return finish(hist + medians, 240)


def rt_trend_chart(trend: pd.DataFrame):
    line = alt.Chart(trend).mark_line(color=BLUE, strokeWidth=3, point=alt.OverlayMarkDef(filled=True, size=60, color=BLUE)).encode(
        x=alt.X("day:T", title=None, axis=alt.Axis(format="%d %b", labelOverlap=True)),
        y=alt.Y("median_s:Q", title="Median seconds (correct answers)", scale=alt.Scale(zero=False)),
        tooltip=_tip(("day", "Day", "%d %b"), ("median_s", "Median seconds", ".1f"), ("n", "Correct answers", "d")))
    return finish(line, 230)


def hour_chart(hours: pd.DataFrame):
    chart = alt.Chart(hours).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("hour:O", title="Hour of day", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("n:Q", title="Answers"),
        color=alt.Color("acc:Q", title="Accuracy", scale=alt.Scale(domain=[0.3, 1.0], range=["#CFE0EA", BLUE]), legend=alt.Legend(format="%", orient="bottom", gradientLength=140)),
        tooltip=_tip(("hour", "Hour", "d"), ("n", "Answers", "d"), ("acc", "Accuracy", ".0%")))
    return finish(chart, 230)


def scatter_frequency(wt: pd.DataFrame):
    data = wt.dropna(subset=["zipf"])
    points = alt.Chart(data).mark_circle(color=BLUE, opacity=0.55).encode(
        x=alt.X("zipf:Q", title="Word frequency (Zipf: higher = more common)", scale=alt.Scale(zero=False)),
        y=alt.Y("accuracy:Q", axis=PCT, scale=alt.Scale(domain=[0, 1.02])),
        size=alt.Size("attempts:Q", legend=None, scale=alt.Scale(range=[40, 320])),
        tooltip=_tip(("german", "German", ""), ("english", "English", ""), ("zipf", "Zipf", ".2f"), ("attempts", "Answers", "d"), ("accuracy", "Accuracy", ".0%")))
    trend = (alt.Chart(data).transform_regression("zipf", "accuracy").mark_line(color=ORANGE, strokeWidth=3)
             .encode(x=alt.X("zipf:Q", scale=alt.Scale(zero=False)), y=alt.Y("accuracy:Q", axis=PCT)))
    return finish(points + trend, 280)


# ----------------------------------------------------------------------------- the dataset itself
def class_mix(words: pd.DataFrame):
    counts = words["word_class"].value_counts().rename_axis("word_class").reset_index(name="words")
    chart = alt.Chart(counts).mark_bar(cornerRadiusEnd=4, size=20).encode(
        y=alt.Y("word_class:N", sort="-x", title=None), x=alt.X("words:Q", title="Words"),
        color=alt.Color("word_class:N", legend=None, scale=alt.Scale(domain=list(CLASS_COLORS), range=list(CLASS_COLORS.values()))),
        tooltip=_tip(("word_class", "Class", ""), ("words", "Words", "d")))
    labels = alt.Chart(counts).mark_text(align="left", dx=6, color=INK).encode(
        y=alt.Y("word_class:N", sort="-x"), x="words:Q", text="words:Q")
    return finish(chart + labels, max(150, 32 * len(counts) + 40))


def zipf_histogram(words: pd.DataFrame):
    data = words.dropna(subset=["zipf"])
    chart = alt.Chart(data).mark_bar(binSpacing=1).encode(
        x=alt.X("zipf:Q", bin=alt.Bin(step=0.25), title="Zipf frequency (higher = more common)"),
        y=alt.Y("count():Q", title="Words"),
        color=alt.Color("word_class:N", title=None, scale=alt.Scale(domain=list(CLASS_COLORS), range=list(CLASS_COLORS.values()))),
        tooltip=_tip(("word_class", "Class", ""), ("count()", "Words", "d")))
    return finish(chart, 260)
