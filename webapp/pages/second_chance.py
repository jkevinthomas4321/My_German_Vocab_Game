from nicegui import ui

from wortschatz import config, session

from .. import components as C
from ..layout import frame
from ..state import state
from .learn import CLASS_NAMES, DIRECTION_CHOICES, directions_from

GERMAN_SLOT = """<q-td :props="props"><span v-if="props.row.article" :class="'art art-' + props.row.article">{{ props.row.article }}</span>
<b class="serif" style="font-size:1.1rem"> {{ props.row.german }}</b></q-td>"""


def forms_text(word: dict) -> str:
    if word["word_class"] == "verb" and word["past_tense"]:
        return f'{word["past_tense"]} · {word["perfect_tense"]}'
    return f'Plural: {word["plural"]}' if word["plural"] else ""


def word_rows(words: list[dict], extra) -> list[dict]:
    return [{"id": w["word_id"], "article": w["article"], "german": w["german"], "english": w["english"],
             "forms": forms_text(w), **extra(w)} for w in words]


def second_chance() -> None:
    with frame("second"):
        ui.label("Second chance").classes("text-3xl font-bold serif")
        ui.label("Words you missed wait here. Study them again, then pass a re-test to move them into your diary.").classes("muted")
        words = session.pick_second_chance(state.store.progress)
        if not words:
            C.empty_state("task_alt", "Nothing to repeat", "Every word you have been tested on is in your diary.", "Learn new words", "/learn")
            return

        form = {"count": min(config.DEFAULT_COUNT, len(words)), "dirs": "both"}

        def start() -> None:
            chosen = session.pick_second_chance(state.store.progress, form["count"])
            state.start(config.PHASE_RETEST, chosen, directions_from(form["dirs"]), cards=True)
            ui.navigate.to("/play")

        with ui.column().classes("card w-full gap-3"):
            with ui.row().classes("items-center gap-4 w-full no-wrap"):
                ui.label("How many?").classes("font-bold").style("min-width:7rem")
                ui.slider(min=1, max=max(min(config.MAX_COUNT, len(words)), 2), step=1, value=form["count"],
                          on_change=lambda e: form.update(count=int(e.value))).props("label-always color=primary").classes("grow")
            with ui.row().classes("items-center gap-4"):
                ui.label("Test me").classes("font-bold").style("min-width:7rem")
                C.segmented(DIRECTION_CHOICES, "both", lambda e: form.update(dirs=e.value))
            ui.label("The words you missed most often come first.").classes("muted text-sm")
            if state.is_demo:
                ui.label("The demo profile is read-only.").classes("muted")
            else:
                ui.button("Review & re-test", icon="replay", on_click=start).props("unelevated no-caps size=lg color=primary").classes("self-start")

        rows = word_rows(words, lambda w: {"fails": w["fails"], "since": f'{w["last_tested"]:%d %b}' if w["last_tested"] else ""})
        columns = [{"name": "german", "label": "German", "field": "german", "align": "left", "sortable": True},
                   {"name": "english", "label": "English", "field": "english", "align": "left", "sortable": True},
                   {"name": "forms", "label": "Forms", "field": "forms", "align": "left"},
                   {"name": "fails", "label": "Missed", "field": "fails", "sortable": True},
                   {"name": "since", "label": "Last tested", "field": "since"}]
        table = ui.table(columns=columns, rows=rows, row_key="id", pagination=15).classes("w-full")
        table.add_slot("body-cell-german", GERMAN_SLOT)
