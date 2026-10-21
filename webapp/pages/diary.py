from nicegui import ui

from wortschatz import config, session, wordlist

from .. import components as C
from ..layout import frame
from ..state import state
from .learn import CLASS_NAMES, DIRECTION_CHOICES, directions_from
from .second_chance import GERMAN_SLOT, forms_text, word_rows

ACTIONS_SLOT = """<q-td :props="props"><q-btn flat round dense icon="delete_outline" color="grey-7"
 @click="() => $parent.$emit('remove', props.row)"><q-tooltip>Remove from the diary</q-tooltip></q-btn></q-td>"""


def diary() -> None:
    with frame("diary"):
        progress = state.store.progress
        diary_frame = progress.frame(config.STATUS_DIARY)
        ui.label("My diary").classes("text-3xl font-bold serif")
        ui.label("Only words you passed a test on are in here. Revise them whenever you like. A word you miss goes back to second chance.").classes("muted")
        if diary_frame.empty:
            C.empty_state("menu_book", "Your diary is empty", "Learn some words and pass the test to fill it.", "Learn new words", "/learn")
            return

        counts = session.class_counts(diary_frame)
        C.tiles([("Words in the diary", str(len(diary_frame)), ""), *[(CLASS_NAMES.get(c, c.title()), str(n), "") for c, n in list(counts.items())[:3]]])

        # ------------------------------------------------------------------ revision test
        form = {"cls": "all", "count": min(config.DEFAULT_COUNT, len(diary_frame)), "order": "stale", "dirs": "both"}

        @ui.refreshable
        def revise_controls() -> None:
            n = len(diary_frame) if form["cls"] == "all" else counts.get(form["cls"], 0)
            top = max(min(config.MAX_COUNT, n), 1)
            form["count"] = max(1, min(form["count"], top))
            with ui.row().classes("items-center gap-4"):
                ui.label("Words from").classes("font-bold").style("min-width:8rem")
                options = {"all": f"Everything ({len(diary_frame)})", **{c: f"{CLASS_NAMES.get(c, c.title())} ({k})" for c, k in counts.items()}}
                ui.select(options, value=form["cls"], on_change=lambda e: (form.update(cls=e.value), revise_controls.refresh())
                          ).props("outlined dense").classes("w-60")
            with ui.row().classes("items-center gap-4 w-full no-wrap"):
                ui.label("How many?").classes("font-bold").style("min-width:8rem")
                ui.slider(min=1, max=max(top, 2), step=1, value=form["count"],
                          on_change=lambda e: form.update(count=int(e.value))).props("label-always color=primary").classes("grow")
            with ui.row().classes("items-center gap-4"):
                ui.label("Which first?").classes("font-bold").style("min-width:8rem")
                ui.select(session.DIARY_ORDERS, value=form["order"], on_change=lambda e: form.update(order=e.value)).props("outlined dense").classes("w-60")
            with ui.row().classes("items-center gap-4"):
                ui.label("Test me").classes("font-bold").style("min-width:8rem")
                C.segmented(DIRECTION_CHOICES, form["dirs"], lambda e: form.update(dirs=e.value))

        def start() -> None:
            chosen = session.pick_diary(state.store.progress, form["cls"], form["count"], form["order"])
            if not chosen:
                ui.notify("No diary words in that selection.", type="warning")
                return
            state.start(config.PHASE_DIARY, chosen, directions_from(form["dirs"]), cards=False)
            ui.navigate.to("/play")

        with ui.column().classes("card w-full gap-3"):
            ui.label("Revision test").classes("text-lg font-bold")
            revise_controls()
            if state.is_demo:
                ui.label("The demo profile is read-only.").classes("muted")
            else:
                ui.button("Start the revision test", icon="quiz", on_click=start).props("unelevated no-caps size=lg color=primary").classes("self-start")

        # ------------------------------------------------------------------ the list
        rows = word_rows(diary_frame.to_dict("records"), lambda w: {
            "tests": w["tests"], "streak": w["streak"], "last": f'{w["last_tested"]:%d %b %Y}' if w["last_tested"] is not None and w["last_tested"] == w["last_tested"] else ""})
        columns = [{"name": "german", "label": "German", "field": "german", "align": "left", "sortable": True},
                   {"name": "english", "label": "English", "field": "english", "align": "left", "sortable": True},
                   {"name": "forms", "label": "Forms", "field": "forms", "align": "left"},
                   {"name": "streak", "label": "Passed in a row", "field": "streak", "sortable": True},
                   {"name": "tests", "label": "Tests", "field": "tests", "sortable": True},
                   {"name": "last", "label": "Last tested", "field": "last"},
                   {"name": "actions", "label": "", "field": "id"}]
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("All diary words").classes("text-lg font-bold")
            search = ui.input(placeholder="Search…").props("outlined dense clearable").classes("w-64")
            with ui.row().classes("gap-2"):
                ui.button("CSV", icon="download", on_click=lambda: ui.download.content(
                    wordlist.to_csv_bytes(diary_frame), "my_diary.csv"), color=None).props("outline no-caps dense")
                ui.button("Excel", icon="download", on_click=lambda: ui.download.content(
                    wordlist.to_excel_bytes(diary_frame), "my_diary.xlsx"), color=None).props("outline no-caps dense")
        table = ui.table(columns=columns, rows=rows, row_key="id", pagination=15).classes("w-full")
        table.add_slot("body-cell-german", GERMAN_SLOT)
        table.add_slot("body-cell-actions", ACTIONS_SLOT)
        search.bind_value(table, "filter")

        def remove(event) -> None:
            row = event.args

            def confirm() -> None:
                state.store.remove_word(row["id"])
                dialog.close()
                ui.navigate.reload()

            with ui.dialog() as dialog, ui.card():
                ui.label(f"Remove “{row['german']}” from the diary?").classes("text-lg font-bold")
                ui.label("It will be treated as a new word and can be learned again.").classes("muted")
                with ui.row().classes("justify-end w-full"):
                    ui.button("Cancel", on_click=dialog.close).props("flat no-caps")
                    ui.button("Remove", on_click=confirm).props("unelevated no-caps color=negative")
            dialog.open()

        if not state.is_demo:
            table.on("remove", remove)
