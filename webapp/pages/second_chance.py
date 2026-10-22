"""The Second-chance room: words you missed wait here until you pass a re-test."""
from nicegui import ui

from wortschatz import config, session

from .. import components as C
from ..layout import frame
from ..state import state
from .learn import DIRECTION_CHOICES, directions_from

GERMAN_SLOT = """<q-td :props="props"><span v-if="props.row.article" :class="'art art-' + props.row.article">{{ props.row.article }}</span>
<b class="serif" style="font-size:1.1rem"> {{ props.row.german }}</b></q-td>"""


def forms_text(word: dict) -> str:
    if word["word_class"] == "verb" and word["past_tense"]:
        return f'{word["past_tense"]} · {word["perfect_tense"]}'
    return f'Plural: {word["plural"]}' if word["plural"] else ""


def word_rows(words: list[dict], extra) -> list[dict]:
    return [{"id": w["word_id"], "article": w["article"], "german": w["german"], "english": w["english"],
             "forms": forms_text(w), **extra(w)} for w in words]


def source_options(frame_ids: set[str], all_label: str, caption: str) -> list[tuple]:
    """Cards for 'all my words' plus each word list, with how many of the player's words each contains."""
    options = [("all", all_label, len(frame_ids), "from every list")]
    for name in state.catalog():
        options.append((name, C.pretty(name), len(frame_ids & set(state.words_of(name)["word_id"])), caption))
    return options


def second_chance() -> None:
    with frame("second"):
        C.room_banner("second", "Second-chance room", "Words you missed wait here. Study them again, then pass a re-test to send them to your diary.")
        everything = session.pick_second_chance(state.store.progress)
        if not everything:
            C.empty_state("task_alt", "Nothing to repeat", "Every word you have been tested on is in your diary.", "Go to the Learn room", "/learn")
            return

        form = {"source": "all", "count": min(config.DEFAULT_COUNT, len(everything)), "dirs": "both"}

        def chosen_ids():
            return state.list_ids(None if form["source"] == "all" else form["source"])

        def start() -> None:
            chosen = session.pick_second_chance(state.store.progress, form["count"], word_ids=chosen_ids())
            if not chosen:
                ui.notify("No second-chance words from that list.", type="warning")
                return
            state.start(config.PHASE_RETEST, chosen, directions_from(form["dirs"]), cards=True)
            ui.navigate.to("/play")

        @ui.refreshable
        def body() -> None:
            ids = {w["word_id"] for w in session.pick_second_chance(state.store.progress, word_ids=chosen_ids())}
            C.step_title(1, "Choose a word list")

            def select(value: str) -> None:
                form["source"] = value
                form["count"] = max(1, min(form["count"], max(len(session.pick_second_chance(state.store.progress, word_ids=chosen_ids())), 1)))
                body.refresh()

            all_ids = {w["word_id"] for w in everything}
            C.list_cards("second", source_options(all_ids, "All my second-chance words", "waiting from this list"), form["source"], select)
            with ui.column().classes("card w-full gap-3"):
                C.step_title(2, "How many?")
                top = max(min(config.MAX_COUNT, len(ids)), 1)
                form["count"] = max(1, min(form["count"], top))
                with ui.row().classes("items-center gap-4 w-full no-wrap"):
                    ui.label("Words").classes("font-bold").style("min-width:7rem")
                    ui.slider(min=1, max=max(top, 2), step=1, value=form["count"],
                              on_change=lambda e: form.update(count=int(e.value))).props("label-always color=primary").classes("grow")
                with ui.row().classes("items-center gap-4"):
                    ui.label("Test me").classes("font-bold").style("min-width:7rem")
                    C.segmented(DIRECTION_CHOICES, form["dirs"], lambda e: form.update(dirs=e.value))
                ui.label("The words you missed most often come first.").classes("muted text-sm")
                if state.is_demo:
                    ui.label("The demo profile is read-only.").classes("muted")
                else:
                    ui.button("Review & re-test", icon="replay", on_click=start).props("unelevated no-caps size=lg color=primary").classes("self-start")

        body()

        rows = word_rows(everything, lambda w: {"fails": w["fails"], "since": f'{w["last_tested"]:%d %b}' if w["last_tested"] else ""})
        columns = [{"name": "german", "label": "German", "field": "german", "align": "left", "sortable": True},
                   {"name": "english", "label": "English", "field": "english", "align": "left", "sortable": True},
                   {"name": "forms", "label": "Forms", "field": "forms", "align": "left"},
                   {"name": "fails", "label": "Missed", "field": "fails", "sortable": True},
                   {"name": "since", "label": "Last tested", "field": "since"}]
        ui.label("Waiting in this room").classes("text-lg font-bold")
        table = ui.table(columns=columns, rows=rows, row_key="id", pagination=15).classes("w-full")
        table.add_slot("body-cell-german", GERMAN_SLOT)
