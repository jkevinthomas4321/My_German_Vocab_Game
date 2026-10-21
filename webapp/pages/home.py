from nicegui import ui

from wortschatz import config, stats

from .. import components as C
from ..layout import frame
from ..state import state


def stage_card(title: str, number: int, caption: str, color: str, button: str, target: str, text: str) -> None:
    with ui.column().classes("card stage grow").style(f"--stage:{color}"):
        ui.label(title).classes("title")
        ui.label(str(number)).classes("num")
        ui.label(caption).classes("muted text-sm")
        ui.label(text).classes("text-sm").style("flex:1")
        ui.button(button, on_click=lambda: ui.navigate.to(target)).props("unelevated no-caps color=primary").classes("self-start")


def home() -> None:
    with frame("home"):
        counts = state.counts()
        kpi = stats.kpis(state.store.progress, state.store.attempts())
        list_name = (state.list_name() or "").replace("_", " ")

        with ui.element("div").classes("hero w-full"):
            ui.html("<h1>Guten Tag!</h1><p>Learn a few words, pass the test, and build your own diary of words you really know.</p>")

        with ui.row().classes("w-full gap-4 items-stretch max-md:flex-wrap no-wrap"):
            stage_card("Learn new words", counts["new"], f"new words in “{list_name}”", "#2A6FDB", "Start learning", "/learn",
                       "Pick nouns, verbs or adjectives and how many. Study the cards, then take the test.")
            stage_card("Second chance", counts["second"], "words to learn properly", "#E3A008", "Review & re-test", "/second-chance",
                       "Words you missed wait here. Study them again and pass a re-test to move them to your diary.")
            stage_card("My diary", counts["diary"], "words you have passed", "#2F9E6B", "Open the diary", "/diary",
                       "Only words that passed a test live here. Take a revision test whenever you like.")

        with ui.row().classes("w-full gap-4 items-stretch max-md:flex-wrap no-wrap"):
            with ui.column().classes("card grow gap-3").style("flex:2"):
                ui.label("How the game works").classes("text-lg font-bold")
                steps = [("Learn", "Study the cards for the words you picked, in both directions."),
                         ("Test", "Type the translation German → English and English → German."),
                         ("Diary or second chance", "Every answer right: the word enters your diary. Any answer wrong: it goes to the second-chance list."),
                         ("Revise", "Test yourself on the diary any time. A word you miss goes back to second chance.")]
                for i, (title, text) in enumerate(steps, 1):
                    with ui.element("div").classes("step"):
                        ui.label(str(i)).classes("dot")
                        ui.html(f"<b>{C.esc(title)}</b><br><span class='muted'>{C.esc(text)}</span>")
            with ui.column().classes("card grow gap-2").style("flex:1"):
                ui.label("Today").classes("text-lg font-bold")
                C.tiles([("Words tested", str(kpi["today_words"]), "today")])
                C.tiles([("Streak", f"{kpi['streak']} d", f"best {kpi['best_streak']} d")])
                rate = f"{100 * kpi['first_try_rate']:.0f}%" if kpi["first_try_rate"] == kpi["first_try_rate"] else "–"
                C.tiles([("First-try pass rate", rate, "words passed on their first test")])
