"""The Learn room: choose a word list, choose what to learn, then study the cards and take the test."""
from nicegui import ui

from wortschatz import config, session

from .. import components as C
from ..layout import frame
from ..state import state

DIRECTION_CHOICES = {"both": "Both ways", "de_en": "German → English", "en_de": "English → German"}
CLASS_NAMES = {"noun": "Nouns", "verb": "Verbs", "adjective": "Adjectives", "adverb": "Adverbs", "preposition": "Prepositions",
               "conjunction": "Conjunctions", "interjection": "Interjections", "other": "Other"}


def directions_from(choice: str) -> list[str]:
    return ["de_en", "en_de"] if choice == "both" else [choice]


def learn() -> None:
    with frame("learn"):
        progress = state.store.progress
        C.room_banner("learn", "Learn room", "Pick a word list, choose what to study, study the cards, then prove it in the test.")
        if state.is_demo:
            C.empty_state("science", "The demo profile is read-only", "Switch to “My diary” in the menu to learn words.")
            return

        # ------------------------------------------------------------------ 1  the word list
        def choose_list(name: str) -> None:
            state.wordlist = name
            ui.navigate.reload()

        C.step_title(1, "Choose a word list")
        options = []
        for name in state.catalog():
            words = state.words_of(name)
            options.append((name, C.pretty(name), len(session.new_words(words, progress)), f"new words · {len(words)} in the list"))
        C.list_cards("learn", options, state.list_name(), choose_list)

        words = state.words()
        fresh = session.new_words(words, progress)
        counts = session.class_counts(fresh)
        if not counts:
            C.empty_state("celebration", "You have been tested on every word in this list",
                          "Choose another word list, or revise your diary in the Test room.", "Go to the Test room", "/test")
            return
        form = {"cls": next(iter(counts)), "count": min(config.DEFAULT_COUNT, counts[next(iter(counts))]),
                "order": "frequency" if fresh["zipf"].notna().any() else "sheet", "dirs": "both"}

        def available() -> int:
            return len(fresh) if form["cls"] == "all" else counts.get(form["cls"], 0)

        @ui.refreshable
        def picker() -> None:
            with ui.row().classes("gap-3"):
                for key, number in [*counts.items(), ("all", len(fresh))]:
                    label = "Everything" if key == "all" else CLASS_NAMES.get(key, key.title())

                    def choose(k=key):
                        form["cls"] = k
                        form["count"] = min(form["count"], max(available(), 1))
                        picker.refresh()
                        controls.refresh()

                    with ui.element("div").classes("pick" + (" on" if form["cls"] == key else "")).on("click", choose):
                        ui.label(label).classes("font-bold")
                        ui.label(f"{number} new").classes("n")

        @ui.refreshable
        def controls() -> None:
            n = available()
            top = min(config.MAX_COUNT, n)
            form["count"] = max(1, min(form["count"], top))
            with ui.row().classes("items-center gap-4 w-full no-wrap"):
                ui.label("How many words?").classes("font-bold").style("min-width:9rem")
                ui.slider(min=1, max=max(top, 2), step=1, value=form["count"],
                          on_change=lambda e: form.update(count=int(e.value))).props("label-always color=primary").classes("grow")
            with ui.row().classes("items-center gap-4"):
                ui.label("Which first?").classes("font-bold").style("min-width:9rem")
                orders = {k: v for k, v in session.NEW_ORDERS.items() if k != "frequency" or fresh["zipf"].notna().any()}
                ui.select(orders, value=form["order"], on_change=lambda e: form.update(order=e.value)).props("outlined dense").classes("w-60")
            with ui.row().classes("items-center gap-4"):
                ui.label("Test me").classes("font-bold").style("min-width:9rem")
                C.segmented(DIRECTION_CHOICES, form["dirs"], lambda e: form.update(dirs=e.value))

        def start() -> None:
            chosen = session.pick_new_words(words, progress, form["cls"], form["count"], form["order"])
            if not chosen:
                ui.notify("No new words in that selection.", type="warning")
                return
            state.start(config.PHASE_LEARN, chosen, directions_from(form["dirs"]), cards=True)
            ui.navigate.to("/play")

        with ui.column().classes("card w-full gap-4"):
            C.step_title(2, "What do you want to learn?")
            picker()
            ui.separator()
            C.step_title(3, "How much?")
            controls()
            ui.button("Start learning", icon="play_arrow", on_click=start).props("unelevated no-caps size=lg color=primary").classes("self-start")
