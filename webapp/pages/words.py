"""Word list page: choose the sheet to learn from, load your own CSV/Excel file, see what is in it."""
import io

import pandas as pd
from nicegui import events, ui

from wortschatz import config, session, wordlist

from .. import components as C
from ..layout import frame
from ..state import state
from .learn import CLASS_NAMES
from .second_chance import GERMAN_SLOT, forms_text

TEMPLATE = pd.DataFrame({
    "word_class": ["noun", "noun", "verb", "adjective"], "english": ["apple", "house", "to read", "big"],
    "article": ["der", "das", "", ""], "german": ["Apfel", "Haus", "lesen", "groß"], "plural": ["Äpfel", "Häuser", "", ""],
    "past_tense": ["", "", "las", ""], "perfect_tense": ["", "", "hat gelesen", ""]})


HEADER_LINE = ",".join(config.WORD_COLUMNS)

# (column, required?, what it holds, example)
EXPECTED_COLUMNS = [
    ("english", "required", "The English meaning. Several accepted answers can be separated by / or ;", "to read / to study"),
    ("german", "required", "The German word, without its article (an article typed in this cell is split off automatically)", "lesen"),
    ("word_class", "optional", "noun, verb, adjective, adverb, preposition, conjunction, interjection or other (default: other)", "verb"),
    ("article", "optional", "der, die or das. Nouns are tested with their article", "der"),
    ("plural", "optional", "The plural, shown on noun cards", "Äpfel"),
    ("past_tense", "optional", "Präteritum. Verbs with both tenses are tested on all three forms", "las"),
    ("perfect_tense", "optional", "Perfekt, with its helper verb", "hat gelesen"),
    ("zipf", "optional", "Word frequency (about 1 to 8). If present, common words are offered first", "5.2"),
]


def columns_help() -> None:
    """What a file needs: the exact header row, one line per column, and the spellings that are also accepted."""
    ui.label("Columns your file needs").classes("text-lg font-bold")
    ui.label("One word per row, any number of rows (1,000 is fine). The first row must be the header. CSV (comma or semicolon) or Excel .xlsx (first sheet). "
             "Save CSV files as UTF-8 so ä ö ü ß survive.").classes("muted text-sm")
    with ui.row().classes("items-center gap-2 w-full no-wrap"):
        ui.html(f'<div class="headerline">{HEADER_LINE}</div>', sanitize=False).classes("grow")
        ui.button("Copy header", icon="content_copy", color=None, on_click=lambda: (ui.clipboard.write(HEADER_LINE), ui.notify("Header copied", type="positive"))).props("outline no-caps dense")
    rows = [{"column": name, "need": need, "what": what, "example": example,
             "also": ", ".join(a for a in config.COLUMN_ALIASES[name] if a != name)} for name, need, what, example in EXPECTED_COLUMNS]
    table = ui.table(columns=[{"name": "column", "label": "Column", "field": "column", "align": "left"},
                              {"name": "need", "label": "Needed", "field": "need", "align": "left"},
                              {"name": "what", "label": "What it holds", "field": "what", "align": "left", "style": "white-space:normal;min-width:260px"},
                              {"name": "example", "label": "Example", "field": "example", "align": "left"},
                              {"name": "also", "label": "Also accepted as", "field": "also", "align": "left", "style": "white-space:normal;min-width:180px"}],
                     rows=rows, row_key="column").classes("w-full").props("dense flat")
    table.add_slot("body-cell-column", '<q-td :props="props"><b class="mono">{{ props.row.column }}</b></q-td>')
    table.add_slot("body-cell-need", """<q-td :props="props"><span :class="props.row.need === 'required' ? 'req' : 'opt'">{{ props.row.need }}</span></q-td>""")
    ui.label("Only english and german are required; everything else can be left out. The header names are not case-sensitive.").classes("muted text-sm")


def pretty(name: str) -> str:
    return name.replace("_", " ").title()


def words_page() -> None:
    with frame("words"):
        ui.label("Word list").classes("text-3xl font-bold serif")
        ui.label("The sheet the game learns from. Use the bundled list or load your own Excel or CSV file.").classes("muted")
        catalog = state.catalog()
        words = state.words()

        def pick(event) -> None:
            state.wordlist = event.value
            ui.navigate.reload()

        with ui.row().classes("items-center gap-3"):
            ui.label("Active list").classes("font-bold")
            ui.select({n: pretty(n) for n in catalog}, value=state.list_name(), on_change=pick).props("outlined dense").classes("w-64")

        # ------------------------------------------------------------------ what is in the list
        fresh = session.new_words(words, state.store.progress)
        C.tiles([("Words", str(len(words)), pretty(state.list_name() or "")), ("Not learned yet", str(len(fresh)), "available to learn"),
                 *[(CLASS_NAMES.get(c, c.title()), str(n), "") for c, n in list(session.class_counts(words).items())[:2]]])

        # ------------------------------------------------------------------ loading a sheet
        preview: dict = {"df": None, "report": None, "name": "my_words"}

        @ui.refreshable
        def upload_result() -> None:
            df, report = preview["df"], preview["report"]
            if df is None:
                return
            C.tiles([("Rows read", str(report.rows_read), ""), ("Words kept", str(report.rows_kept), ""), ("Removed", str(report.rows_dropped), "empty, incomplete or duplicate")])
            for note in report.messages:
                ui.label("• " + note).classes("muted text-sm")
            ui.table(columns=[{"name": c, "label": c, "field": c, "align": "left"} for c in config.WORD_COLUMNS],
                     rows=df[config.WORD_COLUMNS].head(8).fillna("").to_dict("records"), row_key="german").classes("w-full")
            ui.input("Name for this list", value=preview["name"], on_change=lambda e: preview.update(name=e.value)).props("outlined dense").classes("w-64")
            ui.button("Save and use this list", icon="save", on_click=save).props("unelevated no-caps color=primary")

        async def handle_upload(event: events.UploadEventArguments) -> None:
            data = await event.file.read()
            name = event.file.name
            try:
                sheet = 0
                if name.lower().endswith(".xlsx") and len(wordlist.list_sheets(io.BytesIO(data))) > 1:
                    ui.notify("The first sheet of the workbook was used.", type="info")
                df, report = wordlist.load_wordlist(io.BytesIO(data), filename=name, sheet_name=sheet)
            except wordlist.WordListError as error:
                ui.notify(str(error), type="negative", multi_line=True)
                return
            if df.empty:
                ui.notify("The file has no usable rows.", type="warning")
                return
            preview.update(df=df, report=report, name=wordlist.safe_name(name))
            upload_result.refresh()

        def save() -> None:
            path = wordlist.save_upload(preview["df"], preview["name"])
            state.wordlist = path.stem
            ui.notify(f"Saved “{path.stem}” and selected it.", type="positive")
            ui.navigate.reload()

        with ui.column().classes("card w-full gap-3"):
            ui.label("Load your own sheet").classes("text-lg font-bold")
            columns_help()
            ui.upload(on_upload=handle_upload, auto_upload=True, label="Drop a .csv or .xlsx file here").props("accept=.csv,.xlsx flat bordered").classes("w-full")
            with ui.row().classes("gap-2"):
                ui.button("Template (CSV)", icon="download", on_click=lambda: ui.download.content(wordlist.to_csv_bytes(TEMPLATE), "wortschatz_template.csv"), color=None).props("outline no-caps dense")
                ui.button("Template (Excel)", icon="download", on_click=lambda: ui.download.content(wordlist.to_excel_bytes(TEMPLATE), "wortschatz_template.xlsx"), color=None).props("outline no-caps dense")
            upload_result()

        report = state.load_list(state.list_name())[1] if state.list_name() else None
        checks = wordlist.quality_checks(words) if len(words) else []
        with ui.column().classes("card w-full gap-2"):
            ui.label("Data-quality checks").classes("text-lg font-bold")
            ui.label("Run on every list you load.").classes("muted text-sm")
            for check in checks:
                icon, color = {"pass": ("check_circle", "#2F855A"), "warn": ("warning", "#E3A008"), "fail": ("error", "#C8102E")}[check.status]
                with ui.row().classes("items-center gap-2 no-wrap"):
                    ui.icon(icon).style(f"color:{color}")
                    ui.label(check.name).classes("font-medium")
                    ui.label(check.detail).classes("muted text-sm")
            if report and report.messages:
                ui.label("Cleaning applied when the file was loaded: " + "; ".join(report.messages)).classes("muted text-sm")

        # ------------------------------------------------------------------ browse
        ui.label("Browse the list").classes("text-lg font-bold")
        search = ui.input(placeholder="Search German or English…").props("outlined dense clearable").classes("w-72")
        rows = [{"id": w["word_id"], "article": w["article"], "german": w["german"], "english": w["english"], "type": w["word_class"],
                 "forms": forms_text(w)} for w in words.to_dict("records")]
        columns = [{"name": "german", "label": "German", "field": "german", "align": "left", "sortable": True},
                   {"name": "english", "label": "English", "field": "english", "align": "left", "sortable": True},
                   {"name": "type", "label": "Type", "field": "type", "align": "left", "sortable": True},
                   {"name": "forms", "label": "Forms", "field": "forms", "align": "left"}]
        table = ui.table(columns=columns, rows=rows, row_key="id", pagination=12).classes("w-full")
        table.add_slot("body-cell-german", GERMAN_SLOT)
        search.bind_value(table, "filter")
