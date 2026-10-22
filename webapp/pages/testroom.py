"""The Test room: revise the words in your diary. A word you miss goes back to the second-chance room."""
from nicegui import ui

from wortschatz import config, session

from .. import components as C
from ..layout import frame
from ..state import state
from .learn import CLASS_NAMES, DIRECTION_CHOICES, directions_from
from .second_chance import source_options


def test_room() -> None:
    with frame("test"):
        C.room_banner("test", "Test room", "Revision: test yourself on the words in your diary. Miss one and it goes back to the second-chance room.")
        diary = state.store.progress.frame(config.STATUS_DIARY)
        if diary.empty:
            C.empty_state("menu_book", "Your diary is empty", "Learn some words and pass the test, then come back to revise them.",
                          "Go to the Learn room", "/learn")
            return

        form = {"source": "all", "cls": "all", "count": config.DEFAULT_COUNT, "order": "stale", "dirs": "both"}

        def source_ids():
            return state.list_ids(None if form["source"] == "all" else form["source"])

        def available() -> dict[str, int]:
            """Diary words per word type for the chosen word list."""
            ids = source_ids()
            subset = diary if ids is None else diary[diary["word_id"].isin(ids)]
            return session.class_counts(subset) if len(subset) else {}

        def start() -> None:
            chosen = session.pick_diary(state.store.progress, form["cls"], form["count"], form["order"], word_ids=source_ids())
            if not chosen:
                ui.notify("No diary words in that selection.", type="warning")
                return
            state.start(config.PHASE_DIARY, chosen, directions_from(form["dirs"]), cards=False)
            ui.navigate.to("/play")

        @ui.refreshable
        def body() -> None:
            C.step_title(1, "Choose a word list")

            def select(value: str) -> None:
                form["source"], form["cls"] = value, "all"
                body.refresh()

            C.list_cards("test", source_options(set(diary["word_id"]), "My whole diary", "diary words from this list"), form["source"], select)
            counts = available()
            total = sum(counts.values())
            with ui.column().classes("card w-full gap-3"):
                C.step_title(2, "What do you want to be tested on?")
                if not total:
                    ui.label("No diary words from that list yet.").classes("muted")
                    return
                with ui.row().classes("gap-3"):
                    for key, number in [*counts.items(), ("all", total)]:
                        label = "Everything" if key == "all" else CLASS_NAMES.get(key, key.title())

                        def choose(k=key):
                            form["cls"] = k
                            body.refresh()

                        with ui.element("div").classes("pick" + (" on" if form["cls"] == key else "")).on("click", choose):
                            ui.label(label).classes("font-bold")
                            ui.label(f"{number} in the diary").classes("n")
                top = max(min(config.MAX_COUNT, total if form["cls"] == "all" else counts.get(form["cls"], 1)), 1)
                form["count"] = max(1, min(form["count"], top))
                ui.separator()
                C.step_title(3, "How much?")
                with ui.row().classes("items-center gap-4 w-full no-wrap"):
                    ui.label("How many words?").classes("font-bold").style("min-width:9rem")
                    ui.slider(min=1, max=max(top, 2), step=1, value=form["count"],
                              on_change=lambda e: form.update(count=int(e.value))).props("label-always color=primary").classes("grow")
                with ui.row().classes("items-center gap-4"):
                    ui.label("Which first?").classes("font-bold").style("min-width:9rem")
                    ui.select(session.DIARY_ORDERS, value=form["order"], on_change=lambda e: form.update(order=e.value)).props("outlined dense").classes("w-60")
                with ui.row().classes("items-center gap-4"):
                    ui.label("Test me").classes("font-bold").style("min-width:9rem")
                    C.segmented(DIRECTION_CHOICES, form["dirs"], lambda e: form.update(dirs=e.value))
                if state.is_demo:
                    ui.label("The demo profile is read-only.").classes("muted")
                else:
                    ui.button("Start the revision test", icon="quiz", on_click=start).props("unelevated no-caps size=lg color=primary").classes("self-start")

        body()
