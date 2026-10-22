import pandas as pd
from nicegui import ui

from wortschatz import stats

from .. import charts
from .. import components as C
from ..layout import frame
from ..state import state

TONE = {"good": "#2F5D50", "watch": "#A4553D", "info": "#35506B"}


def chart_card(title: str, caption: str, options: dict, height: int = 280) -> None:
    with ui.column().classes("card grow gap-1").style("flex:1;min-width:300px"):
        ui.label(title).classes("text-lg font-bold")
        ui.label(caption).classes("muted text-sm")
        ui.echart(options).style(f"height:{height}px;width:100%")


def finding_card(item: dict) -> None:
    with ui.column().classes("card-flat grow gap-1").style(f"border-left:6px solid {TONE[item['tone']]};flex:1"):
        with ui.row().classes("items-center gap-2"):
            ui.icon(item["icon"]).style(f"color:{TONE[item['tone']]}")
            ui.label(item["title"]).classes("font-bold")
        ui.label(item["text"]).classes("text-sm")


def stats_page() -> None:
    with frame("stats"):
        progress, attempts = state.store.progress, state.store.attempts()
        outcomes = stats.word_outcomes(attempts)
        ui.label("Stats").classes("text-3xl font-bold serif")
        ui.label("Everything here is computed from your answers. Rates show their 95% confidence interval and sample size.").classes("muted")
        if outcomes.empty:
            C.empty_state("insights", "No tests yet", "Learn some words and take a test, or open the demo profile to see the statistics.",
                          "Learn new words", "/learn")
            return

        k = stats.kpis(progress, attempts)
        rate = f"{100 * k['first_try_rate']:.0f}%" if k["first_try_rate"] == k["first_try_rate"] else "–"
        C.tiles([("Level", str(state.level().number), f"{state.level().title} · {state.total_points()} points"),
                 ("Diary", str(k["diary"]), "words passed"), ("Second chance", str(k["second_chance"]), "to repeat"),
                 ("Word tests", str(k["tests"]), f"{k['answers']} answers"), ("First-try pass rate", rate, "new words"),
                 ("Streak", f"{k['streak']} d", f"best {k['best_streak']} d")])

        found = stats.findings(progress, attempts)
        if found:
            ui.label("What the data says").classes("text-xl font-bold serif")
            for start in range(0, min(len(found), 6), 3):
                with ui.row().classes("w-full gap-3 flex-wrap"):
                    for item in found[start:start + 3]:
                        finding_card(item)

        growth = stats.diary_growth(attempts)
        with ui.row().classes("w-full gap-4 flex-wrap items-stretch"):
            chart_card("Diary growth", "Words in the diary at the end of each day.", charts.diary_growth(growth))
            chart_card("Words tested per day", "Passed and failed word tests.", charts.daily_tests(stats.daily_activity(outcomes)))

        with ui.column().classes("card w-full gap-1"):
            ui.label("Activity").classes("text-lg font-bold")
            ui.echart(charts.calendar(stats.calendar_counts(outcomes), outcomes["ts"].max(), weeks=min(26, max(8, (outcomes["ts"].max() - outcomes["ts"].min()).days // 7 + 3)))).style("height:190px;width:100%")

        phase, by_class, directions = stats.pass_rate_by_phase(outcomes), stats.pass_rate_by_class(outcomes), stats.direction_accuracy(attempts)
        with ui.row().classes("w-full gap-4 flex-wrap items-stretch"):
            chart_card("Pass rate by stage", "A word passes when every question about it is right.",
                       charts.rate_with_whiskers(phase["label"], phase["rate"], phase["lo"], phase["hi"], phase["n"]))
            chart_card("Pass rate by word type", "Which kind of word is hardest?",
                       charts.rate_with_whiskers(by_class["word_class"], by_class["rate"], by_class["lo"], by_class["hi"], by_class["n"], "#1B2A41"))
        gaps, journey = stats.revision_by_gap(outcomes), stats.second_chance_journey(outcomes, progress)
        with ui.row().classes("w-full gap-4 flex-wrap items-stretch"):
            chart_card("Which direction is harder?", "Share of questions answered correctly.",
                       charts.rate_with_whiskers(directions["label"], directions["rate"], directions["lo"], directions["hi"], directions["n"], charts.GREEN))
            if len(gaps):
                chart_card("Do diary words fade?", "Revision pass rate by days since the word was last tested.",
                           charts.line_with_band(gaps["gap"], gaps["rate"], gaps["lo"], gaps["hi"], gaps["n"]))
            if len(journey):
                chart_card("Second-chance journey", "Re-tests needed by words that failed their first test.",
                           charts.counts_bars(list(journey["retests"]), list(journey["words"])))

        hardest = stats.hardest_words(outcomes)
        if len(hardest):
            ui.label("Hardest words").classes("text-xl font-bold serif")
            rows = [{"german": r.german, "english": r.english, "word_class": r.word_class, "tests": int(r.tests), "fails": int(r.fails),
                     "rate": f"{100 * r.fail_rate:.0f}%"} for r in hardest.itertuples()]
            columns = [{"name": c, "label": label, "field": c, "align": "left"} for c, label in
                       [("german", "German"), ("english", "English"), ("word_class", "Type"), ("tests", "Tests"), ("fails", "Failed"), ("rate", "Fail rate")]]
            ui.table(columns=columns, rows=rows, row_key="german").classes("w-full")
