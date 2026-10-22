"""The Living room: your diary, the words that stay with you."""
from nicegui import ui

from wortschatz import config, session, wordlist

from .. import components as C
from ..layout import frame
from ..state import state
from .learn import CLASS_NAMES
from .second_chance import GERMAN_SLOT, word_rows

ACTIONS_SLOT = """<q-td :props="props"><q-btn flat round dense icon="delete_outline" color="grey-7"
 @click="() => $parent.$emit('remove', props.row)"><q-tooltip>Remove from the diary</q-tooltip></q-btn></q-td>"""


def diary() -> None:
    with frame("diary"):
        progress = state.store.progress
        diary_frame = progress.frame(config.STATUS_DIARY)
        C.room_banner("stay", "Living room", "Your diary: only words you have passed live here. Revise them in the Test room.")
        if diary_frame.empty:
            C.empty_state("menu_book", "Your diary is empty", "Learn some words and pass the test to fill it.", "Go to the Learn room", "/learn")
            return

        counts = session.class_counts(diary_frame)
        C.tiles([("Words in the diary", str(len(diary_frame)), ""), *[(CLASS_NAMES.get(c, c.title()), str(n), "") for c, n in list(counts.items())[:3]]])
        with ui.row().classes("gap-3"):
            ui.button("Revise them in the Test room", icon="quiz", on_click=lambda: ui.navigate.to("/test")).props("unelevated no-caps color=primary")

        rows = word_rows(diary_frame.to_dict("records"), lambda w: {
            "tests": w["tests"], "streak": w["streak"],
            "last": f'{w["last_tested"]:%d %b %Y}' if w["last_tested"] is not None and w["last_tested"] == w["last_tested"] else ""})
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
